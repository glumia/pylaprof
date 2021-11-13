import os
import shutil
import sys
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from functools import partial, wraps
from io import StringIO

import boto3


class Storer:
    def store(self, file):
        """
        Store a profiling report.

        file
          A file-like object with profiling's data.
        """
        pass


class FS(Storer):
    """
    Stores report's data on the filesystem.
    """

    def __init__(self, path=None):
        """
        path (str)
          Where to store the report. Defaults to `pylaprof-{date}.txt` if None.
        """
        self.path = path

    def store(self, file):
        path = self.path
        if path is None:
            now = datetime.now(timezone.utc).isoformat()
            path = f"pylaprof-{now}.txt"
        with open(path, "w") as fp:
            shutil.copyfileobj(file, fp)


class S3(Storer):
    """
    Stores report's data on S3.
    """

    def __init__(
        self,
        bucket="pylaprof",
        bucket_opts=None,
        create_bucket=True,
        prefix=None,
        put_object_opts=None,
    ):
        """
        bucket (string)
          Bucket where to store the report file.
        bucket_opts (dict)
          Additional options to provide to boto's S3 `create_bucket` method.
        create_bucket (bool)
          Create bucket if it doesn't already exists.
        prefix (string)
          String to prepend to report files. Defaults to a random string of 8
          characters if None.
        put_object_opts (dict)
          Additional options to provide to bucket's `put_object` method.
        """
        s3 = boto3.resource("s3")

        if bucket_opts is None:
            bucket_opts = {}

        self.bucket = s3.Bucket(bucket)
        if create_bucket:
            self.bucket = s3.create_bucket(Bucket=bucket, **bucket_opts)

        self.prefix = lambda: str(uuid.uuid4())[:8]
        if prefix is not None:
            self.prefix = lambda: prefix

        self.put_object_opts = put_object_opts if put_object_opts is not None else {}

    def store(self, file):
        prefix = self.prefix()
        now = datetime.now(timezone.utc).isoformat()
        key = f"{prefix}-{now}.txt"
        self.bucket.put_object(Body=file.read(), Key=key, **self.put_object_opts)


class Sampler:
    def sample(self, frame):
        """
        Sample a thread's stack trace.

        frame (frame)
          A frame object (check https://docs.python.org/3/library/inspect.html).
        """
        pass

    def dump(self, storer):
        """
        Dump sampling data.

        storer (Storer)
          Storer to use for data's storage.
        """
        pass


class StackCollapse(Sampler):
    """
    Create profiling data that can be fed to Brendan Gregg's Flamegraph
    generator (https://github.com/brendangregg/flamegraph).
    """

    def __init__(self):
        self._data = defaultdict(lambda: 0)

    def sample(self, frame):
        stack = []
        while frame:
            filename = frame.f_code.co_filename
            funcname = frame.f_code.co_name
            lineno = frame.f_lineno
            stack.append(f"{funcname} ({filename}:{lineno})")
            frame = frame.f_back
        self._data[tuple(stack)] += 1

    def dump(self, storer):
        file = StringIO()
        for stack, hits in self._data.items():
            print(";".join(stack[::-1]), hits, file=file)
        file.seek(0)
        storer.store(file)


class Profile(threading.Thread):
    def __init__(self, period=0.01, single=True, min_time=0, sampler=None, storer=None):
        """
        period (float)
          How many seconds to wait between consecutive samples.
          The smaller, the more profiling overhead, but the faster results
          become meaningful.
          The larger, the less profiling overhead, but requires long profiling
          session to get meaningful results.
        single (bool)
          Profile only the thread which created this instance.
        min_time (int)
          Store profiling data only if execution lasts more than this amount of time.
        sampler (Sampler)
          Sampler to use to process stack frames.
          Defaults to an instance of `StackCollapse` if None.
        storer (Storer)
          Storer to use to memorize sampler's report.
          Defaults to an instance of `S3` if none.

        Profiler's activity can be controlled through the `PYLAPROF_DISABLE` environment
        variable: if it is set to a truthy value then its context will be a noop (but
        existing profiling activity will continue until the profiled function doesn't
        return). This can be useful if you want to profile a function you use in
        production: just decorate it and turn on/off profiling through this environment
        variable.
        """
        super().__init__()

        self.period = period
        self.min_time = min_time

        self._test = None
        if single:
            self._test = lambda x, ident=threading.current_thread().ident: ident == x

        if storer is None:
            storer = S3()
        self.storer = storer

        if sampler is None:
            sampler = StackCollapse()
        self.sampler = sampler

        self._can_run = False
        self._stop_event = threading.Event()
        self.daemon = True
        self.clean_exit = False

    def start(self):
        self.clean_exit = False
        self._can_run = True
        super().start()

    def stop(self):
        """
        Request thread to stop.
        Does not wait for actual termination (use join() method).
        """
        if self.is_alive():
            self._can_run = False
            self._stop_event.set()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.join()

    def run(self):
        if os.getenv("PYLAPROF_DISABLE"):
            self._stop_event.clear()
            self.clean_exit = True
            return

        # The `while self._can_run` block below is a tight loop, we do those assignments
        # to reduce indirection when it runs.
        test = self._test
        if test is None:
            test = lambda x, ident=threading.current_thread().ident: ident != x
        stop_event = self._stop_event
        wait = partial(stop_event.wait, self.period)
        current_frames = sys._current_frames
        sample = self.sampler.sample

        start = time.time()
        while self._can_run:
            for ident, frame in current_frames().items():
                if test(ident):
                    sample(frame)
            wait()
        end = time.time()

        if end - start >= self.min_time:
            self.sampler.dump(self.storer)

        stop_event.clear()
        self.clean_exit = True


class profile:
    """
    Allows to use `Profile` as a decorator:

    @profile(period=0.01, single=True)
    def slow_function():
        ...
    """

    def __init__(self, period=0.01, single=True, min_time=0, sampler=None, storer=None):
        """
        Check `Profile`.
        """
        self.period = period
        self.single = single
        self.min_time = min_time
        self.sampler = sampler
        self.storer = storer

    def __call__(self, func):
        @wraps(func)
        def profile_wrapped(*args, **kwargs):
            with Profile(
                period=self.period,
                single=self.single,
                min_time=self.min_time,
                sampler=self.sampler,
                storer=self.storer,
            ):
                return func(*args, **kwargs)

        return profile_wrapped
