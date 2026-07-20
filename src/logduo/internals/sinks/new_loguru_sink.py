"""
new_loguru_sink.py

Initialize for user's custom new_loguru_sink().

Internal integration for attaching external Loguru sinks via `logger.add()`.

Purpose:
- Accept a single `sink` input (name OR absolute file path)
- Resolve it into a fully-qualified file path
- Apply file initialization behavior (write / append / timestamped)
- Attach a Loguru sink
- Register the file in CreatedFileRecord for tracking and reporting
- Optionally emit a JSONL event describing the sink creation

Notes:
- This is a thin integration layer.
- Logduo resolves file paths, applies file_mode behavior, and tracks created files.
- Loguru retains control of filtering, formatting,
  serialization, rotation, retention, compression,
  and other sink-specific behavior.
- Callable Loguru arguments are passed through unchanged.

Last edited: 2026-5-27
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from logduo.logduo import Duo

from loguru import logger as _loguru_logger

from logduo.internals.api_arg_resolvers.api_arg_resolver_helpers import (
    _resolve_log_file_mode,
    _resolve_new_logger_target_arg,
)
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.filesystem.created_file_record_builders import (
    _build_loguru_created_file_record,
)
from logduo.internals.filesystem.created_file_record_registration import (
    _register_created_file_record,
)
from logduo.internals.filesystem.path_finders import _apply_timestamp_to_filename
from logduo.internals.session_config.session_constants import (
    _NOT_GIVEN,
    _NotGiven,
    _VALID_LOGURU_ADD_KWARGS,
    LogFileModeType,
)


def _initialize_new_loguru_sink(
    duo: Duo,
    sink: str | Path,
    file_mode: str | LogFileModeType | _NotGiven = _NOT_GIVEN,
    **kwargs: Any,
) -> int | None:
    """
    Resolve a Loguru sink path, apply Logduo file-mode behavior,
    attach the sink, and register it for tracking.
    Advanced Loguru behavior (filters, formatters, rotation,
    retention, serialization, callable hooks, etc.) is passed
    through unchanged.
    """

    duo._ensure_initialized()
    runtime = duo._runtime

    # --- capture original raw kwargs (before mutation) ---
    raw_kwargs = dict(kwargs)
    invalid_kwargs = [k for k in raw_kwargs if k not in _VALID_LOGURU_ADD_KWARGS]
    if invalid_kwargs:
        _runtime_warning(
            duo, warn_msg=f"Ignored invalid loguru kwargs in new_loguru_sink(): {invalid_kwargs}"
        )
    filtered_kwargs = {k: v for k, v in raw_kwargs.items() if k in _VALID_LOGURU_ADD_KWARGS}

    # Resolve user sink argument into a validated file path.
    sink_info = _resolve_new_logger_target_arg(duo=duo, value=sink)
    resolved_file_path = sink_info["file_path"]

    # --- validate file_mode ---
    file_mode = _resolve_log_file_mode(duo=duo, log_file_mode=file_mode)

    # --- timestamp ---
    if file_mode == "timestamped":
        assert runtime.session_timestamp is not None
        resolved_file_path = resolved_file_path.with_name(
            _apply_timestamp_to_filename(
                filename=resolved_file_path.name, session_timestamp=runtime.session_timestamp
            )
        )

    # --- finalize path ---
    final_path = resolved_file_path.resolve(strict=False)

    # --- duplicate check ---
    existing_paths = {
        Path(cfr.path).resolve(strict=False) for cfr in runtime._get_file_list_in_cfr()
    }

    if final_path in existing_paths:
        raise ValueError(f"Output file already in use: {final_path}")

    # --- ensure directory ---
    try:
        final_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        _runtime_warning(duo, warn_msg=f"Failed to create directory → {e}")
        return None

    # --- apply write mode ---
    if file_mode == "write":
        try:
            with final_path.open("w", encoding="utf-8"):
                pass
        except OSError as e:
            _runtime_warning(duo, warn_msg=f"Failed to initialize loguru file → {e}")
            return None

    # --- attach loguru sink ---
    try:
        if "enqueue" not in filtered_kwargs:
            filtered_kwargs["enqueue"] = True
        if "format" not in filtered_kwargs:
            filtered_kwargs["format"] = "{message}"

        sink_id = _loguru_logger.add(final_path, **filtered_kwargs)

    except (OSError, ValueError, TypeError) as e:
        _runtime_warning(
            duo,
            warn_msg=f"Failed to attach external Loguru sink {sink} ({type(e).__name__}): {e}",
        )
        return None

    # --- register CFR (non-fatal if fails) ---
    try:
        cfr = _build_loguru_created_file_record(file_path=final_path, sink_id=sink_id)

        extra: dict[str, object] = {
            "raw_kwargs": _serialize_new_loguru_kwargs_for_cfr_field(raw_kwargs),
            "final_kwargs": _serialize_new_loguru_kwargs_for_cfr_field(filtered_kwargs),
        }

        _register_created_file_record(duo, cfr, extra=extra)

    except (ValueError, OSError) as e:
        _runtime_warning(duo, warn_msg=f"Failed to register loguru file → {e}")
        # DO NOT return → sink already attached

    return sink_id


# --- _serialize_new_loguru_kwargs_for_cfr_field() ------------------------------------------
def _serialize_new_loguru_kwargs_for_cfr_field(d: dict) -> dict[str, str | int | float | bool]:
    out = {}
    for k, v in d.items():
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = f"<{type(v).__name__}>"
    return out
