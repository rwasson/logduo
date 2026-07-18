"""
test_prune.py

Tests run-directory pruning.

Last edited: 2026-06-08
"""
from __future__ import annotations

import shutil
from pathlib import Path

from developer_resources.logduo_validation.pytest_files.pytest_helpers.file_helpers import (
    _make_run_dir,
)
from logduo.internals.filesystem.prune import _prune_run_dirs


# --- test_01_keep_off_disables_pruning() --------------------------------------
def test_01_keep_off_disables_pruning(tmp_path: Path):

    run_dir = _make_run_dir(tmp_path, "run_1")

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep="off",
        current_main_path=run_dir / "session.log",
    )

    assert deleted == 0
    assert run_dir.exists()


# --- test_02_non_run_layout_disables_pruning() -------------------------------
def test_02_non_run_layout_disables_pruning(tmp_path: Path):

    run_dir = _make_run_dir(tmp_path, "run_1")

    deleted = _prune_run_dirs(
        log_file_layout="script",
        keep=3,
        current_main_path=run_dir / "session.log",
    )

    assert deleted == 0
    assert run_dir.exists()


# --- test_03_current_main_path_none_disables_pruning() ------------------------
def test_03_current_main_path_none_disables_pruning(tmp_path: Path):

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=3,
        current_main_path=None,
    )

    assert deleted == 0


# --- test_04_keep_newest_two_runs() -------------------------------------------
def test_04_keep_newest_two_runs(tmp_path: Path):

    r1 = _make_run_dir(tmp_path, "run_2026_01_01__10_00_00")
    r2 = _make_run_dir(tmp_path, "run_2026_01_02__10_00_00")
    r3 = _make_run_dir(tmp_path, "run_2026_01_03__10_00_00")

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=2,
        current_main_path=r3 / "session.log",
    )

    assert deleted == 1

    assert not r1.exists()
    assert r2.exists()
    assert r3.exists()


# --- test_05_current_run_always_preserved() -----------------------------------
def test_05_current_run_always_preserved(tmp_path: Path):
    """
    Simulate a normal Logduo session:

    Existing runs:
        r1 (oldest)
        r2
    New session:
        r3 (current run)
    keep=1 should still preserve the active current run.

    """

    r1 = _make_run_dir(tmp_path, "run_2026_01_01__10_00_00")
    r2 = _make_run_dir(tmp_path, "run_2026_01_02__10_00_00")
    r3 = _make_run_dir(tmp_path, "run_2026_01_03__10_00_00")

    print(" ")
    print("********************************************************************")
    print("test_05_current_run_always_preserved")
    print("-------------")
    print("before prune")
    for name, run_dir in (
        ("r1", r1),
        ("r2", r2),
        ("r3 (current)", r3),
    ):
        print(
            f"{name}: "
            f"exists={run_dir.exists()}  "
            f"marker={(run_dir / '.logduo_marker').exists()}  "
            f"path={run_dir}"
        )

    deleted_file_count = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        current_main_path=r3 / "session.log",
    )
    print(" ")

    print("-------------")
    print("after prune")
    print(f"deleted_file_count = {deleted_file_count}")
    for name, run_dir in (
        ("r1", r1),
        ("r2", r2),
        ("r3 (current)", r3),
    ):

        print(
            f"{name}: "
            f"exists={run_dir.exists()}  "
            f"marker={(run_dir / '.logduo_marker').exists()}  "
            f"path={run_dir}"
        )
    # Current implementation behavior:
    #   keep=1 preserves:
    #       - current run (r3)
    #       - newest retained run slot
    #
    # Result:
    #       r1 deleted
    #       r2 deleted
    #       r3 preserved


    assert deleted_file_count == 2
    assert not r1.exists()
    assert not r2.exists()
    assert r3.exists()


# --- test_06_ignore_non_logduo_directories() ----------------------------------
def test_06_ignore_non_logduo_directories(tmp_path: Path):

    r1 = _make_run_dir(tmp_path, "run_1")

    other = tmp_path / "run_2"
    other.mkdir()

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        current_main_path=r1 / "session.log",
    )

    assert deleted == 0

    assert r1.exists()
    assert other.exists()


# --- test_07_keep_zero_disables_pruning() -------------------------------------
def test_07_keep_zero_disables_pruning(tmp_path: Path):

    r1 = _make_run_dir(tmp_path, "run_1")

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=0,
        current_main_path=r1 / "session.log",
    )

    assert deleted == 0
    assert r1.exists()


# --- test_08_no_logduo_marker_dirs_not_pruned() -------------------------------
def test_08_no_logduo_marker_dirs_not_pruned(tmp_path: Path):
    (tmp_path / "run_1").mkdir()
    (tmp_path / "run_2").mkdir()

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        current_main_path=(tmp_path / "run_2" / "session.log"),
    )

    assert deleted == 0


# --- test_09_non_run_layout_never_prunes() -----------------------------------
def test_09_non_run_layout_never_prunes(tmp_path: Path):
    logs_dir = tmp_path / "my_script"
    logs_dir.mkdir()
    session_dir = logs_dir / "session"
    session_dir.mkdir()

    r1 = session_dir / "session_a.log"
    r2 = session_dir / "session_b.log"

    r1.write_text("a")
    r2.write_text("b")

    deleted_file_count = _prune_run_dirs(
        log_file_layout="script",
        keep=1,
        current_main_path=r2,
    )

    print(" ")
    print("********************************************************************")
    print("test_09_non_run_layout_never_prunes")
    print(f"deleted_file_count = {deleted_file_count}")
    print(f"r1.exists() = {r1.exists()}")
    print(f"r2.exists() = {r2.exists()}")

    assert deleted_file_count == 0
    assert r1.exists()
    assert r2.exists()
    assert r1.read_text() == "a"
    assert r2.read_text() == "b"


# --- test_10_current_run_preserved_when_not_newest() -------------------------
def test_10_current_run_preserved_when_not_newest(tmp_path: Path):

    current = _make_run_dir(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    newer_1 = _make_run_dir(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )
    newer_2 = _make_run_dir(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        current_main_path=current / "session.log",
    )

    assert deleted == 2

    assert current.exists()
    assert not newer_1.exists()
    assert not newer_2.exists()


# --- test_11_only_marked_run_directories_are_deleted() -----------------------
def test_11_only_marked_run_directories_are_deleted(tmp_path: Path):

    old_run = _make_run_dir(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    current_run = _make_run_dir(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )

    unmarked_run = tmp_path / "run_2025_01_01__10_00_00"
    unmarked_run.mkdir()

    wrong_prefix = tmp_path / "backup_2025_01_01"
    wrong_prefix.mkdir()
    (wrong_prefix / ".logduo_marker").write_text("", encoding="utf-8")

    ordinary_file = tmp_path / "run_notes.txt"
    ordinary_file.write_text("keep me", encoding="utf-8")

    marker_directory_run = tmp_path / "run_2024_01_01__10_00_00"
    marker_directory_run.mkdir()
    (marker_directory_run / ".logduo_marker").mkdir()

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        current_main_path=current_run / "session.log",
    )

    assert deleted == 1
    assert not old_run.exists()

    assert current_run.exists()
    assert unmarked_run.exists()
    assert wrong_prefix.exists()
    assert ordinary_file.exists()
    assert marker_directory_run.exists()


# --- test_12_deletion_failure_is_safe_and_pruning_continues() ----------------
def test_12_deletion_failure_is_safe_and_pruning_continues(
    tmp_path: Path,
    monkeypatch,
):

    old_1 = _make_run_dir(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    old_2 = _make_run_dir(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )
    current = _make_run_dir(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    real_rmtree = shutil.rmtree

    def guarded_rmtree(path: Path):
        if Path(path) == old_1:
            raise PermissionError("simulated deletion failure")

        real_rmtree(path)

    monkeypatch.setattr(
        "logduo.internals.filesystem.prune.shutil.rmtree",
        guarded_rmtree,
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        current_main_path=current / "session.log",
    )

    assert deleted == 1

    assert old_1.exists()
    assert not old_2.exists()
    assert current.exists()


# --- test_13_missing_session_runs_directory_is_safe() ------------------------
def test_13_missing_session_runs_directory_is_safe(tmp_path: Path):

    current_main_path = (
        tmp_path
        / "missing_session"
        / "run_2026_01_01__10_00_00"
        / "session.log"
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        current_main_path=current_main_path,
    )

    assert deleted == 0
    assert not tmp_path.joinpath("missing_session").exists()


# --- test_14_keep_greater_than_run_count_deletes_nothing() -------------------
def test_14_keep_greater_than_run_count_deletes_nothing(tmp_path: Path):

    r1 = _make_run_dir(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    r2 = _make_run_dir(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=10,
        current_main_path=r2 / "session.log",
    )

    assert deleted == 0
    assert r1.exists()
    assert r2.exists()


