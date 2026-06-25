"""
write_session_artifacts.py

Build and write session artifacts:
- config_table.txt
- config.json

Coordinates artifact generation from validated runtime/config state.

Last edited: 2026-05-27
"""
from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, TYPE_CHECKING

from logduo.internals.engine.runtime_classes import RuntimeRecord

if TYPE_CHECKING:
    from logduo import Duo

from logduo.internals.artifacts.build_config_table import (
    _build_session_config_class_instance_table_rows,
    _build_session_config_class_instance_txt,
)
from logduo.internals.session_config.session_config_classes import ArgSourceRecord, SessionConfig
from logduo.internals.session_config.session_config_spec import SESSION_CONFIG_SPEC

_CONFIG_TABLE_TOTAL_WIDTH = 120
_CONFIG_TABLE_MAX_WRAP_LINES = 5
_CONFIG_TABLE_MAX_COL_WIDTHS_LIST = [19, 10, 10, 10, 35, 29]
# Field Name, Group, Value, Source, Description, Allowed


# --- _write_session_artifacts() -----------------------------------------------
def _write_session_artifacts(
    duo: Duo,
    *,
    arg_source_record: ArgSourceRecord,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build rows + write enabled artifacts."""
    session_config = duo.session_config
    runtime = duo._runtime
    created_artifacts: list[dict[str, Any]] = []

    log_dir_path = runtime.main_sink_log_dir_path_abs
    assert runtime.log_dir_path_abs is not None

    if not log_dir_path:
        return [], []

    _ensure_artifact_dir_exists(log_dir_path)

    rows = _build_config_rows(
        session_config=session_config,
        arg_source_record=arg_source_record,
    )

    table_text_complete = _build_session_config_report(
        rows=rows,
        session_config=session_config,
        runtime=runtime,
        toml_record=arg_source_record.toml_record,
    )

    runtime.session_config_report = table_text_complete

    # --- config_table.txt ---
    if session_config.write_config_table:
        _write_config_table_txt(
            log_dir_path=log_dir_path,
            table_text_complete=table_text_complete,
            created_artifacts=created_artifacts,
        )

    # --- config.json ---
    if session_config.write_config_json:
        _write_config_json(
            log_dir_path=log_dir_path,
            rows=rows,
            created_artifacts=created_artifacts,
        )


    return rows, created_artifacts


# --- _ensure_artifact_dir_exists() --------------------------------------------
def _ensure_artifact_dir_exists(log_dir_path: Path) -> None:
    try:
        log_dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR:\n\n"
            "Failed to create log directory for artifacts.\n\n"
        ) from e


# --- _build_config_rows() -----------------------------------------------------
def _build_config_rows(
    *,
    session_config: SessionConfig,
    arg_source_record: ArgSourceRecord,
) -> list[dict[str, Any]]:
    try:
        return _build_session_config_class_instance_table_rows(
            session_config=session_config,
            arg_source_dict=arg_source_record.arg_source_dict,
            session_config_spec=SESSION_CONFIG_SPEC,
        )
    except Exception as e:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR:\n\n"
            "Failed to create rows for session_config table.\n\n"
        ) from e


# --- _build_session_config_report() -------------------------------------------
def _build_session_config_report(
    *,
    rows: list[dict[str, Any]],
    session_config: SessionConfig,
    runtime: RuntimeRecord,
    toml_record: dict[str, Any],
) -> str:

    table_title = "Logduo Configuration"

    if runtime.script_path_abs is None:
        subtitle = "Session"
    else:
        subtitle = f"Script: {runtime.script_name}"

    table_text_body = _build_session_config_class_instance_txt(
        title=table_title,
        subtitle=subtitle,
        rows=rows,
        session_config=session_config,
        runtime=runtime,
        toml_record=toml_record,
        wrap_table_width=_CONFIG_TABLE_TOTAL_WIDTH,
        max_col_widths=_CONFIG_TABLE_MAX_COL_WIDTHS_LIST,
        max_cell_lines=_CONFIG_TABLE_MAX_WRAP_LINES,
    )


    session_config_footer = (
        f"\n\nGenerated: {runtime.start_time_display if runtime.start_time else 'N/A'}\n"
    )

    return table_text_body + session_config_footer


# --- _write_config_table_txt() ------------------------------------------------
def _write_config_table_txt(
    *,
    log_dir_path: Path,
    table_text_complete: str,
    created_artifacts: list[dict[str, Any]],
) -> None:
    try:
        path = (log_dir_path / "config_table.txt").resolve(strict=False)

        path.write_text(
            table_text_complete,
            encoding="utf-8",
        )

        created_artifacts.append(
            {
                "path": path,
                "short_label": "config_table.txt",
                "display_order": 0,
            }
        )

    except Exception as e:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR:\n\n"
            "Failed to write config_table.txt.\n\n"
        ) from e


# --- _write_config_json() -----------------------------------------------------
def _write_config_json(
    *,
    log_dir_path: Path,
    rows: list[dict[str, Any]],
    created_artifacts: list[dict[str, Any]],
) -> None:
    try:
        path = (log_dir_path / "config.json").resolve(strict=False)

        payload = {"config_rows": rows}

        with path.open("w", encoding="utf-8") as f:
            json.dump(
                _make_json_safe(payload),
                f,
                indent=2,
                ensure_ascii=False,
            )

        created_artifacts.append(
            {
                "path": path,
                "short_label": "config.json",
                "display_order": 0,
            }
        )

    except Exception as e:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR:\n\n"
            "Failed to write config.json.\n\n"
        ) from e



# === Internal helpers =========================================================

# --- _make_json_safe() --------------------------------------------------------
def _make_json_safe(obj: object) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (MappingProxyType, dict)):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_safe(v) for v in obj]
    return obj
