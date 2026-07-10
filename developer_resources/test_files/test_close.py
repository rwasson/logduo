"""
test_close.py

test file: close_session.py

Last edited: 2026-06-12
"""


from datetime import datetime, timedelta

from developer_resources.pytest_toolkit.test_utils import (
    _find_main_log,
    _new_test_log,
    _read_file,
)
from logduo import Duo
from logduo.internals.engine.close_session import (
    _close_session,
    _finalize_timing,
)
from logduo.internals.engine.runtime_classes import RuntimeRecord


# --- test_01_close_writes_main_log_footer() ----------------------------------
def test_01_close_writes_main_log_footer(tmp_path):

    log = _new_test_log(tmp_path)

    log("hello")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "logging ended" in content


# --- test_02_close_writes_user_sink_footer() ---------------------------------
def test_02_close_writes_user_sink_footer(tmp_path):
    log = _new_test_log(tmp_path)

    rep = log.new_logger("audit")

    rep("hello")
    log.close()

    content = _read_file(tmp_path / "session" / "audit.log")

    assert "logging ended" in content


# --- test_03_close_resets_initialized_state() --------------------------------
def test_03_close_resets_initialized_state(tmp_path):
    log = _new_test_log(tmp_path)

    assert log._initialized is True

    log.close()

    assert log._initialized is False


# --- test_04_close_is_idempotent() -------------------------------------------
def test_04_close_is_idempotent(tmp_path):
    log = _new_test_log(tmp_path)

    log.close()
    log.close()


# --- test_05_close_uninitialized_session() -----------------------------------
def test_05_close_uninitialized_session():

    log = Duo()

    log.close()


# --- test_06_close_records_duration() ----------------------------------------
def test_06_close_records_duration(tmp_path):
    log = _new_test_log(tmp_path)

    runtime = log._runtime

    log.close()

    assert runtime.end_time is not None
    assert runtime.duration_display is not None


# --- test_07_close_footer_lists_created_files() ------------------------------
def test_07_close_footer_lists_created_files(tmp_path):
    log = _new_test_log(tmp_path)

    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "Logduo-managed files created this run" in content


# --- test_08_close_respects_log_verbosity_zero() -----------------------------
def test_08_close_respects_log_verbosity_zero(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        log_verbosity=0,
    )

    log("hello")
    log.close()

    assert not (tmp_path / "session" / "session.log").exists()


# --- test_09_close_sets_closing_state() --------------------------------------
def test_09_close_sets_closing_state(tmp_path):
    log = _new_test_log(tmp_path)

    print(" ")
    print("**************************************")
    print("test_09_close_sets_closing_state")
    print(f"log._runtime.session_state: {log._runtime.session_state}")
    print("log._runtime before close:")
    print(f"log._runtime.session_state: {log._runtime.session_state}")


    log.close()
    print(" ")
    print("log._runtime after close:")
    print(f"log._runtime.session_state: {log._runtime.session_state}")



    assert log._runtime.session_state == "initializing"


# --- test_10_close_preserves_user_sink_until_footer() ------------------------
def test_10_close_preserves_user_sink_until_footer(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
    )

    rep = log.new_logger("audit")

    rep("hello")
    log.close()

    content = _read_file(tmp_path / "session" / "audit.log")

    assert "hello" in content
    assert "logging ended" in content


# --- test_11_finalize_timing_seconds_only() ----------------------------------
def test_11_finalize_timing_seconds_only():

    runtime = RuntimeRecord()

    runtime.start_time = datetime.now() - timedelta(seconds=10)

    _finalize_timing(runtime)

    assert runtime.duration_seconds == 10
    assert runtime.duration_display == "10 sec"


# --- test_12_finalize_timing_minutes() ---------------------------------------
def test_12_finalize_timing_minutes():

    runtime = RuntimeRecord()

    runtime.start_time = datetime.now() - timedelta(seconds=65)

    _finalize_timing(runtime)

    assert runtime.duration_seconds == 65
    assert runtime.duration_display == "01:05 min:sec"


# --- test_13_finalize_timing_hours() -----------------------------------------
def test_13_finalize_timing_hours():

    runtime = RuntimeRecord()

    runtime.start_time = datetime.now() - timedelta(seconds=3665)

    _finalize_timing(runtime)

    assert runtime.duration_seconds == 3665
    assert runtime.duration_display == "01:01:05 hr:min:sec"


# --- test_14_user_sink_end_failure_printed() ---------------------------------
def test_14_user_sink_end_failure_printed(
    tmp_path,
    monkeypatch,
    capsys,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
    )

    def boom(*args, **kwargs):
        raise RuntimeError("forced failure")

    monkeypatch.setattr(
        "logduo.internals.engine.close_session._emit_user_sink_end",
        boom,
    )

    _close_session(log)

    err = capsys.readouterr().err

    assert "_emit_user_sink_end crashed unexpectedly" in err
    assert "forced failure" in err


# --- test_15_main_sink_end_failure_printed() ---------------------------------
def test_15_main_sink_end_failure_printed(
    tmp_path,
    monkeypatch,
    capsys,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
    )

    def boom(*args, **kwargs):
        raise RuntimeError("forced failure")

    monkeypatch.setattr(
        "logduo.internals.engine.close_session._emit_main_sink_log_end",
        boom,
    )

    _close_session(log)

    err = capsys.readouterr().err

    assert "_emit_main_sink_log_end failed" in err
    assert "forced failure" in err


# --- test_16_console_end_failure_printed() -----------------------------------
def test_16_console_end_failure_printed(
    tmp_path,
    monkeypatch,
    capsys,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
    )

    def boom(*args, **kwargs):
        raise RuntimeError("forced failure")

    monkeypatch.setattr(
        "logduo.internals.engine.close_session._emit_console_end",
        boom,
    )

    _close_session(log)

    err = capsys.readouterr().err

    assert "_emit_console_end failed" in err
    assert "forced failure" in err


# --- test_17_jsonl_end_failure_printed() -------------------------------------
def test_17_jsonl_end_failure_printed(
    tmp_path,
    monkeypatch,
    capsys,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        write_jsonl=True,
    )

    def boom(*args, **kwargs):
        raise RuntimeError("forced failure")

    monkeypatch.setattr(
        "logduo.internals.engine.close_session._emit_jsonl_end",
        boom,
    )

    _close_session(log)

    err = capsys.readouterr().err

    assert "_emit_jsonl_end failed" in err
    assert "forced failure" in err


# --- test_18_missing_files_warning() -----------------------------------------
def test_18_missing_files_warning(
    tmp_path,
    monkeypatch,
    capsys,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
    )

    monkeypatch.setattr(
        "logduo.internals.engine.close_session._build_auto_footer_created_file_lists",
        lambda runtime: ([], "missing.txt"),
    )

    _close_session(log)

    err = capsys.readouterr().err

    assert "Declared but not created" in err
    assert "missing.txt" in err
