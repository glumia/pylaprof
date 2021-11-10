import sys
import threading
from collections import defaultdict
from functools import partial, wraps


class Sampler:
    def sample(self, frame):
        pass

    def dump(self):
        pass


class StackCollapse(Sampler):
    def __init__(self):
        super().__init__()
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
        with open("stackcollapse.out", "w") as fp:
            for stack, hits in self._data.items():
                print(";".join(stack[::-1]), hits, file=fp)


class Profile(threading.Thread):
    def __init__(self, period=0.01, single=True, sampler=None):
        """
        period (float)
          How many seconds to wait between consecutive samples.
          The smaller, the more profiling overhead, but the faster results
          become meaningful.
          The larger, the less profiling overhead, but requires long profiling
          session to get meaningful results.
        single (bool)
          Profile only the thread which created this instance.
        sampler (Sampler)
          Sampler to use to process stack frames.
          Defaults to an instance of `StackCollapse` if none.
        """
        if sampler is None:
            self.sampler = StackCollapse()
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
        test = self._test
        stop_event = self._stop_event
        wait = partial(stop_event.wait, self._period)
        current_frames = sys._current_frames
        sample = self.sampler.sample
        while self._can_run:
            for ident, frame in current_frames().items():
                if test(ident):
                    sample(frame)
            wait()

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
