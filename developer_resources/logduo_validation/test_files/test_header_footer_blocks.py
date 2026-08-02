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

from developer_resources.logduo_validation.test_files.test_helpers.file_helpers import (
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
    _build_auto_footer_generated_file_lists,
    _build_auto_footer_info_rows,
    _build_auto_header_info_rows,
    _derive_label_pad,
)
from logduo.internals.session_config.session_constants import (
    FileKindType,
    LogFileModeType,
)
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
    log_file_mode: LogFileModeType = "write",
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
        log_file_mode=log_file_mode,
        log_prefix="off",
        log_wrap_width="off",
        log_header="off",
        log_footer="off",
        show_pid_in_log=False,
        continuation_prefix_len=0,
    )


# --- test_01_default_header_footer() ------------------------------------------
def test_01_default_header_footer(tmp_path: Path):
    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        log_file_mode="write",
    )
    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    _print_test_details(
        test_name="test_01_default_header_footer",
        assertion="'Started' in log_content",
        expected=True,
        actual=("Logging started" in log_content),
        log_content=log_content,
    )

    assert "Logging started" in log_content
    assert "Logging ended" in log_content


# --- test_02_custom_global_header_footer() ------------------------------------
def test_02_custom_global_header_footer(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
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
        log_file_layout="script",
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
        log_file_layout="script",
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
        log_file_layout="script",
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

    main_log_path = log.main_log_file_path
    assert main_log_path is not None

    log.close()

    new_logger_log = _find_new_logger_log(tmp_path, sink_name="secondary")
    new_logger_text = _read_file(new_logger_log)
    main_text = _read_file(main_log_path)

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
        log_file_layout="script",
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
        log_file_layout="script",
        log_wrap_width="off",
    )

    log.close()
    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    # Note pytest does not behave like script generated session
    # no script path should be found
    assert "Script path" not in log_content
    assert "Logging ended" in log_content
    assert "Log-generated files in output directory:" in log_content
    assert "config_table.txt" in log_content


# --- test_08_user_sink_footer_contains_log_file_path() ------------------------
def test_08_user_sink_footer_contains_log_file_path(
    tmp_path: Path,
) -> None:
    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
    )

    audit = log.new_logger(
        "audit",
        to_main_log=False,
    )

    audit("test message")
    log.close()

    audit_log = _find_file(tmp_path, "audit.log")
    audit_content = _read_file(audit_log)

    assert "Logging ended" in audit_content

    lines = audit_content.splitlines()
    log_file_label_index = lines.index("Log file path:")
    displayed_path_lines: list[str] = []

    for line in lines[log_file_label_index + 1:]:
        if not line.startswith(" "):
            break
        displayed_path_lines.append(line)

    assert displayed_path_lines

    first_path_line = displayed_path_lines[0]

    assert first_path_line.startswith("    ")
    assert not first_path_line.startswith("        ")

    for continuation_line in displayed_path_lines[1:]:
        assert continuation_line.startswith("        ")

    displayed_path = "".join(
        line.strip()
        for line in displayed_path_lines
    )

    assert displayed_path == str(audit_log.absolute())


# --- test_09_console_verbosity_zero_hides_startup_footer() --------------------
def test_09_console_verbosity_zero_hides_startup_footer(
    tmp_path: Path,
    capsys,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path), console_verbosity=0,
        log_file_layout="script",
    )

    log.close()

    captured = capsys.readouterr()

    console_output = captured.out + captured.err

    assert "Logging started" not in console_output
    assert "Logging ended" not in console_output


# --- test_10_script_mode_populates_script_path() -------------------------
def test_10_script_mode_populates_script_path(tmp_path: Path):

    env = os.environ.copy()
    env["LOGDUO_TEST_OUTPUT_DIR"] = str(tmp_path)

    script_path = Path(
        __file__).parent.parent / "test_files" / "test_helpers" / "script_simple.py"
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
    assert "Script path" in log_content
    assert "script_simple.py" in log_content


# --- test_11_pytest_is_not_treated_as_script() -------------------------------
def test_11_pytest_is_not_treated_as_script(tmp_path: Path):
    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
    )

    runtime = log._runtime
    assert runtime.script_path_abs is None  # while still running

    log.close()
    assert runtime.script_path_abs is None   # reset after close


# --- test_12_main_log_footer_wraps_script_path() ------------------------------
def test_12_main_log_footer_wraps_script_path(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["LOGDUO_TEST_OUTPUT_DIR"] = str(tmp_path)

    script_path = (
        Path(__file__).parent.parent
        / "test_files"
        / "test_helpers"
        / "script_simple.py"
    )

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)
    lines = log_content.splitlines()

    script_label_index = lines.index("Script path:")

    first_path_line = lines[script_label_index + 1]
    continuation_line = lines[script_label_index + 2]

    assert first_path_line.startswith("    ")
    assert not first_path_line.startswith("        ")

    assert continuation_line.startswith("        ")

    displayed_path_lines: list[str] = []
    for line in lines[script_label_index + 1:]:
        if not line.startswith(" "):
            break
        displayed_path_lines.append(line)

    assert len(displayed_path_lines) >= 2
    assert displayed_path_lines[0].startswith("    ")
    assert not displayed_path_lines[0].startswith("        ")

    for continuation_line in displayed_path_lines[1:]:
        assert continuation_line.startswith("        ")

    displayed_path = "".join(
        line.strip()
        for line in displayed_path_lines
    )
    assert displayed_path == str(script_path.absolute())


# --- test_13_main_log_footer_wraps_generated_files() ------------------------
def test_13_main_log_footer_wraps_generated_files(tmp_path: Path):
    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        log_wrap_width=80,
    )

    log_path = log.main_log_file_path
    assert log_path is not None

    log.close()

    log_content = log_path.read_text(encoding="utf-8")

    print()
    print("**********************************************")
    print("test_13_main_log_footer_wraps_generated_files")
    print()
    print(log_content)
    print("**********************************************")
    print(" ")

    marker = "Log-generated files in output directory:"
    assert marker in log_content

    footer = log_content.split(marker, maxsplit=1)[1]

    footer_lines = [
        line
        for line in footer.splitlines()
        if line.strip()
    ]

    assert footer_lines

    too_long_lines = [
        (len(line), line)
        for line in footer_lines
        if len(line) > 80
    ]

    assert not too_long_lines, (
        "Footer contains lines longer than 80 characters:\n"
        + "\n".join(
            f"{length}: {line!r}"
            for length, line in too_long_lines
        )
    )


# --- test_14_main_log_footer_wraps_output_directory() ------------------------
def test_14_main_log_footer_wraps_output_directory(
    tmp_path: Path,
) -> None:
    long_log_dir = (
            tmp_path
            / "deliberately_long_directory_name_for_footer_wrapping"
            / "another_long_directory_component"
    )
    log = Duo()

    log.configure(
        log_dir_path=str(long_log_dir),
        log_file_layout="script",
        log_wrap_width=80,
    )

    output_dir_path = log.output_dir_path
    assert output_dir_path is not None

    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)
    lines = log_content.splitlines()

    output_dir_label_index = lines.index("Output directory:")

    displayed_path_lines: list[str] = []

    for line in lines[output_dir_label_index + 1:]:
        if not line.startswith(" "):
            break

        displayed_path_lines.append(line)

    assert len(displayed_path_lines) >= 2

    first_path_line = displayed_path_lines[0]

    assert first_path_line.startswith("    ")
    assert not first_path_line.startswith("        ")

    for continuation_line in displayed_path_lines[1:]:
        assert continuation_line.startswith("        ")

    displayed_path = "".join(
        line.strip()
        for line in displayed_path_lines
    )

    assert displayed_path == str(output_dir_path.absolute())


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
    assert ("Logging started", "10:00") in rows
    assert ("Generated by", "demo.py") in rows


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
    assert ("Running script", "demo.py") in rows


# --- test_27_build_auto_footer_info_rows_duration() ---------------------------
def test_27_build_auto_footer_info_rows_duration(tmp_path):

    runtime = RuntimeRecord(
        end_time_display="11:00",
        duration_display="5 sec",
        project_dir_path_abs=tmp_path / "project",
    )

    rows = _build_auto_footer_info_rows(
        runtime=runtime,
        is_main_sink=True,
    )

    assert rows[0] == (
        "Logging ended",
        "11:00 (duration 5 sec)",
    )



# --- test_28_derive_label_pad_ignores_none() ----------------------------------
def test_28_derive_label_pad_ignores_none():
    rows = [
        (None, "title"),
        ("short", "x"),
        ("longest label", "y"),
    ]

    assert _derive_label_pad(rows) == len("longest label")


# --- test_29_build_auto_footer_generated_file_lists_missing() ----------------
def test_29_build_auto_footer_generated_file_lists_missing(
    tmp_path: Path,
) -> None:
    runtime = RuntimeRecord()
    runtime.main_sink_log_dir_path_abs = tmp_path

    write_path = tmp_path / "missing_write.log"
    append_path = tmp_path / "missing_append.log"

    write_cfr = _make_cfr(
        write_path,
        file_kind="artifact",
    )

    append_cfr = _make_cfr(
        append_path,
        file_kind="artifact",
        log_file_mode="append",
    )

    runtime.created_file_record_registry[write_path] = write_cfr
    runtime.created_file_record_registry[append_path] = append_cfr

    (
        output_dir_path,
        output_dir_files,
        other_files,
        missing_files,
    ) = _build_auto_footer_generated_file_lists(
        runtime=runtime,
    )

    assert output_dir_path == str(tmp_path.absolute())
    assert output_dir_files == []
    assert other_files == []

    assert missing_files == [
        f"{append_path.absolute()} (append)",
        str(write_path.absolute()),
    ]


# --- test_30_build_auto_footer_generated_file_lists_jsonl_included(tmp_path) ---
def test_30_build_auto_footer_generated_file_lists_jsonl_included(
    tmp_path,
) -> None:
    runtime = RuntimeRecord()
    runtime.main_sink_log_dir_path_abs = tmp_path
    path = tmp_path / "events.jsonl"
    jsonl_cfr = _make_cfr(
        path,
        file_kind="jsonl",
    )

    runtime.created_file_record_registry[path] = jsonl_cfr
    (
        output_dir_path,
        output_dir_files,
        other_files,
        missing_files,
    ) = _build_auto_footer_generated_file_lists(runtime=runtime)

    assert output_dir_path == str(tmp_path.absolute())
    assert output_dir_files == ["events.jsonl"]
    assert other_files == []
    assert missing_files == []


def test_31_generated_file_lists_marks_append_mode(
    tmp_path: Path,
) -> None:
    runtime = RuntimeRecord()
    runtime.main_sink_log_dir_path_abs = tmp_path

    write_path = tmp_path / "write.log"
    append_path = tmp_path / "append.log"

    write_path.write_text("", encoding="utf-8")
    append_path.write_text("", encoding="utf-8")

    runtime.created_file_record_registry[write_path] = _make_cfr(
        write_path,
    )
    runtime.created_file_record_registry[append_path] = _make_cfr(
        append_path,
        log_file_mode="append",
    )

    (
        output_dir_path,
        output_dir_files,
        other_files,
        missing_files,
    ) = _build_auto_footer_generated_file_lists(runtime=runtime)

    assert output_dir_path == str(tmp_path.absolute())
    assert output_dir_files == [
        "append.log (append)",
        "write.log",
    ]
    assert other_files == []
    assert missing_files == []

def test_32_generated_file_lists_groups_other_files(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    other_dir = tmp_path / "other"
    output_dir.mkdir()
    other_dir.mkdir()

    runtime = RuntimeRecord()
    runtime.main_sink_log_dir_path_abs = output_dir

    output_file = output_dir / "main.log"
    other_file = other_dir / "report.log"

    output_file.write_text("", encoding="utf-8")
    other_file.write_text("", encoding="utf-8")

    runtime.created_file_record_registry[output_file] = _make_cfr(
        output_file,
    )
    runtime.created_file_record_registry[other_file] = _make_cfr(
        other_file,
    )

    (
        output_dir_path,
        output_dir_files,
        other_files,
        missing_files,
    ) = _build_auto_footer_generated_file_lists(runtime=runtime)

    assert output_dir_path == str(output_dir.absolute())
    assert output_dir_files == ["main.log"]
    assert other_files == [str(other_file.absolute())]
    assert missing_files == []


# ==+ Internal helper ==========================================================

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




