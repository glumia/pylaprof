import sys
import threading
from collections import defaultdict


class Profile(threading.Thread):
    def __init__(self, period=0.01, single=True):
        """
        period (float)
          How many seconds to wait between consecutive samples.
          The smaller, the more profiling overhead, but the faster results
          become meaningful.
          The larger, the less profiling overhead, but requires long profiling
          session to get meaningful results.
        single (bool)
          Profile only the thread which created this instance.
        """
        self._data = defaultdict(lambda: 0)
        self._test = None
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
        if test is None:
            test = lambda x, ident=threading.current_thread().ident: ident != x
        stop_event = self._stop_event
        while self._can_run:
            for ident, frame in sys._current_frames().items():
                if test(ident):
                    stack = []
                    while frame:
                        filename = frame.f_code.co_filename
                        funcname = frame.f_code.co_name
                        lineno = frame.f_lineno
                        stack.append(f"{funcname} ({filename}:{lineno})")
                        frame = frame.f_back
                    self._data[tuple(stack)] += 1
            frame = None
            stop_event.wait(self._period)

        # Dump profiling data
        with open("flamegraph-beta.txt", "w") as fp:
            for stack, hits in self._data.items():
                print(";".join(stack[::-1]), hits, file=fp)

        stop_event.clear()
        self.clean_exit = True
