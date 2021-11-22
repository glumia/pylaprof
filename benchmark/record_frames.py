#!/usr/bin/env python
"""Script to dump frames of execution of example's handler.

We need to define a `Code` and `Frame` class as pickle isn't able to dump Python's
native `frame` and `code` classes.
"""

import pickle

from handler import handler

from pylaprof import FS, Profiler, Sampler


class Code:
    def __init__(self, co_filename, co_name):
        self.co_filename = co_filename
        self.co_name = co_name


class Frame:
    def __init__(self, f_code, f_lineno, f_back):
        self.f_code = f_code
        self.f_lineno = f_lineno
        self.f_back = f_back


class Raw(Sampler):
    def __init__(self):
        self.data = []

    def sample(self, frame):
        # Flatten frames into a list
        frames = []
        while frame:
            frames.append(frame)
            frame = frame.f_back

        # Rebuild the stack with our custom `Frame` and `Code` instances
        frames = frames[::-1]
        for i in range(len(frames)):
            frame = frames[i]
            code = Code(frame.f_code.co_filename, frame.f_code.co_name)
            frame = Frame(code, frame.f_lineno, None)
            if i > 0:
                frame.f_back = frames[i - 1]
            frames[i] = frame

        # Record custom stack
        self.data.append(frames[-1])

    def dump(self, file):
        pickle.dump(self.data, file)


if __name__ == "__main__":
    with Profiler(period=0.001, sampler=Raw(), storer=FS(path=lambda: "frames.dump")):
        handler({"dummy": "event"}, {"dummy": "context"})
