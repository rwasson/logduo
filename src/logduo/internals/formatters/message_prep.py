"""
message_prep.py

    "_message_kind",             # Classifies message into INLINE / STRUCTURED / OBJECT
    "_prepare_text_block",     # Apply _resolve_text_layout, and prepares text_block for emission
    "_build_plain_message",    # Convert message → plain text for logs/files
    "_object_placeholder",     # Create placeholder for objects that can't be stringified (Rich,...)
    "_to_plain_log_text",      # Convert Rich/markup text to plain log-safe text
    "_effective_prefix_length", # Return the effective first-line and continuation prefix lengths

Last edited: 2026-6-11
"""

import re
from typing import Any

from rich.errors import MarkupError
from rich.protocol import is_renderable
from rich.text import Text

from logduo.internals.engine.runtime_classes import MessageKind
from logduo.internals.session_config.session_constants import _NO_WRAP_WIDTH
from logduo.utils.wrap.wrap_text import wrap_text

# === Text block helpers =======================================================


# --- _message_kind() ------------------------------------------------------------
def _message_kind(message: Any) -> MessageKind:
    """Categorize payload shape for downstream emission behavior."""
    if isinstance(message, str):
        return (
            MessageKind.INLINE
            if "\n" not in message
            else MessageKind.STRUCTURED
        )

    if isinstance(message, Text):
        return MessageKind.RICH_TEXT

    if is_renderable(message):
        return MessageKind.RICH_RENDERABLE

    return MessageKind.OBJECT


# --- _build_plain_message() ---------------------------------------------------
def _build_plain_message(
        message: Any,
) -> str | None:
    """
    Convert message to plain text for log/file output.
    Returns:
        - str  -> emit this text to the log
        - None -> suppress log output entirely

    Rules:
        - str: passes plain str
        - Rich Text converted to plain str
            * Rich markup (e.g. [blue]...[/blue]) is converted to plain text
            * ANSI escape codes are stripped
        - Other objects: converted to plain str
    """
    # strip Ansi
    if isinstance(message, str):
        return _to_plain_log_text(message)

    if isinstance(message, Text):
        return message.plain

    try:
        return str(message)
    except (TypeError, ValueError):
        return "<unprintable object>"


# --- _prepare_text_block() ----------------------------------------------------
def _prepare_text_block(
    *,
    text: str,
    first_line_prefix_len: int,
    continuation_prefix_len: int,
    line_width: int,
    wrap: bool,
) -> str:
    """
    Format a plain text message for output.

    Only INLINE text blocks should normally use wrap=True.
    """

    # --- no wrap ---
    if not wrap:
        return text

    first_width = line_width - first_line_prefix_len

    # --- continuation indent = prefix width ---
    hanging_indent = continuation_prefix_len if continuation_prefix_len >= 1 else None

    wrapped_text_block = "\n".join(
        wrap_text(
            text, width=first_width, continuation_width=line_width, hanging_indent=hanging_indent
        )
    )

    return wrapped_text_block



# --- _prepare_log_payload() ---------------------------------------------------
def _prepare_log_payload(
    *,
    msg: str,
    message_kind: MessageKind,
    no_prefix: bool,
    prefix: str,
    cfr_continuation_prefix_len: int,
    log_wrap_width: int,
) -> str:

    # --- 3. resolve layout + prepare payload --------------------------------
    if no_prefix:
        first_line_prefix_len = 0
        continuation_prefix_len = 0
    else:
        first_line_prefix_len = len(prefix)
        continuation_prefix_len = cfr_continuation_prefix_len

    line_width = log_wrap_width if log_wrap_width != "off" else _NO_WRAP_WIDTH

    # --- determine wrapping policy ---
    is_log_payload_structured = "\n" in msg

    if message_kind != MessageKind.RICH_TEXT:
        if message_kind == MessageKind.STRUCTURED:
            should_wrap = False
        elif message_kind in (MessageKind.INLINE, MessageKind.RICH_RENDERABLE, MessageKind.OBJECT):
            should_wrap = (log_wrap_width != "off")
        else:
            raise RuntimeError(
                f"LOGDUO INTERNAL ERROR: invalid message_kind {message_kind!r}"
            )
    elif message_kind == MessageKind.RICH_TEXT:
        if is_log_payload_structured:
            should_wrap = False
        else:
            should_wrap = (log_wrap_width != "off")
    else:
        raise RuntimeError(f"LOGDUO INTERNAL ERROR: invalid message_kind {message_kind!r}")

    payload = _prepare_text_block(
        text=msg,
        first_line_prefix_len=first_line_prefix_len,
        continuation_prefix_len=continuation_prefix_len,
        line_width=line_width,
        wrap=should_wrap,
    )

    return payload


# --- _to_plain_log_text() ----------------------------------------------------
def _to_plain_log_text(s: str) -> str:
    """
    Normalize a string for log/file output.

    Applies:
        - Rich markup parsing → plain text (via Text.from_markup().plain)
        - ANSI escape code stripping

    Behavior:
        - Valid Rich markup is removed, preserving readable text
        - Invalid markup is left unchanged
        - ANSI color codes are always stripped

    Intended use:
        - All log/file sinks (main log, user sinks, headers/footers)
        - Ensures logs remain clean, readable, and tool-friendly

    Does NOT affect:
        - Console rendering (Rich styling remains intact there)
    """
    try:
        plain = Text.from_markup(s).plain
    except MarkupError:
        plain = s
    return re.sub(r"\x1b\[[0-9;]*m", "", plain)
