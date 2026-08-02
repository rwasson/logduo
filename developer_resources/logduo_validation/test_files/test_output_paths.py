"""
test_output_paths.py

Integration test_files for output directory and log path derivation.

Last edited: 2026-06-16
"""

from pathlib import Path

import pytest

from logduo import Duo


# --- test_01_flat_layout_default_path() -----------------------------------------
def test_01_flat_layout_default_path(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="flat",
        write_config_table=False,
    )

    assert log.output_dir_path == tmp_path
    assert log._runtime.main_sink_log_dir_path_abs == tmp_path


# --- test_02_script_layout_default_path() ---------------------------------------
def test_02_script_layout_default_path(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        write_config_table=False,
    )

    expected_dir = tmp_path / "session"

    print(" ")
    print("*********************************")
    print("test_02_script_layout_default_path")
    print('expected_dir: = tmp_path / "session"')
    print(expected_dir)
    print('log.output_dir_path:')
    print(log.output_dir_path)
    assert log.output_dir_path == expected_dir
    assert log._runtime.main_sink_log_dir_path_abs == expected_dir


# --- test_03_timestamped_file_mode_adds_timestamp() -----------------------------
def test_03_timestamped_file_mode_adds_timestamp(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="flat",
        log_file_name="audit.log",
        log_file_mode="timestamped",
        write_config_table=False,
    )

    file_path = log._runtime.main_sink_log_file_path_abs

    assert file_path is not None
    assert file_path.name.startswith("audit_")
    assert file_path.suffix == ".log"


# --- test_04_log_file_path_overrides_layout() -----------------------------------
def test_04_log_file_path_overrides_layout(tmp_path: Path):

    explicit_path = tmp_path / "custom.log"

    log = Duo()

    log.configure(
        log_file_path=str(explicit_path),
        log_file_layout="script",   # should be ignored
        write_config_table=False,
    )

    assert log.output_dir_path == tmp_path
    assert log._runtime.main_sink_log_file_path_abs == explicit_path


# --- test_05_log_verbosity_zero_creates_no_main_log() ---------------------------
def test_05_log_verbosity_zero_creates_no_main_log(tmp_path: Path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_verbosity=0,
        write_config_table=False,
    )

    log.info("hello")

    file_path = log._runtime.main_sink_log_file_path_abs

    assert file_path is not None
    assert not file_path.exists()


# --- test_06_output_dir_path_is_read_only() -----------------------------------
def test_06_output_dir_path_is_read_only(tmp_path: Path) -> None:
    log = Duo()

    log.configure(log_dir_path=str(tmp_path),)

    with pytest.raises(AttributeError):
        log.output_dir_path = Path("/other/path")    # noqa  # intentional error


# --- test_07_main_log_file_path_is_read_only() -----------------------------------
def test_07_main_log_file_path_is_read_only(tmp_path: Path) -> None:
    log = Duo()

    log.configure(log_dir_path=str(tmp_path), )

    with pytest.raises(AttributeError):
        log.main_log_file_path = Path("/other/path")  # noqa  # intentional error

