# TO-DO
## Wave 1 - features features features
- Turn on/off profiling with an environment variable <--- OK!
- Just a simple decorator for your existing handler function <-- OK!
- Save profiling data on S3 <--- OK!
- Allow merge of multiple profiling data files <--- OK!
- Decouple profiler from S3 logic (or more in general storage) - I want to be able to
  use the profiler in environments other than AWS Lambdas <--- OK! (the
  Storer/Sampler/Profiler abstraction should be good enough)
- Specify a threeshold in order to save the profiling data only if execution lasts more
  than X seconds <--- OK!

## Wave 2
- Fix the mess you did in iteration 1 <--- OK!

## Wave 3 - Time for the boring work
- Add a test suite 
- Add coverage report generation
- Packaging (poetry!)
- Add linters (flake8, black, isort, bandit, safety)
- Documentation, documentation, documentation. Show what we can do with pylaprof :)
- Set-up CI/CD (Github Actions, package upload on PyPI, documentation on
  readthedocs).

## Wave 4 - Let's get production ready
- Error handling and logging
- Tight loop optimization (maybe use Cython for that?)
- Measure and document performance impact