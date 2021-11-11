pylaprof features

# Wave 1
- Turn on/off profiling with an environment variable <--- OK!
- just a simple decorator for your existing handler function <-- OK!
- save profiling data on S3 <--- OK!
- allow merge of multiple profiling data files <--- OK!
- decouple profiler from S3 logic (or more in general storage), I want to be able to
  use it in other environments. <--- OK! (Storer/Sampler/Profiler should be good enough)
- specify a threeshold in order to save the profiling data only if execution lasts more
  than X seconds <--- OK!

# Wave 2
- Fix the mess you did in iteration 1
