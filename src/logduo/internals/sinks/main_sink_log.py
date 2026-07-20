"""
main_sink_log.py

Initialize, emit, and end for main sink log.

Lifecycle:
    - initialize: derive from SessionConfig, register file, write header
    - emit: write per-line output using resolved event data
    - end: write footer / finalize output

Dependencies:
    - execution values: EmitEvent (fully resolved execution state)
    - global values: duo.session_config (frozen at startup)

Contract:
    - All configuration is resolved before per-line emit
    - No `_NOT_GIVEN` or "auto" values reach per-line emit
    - No resolution occurs during per-line emit
    - End-phase emit may resolve deferred lifecycle values (e.g., "auto" footer)

Notes:
    - No per-sink session_config object; all values originate from SessionConfig

Last edited: 2026-5-27
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logduo.logduo import Duo



from logduo.internals.engine.runtime_classes import EmitEvent
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.filesystem.created_file_record_builders import (
    _build_main_sink_log_created_file_record,
)
from logduo.internals.filesystem.created_file_record_registration import (
    _register_created_file_record,
)
from logduo.internals.formatters.log_header_footer_builders import _build_log_footer, _build_log_header
from logduo.internals.formatters.message_prep import (
    _build_plain_message,
    _prepare_log_payload,
    MessageKind,
)
from logduo.internals.formatters.prefix_builder import _build_prefix
from logduo.internals.sinks.loguru_integration import _create_logduo_log_sink, _emit_log_payload


# --- _initialize_main_sink_log() ----------------------------------------------
def _initialize_main_sink_log(duo: Duo) -> None:
    """
    Ensure the main sink log file exists and is attached.

    This method is idempotent. It creates the log directory if needed
    and attaches (or refreshes) the main Loguru sink based on the
    already-derived canonical path state.
    """
    session_config = duo.session_config
    runtime = duo._runtime
    if session_config.log_verbosity <= 0:
        return

    main_dir = runtime.main_sink_log_dir_path_abs
    if main_dir is None:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: main_sink_log_dir_path_abs missing during sink initialization"
        )

    main_dir = Path(main_dir)

    try:
        main_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        _runtime_warning(duo, warn_msg=f"Failed to create log directory {main_dir}: {e}")
        return

    # --- determine if log file creation is needed ---
    need_main_log = duo.session_config.log_verbosity > 0
    main_sink_log_file_path_abs = runtime.main_sink_log_file_path_abs

    if need_main_log and main_sink_log_file_path_abs is None:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: main_sink_log_file_path_abs missing when log_verbosity > 0"
        )

    main_log_file_exists = any(
        cfr.file_kind == "main_sink_log" for cfr in runtime._get_file_list_in_cfr()
    )

    # --- create main_sink_log file ---
    if need_main_log and not main_log_file_exists:
        assert main_sink_log_file_path_abs is not None
        sink_id = _create_logduo_log_sink(
            duo=duo,
            log_file_path=main_sink_log_file_path_abs,
            log_file_kind="main_sink_log",
            log_file_mode=duo.session_config.log_file_mode,
            sink_name="main_sink",
        )

        cfr = _build_main_sink_log_created_file_record(
            config=session_config,
            file_path=main_sink_log_file_path_abs,
            sink_name="main_sink",
            sink_id=sink_id,
        )
        _register_created_file_record(duo, cfr)

        # --- build main_sink_log header ---
        log_header = _build_log_header(runtime=runtime, cfr=cfr)

        # --- emit main_sink_log header ---
        if log_header is not None:
            _emit_log_payload(
                level="INFO",
                prefix="",
                payload=log_header,
                message_kind=MessageKind.STRUCTURED,
                sink_name="main_sink",
                target_kind="main_sink_log",
                file_name=cfr.file_name,
                is_log_file=True,
            )


# --- _emit_main_sink_log() ----------------------------------------------------
def _emit_main_sink_log(duo: Duo, *, event: EmitEvent) -> None:

    session_config = duo.session_config
    log_prefix = session_config.log_prefix

    cfr = event.created_file_record
    assert cfr is not None, "LOGDUO INTERNAL ERROR: main sink emitter requires CreatedFileRecord."

    rca = event.resolved_call_args
    no_prefix = rca["no_prefix"]
    log_wrap_width = rca["log_wrap_width"]
    # two rca fields not used in this function:
    #     console_style = rca["console_style"]
    #     warn_key = rca.get("warn_key")

    msg = _build_plain_message(event.message)
    if msg is None:
        return
    if msg is not None and not isinstance(msg, str):
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR: _build_plain_message returned non-str: {type(msg).__name__}"
        )

    prefix = _build_prefix(
        duo=duo,
        level_label=event.label,
        no_prefix=no_prefix,
        callsite=event.callsite,
        prefix_mode=log_prefix,
        is_log=True,
        sink_tag=event.sink_tag,
    )

    assert isinstance(prefix, str), "LOGDUO INTERNAL ERROR: main sink log prefix must be str."

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
        is_log_file=cfr.is_log_file,
    )


# --- _emit_main_sink_log_end() -----------------------------------------------------
def _emit_main_sink_log_end(duo: Duo) -> None:
    session_config = duo.session_config
    runtime = duo._runtime

    if session_config.log_verbosity <= 0:
        return

    for cfr in runtime._get_file_list_in_cfr():
        if cfr.file_kind != "main_sink_log":
            continue

        # --- build footer payload ---
        log_footer = _build_log_footer(
            runtime=runtime, session_config=session_config, cfr=cfr, is_main_sink_log=True
        )

        if log_footer is None:
            continue

        # --- emit footer payload ---
        _emit_log_payload(
            level="INFO",
            prefix="",
            payload=log_footer,
            message_kind=MessageKind.STRUCTURED,
            sink_name="main_sink",
            target_kind="main_sink_log",
            file_name=cfr.file_name,
            is_log_file=True,
        )
