"""
level_call_args_resolver.py

The resolver functions convert raw user arg values into valid, allowed values.
Resolved values are used by dispatcher.py to build messages to send to emitters.

After resolution, for call args:
- Allowed values include: "off", user_value
- User-provided None or 'auto' is NOT allowed for these fields → raises error
- None may be introduced internally during resolution ONLY for: console_style
      this is a passthrough field to satisfy requirements of other package (Rich)
- No values remain:
    - _NOT_GIVEN
    - invalid types or values
- Default handling:
    - If default_value is available → _NOT_GIVEN → default_value
- Cross-field rules applied here, e.g., no_prefix is True -> subsequent_indent = "off"

Last edited: 2026-5-27
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from logduo.internals.engine.runtime_classes import CreatedFileRecord

from logduo.internals.session_config.session_config_classes import SessionConfig

if TYPE_CHECKING:
    from logduo import Duo

from logduo.internals.api_arg_resolvers.api_arg_resolver_helpers import (
    _assert_no_none,
    _assert_no_not_given,
    _resolve_call_console_style,
    _resolve_call_log_wrap_width,
    _resolve_call_no_prefix,
)


# --- _resolve_level_call_args() -----------------------------------------------
def _resolve_level_call_args(
    duo: Duo,
    is_console_sink: bool,
    sink_config: SessionConfig | CreatedFileRecord,
    call_args: dict[str, Any],
) -> dict[str, Any]:
    """Resolve normalized call arguments for dispatcher use."""
    no_prefix = _resolve_call_no_prefix(
        is_console_sink=is_console_sink,
        sink_config=sink_config,
        no_prefix=call_args["no_prefix"])

    theme_dict = duo.session_config.console_theme_dict
    console_style = _resolve_call_console_style(
        console_style=call_args["console_style"],
        theme_dict=theme_dict,
    )

    norm_call = {
        "no_prefix": no_prefix,
        "log_wrap_width": _resolve_call_log_wrap_width(
            duo=duo,
            sink_config=sink_config,
            log_wrap_width=call_args["log_wrap_width"]
        ),
        "console_style": console_style,
    }

    _assert_no_not_given(norm_call)
    _assert_no_none(norm_call, allowed_fields={"console_style"})

    return norm_call
