"""
created_file_record_registration.py

Central registration point for CreatedFileRecord objects.

Responsible for:
- resolved-path enforcement
- duplicate-path prevention
- runtime registry insertion
- JSONL registration event emission

Last edited 2026-5-27
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from logduo.internals.engine.runtime_classes import CreatedFileRecord
from logduo.internals.engine.runtime_warning import _runtime_warning


# --- _register_created_file_record() ------------------------------------------
def _register_created_file_record(
    duo: Duo, record: CreatedFileRecord, *, extra: dict[str, object] | None = None
) -> CreatedFileRecord:
    runtime = duo._runtime

    path = record.path
    if path != record.path.resolve(strict=False):
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: CreatedFileRecord.path must be resolved before registration"
        )

    # --- enforce path uniqueness ---
    for cfr in runtime._get_file_list_in_cfr():
        if path == cfr.path:
            raise ValueError(
                f"Duplicate file path detected: '{path}'. "
                "Another sink is already writing to this file. "
                "Choose a different file name/path, or use file_mode='timestamped' "
                "to generate unique files per run. "
                "(e.g., new_logger('audit', file_mode='timestamped'))."
            )

    key = path
    runtime.created_file_record_registry[key] = record

    # --- emit JSONL registration event ---
    if duo.session_config.write_jsonl:
        try:
            from logduo.internals.sinks.jsonl import _emit_jsonl_file_registration

            _emit_jsonl_file_registration(duo, record, extra=extra)
        except Exception as e:
            _runtime_warning(
                duo, warn_msg=f"JSONL file registration event failed -> {type(e).__name__}: {e}"
            )

    return record
