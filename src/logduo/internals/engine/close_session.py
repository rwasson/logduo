"""
close_session.py

Finalize active Logduo session state and close all outputs.

Responsible for:
- final timing metadata
- sink shutdown
- footer emission
- session reset

Last edited: 2026-5-27
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from logduo.internals.engine.reset_session import _reset_session
from logduo.internals.engine.runtime_classes import RuntimeRecord
from logduo.internals.formatters.header_footer_formatters import (
    _build_auto_footer_created_file_lists,
)
from logduo.internals.sinks.console import _emit_console_end
from logduo.internals.sinks.jsonl import _emit_jsonl_end
from logduo.internals.sinks.main_sink_log import _emit_main_sink_log_end
from logduo.internals.sinks.user_sink_log import _emit_user_sink_end


# --- _close_session() ---------------------------------------------------------
def _close_session(duo: Duo) -> None:
    if not duo._initialized:
        return

    runtime = duo._runtime
    runtime.session_state = "closing"

    try:
        try:
            _finalize_timing(runtime)
        except Exception as e:
            fallback_end_time = datetime.now()

            runtime.end_time = fallback_end_time
            runtime.end_time_display = fallback_end_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            runtime.duration_seconds = None
            runtime.duration_display = None

            print(
                "LOGDUO WARNING: _finalize_timing failed; "
                "using fallback end time "
                f"→ {type(e).__name__}: {e}",
                file=sys.stderr,
            )

        try:
            _emit_user_sink_end(duo)
        except Exception as e:
            print(
                "LOGDUO WARNING: _emit_user_sink_end failed "
                f"→ {type(e).__name__}: {e}",
                file=sys.stderr,
            )

        try:
            _emit_main_sink_log_end(duo)
        except Exception as e:
            print(
                "LOGDUO WARNING: _emit_main_sink_log_end failed "
                f"→ {type(e).__name__}: {e}",
                file=sys.stderr,
            )

        try:
            _emit_console_end(duo)
        except Exception as e:
            print(
                "LOGDUO WARNING: _emit_console_end failed "
                f"→ {type(e).__name__}: {e}",
                file=sys.stderr,
            )

        try:
            if runtime.jsonl_path_abs is not None:
                _emit_jsonl_end(duo)
        except Exception as e:
            print(
                "LOGDUO WARNING: _emit_jsonl_end failed "
                f"→ {type(e).__name__}: {e}",
                file=sys.stderr,
            )

        try:
            (
                _output_dir_files,
                _project_files,
                _external_files,
                missing_files,
            ) = _build_auto_footer_created_file_lists(
                runtime=runtime,
            )
            if missing_files:
                print(
                    "LOGDUO WARNING: Declared but not created:\n"
                    f"{missing_files}",
                    file=sys.stderr,
                )
        except Exception as e:
            print(
                "LOGDUO WARNING: footer file check failed "
                f"→ {type(e).__name__}: {e}",
                file=sys.stderr,
            )

    finally:
        _reset_session(duo)


# === Internal helpers =========================================================

# --- _finalize_timing() -------------------------------------------------------
def _finalize_timing(runtime: RuntimeRecord) -> None:
    if not runtime.end_time:
        runtime.end_time = datetime.now()
        runtime.end_time_display = runtime.end_time.strftime("%Y-%m-%d %H:%M:%S")

    if runtime.start_time and runtime.end_time:
        delta = runtime.end_time - runtime.start_time

        total_seconds = int(delta.total_seconds())
        runtime.duration_seconds = total_seconds

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours:
            runtime.duration_display = f"{hours:02d}:{minutes:02d}:{seconds:02d} hr:min:sec"
        elif minutes:
            runtime.duration_display = f"{minutes:02d}:{seconds:02d} min:sec"
        else:
            runtime.duration_display = f"{seconds:02d} sec"
