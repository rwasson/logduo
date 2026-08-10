"""
prune.py

Run-directory pruning helpers for log_file_layout="run".

Responsible for:
- identifying eligible Logduo run directories
- removing an empty current run directory containing only the Logduo marker
- preserving active/current session directories
- enforcing keep retention policy
- safe best-effort directory deletion

Last edited: 2026-08-10
"""

import shutil
from pathlib import Path

from logduo.internals.session_config.session_constants import (
    _LOGDUO_RUN_DIR_MARKER_NAME,
)


def _prune_run_dirs(  # noqa: PLR0911
    *,
    log_file_layout: str,
    keep: int | str,
    main_sink_log_file_path: Path | None,
) -> int:
    """
    Prune Logduo-managed run directories.

    If the current run directory was never created, no pruning is performed.

    If the current run directory contains only the Logduo ownership marker,
    remove that directory without counting it as a pruned retained run.

    Otherwise, keep the current run and enforce the configured retention count.

    Returns:
        Number of older retained run directories pruned by the keep policy.
    """

    if (
        log_file_layout != "run"
        or main_sink_log_file_path is None
    ):
        return 0

    current_run_dir = main_sink_log_file_path.parent

    # --- Current run was never materialized ----------------------------------
    if not current_run_dir.exists():
        return 0

    # --- Remove marker-only current run directory -----------------------------
    if _is_marker_only_run_dir(current_run_dir):
        try:
            shutil.rmtree(current_run_dir)
        except OSError:
            pass
        else:
            return 0

    # --- Current directory must be Logduo-managed -----------------------------
    if not _is_logduo_run_dir(current_run_dir):
        return 0

    # --- Retention pruning disabled -------------------------------------------
    if keep == "off":
        return 0

    if not isinstance(keep, int) or keep <= 0:
        return 0

    # --- Find Logduo-managed run directories ----------------------------------
    try:
        session_runs_dir = current_run_dir.parent
        entries = list(session_runs_dir.iterdir())
    except OSError:
        return 0

    run_dirs = [
        path
        for path in entries
        if _is_logduo_run_dir(path)
    ]

    if not run_dirs:
        return 0

    # Newest first.
    run_dirs.sort(
        key=lambda path: path.name,
        reverse=True,
    )

    keep_dirs: list[Path] = []

    # If the current run still exists, always retain it first.
    if _is_logduo_run_dir(current_run_dir):
        keep_dirs.append(current_run_dir)

    # Fill remaining keep slots with the newest prior runs.
    for run_dir in run_dirs:
        if len(keep_dirs) >= keep:
            break

        if run_dir in keep_dirs:
            continue

        keep_dirs.append(run_dir)

    # --- Delete runs outside retention policy ---------------------------------
    deleted_run_dir_count = 0

    for run_dir in run_dirs:
        if run_dir in keep_dirs:
            continue

        try:
            shutil.rmtree(run_dir)
            deleted_run_dir_count += 1
        except OSError:
            continue

    return deleted_run_dir_count


# === Internal helpers =========================================================
# --- _is_logduo_run_dir() -----------------------------------------------------
def _is_logduo_run_dir(
    path: Path,
) -> bool:
    """
    Return True only for a Logduo-managed run directory.
    """
    return (
        path.is_dir()
        and path.name.startswith("run_")
        and (path / _LOGDUO_RUN_DIR_MARKER_NAME).is_file()
    )


# --- _is_marker_only_run_dir() ------------------------------------------------
def _is_marker_only_run_dir(
    path: Path,
) -> bool:
    """
    Return True when a Logduo run directory contains only its ownership marker.
    """
    if not _is_logduo_run_dir(path):
        return False

    try:
        entries = list(path.iterdir())
    except OSError:
        return False

    return (
        len(entries) == 1
        and entries[0].name == _LOGDUO_RUN_DIR_MARKER_NAME
    )
