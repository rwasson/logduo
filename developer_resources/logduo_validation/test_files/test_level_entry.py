"""
test_level_entry.py

Tests:
    level_entry.py, user_sink_call_adapter.py

Last edited: 2026-06-11
"""

from __future__ import annotations

import pytest
from rich.text import Text

from logduo import Duo
from logduo.internals.engine.level_entry import (
    _build_traceback_text_box,
    _exception_entry,
    _filter_level_kwargs,
    _indent_traceback_lines,
    _level_entry,
    _raise_if_none,
)
from logduo.internals.engine.user_sink_call_adapter import UserSinkCallAdapter


# --- test_01_raise_if_none_no_prefix() ----------------------------------------
def test_01_raise_if_none_no_prefix():

    with pytest.raises(ValueError):
        _raise_if_none(
            no_prefix=None,         # noqa, intentional error
            log_wrap_width="off",
            console_style="blue",
        )


# --- test_02_raise_if_none_log_wrap_width() -----------------------------------
def test_02_raise_if_none_log_wrap_width():

    with pytest.raises(ValueError):
        _raise_if_none(
            no_prefix=False,
            log_wrap_width=None,        # noqa, intentional error
            console_style="blue",
        )


# --- test_03_raise_if_none_console_style() ------------------------------------
def test_03_raise_if_none_console_style():

    with pytest.raises(ValueError):
        _raise_if_none(
            no_prefix=False,
            log_wrap_width="off",
            console_style=None,             # noqa, intentional error
        )


# --- test_04_indent_traceback_lines() -----------------------------------------
def test_04_indent_traceback_lines():

    block = (
        'File "/tmp/test.py", line 123, in my_func\n'
        "    raise ValueError"
    )

    result = _indent_traceback_lines(block)

    assert 'File "/tmp/test.py"' in result
    assert "line 123, in my_func" in result


# --- test_05_build_traceback_text_box_dark_theme() ----------------------------
def test_05_build_traceback_text_box_dark_theme():

    result = _build_traceback_text_box(
        "hello",
        title="Traceback ValueError",
        theme="dark",
        width=80,
    )

    assert isinstance(result, Text)

    plain = result.plain

    assert "Traceback ValueError" in plain
    assert "hello" in plain
    assert "╭" in plain
    assert "╰" in plain


# --- test_06_build_traceback_text_box_light_theme() ---------------------------
def test_06_build_traceback_text_box_light_theme():

    result = _build_traceback_text_box(
        "hello",
        title="Traceback ValueError",
        theme="light",
        width=80,
    )

    assert isinstance(result, Text)
    assert "hello" in result.plain


# --- test_07_build_traceback_text_box_width_floor() ---------------------------
def test_07_build_traceback_text_box_width_floor():

    result = _build_traceback_text_box(
        "hello",
        title="Traceback",
        theme="dark",
        width=10,
    )

    assert isinstance(result, Text)


# --- test_08_build_traceback_text_box_width_ceiling() -------------------------
def test_08_build_traceback_text_box_width_ceiling():

    result = _build_traceback_text_box(
        "hello",
        title="Traceback",
        theme="dark",
        width=500,
    )

    assert isinstance(result, Text)


# --- test_09_level_entry_system_sink_raises() ---------------------------------
def test_09_level_entry_system_sink_raises():

    log = Duo()

    with pytest.raises(RuntimeError):

        _level_entry(
            log,
            "hello",
            level="INFO",
            sink_name="system",
        )


# --- test_10_filter_level_kwargs_clears_kwargs() ------------------------------
def test_10_filter_level_kwargs_clears_kwargs(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    kwargs = {
        "banana": True,
        "apple": 123,
    }

    _filter_level_kwargs(
        log,
        label="INFO",
        kwargs=kwargs,
    )

    assert kwargs == {}


# --- test_11_exception_entry_no_active_exception() ----------------------------
def test_11_exception_entry_no_active_exception(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    _exception_entry(log)


# --- test_12_exception_entry_active_exception() -------------------------------
def test_12_exception_entry_active_exception(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_verbosity=3,
        console_verbosity=3,
    )

    try:
        raise ValueError("boom")

    except ValueError:
        _exception_entry(
            log,
            "testing exception",
        )

    log.close()


# --- test_13_level_entry_default_sink_name() ---------------------------------
def test_13_level_entry_default_sink_name(tmp_path, monkeypatch):

    captured = {}

    def fake_dispatch_event(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.level_entry._dispatch_event",
        fake_dispatch_event,
    )

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    _level_entry(
        log,
        "hello",
        level="INFO",
    )

    print("")
    print("***********************************")
    print("test_13_level_entry_default_sink_name")
    print("captured")
    print(captured)

    assert captured["sink_name"] == "main_sink"


# --- test_14_level_entry_normalizes_level_and_label() ------------------------
def test_14_level_entry_normalizes_level_and_label(tmp_path, monkeypatch):

    captured = {}

    def fake_dispatch_event(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.level_entry._dispatch_event",
        fake_dispatch_event,
    )

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    _level_entry(
        log,
        "hello",
        level="warning",
        label="tip",
    )

    assert captured["level"] == "WARNING"
    assert captured["label"] == "TIP"


# --- test_15_level_entry_defaults_label_to_level() ---------------------------
def test_15_level_entry_defaults_label_to_level(tmp_path, monkeypatch):

    captured = {}

    def fake_dispatch_event(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.level_entry._dispatch_event",
        fake_dispatch_event,
    )

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    _level_entry(
        log,
        "hello",
        level="warning",
    )

    assert captured["label"] == "WARNING"


# --- test_16_level_entry_preserves_raw_call_args() ---------------------------
def test_16_level_entry_preserves_raw_call_args(tmp_path, monkeypatch):

    captured = {}

    def fake_dispatch_event(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.level_entry._dispatch_event",
        fake_dispatch_event,
    )

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    _level_entry(
        log,
        "hello",
        level="INFO",
        no_prefix=True,
        log_wrap_width=123,
        console_style="red",
    )

    call_args = captured["call_args"]

    assert call_args["no_prefix"] is True
    assert call_args["log_wrap_width"] == 123
    assert call_args["console_style"] == "red"


# --- test_17_level_entry_forwards_event_metadata() ---------------------------
def test_17_level_entry_forwards_event_metadata(tmp_path, monkeypatch):

    captured = {}

    def fake_dispatch_event(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.level_entry._dispatch_event",
        fake_dispatch_event,
    )

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    _level_entry(
        log,
        "hello",
        level="INFO",
        event_type="system_warning",
        warn_key="abc",
    )

    assert captured["event_type"] == "system_warning"
    assert captured["warn_key"] == "abc"


# --- test_18_level_entry_unknown_kwargs_warn() -------------------------------
def test_18_level_entry_unknown_kwargs_warn(tmp_path, monkeypatch):

    calls = []
    captured = {}


    def fake_runtime_warning(*args, **kwargs):
        captured["args"] = args
        calls.append((args, kwargs))

    monkeypatch.setattr(
        "logduo.internals.engine.level_entry._runtime_warning",
        fake_runtime_warning,
    )

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    _level_entry(
        log,
        "hello",
        level="INFO",
        banana=True,
    )

    assert len(calls) == 1


# --- test_19_user_sink_call_routes_to_info() ---------------------------------
def test_19_user_sink_call_routes_to_info(monkeypatch):

    captured = {}

    def fake_level_entry(*args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.user_sink_call_adapter._level_entry",
        fake_level_entry,
    )

    log = Duo()

    adapter = UserSinkCallAdapter(
        log,
        sink_name="audit",
    )

    adapter("hello")

    assert captured["level"] == "INFO"
    assert captured["label"] == "INFO"
    assert captured["sink_name"] == "audit"


# --- test_20_user_sink_warning_routes_correctly() ----------------------------
def test_20_user_sink_warning_routes_correctly(monkeypatch):

    captured = {}

    def fake_level_entry(*args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.user_sink_call_adapter._level_entry",
        fake_level_entry,
    )

    log = Duo()

    adapter = UserSinkCallAdapter(
        log,
        sink_name="audit",
    )

    adapter.warning("hello")

    assert captured["level"] == "WARNING"
    assert captured["label"] == "WARNING"
    assert captured["sink_name"] == "audit"


# --- test_21_user_sink_exception_routes_correctly() --------------------------
def test_21_user_sink_exception_routes_correctly(monkeypatch):

    captured = {}

    def fake_exception_entry(*args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.user_sink_call_adapter._exception_entry",
        fake_exception_entry,
    )

    log = Duo()

    adapter = UserSinkCallAdapter(
        log,
        sink_name="audit",
    )

    adapter.exception("boom")

    assert captured["message"] == "boom"
    assert captured["sink_name"] == "audit"


# --- test_22_user_sink_custom_label_dispatch() -------------------------------
def test_22_user_sink_custom_label_dispatch(monkeypatch):

    captured = {}

    def fake_level_entry(*args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.user_sink_call_adapter._level_entry",
        fake_level_entry,
    )

    log = Duo()

    log._runtime.new_levels["tip"] = (
        "TIP",
        "blue",
        "INFO",
    )

    adapter = UserSinkCallAdapter(
        log,
        sink_name="audit",
    )

    adapter.tip("hello")

    assert captured["level"] == "INFO"
    assert captured["label"] == "TIP"
    assert captured["sink_name"] == "audit"


# --- test_23_user_sink_bad_custom_label_tuple_raises() -----------------------
def test_23_user_sink_bad_custom_label_tuple_raises():

    log = Duo()

    log._runtime.new_levels["tip"] = ("TIP",) # noqa intionally invalid tuple

    adapter = UserSinkCallAdapter(
        log,
        sink_name="audit",
    )

    with pytest.raises(RuntimeError):
        adapter.tip("hello")


# --- test_24_user_sink_unknown_method_fallback() -----------------------------
def test_24_user_sink_unknown_method_fallback(monkeypatch):

    captured = {}

    def fake_level_entry(*args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.user_sink_call_adapter._level_entry",
        fake_level_entry,
    )

    log = Duo()

    adapter = UserSinkCallAdapter(
        log,
        sink_name="audit",
    )

    adapter.audit("hello")

    assert captured["level"] == "AUDIT"
    assert captured["label"] == "AUDIT"
    assert captured["sink_name"] == "audit"


# --- test_25_user_sink_debug_routes_correctly() ------------------------------
def test_25_user_sink_debug_routes_correctly(monkeypatch):
    captured = {}

    def fake_level_entry(*args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "logduo.internals.engine.user_sink_call_adapter._level_entry",
        fake_level_entry,
    )

    log = Duo()
    adapter = UserSinkCallAdapter(
        log,
        sink_name="audit",
    )

    adapter.debug("hello")

    assert captured["level"] == "DEBUG"
    assert captured["label"] == "DEBUG"
    assert captured["sink_name"] == "audit"


# --- test_26_exception_entry_emits_error_and_traceback() ---------------------
def test_26_exception_entry_emits_error_and_traceback(tmp_path, monkeypatch):
    calls = []


    def fake_level_entry(*args, **kwargs):
        calls.append({
            "args": args,
            "kwargs": kwargs,
        })

    monkeypatch.setattr(
        "logduo.internals.engine.level_entry._level_entry",
        fake_level_entry,
    )

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    try:
        raise ValueError("boom")
    except ValueError:
        _exception_entry(
            log,
            "testing exception",
        )

    print(calls)
    assert len(calls) == 2
    assert calls[0]["kwargs"]["level"] == "ERROR"
    assert calls[1]["kwargs"]["level"] == "ERROR"
    assert isinstance(
        calls[1]["args"][1],
        Text,
    )
