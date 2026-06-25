"""
created_file_record_builders.py

Centralized builders for CreatedFileRecord.

Design:
- Each builder fully resolves and populates all fields
- No partial records
- No per-emitter duplication
- No runtime mutation after creation

Used by:
- sink initializers (main_sink_log, user_sink, jsonl, capture)
- artifact creation paths

Last edited: 2026-05-27
"""

from dataclasses import fields
from pathlib import Path

from logduo.internals.engine.runtime_classes import CreatedFileRecord, UserSinkConfig
from logduo.internals.formatters.prefix_builder import _compute_continuation_prefix_len
from logduo.internals.session_config.session_config_classes import SessionConfig
from logduo.internals.session_config.session_constants import (
    _LOGURU_DISPLAY_ORDER,
    FileKindType,
    LogFileModeType,
    PrefixType,
    VerbosityLevelType,
)


# --- _build_main_sink_log_created_file_record() ------------------------------------
def _build_main_sink_log_created_file_record(
    *, config: SessionConfig, file_path: Path, sink_name: str, sink_id: int, display_order: int = 0
) -> CreatedFileRecord:

    if not isinstance(config, SessionConfig):
        raise RuntimeError("LOGDUO INTERNAL ERROR: Main log requires SessionConfig")

    return _build_cfr_base(
        file_path=file_path,
        sink_name=sink_name,
        sink_id=sink_id,
        file_kind="main_sink_log",
        is_log_file=True,
        log_verbosity=config.log_verbosity,
        log_file_mode=config.log_file_mode,
        log_prefix=config.log_prefix,
        log_wrap_width=config.log_wrap_width,
        log_header=config.log_header,
        log_footer=config.log_footer,
        show_pid_in_log=config.show_pid_in_log,
        display_order=display_order,
    )


# --- _build_user_sink_log_created_file_record() -------------------------------
def _build_user_sink_log_created_file_record(
    *,
    config: UserSinkConfig,
    show_pid_in_log: bool,
    file_path: Path,
    sink_name: str,
    sink_id: int,
    display_order: int = 0,
) -> CreatedFileRecord:

    if not isinstance(config, UserSinkConfig):
        raise RuntimeError("LOGDUO INTERNAL ERROR: User sink log requires UserSinkConfig")

    return _build_cfr_base(
        file_path=file_path,
        sink_name=sink_name,
        sink_id=sink_id,
        file_kind="user_sink_log",
        is_log_file=True,
        log_verbosity=config.log_verbosity,
        log_file_mode=config.log_file_mode,
        log_prefix=config.log_prefix,
        log_wrap_width=config.log_wrap_width,
        log_header=config.log_header,
        log_footer=config.log_footer,
        show_pid_in_log=show_pid_in_log,
        display_order=display_order,
    )


# --- _build_jsonl_created_file_record() ---------------------------------------
def _build_jsonl_created_file_record(
    *, file_path: Path, display_order: int = 0
) -> CreatedFileRecord:

    return _build_cfr_base(
        file_path=file_path,
        sink_name=None,
        sink_id=None,
        file_kind="jsonl",
        is_log_file=False,
        log_verbosity=0,
        log_file_mode="write",
        log_prefix="off",
        log_wrap_width="off",
        log_header="off",
        log_footer="off",
        show_pid_in_log=False,
        display_order=display_order,
    )


# --- _build_artifact_created_file_record() ------------------------------------
def _build_artifact_created_file_record(
    *, file_path: Path, display_order: int = 0
) -> CreatedFileRecord:

    return _build_cfr_base(
        file_path=file_path,
        sink_name=None,
        sink_id=None,
        file_kind="artifact",
        is_log_file=False,
        log_verbosity=0,
        log_file_mode="write",
        log_prefix="off",
        log_wrap_width="off",
        log_header="off",
        log_footer="off",
        show_pid_in_log=False,
        display_order=display_order,
    )


# --- _build_loguru_created_file_record() --------------------------------------
def _build_loguru_created_file_record(
    *,
    file_path: Path,
    sink_id: int,
    file_mode: LogFileModeType = "write",
    display_order: int = _LOGURU_DISPLAY_ORDER,
) -> CreatedFileRecord:

    return _build_cfr_base(
        file_path=file_path,
        sink_name=None,
        sink_id=sink_id,
        file_kind="loguru_log",
        is_log_file=True,
        log_verbosity=0,
        log_file_mode=file_mode,
        log_prefix="off",
        log_wrap_width="off",
        log_header="off",
        log_footer="off",
        show_pid_in_log=False,
        display_order=display_order,
    )


# === Internal helpers =========================================================


# --- _build_cfr_base() --------------------------------------------------------
def _build_cfr_base(
    *,
    file_path: Path,
    sink_name: str | None,
    sink_id: int | None,
    file_kind: FileKindType,
    is_log_file: bool,
    log_verbosity: VerbosityLevelType,
    log_file_mode: LogFileModeType,
    log_prefix: PrefixType,
    log_wrap_width: int | str,
    log_header: str,
    log_footer: str,
    show_pid_in_log: bool,
    # --- display ---
    display_order: int = 0,
) -> CreatedFileRecord:
    """
    Build fully resolved immutable CreatedFileRecord with invariant validation.
    """

    if not isinstance(file_path, Path):
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: file_path must be Path to record file in CreatedFileRecord"
        )

    file_name = file_path.name
    file_ext = file_path.suffix.lstrip(".")

    # --- compute prefix wrap width  ---
    continuation_prefix_len = _compute_continuation_prefix_len(prefix_mode=log_prefix)

    # --- validate critical enums ---
    if log_verbosity not in (0, 1, 2, 3):
        raise RuntimeError(f"LOGDUO INTERNAL ERROR: invalid log_verbosity={log_verbosity}")

    kwargs = dict(
        path=file_path,
        file_name=file_name,
        file_ext=file_ext,
        file_kind=file_kind,
        is_log_file=is_log_file,
        # sink id
        sink_name=sink_name,
        sink_id=sink_id,
        # resolved per-file behavior
        log_verbosity=log_verbosity,
        log_file_mode=log_file_mode,
        log_prefix=log_prefix,
        log_wrap_width=log_wrap_width,
        log_header=log_header,
        log_footer=log_footer,
        show_pid_in_log=show_pid_in_log,
        # display metadata
        continuation_prefix_len=continuation_prefix_len,
        display_order=display_order,
    )
    _validate_cfr_fields_complete(kwargs)
    cfr_order = [f.name for f in fields(CreatedFileRecord)]

    passed_order = list(kwargs.keys())

    if cfr_order != passed_order:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: CreatedFileRecord field order mismatch.\n"
            f"Expected: {cfr_order}\n"
            f"Got: {passed_order}"
        )

    return CreatedFileRecord(
        path=file_path,
        file_name=file_name,
        file_ext=file_ext,
        file_kind=file_kind,
        is_log_file=is_log_file,
        sink_name=sink_name,
        sink_id=sink_id,
        log_verbosity=log_verbosity,
        log_file_mode=log_file_mode,
        log_prefix=log_prefix,
        log_wrap_width=log_wrap_width,
        log_header=log_header,
        log_footer=log_footer,
        show_pid_in_log=show_pid_in_log,
        continuation_prefix_len=continuation_prefix_len,
        display_order=display_order,
    )


# --- _validate_cfr_fields_complete() ---------------------------------------------
def _validate_cfr_fields_complete(kwargs: dict[str, object]) -> None:
    cfr_fields = {f.name for f in fields(CreatedFileRecord)}
    passed_fields = set(kwargs.keys())
    if cfr_fields != passed_fields:
        missing = cfr_fields - passed_fields
        extra = passed_fields - cfr_fields
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: CreatedFileRecord field mismatch in _build_cfr_base.\n"
            f"Missing fields: {sorted(missing)}\n"
            f"Unexpected fields: {sorted(extra)}"
        )
