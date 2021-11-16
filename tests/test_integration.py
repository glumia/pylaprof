import re

import boto3
import pytest
from moto import mock_s3

from pylaprof import FS, S3, Profiler

from .sleepy import sleepy


def test_profiler_with_fs_storer(tmpcwd):
    """Check profiler with FS storer.

    We set a period of 0.01s and run `sleepy` for 0.105s, so we should get a report with
    10 hits of this function.
    """
    with Profiler(period=0.01, storer=FS(path=lambda: "report.txt")):
        sleepy(0.105)

    regex = re.compile(r".*;sleepy \(\/[^)]+\/sleepy\.py:28\) 10")
    with open("report.txt", "r") as fp:
        report = fp.read()
    for line in report.split("\n"):
        if regex.match(line):
            return  # Ok!
    else:
        pytest.fail("something is wrong with the report:\n" + report)


@mock_s3
def test_profiler_with_s3_storer():
    """Check profiler with S3 storer.

    We set a period of 0.01s and run `sleepy` for 0.105s, so we should get a report with
    10 hits of this function.
    """
    boto3.resource("s3").Bucket("pylaprof").create()

    with Profiler(period=0.01, storer=S3(key=lambda: "report.txt")):
        sleepy(0.105)

    regex = re.compile(r".*;sleepy \(\/[^)]+\/sleepy\.py:28\) 10")
    report = (
        boto3.resource("s3")
        .Object("pylaprof", "report.txt")
        .get()["Body"]
        .read()
        .decode("utf-8")
    )
    for line in report.split("\n"):
        if regex.match(line):
            return  # Ok!
    else:
        pytest.fail("something is wrong with the report:\n" + report)
