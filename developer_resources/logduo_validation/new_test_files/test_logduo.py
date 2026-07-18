"""
test_logduo.py

Last edited: 2026-06-13
"""

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

from developer_resources.logduo_validation.pytest_files.pytest_helpers.file_helpers import (
    _find_main_log,
    _read_file,
)
from logduo.internals.formatters.safe_console_print import _safe_chars
from logduo.logduo import Duo

logduo_module = importlib.import_module("logduo.logduo")

# --- test_01_duo_initial_state() ---------------------------------------------
def test_01_duo_initial_state(tmp_path):

    log = Duo()

    assert log.initialized is False
    assert log.session_config == log._startup_config
    assert log.output_dir_path is None

    log.configure(log_dir_path=str(tmp_path))

    assert log.initialized is True
    assert log.session_config != log._startup_config
    assert log.output_dir_path is not None
    log.close()


# --- test_02_output_dir_path_after_configure() -------------------------------
def test_02_output_dir_path_after_configure(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    assert log.output_dir_path is not None
    assert log.output_dir_path.exists()
    log.close()


# --- test_03_join_without_active_session_raises() ----------------------------
def test_03_join_without_active_session_raises(monkeypatch):

    monkeypatch.setattr(
        logduo_module,
        "_get_active_duo",
        lambda: None,
    )

    with pytest.raises(RuntimeError):
        Duo().join()



# --- test_04_unknown_attribute_raises() --------------------------------------
def test_04_unknown_attribute_raises():

    log = Duo()

    with pytest.raises(AttributeError) as exc:
        log.this_does_not_exist             # noqa

    assert "Unknown Logduo method or attribute" in str(exc.value)


# --- test_05_getattr_standard_level_returns_callable() -----------------------
def test_05_getattr_standard_level_returns_callable():

    log = Duo()

    fn = getattr(log, "info")

    assert callable(fn)


# --- test_06_new_level_registers_label() -------------------------------------
def test_06_new_level_registers_label(tmp_path):

    log = Duo()
    log.configure(log_dir_path=tmp_path)

    log.new_level(
        "NOTE",
        console_style="purple",
    )

    assert "note" in log._runtime.new_levels
    log.close()

# --- test_07_custom_label_resolves_via_getattr() -----------------------------
def test_07_custom_label_resolves_via_getattr(tmp_path):

    log = Duo()
    log.configure(log_dir_path=tmp_path)

    log.new_level(
        "NOTE",
        console_style="purple",
    )

    fn = getattr(log, "note")

    assert callable(fn)
    log.close()


# --- test_08_register_close_on_exit_idempotent() -----------------------------
def test_08_register_close_on_exit_idempotent(tmp_path):

    log = Duo()


    print(_safe_chars(" "))
    print(_safe_chars("******************************************"))
    print(_safe_chars("test_08_register_close_on_exit_idempotent"))
    print(_safe_chars(" "))
    print(_safe_chars("check 1: before initialized, before log.configure)): "))
    print(_safe_chars(f"expect: log._atexit_registered =  False (actual = {log._atexit_registered}) "))
    assert log._initialized is False
    assert log._atexit_registered is False

    log.configure(log_dir_path=str(tmp_path))
    print(_safe_chars("check 2: right after log.configure(): "))
    print(_safe_chars(f"expect: log._atexit_registered =  True (actual = {log._atexit_registered}) "))
    assert log._initialized is True
    assert log._atexit_registered is True

    log._register_close_on_exit()
    print(_safe_chars(" "))
    print(_safe_chars("check 3: right after log._register_close_on_exit(): "))
    print(_safe_chars(f"expect: log._atexit_registered = True (actual = {log._atexit_registered})"))
    assert log._atexit_registered is True


    log._register_close_on_exit()
    print(_safe_chars(" "))
    print(_safe_chars("check 4: idempotent: right after 2nd log._register_close_on_exit(): "))
    print(_safe_chars(f"expect: log._atexit_registered = True (actual = {log._atexit_registered})"))
    print(_safe_chars("Do not expect to see print(_safe_chars for check 5, after log.close()"))
    assert log._atexit_registered is True

    log.close()
    print(_safe_chars(" "))
    print(_safe_chars("check 5: right after log.close(): "))
    print(_safe_chars(f"expect: log._atexit_registered = True (actual = {log._atexit_registered})"))
    print(_safe_chars("******************************************"))
    assert log._atexit_registered is True



# --- test_09_refresh_pid_assigns_runtime_values() ----------------------------
def test_09_refresh_pid_assigns_runtime_values(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    log._refresh_pid()

    assert log._runtime.pid is not None
    assert log._runtime.instance_index is not None
    log.close()


# --- test_10_configure_second_call_warns_once() ------------------------------
def test_10_configure_second_call_warns_once(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    assert log._warned_already_configured is False

    log.configure()
    log.configure()

    assert log._warned_already_configured is True
    log.close()


# --- test_11_call_defaults_to_info() -----------------------------------------
def test_11_call_defaults_to_info(tmp_path):
    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        console_verbosity=0,
    )

    log("hello")
    log_path = log.main_log_file_path
    assert log_path is not None
    log.close()

    text = log_path.read_text(encoding="utf-8")
    print(_safe_chars(""))
    print(_safe_chars("********************************"))
    print(_safe_chars("test_11_call_defaults_to_info"))
    print(_safe_chars("log file content:"))
    print(_safe_chars(text))
    print(_safe_chars("********************************"))

    assert "session.log" in text
    assert "INFO" in text
    assert "hello" in text


# --- test_12_critical_bypasses_console_verbosity_zero() -----------------------
def test_12_critical_bypasses_console_verbosity_zero(tmp_path, capsys):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path), console_verbosity=0)

    log("hello before log.critical('boom')")
    log.critical("boom")
    log("hello after log.critical('boom')")

    # trigger an internal warning that should display on console,
    # even if console_verbosity = 0
    log.new_loguru_sink(
        "new_loguru_sink.log",
        bad_kwarg=True,
    )

    log.close()

    captured = capsys.readouterr()
    console_output = captured.out

    log_file = _find_main_log(tmp_path)
    log_text = _read_file(log_file)

    print(_safe_chars(" "))
    print(_safe_chars("******************************"))
    print(_safe_chars("test_12_critical_bypasses_console_verbosity_zero"))
    print(_safe_chars("console output:"))
    print(_safe_chars(console_output))
    print(_safe_chars(" "))
    print(_safe_chars("log file content:"))
    print(_safe_chars(log_text))
    print(_safe_chars("******************************"))

    print('assert "CRITICAL" in log_text')
    assert "CRITICAL" in log_text

    print('assert "boom" in log_text')
    assert "boom" in log_text

    print('assert "Ignored invalid loguru kwargs" in log_text')
    assert "Ignored invalid loguru kwargs" in log_text

    print('assert "hello" not in console_output')
    assert "hello" not in console_output

    print(' assert "CRITICAL" not in console_output')
    assert "CRITICAL" not in console_output

    print('assert "boom" not in console_output')
    assert "boom" not in console_output

    print('assert "Ignored invalid loguru kwargs" in console_output')
    assert "Ignored invalid loguru kwargs" in console_output



# --- test_13_internal_error_visible_to_user() ------------------------------------
def test_13_internal_error_visible_to_user(tmp_path):

    script_path = Path(
        __file__).parent.parent / "pytest_files" / "pytest_helpers" / "script_raise.py"

    print(_safe_chars(" "))
    print(_safe_chars("********************************"))
    print(_safe_chars("test_13_internal_error_visible_to_user"))
    print(_safe_chars("script_path:"))
    print(_safe_chars(script_path))

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    print(_safe_chars("output:"))
    print(_safe_chars(output))
    print(_safe_chars("********************************"))
    print(_safe_chars("test_13_internal_error_visible_to_user"))


    assert result.returncode != 0
    assert "LOGDUO INTERNAL ERROR: test invariant failure" in output


# --- test_14_custom_label_written() ------------------------------------------
def test_14_custom_label_written(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        console_verbosity=0,
    )

    log.new_level(
        "NOTE",
        console_style="purple",
        level="WARNING",

    )

    assert log._runtime.new_levels["note"] == (
        "NOTE",
        "purple",
        "WARNING",
    )

    log.note("hello")
    log_path = log._runtime.main_sink_log_file_path_abs
    assert log_path is not None

    log.close()

    text = log_path.read_text(encoding="utf-8")

    print(_safe_chars(""))
    print(_safe_chars("************************************************"))
    print(_safe_chars("test_14_custom_label_written"))
    print(_safe_chars(f"log path: {log_path}"))
    print(_safe_chars(f"exists: {log_path.exists()}"))
    print(_safe_chars("log contents:"))
    print(_safe_chars(repr(text)))
    print(_safe_chars("************************************************"))
    assert "NOTE" in text
    assert "hello" in text


# --- test_15_unknown_attribute_help_text() -----------------------------------
def test_15_unknown_attribute_help_text(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    with pytest.raises(AttributeError) as exc:
        log.banana                                    # noqa, intentional error

    msg = str(exc.value)

    assert "configure()" in msg
    assert "new_logger()" in msg
    assert "For help:" in msg
    log.close()


# --- test_16_output_dir_path_matches_runtime() -------------------------------
def test_16_output_dir_path_matches_runtime(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    assert (
        log.output_dir_path
        == log._runtime.main_sink_log_dir_path_abs
    )
    log.close()



# --- test_17_register_close_on_exit_only_once() ------------------------------
def test_17_register_close_on_exit_only_once(monkeypatch):

    calls = []

    def fake_register(*args, **kwargs):  # noqa
        calls.append(True)

    monkeypatch.setattr(
        logduo_module.atexit,
        "register",
        fake_register,

    )

    log = Duo()

    log._register_close_on_exit()
    log._register_close_on_exit()

    assert len(calls) == 1


# --- test_18_join_returns_active_duo() ----------------------------------------
def test_18_join_returns_active_duo(monkeypatch):

    active_log = Duo()

    monkeypatch.setattr(
        logduo_module,
        "_get_active_duo",
        lambda: active_log,
    )

    result = Duo().join()

    assert result is active_log


# --- test_19_call_rejects_extra_positional_arguments() ------------------------
def test_19_call_rejects_extra_positional_arguments():

    log = Duo()

    with pytest.raises(
        TypeError,
        match="single positional message argument",
    ):
        log("hello", "extra")


# --- test_20_main_log_file_path_matches_runtime(tmp_path) ---------------------
def test_20_main_log_file_path_matches_runtime(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        log_file_layout="script",
    )

    assert (
        log.main_log_file_path
        == log._runtime.main_sink_log_file_path_abs
    )
    assert log.main_log_file_path is not None
    assert log.main_log_file_path.exists()
    log.close()


# --- test_21_explicit_level_methods_write_expected_labels() ------------------
def test_21_explicit_level_methods_write_expected_labels(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        log_file_layout="script",
        console_verbosity=0,
        log_verbosity=3,
    )

    log.critical("critical message")
    log.error("error message")
    log.warning("warning message")
    log.success("success message")
    log.info("info message")
    log.debug("debug message")
    log.trace("trace message")

    log.close()

    log_text = _read_file(_find_main_log(tmp_path))

    print(_safe_chars(""))
    print(_safe_chars("************************************************"))
    print(_safe_chars("test_21_explicit_level_methods_write_expected_labels"))
    print(_safe_chars("log_text:"))
    print(_safe_chars(log_text))
    print(_safe_chars("************************************************"))

    assert "CRITICAL" in log_text
    assert "critical message" in log_text

    assert "ERROR" in log_text
    assert "error message" in log_text

    assert "WARNING" in log_text
    assert "warning message" in log_text

    assert "SUCCESS" in log_text
    assert "success message" in log_text

    assert "INFO" in log_text
    assert "info message" in log_text

    assert "DEBUG" in log_text
    assert "debug message" in log_text

    assert "TRACE" in log_text
    assert "trace message" in log_text



# --- test_22_invalid_custom_level_registry_entry_raises() --------------------
def test_22_invalid_custom_level_registry_entry_raises(tmp_path):
    log = Duo()
    log.configure(log_dir_path=tmp_path)

    try:
        log._runtime.new_levels["broken"] = (
            "invalid",
        )  # type: ignore[assignment]
        with pytest.raises(
            RuntimeError,
            match="Invalid new_levels entry",
        ):
            getattr(log, "broken")

    finally:
        log.close()


# --- test_23_refresh_pid_after_pid_change() -----------------------------------
def test_23_refresh_pid_after_pid_change(monkeypatch):

    log = Duo()
    log._runtime.pid = -1

    monkeypatch.setattr(
        logduo_module.os,
        "getpid",
        lambda: 123456,
    )

    log._refresh_pid()

    assert log._runtime.pid == 123456
    assert log._runtime.instance_index >= 1



