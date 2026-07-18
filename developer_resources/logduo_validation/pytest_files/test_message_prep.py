"""
test_message_prep.py
"""
import pytest
from rich.text import Text

from logduo.internals.engine.runtime_classes import MessageKind
from logduo.internals.formatters.message_prep import (
    _build_plain_message,
    _message_kind,
    _prepare_text_block,
    _to_plain_log_text, _prepare_log_payload,
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


# --- test_13_prepare_log_payload_no_prefix_uses_full_width() ------------------
def test_13_prepare_log_payload_no_prefix_uses_full_width():

    message = "one two three four"

    result_without_prefix = _prepare_log_payload(
        msg=message,
        message_kind=MessageKind.INLINE,
        no_prefix=True,
        prefix="LONG PREFIX ",
        cfr_continuation_prefix_len=12,
        log_wrap_width=18,
    )

    result_with_prefix = _prepare_log_payload(
        msg=message,
        message_kind=MessageKind.INLINE,
        no_prefix=False,
        prefix="LONG PREFIX ",
        cfr_continuation_prefix_len=12,
        log_wrap_width=18,
    )

    assert len(result_without_prefix.splitlines()) <= len(
        result_with_prefix.splitlines()
    )


# --- test_14_prepare_log_payload_single_line_rich_text_wraps() ----------------
def test_14_prepare_log_payload_single_line_rich_text_wraps():

    result = _prepare_log_payload(
        msg="one two three four five",
        message_kind=MessageKind.RICH_TEXT,
        no_prefix=True,
        prefix="",
        cfr_continuation_prefix_len=0,
        log_wrap_width=12,
    )

    assert "\n" in result


# --- test_15_prepare_log_payload_structured_rich_text_does_not_wrap() ---------
def test_15_prepare_log_payload_structured_rich_text_does_not_wrap():

    message = "first line\nsecond line"

    result = _prepare_log_payload(
        msg=message,
        message_kind=MessageKind.RICH_TEXT,
        no_prefix=True,
        prefix="",
        cfr_continuation_prefix_len=0,
        log_wrap_width=12,
    )

    assert result == message


# --- test_16_prepare_log_payload_object_wraps() -------------------------------
def test_16_prepare_log_payload_object_wraps():

    result = _prepare_log_payload(
        msg="one two three four five",
        message_kind=MessageKind.OBJECT,
        no_prefix=True,
        prefix="",
        cfr_continuation_prefix_len=0,
        log_wrap_width=12,
    )

    assert "\n" in result


# --- test_17_prepare_log_payload_rich_renderable_wraps() ----------------------
def test_17_prepare_log_payload_rich_renderable_wraps():

    result = _prepare_log_payload(
        msg="one two three four five",
        message_kind=MessageKind.RICH_RENDERABLE,
        no_prefix=True,
        prefix="",
        cfr_continuation_prefix_len=0,
        log_wrap_width=12,
    )

    assert "\n" in result


# --- test_18_prepare_log_payload_invalid_message_kind_raises() ----------------
def test_18_prepare_log_payload_invalid_message_kind_raises():

    with pytest.raises(RuntimeError, match="invalid message_kind"):
        _prepare_log_payload(
            msg="hello",
            message_kind="banana",  # type: ignore[arg-type]
            no_prefix=True,
            prefix="",
            cfr_continuation_prefix_len=0,
            log_wrap_width=80,
        )


# === _to_plain_log_text() =====================================================

# --- test_19_to_plain_log_text_markup() ---------------------------------------
def test_19_to_plain_log_text_markup():

    assert _to_plain_log_text("[blue]hello[/blue]") == "hello"


# --- test_20_to_plain_log_text_invalid_markup() -------------------------------
def test_20_to_plain_log_text_invalid_markup():

    result = _to_plain_log_text("[blue")

    assert result == "[blue"


# --- test_21_to_plain_log_text_ansi() -----------------------------------------
def test_21_to_plain_log_text_ansi():

    result = _to_plain_log_text(
        "\x1b[31mhello\x1b[0m"     # noqa
    )

    assert result == "hello"


# --- test_22_invalid_markup_still_strips_ansi() -------------------------------
def test_22_invalid_markup_still_strips_ansi():

    result = _to_plain_log_text(
        "\x1b[31m[/missing]\x1b[0m"
    )

    assert result == "[/missing]"
    assert "\x1b[" not in result


# === _build_plain_message() ===================================================

# --- test_23_build_plain_message_string() -------------------------------------
def test_23_build_plain_message_string():

    assert _build_plain_message("[red]hello[/red]") == "hello"


# --- test_24_build_plain_message_rich_text() ----------------------------------
def test_24_build_plain_message_rich_text():

    assert _build_plain_message(Text("hello")) == "hello"


# --- test_25_build_plain_message_regular_object() -----------------------------
def test_25_build_plain_message_regular_object():

    result = _build_plain_message(
        {
            "a": 1,
        }
    )

    assert result == "{'a': 1}"


# --- test_26_build_plain_message_unprintable_object() -------------------------
def test_26_build_plain_message_unprintable_object():

    class Unprintable:
        def __str__(self):
            raise ValueError("cannot convert")

    result = _build_plain_message(Unprintable())

    assert result == "<unprintable object>"






