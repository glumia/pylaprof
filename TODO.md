pylaprof features

- Turn on/off profiling with an environment variable
- just a simple decorator for your existing handler function <-- OK!
- save profiling data on S3
- allow merge of multiple profiling data files
- decouple profiler from S3 logic (or more in general storage), I want to be able to use it in other environments.
- specify a threeshold in order to save the profiling data only if execution lasts more than X seconds
