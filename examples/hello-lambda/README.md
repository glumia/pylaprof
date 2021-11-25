# hello-lambda
A dead-simple serverless framework project with an AWS lambda function we
profile with pylaprof's decorator.

If you don't specify any storer pylaprof will instantiate and use a default
S3 storer that requires a `pylaprof` bucket on your AWS account.

Remember to give your lambda functions permissions to write on this bucket
(check lines 6-10 of [serverless.yml](./serverless.yml)), otherwise pylaprof
will not be able to store the profiling report.

You can turn on/off pylaprof once your lambda function is deployed by changing
the `PYLAPROF_DISABLE` environment variable (no need for another deploy!).
