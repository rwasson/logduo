"""
test_system_helpers.py

testing modules: active_duo_registry, runtime_warning,  safe_console_print, run
"""
import pytest
from rich.panel import Panel

from logduo import Duo, run
from logduo.internals.engine.active_duo_registry import (
    _get_active_duo,
    _set_active_duo,
    _clear_active_duo,
)
from logduo.internals.engine.reset_session import _abort_setup_config, _reset_session
from logduo.internals.engine.runtime_classes import MessageKind
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.formatters.safe_console_print import _safe_console_print


# --- _new_test_log()
def _new_test_log(tmp_path):
    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )
    return log


# --- test_01_active_duo_registry() --------------------------------------------
def test_01_active_duo_registry():
    a = Duo()
    b = Duo()
    _clear_active_duo()

    assert _get_active_duo() is None

    _set_active_duo(a)
    assert _get_active_duo() is a
    _clear_active_duo(b)

    assert _get_active_duo() is a
    _clear_active_duo(a)

    assert _get_active_duo() is None


# --- test_02_runtime_warning_dedup() ------------------------------------------
def test_02_runtime_warning_dedup(tmp_path, capsys):
    log = _new_test_log(tmp_path)

    _runtime_warning(
        log,
        warn_msg="duplicate test",
    )

    _runtime_warning(
        log,
        warn_msg="duplicate test",
    )

    captured = capsys.readouterr()

    assert captured.out.count("duplicate test") == 1
    assert len(log._runtime.unique_warning_set) == 1

    assert "duplicate test" in log._runtime.unique_warning_set


# --- test_03_abort_setup_config() ---------------------------------------------
def test_03_abort_setup_config(tmp_path):
    log = Duo()

    log._initialized = True

    _abort_setup_config(log)

    assert log._initialized is False
    assert log.session_config == log._startup_config
    assert log._arg_source_record is not None


# --- test_04_reset_session() --------------------------------------------------
def test_04_reset_session(tmp_path):
    log = _new_test_log(tmp_path)

    assert log._initialized is True

    runtime_before = log._runtime

    _reset_session(log)

    assert log._initialized is False
    assert log.session_config == log._startup_config
    assert log._runtime is not runtime_before
    assert log._runtime.session_state == "initializing"



# --- test_05_reset_session_clears_active_registry() ---------------------------
def test_05_reset_session_clears_active_registry(tmp_path):
    log = _new_test_log(tmp_path)

    _set_active_duo(log)

    _reset_session(log)

    assert _get_active_duo() is None




# --- test_06_safe_console_print_string() --------------------------------------
def test_06_safe_console_print_string(tmp_path, capsys):
    log = _new_test_log(tmp_path)

    _safe_console_print(log, message="hello world", message_kind=MessageKind.INLINE)

    captured = capsys.readouterr()

    assert "hello world" in captured.out


# --- test_07_safe_console_print_renderable() ----------------------------------
def test_07_safe_console_print_renderable(tmp_path, capsys):
    log = _new_test_log(tmp_path)

    _safe_console_print(log, message=Panel("hello panel"), message_kind=MessageKind.RICH_RENDERABLE)

    captured = capsys.readouterr()

    assert "hello panel" in captured.out



# --- test_08_safe_console_print_no_console() ----------------------------------
def test_08_safe_console_print_no_console(tmp_path):
    log = Duo()

    log._console = None

    _safe_console_print(log, message="hello world", message_kind=MessageKind.INLINE)




# --- test_09_safe_console_print_non_string_object() ---------------------------
def test_09_safe_console_print_non_string_object(tmp_path, capsys):
    log = _new_test_log(tmp_path)

    _safe_console_print(
        log,
        message=tmp_path,
        message_kind=MessageKind.OBJECT
    )

    captured = capsys.readouterr()

    assert str(tmp_path) in captured.out



# --- test_10_safe_console_print_fallback_path() -------------------------------
def test_10_safe_console_print_fallback_path(
    tmp_path,
    monkeypatch,
    capsys,
):

    class BadObject:
        def __str__(self):
            return "bad"

    log = _new_test_log(tmp_path)

    calls = {"count": 0}

    def fake_print(*args, **kwargs):    # noqa intentional
        calls["count"] += 1
        raise RuntimeError("boom")

    monkeypatch.setattr(
        log._console,
        "print",
        fake_print,
    )

    _safe_console_print(
        log,
        message=BadObject(),
        message_kind=MessageKind.OBJECT,
    )

    captured = capsys.readouterr()

    assert calls["count"] == 1
    assert "bad" in captured.out


# --- test_11_safe_console_print_fallback_also_fails() ----------------------
def test_11_safe_console_print_fallback_also_fails(tmp_path, monkeypatch):
    log = _new_test_log(tmp_path)

    def always_fail(*args, **kwargs):     # noqa
        raise RuntimeError("boom")

    monkeypatch.setattr(
        log._console,
        "print",
        always_fail,
    )

    _safe_console_print(
        log,
        message="hello",
        message_kind=MessageKind.INLINE,
    )
