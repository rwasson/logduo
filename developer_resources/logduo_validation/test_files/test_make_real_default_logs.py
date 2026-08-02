"""
real_log_test.py

These test_files need to  create real output logs

This test file can be skipped most runs

Last edited: 2026-06-12
"""

from logduo import Duo


# --- test_01_auto_initialize_on_first_log_call() ------------------------------
def test_01_auto_initialize_on_first_log_call():
    log = Duo()
    assert log._initialized is False
    log("hello")
    assert log._initialized is True
    assert log.session_config is not None


# --- test_02_warn_if_configure_after_auto_configuration -----------------------------------------
def test_02_warn_if_configure_after_auto_configuration(capsys):
    log = Duo()
    log("hello")
    log.configure()
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "log.configure() called after a log level statement" in output
    print("************************")
    print("test_03a_warn_if_configure_after_auto_configuration")
    print("warning after second configure attempt:")
    print(captured)


# --- test_03_auto_configuration_sets_flag() ------------------------------------
def test_03_auto_configuration_sets_flag():
    log = Duo()
    log("hello")
    assert log._auto_configured is True


# --- test_04_ensure_initialized_auto_configures() ----------------------------
def test_04_ensure_initialized_auto_configures():
    log = Duo()

    log._ensure_initialized()
    print(f"02 {log.output_dir_path}")

    assert log.initialized is True
    assert log._auto_configured is True

