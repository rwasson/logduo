"""
callsite_utils.py

Utilities for:
- caller/frame inspection
- traceback trimming
- source-prefix shortening
- sink/file-name validation

Used by dispatcher, traceback formatting, and sink validation.

Last edited: 2026-5-27
"""

from __future__ import annotations

import os
import sys
from types import FrameType

from logduo.internals.session_config.session_constants import (
    _CALLSITE_MAX_LINE_NUM_DISPLAY_WIDTH,
    _CALLSITE_MAX_SOURCE_DISPLAY_WIDTH,
    _PACKAGE_NAME,
)

_MIN_CHUNK_SIZE = 3

# --- _trim_stack_lines() ------------------------------------------------------
def _trim_stack_lines(lines: list[str], *, head: int, tail: int) -> list[str]:
    """Collapse middle traceback lines while preserving head/tail context."""
    if len(lines) <= head + tail + 1:
        return lines
    return lines[:head] + ["    ... (elided) ...\n"] + lines[-tail:]


# --- _shorten_middle_with_ellipsis() ------------------------------------------
def _shorten_middle_with_ellipsis(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    if max_len <= _MIN_CHUNK_SIZE:
        return text[:max_len]
    left = (max_len - _MIN_CHUNK_SIZE) // 2
    right = max_len - _MIN_CHUNK_SIZE - left
    return f"{text[:left]}...{text[-right:]}"


# --- _shorten_callsite_for_prefix() ---------------------------------------------
def _shorten_callsite_for_prefix(
    file_name: str,
    line_num: int,
    max_chars: int = _CALLSITE_MAX_SOURCE_DISPLAY_WIDTH,
   max_callsite_num_width: int = _CALLSITE_MAX_LINE_NUM_DISPLAY_WIDTH,
) -> str:
    """Max of 36 characters long."""
    base = os.path.basename(file_name)
    # Interactive sessions and interpreter-generated pseudo-files, e.g. <input>
    # are not useful for user-facing source prefixes.
    if base.startswith("<") and base.endswith(">"):
        return ""
    short_source = _shorten_middle_with_ellipsis(base, max_chars)

    line_num_str = str(line_num)

    if len(line_num_str) > max_callsite_num_width:
        line_num_str = ">" + ("9" * max_callsite_num_width)  # noqa: PLR2004

    return f"{short_source}:{line_num_str}"


# --- _get_caller() ------------------------------------------------------------
def _get_caller() -> tuple[str, int]:
    """Return first external caller outside the logduo package (efficient)."""

    frame: FrameType | None = sys._getframe(2)

    while frame:
        module_name = str(frame.f_globals.get("__name__", ""))
        if module_name != _PACKAGE_NAME and not module_name.startswith(f"{_PACKAGE_NAME}."):
            return frame.f_code.co_filename, frame.f_lineno

        frame = frame.f_back

    return "<unknown>", 0


'''
# KEEP in case later need to revert to more time-intensive look back

import inspect
# --- _get_caller() ------------------------------------------------------------
def _get_caller() -> tuple[str, int]:
    """ Return first external caller outside the logduo package (exact). """
    current_module = __name__.split(".")[0]
    for frame_info in inspect.stack()[2:]:
        mod = inspect.getmodule(frame_info.frame)
        if not mod or not mod.__name__.startswith(current_module):
            return frame_info.filename, frame_info.lineno
    top = inspect.stack()[2]
    return top.filename, top.lineno
'''
