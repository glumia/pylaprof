import logging
import os
import shutil
import sys
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from distutils.util import strtobool
from functools import partial, wraps
from io import BytesIO

try:
    import boto3

except ModuleNotFoundError:  # pragma: nocover
    pass  # That's fine if you don't want to use S3


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Storer:
    def store(self, file):
        """
        Store a profiling report.

        file
          A file-like object in binary mode with profiling's data.
        """
        pass  # pragma: no cover


class FS(Storer):
    """
    Stores report's data on the filesystem.
    """

    def __init__(self, path=None):
        """
        path (func() -> str)
          Function to use to get report's destination path. Defaults to a generator with
          format `pylaprof-{date}.txt` if None.
        """
        self.path = path
        if path is None:
            self.path = lambda: f"pylaprof-{datetime.now(timezone.utc).isoformat()}.txt"

    def store(self, file):
        path = self.path()
        with open(path, "wb") as fp:
            shutil.copyfileobj(file, fp)


class S3(Storer):
    """
    Stores report's data on S3.
    """

    def __init__(
        self,
        s3_opts=None,
        bucket="pylaprof",
        key=None,
        put_object_opts=None,
    ):
        """
        s3_opts (dict)
          Additional options to provide to boto3's `resource` method.
        bucket (string)
          Bucket where to store the report file(s).
        key (func() -> str)
          Function to use to get report's object key. Defaults to a generator with
          format `{randstr}-{date}.txt` if None.
        put_object_opts (dict)
          Additional options to provide to bucket's `put_object` method.
        """
        if s3_opts is None:
            s3_opts = {}
        s3 = boto3.resource("s3", **s3_opts)

        self.bucket = s3.Bucket(bucket)

        self.key = key
        if key is None:
            self.key = (
                lambda: f"{str(uuid.uuid4())[:8]}-{datetime.now(timezone.utc).isoformat()}.txt"  # noqa
            )

        self.put_object_opts = {}
        if put_object_opts is not None:
            self.put_object_opts = put_object_opts

    def store(self, file):
        key = self.key()
        self.bucket.put_object(Body=file.read(), Key=key, **self.put_object_opts)


class Sampler:
    def sample(self, frame):
        """
        Sample a thread's stack trace.

        frame (frame)
          A frame object (check https://docs.python.org/3/library/inspect.html).
        """
        pass  # pragma: no cover

    def dump(self, file):
        """
        Dump sampling data.

        file
          A file-like object in binary mode where to write data.
        """
        pass  # pragma: no cover


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

    def dump(self, file):
        for stack, hits in self._data.items():
            line = f"{';'.join(stack[::-1])} {hits}\n"
            file.write(line.encode())


class Profiler(threading.Thread):
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
          Store profiling data only if execution lasts more than this amount of seconds.
        sampler (Sampler)
          Sampler to use to process stack frames.
          Defaults to an instance of `StackCollapse` if None.
        storer (Storer)
          Storer to use to memorize sampler's report.
          Defaults to an instance of `S3` if none.

        Profiler's activity can be controlled through the `PYLAPROF_DISABLE` environment
        variable: if it is set to 'true' then profiler's context will be a noop (but
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

        self._can_run = False  # Variable to control profiler's main loop.
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
        self._can_run = False
        self._stop_event.set()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.join()

    def run(self):
        try:
            if strtobool(os.getenv("PYLAPROF_DISABLE", "false")):
                self._stop_event.clear()
                self.clean_exit = True
                return

            # The `while self._can_run` block below is a tight loop, we do those
            # assignments to reduce indirection when it runs.
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
                file = BytesIO()
                self.sampler.dump(file)
                file.seek(0)
                self.storer.store(file)

            stop_event.clear()
            self.clean_exit = True
        except Exception:
            logger.exception("Uncaught exception")


class profile:
    """
    Allows to use `Profiler` as a decorator:

    @profile(period=0.01, single=True)
    def slow_function():
        ...
    """

    def __init__(self, period=0.01, single=True, min_time=0, sampler=None, storer=None):
        """
        Check `Profiler`.
        """
        self.period = period
        self.single = single
        self.min_time = min_time
        self.sampler = sampler
        self.storer = storer

    def __call__(self, func):
        @wraps(func)
        def profiler_wrapped(*args, **kwargs):
            with Profiler(
                period=self.period,
                single=self.single,
                min_time=self.min_time,
                sampler=self.sampler,
                storer=self.storer,
            ):
                return func(*args, **kwargs)

        return profiler_wrapped
