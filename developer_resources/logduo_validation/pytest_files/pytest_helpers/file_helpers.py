"""
file_helpers.py

Commonly used test utility functions

Last edited: 2026-06-12
"""

from pathlib import Path

import pytest

from logduo import Duo

_VERBOSITY_EXPECTATIONS = [
    pytest.param(
        0,
        set(),
        id="verbosity-0",
    ),
    pytest.param(
        1,
        {"critical", "error", "warning"},
        id="verbosity-1",
    ),
    pytest.param(
        2,
        {"critical", "error", "warning", "success", "info"},
        id="verbosity-2",
    ),
    pytest.param(
        3,
        {
            "critical",
            "error",
            "warning",
            "success",
            "info",
            "debug",
            "trace",
        },
        id="verbosity-3",
    ),
]


_LEVEL_MESSAGES = {
    "critical": "LEVEL_TEST_CRITICAL",
    "error": "LEVEL_TEST_ERROR",
    "warning": "LEVEL_TEST_WARNING",
    "success": "LEVEL_TEST_SUCCESS",
    "info": "LEVEL_TEST_INFO",
    "debug": "LEVEL_TEST_DEBUG",
    "trace": "LEVEL_TEST_TRACE",
}

# --- _emit_all_levels() -------------------------------------------------------
def _emit_all_levels(log: Duo) -> None:
    log.critical("LEVEL_TEST_CRITICAL")
    log.error("LEVEL_TEST_ERROR")
    log.warning("LEVEL_TEST_WARNING")
    log.success("LEVEL_TEST_SUCCESS")
    log.info("LEVEL_TEST_INFO")
    log.debug("LEVEL_TEST_DEBUG")
    log.trace("LEVEL_TEST_TRACE")


# --- read_file() --------------------------------------------------------------
def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- find_main_log() -------------------------------------------------------
def _find_main_log(tmp_path: Path) -> Path:
    files = [f for f in tmp_path.rglob("*.log") if "new_logger" not in f.name]
    assert files, "Main log file not found"
    return files[0]


# --- find_file() --------------------------------------------------------------
def _find_file(tmp_path: Path, file_name: str) -> Path:
    files = list(tmp_path.rglob(file_name))
    assert files, f"No file found with file_name = {file_name}"
    return files[0]


# --- _find_new_logger_log() ---------------------------------------------------
def _find_new_logger_log(
    tmp_path: Path,
    sink_name: str,
) -> Path:
    files = list(tmp_path.rglob(f"{sink_name}*.log"))
    assert files, f"New_logger log file not found: {sink_name}"
    return files[0]


# --- _make_run_dir() ----------------------------------------------------------
def _make_run_dir(
    tmp_path: Path,
    name: str,
) -> Path:

    run_dir = tmp_path / name
    run_dir.mkdir(parents=True)

    (run_dir / ".logduo_marker").write_text("marker")

    return run_dir


# --- _new_test_log() ----------------------------------------------------------
def _new_test_log(tmp_path):
    from logduo import Duo

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
    )
    return log
