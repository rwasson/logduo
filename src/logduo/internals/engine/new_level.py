"""
new_level.py

Create user-defined log labels mapped onto existing severity levels.

Responsible for:
- label validation
- Rich color validation
- custom label registration

Last edited: 2026-5-27
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from logduo.internals.api_arg_resolvers.api_arg_resolver_helpers import _resolve_call_console_style
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.session_config.session_constants import (
    _NOT_GIVEN,
    _NotGiven,
    _RESERVED_LABELS,
    _VALID_LEVELS,
)

_MAX_LABEL_WIDTH = max(len(level) for level in _VALID_LEVELS)


# --- _create_custom_level_label() ---------------------------------------------
def _create_custom_level_label(
    duo: Duo,
    label: str,
    *,
    console_style: str | _NotGiven = _NOT_GIVEN,
    level: str = "INFO",
) -> None:
    """
    Register a custom display label mapped onto an existing severity level.
    """

    display_label = (label or "").strip().upper()
    display_label = display_label[:_MAX_LABEL_WIDTH]

    if len(display_label) < len((label or "").strip()):
        warn_msg = (
            f"Custom label '{label}' truncated to '{display_label}'"
            f" (max {_MAX_LABEL_WIDTH} chars)."
        )
        _runtime_warning(duo, warn_msg=warn_msg)

    label = display_label
    label_key = display_label.lower()
    level = level.upper()

    theme_dict = duo.session_config.console_theme_dict
    resolved_console_style = _resolve_call_console_style(
        console_style=console_style,
        theme_dict=theme_dict,
    )

    _validate_label_and_level_args(duo, label=label, level=level)

    duo._runtime.new_levels[label_key] = (label, resolved_console_style, level)



# === Internal helpers =========================================================

# --- _validate_label_and_level_args() -----------------------------------------------
def _validate_label_and_level_args(duo: Duo, *, label: str, level: str) -> None:

    if not isinstance(label, str) or not label.strip():
        raise ValueError("label must be a non-empty string")

    if label in _RESERVED_LABELS:
        raise ValueError(f"'{label}' is a reserved label name")

    if level not in _VALID_LEVELS:
        raise ValueError(f"Invalid severity '{level}'. Must be one of: {', '.join(_VALID_LEVELS)}")

    label_key = label.lower()

    # --- existing labels (with structural guard) ---
    existing = [label for label, _, _ in duo._runtime.new_levels.values()]

    if label_key in duo._runtime.new_levels:
        raise ValueError(
            f"Custom label '{label}' already exists. Existing custom labels: {', '.join(existing)}"
        )
