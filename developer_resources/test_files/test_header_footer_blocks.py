"""
test_header_footer_blocks.py

Tests log header and footer generation for
primary logs and user sinks.

Last edited: 2026-06-06
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

from developer_resources.pytest_toolkit.test_utils import (
    _find_file,
    _find_main_log,
    _find_new_logger_log,
    _read_file,
)
from logduo import Duo
from logduo.internals.engine.runtime_classes import CreatedFileRecord, RuntimeRecord
from logduo.internals.formatters.console_header_footer_builders import (
    _build_console_footer,
    _build_console_header,
    _render_rich_label_value_row,
)
from logduo.internals.formatters.header_footer_formatters import (
    _build_auto_footer_created_file_lists,
    _build_auto_footer_info_rows,
    _build_auto_header_info_rows,
    _build_shortened_file_path_display_label,
    _derive_label_pad,
)
from logduo.internals.session_config.session_constants import FileKindType
from logduo.utils.wrap.wrap_text import wrap_text

# === Custom Blocks used in test_files ==============================================

_DEBUG_TEST_PRINT = False

CUSTOM_HEADER = (
    "[blue]═══ CUSTOM HEADER BLOCK ════════════════════════════════════════════[/blue]\n"
    "[blue]Project:[/blue] TEST\n"
    "[blue]════════════════════════════════════════════════════════════════════[/blue]\n"
)

CUSTOM_FOOTER = (
    "[blue]════════════════════════════════════════════════════════════════════[/blue]\n"
    "[blue]CUSTOM FOOTER:[/blue] End of session\n"
    "[blue]════════════════════════════════════════════════════════════════════[/blue]\n"
)


#  --- helper for test_files' CreatedFileRecord -------------------------------------
def _make_cfr(
    path: Path,
    *,
    file_kind: FileKindType = "artifact",
) -> CreatedFileRecord:
    return CreatedFileRecord(
        path=path,
        file_name=path.name,
        file_ext=path.suffix.lstrip("."),
        file_kind=file_kind,
        is_log_file=False,
        sink_name=None,
        sink_id=None,
        log_verbosity=0,
        log_file_mode="write",
        log_prefix="off",
        log_wrap_width="off",
        log_header="off",
        log_footer="off",
        show_pid_in_log=False,
        continuation_prefix_len=0,
        display_order=0,
    )



# --- test_01_default_header_footer() ------------------------------------------
def test_01_default_header_footer(tmp_path: Path):
    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_file_mode="write",
    )
    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    _print_test_details(
        test_name="test_01_default_header_footer",
        assertion="'started' in log_content",
        expected=True,
        actual=("logging started" in log_content),
        log_content=log_content,
    )

    assert "logging started" in log_content
    assert "logging ended" in log_content


# --- test_02_custom_global_header_footer() ------------------------------------
def test_02_custom_global_header_footer(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_file_mode="write",
        log_header=CUSTOM_HEADER,
        log_footer=CUSTOM_FOOTER,
    )

    log("Custom global header/footer test")
    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    _print_test_details(
        test_name="test_02_custom_global_header_footer",
        assertion="'CUSTOM HEADER BLOCK' in log_content",
        expected=True,
        actual=("CUSTOM HEADER BLOCK" in log_content),
        log_content=log_content,
    )

    assert "CUSTOM HEADER BLOCK" in log_content
    assert "CUSTOM FOOTER:" in log_content

    # Rich markup flattened
    assert "[blue]" not in log_content


# --- test_03_header_off_footer_default() --------------------------------------
def test_03_header_off_footer_default(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_file_mode="write",
        log_header="off",
        log_footer="default",
    )

    log("Header disabled test")
    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    _print_test_details(
        test_name="test_03_header_off_footer_default",
        assertion="'CUSTOM HEADER BLOCK' not in log_content",
        expected=True,
        actual=("CUSTOM HEADER BLOCK" not in log_content),
        log_content=log_content,
    )

    assert "Header disabled test" in log_content
    assert "CUSTOM HEADER BLOCK" not in log_content


# --- test_04_footer_off_header_default() --------------------------------------
def test_04_footer_off_header_default(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_file_mode="write",
        log_footer="off",
    )

    log("Footer disabled test")
    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    _print_test_details(
        test_name="test_04_footer_off_header_default",
        assertion="'CUSTOM FOOTER' not in log_content",
        expected=True,
        actual=("CUSTOM FOOTER" not in log_content),
        log_content=log_content,
    )

    assert "Footer disabled test" in log_content
    assert "CUSTOM FOOTER:" not in log_content


# --- test_05_new_logger_overrides() ---------------------------------------
def test_05_new_logger_overrides(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    new_logger_verbosity = 2

    sec = log.new_logger(
        "secondary",
        log_verbosity=new_logger_verbosity,
        to_main_log=False,
        log_header=CUSTOM_HEADER,
        log_footer=CUSTOM_FOOTER,
    )

    assert callable(sec)

    # log("\nDuo.new_logger signature:", Duo.new_logger)

    sec("New_logger (secondary sink) custom header/footer")

    log("Main log still using config log_verbosity")
    log(f"New_logger (secondary sink) log using custom "
        f"extra_log_verbosity_value = {new_logger_verbosity}")
    log(f"DEFAULT_LOG_VERBOSITY_FOR_SECONDARY_SINKS = 2")

    log.close()

    new_logger_log = _find_new_logger_log(tmp_path, sink_name="secondary")
    main_log = _find_main_log(tmp_path)

    new_logger_text = _read_file(new_logger_log)
    main_text = _read_file(main_log)

    _print_test_details(
        test_name="test_05_new_logger_overrides",
        assertion="'CUSTOM HEADER BLOCK' not in primary_text",
        expected=True,
        actual=("CUSTOM HEADER BLOCK" not in main_text),
        log_content=new_logger_text,
    )

    print("\n--- PRIMARY LOG ---")
    print(main_text)


    assert "CUSTOM HEADER BLOCK" in new_logger_text
    assert "CUSTOM FOOTER:" in new_logger_text
    assert "[blue]" not in new_logger_text

    assert "CUSTOM HEADER BLOCK" not in main_text
    assert "CUSTOM FOOTER:" not in main_text


# --- test_06_append_mode() ----------------------------------------------------
def test_06_append_mode(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_file_mode="append",
    )

    log("Append mode test")
    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    _print_test_details(
        test_name="test_06_append_mode",
        assertion="'Append mode test' in log_content",
        expected=True,
        actual=("Append mode test" in log_content),
        log_content=log_content,
    )

    assert "Append mode test" in log_content

# --- test_07_log_footer_wrap_width_off() --------------------------------------
def test_07_log_footer_wrap_width_off(tmp_path: Path):
    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_wrap_width="off",
    )

    log.close()
    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    # Note pytest does not behave like script generated session
    # no script path should be found
    assert "script path" not in log_content
    assert "logging ended" in log_content
    assert "Logduo-managed files created this run" in log_content
    assert "config_table.txt" in log_content


# --- test_08_user_sink_footer_contains_log_file_path() ------------------------
def test_08_user_sink_footer_contains_log_file_path(tmp_path: Path):
    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    audit = log.new_logger(
        "audit",
        to_main_log=False,
    )

    audit("test message")
    log.close()

    audit_log = _find_file(tmp_path, "audit.log")
    audit_content = _read_file(audit_log)

    assert "logging ended" in audit_content
    assert "log file path" in audit_content.lower()
    assert "audit.log" in audit_content


# --- test_09_console_verbosity_zero_hides_startup_footer() --------------------
def test_09_console_verbosity_zero_hides_startup_footer(
    tmp_path: Path,
    capsys,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path), console_verbosity=0,
        log_dir_layout="script",
    )

    log.close()

    captured = capsys.readouterr()

    console_output = captured.out + captured.err

    assert "logging started" not in console_output.lower()
    assert "logging ended" not in console_output.lower()


# --- test_10_script_mode_populates_script_path() -------------------------
def test_10_script_mode_populates_script_path(tmp_path: Path):

    env = os.environ.copy()
    env["LOGDUO_TEST_OUTPUT_DIR"] = str(tmp_path)

    script_path = Path(
        __file__).parent.parent / "test_files" / "test_file_helpers" / "script_simple.py"
    print(" ")
    print("***********************************************************")
    print("test_10_script_mode_populates_script_path(tmp_path: Path) ")
    print(f"script_path = {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        env=env,
    )

    output = result.stdout + result.stderr

    assert result.returncode == 0
    print(sorted(tmp_path.rglob("*")))
    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    print("log_content:")
    print(log_content)

    assert "script_simple.py" in output
    assert "script path" in log_content.lower()
    assert "script_simple.py" in log_content


# --- test_11_pytest_is_not_treated_as_script() -------------------------------
def test_11_pytest_is_not_treated_as_script(tmp_path: Path):
    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    runtime = log._runtime
    assert runtime.script_path_abs is None  # while still running

    log.close()
    assert runtime.script_path_abs is None   # reset after close


# --- test_12_main_log_footer_wraps_script_path() ------------------------------
def test_12_main_log_footer_wraps_script_path(tmp_path: Path):

    env = os.environ.copy()
    env["LOGDUO_TEST_OUTPUT_DIR"] = str(tmp_path)

    script_path = Path(
        __file__).parent.parent / "test_files" / "test_file_helpers" / "script_simple.py"


    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    assert "script path" in log_content.lower()

    lines = log_content.splitlines()

    script_line_index = next(
        i
        for i, line in enumerate(lines)
        if line.lower().startswith("script path")
    )

    continuation_line = lines[script_line_index + 1]

    print(" ")
    print("*************************************************************************")
    print("test_12__main_log_footer_wraps_script_path")
    print("script_path:")
    print(script_path)

    print("\nSCRIPT PATH CONTINUATION LINE:")
    print(repr(continuation_line))
    print(f"assert continuation_line.startswith(' ')")

    assert continuation_line.startswith(" ")



# --- test_13_main_log_footer_wraps_created_files() ------------------------
def test_13_main_log_footer_wraps_created_files(tmp_path: Path):
    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_wrap_width=80,
    )

    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    assert "Logduo-managed files created this run" in log_content

    lines = log_content.splitlines()

    file_lines = [
        line
        for line in lines
        if "config_table.txt" in line
           or "config.json" in line
    ]

    assert file_lines

    print(" ")
    print("*************************************************************************")
    print("test_13_main_log_footer_wraps_created_files")
    print("\nFILE LINES:")
    for line in file_lines:
        print(repr(line))


# --- test_14_main_log_footer_uses_hanging_indent_for_paths() ------------------
def test_14_main_log_footer_uses_hanging_indent_for_paths(tmp_path: Path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
        log_wrap_width=80,
    )

    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    lines = log_content.splitlines()

    continuation_lines = [
        line
        for line in lines
        if line.startswith("    ")
    ]

    print(" ")
    print("*************************************************************************")
    print("test_14_main_log_footer_uses_hanging_indent_for_paths")
    print("\nCONTINUATION LINES:")
    for line in continuation_lines:
        print(repr(line))

    assert continuation_lines


# --- test_15_hanging_indent_applied() --------------------------------------------
def test_15_hanging_indent_applied():

    text = (
        "abcdefghijklmnopqrstuvwxyz "   # noqa
        "abcdefghijklmnopqrstuvwxyz "   # noqa
        "abcdefghijklmnopqrstuvwxyz"    # noqa
    )

    lines = wrap_text(
        text,
        width=20,
        continuation_width=20,
        hanging_indent=4,
    )

    assert len(lines) > 1
    for line in lines[1:]:
        assert line.startswith("    ")


# --- test_16_hanging_indent_respects_continuation_width() ------------------------
def test_16_hanging_indent_respects_continuation_width():
    text = "word " * 50

    lines = wrap_text(
        text,
        width=80,
        continuation_width=80,
        hanging_indent=10,
    )

    for line in lines:
        assert len(line) <= 80



# --- test_17_build_console_header_off() ---------------------------------------
def test_17_build_console_header_off():

    runtime = RuntimeRecord()
    result = _build_console_header(
        runtime=runtime,
        console_header="off",
        styles={},
    )

    assert result is None


# --- test_18_build_console_header_custom_markup() -----------------------------
def test_18_build_console_header_custom_markup():
    runtime = RuntimeRecord()
    result = _build_console_header(
        runtime=runtime,
        console_header="[blue]HELLO[/blue]",
        styles={},
    )

    assert result is not None
    assert "HELLO" in result.plain


# --- test_19_build_console_header_invalid_markup() ----------------------------
def test_19_build_console_header_invalid_markup():
    runtime = RuntimeRecord()
    result = _build_console_header(
        runtime=runtime,
        console_header="[blue",
        styles={},
    )

    assert result is not None
    assert "[blue" in result.plain


# --- test_20_build_console_footer_off() ---------------------------------------
def test_20_build_console_footer_off():
    runtime = RuntimeRecord()

    result = _build_console_footer(
        runtime=runtime,
        console_footer="off",
        console_wrap_width=100,
        styles={},
        show_created_files=False,
    )

    assert result is None


# --- test_21_build_console_footer_custom_markup() -----------------------------
def test_21_build_console_footer_custom_markup():
    runtime = RuntimeRecord()

    result = _build_console_footer(
        runtime=runtime,
        console_footer="[green]GOODBYE[/green]",
        console_wrap_width=100,
        styles={},
        show_created_files=False,
    )

    assert result is not None
    assert "GOODBYE" in result.plain


# --- test_22_build_console_footer_invalid_markup() ----------------------------
def test_22_build_console_footer_invalid_markup():
    runtime = RuntimeRecord()

    result = _build_console_footer(
        runtime=runtime,
        console_footer="[green",
        console_wrap_width=100,
        styles={},
        show_created_files=False,
    )

    assert result is not None
    assert "[green" in result.plain


# --- test_23_render_rich_label_value_row_label_only() -------------------------
def test_23_render_rich_label_value_row_label_only():
    result = _render_rich_label_value_row(
        "TITLE",
        None,
        label_style="blue",
        value_style="white",
        label_pad=20,
    )

    assert result.plain == "TITLE"


# --- test_24_render_rich_label_value_row_empty() ------------------------------
def test_24_render_rich_label_value_row_empty():
    result = _render_rich_label_value_row(
        "",
        None,
        label_style="blue",
        value_style="white",
        label_pad=20,
    )

    assert result.plain == ""


# --- test_25_build_auto_header_info_rows_log_file() ---------------------------
def test_25_build_auto_header_info_rows_log_file():
    runtime = RuntimeRecord(
        start_time_display="10:00",
        script_name="demo.py",
    )

    rows = _build_auto_header_info_rows(
        runtime=runtime,
        file_name="main.log",
        is_log_file=True,
    )

    assert (None, "main.log") in rows
    assert ("logging started", "10:00") in rows
    assert ("created by", "demo.py") in rows


# --- test_26_build_auto_header_info_rows_console() ----------------------------
def test_26_build_auto_header_info_rows_console():
    runtime = RuntimeRecord(
        start_time_display="10:00",
        script_name="demo.py",
    )

    rows = _build_auto_header_info_rows(
        runtime=runtime,
        file_name="ignored.log",
        is_log_file=False,
    )

    assert (None, "ignored.log") not in rows
    assert ("running script", "demo.py") in rows


# --- test_27_build_auto_footer_info_rows_user_sink(tmp_path) ------------------
def test_27_build_auto_footer_info_rows_user_sink(tmp_path):
    path = tmp_path / "audit.log"
    cfr = _make_cfr(
        path,
        file_kind="user_sink_log",
    )
    runtime = RuntimeRecord(
        end_time_display="11:00",
    )

    rows = _build_auto_footer_info_rows(
        runtime=runtime,
        cfr=cfr,
        path_display_width="off",
        is_main_sink=False,
    )

    assert ("log file path", str(path)) in rows


# --- test_28_build_auto_footer_info_rows_duration() ---------------------------
def test_28_build_auto_footer_info_rows_duration():
    runtime = RuntimeRecord(
        end_time_display="11:00",
        duration_display="5 sec",
    )

    rows = _build_auto_footer_info_rows(
        runtime=runtime,
        path_display_width="off",
        is_main_sink=True,
    )

    assert "duration 5 sec" in rows[0][1]


# --- test_29_shortened_file_path_display_label_off(tmp_path) ------------------
def test_29_shortened_file_path_display_label_off(tmp_path):
    path = tmp_path / "test.log"

    result = _build_shortened_file_path_display_label(
        path,
        anchor_dir=None,
        path_display_width="off",
    )

    assert result == str(path)


# --- test_30_shortened_file_path_display_label_bool_raises(tmp_path) ----------
def test_30_shortened_file_path_display_label_bool_raises(tmp_path):
    path = tmp_path / "test.log"

    with pytest.raises(RuntimeError):
        _build_shortened_file_path_display_label(
            path,
            anchor_dir=None,
            path_display_width=True,
        )


# --- test_31_shortened_file_path_display_label_invalid_type_raises(tmp_path) --
def test_31_shortened_file_path_display_label_invalid_type_raises(tmp_path):
    path = tmp_path / "test.log"
    with pytest.raises(RuntimeError):
        _build_shortened_file_path_display_label(
            path,
            anchor_dir=None,
            path_display_width=cast(object, []),   # noqa, intentional
        )


# --- test_32_derive_label_pad_ignores_none() ----------------------------------
def test_32_derive_label_pad_ignores_none():
    rows = [
        (None, "title"),
        ("short", "x"),
        ("longest label", "y"),
    ]

    assert _derive_label_pad(rows) == len("longest label")


# --- test_33_build_auto_footer_created_file_lists_missing(tmp_path) -----------
def test_33_build_auto_footer_created_file_lists_missing(tmp_path):
    runtime = RuntimeRecord()

    cfr = _make_cfr(
        tmp_path / "missing.log",
        file_kind="artifact",
    )

    runtime.created_file_record_registry[cfr.path] = cfr
    existing, missing = _build_auto_footer_created_file_lists(runtime)

    assert existing == []
    assert missing == [cfr]


# --- test_34_build_auto_footer_created_file_lists_jsonl_included(tmp_path) ---
def test_34_build_auto_footer_created_file_lists_jsonl_included(tmp_path):
    runtime = RuntimeRecord()
    jsonl_cfr = _make_cfr(
        tmp_path / "events.jsonl",
        file_kind="jsonl",
    )

    runtime.created_file_record_registry[jsonl_cfr.path] = jsonl_cfr
    existing, missing = _build_auto_footer_created_file_lists(runtime)

    assert jsonl_cfr in existing
    assert missing == []


# --- test_35_build_auto_footer_created_file_lists_jsonl_excluded(tmp_path) ---
def test_35_build_auto_footer_created_file_lists_jsonl_excluded(tmp_path):
    runtime = RuntimeRecord()

    jsonl_cfr = _make_cfr(
        tmp_path / "events.jsonl",
        file_kind="jsonl",
    )

    runtime.created_file_record_registry[jsonl_cfr.path] = jsonl_cfr
    existing, missing = _build_auto_footer_created_file_lists(
        runtime,
        include_jsonl=False,
    )

    assert jsonl_cfr not in existing


# --- test_36_build_auto_footer_created_file_lists_existing(tmp_path) ----------
def test_36_build_auto_footer_created_file_lists_existing(tmp_path):
    runtime = RuntimeRecord()
    path = tmp_path / "exists.log"
    path.write_text("hello")
    cfr = _make_cfr(path)

    runtime.created_file_record_registry[path] = cfr
    existing, missing = _build_auto_footer_created_file_lists(runtime)

    assert existing == [cfr]
    assert missing == []


# --- _print_test_details() ----------------------------------------------------
def _print_test_details(
    *,
    test_name: str,
    assertion: str,
    expected: object,
    actual: object,
    log_content: str | None = None,

) -> None:
    if not _DEBUG_TEST_PRINT:
        return

    print(" ")
    print("********************************************************************************")
    print(test_name)
    print(
        f"test outcome: "
        f"{'PASS' if expected == actual else '*** FAIL ***'}"
    )

    print(f"assertion   : {assertion}")
    print(f"expected    : {expected!r}")
    print(f"actual      : {actual!r}")
    print("")
    if log_content is not None:
        print("LOG CONTENT:")
        print(log_content)
        print(" ")




