"""
test_initialize.py

"""
import pytest

from developer_resources.pytest_toolkit.test_utils import _new_test_log
from logduo import Duo
import logduo.internals.engine.start_session as start_session



# --- test_01_configure_initializes() ------------------------------------------
def test_01_configure_initializes(tmp_path):
    log = _new_test_log(tmp_path)
    assert log._initialized is True
    assert log.session_config is not None


# --- test_02_warn_if_configure_after_explicit_configuration -----------------------------------------
def test_02_warn_if_configure_after_explicit_configuration(tmp_path, capsys):
    log = _new_test_log(tmp_path)
    log.configure()
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "log.configure() called more than once." in output
    print("************************")
    print("test_02_warn_if_configure_after_explicit_configuration")
    print("warning after second configure attempt:")
    print(captured)



# ---  test_03_explicit_configuration_not_auto() -------------------------------
def test_03_explicit_configuration_not_auto(tmp_path):
    log = _new_test_log(tmp_path)
    assert log._auto_configured is False


# --- test_04_session_running_after_init() -------------------------------------
def test_04_session_running_after_init(tmp_path):
    log = _new_test_log(tmp_path)
    assert log._runtime.session_state == "running"


# ---  test_05_run_layout_creates_marker_file(tmp_path) -----------------------
def test_05_run_layout_creates_marker_file(tmp_path):
    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="run",
    )
    marker = next(tmp_path.rglob(".logduo_marker"))
    assert marker.exists()


# --- test_06_script_layout_no_marker(tmp_path) --------------------------------
def test_06_script_layout_no_marker(tmp_path):
    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )
    marker_files = list(tmp_path.rglob(".logduo_marker"))
    assert marker_files == []



# --- test_07_initialize_session_idempotent() ----------------------------------
def test_07_initialize_session_idempotent(tmp_path):
    log = _new_test_log(tmp_path)
    config_before = log.session_config
    result = log._initialize_session()
    assert result is config_before


# --- test_08_failure_setting_up_sinks_resets_session() ------------------------
def boom(*args, **kwargs):     # noqa  intentional error
    raise RuntimeError("boom")

def test_08_failure_setting_up_sinks_resets_session(tmp_path, monkeypatch):
    log = Duo()
    monkeypatch.setattr(
        start_session,
        "_setup_sinks",
        boom,
    )
    with pytest.raises(RuntimeError):
        log.configure(log_dir_path=str(tmp_path),)

    assert log._initialized is False
    assert log._runtime.session_state != "running"
    assert log.session_config == log._startup_config
