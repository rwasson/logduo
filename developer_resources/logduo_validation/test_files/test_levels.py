"""
test_levels.py

Integration tests for public Logduo level calls.

Covers:
- standard level methods
- log() shorthand
- left_indent
- no_prefix
- log_wrap_width
- console_style interaction
- structured block/newline preservation

Last edited: 2026-08-09
"""

from pathlib import Path

import pytest
from rich.text import Text

from developer_resources.pytest_harness.dashboard_wrapper import strip_ansi
from logduo import Duo

# === Helpers =================================================================


def _read_main_log(log_file_path: Path) -> str:
    return log_file_path.read_text(encoding="utf-8")


# === Standard levels =========================================================


# --- test_01_standard_levels_accept_left_indent() ----------------------------
@pytest.mark.parametrize(
    ("level_name", "message"),
    [
        ("critical", "critical indented message"),
        ("error", "error indented message"),
        ("warning", "warning indented message"),
        ("success", "success indented message"),
        ("info", "info indented message"),
        ("debug", "debug indented message"),
        ("trace", "trace indented message"),
    ],
)
def test_01_standard_levels_accept_left_indent(
    tmp_path: Path,
    capsys,
    level_name: str,
    message: str,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        console_verbosity=3,
        log_verbosity=3,
        console_prefix="level",
        log_prefix="level",
    )

    log_file_path = log.main_log_file_path
    assert log_file_path is not None

    level_method = getattr(log, level_name)

    level_method(
        message,
        left_indent=5,
    )

    captured = capsys.readouterr()

    log.close()

    log_content = _read_main_log(log_file_path)

    assert f"     {message}" in captured.out
    assert f"     {message}" in log_content


# --- test_02_log_shorthand_accepts_left_indent() -----------------------------
def test_02_log_shorthand_accepts_left_indent(
    tmp_path: Path,
    capsys,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        console_prefix="level",
        log_prefix="level",
    )

    log_file_path = log.main_log_file_path
    assert log_file_path is not None

    log(
        "shorthand indented message",
        left_indent=7,
    )

    captured = capsys.readouterr()

    log.close()

    log_content = _read_main_log(log_file_path)

    assert "       shorthand indented message" in captured.out
    assert "       shorthand indented message" in log_content


# === Per-call argument interaction ===========================================


# --- test_03_left_indent_and_no_prefix() -------------------------------------
def test_03_left_indent_and_no_prefix(
    tmp_path: Path,
    capsys,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        console_prefix="level",
        log_prefix="level",
    )

    log_file_path = log.main_log_file_path
    assert log_file_path is not None

    message = "indented message without prefix"

    log.info(
        message,
        no_prefix=True,
        left_indent=6,
    )

    captured = capsys.readouterr()

    log.close()

    log_content = _read_main_log(log_file_path)

    # Message remains indented.
    assert f"      {message}" in captured.out
    assert f"      {message}" in log_content

    # Prefix is suppressed for this message.
    console_line = next(
        line
        for line in captured.out.splitlines()
        if message in line
    )
    log_line = next(
        line
        for line in log_content.splitlines()
        if message in line
    )

    assert "| INFO" not in console_line
    assert "| INFO" not in log_line


# --- test_04_left_indent_and_log_wrap_width() --------------------------------
def test_04_left_indent_and_log_wrap_width(
    tmp_path: Path,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        console_verbosity=0,
        log_verbosity=3,
        log_prefix="off",
        log_wrap_width=100,
    )

    log_file_path = log.main_log_file_path
    assert log_file_path is not None


    message = (
        "LEFT_INDENT_WRAP_TEST one two three four five six seven eight nine ten "
        "eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen "
        "nineteen twenty twenty-one twenty-two twenty-three twenty-four"
    )

    log.info(
        message,
        left_indent=5,
        log_wrap_width=80,
    )

    log.close()

    log_content = _read_main_log(log_file_path)

    message_lines = [
        line
        for line in log_content.splitlines()
        if (
            "LEFT_INDENT_WRAP_TEST" in line
            or line.startswith("     one")
            or line.startswith("     two")
            or line.startswith("     three")
            or line.startswith("     four")
            or line.startswith("     five")
            or line.startswith("     six")
            or line.startswith("     seven")
            or line.startswith("     eight")
            or line.startswith("     nine")
            or line.startswith("     ten")
            or line.startswith("     eleven")
            or line.startswith("     twelve")
        )
    ]

    assert len(message_lines) > 1
    assert all(line.startswith(" " * 5) for line in message_lines)
    assert all(len(line) <= 80 for line in message_lines)


# --- test_05_left_indent_no_prefix_wrap_and_console_style() ------------------
def test_05_left_indent_no_prefix_wrap_and_console_style(
    tmp_path: Path,
    capsys,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        console_verbosity=3,
        log_verbosity=3,
        console_prefix="level",
        log_prefix="level",
        log_wrap_width=100,
    )

    log_file_path = log.main_log_file_path
    assert log_file_path is not None

    message = (
        "COMBINED_ARGS_TEST this deliberately long message verifies that "
        "left_indent, no_prefix, log_wrap_width, and console_style can all "
        "be supplied on the same logging call."
    )

    log.info(
        message,
        left_indent=4,
        no_prefix=True,
        log_wrap_width=80,
        console_style="bold",
    )

    captured = capsys.readouterr()

    log.close()

    log_content = _read_main_log(log_file_path)

    # --- locate relevant console/log lines ----------------------------------
    console_line = next(
        line
        for line in captured.out.splitlines()
        if "COMBINED_ARGS_TEST" in line
    )
    console_line_plain = strip_ansi(console_line)

    log_lines = log_content.splitlines()

    start_index = next(
        i
        for i, line in enumerate(log_lines)
        if "COMBINED_ARGS_TEST" in line
    )

    # This message currently wraps to three physical log lines.
    relevant_log_lines = log_lines[start_index:start_index + 3]

    # --- diagnostics ---------------------------------------------------------
    print("\n***********************")
    print("test_05_left_indent_no_prefix_wrap_and_console_style()")

    print("\ncaptured.out repr:")
    print(repr(captured.out))

    print("\nconsole_line repr:")
    print(repr(console_line))

    print("\nconsole_line_plain repr:")
    print(repr(console_line_plain))

    print("\nfull log_content:")
    print(log_content)

    print("\nrelevant_log_lines:")
    for i, line in enumerate(relevant_log_lines):
        print(
            f"{i}: "
            f"len={len(line)} "
            f"starts_with_4_spaces={line.startswith(' ' * 4)} "
            f"{line!r}"
        )

    print("***********************\n")

    # --- basic routing -------------------------------------------------------
    assert "COMBINED_ARGS_TEST" in captured.out
    assert "COMBINED_ARGS_TEST" in log_content

    # --- left_indent ---------------------------------------------------------
    assert console_line_plain.startswith(" " * 4)

    assert len(relevant_log_lines) == 3
    assert all(
        line.startswith(" " * 4)
        for line in relevant_log_lines
    )

    # --- no_prefix -----------------------------------------------------------
    assert "| INFO" not in console_line_plain

    assert all(
        "| INFO" not in line
        for line in relevant_log_lines
    )

    # --- log_wrap_width ------------------------------------------------------
    assert all(
        len(line) <= 80
        for line in relevant_log_lines
    )

    # console_style is intentionally not asserted via ANSI escape sequences.
    # Its validation is covered separately; this test confirms that supplying
    # console_style does not interfere with left_indent, no_prefix, or
    # log_wrap_width.


# === Structured strings ======================================================


# --- test_06_structured_message_preserves_edge_and_interior_newlines() -------
def test_06_structured_message_preserves_edge_and_interior_newlines(
    tmp_path: Path,
    capsys,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        console_prefix="level",
        log_prefix="level",
    )

    log_file_path = log.main_log_file_path
    assert log_file_path is not None

    message = (
        "\n"
        "STRUCTURED_LINE_ONE\n"
        "\n"
        "STRUCTURED_LINE_THREE\n"
    )

    log.info(
        message,
        left_indent=4,
    )

    captured = capsys.readouterr()

    log.close()

    log_content = _read_main_log(log_file_path)

    expected_block = (
        "\n"
        "    STRUCTURED_LINE_ONE\n"
        "\n"
        "    STRUCTURED_LINE_THREE\n"
    )

    assert expected_block in captured.out
    assert expected_block in log_content


# --- test_07_structured_message_is_not_rewrapped() ---------------------------
def test_07_structured_message_is_not_rewrapped(
    tmp_path: Path,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        console_verbosity=0,
        log_verbosity=3,
        log_prefix="off",
        log_wrap_width=80,
    )

    log_file_path = log.main_log_file_path
    assert log_file_path is not None

    long_line = (
        "STRUCTURED_LONG_LINE this line is intentionally much longer than eighty "
        "characters so that the test can verify structured content is preserved "
        "without automatic wrapping."
    )

    log.info(
        f"{long_line}\nsecond line",
        left_indent=3,
    )

    log.close()

    log_content = _read_main_log(log_file_path)

    assert f"   {long_line}" in log_content
    assert "   second line" in log_content


# === Rich Text ===============================================================


# --- test_08_rich_text_accepts_left_indent() ---------------------------------
def test_08_rich_text_accepts_left_indent(
    tmp_path: Path,
    capsys,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        console_prefix="level",
        log_prefix="level",
    )

    log_file_path = log.main_log_file_path
    assert log_file_path is not None

    rich_message = Text()
    rich_message.append("RICH_INDENT_TEST ", style="bold")
    rich_message.append("styled Rich Text", style="green")

    log.info(
        rich_message,
        left_indent=5,
    )

    captured = capsys.readouterr()

    log.close()

    console_output = strip_ansi(captured.out)
    log_content = _read_main_log(log_file_path)

    # Console retains Rich rendering but applies Rich Padding.
    assert "     RICH_INDENT_TEST styled Rich Text" in console_output

    # Log converts Rich Text to plain text and applies normal text indentation.
    assert "     RICH_INDENT_TEST styled Rich Text" in console_output
    assert "     RICH_INDENT_TEST styled Rich Text" in log_content


# --- test_09_rich_text_multiline_left_indent() -------------------------------
def test_09_rich_text_multiline_left_indent(
    tmp_path: Path,
    capsys,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        console_prefix="level",
        log_prefix="level",
    )

    log_file_path = log.main_log_file_path
    assert log_file_path is not None

    rich_message = Text()
    rich_message.append("RICH_LINE_ONE", style="bold")
    rich_message.append("\n")
    rich_message.append("RICH_LINE_TWO", style="green")

    log.info(
        rich_message,
        left_indent=6,
    )

    captured = capsys.readouterr()

    log.close()

    console_output = strip_ansi(captured.out)
    log_content = _read_main_log(log_file_path)

    assert "      RICH_LINE_ONE" in console_output
    assert "      RICH_LINE_TWO" in console_output

    assert "      RICH_LINE_ONE" in log_content
    assert "      RICH_LINE_TWO" in log_content
