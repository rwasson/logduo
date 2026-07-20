"""
level_entry.py

_level_entry() is the single normalized entry path for all public log calls.

Guarantees:
     - unsupported kwargs filtering
     - preservation of _NOT_GIVEN values
     - rejection of user-passed None values
     - level / label normalization
     - sink_name normalization
     - capture of raw per-call call_args

 _level_entry() does NOT:
     - resolve final effective call_args
     - perform routing decisions
     - apply sink-specific defaults
     - perform formatting or emission

Final call_arg resolution occurs separately per destination inside dispatcher.

Example:
     log.info(...)
         -> sink_name = "main_sink"

     audit = log.new_logger("audit")
     audit.warning(...)
         -> sink_name = "audit"

Last edited: 2026-5-27
"""
from __future__ import annotations

import re
import sys
import traceback
from linecache import getline
from pathlib import Path
from textwrap import wrap
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from logduo.logduo import Duo

# Use standalone wrapping here rather than emitter wrapping helpers.
# Traceback blocks manage their own fixed-width layout.
from rich.text import Text

from logduo.internals.engine.dispatcher import _dispatch_event
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.filesystem.callsite_utils import _get_caller, _trim_stack_lines
from logduo.internals.session_config.session_constants import (
    _MAX_VERBOSITY_LEVEL,
    _NOT_GIVEN,
    _NotGiven,
)


# --- _level_entry() -----------------------------------------------------------
def _level_entry(
    duo: Duo,
    message: object,
    *,
    level: str,
    label: str | None = None,  # passed internally by Logduo
    # --- prefix / structure ---
    no_prefix: bool | _NotGiven = _NOT_GIVEN,
    log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
    console_style: str | _NotGiven = _NOT_GIVEN,
    # internal warn flag for JSONL
    event_type: str = "message",
    warn_key: str | None = None,
    sink_name: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Dispatcher should always receive a concrete routing name.

    Valid console_style values:
        - Rich style strings
            Example: "italic blue", "bold red", "underline"
        - Internal Logduo theme keys
            Example: "warning", "muted", "title"

    Theme keys are supported for Logduo internal calls because the
    Console is initialized in console.py with:
        Console(theme=Theme(console_theme_dict))
    allowing Rich to resolve theme names at render time.

    """
    if sink_name is None:
        sink_name = "main_sink"
    if sink_name == "system":
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: "
            "'system' is an invalid value for sink_name. "
            "Internal events should still use sink_name='main_sink'."
            "Use event_type for system classification. "
        )

    level_up = level.upper()
    effective_label = (label or level_up).upper()

    # --- Catch unsupported kwargs early ---
    if kwargs:
        _filter_level_kwargs(duo, label=effective_label, kwargs=kwargs)

    # --- Ensure runtime ready ---
    duo._ensure_initialized()

    # -- Ensure user did not pass None as arg value ---
    # this must come BEFORE Normalize (console_style, a Rich passthrough, can be None)
    _raise_if_none(
        no_prefix=no_prefix,
        log_wrap_width=log_wrap_width,
        console_style=console_style,
    )


    # --- Capture raw call_args (no validation yet) ---
    # depends on sink destination
    call_args = {
        "no_prefix": no_prefix,
        "log_wrap_width": log_wrap_width,
        "console_style": console_style,
    }

    _dispatch_event(
        duo,
        sink_name=sink_name,
        level=level_up,
        label=effective_label,
        message=message,
        # --- routing / structure (RAW VALUES) ---
        call_args=call_args,
        warn_key=warn_key,
        event_type=event_type,
    )


# --- _exception_entry() -------------------------------------------------------
def _exception_entry(
    duo: Duo,
    message: object | None = None,
    *,
    sink_name: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Emit ERROR message plus formatted traceback block.
    Tracebacks are emitted through normal routing paths so
    console, log sinks, and JSONL remain synchronized.
    """
    duo._ensure_initialized()

    line = message or "Unhandled exception"

    _level_entry(duo, line, level="ERROR", label="ERROR", sink_name=sink_name, **kwargs)

    _emit_traceback_block(duo, sink_name=sink_name)


# === Internal helpers =========================================================


# --- _filter_level_kwargs() -----------------------------------------------------------------
def _filter_level_kwargs(duo: Duo, *, label: str, kwargs: dict[str, Any]) -> None:
    """Warn once for unsupported kwargs passed to any log-level method."""
    if not kwargs:
        return

    unknowns = ", ".join(kwargs.keys())

    filepath, lineno = _get_caller()

    # Use project directory as the shortening anchor.
    display_path = _build_path_display_label(
        filepath,
        anchor_dir=duo._runtime.project_dir_path_abs,
    )

    raw_line = getline(filepath, lineno).rstrip("\n")
    source_line = f" ⇒ {raw_line.strip()}" if raw_line.strip() else ""

    warn_msg = (
        f"Ignored unsupported argument(s): {unknowns} → "
        f"in {label} logging call at {display_path}:{lineno}{source_line}"
    )
    _runtime_warning(duo, warn_msg=warn_msg)
    kwargs.clear()


# --- _emit_traceback_block() --------------------------------------------------
def _emit_traceback_block(
        duo: Duo,
        *,
        sink_name: str | None = None,
) -> None:
    # Traceback output should use the same sink-aware path as normal log calls.

    # This lets dispatcher handle main log, user sinks, console, and JSONL.
    session_config = duo.session_config
    log_v = session_config.log_verbosity
    exc_type, exc_val, exc_tb = sys.exc_info()

    if not exc_tb:
        return
    traceback_lines = traceback.format_exception(exc_type, exc_val, exc_tb)
    if log_v < _MAX_VERBOSITY_LEVEL:
        traceback_lines = _trim_stack_lines(traceback_lines, head=12, tail=8)
    block = "".join(traceback_lines).rstrip()
    if block.count("Traceback (most recent call last):") == 1 and "During handling" not in block:
        block = block.replace("Traceback (most recent call last):", "Traceback:", 1)
    anchor_dir = duo._runtime.project_dir_path_abs
    block = re.sub(
        r'File "([^"]+)"',
        lambda match: (
            f'File "{
                _build_path_display_label(
                    match.group(1),
                    anchor_dir=anchor_dir,
                )
            }"'
        ),
        block,
    )
    block = _indent_traceback_lines(block)
    traceback_text = _build_traceback_text_box(
        block,
        title=f"Traceback {exc_type.__name__ if exc_type else ''}".rstrip(),
        theme=session_config.console_theme,
        width=session_config.console_wrap_width,
    )
    _level_entry(
        duo,
        traceback_text,
        level="ERROR",
        label="ERROR",
        no_prefix=False,
        log_wrap_width="off",
        console_style=_NOT_GIVEN,
        sink_name=sink_name,
    )


# --- _build_traceback_text_box() ----------------------------------------------
def _build_traceback_text_box(block: str, *, title: str, theme: str, width: int) -> Text:
    """Render traceback block as Rich Text with fixed-width borders."""
    border_style = "red" if theme == "dark" else "red3"

    # Keep room for:
    #   "│ " + content + " │"
    traceback_width = min(max(width, 40), 100)
    inner_width = max(traceback_width - 4, len(title) + 2, 40)

    raw_lines = block.splitlines() or [""]

    wrapped_lines: list[str] = []
    for line in raw_lines:
        if not line:
            wrapped_lines.append("")
            continue

        wrapped = wrap(
            line,
            width=inner_width,
            replace_whitespace=False,
            drop_whitespace=False,
            break_long_words=True,
            break_on_hyphens=False,
        )
        wrapped_lines.extend(wrapped or [""])

    top = f"╭─ {title} " + "─" * max(0, inner_width - len(title) - 1) + "╮"
    bottom = "╰" + "─" * (inner_width + 2) + "╯"

    text = Text()
    text.append(top + "\n", style=border_style)

    for line in wrapped_lines:
        text.append("│ ", style=border_style)
        text.append(line.ljust(inner_width))
        text.append(" │\n", style=border_style)

    text.append(bottom, style=border_style)

    return text


# ---  _indent_traceback_lines() -----------------------------------------------
def _indent_traceback_lines(block: str) -> str:
    """
    Pretty-print traceback lines by breaking the 'line N, in func'
    clause onto a new indented line.

    Example:
      File "/path/to/foo.py", line 123, in my_func
    becomes:
      File "/path/to/foo.py"
            line 123, in my_func
    """
    return re.sub(r'(File ".*?"), line (\d+), in ([^\n]+)', r"\1\n      line \2, in \3", block)


# --- _raise_if_none() ---------------------------------------------------------------------
def _raise_if_none(
    *,
    no_prefix: bool | _NotGiven,
    log_wrap_width: int | str | _NotGiven,
    console_style: str | _NotGiven,
) -> None:
    if no_prefix is None:
        raise ValueError("no_prefix does not accept None; omit the argument instead")

    if log_wrap_width is None:
        raise ValueError("log_wrap_width does not accept None; omit the argument instead")

    if console_style is None:
        raise ValueError("console_style does not accept None; omit the argument instead")


# --- _build_path_display_label() ---------------------------------------------
def _build_path_display_label(
    path: str | Path,
    *,
    anchor_dir: Path | None,
) -> str:
    path_abs = Path(path)
    if anchor_dir is not None:
        try:
            return str(path_abs.relative_to(anchor_dir.parent))
        except ValueError:
            pass
    return str(path_abs)
