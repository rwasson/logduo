"""
reset_session.py

Force-reset Logduo runtime state after failed setup or session shutdown.

Responsible for:
- Loguru handler cleanup
- runtime object replacement
- registry cleanup
- state reset for interactive reuse

Last edited: 2026-5-23
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo


# --- _abort_setup_config() ----------------------------------------------------
def _abort_setup_config(duo: Duo) -> None:
    """Reset partially initialized setup state before runtime activation."""
    from logduo.internals.engine.active_duo_registry import _clear_active_duo
    from logduo.internals.engine.runtime_classes import RuntimeRecord
    from logduo.internals.session_config.session_config_classes import ArgSourceRecord

    duo._runtime = RuntimeRecord()
    duo._arg_source_record = ArgSourceRecord()
    duo.session_config = duo._startup_config
    duo._initialized = False
    _clear_active_duo(duo)


# --- _reset_session() --------------------------------------------------------
def _reset_session(duo: Duo) -> None:
    """
    Force-reset all Logduo runtime state.

    Intended for:
        - failed setup after sinks/files may exist
        - post-close cleanup
        - interactive-session reuse

    Responsibilities:
        - remove ALL attached Loguru handlers
        - release sink ownership
        - clear CreatedFileRecords
        - reset runtime/global/session state
        - suppress normal lifecycle/footer behavior

    This is a HARD reset.

    Unlike close():
        - no footer lifecycle
        - no graceful shutdown
        - no user-facing summaries
    """

    from loguru import logger as _loguru_logger

    from logduo.internals.engine.active_duo_registry import _clear_active_duo
    from logduo.internals.engine.runtime_classes import RuntimeRecord
    from logduo.internals.session_config.session_config_classes import ArgSourceRecord

    runtime = duo._runtime

    # --- mark closing state (best-effort debug visibility) ---
    runtime.session_state = "closing"

    # --- remove ALL Loguru handlers ---
    # safer than relying only on CFR tracking
    try:
        _loguru_logger.remove()

    except Exception as e:
        print(f"LOGDUO WARNING: global Loguru cleanup failed -> {type(e).__name__}: {e}")

    # --- clear CFR registry ---
    try:
        runtime.created_file_record_registry.clear()
    except Exception as e:
        print(f"LOGDUO WARNING: CFR cleanup failed -> {type(e).__name__}: {e}")

    # --- clear runtime-managed path fields ---
    # defensive: may help GC/release references
    try:
        runtime.main_sink_log_file_path_abs = None
        runtime.main_sink_log_dir_path_abs = None
        runtime.log_dir_path_abs = None
        runtime.jsonl_path_abs = None

    except Exception as e:
        print(f"LOGDUO WARNING: runtime path cleanup failed -> {type(e).__name__}: {e}")

    # --- replace runtime with pristine object ---
    duo._runtime = RuntimeRecord()
    duo._arg_source_record = ArgSourceRecord()

    # --- clear configs/state ---
    duo.session_config = duo._startup_config
    duo._initialized = False

    # --- clear optional console ownership ---
    if hasattr(duo, "_console"):
        duo._console = None

    _clear_active_duo(duo)
