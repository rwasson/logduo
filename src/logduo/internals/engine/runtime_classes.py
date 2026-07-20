"""
runtime_classes.py

Dataclasses used across Logduo session lifecycle:
    UserSinkConfig (immutable)
    CreatedFileRecord (immutable)
    RuntimeRecord (mutable)
    EmitEvent (mutable)

Provides the shared runtime state model used by dispatcher,
emitters, lifecycle management, and artifact generation.

Note:
- SessionConfig and ArgSourceRecord are defined in session_config_classes.py
- Maintainer/debugging aid for dataclass-style inspection:
      from logduo import log, text_table
      print(text_table(runtime_record))

Last edited: 2026-07-08
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from logduo.internals.session_config.session_constants import (
    _VALID_SESSION_STATE,
    FileKindType,
    LogFileModeType,
    PrefixType,
    TargetKindType,
    VerbosityLevelType,
)


class NotGiven:
    """
    Sentinel for omitted user arguments
    for Duo methods called during session.
    """
    pass


# --- class UserSinkConfig -----------------------------------------------------
# UserSinkConfig represents new_logger() sink behavior/policy.
# It is later resolved into one or more CreatedFileRecord objects
# used by emitters and runtime file tracking.
@dataclass(slots=True, frozen=True)
class UserSinkConfig:
    # --- identity ---
    sink_name: str  # registry key

    # --- routing / emission ---
    to_console: bool
    to_main_log: bool
    log_verbosity: VerbosityLevelType

    # --- paths ---
    sink_dir_path: Path
    log_file_path: Path  # used as lookup key into runtime file registry

    # --- formatting ---
    log_file_mode: LogFileModeType
    log_prefix: PrefixType
    log_wrap_width: int | str
    log_header: str
    log_footer: str


# --- class CreatedFileRecord --------------------------------------------------
# Immutable metadata record for files created during a session.
# Stored in runtime.created_file_record_registry and shared across
# dispatcher, emitters, footers, and JSONL summaries.
@dataclass(frozen=True, slots=True)
class CreatedFileRecord:
    path: Path
    file_name: str
    file_ext: str
    file_kind: FileKindType
    is_log_file: bool

    # sink id for log files
    sink_name: str | None
    sink_id: int | None

    # resolved per-file behavior
    log_verbosity: (
        VerbosityLevelType  # informational only (not used for routing at emit time)
    )
    log_file_mode: LogFileModeType
    log_prefix: PrefixType
    log_wrap_width: int | str
    log_header: str
    log_footer: str
    show_pid_in_log: bool

    # display metadata
    continuation_prefix_len: int


# --- class RuntimeRecord ------------------------------------------------------
@dataclass(slots=True)
class RuntimeRecord:
    # session identity and state
    # session_name = script path name's stem, else 'session'
    session_name: str | None = None
    session_state: _VALID_SESSION_STATE = "initializing"

    # start time
    start_time: datetime | None = None
    start_time_display: str | None = None  # human-readable display
    session_timestamp: str | None = None  # path-safe timestamp (for path)
    run_id_iso: str | None = None
    # ISO timestamp (machine-readable, JSON-safe)  logduo session identity

    # end time
    end_time: datetime | None = None
    end_time_display: str | None = None
    duration_seconds: int | None = None  # in seconds
    duration_display: str | None = None

    # runtime environment
    os_name: str | None = None
    python_version: str | None = None

    # process-bound runtime identity
    pid: int | None = None
    instance_index: int | None = None

    # execution mode
    detected_interactive: bool = field(default=False)

    # script info - saved in _resolve_session_config()
    script_path_abs: Path | None = None
    script_path_source: str | None = None
    script_name: str | None = None

    # project info - saved in _resolve_session_config()
    cwd_path_abs: Path | None = None
    project_dir_path_abs: Path | None = None
    toml_path_abs: Path | None = None
    toml_args_used: bool = field(default=False)

    # dir/file paths - saved in _resolve_session_config()
    log_dir_path_abs: Path | None = None
    main_sink_log_dir_path_abs: Path | None = None
    main_sink_log_file_path_abs: Path | None = None   # user facing, output_dir_path

    # JSONL file path saved in - _initialize_jsonl()
    jsonl_path_abs: Path | None = None

    # Custom labels created via log.new_level().
    # key = lowercase label lookup
    # value = (display_label, color, level)
    new_levels: dict[str, tuple[str, str | None, str]] = field(default_factory=dict)

    # created_file_record_registry - key is unique resolved file path
    created_file_record_registry: dict[Path, CreatedFileRecord] = field(default_factory=dict)

    # user_sink_config_registry - key is unique sink_name (each user sink generates a log file)
    user_sink_config_registry: dict[str, UserSinkConfig] = field(
        default_factory=dict
    )  # key is sink_name

    # console runtime state
    console_continuation_prefix_len: int = 0

    # runtime counters
    event_count: int = 0
    deleted_file_count: int = 0

    # warnings
    unique_warning_set: set[str] = field(default_factory=set)

    # session_config table string for duo.print_session_config()
    session_config_report: str | None = None

    # --- RuntimeRecord methods ---
    def _get_created_file_record_by_file_path(self, file_path: Path) -> CreatedFileRecord:
        try:
            return self.created_file_record_registry[file_path]
        except KeyError as e:
            raise RuntimeError(
                f"LOGDUO INTERNAL ERROR: CreatedFileRecord not found for {file_path}"
            ) from e

    def _get_file_list_in_cfr(self) -> list[CreatedFileRecord]:
        return list(self.created_file_record_registry.values())

    def _get_user_sink_record(self, sink_name: str) -> UserSinkConfig:
        try:
            return self.user_sink_config_registry[sink_name]
        except KeyError as e:
            raise RuntimeError(
                f"LOGDUO INTERNAL ERROR: User sink logger not found: {sink_name}"
            ) from e

    def warning_already_registered(self, warn_msg: str) -> bool:
        """Return True if this warning was already emitted this session."""
        return warn_msg in self.unique_warning_set


# --- class EmitEvent ----------------------------------------------------------
@dataclass(slots=True)
class EmitEvent:
    sink_name: str
    target_kind: TargetKindType
    level: str
    label: str
    message: Any
    resolved_call_args: dict[str, Any]
    callsite: str | None
    created_file_record: CreatedFileRecord | None
    warn_key: str | None
    event_type: str | None
    sink_tag: str | None
    output_targets: list[str] | None
    message_kind: MessageKind


# --- class MessageKind ----------------------------------------------------------
class MessageKind(StrEnum):
    INLINE = "inline"  # string with no newlines '\n'
    STRUCTURED = "structured"  # string has a newline '\n' (internal and/or leading/trailing)
    RICH_TEXT = "rich_text"
    RICH_RENDERABLE = "rich_renderable"  # other than Text
    OBJECT = "object"  # everything else
