# Examples
This directory contains two examples of how you can use pylaprof and the reports
it generates: [hello-lambda](./hello-lambda), an AWS lambda function, and
*launcher.py*, a dummy command-line application.

## launcher.py
This "project" shows how you can use pylaprof as a context manager for
any Python function.

To reproduce `flame.svg`, launch the dummy HTTP API service:
```
$ ./server.py
```

Run code of `handler.py` and generate a stackcollapse report in the current directory:
```
$ ./launcher.py --fs
```

Finally use Brendan Gregg's [flamegraph generator](
https://github.com/brendangregg/flamegraph):
```
$ $HOME/FlameGraph/flamegraph.pl pylaprof-2021-11-21T10\:48\:51.865486+00\:00.txt > flame.svg
```
