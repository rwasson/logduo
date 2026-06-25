"""
test_logduo.py

Last edited: 2026-06-13
"""

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

from developer_resources.pytest_toolkit.test_utils import (
    _find_main_log,
    _read_file,
)
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


# --- test_02_output_dir_path_after_configure() -------------------------------
def test_02_output_dir_path_after_configure(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    assert log.output_dir_path is not None
    assert log.output_dir_path.exists()


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


# --- test_08_register_close_on_exit_idempotent() -----------------------------
def test_08_register_close_on_exit_idempotent(tmp_path):

    log = Duo()


    print(" ")
    print("******************************************")
    print("test_08_register_close_on_exit_idempotent")
    print(" ")
    print("check 1: before initialized, before log.configure(): ")
    print(f"expect: log._atexit_registered =  False (actual = {log._atexit_registered}) ")
    assert log._initialized is False
    assert log._atexit_registered is False

    log.configure(log_dir_path=str(tmp_path))
    print("check 2: right after log.configure(): ")
    print(f"expect: log._atexit_registered =  True (actual = {log._atexit_registered}) ")
    assert log._initialized is True
    assert log._atexit_registered is True

    log._register_close_on_exit()
    print(" ")
    print("check 3: right after log._register_close_on_exit(): ")
    print(f"expect: log._atexit_registered = True (actual = {log._atexit_registered})")
    assert log._atexit_registered is True


    log._register_close_on_exit()
    print(" ")
    print("check 4: idempotent: right after 2nd log._register_close_on_exit(): ")
    print(f"expect: log._atexit_registered = True (actual = {log._atexit_registered})")
    print("Do not expect to see prints for check 5, after log.close()")
    assert log._atexit_registered is True

    log.close()
    print(" ")
    print("check 5: right after log.close(): ")
    print(f"expect: log._atexit_registered = True (actual = {log._atexit_registered})")
    print("******************************************")
    assert log._atexit_registered is True



# --- test_09_refresh_pid_assigns_runtime_values() ----------------------------
def test_09_refresh_pid_assigns_runtime_values(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    log._refresh_pid()

    assert log._runtime.pid is not None
    assert log._runtime.instance_index is not None


# --- test_10_configure_second_call_warns_once() ------------------------------
def test_10_configure_second_call_warns_once(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    assert log._warned_already_configured is False

    log.configure()
    log.configure()

    assert log._warned_already_configured is True


# --- test_11_call_routes_to_info() -------------------------------------------
def test_11_call_defaults_to_info(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path), console_verbosity=0)

    log("hello")
    text = log._runtime.main_sink_log_file_path_abs.read_text()
    print("")
    print("********************************")
    print("test_11_call_defaults_to_info")
    print("log file content:")
    print(text)
    print(" ")

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

    print(" ")
    print("******************************")
    print("test_12_critical_bypasses_console_verbosity_zero")
    print("console output:")
    print(console_output)
    print(" ")
    print("log file content:")
    print(log_text)
    print("******************************")

    assert "CRITICAL" in log_text
    assert "boom" in log_text
    assert "Ignored invalid loguru kwargs" in log_text

    assert "hello" not in console_output
    assert "CRITICAL" not in console_output
    assert "boom" not in console_output
    assert "Ignored invalid loguru kwargs" in console_output



# --- test_13_internal_error_visible_to_user() ------------------------------------
def test_13_internal_error_visible_to_user(tmp_path):

    script_path = Path(
        __file__).parent.parent / "test_files" / "test_helper_files" / "script_raise.py"

    print(" ")
    print("********************************")
    print("test_14_internal_error_visible_to_user")
    print("script_path:")
    print(script_path)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    print("output:")
    print(output)
    print("********************************")
    print("test_13_internal_error_visible_to_user")


    assert result.returncode != 0
    assert "LOGDUO INTERNAL ERROR: test invariant failure" in output


# --- test_14_custom_label_routes_correct_level() -----------------------------
def test_14_custom_label_written(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        console_verbosity=0,
    )

    log.new_level(
        "NOTE",
        console_style="purple",
        level="WARNING",
    )

    log.note("hello")
    text = log._runtime.main_sink_log_file_path_abs.read_text()

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


# --- test_16_output_dir_path_matches_runtime() -------------------------------
def test_16_output_dir_path_matches_runtime(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    assert (
        log.output_dir_path
        == log._runtime.main_sink_log_dir_path_abs
    )




# --- test_17_register_close_on_exit_only_once() ------------------------------
def test_17_register_close_on_exit_only_once(monkeypatch):

    calls = []

    def fake_register(*args, **kwargs):
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
