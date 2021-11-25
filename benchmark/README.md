## Measure performance impact
`performance_impact.py` is a utility to benchmark the impact of pylaprof on example's
handler code.

```
./performance_impact.py --iterations 10 --period 0.01
```

You can easily adapt it to measure the impact of pylaprof on any other function.


## Profile and benchmark a sampler
Sampler's `sample` execution time imposes a lower bound to the real period of
profiler's sampling: it is useless to provide 10 μs (`0.00001`) as *period* parameter if
`sample` takes 100 μs to run (the actual sampling period would be 110 μs).

The smaller the period that is provided the more it matters how much our sampler
actually takes to process the return value of `sys._current_frames`.

`record_frames.py` and `process_frames.py` are two utility scripts to profile and
benchmark the `sample` implementation of `StackCollapse`.

To generate frames data that can later be fed to our sampler (this requires
example's dummy API server to be running):
```
./record_frames.py
```

To profile the `sample` implementation of `StackCollapse` using the generated data (we
could use pylaprof itself instead of py-spy for that but... let's avoid Inception):
```
py-spy record -r 1000 -i -- ./process_frames.py
```

And to benchmark it (replace 1000 with the number of iterations over the data
set you want, the more the better):
```
./process_frames.py --iterations 1000
```

Any other sampler implementation can be profiled and benchmarked similarly with
smaller changes to `process_frames.py`.

## Benchmark results
Results of benchmarks on a i7-1165G7 @ 2.80GHz with 16GB of LPDDR4 4267 MHz ram.

```
$ ./server.py 2>/dev/null &
[1] 15751
$ ./record_frames.py
$ ./process_frames.py --iterations 10000
Iterating 10000 times over 5266 frames.

Performance stats for `sample` method of class `StackCollapse`:
         3.308478209440852e-06 +- 5.438494214420574e-07 seconds per call
$ ./performance_impact.py --iterations 10
Iterating 10 times over example's handler w/wo pylaprof.

Performance stats for `handler({"dummy": "event"}, {"dummy": "context"})` (native):
         9.006643843650817 +- 0.5760573076093592 seconds per execution
Performance stats for `handler({"dummy": "event"}, {"dummy": "context"})` (pylaprof enabled with period 0.01):
         8.722303414344788 +- 0.11405732794170521 seconds per execution

Performance impact of pylaprof:
         -0.2843404293060292  +- 0.587240236791848 seconds per execution
```

The sampler takes ~3.3 μs to process a stack snapshot and the impact of pylaprof with a
sampling period of 0.01 on handler's performance is indistinguishable from the noise of
other factors.

**Note**: in those benchmarks we use a dummy storer that ignores the report file generated
by the sampler, **in a real scenario you need to take into account the time to store
report's data** on the filesystem or upload it on S3.
