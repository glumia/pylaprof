# pylaprof
pylaprof is a Python library that allows you to profile functions or sections of code.

As a decorator:
```python
from pylaprof import profile

@profile()
def handler(event, context):
  ...
```

As a context manager:
```python
from pylaprof import Profiler

def main():
  ...
  with Profiler():
    # Only code inside this context will be profiled.
    ...
```

It is built around three main abstractions: the *profiler*, the *sampler*, and
the *storer*.

The profiler is the main component of pylaprof, it takes care of taking
snapshots of your program's stack at regular intervals of times and feeding them
to the *sampler* for processing; at the end of the profiling session, it will
then ask the *sampler* for a report and provide it to the *storer*.

Take a look at the [source](./pylaprof/__init__.py) for more documentation and
some pre-implemented samplers and storers or [here](./examples) for some
usage examples.

## Features
- Accessible: pylaprof's code is thoroughly documented and written to be read and
  understood by other humans.

- Extensible: you can write your own sampler or storer to generate reports in the format
  you like and store them where and how you want.

- Zero external dependencies[^1].

- Close to zero impact on performances (check [benchmark](./benchmark) for
  more details).

- Production-ready: pylaprof was built with the context of long-running
  applications or continuously invoked lambda functions in mind.
  It will never break your code or pollute your standard output or error
  with unwanted messages.

- Turn on/off profiling with an environment variable.

- Store the profiling report only if execution takes longer than a threshold.

[^1]: boto3 is optional and required only if you want to use the S3 storer.

### pylaprof-merge
`pylaprof-merge` is a simple CLI tool to merge multiple stackcollapse reports
into a single one. This might come in handy if you want to get an aggregated
overview of a function or piece of code that is executed frequently for short
periods. It is installed automatically if you get pylaprof with pip.


## Installation
```
pip install pylaprof
```

Or just copy-paste the pylaprof directory where you need it.


## Credits
- This library is heavily inspired to [pprofile](
  https://github.com/vpelletier/pprofile): thanks to its authors for writing such
  accessible and well-documented code.
- Thanks to @jvns for writing and distributing some of her *wizard zines* for free:
  it's what got me into the rabbit hole of profiling in the first place.
