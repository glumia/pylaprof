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
    def store(file):
        pass


class FS(Storer):
    def __init__(self, path=None):
        self.path = path

    def store(self, file):
        if self.path is None:
            now = datetime.now(timezone.utc).isoformat()
            filepath = f"pylaprof-{now}.txt"
        with open(filepath, "w") as fp:
            shutil.copyfileobj(file, fp)


class S3(Storer):
    def __init__(self):
        s3 = boto3.resource("s3")
        self.bucket = s3.create_bucket(
            Bucket="pylaprof",
        )

    def store(self, file):
        uid = str(uuid.uuid4())[:8]  # helps us to avoid conflicts on S3
        now = datetime.now(timezone.utc).isoformat()
        key = f"{uid}-{now}.txt"
        self.bucket.put_object(Body=file.read(), Key=key)


class Sampler:
    def __init__(self, storer=None):
        if storer is None:
            storer = FS()
        self.storer = storer

    def sample(self, frame):
        pass

    def dump(self):
        pass


class StackCollapse(Sampler):
    def __init__(self, storer=None):
        super().__init__(storer=storer)
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

    def dump(self):
        file = StringIO()
        for stack, hits in self._data.items():
            print(";".join(stack[::-1]), hits, file=file)
        file.seek(0)
        self.storer.store(file)


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
          Store sampler's report only if execution lasts more than this amount of time.
        sampler (Sampler)
          Sampler to use to process stack frames.
          Defaults to an instance of `StackCollapse` if none.
        storer (Storer)
          Storer to use to memorize sampler's report.
          Defaults to an instance of `FS` if none.
        """
        self.min_time = min_time
        if sampler is None:
            self.sampler = StackCollapse(storer=storer)
        self._test = lambda x, ident=threading.current_thread().ident: ident != x
        if single:
            self._test = lambda x, ident=threading.current_thread().ident: ident == x

        super().__init__()
        self._stop_event = threading.Event()
        self._period = period
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
            self.clean_exit = True
            return

        test = self._test
        stop_event = self._stop_event
        wait = partial(stop_event.wait, self._period)
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
            self.sampler.dump()
        stop_event.clear()
        self.clean_exit = True

    def __call__(self, func):
        """
        Allows to use `Profile` as a decorator:

        @Profile(period=0.01, single=True)
        def slow_function():
            ...
        """

        @wraps(func)
        def pfunc(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return pfunc
