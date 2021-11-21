from collections import defaultdict
from unittest.mock import Mock

from pylaprof import StackCollapse


def test_stack_collapse_init():
    stack_collapse = StackCollapse()

    assert isinstance(stack_collapse._data, defaultdict)
    assert stack_collapse._data["some_key"] == 0


def test_stack_collapse_sample():
    """Check that frames are recorded in a way that allows us to build a stackcollapse
    later on when `dump` is called."""
    file_i = "some_path/some_module.py"  # innermost frame
    func_i = "some_func"
    lineno_i = 4
    frame_i = Mock(
        f_code=Mock(
            co_filename=file_i,
            co_name=func_i,
        ),
        f_lineno=lineno_i,
        f_back=None,
    )
    file_m = "some_other_path/some_other_module.py"  # middle frame
    func_m = "some_other_func"
    lineno_m = 2
    frame_m = Mock(
        f_code=Mock(
            co_filename=file_m,
            co_name=func_m,
        ),
        f_lineno=lineno_m,
        f_back=frame_i,
    )
    file_o = "yet_another_path/yet_another_module.py"  # outermost frame
    func_o = "yet_another_func"
    lineno_o = 42
    frame_o = Mock(
        f_code=Mock(
            co_filename=file_o,
            co_name=func_o,
        ),
        f_lineno=lineno_o,
        f_back=frame_m,
    )
    stack_collapse = StackCollapse()

    stack_collapse.sample(frame_o)

    fmt = lambda file, func, lineno: f"{func} ({file}:{lineno})"
    key = (
        fmt(file_o, func_o, lineno_o),
        fmt(file_m, func_m, lineno_m),
        fmt(file_i, func_i, lineno_i),
    )
    assert key in stack_collapse._data
    assert stack_collapse._data[key] == 1

    # Let's see if the hit counter is correctly incremented
    stack_collapse.sample(frame_o)
    assert stack_collapse._data[key] == 2


def test_stack_collapse_dump():
    """Check that the storer is correctly called and that data in `_data` is correctly
    formatted."""
    stack_collapse = StackCollapse()
    stack_collapse._data[
        (
            "one (some_path/some_module.py:12)",
            "three (some_path/some_module.py:42)",
        )
    ] = 4
    stack_collapse._data[
        (
            "some_func (some_path/some_other_module.py:11)",
            "three_v2 (some_path/some_module.py:82)",
        )
    ] = 2
    exp_file = (
        "three (some_path/some_module.py:42);one (some_path/some_module.py:12) 4\n"
        + "three_v2 (some_path/some_module.py:82);some_func (some_path/some_other_module.py:11) 2\n"  # noqa
    ).encode()
    storer = Mock()

    stack_collapse.dump(storer=storer)

    storer.store.assert_called()
    args, _ = storer.store.call_args_list[0]
    assert args[0].read() == exp_file
