"""
test_loguru_integration.py

Tests Logduo's Loguru integration layer.

Focus:
    - routing filters
    - payload emission
    - rotation/retention validation
    - sink attachment invariants

Last edited: 2026-06-14
"""


import pytest

from developer_resources.logduo_validation.pytest_files.pytest_helpers.file_helpers import (
    _find_file,
    _find_main_log,
    _read_file,
)
from logduo import Duo
from logduo.internals.sinks.loguru_integration import (
    _build_logduo_filter,
    _probe_loguru_rotation_retention,
)


# --- test_01_main_sink_accepts_main_sink_records() ----------------------------
def test_01_main_sink_accepts_main_sink_records():

    filt = _build_logduo_filter(              # noqa spelling
        log_file_kind="main_sink_log",
        sink_name="ignored",
    )

    record = {
        "extra": {
            "target_kind": "main_sink_log",
        }
    }

    assert filt(record) is True


# --- test_02_main_sink_rejects_user_sink_records() ----------------------------
def test_02_main_sink_rejects_user_sink_records():

    filt = _build_logduo_filter(       # noqa spelling
        log_file_kind="main_sink_log",
        sink_name="ignored",
    )

    record = {
        "extra": {
            "target_kind": "user_sink_log",
            "sink_name": "audit",
        }
    }

    assert filt(record) is False


# --- test_03_user_sink_accepts_matching_sink_name() ---------------------------
def test_03_user_sink_accepts_matching_sink_name():

    filt = _build_logduo_filter(             # noqa spelling
        log_file_kind="user_sink_log",
        sink_name="audit",
    )

    record = {
        "extra": {
            "target_kind": "user_sink_log",
            "sink_name": "audit",
        }
    }

    assert filt(record) is True


# --- test_04_user_sink_rejects_nonmatching_sink_name() ------------------------
def test_04_user_sink_rejects_nonmatching_sink_name():

    filt = _build_logduo_filter(                  # noqa spelling
        log_file_kind="user_sink_log",
        sink_name="audit",
    )

    record = {
        "extra": {
            "target_kind": "user_sink_log",
            "sink_name": "report",
        }
    }

    assert filt(record) is False


# --- test_05_rotation_accepts_valid_size_string() ----------------------------
def test_05_rotation_accepts_valid_size_string():

    _probe_loguru_rotation_retention(
        config={"rotation": "10 MB"}
    )


# --- test_06_rotation_rejects_invalid_value() -------------------------------
def test_06_rotation_rejects_invalid_value():

    with pytest.raises(ValueError):
        _probe_loguru_rotation_retention(
            config={"rotation": object()}
        )


# --- test_07_retention_accepts_valid_string() -------------------------------
def test_07_retention_accepts_valid_string():

    _probe_loguru_rotation_retention(
        config={"retention": "7 days"}
    )


# --- test_08_retention_rejects_invalid_value() ------------------------------
def test_08_retention_rejects_invalid_value():

    with pytest.raises(ValueError):
        _probe_loguru_rotation_retention(
            config={"retention": object()}
        )



# --- test_09_invalid_log_file_kind_raises() ---------------------------------
def test_09_invalid_log_file_kind_raises():

    with pytest.raises(RuntimeError):
        _build_logduo_filter(
            log_file_kind="bad_kind",             # noqa intentional error
            sink_name="audit",
        )


# ---  test_10_literal_characters() --------------------------------------------
def test_10_literal_characters(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    log("<input>")
    log("a < b")
    log("{hello}")
    log("{{hello}}")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "<input>" in content
    assert "a < b" in content
    assert "{hello}" in content
    assert "{{hello}}" in content


# --- test_11_ansi_removed_from_log_file() -------------------------------------
def test_11_ansi_removed_from_log_file(tmp_path, capsys):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    RED = "\033[31m"
    RESET = "\033[0m"

    log(f"{RED}hello{RESET}")
    log(f"{RED}<input>{RESET}")
    log(f"{RED}{{hello}}{RESET}")
    log.close()

    log_content = _read_file(_find_main_log(tmp_path))
    console_output = capsys.readouterr().out

    assert "hello" in log_content
    assert "<input>" in log_content
    assert "{hello}" in log_content

    assert "hello" in console_output
    assert "<input>" in console_output
    assert "{hello}" in console_output
    # assert "[0m" not in console_output  # code will be there, but not visible on console

    assert "\033[31m" not in log_content
    assert "\033[0m" not in log_content
    assert "[31m" not in log_content
    assert "[0m" not in log_content
    assert "RED" not in log_content
    assert "RESET" not in log_content


# --- test_12_literal_characters_new_logger() ---------------------------------
def test_12_literal_characters_new_logger(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    audit = log.new_logger("audit")

    audit("<input>")
    audit("a < b")
    audit("{hello}")
    audit("{{hello}}")
    log.close()

    audit_path = _find_file(tmp_path, "audit.log")

    print(f"audit path: {audit_path}")
    log_content = _read_file(audit_path)

    print(" ")
    print("*********************************")
    print("test_12_literal_characters_new_logger")
    print("log_content")
    print(log_content)
    print(" ")

    assert "<input>" in log_content
    assert "a < b" in log_content
    assert "{hello}" in log_content
    assert "{{hello}}" in log_content
    print("*********************************")


# --- test_13_long_ansi_message_wraps_and_logs_cleanly() -----------------------
def test_13_long_ansi_message_wraps_and_logs_cleanly(
    tmp_path,
    capsys,
):
    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        console_wrap_width=80,
        log_wrap_width=80,
    )

    RED = "\033[31m"
    RESET = "\033[0m"

    long_msg = (
        f"Logduo is designed for {RED}data scientists, researchers, students, and "
        f"Python developers{RESET} who want readable console output, "
        f"{RED}organized{RESET} log files, and "
        f"{RED}minimal{RESET} logging setup."
    )

    log(long_msg)
    log.close()

    console_output = capsys.readouterr().out
    log_content = _read_file(_find_main_log(tmp_path))

    print(" ")
    print("*********************************")
    print("test_13_long_ansi_message_wraps_and_logs_cleanly")
    print("console_output")
    print(console_output)
    print(" ")
    print("log_content")
    print(log_content)
    print("*********************************")


    assert "data scientists" in console_output
    assert "organized" in console_output
    assert "minimal" in console_output

    assert "data scientists" in log_content
    assert "organized" in log_content
    assert "minimal" in log_content

    assert "\033[31m" not in log_content
    assert "\033[0m" not in log_content


# --- test_14_braces_and_angle_brackets_with_ansi() ----------------------------
def test_14_braces_and_angle_brackets_with_ansi(
    tmp_path,
):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    RED = "\033[31m"
    RESET = "\033[0m"

    log(f"{RED}<input>{RESET}")
    log(f"{RED}a < b{RESET}")
    log(f"{RED}{{hello}}{RESET}")
    log(f"{RED}{{{{hello}}}}{RESET}")

    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "<input>" in content
    assert "a < b" in content
    assert "{hello}" in content
    assert "{{hello}}" in content

    assert "\033[" not in content
