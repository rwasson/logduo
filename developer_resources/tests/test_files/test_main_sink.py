"""
test_main_sink.py

Last edited: 2026-06-11
"""
import pytest
from rich.text import Text



from logduo import Duo
from developer_resources.pytest_toolkit.test_utils import (
    _read_file,
    _find_main_log,
)


LONG_MSG = ("Logduo is designed for data scientists, researchers, students, and "
    "Python developers who want readable console output, organized log files, "
    "and minimal logging setup.")

CUSTOM_HEADER = "MY CUSTOM HEADER"
CUSTOM_FOOTER = "MY CUSTOM FOOTER"

# --- test_01_emit_main_sink_log_string_inline() -------------------------------
def test_01_main_log_writes_inline_string(tmp_path):
    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_prefix="timestamp",
        log_wrap_width=80,
        show_pid_in_log=True,
    )

    log("hello world")
    log(LONG_MSG)
    log("a < 3")


    log.close()

    content = _read_file(_find_main_log(tmp_path))
    print(" ")
    print("***********************")
    print("test_01_main_log_writes_inline_string()")
    print("content")
    print(content)

    assert "hello world" in content
    assert "a < 3" in content

    lines = [
        line
        for line in content.splitlines()
        if "Logduo is designed" in line
           or "minimal logging setup." in line
    ]
    assert len(lines) >= 2
    # at least 4 blank characters at start of second wrapped line
    assert lines[1].startswith("     ")


    # header/footer written
    assert "logging started" in content
    assert "logging ended" in content

    # prefix generation
    assert "INFO" in content

    # pid formatting enabled
    assert "(" in content
    assert ":i1)" in content



# --- test_02_main_log_preserves_structured_string() --------------------------
def test_02_main_log_preserves_structured_string(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    log("a\nb\nc")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    print("***************************************")
    print("test_02_main_log_preserves_structured_string()")
    print("log content (should show structure block below prefix)")
    print(content)

    # structured blocks should not be rewrapped
    assert "|\na\nb\nc" in content



# --- test_03_main_log_flattens_rich_text() -----------------------------------
def test_03_main_log_flattens_rich_text(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    log(Text.from_markup("[blue]hello[/blue]"))
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    print(" ")
    print("***************************************")
    print("test_03_main_log_flattens_rich_text()")
    print("log content:")
    print(content)

    assert "hello" in content

    # no Rich object placeholder
    assert "[blue]" not in content
    assert "[/blue]" not in content

    # emitted as plain text
    assert "INFO" in content


# --- test_04_main_log_wrap_off_preserves_single_line() ------------------------
def test_04_main_log_wrap_off_preserves_single_line(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_wrap_width="off",
    )

    log(LONG_MSG)
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert LONG_MSG in content


# --- test_05_main_log_prefix_off() --------------------------------------------
def test_05_main_log_prefix_off(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_prefix="off",
    )

    log("hello world")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "hello world" in content
    assert "INFO" not in content


# --- test_06_main_log_prefix_level() ------------------------------------------
def test_06_main_log_prefix_level(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_prefix="level",
    )

    log("hello world")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "INFO" in content


# --- test_07_main_log_prefix_source() -----------------------------------------
def test_07_main_log_prefix_source(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_prefix="source",
    )

    log("hello world")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "hello world" in content

    # source path/file should appear
    assert ".py:" in content


# --- test_08_main_log_show_pid_enabled() --------------------------------------
def test_08_main_log_show_pid_enabled(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        show_pid_in_log=True,
    )

    log("hello world")
    log(f"log._runtime.pid = {log._runtime.pid}")
    print(" ")
    print(" **********************************")
    print("test_08_main_log_show_pid_enabled()")
    pid = log._runtime.pid
    print(f"log._runtime.pid = {log._runtime.pid}")
    log.close()

    content = _read_file(_find_main_log(tmp_path))
    print("log content:")
    print(content)

    assert str(pid) in content


# --- test_09_main_log_show_pid_disabled() -------------------------------------
def test_09_main_log_show_pid_disabled(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        show_pid_in_log=False,
    )

    log("hello world")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert ":i1)" not in content


# --- test_10_main_log_header_off() --------------------------------------------
def test_10_main_log_header_off(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_header="off",
    )

    log("hello world")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "logging started" not in content


# --- test_11_main_log_footer_off() --------------------------------------------
def test_11_main_log_footer_off(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_footer="off",
    )

    log("hello world")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "logging ended" not in content


# --- test_12_main_log_custom_header() -----------------------------------------
def test_12_main_log_custom_header(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_header=CUSTOM_HEADER,
    )

    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert CUSTOM_HEADER in content


# --- test_13_main_log_custom_footer() -----------------------------------------
def test_13_main_log_custom_footer(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_footer=CUSTOM_FOOTER,
    )

    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert CUSTOM_FOOTER in content


# --- test_14_main_log_verbosity_zero_creates_no_log() -------------------------
def test_14_main_log_verbosity_zero_creates_no_log(tmp_path):

    log = Duo()

    log.configure(log_dir_path=str(tmp_path), console_verbosity=0,
        log_dir_layout="script",
        log_verbosity=0,
    )

    log("hello world")
    log.close()

    log_files = list(tmp_path.rglob("*.log"))

    assert not log_files


# --- test_15_main_log_file_path_override() ------------------------------------
def test_15_main_log_file_path_override(tmp_path):

    custom_log = tmp_path / "custom" / "audit.log"

    log = Duo()

    log.configure(
        log_file_path=str(custom_log),
    )

    log("hello world")
    log.close()

    assert custom_log.exists()

    content = custom_log.read_text(encoding="utf-8")

    assert "hello world" in content


# --- test_16_main_log_file_name_override() ------------------------------------
def test_16_main_log_file_name_override(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_file_name="audit.log",
    )

    log("hello world")
    log.close()

    files = list(tmp_path.rglob("audit.log"))

    assert len(files) == 1

# --- test_17_main_log_file_mode_append() --------------------------------------
def test_17_main_log_file_mode_append(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_file_mode="append",
    )

    log("first")
    log.close()

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_file_mode="append",
    )

    log("second")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "first" in content
    assert "second" in content


# --- test_18_main_log_file_mode_write() ---------------------------------------
def test_18_main_log_file_mode_write(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_file_mode="write",
    )

    log("first")
    log.close()

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_file_mode="write",
    )

    log("second")
    log.close()

    content = _read_file(_find_main_log(tmp_path))

    assert "second" in content


# --- test_19_initialize_main_log_is_idempotent() ------------------------------
def test_19_initialize_main_log_is_idempotent(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    runtime = log._runtime

    initial_count = len(runtime._get_file_list_in_cfr())

    from logduo.internals.sinks.main_sink_log import (
        _initialize_main_sink_log,
    )

    _initialize_main_sink_log(log)

    final_count = len(runtime._get_file_list_in_cfr())

    assert final_count == initial_count


# ---  test_20_initialize_missing_main_dir_raises() ----------------------------
def test_20_initialize_missing_main_dir_raises(tmp_path):

    log = Duo()

    log.configure(log_dir_path=str(tmp_path))

    log._runtime.main_sink_log_dir_path_abs = None

    from logduo.internals.sinks.main_sink_log import (
        _initialize_main_sink_log,
    )

    with pytest.raises(RuntimeError):
        _initialize_main_sink_log(log)


# ---  test_21_initialize_missing_log_path_raises() ----------------------------
def test_21_initialize_missing_log_path_raises(tmp_path):

    log = Duo()

    log.configure(log_dir_path=str(tmp_path))

    log._runtime.main_sink_log_file_path_abs = None

    from logduo.internals.sinks.main_sink_log import (
        _initialize_main_sink_log,
    )

    with pytest.raises(RuntimeError):
        _initialize_main_sink_log(log)



