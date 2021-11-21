#!/usr/bin/env python
"""Benchmark pylaprof's impact on example's handler.
"""

import argparse
import math
import statistics
import sys
import time

from handler import handler

from pylaprof import Profiler, Storer


class Null(Storer):
    """Storer that doesn't do anything with the record file."""

    def store(self, file):
        pass


def main():
    parser = argparse.ArgumentParser(sys.argv[0])
    parser = argparse.ArgumentParser(
        description="benchmark pylaprof's impact on example's handler"
    )
    parser.add_argument(
        "--period",
        metavar="PERIOD",
        type=float,
        default=0.01,
        help="`period` parameter for pylaprof (default: 0.01)",
    )
    parser.add_argument(
        "--iterations",
        metavar="NUM",
        type=int,
        default=3,
        help="number of executions (default: 3)",
    )
    opts = parser.parse_args(sys.argv[1:])

    print("Iterating", opts.iterations, "times over example's handler w/wo pylaprof.\n")

    durations_native = []
    durations_pylaprof = []
    for i in range(opts.iterations):
        start = time.time()
        with Profiler(period=opts.period, storer=Null()):
            handler({"dummy": "event"}, {"dummy": "context"})
        durations_pylaprof.append(time.time() - start)

        start = time.time()
        handler({"dummy": "event"}, {"dummy": "context"})
        durations_native.append(time.time() - start)

    print(
        'Performance stats for `handler({"dummy": "event"}, {"dummy": "context"})`',
        "(native):\n\t",
        statistics.mean(durations_native),
        "+-",
        statistics.stdev(durations_native),
        "seconds per execution",
    )

    print(
        'Performance stats for `handler({"dummy": "event"}, {"dummy": "context"})`',
        f"(pylaprof enabled with period {opts.period}):\n\t",
        statistics.mean(durations_pylaprof),
        "+-",
        statistics.stdev(durations_pylaprof),
        "seconds per execution",
    )

    # ~ Quick probability theory recap.
    # Let X and Y be two independent and identically distributed random variables, then:
    #
    # mean(X-Y) = mean(X) + mean(Y)
    # variance(X-Y) = variance(X) + variance(Y)
    # stdev(X) = sqrt(variance(X))
    print(
        "\nPerformance impact of pylaprof:\n\t",
        statistics.mean(durations_pylaprof) - statistics.mean(durations_native),
        " +-",
        math.sqrt(
            statistics.variance(durations_pylaprof)
            + statistics.variance(durations_native)
        ),
        "seconds per execution",
    )


if __name__ == "__main__":
    main()
