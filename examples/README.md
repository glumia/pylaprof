Just a bunch of examples of how you can use pylaprof.

### hello-lambda
This project shows how you can use pylaprof as a decorator for your lambda
function (check `hello-lambda/handler.py`).


### launcher
This "project" shows how you can use pylaprof as a context manager for
any Python function (check `launcher.py`).

To reproduce `flame.svg`, launch the *slowserver* API service:
```
~/pylaprof/examples$ go run slowserver.go
```

Run code of `handler.py` and generate a stackcollapse report in the current directory:
```
~/pylaprof/examples$ ./launcher --fs
```

Finally use Brendan Gregg's [flamegraph generator](
https://github.com/brendangregg/flamegraph):
```
~/pylaprof/examples$ ../../FlameGraph/flamegraph.pl pylaprof-2021-11-14T21\:13\:30.548307+00\:00.txt > flame.svg
```
