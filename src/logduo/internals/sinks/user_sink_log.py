"""
user_sink_log.py

Initialize, emit, and end for user sink logs - created via new_logger()

Lifecycle:
    - initialize: resolve new_logger() args, register file, emit header
    - emit: write per-line output using resolved event data
    - end: emit footer / finalize output

Dependencies:
    - execution values: EmitEvent (fully resolved execution state)
    - global values: duo.session_config (frozen at startup)

Contract:
    - All configuration is resolved before per-line emit
    - No `_NOT_GIVEN` or "auto" values reach per-line emit
    - No resolution occurs during per-line emit
    - End-phase emit may resolve deferred lifecycle values (e.g., "auto" footer)

Notes:
    - No per-sink session_config object; all values originate from:
        - resolved new_logger() args
        - SessionConfig defaults
    - Supports independent routing and formatting policies per user sink

Last edited: 2026-05-27
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo
    from logduo.internals.engine.user_sink_call_adapter import UserSinkCallAdapter


from logduo.internals.api_arg_resolvers.new_logger_args_resolver import _resolve_new_logger_args
from logduo.internals.engine.runtime_classes import EmitEvent, UserSinkConfig
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.filesystem.created_file_record_builders import (
    _build_user_sink_log_created_file_record,
)
from logduo.internals.filesystem.created_file_record_registration import (
    _register_created_file_record,
)
from logduo.internals.filesystem.path_finders import _apply_timestamp_to_filename
from logduo.internals.formatters.log_header_footer_builders import _build_log_footer, _build_log_header
from logduo.internals.formatters.message_prep import (
    _build_plain_message,
    _prepare_log_payload,
    MessageKind,
)
from logduo.internals.formatters.prefix_builder import _build_prefix
from logduo.internals.sinks.loguru_integration import _create_logduo_log_sink, _emit_log_payload


# --- _initialize_user_sink() --------------------------------------------------
def _initialize_user_sink(
        duo: Duo,
        *,
        new_logger_args: dict
) -> UserSinkCallAdapter:
    from logduo.internals.engine.user_sink_call_adapter import UserSinkCallAdapter

    duo._ensure_initialized()
    runtime = duo._runtime

    # --- resolve args ---
    # Hardcoded defaults:
    #     to_console=True
    #     to_main_log=True
    #
    # Remaining args inherit resolved session_config values
    # unless explicitly overridden in new_logger().
    resolved = _resolve_new_logger_args(
        duo=duo,
        new_logger_args=new_logger_args,
    )

    log_verbosity = resolved["log_verbosity"]
    if log_verbosity == 0:
        raise ValueError("new_logger() requires log_verbosity > 0")

    file_path = resolved["file_path"]
    if file_path is None:
        raise ValueError("new_logger() requires a valid file_path")

    sink_name = Path(resolved["base_file_name_with_ext"]).stem.lower()
    log_file_mode = resolved["log_file_mode"]

    # --- timestamp (applies once to base path) ---
    assert runtime.session_timestamp is not None
    if log_file_mode == "timestamped":
        file_path = file_path.with_name(
            _apply_timestamp_to_filename(
                filename=file_path.name, session_timestamp=runtime.session_timestamp
            )
        )

    user_sink_dir_path = file_path.parent

    user_sink_config = UserSinkConfig(
        sink_name=sink_name,
        to_console=resolved["to_console"],
        to_main_log=resolved["to_main_log"],
        log_verbosity=log_verbosity,
        sink_dir_path=user_sink_dir_path,
        log_file_path=file_path,
        log_file_mode=log_file_mode,
        log_prefix=resolved["log_prefix"],
        log_wrap_width=resolved["log_wrap_width"],
        log_header=resolved["log_header"],
        log_footer=resolved["log_footer"],
    )

    # --- ensure duplicate user sink is not created  ---
    sink_name_already_exists = any(
        cfr.file_kind == "user_sink_log" and cfr.sink_name == sink_name
        for cfr in runtime._get_file_list_in_cfr()
    )

    if sink_name_already_exists:
        raise ValueError(
            f"Duplicate new_logger name '{sink_name}' detected. "
            "new_logger names must be unique per session."
        )

    # --- ensure parent dir exists ---
    try:
        user_sink_dir_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR: Failed to create new_logger() log at {user_sink_dir_path}: {e}"
        ) from e

    sink_id = _create_logduo_log_sink(
        duo=duo,
        log_file_path=file_path,
        log_file_kind="user_sink_log",
        log_file_mode=duo.session_config.log_file_mode,
        sink_name=sink_name,
    )

    cfr = _build_user_sink_log_created_file_record(
        config=user_sink_config,
        file_path=file_path,
        sink_name=sink_name,
        sink_id=sink_id,
        show_pid_in_log=duo.session_config.show_pid_in_log,
    )
    _register_created_file_record(duo, cfr)

    runtime.user_sink_config_registry[sink_name] = user_sink_config

    log_header = _build_log_header(runtime=runtime, cfr=cfr)

    # --- emit user sink log header ---
    if log_header is not None:
        _emit_log_payload(
            level="INFO",
            prefix="",
            payload=log_header,
            message_kind=MessageKind.STRUCTURED,
            sink_name=sink_name,
            target_kind="user_sink_log",
            file_name=cfr.file_name,
            is_log_file=True,
        )

    # --- return callable sink adapter ---
    # Example:
    #     aud = new_logger("audit")
    #     aud("my message")
    # The Python variable name does not need to match the sink name.
    return UserSinkCallAdapter(duo=duo, sink_name=sink_name)


# --- _emit_user_sink() --------------------------------------------------------
def _emit_user_sink(
        duo: Duo,
        *,
        event: EmitEvent,
) -> None:

    cfr = event.created_file_record
    assert cfr is not None, "LOGDUO INTERNAL ERROR: user_sink emitter requires CreatedFileRecord."

    rca = event.resolved_call_args
    log_wrap_width = rca["log_wrap_width"]
    no_prefix = rca["no_prefix"]

    msg = _build_plain_message(event.message)
    if msg is None:
        return
    if not isinstance(msg, str):
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR: _build_plain_message returned non-str: {type(msg).__name__}"
        )

    prefix = _build_prefix(
        duo=duo,
        level_label=event.label,
        no_prefix=no_prefix,
        callsite=event.callsite,
        prefix_mode=cfr.log_prefix,
        is_log=True,
        sink_tag=event.sink_tag,
    )

    assert isinstance(prefix, str), "LOGDUO INTERNAL ERROR: user sink log prefix must be str."

    # --- resolve inline/structured layout, wrap, + apply prefixes ---
    payload = _prepare_log_payload(
        msg=msg,
        message_kind=event.message_kind,
        no_prefix=no_prefix,
        prefix=prefix,
        cfr_continuation_prefix_len=cfr.continuation_prefix_len,
        log_wrap_width=log_wrap_width,
    )

    # --- emit prepared payload through Loguru ---
    _emit_log_payload(
        level=event.level,
        prefix=prefix,
        payload=payload,
        message_kind=event.message_kind,
        sink_name=event.sink_name,
        target_kind=event.target_kind,
        file_name=cfr.file_name,
        is_log_file=True,
    )


# --- _emit_user_sink_end() ----------------------------------------------------
def _emit_user_sink_end(duo: Duo) -> None:
    runtime = duo._runtime

    for cfr in runtime._get_file_list_in_cfr():
        if cfr.file_kind != "user_sink_log":
            continue

        try:
            # --- build footer payload ---
            # session_config not needed for user_sinks's footers
            # no list of created files provided
            log_footer = _build_log_footer(
                runtime=runtime,
                session_config=None,
                cfr=cfr,
                is_main_sink_log=False,
            )

            if log_footer is None:
                continue

            # --- emit footer payload ---
            _emit_log_payload(
                level="INFO",
                prefix="",
                payload=log_footer,
                message_kind=MessageKind.STRUCTURED,
                sink_name=cfr.sink_name,
                target_kind="user_sink_log",
                file_name=cfr.file_name,
                is_log_file=True,
            )

        except Exception as e:
            _runtime_warning(
                duo,
                warn_msg=f"user sink footer failed "
                f"[sink_name={cfr.sink_name!r}, "
                f"file_name={cfr.file_name!r}] → "
                f"in _build_auto_footer_info_rows() "
                f"{type(e).__name__}: {e}",
            )
