"""
prune.py

Run-directory pruning helpers for log_file_layout="run".

Responsible for:
- identifying eligible Logduo run directories
- preserving active/current session directories
- enforcing keep retention policy
- safe best-effort directory deletion


Last edited 2026-5-27
"""

import shutil
from pathlib import Path


# --- _prune_run_dirs() --------------------------------------------------------
def _prune_run_dirs(*, log_file_layout: str, keep: int | str, current_main_path: Path | None) -> int:
    """
    Prune old Logduo run directories while preserving active sessions.
    """

    # --- disable pruning ---

    if keep == "off" or current_main_path is None or log_file_layout != "run":
        deleted_file_count = 0  # no pruning performed
        return deleted_file_count

    if not isinstance(keep, int) or keep <= 0:
        deleted_file_count = 0
        return deleted_file_count

    try:
        session_runs_dir = current_main_path.parent.parent
        entries = list(session_runs_dir.iterdir())
    except (FileNotFoundError, PermissionError, NotADirectoryError, OSError):
        deleted_file_count = 0  # no pruning performed
        return deleted_file_count

    run_dirs = [
        p
        for p in entries
        if (p.is_dir() and p.name.startswith("run_") and (p / ".logduo_marker").is_file())
    ]

    if not run_dirs:
        deleted_file_count = 0  # no pruning performed
        return deleted_file_count

    # newest first
    run_dirs.sort(key=lambda p: p.name, reverse=True)

    keep_dirs: list[Path] = []

    # always keep current run
    if current_main_path is not None:
        current_dir = current_main_path.parent
        for p in run_dirs:
            try:
                if p.samefile(current_dir):
                    keep_dirs.append(p)
                    break
            except OSError:
                continue

    # fill remaining keep slots
    # keep counts total retained run directories, including the current run
    for p in run_dirs:
        if len(keep_dirs) >= keep:
            break
        if p in keep_dirs:
            continue
        keep_dirs.append(p)

    deleted_file_count = 0  # initialize

    for p in run_dirs:
        if p not in keep_dirs:
            try:
                shutil.rmtree(p)
                deleted_file_count += 1
            except OSError:
                continue

    return deleted_file_count
