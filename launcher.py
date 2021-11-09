#!/usr/bin/env python3

import sys

from handler import handler
from pylaprof import Profile


def main():
    print("launcher: calling handler")

    context = {"some": "context value"}
    event = {"some": "event value"}
    response = handler(context, event)

    print("launcher: got response", response)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--bare":
        main()
    else:
        with Profile(period=0.01, single=True):
            main()
