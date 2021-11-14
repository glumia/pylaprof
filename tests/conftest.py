import os
import tempfile
from unittest.mock import Mock

import pytest


@pytest.fixture
def tmpcwd():
    """Run test in a temporary directory."""
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory(prefix="pylaprof-test") as tmpdir:
        os.chdir(tmpdir)
        yield
    os.chdir(cwd)


@pytest.fixture
def boto3_mock(monkeypatch):
    """Monkeypatch pylaprof's boto3 module."""
    mock = Mock()
    monkeypatch.setattr("pylaprof.boto3", mock)
    return mock
