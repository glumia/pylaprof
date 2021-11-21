import filecmp
import os
from unittest.mock import Mock
from uuid import UUID

from freezegun import freeze_time

from pylaprof import FS, S3

dummy_report = os.path.dirname(__file__) + "/dummy-report.txt"


def test_fs_init():
    path = lambda: "report.txt"

    fs = FS(path=path)

    assert fs.path == path


@freeze_time("2021-11-14T09:29:38.743604+00:00")
def test_fs_init_defaults():
    fs = FS()

    assert fs.path is not None
    assert fs.path() == "pylaprof-2021-11-14T09:29:38.743604+00:00.txt"


def test_fs_store(tmpcwd):
    path = lambda: "report.txt"
    fs = FS(path=path)

    with open(dummy_report, "rb") as fp:
        fs.store(fp)

    assert filecmp.cmp(dummy_report, path())


def test_s3_init(boto3_mock):
    s3_opts = {"region_name": "eu-central-1"}
    bucket = {"profiling"}
    key = lambda: "pylaprof-my-lambda.txt"
    put_object_opts = {"Metadata": {"some_key": "some_value"}}

    s3 = S3(s3_opts=s3_opts, bucket=bucket, key=key, put_object_opts=put_object_opts)

    boto3_mock.resource.assert_called_with("s3", **s3_opts)
    boto3_mock.resource().Bucket.assert_called_with(bucket)
    assert s3.bucket == boto3_mock.resource().Bucket()
    assert s3.key == key
    assert s3.put_object_opts == put_object_opts


@freeze_time("2021-11-14T09:29:38.743604+00:00")
def test_s3_init_defaults(monkeypatch, boto3_mock):
    dummy_uuid = "b749d67e-63ac-4242-b78f-ca28aa63d7b4"
    monkeypatch.setattr("uuid.uuid4", Mock(return_value=UUID(dummy_uuid)))

    s3 = S3()

    boto3_mock.resource.assert_called_with("s3")
    boto3_mock.resource().Bucket.assert_called_with("pylaprof")
    assert s3.bucket == boto3_mock.resource().Bucket()
    assert s3.key is not None
    assert s3.key() == f"{dummy_uuid[:8]}-2021-11-14T09:29:38.743604+00:00.txt"
    assert s3.put_object_opts == {}


def test_s3_store(boto3_mock):
    bucket = Mock()
    key = lambda: "pylaprof-42.txt"
    put_obj_opts = {"dummy_key": "dummy_value"}
    s3 = S3(key=key, put_object_opts=put_obj_opts)
    s3.bucket = bucket

    with open(dummy_report, "r") as fp:
        s3.store(fp)

        fp.seek(0)
        bucket.put_object.assert_called_with(Body=fp.read(), Key=key(), **put_obj_opts)
