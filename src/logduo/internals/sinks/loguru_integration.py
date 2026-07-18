"""
loguru_integration.py

Internal integration layer between Logduo and Loguru.

Responsibilities:
    - Attach Logduo-managed file sinks to Loguru
    - Apply Logduo-controlled Loguru settings
    - Enforce physical-destination routing filters
    - Emit already-formatted payloads through Loguru
    - Validate Loguru passthrough settings (rotation/retention)

Architecture:
    - Logduo owns:
        * routing decisions
        * verbosity gating
        * prefix formatting
        * wrapping/layout
        * sink fan-out policy

    - Loguru owns:
        * file writing
        * rotation/retention/compression
        * enqueue/thread/process safety

Important:
    - Loguru never decides logical routing.
    - Loguru filters only enforce physical file destinations.
    - All payload formatting is completed before emission.
    - Loguru receives fully formatted messages via format="{message}".

Notes:
    - One attached Loguru sink corresponds to exactly one physical file.
    - Runtime routing metadata is passed via logger.bind(extra=...).
    - Dispatcher controls target_kind and sink_name semantics.

Last edited 2026-5-27
"""
from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from loguru import logger as _loguru_logger

from logduo.internals.engine.runtime_classes import MessageKind
from logduo.internals.session_config.session_constants import (
    LogFileModeType,
    LogKindType,
    TargetKindType,
)

DUMMY_SINK = os.devnull


# --- _create_logduo_log_sink() --------------------------------------------------
def _create_logduo_log_sink(
    *,
    duo: Duo,
    log_file_path: Path,
    log_file_kind: LogKindType,  # "main_sink_log" or "user_sink_log"
    log_file_mode: LogFileModeType,
    sink_name: str,
) -> int:
    session_config = duo.session_config
    runtime = duo._runtime

    log_file_path_abs = Path(log_file_path).expanduser().resolve(strict=False)

    # --- uniqueness ---
    for existing in runtime._get_file_list_in_cfr():
        if existing.path.resolve(strict=False) == log_file_path_abs:
            raise ValueError(f"Log file already exists: '{log_file_path_abs}'")

    # --- file mode ---
    # Loguru sink itself always opens in append mode.
    # If log_file_mode = "write",
    # This step clears any previous file contents so the
    # new session starts with a fresh log file.
    if log_file_mode == "write":
        with log_file_path_abs.open("w", encoding="utf-8"):
            pass

    # --- attach loguru ---
    sink_id = _attach_logduo_log_sink(
        logger=_loguru_logger,
        sink_path=log_file_path_abs,
        session_config=session_config,
        sink_name=sink_name,
        log_file_kind=log_file_kind,
    )

    return sink_id


# --- _emit_log_payload() --------------------------------------------
def _emit_log_payload(
    *,
    level: str,
    prefix: str,
    payload: str,
    message_kind: MessageKind,
    sink_name: str | None,
    target_kind: TargetKindType,
    file_name: str | None,
    is_log_file: bool,
) -> None:
    """
    Takes already-prepared payload → decide WHERE prefix goes and prints

    NOTE: payload is always a string
    """
    if sink_name is None:
        raise RuntimeError("LOGDUO INTERNAL ERROR: sink_name must be set for all log emissions")

    if target_kind not in {"user_sink_log", "main_sink_log"}:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: target_kind must be main_sink_log or a user_sink_log"
        )

    lg = _loguru_logger.bind(
        sink_name=sink_name,
        target_kind=target_kind,  # set per message in _dispatch_event()
        file_name=file_name,
        is_log_file=is_log_file,
    )
    # bind() is safe with None values; no guards required.
    # These fields are used to ensure routing obeys dispatcher

    if message_kind in (
            MessageKind.INLINE,
            MessageKind.OBJECT,
            MessageKind.RICH_RENDERABLE,
    ):
        _emit_log_line(lg, level, prefix + payload)
        return
    elif message_kind == MessageKind.STRUCTURED:
        if prefix:
            _emit_log_line(lg, level, prefix.rstrip())
        for line in payload.split("\n"):
            _emit_log_line(lg, level, line)
        return
    elif message_kind == MessageKind.RICH_TEXT:
        # Rich Text was converted to plain text earlier.
        # Emit according to resulting payload structure.

        if "\n" in payload:
            if prefix:
                _emit_log_line(lg, level, prefix.rstrip())

            for line in payload.split("\n"):
                _emit_log_line(lg, level, line)
        else:
            _emit_log_line(lg, level, prefix + payload)
        return
    else:
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR: unsupported message_kind={message_kind!r}"
        )


# --- _probe_loguru_rotation_retention() ---------------------------------------
def _probe_loguru_rotation_retention(*, config: dict[str, Any]) -> None:
    """
    Validate user-supplied rotation and retention values using Loguru.

    Policy:
        - Fail-fast: invalid values raise ValueError
        - No mutation of _building_config
        - No warnings / silent fallback
    """

    # --- validate rotation ----------------------------------------------------
    rotation = config.get("rotation")
    if rotation is not None:
        sink_id = None
        try:
            sink_id = _loguru_logger.add(DUMMY_SINK, rotation=rotation)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid value for 'rotation': {rotation!r}\n"
                f"Allowed formats:\n"
                f"  • int = max file size in BYTES (e.g. 10_000_000)\n"
                f"  • datetime.time = rotate daily at a time-of-day (e.g. time(0, 0))\n"
                f"  • str = human-friendly size/time (e.g., '10 MB', '4 days', '18:00')\n"
                f"  • datetime.timedelta (Python config only)\n"
                f"  • callable (Python config only)\n"
                f"  • None = disable rotation\n"
            ) from e
        finally:
            if sink_id is not None:
                _loguru_logger.remove(sink_id)

    # --- validate retention ---------------------------------------------------
    retention = config.get("retention")
    if retention is not None:
        sink_id = None
        try:
            sink_id = _loguru_logger.add(DUMMY_SINK, retention=retention)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid value for 'retention': {retention!r}\n"
                f"Allowed formats:\n"
                f"  • int = number of files to keep (e.g., 7)\n"
                f"  • str = max age (e.g. '10 days', '1 week, 3 days')\n"
                f"  • datetime.timedelta (Python config only)\n"
                f"  • callable (Python config only)\n"
                f"  • None = disable retention\n"
            ) from e
        finally:
            if sink_id is not None:
                _loguru_logger.remove(sink_id)


# === Internal helpers =========================================================


# --- _attach_logduo_log_sink() -----------------------------------------------
def _attach_logduo_log_sink(
    *,
    logger: Any,
    sink_path: str | Path,
    log_file_kind: LogKindType,
    sink_name: str,
    session_config: Any,
) -> int:
    """
    Attach one Logduo-managed log sink to Loguru during log file creation.

    Responsibilities
    ----------------
    - Attach exactly one physical file destination
    - Apply Logduo-controlled Loguru settings
    - Restrict sink to matching target_sink_name
    - Preserve dispatcher-owned routing semantics

    Notes
    -----
    Dispatcher fully controls:
        - verbosity
        - mirroring
        - fan-out
        - routing policy

    Loguru filtering here is physical-destination-only.

    One attached sink corresponds to exactly one physical log file.

    target_sink_name identifies the physical emission target,
    NOT the logical origin of the message.
    """

    sink_kwargs: dict[str, Any] = {
        "rotation": session_config.rotation,
        "retention": session_config.retention,
        "compression": session_config.compression,
        "enqueue": session_config.enqueue,
        "catch": session_config.catch,
        "backtrace": session_config.backtrace,
        "diagnose": session_config.diagnose,
    }

    # --- remove None values ---
    sink_kwargs = {k: v for k, v in sink_kwargs.items() if v is not None}

    # --- enforce Logduo policy ---
    sink_kwargs["mode"] = "a"

    # Logduo fully formats messages before they reach Loguru.
    # Use: format = "{message}" so Loguru writes the preformatted message unchanged.
    # A callable formatter function causes Loguru to re-interpret the returned string
    # as a Loguru format template, which breaks literal text such as:
    #     <input>
    #     a < b
    #     {hello}
    try:
        sink_id = logger.add(
            str(sink_path),
            format="{message}",
            filter=_build_logduo_filter(log_file_kind=log_file_kind, sink_name=sink_name),
            level="TRACE",
            colorize=False,
            **sink_kwargs,
        )

        assert isinstance(sink_id, int)
        return sink_id

    except (ValueError, OSError, TypeError) as e:
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR: "
            f"failed to attach sink {sink_name}: {e}"
        ) from e


# --- _build_logduo_filter() ---------------------------------------------------
def _build_logduo_filter(
    log_file_kind: LogKindType, sink_name: str
) -> Callable[[dict[str, Any]], bool]:
    """
    Build the Loguru filter callable for one attached Logduo log sink.

    Called once during sink creation by _attach_logduo_log_sink().

    The returned filter is later called automatically by Loguru
    for every emitted record.

    Runtime routing metadata is supplied by emitter bind():

        logger.bind(
            target_kind=...,
            sink_name=...,
        )

    Responsibilities
    ----------------
    main_sink_log:
        Accept all records routed toward main_sink_log.

    user_sink_log:
        Accept only records routed toward user_sink_log
        AND matching this sink_name.
    """

    # --- main sink log ---
    if log_file_kind == "main_sink_log":
        def _filter(record: dict[str, Any]) -> bool:
            extra = record["extra"]
            return bool(extra.get("target_kind") == "main_sink_log")

        return _filter

    # --- user sink log ---
    if log_file_kind == "user_sink_log":
        def _filter(record: dict[str, Any]) -> bool:
            extra = record["extra"]
            return bool(
                extra.get("target_kind") == "user_sink_log"
                and extra.get("sink_name") == sink_name
            )

        return _filter

    # --- defensive fallback ---
    raise RuntimeError(f"LOGDUO INTERNAL ERROR: Unsupported log_file_kind {log_file_kind!r}")


# --- _emit_log_line() ---------------------------------------------------------
def _emit_log_line(lg: Any, level: str, line: str) -> None:
    """Used internally to emit log line in _emit_log_payload()."""
    if level == "TRACE":
        lg.trace(line)
    elif level == "DEBUG":
        lg.debug(line)
    elif level == "INFO":
        lg.info(line)
    elif level == "WARNING":
        lg.warning(line)
    elif level == "ERROR":
        lg.error(line)
    elif level == "CRITICAL":
        lg.critical(line)
    elif level == "SUCCESS":
        lg.success(line)
    else:
        lg.info(line)
