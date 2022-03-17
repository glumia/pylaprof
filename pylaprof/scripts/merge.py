#!/usr/bin/env python

import argparse
import sys
from collections import defaultdict

DEFAULT_OUT = "stackcollapse-merged.txt"


def merge(files, dst):
    data = defaultdict(lambda: 0)

    for file in files:
        with open(file, "r") as fp:
            for line in fp.readlines():
                stack, hits = line.rsplit(" ", 1)
                hits = int(hits)
                data[stack] += hits

    with open(dst, "w") as fp:
        for stack, hits in data.items():
            print(stack, hits, file=fp)


def main():
    parser = argparse.ArgumentParser(sys.argv[0])
    parser = argparse.ArgumentParser(
        description="merge multiple stackcollapes into a single one"
    )
    parser.add_argument(
        "files", metavar="FILE", type=str, nargs="+", help="a stackcollapse file"
    )
    parser.add_argument(
        "-o",
        "--out",
        default=DEFAULT_OUT,
        help=f"write resulting stackcollapse to this file (default: {DEFAULT_OUT})",
    )
    opts = parser.parse_args(sys.argv[1:])

    merge(opts.files, opts.out)


if __name__ == "__main__":
    main()
