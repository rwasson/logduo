"""
test_wrap_text.py

Last edited: 2026-6-14
"""
from logduo.utils.wrap.wrap_text import wrap_text, _wrap_text_with_ansi, strip_ansi


# --- test_01_no_wrap_short_message() ------------------------------------------
def test_01_no_wrap_short_message():

    text = "hello world"
    lines = wrap_text(text, width=100)
    assert lines == ["hello world"]


# --- test_02_wrap_long_message() ----------------------------------------------
def test_02_wrap_long_message():

    long_msg = (
        "Logduo is designed for data scientists, researchers, students, and "
        "Python developers who want readable console output, organized log files, "
        "and minimal logging setup."
    )

    lines = wrap_text(long_msg, width=40)
    assert len(lines) > 1


# --- test_03_hanging_indent_applied() -----------------------------------------
def test_03_hanging_indent_applied():

    long_msg = (
        "Logduo is designed for data scientists, researchers, students, and "
        "Python developers who want readable console output, organized log files, "
        "and minimal logging setup."
    )

    lines = wrap_text(
        long_msg,
        width=40,
        continuation_width=40,
        hanging_indent=4,
    )

    assert len(lines) > 1
    for line in lines[1:]:
        assert line.startswith("    ")


# --- test_04_ansi_no_wrap_preserves_text() ------------------------------------
def test_04_ansi_no_wrap_preserves_text():

    red = "\033[31m"
    reset = "\033[0m"

    text = f"{red}hello world{reset}"
    wrapped = _wrap_text_with_ansi(text, width=100)

    assert len(wrapped) == 1
    line = wrapped[0]
    assert text[line.start:line.end] == line.text
    assert line.text == text


# --- test_05_ansi_wrap_preserves_slice_invariant() ----------------------------
def test_05_ansi_wrap_preserves_slice_invariant():
    red = "\033[31m"
    reset = "\033[0m"

    long_msg = (
        "Logduo is designed for data scientists, researchers, students, and "
        "Python developers who want readable console output, organized log files, "
        "and minimal logging setup."
    )

    text = f"{red}{long_msg}{reset}"
    wrapped = _wrap_text_with_ansi(
        text,
        width=40,
    )

    assert len(wrapped) > 1
    for line in wrapped:
        assert text[line.start:line.end] == line.text


# --- test_06_ansi_ignored_for_visible_width() ---------------------------------
def test_06_ansi_ignored_for_visible_width():

    red = "\033[31m"
    reset = "\033[0m"

    text = (
        f"{red}"
        "abcdefghijklmnopqrstuvwxyz"     # noqa
        "abcdefghijklmnopqrstuvwxyz"     # noqa
        f"{reset}"
    )

    wrapped = _wrap_text_with_ansi(text, width=20,)

    for line in wrapped:
        assert len(strip_ansi(line.text)) <= 20


# --- test_07_multiple_ansi_blocks() -------------------------------------------
def test_07_multiple_ansi_blocks():

    red = "\033[31m"
    blue = "\033[34m"
    reset = "\033[0m"

    text = (
        f"{red}RED{reset} "
        "normal "
        f"{blue}BLUE{reset}"
    )

    wrapped = _wrap_text_with_ansi(text, width=100)
    assert len(wrapped) == 1

    line = wrapped[0]
    assert text[line.start:line.end] == line.text


# --- test_08_wrap_text_rejects_newlines() ------------------------------------
def test_08_wrap_text_rejects_newlines():

    import pytest

    with pytest.raises(ValueError):
        wrap_text(
            "hello\nworld",
            width=20,
        )
