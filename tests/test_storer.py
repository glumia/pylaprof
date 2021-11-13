from pylaprof import FS


def test_fs_init():
    custom_path = "my-report.txt"
    fs = FS(path=custom_path)

    assert fs.path == custom_path
