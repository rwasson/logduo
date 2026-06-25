"""
prefix_builder.py

Build console and log prefix components for emitted messages.

Responsible for:
- prefix component selection
- prefix formatting for console and log outputs
- label color resolution
- prefix visibility policy (timestamp/source/pid/sink_tag)

Last edited: 2026-06-7
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from rich.text import Text

from logduo.internals.session_config.session_constants import _LINE_TIMESTAMP_FMT, _MAX_LEVEL_WIDTH


# --- _build_prefix() ----------------------------------------------------------
def _build_prefix(
    *,
    duo: Duo,
    level_label: str,
    no_prefix: bool,
    callsite: str | None,
    prefix_mode: str,
    is_log: bool,
    sink_tag: str | None = None,
) -> Text | str:
    """Build formatted console or log prefix output."""

    prefix_components = _build_prefix_components(
        duo=duo,
        level_label=level_label,
        no_prefix=no_prefix,
        callsite=callsite,
        prefix_mode=prefix_mode,
        sink_tag=sink_tag,
        is_log=is_log,
    )
    if is_log:
        return _format_prefix_log(prefix_components)
    else:
        return _format_prefix_console(duo, prefix_components)


# --- _build_prefix_components() -----------------------------------------------
def _build_prefix_components(
    *,
    duo: Duo,
    level_label: str,
    no_prefix: bool,
    callsite: str | None,
    prefix_mode: str,
    sink_tag: str | None = None,
    is_log: bool,
) -> list[dict[str, str]]:
    # ) -> tuple[list[dict[str, str]], int]:
    """Build normalized prefix component records before sink formatting."""
    runtime = duo._runtime
    components: list[dict[str, str]] = []

    need_ts, need_label, need_source, need_pid = _compute_prefix_flags(
        duo=duo,
        label=level_label,
        no_prefix=no_prefix,
        prefix_mode=prefix_mode,
        callsite=callsite,
        is_log=is_log,
    )

    if need_ts:
        timestamp_text = datetime.now().strftime(_LINE_TIMESTAMP_FMT)[:-3]
        components.append({"type": "timestamp", "text": timestamp_text})

    if need_label:
        padded_label_text = (level_label or "").upper().ljust(_MAX_LEVEL_WIDTH)
        components.append({"type": "level_label", "text": padded_label_text})

    if need_source and callsite:
        components.append({"type": "source", "text": callsite})

    if need_pid:
        pid_text = f"{runtime.pid}:i{runtime.instance_index}"
        components.append({"type": "pid", "text": pid_text})

    if sink_tag:
        # sink_tag only applies to mirrored user-sink output
        components.append({"type": "sink_tag", "text": sink_tag})

    return components


# --- _format_prefix_console() -------------------------------------------------
def _format_prefix_console(duo: Duo, prefix_components: list[dict[str, str]]) -> Text:
    """prefix for console. Edit _format_prefix_log to match"""
    session_config = duo.session_config
    prefix_text = Text()
    pipe_style = session_config.console_theme_dict["pipe"]
    sink_tag_style = session_config.console_theme_dict["sink_tag"]

    for component in prefix_components:
        component_type = component["type"]
        component_text = component["text"]

        if component_type == "timestamp":
            prefix_text.append(component_text, style="muted")

        elif component_type == "level_label":
            if component is not prefix_components[0]:
                prefix_text.append(" ")
            prefix_text.append("|", style=pipe_style)
            prefix_text.append(" ")

            color_style = _get_label_color_style(duo, component_text.strip())
            text_style = f"{color_style}" if color_style else "bold"
            prefix_text.append(component_text, style=text_style)

            prefix_text.append(" ")
            prefix_text.append("|", style=pipe_style)

        elif component_type == "source":
            prefix_text.append(" ")
            prefix_text.append(component_text, style="muted")
            prefix_text.append(" -", style="muted")

        elif component_type == "pid":
            prefix_text.append(f" ({component_text})", style="muted")

        elif component_type == "sink_tag":
            prefix_text.append(" ")
            prefix_text.append(component_text, style=f"{sink_tag_style}")
            prefix_text.append(":", style="muted")

    if prefix_components:
        prefix_text.append(" ")

    return prefix_text


# --- _format_prefix_log() -----------------------------------------------------
def _format_prefix_log(prefix_components: list[dict[str, str]]) -> str:
    """prefix for log file. Edit _format_prefix_console to match"""
    prefix = ""

    for component in prefix_components:
        component_type = component["type"]
        component_text = component["text"]
        if component_type == "timestamp":
            prefix += component_text
        elif component_type == "level_label":
            if component is not prefix_components[0]:
                prefix += " "
            prefix += f"| {component_text} |"
        elif component_type == "source":
            prefix += f" {component_text} -"
        elif component_type == "pid":
            prefix += f" ({component_text})"
        elif component_type == "sink_tag":
            prefix += f" {component_text}:"
    if prefix:
        prefix += " "
    return prefix


# ---  _get_label_color_style() ------------------------------------------------
def _get_label_color_style(duo: Duo, level_label: str) -> str | None:
    session_config = duo.session_config
    label_key = level_label.lower()

    if label_key in duo._runtime.new_levels:
        label_data = duo._runtime.new_levels[label_key]
        color = label_data[1] if len(label_data) > 1 else None
        assert color is None or isinstance(color, str)
        return color

    color = session_config.console_theme_dict.get(label_key)
    assert color is None or isinstance(color, str)
    return color


# --- _compute_prefix_flags() --------------------------------------------------
def _compute_prefix_flags(
    *, duo: Duo, label: str, no_prefix: bool, prefix_mode: str, callsite: str | None, is_log: bool
) -> tuple[bool, bool, bool, bool]:
    """
    Returns:
        need_ts, need_label, need_source, need_pid
    """

    session_config = duo.session_config
    suppress = bool(no_prefix)

    need_ts = prefix_mode in {"timestamp", "source"} and not suppress

    need_label = not suppress
    # Prefix modes always display the level label.
    # INFO is not treated specially.

    need_source = (
        ((prefix_mode == "source") or (label == "DEBUG" and session_config.show_debug_source))
        and not suppress
        and bool(callsite)
    )

    if is_log:
        need_pid = bool(session_config.show_pid_in_log)
    else:
        need_pid = bool(session_config.show_pid_in_console)
    need_pid = need_pid and not suppress

    return need_ts, need_label, need_source, need_pid


# --- _compute_continuation_prefix_len() ---------------------------------------
def _compute_continuation_prefix_len(*, prefix_mode: str) -> int:
    """Compute indentation width for wrapped continuation lines."""

    timestamp_width = len(datetime.now().strftime(_LINE_TIMESTAMP_FMT)[:-3])

    if prefix_mode in {"timestamp", "source"}:
        return (
            timestamp_width
            + 1  # space before first pipe
            + len("| ")
            + _MAX_LEVEL_WIDTH
            + len(" | ")
        )

    if prefix_mode in {"level"}:
        return len("| ") + _MAX_LEVEL_WIDTH + len(" | ")

    return 0
