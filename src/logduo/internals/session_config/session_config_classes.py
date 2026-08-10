"""
session_config_classes.py

Last edited 2026-08-10
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from logduo.internals.session_config.session_constants import (
    LogDirLayoutType,
    LogFileModeType,
    PrefixType,
    VerbosityLevelType,
)


# --- SessionConfig -------------------------------------------------------------
# Allowed None fields in SessionConfig: {"rotation", "retention", "compression"}
@dataclass(slots=True, frozen=True)
class SessionConfig:
    # --- File management ---
    log_file_mode: LogFileModeType
    log_file_path: str
    log_file_name: str
    log_file_layout: LogDirLayoutType
    log_dir_path: str
    keep: int | Literal["off"]

    # --- Formatting ---
    # console
    console_verbosity: VerbosityLevelType
    console_prefix: PrefixType
    console_wrap_width: int
    console_header: str
    console_footer: str
    console_color: bool
    console_theme: Literal["dark", "light"]
    console_theme_dict: dict[str, Any]
    # log
    log_verbosity: VerbosityLevelType
    log_prefix: PrefixType
    log_wrap_width: int | str
    log_header: str
    log_footer: str

    # --- Advanced ---
    show_debug_source: bool
    show_logger_name: bool
    show_pid_in_console: bool
    show_pid_in_log: bool
    write_config_table: bool
    write_config_json: bool
    write_jsonl: bool
    first_instance_owns_console: bool

    # --- Loguru ---
    rotation: str | None
    retention: int | None
    compression: str | None
    enqueue: bool
    catch: bool
    backtrace: bool
    diagnose: bool

    @classmethod
    def from_dict(
            cls,
            resolved_session_config: dict[str, Any],
    ) -> "SessionConfig":
        """
        Build SessionConfig from a resolved configuration dictionary.
        Unexpected keys are ignored to support forward-compatible
        configuration expansion.
        """
        allowed = cls.__annotations__.keys()
        filtered = {
            key: value
            for key, value in resolved_session_config.items()
            if key in allowed
        }
        return cls(**filtered)


# --- class ArgSourceRecord ----------------------------------------------------
@dataclass(slots=True)
class ArgSourceRecord:
    arg_source_dict: dict[str, str] = field(default_factory=dict)
    toml_record: dict[str, Any] = field(default_factory=dict)

    # toml_record: dict[str, Any] = {
    #         "toml_file_path": (
    #             str(toml_path_abs)
    #             if toml_path_abs
    #             else None
    #         ),
    #         "has_pyproject": False,
    #         "has_tool_table": False,
    #         "toml_keys": [],
    #     }
