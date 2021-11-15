import sys
import threading
from inspect import signature
from unittest.mock import MagicMock, Mock

from pylaprof import Profiler, profile


def test_profiler_init():
    period = 0.42
    single = False
    min_time = 60
    sampler = object()
    storer = object()

    profiler = Profiler(
        period=period, single=single, min_time=min_time, sampler=sampler, storer=storer
    )

    # Check instance attributes were correctly set
    assert profiler.period == period
    assert profiler._test is None  # None will signal to the profiler thread to setup a
    # test function that excludes itself.
    assert profiler.min_time == min_time
    assert profiler.sampler == sampler
    assert profiler.storer == storer
    assert profiler._can_run is False
    assert profiler.daemon is True
    assert profiler.clean_exit is False


def test_profiler_init_defaults(monkeypatch):
    s3_mock = Mock()
    monkeypatch.setattr("pylaprof.S3", s3_mock)
    stack_collapse_mock = Mock()
    monkeypatch.setattr("pylaprof.StackCollapse", stack_collapse_mock)

    profiler = Profiler()

    # Check that S3 and StackCollapses where instantiated with default args
    s3_mock.assert_called_with()
    stack_collapse_mock.assert_called_with()

    # Check instance attributes were correctly set
    assert profiler.period == 0.01
    assert profiler._test is not None
    assert profiler._test(threading.get_ident()) is True
    assert profiler.min_time == 0
    assert profiler.sampler == stack_collapse_mock()
    assert profiler.storer == s3_mock()
    assert profiler._can_run is False
    assert isinstance(profiler._stop_event, threading.Event)
    assert profiler.daemon is True
    assert profiler.clean_exit is False


def test_profiler_start(monkeypatch):
    monkeypatch.setattr(threading.Thread, "start", Mock())
    profiler = Profiler(storer=object(), sampler=object())

    profiler.start()

    assert profiler.clean_exit is False
    assert profiler._can_run is True
    threading.Thread.start.assert_called()


def test_profiler_stop():
    profiler = Profiler(storer=object(), sampler=object())
    profiler._can_run = True
    profiler._stop_event = Mock()

    profiler.stop()

    assert profiler._can_run is False
    profiler._stop_event.set.assert_called()


def test_profiler_context_manager():
    profiler = Profiler(sampler=object(), storer=object())
    profiler.start = Mock()
    profiler.stop = Mock()
    profiler.join = Mock()

    with profiler as p:
        assert p == profiler
        p.start.assert_called()
        p.stop.assert_not_called()
        p.join.assert_not_called()
    p.stop.assert_called()
    p.join.assert_called()


def test_profiler_run_pylaprof_disable(monkeypatch):
    """Check that if the `PYLAPROF_DISABLE` environment variable is set thread's
    execution is a noop."""
    monkeypatch.setenv("PYLAPROF_DISABLE", "true")
    profiler = Profiler(sampler=Mock(), storer=Mock())

    profiler.start()
    profiler.join(timeout=0.01)

    assert profiler.clean_exit is True
    profiler.sampler.sample.assert_not_called()
    profiler.storer.store.assert_not_called()


def test_profiler_run(monkeypatch):
    ident1 = "some_thread_ident"
    frame1 = "I'm supposed to be thread's uppermost stack frame"
    ident2 = "some_other_thread"
    frame2 = "like frame 1"
    current_frames = Mock(return_value={ident1: frame1, ident2: frame2})
    monkeypatch.setattr("sys._current_frames", current_frames)
    period = 0.01
    profiler = Profiler(period=period, sampler=Mock(), storer=Mock())
    profiler._test = Mock(side_effect=lambda ident: ident == ident1)
    profiler._stop_event = Mock()

    profiler.start()
    profiler.stop()
    profiler.join()

    profiler._test.assert_any_call(ident1)
    profiler._test.assert_any_call(ident2)
    sampler_calls = {args for args, _ in profiler.sampler.sample.call_args_list}
    assert (frame1,) in sampler_calls
    assert (frame2,) not in sampler_calls
    profiler._stop_event.wait.assert_called_with(period)
    profiler._stop_event.clear.assert_called()
    assert profiler.clean_exit is True


def test_profiler_run_single_false(monkeypatch):
    """In this case the profiler was instantiated with single=False we should pass to
    the sampler the frames of all threads except that of the profiler itself."""
    ident1 = "some_thread_ident"
    frame1 = "I'm supposed to be thread's uppermost stack frame"
    ident2 = "some_other_thread"
    frame2 = "like frame 1"
    current_frames = sys._current_frames

    def frames():
        # Frame of profiler's thread itself
        frames = {
            k: v for k, v in current_frames().items() if k == threading.get_ident()
        }

        # Inject our dummy frames
        frames[ident1] = frame1
        frames[ident2] = frame2
        return frames

    current_frames_mock = Mock(side_effect=frames)
    monkeypatch.setattr("sys._current_frames", current_frames_mock)
    profiler = Profiler(single=False, sampler=Mock(), storer=Mock())

    profiler.start()
    profiler.stop()
    profiler.join()

    sampler_calls = {args for args, _ in profiler.sampler.sample.call_args_list}
    assert {(frame1,), (frame2,)} == sampler_calls


def test_profiler_run_min_time(monkeypatch):
    """Check that we store sampler's report only if execution lasts more than
    `min_time` provided at instantiation.
    """
    mtime = Mock()
    monkeypatch.setattr("pylaprof.time", mtime)
    min_time = 10

    profiler = Profiler(min_time=min_time, sampler=Mock(), storer=Mock())
    mtime.time.return_value = 0
    profiler.start()
    mtime.time.return_value = 8  # end - start < min_time
    profiler.stop()
    profiler.join()
    profiler.sampler.sample.assert_called()  # We sampled some stack frames...
    profiler.sampler.dump.assert_not_called()  # ... but didn't store them.

    profiler = Profiler(min_time=min_time, sampler=Mock(), storer=Mock())
    mtime.time.return_value = 0
    profiler.start()
    mtime.time.return_value = 10  # end - start >= min_time
    profiler.stop()
    profiler.join()
    profiler.sampler.sample.assert_called()  # We sampled some stack frames...
    profiler.sampler.dump.assert_called()  # ... and stored them.


def test_profiler_run_exception(monkeypatch):
    """Check that in case of exception we don't let it bubble up and log it."""
    logger = Mock()
    monkeypatch.setattr("pylaprof.logger", logger)
    sampler = Mock()
    sampler.sample.side_effect = KeyError

    # We patch Profiler's run method to see if it raises an exception.
    run = Profiler.run
    raised_exc = []

    def patched_run(self):
        try:
            run(self)
        except Exception:
            raised_exc.append(True)

    monkeypatch.setattr(Profiler, "run", patched_run)

    profiler = Profiler(sampler=sampler, storer=object())
    profiler.start()
    profiler.stop()
    profiler.join()

    sampler.sample.assert_called()
    assert not raised_exc
    logger.exception.assert_called()
    assert profiler.clean_exit is False  # Allows users to understand that profiler's
    # execution failed.


def test_profiler_decorator(monkeypatch):
    period = 0.42
    single = False
    min_time = 60
    sampler = object()
    storer = object()
    pmock = MagicMock()
    monkeypatch.setattr("pylaprof.Profiler", pmock)
    exp_rvalue = "Hello world :)"

    @profile(
        period=period, single=single, min_time=min_time, sampler=sampler, storer=storer
    )
    def fun():
        return exp_rvalue

    rvalue = fun()

    assert rvalue == exp_rvalue
    pmock.assert_called_with(
        period=period, single=single, min_time=min_time, sampler=sampler, storer=storer
    )
    pmock().__enter__.assert_called()
    pmock().__exit__.assert_called()


def test_profiler_decorator_defaults():
    """Check that profiler's decorator API is the same as class' ones."""
    assert {
        k: v for k, v in signature(Profiler.__init__).parameters.items() if k != "self"
    } == signature(profile).parameters
