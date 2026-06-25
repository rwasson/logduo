"""
new_logger_args_resolver.py

Resolve and validate arguments for new_logger()
before storage in UserSinkConfig

All later code related to new_logger(), is handled by user_sink_log.py

Applies:
- per-arg normalization/validation
- default resolution
- sink-path resolution
- cross-field policy rules

Final runtime-dependent setup is completed in sink setup layers.

Last edited: 2026-5-27
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from logduo.internals.api_arg_resolvers.api_arg_resolver_helpers import (
    _assert_no_none,
    _assert_no_not_given,
    _resolve_bool_arg,
    _resolve_log_file_mode,
    _resolve_log_footer,
    _resolve_log_header,
    _resolve_log_prefix,
    _resolve_log_verbosity,
    _resolve_log_wrap_width,
    _resolve_new_logger_target_arg,
    _resolve_to_main_sink_log,
)

# --- _HARD_CODED_NEW_LOGGER_ARG_DEFAULTS --------------------------------------
# remaining new_logger args inherit defaults from session_config
_HARD_CODED_NEW_LOGGER_ARG_DEFAULTS = {"to_console": True, "to_main_log": True}


# --- _resolve_new_logger_args() -------------------------------------------------
def _resolve_new_logger_args(
        *,
        duo: Duo,
        new_logger_args: dict[str, Any],
) -> dict[str, Any]:

    sink_info = _resolve_new_logger_target_arg(duo=duo, value=new_logger_args["sink"])

    # prevent creating a disabled log file
    logger_log_verbosity = _resolve_log_verbosity(
        duo=duo, log_verbosity=new_logger_args["log_verbosity"]
    )
    if logger_log_verbosity == 0:
        raise ValueError("For new_logger(), log_verbosity cannot be 0. Select from: [1, 2, 3]")

    resolved_args = {
        # --- identity ---
        "value_is_path": sink_info["value_is_path"],
        "file_path": sink_info["file_path"],
        "base_file_name_with_ext": sink_info["base_file_name_with_ext"],
        # --- routing / emission ---
        "to_console": _resolve_bool_arg(
            arg_name="to_console",
            value=new_logger_args["to_console"],
            default=_HARD_CODED_NEW_LOGGER_ARG_DEFAULTS["to_console"],
        ),
        "to_main_log": _resolve_to_main_sink_log(
            duo=duo,
            to_main_log=new_logger_args["to_main_log"],
            default=_HARD_CODED_NEW_LOGGER_ARG_DEFAULTS["to_main_log"],
        ),
        "log_verbosity": logger_log_verbosity,
        # --- path ---
        "log_file_mode": _resolve_log_file_mode(
            duo=duo, log_file_mode=new_logger_args["log_file_mode"]
        ),
        # --- formatting ---
        "log_prefix": _resolve_log_prefix(duo=duo, log_prefix=new_logger_args["log_prefix"]),
        "log_wrap_width": _resolve_log_wrap_width(
            duo=duo, log_wrap_width=new_logger_args["log_wrap_width"]
        ),
        "log_header": _resolve_log_header(log_header=new_logger_args["log_header"]),
        "log_footer": _resolve_log_footer(log_footer=new_logger_args["log_footer"]),
    }

    _assert_no_not_given(resolved_args)
    _assert_no_none(resolved_args)

    return resolved_args
