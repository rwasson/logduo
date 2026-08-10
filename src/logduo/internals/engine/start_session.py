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

Last edited: 2026-08-10
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
from logduo.internals.engine.reset_session import _abort_setup_config, _reset_session
from logduo.internals.engine.runtime_classes import RuntimeRecord
from logduo.internals.filesystem.created_file_record_builders import (
    _build_artifact_created_file_record,
)
from logduo.internals.filesystem.created_file_record_registration import (
    _register_created_file_record,
)
from logduo.internals.filesystem.path_policy import _ensure_run_dir_and_marker
from logduo.internals.session_config.session_config_classes import (
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
        assert duo.session_config is not None

        needs_output_dir = (
                duo.session_config.log_verbosity > 0
                or duo.session_config.write_config_table
                or duo.session_config.write_config_json
                or duo.session_config.write_jsonl
        )
        if needs_output_dir:
            _ensure_run_dir_and_marker(duo)


        # --- Initialize sinks ---
        duo._runtime.session_state = "setting_up_sinks"
        _setup_sinks(duo)

        # --- Finalize session lifecycle ---
        _setup_duo(duo)
        duo._runtime.session_state = "running"
        _set_active_duo(duo)

        # --- Write Artifacts ---
        _setup_artifacts(duo)

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
    duo.session_config = SessionConfig.from_dict(resolved_session_config)

    # --- Rich traceback setup ---
    width = max(60, min(100, duo.session_config.console_wrap_width - 10))
    install(show_locals=False, word_wrap=True, width=width)
    return arg_source_record


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
        _, created_artifacts = _write_session_artifacts(
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


