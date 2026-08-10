"""
test_prune.py

Tests Logduo-managed run-directory pruning.

Last edited: 2026-08-08
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from developer_resources.logduo_validation.test_files.test_helpers.file_helpers import (
    _make_run_dir,
)
from logduo import Duo
from logduo.internals.filesystem.prune import (
    _is_logduo_run_dir,
    _is_marker_only_run_dir,
    _prune_run_dirs,
)
from logduo.internals.session_config.session_constants import (
    _LOGDUO_RUN_DIR_MARKER_NAME,
)

# === Tests ===================================================================

# --- test_01_keep_off_disables_retention_pruning() ----------------------------
def test_01_keep_off_disables_retention_pruning(
    tmp_path: Path,
) -> None:
    old_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep="off",
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 0
    assert old_run.exists()
    assert current_run.exists()


# --- test_02_non_run_layout_disables_pruning() -------------------------------
def test_02_non_run_layout_disables_pruning(
    tmp_path: Path,
) -> None:
    run_dir = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="script",
        keep=1,
        main_sink_log_file_path=run_dir / "session.log",
    )

    assert deleted == 0
    assert run_dir.exists()


# --- test_03_none_main_log_path_disables_pruning() ----------------------------
def test_03_none_main_log_path_disables_pruning() -> None:
    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=3,
        main_sink_log_file_path=None,
    )

    assert deleted == 0


# --- test_04_keep_newest_two_runs() -------------------------------------------
def test_04_keep_newest_two_runs(
    tmp_path: Path,
) -> None:
    old_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    middle_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=2,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 1
    assert not old_run.exists()
    assert middle_run.exists()
    assert current_run.exists()


# --- test_05_keep_one_preserves_only_current_run() ----------------------------
def test_05_keep_one_preserves_only_current_run(
    tmp_path: Path,
) -> None:
    old_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    middle_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 2
    assert not old_run.exists()
    assert not middle_run.exists()
    assert current_run.exists()


# --- test_06_marker_only_current_run_is_removed() -----------------------------
def test_06_marker_only_current_run_is_removed(
    tmp_path: Path,
) -> None:
    current_run = _make_run_dir(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    assert _is_marker_only_run_dir(current_run) is True

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=3,
        main_sink_log_file_path=current_run / "session.log",
    )

    # Removing an unused current run is not counted as retention pruning.
    assert deleted == 0
    assert not current_run.exists()


# --- test_07_marker_only_current_run_does_not_displace_old_runs() -------------
def test_07_marker_only_current_run_does_not_displace_old_runs(
    tmp_path: Path,
) -> None:
    old_run_1 = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    old_run_2 = _make_run_with_output(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )

    current_run = _make_run_dir(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=2,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 0

    # The unused new run disappears.
    assert not current_run.exists()

    # It never consumes a keep slot, so prior useful runs remain.
    assert old_run_1.exists()
    assert old_run_2.exists()


# --- test_08_keep_off_still_removes_marker_only_current_run() -----------------
def test_08_keep_off_still_removes_marker_only_current_run(
    tmp_path: Path,
) -> None:
    old_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    current_run = _make_run_dir(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep="off",
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 0
    assert old_run.exists()
    assert not current_run.exists()


# --- test_09_current_run_with_output_is_not_treated_as_empty() ----------------
def test_09_current_run_with_output_is_not_treated_as_empty(
    tmp_path: Path,
) -> None:
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )

    assert _is_marker_only_run_dir(current_run) is False

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 0
    assert current_run.exists()
    assert (current_run / "session.log").exists()


# --- test_10_unmarked_directories_are_never_pruned() --------------------------
def test_10_unmarked_directories_are_never_pruned(
    tmp_path: Path,
) -> None:
    old_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    unmarked_run = tmp_path / "run_2026_01_01__10_00_00"
    unmarked_run.mkdir()
    (unmarked_run / "user_file.txt").write_text(
        "do not delete",
        encoding="utf-8",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 1
    assert not old_run.exists()
    assert current_run.exists()

    assert unmarked_run.exists()
    assert (unmarked_run / "user_file.txt").exists()


# --- test_11_wrong_prefix_is_never_pruned() -----------------------------------
def test_11_wrong_prefix_is_never_pruned(
    tmp_path: Path,
) -> None:
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    wrong_prefix = tmp_path / "backup_2026_01_01__10_00_00"
    wrong_prefix.mkdir()
    (wrong_prefix / _LOGDUO_RUN_DIR_MARKER_NAME).write_text(
        "",
        encoding="utf-8",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 0
    assert current_run.exists()
    assert wrong_prefix.exists()


# --- test_12_marker_must_be_a_file() ------------------------------------------
def test_12_marker_must_be_a_file(
    tmp_path: Path,
) -> None:
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    marker_directory_run = (
        tmp_path / "run_2026_01_01__10_00_00"
    )
    marker_directory_run.mkdir()
    (
        marker_directory_run
        / _LOGDUO_RUN_DIR_MARKER_NAME
    ).mkdir()

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 0
    assert current_run.exists()
    assert marker_directory_run.exists()


# --- test_13_current_run_is_preserved_even_when_not_newest() ------------------
def test_13_current_run_is_preserved_even_when_not_newest(
    tmp_path: Path,
) -> None:
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    newer_run_1 = _make_run_with_output(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )
    newer_run_2 = _make_run_with_output(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 2
    assert current_run.exists()
    assert not newer_run_1.exists()
    assert not newer_run_2.exists()


# --- test_14_keep_greater_than_run_count_deletes_nothing() -------------------
def test_14_keep_greater_than_run_count_deletes_nothing(
    tmp_path: Path,
) -> None:
    old_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=10,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 0
    assert old_run.exists()
    assert current_run.exists()


# --- test_15_invalid_keep_value_disables_retention_pruning() ------------------
@pytest.mark.parametrize(
    "keep",
    [
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
    ],
)
def test_15_invalid_keep_value_disables_retention_pruning(
    tmp_path: Path,
    keep: int,
) -> None:
    old_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=keep,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 0
    assert old_run.exists()
    assert current_run.exists()


# --- test_16_deletion_failure_is_safe_and_pruning_continues() -----------------
def test_16_deletion_failure_is_safe_and_pruning_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_run_1 = _make_run_with_output(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )
    old_run_2 = _make_run_with_output(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )
    current_run = _make_run_with_output(
        tmp_path,
        "run_2026_01_03__10_00_00",
    )

    real_rmtree = shutil.rmtree

    def guarded_rmtree(
        path: str | Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        if Path(path) == old_run_1:
            raise PermissionError(
                "simulated deletion failure"
            )

        real_rmtree(
            path,
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        "logduo.internals.filesystem.prune.shutil.rmtree",
        guarded_rmtree,
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 1

    assert old_run_1.exists()
    assert not old_run_2.exists()
    assert current_run.exists()


# --- test_17_marker_only_deletion_failure_is_safe() ---------------------------
def test_17_marker_only_deletion_failure_is_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_run = _make_run_dir(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )

    def failing_rmtree(
        path: str | Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        raise PermissionError(
            "simulated deletion failure"
        )

    monkeypatch.setattr(
        "logduo.internals.filesystem.prune.shutil.rmtree",
        failing_rmtree,
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=3,
        main_sink_log_file_path=current_run / "session.log",
    )

    assert deleted == 0
    assert current_run.exists()


# --- test_18_missing_runs_parent_directory_is_safe() --------------------------
def test_18_missing_runs_parent_directory_is_safe(
    tmp_path: Path,
) -> None:
    main_log_path = (
        tmp_path
        / "missing_session"
        / "run_2026_01_01__10_00_00"
        / "session.log"
    )

    deleted = _prune_run_dirs(
        log_file_layout="run",
        keep=1,
        main_sink_log_file_path=main_log_path,
    )

    assert deleted == 0
    assert not (
        tmp_path / "missing_session"
    ).exists()


# --- test_19_is_logduo_run_dir_requires_all_safety_conditions() ---------------
def test_19_is_logduo_run_dir_requires_all_safety_conditions(
    tmp_path: Path,
) -> None:
    valid = _make_run_dir(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )

    no_marker = (
        tmp_path / "run_2026_01_02__10_00_00"
    )
    no_marker.mkdir()

    wrong_name = (
        tmp_path / "backup_2026_01_03__10_00_00"
    )
    wrong_name.mkdir()
    (
        wrong_name / _LOGDUO_RUN_DIR_MARKER_NAME
    ).write_text(
        "",
        encoding="utf-8",
    )

    ordinary_file = tmp_path / "run_notes.txt"
    ordinary_file.write_text(
        "not a directory",
        encoding="utf-8",
    )

    assert _is_logduo_run_dir(valid) is True
    assert _is_logduo_run_dir(no_marker) is False
    assert _is_logduo_run_dir(wrong_name) is False
    assert _is_logduo_run_dir(ordinary_file) is False


# --- test_20_marker_only_requires_exactly_one_marker_file() -------------------
def test_20_marker_only_requires_exactly_one_marker_file(
    tmp_path: Path,
) -> None:
    marker_only = _make_run_dir(
        tmp_path,
        "run_2026_01_01__10_00_00",
    )

    with_output = _make_run_dir(
        tmp_path,
        "run_2026_01_02__10_00_00",
    )
    (with_output / "session.log").write_text(
        "output",
        encoding="utf-8",
    )

    assert _is_marker_only_run_dir(marker_only) is True
    assert _is_marker_only_run_dir(with_output) is False


# --- test_21_unmaterialized_run_does_not_prune_old_runs_on_close() -----------
def test_21_unmaterialized_run_does_not_prune_old_runs_on_close(
        tmp_path: Path,
) -> None:
    log = Duo()

    log.configure(
        log_dir_path=tmp_path / "logs",
        log_file_layout="run",
        keep=1,
        console_verbosity=0,
        log_verbosity=0,
        write_config_table=False,
        write_config_json=False,
        write_jsonl=False,
    )

    current_run_dir = log._runtime.main_sink_log_dir_path_abs

    assert current_run_dir is not None

    # No file output was requested, so the current run is resolved
    # but never physically created.
    assert not current_run_dir.exists()

    # Create two earlier useful Logduo runs beside the prospective current run.
    runs_parent = current_run_dir.parent

    old_run_1 = _make_run_with_output(
        runs_parent,
        "run_2026_01_01__10_00_00",
    )
    old_run_2 = _make_run_with_output(
        runs_parent,
        "run_2026_01_02__10_00_00",
    )

    print("")
    print("--- before close ---")
    print(f"current run exists: {current_run_dir.exists()}")
    print(f"old run 1 exists:   {old_run_1.exists()}")
    print(f"old run 2 exists:   {old_run_2.exists()}")

    log.close()

    print("")
    print("--- after close ---")
    print(f"current run exists: {current_run_dir.exists()}")
    print(f"old run 1 exists:   {old_run_1.exists()}")
    print(f"old run 2 exists:   {old_run_2.exists()}")

    # An unmaterialized session has no run-directory lifecycle:
    # it creates nothing and triggers no retention pruning.
    assert not current_run_dir.exists()
    assert old_run_1.exists()
    assert old_run_2.exists()


# === Internal helpers =========================================================

def _make_run_with_output(
    parent: Path,
    name: str,
) -> Path:
    run_dir = _make_run_dir(
        parent,
        name,
    )

    (run_dir / "session.log").write_text(
        "generated output",
        encoding="utf-8",
    )

    return run_dir
