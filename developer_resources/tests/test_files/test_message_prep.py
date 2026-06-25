"""
test_message_prep.py
"""

from rich.text import Text


from logduo.internals.engine.runtime_classes import MessageKind
from logduo.internals.formatters.message_prep import (
    _message_kind,
    _prepare_text_block,
    _build_plain_message,
    _to_plain_log_text,
)



# --- test_01_block_kind_inline() ---------------------------------------------
def test_01_block_kind_inline():

    assert _message_kind("hello") is MessageKind.INLINE


# --- test_02_block_kind_structured() -----------------------------------------
def test_02_block_kind_structured():

    assert _message_kind("hello\nworld") is MessageKind.STRUCTURED


# --- test_03_block_kind_object() ---------------------------------------------
def test_03_block_kind_object():

    assert _message_kind(123) is MessageKind.OBJECT


# --- test_04_prepare_text_block_no_wrap() ------------------------------------
def test_04_prepare_text_block_no_wrap():

    assert (
        _prepare_text_block(
            text="hello world",
            first_line_prefix_len=0,
            continuation_prefix_len=0,
            line_width=20,
            wrap=False,
        )
        == "hello world"
    )


# --- test_05_prepare_text_block_returns_original_when_text_fits() ---------------
def test_05_prepare_text_block_returns_original_when_text_fits():

    text = "a long message"

    assert (
        _prepare_text_block(
            text=text,
            first_line_prefix_len=30,
            continuation_prefix_len=12,
            line_width=120,
            wrap=True,
        )
        == text
    )


# --- test_06_prepare_text_block_wraps_long_text() ----------------------------
def test_06_prepare_text_block_wraps_long_text():

    result = _prepare_text_block(
        text="one two three four five six",
        first_line_prefix_len=0,
        continuation_prefix_len=0,
        line_width=12,
        wrap=True,
    )

    assert "\n" in result


# --- test_07_prepare_text_block_applies_continuation_indent() --------------
def test_07_prepare_text_block_applies_continuation_indent():
    result = _prepare_text_block(
        text="one two three four five six seven eight",
        first_line_prefix_len=0,
        continuation_prefix_len=10,
        line_width=20,
        wrap=True,
    )

    lines = result.splitlines()
    assert len(lines) > 1
    assert lines[1].startswith(" " * 10)


# --- test_08_to_plain_log_text_markup() --------------------------------------
def test_08_to_plain_log_text_markup():

    assert _to_plain_log_text("[blue]hello[/blue]") == "hello"


# --- test_09_to_plain_log_text_invalid_markup() ------------------------------
def test_09_to_plain_log_text_invalid_markup():

    result = _to_plain_log_text("[blue")

    assert result == "[blue"


# --- test_10_to_plain_log_text_ansi() ----------------------------------------
def test_10_to_plain_log_text_ansi():

    assert (
        _to_plain_log_text("\x1b[31mhello\x1b[0m")    # noqa spelling error
        == "hello"
    )


# --- test_11_build_plain_message_string() ------------------------------------
def test_11_build_plain_message_string():

    assert (_build_plain_message("[red]hello[/red]") == "hello"
    )


# --- test_12_build_plain_message_rich_text() ---------------------------------
def test_12_build_plain_message_rich_text():

    assert (_build_plain_message(Text("hello")) == "hello")







