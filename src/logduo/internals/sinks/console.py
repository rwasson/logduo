"""
console.py

Initialize, emit, and close for console.

Lifecycle:
    - initialize: configure console (Rich), emit header
    - emit: render per-line output (string or Rich object)
    - end: emit footer / finalize output

Dependencies:
    - execution values: event (message, renderable, call args)
    - global values: duo.session_config (frozen at startup)

Contract:
    - All configuration is resolved before per-line emit
    - No `_NOT_GIVEN` or "auto" values reach per-line emit
    - No resolution occurs during per-line emit
    - Lifecycle builders may resolve deferred values (e.g. "auto" headers/footers)

Notes:
    - No per-sink session_config object; for  console, all values originate from SessionConfig
    - Supports Rich renderables; formatting handled at render time


Last edited: 2026-05-27
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo


from rich.console import Console, RenderableType
from rich.protocol import is_renderable
from rich.text import Text
from rich.theme import Theme

from logduo.internals.engine.runtime_classes import EmitEvent
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.formatters.console_header_footer_builders import (
    _build_console_footer,
    _build_console_header,
)
from logduo.internals.formatters.message_prep import (
    _prepare_text_block,
    MessageKind,
)
from logduo.internals.formatters.prefix_builder import (
    _build_prefix,
    _compute_continuation_prefix_len,
)
from logduo.internals.formatters.safe_console_print import _safe_console_print


# --- _initialize_console() ----------------------------------------------------
def _initialize_console(duo: Duo) -> None:
    session_config = duo.session_config

    color_enabled = session_config.console_color

    # --- Resolve Rich terminal/color behavior ---
    # Rich auto-detection is unreliable in some IDE consoles
    if color_enabled:
        if sys.stdout.isatty() or any(
            k in os.environ for k in ("PYCHARM_HOSTED", "TERM_PROGRAM", "VSCODE_PID")
        ):
            force_terminal, no_color = True, None
        else:
            force_terminal, no_color = None, True
    else:
        force_terminal, no_color = None, True

    palette = session_config.console_theme_dict

    if not isinstance(palette, Mapping) or not palette:
        raise RuntimeError(
            " LOGDUO INTERNAL ERROR: console_theme_dict missing or invalid after validation. "
            "This indicates an internal bug; please report your session_config."
        )

    # --- Build console ---
    # Registers Logduo theme keys ("warning", "muted", etc.) saved in palette
    # as valid Rich style names for this Console instance.
    duo._console = Console(
        stderr=False,
        theme=Theme(palette),
        force_terminal=force_terminal,
        no_color=no_color,
        highlight=False,
        soft_wrap=False,
        width=duo.session_config.console_wrap_width,
    )

    if duo._console is None:
        raise RuntimeError(" LOGDUO INTERNAL ERROR: console unavailable.")

    # --- Derive continuation-prefix indentation ---
    duo._runtime.console_continuation_prefix_len = _compute_continuation_prefix_len(
        prefix_mode=session_config.console_prefix
    )

    # --- Claim ownership if enabled ---
    if session_config.first_instance_owns_console:
        os.environ.setdefault("LOGDUO_CONSOLE_OWNER", str(duo._runtime.pid))

    # --- Build console header ---
    if session_config.console_header != "off":
        console_header = _build_console_header(
            runtime=duo._runtime,
            console_header=session_config.console_header,
            styles=session_config.console_theme_dict,
        )

        # --- Emit console header ---
        if session_config.console_verbosity >= 1 and console_header is not None:
            _emit_console_payload(
                duo=duo,
                prefix=Text(),
                payload=console_header,
                message_kind=MessageKind.STRUCTURED,
                console_style=None,
                no_prefix=True,
            )


# --- _emit_console() ----------------------------------------------------------
def _emit_console(duo: Duo, *, event: EmitEvent) -> None:

    session_config = duo.session_config
    runtime = duo._runtime

    rca = event.resolved_call_args
    no_prefix = rca["no_prefix"]
    console_style = rca["console_style"]

    # --- 1. Normalize message into console-displayable payload ---
    # Returns: str, Text, Rich renderable, None (suppressed)
    msg = _build_console_message(
        message=event.message,
        console_style=console_style,
    )
    if msg is None:
        return

    # --- 2. build prefix ---
    prefix = _build_prefix(
        duo=duo,
        level_label=event.label,
        no_prefix=no_prefix,
        callsite=event.callsite,
        prefix_mode=session_config.console_prefix,
        is_log=False,
        sink_tag=event.sink_tag,
    )
    assert isinstance(prefix, Text), "LOGDUO INTERNAL ERROR: console prefix must be Rich Text."

    # --- 3. resolve layout + prepare payload --------------------------------
    message_kind = event.message_kind
    payload: str | Text | RenderableType

    # --- string messages ---
    if isinstance(event.message, str):
        if no_prefix or session_config.console_prefix == "off":
            first_line_prefix_len = 0
            continuation_prefix_len = 0
        else:
            first_line_prefix_len = len(prefix.plain)
            continuation_prefix_len = runtime.console_continuation_prefix_len

        line_width = session_config.console_wrap_width

        if not isinstance(msg, str):
            raise RuntimeError("String input must produce string payload")
        if message_kind == MessageKind.INLINE:
            should_wrap = True
        elif message_kind == MessageKind.STRUCTURED:
            should_wrap = False
        else:
            raise RuntimeError("Invalid message_kind for string")

        payload = _prepare_text_block(
            text=msg,
            first_line_prefix_len=first_line_prefix_len,
            continuation_prefix_len=continuation_prefix_len,
            line_width=line_width,
            wrap=should_wrap,
        )

    # --- event.message is TEXT (Rich Text) ---
    elif isinstance(event.message, Text):
        if not isinstance(msg, Text):
            raise RuntimeError("Text input must produce Text payload")
        payload = msg

    # --- event.message is other RICH OBJECT (Panel, Table, etc.) ---
    elif is_renderable(event.message):
        # console can display event.message
        if not is_renderable(msg):
            raise RuntimeError("Renderable input must produce renderable payload")
        payload = msg

    # --- OTHER OBJECT (non-renderable -> str) ---
    else:
        text = str(msg)
        if no_prefix or session_config.console_prefix == "off":
            first_line_prefix_len = 0
            continuation_prefix_len = 0

        else:
            first_line_prefix_len = len(prefix.plain)
            continuation_prefix_len = runtime.console_continuation_prefix_len

        payload = _prepare_text_block(
            text=text,
            first_line_prefix_len=first_line_prefix_len,
            continuation_prefix_len=continuation_prefix_len,
            line_width=session_config.console_wrap_width,
            wrap=True,
        )

    # --- 4. emit payload ---
    # Take already-prepared payload → decide WHERE prefix goes and print
    _emit_console_payload(
        duo=duo,
        prefix=prefix,
        payload=payload,
        message_kind=message_kind,
        console_style=console_style,
        no_prefix=no_prefix,
    )


# --- _emit_console_end() ------------------------------------------------------
def _emit_console_end(duo: Duo) -> None:
    if duo._console is None:
        return

    session_config = duo.session_config

    # --- Build console footer ---
    console_footer = _build_console_footer(
        runtime=duo._runtime,
        console_footer=session_config.console_footer,
        console_wrap_width=session_config.console_wrap_width,
        styles=session_config.console_theme_dict,
    )

    # --- Emit console footer ---
    if session_config.console_verbosity >= 1 and console_footer is not None:
        _emit_console_payload(
            duo=duo,
            prefix=Text(),
            payload=console_footer,
            message_kind=MessageKind.STRUCTURED,
            console_style=None,
            no_prefix=True,
        )


# === Internal helpers =========================================================

# --- _build_console_message() -------------------------------------------------
def _build_console_message(
    *,
    message: Any,
    console_style: str | None,
) -> Any | None:
    """
    Build one console-ready message payload.
    Rules:
        - str -> unchanged
        - Rich Text -> copied and optionally styled
        - Rich/renderable -> preserved as-is for console rendering
        - non-renderable object -> converted to string
    """
    if isinstance(message, str):
        return message

    if isinstance(message, Text):
        # Note: console style may override style inside of text_obj
        text_obj = message.copy()
        if console_style:
            text_obj.stylize(console_style)
        return text_obj

    if is_renderable(message):
        return message

    try:
        return str(message)
    except (TypeError, ValueError):
        return "<unprintable object>"




# --- _emit_console_payload() --------------------------------------------------
def _emit_console_payload(
    duo: Duo,
    *,
    prefix: Text,
    payload: Any,
    message_kind: MessageKind,
    console_style: str | None,
    no_prefix: bool,
) -> None:
    """
    Takes already-prepared payload → decide WHERE prefix goes and prints
    """

    # --- strings / str(object) ---
    if isinstance(payload, str):
        # INLINE (contains no '/n') → prefix + single line (already wrapped if needed)
        # INLINE and str(OBJECT) -> prefix + inline text
        # Text has already been prepared/wrapped as needed.
        if message_kind in (MessageKind.INLINE, MessageKind.OBJECT):
            text_obj = (
                Text.from_ansi(payload, style=console_style)
                if console_style
                else Text.from_ansi(payload)
            )
            if no_prefix:
                _safe_console_print(duo, message=text_obj, message_kind=MessageKind.INLINE)
            else:
                line = prefix.copy()
                line.append(text_obj)
                _safe_console_print(duo, message=line, message_kind=MessageKind.INLINE)
            return

        # STRUCTURED (contains '/n') → prefix once, then full block below prefix
        if message_kind == MessageKind.STRUCTURED:
            if not no_prefix:
                _safe_console_print(duo, message=prefix, message_kind=MessageKind.STRUCTURED)

            text_obj = Text(payload, style=console_style) if console_style else Text(payload)

            _safe_console_print(duo, message=text_obj, message_kind=MessageKind.STRUCTURED)

            return

        raise RuntimeError(
            "LOGDUO INTERNAL ERROR:\n\n"
            f"String payload cannot be emitted with MessageKind={message_kind!r}."
        )


    # --- Rich Text (including object placeholders) ---
    elif isinstance(payload, Text):
        if console_style is not None:
            _runtime_warning(
                duo,
                warn_msg="console_style ignored for Rich Text; apply style inside the Text object",
            )
        if not no_prefix:
            _safe_console_print(duo, message=prefix, message_kind=MessageKind.RICH_TEXT)

        _safe_console_print(duo, message=payload, message_kind=MessageKind.RICH_TEXT)
        return

    # --- Rich Renderables (other than Text) ---
    elif is_renderable(payload):
        if not no_prefix:
            _safe_console_print(duo, message=prefix, message_kind=MessageKind.RICH_RENDERABLE)
        _safe_console_print(duo, message=payload, message_kind=MessageKind.RICH_RENDERABLE)
        return

    else:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: "
            f"unsupported console payload type "
            f"{type(payload).__name__!r}"
            f"message_kind={message_kind!r}"
        )

