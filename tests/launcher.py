#!/usr/bin/env python3

import sys

from handler import handler
from pylaprof import FS, S3, Profile


def main():
    print("launcher: calling handler")

    context = {"some": "context value"}
    event = {"some": "event value"}
    response = handler(context, event)

    print("launcher: got response", response)


if __name__ == "__main__":
    if len(sys.argv) == 1:  # py-spy or other external profiler
        main()
        exit(0)

    if sys.argv[1] == "--s3":
        storer = S3()
    elif sys.argv[1] == "--fs":
        storer = FS()
    else:
        print("wat")
        exit(1)

    with Profile(period=0.01, storer=storer):
        main()
