"""
test_runtime_warn.py

Tests:
- runtime_warning.py
- show_env_table.py

Last edited: 2026-06-08
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from rich.console import Console

from logduo import Duo
from logduo.internals.engine.runtime_warning import _runtime_warning


# --- test_01_runtime_warning_dedup() -----------------------------------------
def test_01_runtime_warning_dedup(tmp_path):

    log = Duo()
    log.configure(log_dir_path=tmp_path, console_verbosity=0)

    _runtime_warning(
        log,
        warn_msg="duplicate test",
    )

    _runtime_warning(
        log,
        warn_msg="duplicate test",
    )

    assert len(log._runtime.unique_warning_set) == 1

    log.close()


# --- test_02_runtime_warning_extra_does_not_affect_dedup() -------------------
def test_02_runtime_warning_extra_does_not_affect_dedup(tmp_path):

    log = Duo()
    log.configure(log_dir_path=tmp_path, console_verbosity=0)

    _runtime_warning(
        log,
        warn_msg="same warning",
        extra="A",
    )

    _runtime_warning(
        log,
        warn_msg="same warning",
        extra="B",
    )

    assert len(log._runtime.unique_warning_set) == 1

    log.close()


# --- test_03_runtime_warning_visible_when_console_verbosity_zero() ----------
def test_03_runtime_warning_visible_when_console_verbosity_zero(
    tmp_path,
    capsys,
):
    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        console_verbosity=0,
    )
    _runtime_warning(
        log,
        warn_msg="test warning",
    )

    captured = capsys.readouterr()
    assert "LOGDUO WARNING:" in captured.out
    assert "test warning" in captured.out


# --- test_04_runtime_warning_console_fallback() ------------------------------
def test_04_runtime_warning_console_fallback():

    log = Duo()

    log._initialized = False
    log._console = Console()

    with patch(
            "logduo.internals.formatters.safe_console_print._safe_console_print"
    ) as mock_print:

        _runtime_warning(
            log,
            warn_msg="console fallback",
        )

        mock_print.assert_called_once()


# --- test_05_runtime_warning_dispatches_to_level_entry() ---------------------
def test_05_runtime_warning_dispatches_to_level_entry(tmp_path):

    log = Duo()
    log.configure(log_dir_path=tmp_path, console_verbosity=0)

    with patch(
        "logduo.internals.engine.level_entry._level_entry"
    ) as mock_level:

        _runtime_warning(
            log,
            warn_msg="dispatch test",
            warn_key="abc",
        )

        mock_level.assert_called_once()

        kwargs = mock_level.call_args.kwargs

        assert kwargs["level"] == "WARNING"
        assert kwargs["event_type"] == "system_warning"
        assert kwargs["warn_key"] == "abc"

    log.close()



# --- test_06_runtime_warning_shown_during_config_even_if_console_off() ----------
def test_06_runtime_warning_shown_during_config_even_if_console_off(
    tmp_path,
    capsys,
):
    log = Duo()

    log.configure(
        log_file_path=str(tmp_path / "my.log"),
        log_dir_path=str(tmp_path / "other_dir"),
        console_verbosity=0,
        log_verbosity=0,
    )

    output = capsys.readouterr().out

    assert (
        "log_file_path overrides conflicting log_dir_path"
        in output
    )


# --- test_07_runtime_warning_rejects_multiline_message() ----------
def test_07_runtime_warning_rejects_multiline_message(tmp_path):
    log = Duo()
    log.configure(log_dir_path=tmp_path)


    with pytest.raises(RuntimeError) as exc:
        _runtime_warning(
            log,
            warn_msg="line1\nline2",
        )

    assert "Runtime warnings must emit single (inline) messages" in str(exc.value)
