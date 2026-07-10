"""
session_config_resolver.py

Top level orchestrator:
Returns dictionary of final resolved configuration arg values.

Responsibilities:
- runtime script/session detection
- cwd and pyproject.toml discovery
- user/TOML config normalization
- cross-field policy application
- runtime log path derivation
- theme/header/footer derivation
- Loguru passthrough normalization



This module coordinates config resolution but does not:
- emit normal log events
- create files/directories
- attach sinks
- build SessionConfig class instance

Notes:
- Configuration warnings may be emitted immediately via
  _runtime_warning() when user-supplied settings require
  automatic normalization.

Last edited: 2026-5-27
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo


from logduo.internals.engine.runtime_classes import RuntimeRecord
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.filesystem.path_finders import (
    _derive_session_log_paths,
    _get_script_path_abs,
    _get_toml_path_abs,
)
from logduo.internals.filesystem.path_validators import _raise_if_invalid_session_config_path_fields
from logduo.internals.session_config.configure_args_normalizer import (
    _normalize_configure_args_with_defaults_and_toml,
)
from logduo.internals.session_config.session_config_classes import ArgSourceRecord
from logduo.internals.session_config.session_config_spec import (
    _session_config_hints,
    SESSION_CONFIG_SPEC,
)
from logduo.internals.sinks.loguru_integration import _probe_loguru_rotation_retention


# --- _resolve_session_config() -------------------------------------------------
def _resolve_session_config(
    duo: Duo, *, configure_args: dict[str, Any] | None, runtime: RuntimeRecord
) -> tuple[dict[str, Any], RuntimeRecord, ArgSourceRecord]:
    """
    Top-level orchestration for Logduo global config resolution.

    returns resolved session config dictionary
    """

    # --- initialize ---
    configure_args = dict(configure_args or {})
    arg_source_record = ArgSourceRecord()

    # --- forbid reserved internal values ---
    for field, value in configure_args.items():
        if isinstance(value, str) and value.strip().lower() == "auto":
            raise ValueError(
                f"Invalid value for '{field}': 'auto' is reserved for internal use. "
                "Omit the argument to use default behavior."
            )

    # --- Populate script fields in runtime ---
    # will be over-written later if interactive session
    _populate_runtime_script_fields(runtime=runtime)

    # --- Resolve cwd, TOML, and project root ---
    # keep broad Exception - cwd is foundational
    try:
        cwd_path_abs = Path.cwd()
    except Exception as e:
        raise RuntimeError(
            "Logduo could not determine the current working directory.\n\n"
            "This usually means the active working directory "
            "was deleted, moved, or is no longer accessible.\n\n"
            "Recovery options:\n"
            "  1. Restart the session from a valid directory\n"
            "  2. Or explicitly provide:\n"
            "       log_dir_path=absolute_path\n"
            "     or:\n"
            "       log_file_path=absolute_path\n\n"
            f"{type(e).__name__}: {e}"
        ) from e
    runtime.cwd_path_abs = cwd_path_abs
    assert runtime.cwd_path_abs is not None

    toml_path_abs, warn_msg = _get_toml_path_abs(cwd_path_abs=runtime.cwd_path_abs)
    if warn_msg:
        # pyproject.toml found but unreadable (-> toml_path_abs = None)
        _runtime_warning(duo, warn_msg=warn_msg)
    runtime.toml_path_abs = toml_path_abs

    # --- Populate project_dir_path_abs in runtime ---
    if runtime.toml_path_abs is not None:
        runtime.project_dir_path_abs = runtime.toml_path_abs.parent
    else:
        runtime.project_dir_path_abs = runtime.cwd_path_abs

    # --- Normalize user config (policies applied later) ---
    normalized_session_config, arg_source_dict, toml_record = (
        _normalize_configure_args_with_defaults_and_toml(
            toml_path_abs=runtime.toml_path_abs,
            configure_args=configure_args,
            session_config_spec=SESSION_CONFIG_SPEC,
            session_config_hints=_session_config_hints,
        )
    )
    arg_source_record.arg_source_dict = arg_source_dict
    arg_source_record.toml_record = toml_record

    # record toml used flag to runtime for display in footers
    runtime.toml_args_used = bool(toml_record.get("toml_args_used"))

    # --- Apply policies ---
    resolved_session_config = _apply_session_config_policies(
        duo,
        normalized_session_config=normalized_session_config,
        arg_source_record=arg_source_record,
    )

    # --- Runtime path derivation ---
    # resolved paths stored in runtime, not in session_config
    _populate_runtime_log_paths(resolved_config=resolved_session_config, runtime=runtime)

    # --- Final sanity checks ---
    from logduo.internals.api_arg_resolvers.api_arg_resolver_helpers import (
        _assert_no_none,
        _assert_no_not_given,
    )

    _assert_no_not_given(resolved_session_config)

    _assert_no_none(
        resolved_session_config, allowed_fields={"rotation", "retention", "compression"}
    )

    return resolved_session_config, runtime, arg_source_record


# --- _apply_session_config_policies() ------------------------------------------
def _apply_session_config_policies(
    duo: Duo, *, normalized_session_config: dict[str, Any], arg_source_record: ArgSourceRecord
) -> dict[str, Any]:

    normalized_session_config = dict(normalized_session_config or {})

    normalized_session_config = _raise_if_invalid_session_config_path_fields(
        normalized_session_config=normalized_session_config
    )

    # --- resolve cross-validation path conflicts ---
    # e.g., if user provides log_file, then log_file_layout = "flat"
    normalized_session_config = _resolve_path_conflicts(
        duo,
        normalized_session_config=normalized_session_config,
        arg_source_record=arg_source_record,
    )

    # --- theme derivation ---
    _apply_theme_derivation(resolved_config=normalized_session_config)

    # --- header/footer normalization ---
    _apply_header_footer_policy(resolved_config=normalized_session_config)

    # --- Loguru passthrough normalization ---
    if normalized_session_config.get("rotation") == "off":
        normalized_session_config["rotation"] = None
    if normalized_session_config.get("retention") == "off":
        normalized_session_config["retention"] = None
    if normalized_session_config.get("compression") == "off":
        normalized_session_config["compression"] = None

    # --- validate Loguru passthroughs ---
    _probe_loguru_rotation_retention(config=normalized_session_config)

    return normalized_session_config


# === Internal policy helpers for _apply_session_config_policies() ==============


# --- _resolve_path_conflicts() -------------0----------------------------------
def _resolve_path_conflicts(
    duo: Duo, *, normalized_session_config: dict[str, Any], arg_source_record: ArgSourceRecord
) -> dict[str, Any]:
    """
    Apply path precedence rules for overlapping log path arguments.

    A fully specified log_file_path is treated as authoritative
    because it already determines:
        - parent directory
        - filename
        - effective layout structure

    Conflicting lower-specificity fields are normalized or ignored:
        - log_file_layout forced to "flat"
        - conflicting log_dir_path ignored
        - conflicting log_file_name ignored

    Warnings and source tracking are updated accordingly.
    """

    log_file_path = normalized_session_config["log_file_path"]

    # --- only applies when full path explicitly provided ---
    if log_file_path != "auto":
        # --- force flat layout ---
        if normalized_session_config["log_file_layout"] != "flat":
            normalized_session_config["log_file_layout"] = "flat"
            arg_source_record.arg_source_dict["log_file_layout"] = "forced"
            warn_msg = "custom log_file_path provided; forcing log_file_layout='flat'"
            _runtime_warning(duo, warn_msg=warn_msg)

        # --- resolve log_dir_path conflict ---
        if normalized_session_config["log_dir_path"] != "auto":
            log_file_path_parent = Path(normalized_session_config["log_file_path"]).parent
            user_arg_log_dir_path = Path(normalized_session_config["log_dir_path"])

            if log_file_path_parent != user_arg_log_dir_path:
                arg_source_record.arg_source_dict["log_dir_path"] = "forced"
                warn_msg = "log_file_path overrides conflicting log_dir_path"
                _runtime_warning(duo, warn_msg=warn_msg)

        # --- resolve log_file_name conflict ---
        if normalized_session_config["log_file_name"] != "auto":
            user_arg_log_file_name = normalized_session_config["log_file_name"]
            log_file_path_name = Path(normalized_session_config["log_file_path"]).name
            if user_arg_log_file_name != log_file_path_name:
                arg_source_record.arg_source_dict["log_file_name"] = "forced"
                warn_msg = "log_file_path overrides conflicting log_file_name"
                _runtime_warning(duo, warn_msg=warn_msg)

    return normalized_session_config


# === Other Internal helpers ===================================================


# ---_populate_runtime_script_fields() -----------------------------------------
def _populate_runtime_script_fields(*, runtime: RuntimeRecord) -> None:
    """
    Populate runtime script-derived metadata.

    These fields may later be normalized for interactive sessions.
    """

    script_path_abs, script_path_source = _get_script_path_abs()
    runtime.script_path_abs = script_path_abs
    runtime.script_path_source = script_path_source

    if script_path_abs is not None and script_path_abs.is_file():
        runtime.script_name = script_path_abs.name
        runtime.session_name = str(Path(script_path_abs).stem).lower()
    else:
        runtime.script_name = None
        runtime.session_name = "session"


# --- _populate_runtime_log_paths() --------------------------------------------
def _populate_runtime_log_paths(*, resolved_config: dict[str, Any], runtime: RuntimeRecord) -> None:

    assert runtime.project_dir_path_abs is not None
    assert runtime.session_name is not None
    assert runtime.session_timestamp is not None

    paths = _derive_session_log_paths(
        project_dir_path_abs=runtime.project_dir_path_abs,
        session_name=runtime.session_name,
        log_file_layout=resolved_config["log_file_layout"],
        log_file_mode=resolved_config["log_file_mode"],
        session_timestamp=runtime.session_timestamp,
        log_file_path=resolved_config["log_file_path"],
        log_dir_path=resolved_config["log_dir_path"],
        log_file_name=resolved_config["log_file_name"],
    )

    # Need canonical runtime paths for artifacts, JSONL, and log.output_dir()
    if paths["log_dir_path_abs"] is None:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR:\n\n"
            "Failed to derive canonical runtime log paths.\n\n"
            "This indicates an internal Logduo path resolution bug "
            "or invariant violation."
        )

    runtime.log_dir_path_abs = paths["log_dir_path_abs"]
    runtime.main_sink_log_dir_path_abs = paths["main_sink_log_dir_path_abs"]
    runtime.main_sink_log_file_path_abs = paths["main_sink_log_file_path_abs"]


# --- _apply_theme_derivation() ------------------------------------------------
def _apply_theme_derivation(*, resolved_config: dict[str, Any]) -> None:

    dark_console_theme_dict = cast(
        dict[str, str],
        SESSION_CONFIG_SPEC["dark_console_theme_dict"],
    )

    light_console_theme_dict = cast(
        dict[str, str],
        SESSION_CONFIG_SPEC["light_console_theme_dict"],
    )


    theme = resolved_config.get("console_theme") or "dark"
    console_theme_dict = resolved_config.get("console_theme_dict") or {}

    resolved_config["console_theme_dict"] = _derive_console_theme_dict(
        theme=theme,
        console_theme_dict=console_theme_dict,
        dark_console_theme_dict=dark_console_theme_dict,
        light_console_theme_dict=light_console_theme_dict,
    )


# --- _derive_console_theme_dict() ---------------------------------------------
def _derive_console_theme_dict(
    *,
    theme: str,
    console_theme_dict: dict[str, str] | None,
    dark_console_theme_dict: dict[str, str],
    light_console_theme_dict: dict[str, str],
) -> dict[str, str]:
    """
    Merge a preset palette (dark or light) with user overrides.

    Inputs:
      - theme: "dark" or "light" (already normalized by schema / norm_theme).
      - console_theme_dict: user overrides mapping semantic keys → Rich styles.
      - dark_colors / light_colors: built-in palettes from VALIDATION_CONFIG.

    Returns:
      A dict[str, str] of the final palette that logduo will actually use.
    """
    # Defensive: default to "dark"
    theme_normalized = (theme or "dark").strip().lower()
    base = dark_console_theme_dict if theme_normalized == "dark" else light_console_theme_dict

    # Start with the base palette
    merged: dict[str, str] = dict(base)

    # Apply user overrides (only keep clean string→string entries)
    if isinstance(console_theme_dict, dict):
        for key, val in console_theme_dict.items():
            if isinstance(key, str) and isinstance(val, str):
                merged[key] = val

    return merged


# --- _resolve_header_footer_value() -------------------------------------------
def _resolve_header_footer_value(
        *,
        arg_name: str,
        value: Any) -> str:

    # --- must be string ---
    if not isinstance(value, str):
        raise ValueError(
            f"{arg_name} must be 'off' or a non-empty string.\n"
            "Omit the argument to use default behavior."
        )

    # --- cannot be empty string ---
    raw = value.strip()
    if not raw:
        raise ValueError(f"{arg_name} cannot be empty.\nOmit the argument to use default behavior.")

    key = raw.lower()
    if key in {"off", "auto"}:
        return key
    return raw


# --- _resolve_header_footer_field() -------------------------------------------
def _resolve_header_footer_field(*, arg_name: str, config: dict[str, Any]) -> None:
    value = config.get(arg_name)
    resolved = _resolve_header_footer_value(arg_name=arg_name, value=value)

    config[arg_name] = resolved


# --- _apply_header_footer_policy() --------------------------------------------
def _apply_header_footer_policy(*, resolved_config: dict[str, Any]) -> None:

    for arg in ("log_header", "log_footer", "console_header", "console_footer"):
        _resolve_header_footer_field(arg_name=arg, config=resolved_config)
