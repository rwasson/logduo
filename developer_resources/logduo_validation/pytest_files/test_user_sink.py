"""
test_user_sink.py

Last edited: 2026-06-12
"""

import pytest
from rich.text import Text

from developer_resources.logduo_validation.pytest_files.pytest_helpers.file_helpers import _find_main_log, _read_file
from logduo import Duo
from logduo.internals.session_config.session_constants import _DEFAULT_LOG_VERBOSITY

LONG_MSG = ("Logduo is designed for data scientists, researchers, students, and "
    "Python developers who want readable console output, organized log files, "
    "and minimal logging setup.")

CUSTOM_HEADER = "MY CUSTOM HEADER"
CUSTOM_FOOTER = "MY CUSTOM FOOTER"


# --- test_01_user_sink_writes_inline_string() ---------------------------------
def test_01_user_sink_writes_inline_string(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger("audit")
    rep("hello world")

    log.close()

    content = _read_file(tmp_path / "session" / "audit.log")

    assert "hello world" in content
    assert "INFO" in content


# --- test_02_user_sink_preserves_structured_string() --------------------------
def test_02_user_sink_preserves_structured_string(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger("audit")
    rep("a\nb\nc")

    log.close()

    content = _read_file(tmp_path / "session" / "audit.log")

    assert "|\na\nb\nc" in content


# --- test_03_user_sink_flattens_rich_text() -----------------------------------
def test_03_user_sink_flattens_rich_text(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger("audit")
    rep(Text.from_markup("[blue]hello[/blue]"))

    log.close()

    content = _read_file(tmp_path / "session" / "audit.log")

    assert "hello" in content
    assert "[blue]" not in content
    assert "[/blue]" not in content


# --- test_04_user_sink_wraps_inline_string() ----------------------------------
def test_04_user_sink_wraps_inline_string(tmp_path):

    log = Duo()

    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger(
        "audit",
        log_wrap_width=80,
    )

    rep(LONG_MSG)

    log.close()

    content = _read_file(tmp_path / "session" / "audit.log")

    print(" ")
    print(" ************************************* ")
    print("test_04_user_sink_wraps_inline_string")
    print(content)

    assert "Logduo is designed" in content
    assert "logging setup." in content
    assert "students, and Python developers" in content
    assert "console output, organized" in content
    assert LONG_MSG not in content


# --- test_05_user_sink_wrap_width_off() ---------------------------------------
def test_05_user_sink_wrap_width_off(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger(
        "audit",
        log_wrap_width="off",
    )

    rep(LONG_MSG)

    log.close()

    content = _read_file(tmp_path / "session" / "audit.log")

    assert LONG_MSG in content


# --- test_06_user_sink_prefix_off() -------------------------------------------
def test_06_user_sink_prefix_off(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger(
        "audit",
        log_prefix="off",
    )

    rep("hello")

    log.close()

    content = _read_file(tmp_path / "session" / "audit.log")

    assert "hello" in content
    assert "INFO" not in content


# --- test_07_user_sink_show_pid_enabled() -------------------------------------
def test_07_user_sink_show_pid_enabled(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script", show_pid_in_log=True)

    rep = log.new_logger(
        "audit",
    )

    pid = str(log._runtime.pid)

    rep("hello")

    log.close()

    content = _read_file(tmp_path / "session" / "audit.log")

    print(" ")
    print(" ************************************* ")
    print("test_07_user_sink_show_pid_enabled")
    print(content)

    assert str(pid) in content


# --- test_08_user_sink_header_footer_written() --------------------------------
def test_08_user_sink_header_footer_written(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger(
        "audit",
        log_header="MY HEADER",
        log_footer="MY FOOTER",
    )

    rep("hello")

    log.close()

    content = _read_file(tmp_path / "session" / "audit.log")

    assert "MY HEADER" in content
    assert "MY FOOTER" in content


# --- test_09_user_sink_to_main_log_false() ------------------------------------
def test_09_user_sink_to_main_log_false(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger(
        "audit",
        to_main_log=False,
    )

    rep("secret")

    main_log_path = log.main_log_file_path
    assert main_log_path is not None

    log.close()

    audit_content = _read_file(tmp_path / "session" / "audit.log")
    main_content = _read_file(main_log_path)

    assert "secret" in audit_content
    assert "secret" not in main_content


# --- test_10_user_sink_to_main_log_true() -------------------------------------
def test_10_user_sink_to_main_log_true(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger(
        "audit",
        to_main_log=True,
    )

    rep("mirrored")

    log.close()

    audit_content = _read_file(tmp_path / "session" / "audit.log")
    main_content = _read_file(_find_main_log(tmp_path))

    assert "mirrored" in audit_content
    assert "mirrored" in main_content


# --- test_11_new_logger_duplicate_name_raises() -------------------------------
def test_11_new_logger_duplicate_name_raises(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    log.new_logger("audit")

    with pytest.raises(ValueError):
        log.new_logger("audit")


# --- test_12_new_logger_log_verbosity_zero_raises() ---------------------------
def test_12_new_logger_log_verbosity_zero_raises(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    with pytest.raises(ValueError):
        log.new_logger(
            "audit",
            log_verbosity=0,
        )


# --- test_13_new_logger_absolute_path() ---------------------------------------
def test_13_new_logger_absolute_path(tmp_path):

    target = tmp_path / "special" / "audit.log"

    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger(target)
    rep("hello")

    log.close()

    assert target.exists()


# --- test_14_new_logger_timestamped_mode() ------------------------------------
def test_14_new_logger_timestamped_mode(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    log.new_logger(
        "audit.log",
        log_file_mode="timestamped",
    )

    log.close()

    files = list((tmp_path / "session").glob("audit*.log"))

    assert len(files) == 1
    assert files[0].name != "audit.log"


# --- test_15_new_logger_without_extension() -----------------------------------
def test_15_new_logger_without_extension(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    rep = log.new_logger("audit")
    rep("hello")

    log.close()

    assert (tmp_path / "session" / "audit.log").exists()


# --- test_16_main_log_disabled_user_sink_still_created() ----------------------
def test_16_main_log_disabled_user_sink_still_created(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path),  console_verbosity=0, log_verbosity=0)

    rep = log.new_logger("audit")

    print(" ")
    print("********************************")
    print("test_16_main_log_disabled_user_sink_still_created")
    print(
        f"global log.session_config.log_verbosity = "
        f"{log.session_config.log_verbosity}"
    )

    rep("hello")
    print("output_dir_path = ")
    print(log.output_dir_path)

    audit_cfr = next(
        cfr
        for cfr in log._runtime._get_file_list_in_cfr()
        if cfr.sink_name == "audit"
    )

    print(
        f"audit_cfr.log_verbosity = "
        f"{audit_cfr.log_verbosity}"
    )
    print(f"audit_cfr.path = {audit_cfr.path}")

    assert audit_cfr.log_verbosity == _DEFAULT_LOG_VERBOSITY

    log.close()

    # no main log created
    assert not any(
        p.name == "session.log"
        for p in tmp_path.rglob("*.log")
    )

    # audit log created
    assert any(
        p.name == "audit.log"
        for p in tmp_path.rglob("*.log")
    )

    content = _read_file(audit_cfr.path)

    print("audit.log")
    print(content)

    assert "hello" in content
