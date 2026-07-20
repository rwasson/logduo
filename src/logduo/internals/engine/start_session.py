"""
start_session.py

Initialize and bootstrap a Logduo runtime session.

Responsible for:
- runtime initialization
- session_config setup
- sink initialization
- artifact generation
- failure rollback/reset behavior

Acts as the primary lifecycle entry point for log.configure().

Last edited: 2026-5-27
"""

from __future__ import annotations

import platform
import sys
from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from loguru import logger as _loguru_logger
from rich.traceback import install

from logduo.internals.artifacts.write_session_artifacts import _write_session_artifacts
from logduo.internals.engine.active_duo_registry import _set_active_duo
from logduo.internals.engine.level_entry import _level_entry
from logduo.internals.engine.reset_session import _abort_setup_config, _reset_session
from logduo.internals.engine.runtime_classes import RuntimeRecord
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.filesystem.created_file_record_builders import (
    _build_artifact_created_file_record,
)
from logduo.internals.filesystem.created_file_record_registration import (
    _register_created_file_record,
)
from logduo.internals.filesystem.prune import _prune_run_dirs
from logduo.internals.session_config.session_config_classes import (
    _build_session_config_class_instance,
    ArgSourceRecord,
    SessionConfig,
)
from logduo.internals.session_config.session_config_resolver import _resolve_session_config
from logduo.internals.session_config.session_constants import (
    _SESSION_DISPLAY_TIMESTAMP_FMT,
    _SESSION_TIMESTAMP_FMT,
)
from logduo.internals.sinks.console import _initialize_console
from logduo.internals.sinks.jsonl import _initialize_jsonl
from logduo.internals.sinks.main_sink_log import _initialize_main_sink_log


# --- _start_session() ---------------------------------------------------------
def _start_session(
    duo: Duo,
    *,
    configure_args: dict[str, Any] | None = None,
) -> SessionConfig:
    if duo._initialized:
        return duo.session_config
    try:

        # --- Initialize ---
        # default: duo._runtime.session_state = "initializing"

        # remove Loguru default stderr sink.
        _loguru_logger.remove()

        _populate_runtime_time_fields(duo._runtime)
        _populate_runtime_environment_and_process_id_fields(duo)
        _populate_detected_interactive(duo._runtime)

        # duo.build_startup_config(defaults=DEFAULTS)

        # --- Resolve configure args and build SessionConfig --- ---
        duo._runtime.session_state = "setting_up_config"
        duo._arg_source_record = _setup_config(duo, configure_args)
        _create_run_dir(duo)
        assert duo.session_config is not None

        # --- Initialize sinks ---
        duo._runtime.session_state = "setting_up_sinks"
        _setup_sinks(duo)

        # --- Finalize session lifecycle ---
        _setup_duo(duo)
        duo._runtime.session_state = "running"
        _set_active_duo(duo)

        # --- Write Artifacts ---
        _setup_artifacts(duo)

        # --- Prune old run directories (if keep != "off") ---
        _setup_prune(duo)

        return duo.session_config

    except Exception:
        if duo._runtime.session_state in ("initializing", "setting_up_config"):
            _abort_setup_config(duo)
        else:
            _reset_session(duo)
        raise


# === Internal helpers =========================================================

# --- _setup_config() ------------------------------------------------------------
def _setup_config(
        duo: Duo,
        configure_args: dict[str, Any] | None = None,
) -> ArgSourceRecord:

    resolved_session_config, runtime, arg_source_record = _resolve_session_config(
        duo,
        configure_args=configure_args,
        runtime=duo._runtime,
    )

    duo._runtime = runtime
    duo.session_config = _build_session_config_class_instance(
        resolved_session_config
    )

    # --- Rich traceback setup ---
    width = max(60, min(100, duo.session_config.console_wrap_width - 10))
    install(show_locals=False, word_wrap=True, width=width)
    return arg_source_record


# --- _create_run_dir() --------------------------------------------------------
def _create_run_dir(duo: Duo) -> None:
    """
    Create Logduo-managed run directory and ownership marker.

    Called once during startup after paths have been resolved.
    """

    session_config = duo.session_config

    if session_config.log_file_layout != "run":
        return

    log_dir_path = duo._runtime.main_sink_log_dir_path_abs

    if log_dir_path is None:
        raise RuntimeError("LOGDUO INTERNAL ERROR: run directory path missing")
    try:
        log_dir_path.mkdir(parents=True, exist_ok=True)
        marker_path = log_dir_path / ".logduo_marker"
        marker_path.write_text(
            "This directory was created and managed by Logduo.\n"
            "Directories containing this file may be automatically "
            "pruned based on the current 'keep' setting.\n"
            "To disable pruning, set keep=0.\n"
            "Delete this file to prevent this directory from being "
            "automatically pruned.\n",
            encoding="utf-8",
        )

    except OSError as e:
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR: Failed to create run directory "
            f"'{log_dir_path}': {e}"
        ) from e


# --- _setup_sinks() -----------------------------------------------------------
def _setup_sinks(duo: Duo) -> None:
    duo._runtime = duo._runtime
    _initialize_console(duo)
    _initialize_main_sink_log(duo)
    _initialize_jsonl(duo)


# --- _setup_duo() ----------------------------------------------------
def _setup_duo(duo: Duo) -> None:
    duo._runtime = duo._runtime
    duo._initialized = True
    duo._register_close_on_exit()


# --- _setup_artifacts() -------------------------------------------------------
def _setup_artifacts(duo: Duo) -> None:
    try:
        rows, created_artifacts = _write_session_artifacts(
            duo, arg_source_record=duo._arg_source_record
        )
    except Exception as e:
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR:\n\n"
            f"_setup_artifacts() failed.\n\n"
            f"{type(e).__name__}: {e}"
        ) from e

    for record in created_artifacts:
        _register_created_file_record(
            duo, _build_artifact_created_file_record(file_path=record["path"])
        )


# --- _setup_prune() -----------------------------------------------------------
def _setup_prune(duo: Duo) -> None:
    """Prune old run directories after session initialization."""
    deleted = 0
    runtime = duo._runtime

    if duo.session_config.log_file_layout == "run":
        try:
            deleted = _prune_run_dirs(
                log_file_layout=duo.session_config.log_file_layout,
                keep=duo.session_config.keep,
                current_main_path=duo._runtime.main_sink_log_file_path_abs,
            )
        except Exception as e:
            _runtime_warning(
                duo,
                warn_msg=f"Run directory pruning failed ({type(e).__name__}: {e})",
                warn_key="prune_failed",
            )

        duo._runtime.deleted_file_count += deleted

        # --- Prune summary ---
        if runtime.deleted_file_count > 0:
            msg = (
                # f" \n"
                f"pruned run directories: {runtime.deleted_file_count} "
                # f"{'y' if runtime.deleted_file_count == 1 else 'ies'} "
                # f":  {runtime.deleted_file_count}  "
                f"(keep={duo.session_config.keep}) "
                f" \n"
                # f"Set keep='off' to disable."
            )
            _level_entry(
                duo,
                msg,
                level="INFO",
                console_style="muted",
                no_prefix=True,
                event_type="prune_update",
            )


# ==== Internal helpers ===========================================================


# --- _populate_runtime_time_fields() ----------------------------------------
def _populate_runtime_time_fields(runtime: RuntimeRecord) -> None:
    if runtime.start_time is not None:
        return
    start = datetime.now()
    runtime.start_time = start
    runtime.start_time_display = start.strftime(_SESSION_DISPLAY_TIMESTAMP_FMT)
    runtime.session_timestamp = start.strftime(_SESSION_TIMESTAMP_FMT)
    runtime.run_id_iso = start.isoformat(timespec="seconds")


# --- _populate_runtime_environment_and_process_id_fields() ---------------------------------------
def _populate_runtime_environment_and_process_id_fields(duo: Duo) -> None:
    runtime = duo._runtime

    # --- runtime environment ---
    runtime.os_name = platform.system()
    runtime.python_version = sys.version.split()[0]

    # --- process id ---
    duo._refresh_pid()


# --- _populate_detected_interactive() -----------------------------------------
def _populate_detected_interactive(runtime: RuntimeRecord) -> None:
    """Populate best-effort interactive-session detection flags."""
    detected_interactive = any(
        [
            hasattr(sys, "ps1"),
            bool(sys.flags.interactive),
            "pydevconsole" in sys.modules,
            "IPython" in sys.modules,
            "ipykernel" in sys.modules,
        ]
    )

    runtime.detected_interactive = detected_interactive


