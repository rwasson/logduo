"""
jsonl.py

- initialize: create JSONL file, register CreatedFileRecord, emit session_start
- emit: write structured event per line (JSON)
- end: finalize output (no footer formatting)


Notes:
    - No per-sink session_config object; all values originate from SessionConfig
    - Output is structured; no prefix, wrapping, or text formatting
    - Internal/system JSONL events are normalized to
      sink_name="main_sink" during JSONL emission
    - event_type distinguishes internally-generated and user-generated messages

Last edited: 2026-5-27
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from logduo.internals.engine.runtime_classes import CreatedFileRecord, EmitEvent
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.filesystem.created_file_record_builders import (
    _build_jsonl_created_file_record,
)
from logduo.internals.formatters.message_prep import _build_plain_message

JSONL_SCHEMA_VERSION = 1

JSONL_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "message",
        "prune_update",
        "system_warning",
        "session_file_registration",
        "session_start",
        "session_end",
    }
)

MESSAGE_FIELD_ORDER = [
    # --- identity ---
    "event_type",
    "time",
    "callsite",
    # --- core ---
    "sink_name",
    "level",
    "label",
    "message",
    # --- routing ---
    "output_targets",
    # --- resolved per call args (resolved in level_entry.py) ---
    "resolved_call_args",
    # --- context ---
    "pid",
    "instance_index",
]

FILES_CREATED_ENTRY_ORDER = [
    # --- identity ---
    "file_name",
    "file_ext",
    "file_kind",
    "is_log_file",
    "log_file_mode",
    # --- ownership ---
    "sink_name",
    # --- location ---
    "path",
]


SESSION_FILE_REGISTRATION_FIELD_ORDER = [
    # --- identity ---
    "event_type",
    "time",
    # --- file identity ---
    "file_name",
    "file_kind",
    "is_log_file",
    # --- ownership ---
    "sink_name",
    # --- location ---
    "path",
]

SESSION_START_FIELD_ORDER = [
    # --- identity ---
    "event_type",
    "time",
    # --- script ---
    "script_name",
    "script_path",
    # --- session ---
    "run_id_iso",
    "session_timestamp",
    "pid",
    "instance_index",
    "os_name",
    "python_version",
    # --- session_config ---
    "log_file_mode",
    "log_file_layout",
    "log_verbosity",
    "console_verbosity",
    # --- path ---
    "log_dir_path",
    "main_sink_log_dir_path",
    "main_sink_log_file_path",
    # --- flags ---
    "write_config_json",
    # --- version ---
    "jsonl_schema_version",
]


SESSION_END_FIELD_ORDER = [
    "event_type",
    "time",
    # --- timing ---
    "session_end_iso",
    "duration_seconds",
    "duration_display",
    # --- summary ---
    "event_count",
    "total_files_created",
    "files_created",
]

FIELD_ORDERS = {
    "message": MESSAGE_FIELD_ORDER,
    "session_file_registration": SESSION_FILE_REGISTRATION_FIELD_ORDER,
    "session_start": SESSION_START_FIELD_ORDER,
    "session_end": SESSION_END_FIELD_ORDER,
}


# --- _initialize_jsonl_sink() -----------------------------------------------
def _initialize_jsonl(duo: Duo) -> None:  # noqa: PLR0911  # many returns
    from logduo.internals.filesystem.created_file_record_registration import (
        _register_created_file_record,
    )

    session_config = duo.session_config
    runtime = duo._runtime

    # --- feature disabled ---
    if not session_config.write_jsonl:
        return

    log_dir_path = runtime.main_sink_log_dir_path_abs

    # --- missing directory ---
    if not log_dir_path:
        _runtime_warning(duo, warn_msg="JSONL already initialized for this session; skipping")
        return

    # --- resolve path ---
    jsonl_path_abs = (log_dir_path / f"{runtime.session_name}.jsonl").resolve(strict=False)

    # --- check uniqueness ---
    for cfr in runtime._get_file_list_in_cfr():
        if cfr.file_kind == "jsonl":
            _runtime_warning(duo, warn_msg="JSONL already initialized for this session; skipping")
            return

    # --- mkdir ---
    try:
        log_dir_path.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError):
        _runtime_warning(duo, warn_msg="JSONL already initialized for this session; skipping")
        return

    # --- create empty JSONL file ---
    try:
        with jsonl_path_abs.open("w", encoding="utf-8"):
            pass
    except (OSError, ValueError):
        _runtime_warning(duo, warn_msg="Could not create JSONL file.")
        return

    # --- attach to runtime ---
    runtime.jsonl_path_abs = jsonl_path_abs

    # --- build + register file record ---
    _register_created_file_record(
        duo, _build_jsonl_created_file_record(file_path=jsonl_path_abs, display_order=0)
    )

    try:
        # --- emit session_start ---
        _emit_jsonl_payload(
            duo,
            event_type="session_start",
            payload={
                "script_name": runtime.script_name,
                "script_path": str(runtime.script_path_abs) if runtime.script_path_abs else None,
                "run_id_iso": runtime.run_id_iso,
                "session_timestamp": runtime.session_timestamp,
                "pid": runtime.pid,
                "instance_index": runtime.instance_index,
                "os_name": runtime.os_name,
                "python_version": runtime.python_version,
                "log_file_mode": session_config.log_file_mode,
                "log_file_layout": session_config.log_file_layout,
                "log_verbosity": session_config.log_verbosity,
                "console_verbosity": session_config.console_verbosity,
                "log_dir_path": str(runtime.log_dir_path_abs) if runtime.log_dir_path_abs else None,
                "main_sink_log_dir_path": str(runtime.main_sink_log_dir_path_abs)
                if runtime.main_sink_log_dir_path_abs
                else None,
                "main_sink_log_file_path": str(runtime.main_sink_log_file_path_abs)
                if runtime.main_sink_log_file_path_abs
                else None,
                "write_config_json": bool(session_config.write_config_json),
                "jsonl_schema_version": JSONL_SCHEMA_VERSION,
            },
            sink_name="main_sink",
            output_targets=["jsonl"],
        )
        return

    except (OSError, ValueError, TypeError) as e:
        _runtime_warning(duo, warn_msg=f"Could not write JSONL file ({type(e).__name__}).")
        return


# --- _emit_jsonl() ------------------------------------------------------------
def _emit_jsonl(duo: Duo, *, event: EmitEvent) -> None:
    if event.event_type is None:
        raise RuntimeError("LOGDUO INTERNAL ERROR: event_type missing for JSONL event.")

        # --- 1. build message ---
    # JSONL always records object placeholders (never suppress)
    msg = _build_plain_message(event.message)

    if msg is None:
        return

    # --- normalize visual blank-line variants ---
    if isinstance(msg, str) and msg.strip() == "":
        msg = ""

    if not isinstance(msg, str):
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR: _build_plain_message returned non-str: {type(msg).__name__}"
        )

    # --- 2. build payload ---
    payload = _build_jsonl_payload(duo, event=event, message_text=msg)

    # --- 3. emit payload ---
    _emit_jsonl_payload(
        duo,
        event_type=event.event_type,
        payload=payload,
        sink_name=event.sink_name,
        output_targets=event.output_targets,
    )


# --- _emit_jsonl_file_registration() ------------------------------------------
def _emit_jsonl_file_registration(
    duo: Duo, cfr: CreatedFileRecord, *, extra: dict | None = None
) -> None:
    """
    Emit a JSONL event when a file is registered.
    Called from _register_created_file_record().
    """
    raw_payload = {
        "file_name": cfr.file_name,
        "file_kind": cfr.file_kind,
        "sink_name": cfr.sink_name,
        "is_log_file": cfr.is_log_file,
        "path": str(cfr.path),
    }

    payload = {
        k: raw_payload.get(k)
        for k in SESSION_FILE_REGISTRATION_FIELD_ORDER
        if k not in ("event_type", "time")
    }

    if extra:
        payload.update(extra)

    _emit_jsonl_payload(
        duo,
        event_type="session_file_registration",
        payload=payload,
        sink_name="main_sink",
        output_targets=["jsonl"],
    )


# --- _emit_jsonl_end() --------------------------------------------------------
def _emit_jsonl_end(duo: Duo) -> None:
    runtime = duo._runtime
    # cfr = CreatedFileRecord; each cfr contains full metadata for a created file
    # the created_file_record_list is a list of all cfr
    created_file_record_list = runtime._get_file_list_in_cfr() or []
    files_created = [_build_files_created_entry(cfr) for cfr in created_file_record_list]

    # --- build payload ---
    payload_end = {
        # --- timing ---
        "session_end_iso": (runtime.end_time.isoformat() if runtime.end_time else None),
        "duration_seconds": runtime.duration_seconds,
        "duration_display": runtime.duration_display,
        # --- summary ---
        "event_count": runtime.event_count,
        "total_files_created": len(created_file_record_list),
        "files_created": files_created,
    }

    _emit_jsonl_payload(
        duo,
        event_type="session_end",
        payload=payload_end,
        sink_name="main_sink",
        output_targets=["jsonl"],  # system-generated → JSONL only
    )


# === Internal helpers =========================================================


# --- _build_jsonl_payload() ---------------------------------------------------
def _build_jsonl_payload(duo: Duo, *, event: EmitEvent, message_text: str | None) -> dict[str, Any]:
    runtime = duo._runtime
    warn_key = event.warn_key

    payload = {
        "callsite": event.callsite,
        # --- core ---
        "level": event.level,
        "label": event.label,
        "message": message_text,
        # --- resolved call args ---
        "resolved_call_args": event.resolved_call_args,
        # --- runtime context ---
        "pid": runtime.pid,
        "instance_index": runtime.instance_index,
    }

    # --- optional classification ---
    if warn_key is not None:
        payload["warn_key"] = warn_key

    return payload


# --- _emit_jsonl_payload() ------------------------------------------------------
def _emit_jsonl_payload(
    duo: Duo,
    *,
    event_type: str,
    payload: dict[str, Any],
    sink_name: str = "main_sink",
    output_targets: list[str] | None = None,
) -> None:
    runtime = duo._runtime
    jsonl_path_abs = runtime.jsonl_path_abs

    try:
        if not jsonl_path_abs:
            return

        if not isinstance(sink_name, str):
            raise TypeError("LOGDUO INTERNAL ERROR: sink_name must be str | None")

        if event_type == "message" and not sink_name:
            raise RuntimeError("LOGDUO INTERNAL ERROR: message events require sink_name")

        if output_targets is None:
            output_targets = []
        elif not isinstance(output_targets, list):
            raise ValueError("LOGDUO INTERNAL ERROR: output_targets must be a list[str]")

        if event_type not in JSONL_EVENT_TYPES:
            raise ValueError(f"LOGDUO INTERNAL ERROR: invalid event_type '{event_type}'")

        # --- select field order ---
        # needs a comment explaining why need this
        field_order = FIELD_ORDERS.get(event_type, MESSAGE_FIELD_ORDER)
        required_fields = set(field_order)
        required_fields.discard("event_type")
        required_fields.discard("time")

        available_fields = set(payload.keys()) | {"sink_name", "output_targets"}
        missing = required_fields - available_fields
        if missing:
            raise ValueError(
                f"LOGDUO INTERNAL ERROR: JSONL missing required fields for '{event_type}': {sorted(missing)} "
                f"(provided: {sorted(available_fields)})"
            )

        if event_type != "message":
            payload.pop("callsite", None)
            payload.pop("label", None)
            sink_name = "main_sink"

        # --- build full event record ---
        full_event: dict[str, Any] = {
            "event_type": event_type,
            "time": datetime.now().astimezone().isoformat(),
            "sink_name": sink_name,
            "output_targets": output_targets,
            **payload,
        }

        event_record: dict[str, Any] = {}

        # --- ordered fields ---
        for key in field_order:
            if key in full_event:
                event_record[key] = full_event[key]

        # --- append extras ---
        for k, v in full_event.items():
            if k not in event_record:
                event_record[k] = v

        # --- write ---
        with jsonl_path_abs.open("a", encoding="utf-8", newline="\n") as f:
            json.dump(event_record, f, ensure_ascii=False)
            f.write("\n")

    except OSError as e:
        _runtime_warning(duo, warn_msg=f"JSONL write failed: {type(e).__name__}: {e}")


def _build_files_created_entry(cfr: CreatedFileRecord) -> dict[str, Any]:
    raw = {
        "file_name": cfr.file_name,
        "file_ext": cfr.file_ext,
        "file_kind": cfr.file_kind,
        "log_file_mode": cfr.log_file_mode,
        "is_log_file": cfr.is_log_file,
        "sink_name": cfr.sink_name,
        "path": str(cfr.path),
    }

    # --- enforce schema ---
    required = set(FILES_CREATED_ENTRY_ORDER)
    actual = set(raw.keys())

    missing = required - actual
    extra = actual - required

    if missing:
        raise ValueError(f"FILES_CREATED missing fields: {sorted(missing)}")

    if extra:
        raise ValueError(f"FILES_CREATED extra fields: {sorted(extra)}")

    # --- enforce ordering ---
    return {k: raw[k] for k in FILES_CREATED_ENTRY_ORDER}
