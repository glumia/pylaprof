Just a bunch of examples of how you can use pylaprof.

### hello-lambda
This project shows how you can use pylaprof as a decorator for your lambda
function (check `hello-lambda/handler.py`).


### launcher
This "project" shows how you can use pylaprof as a context manager for
any Python function (check `launcher.py`).

To reproduce `flame.svg`, launch the dummy HTTP API service:
```
~/pylaprof/examples$ ./server.py
```

Run code of `handler.py` and generate a stackcollapse report in the current directory:
```
~/pylaprof/examples$ ./launcher.py --fs
```

Finally use Brendan Gregg's [flamegraph generator](
https://github.com/brendangregg/flamegraph):
```
~/pylaprof/examples$ ../../FlameGraph/flamegraph.pl pylaprof-2021-11-21T10\:48\:51.865486+00\:00.txt > flame.svg
```
