"""
test_new_level.py

"""
import pytest

from logduo import Duo
from logduo.internals.engine.new_level import _create_custom_level_label


# --- test_01_create_custom_level_label() --------------------------------------
def test_01_create_custom_level_label(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    _create_custom_level_label(
        log,
        "NOTE",
        console_style="purple",
        level="INFO",
    )

    assert log._runtime.new_levels["note"] == (
        "NOTE",
        "purple",
        "INFO",
    )


# --- test_02_reserved_label_raises() ------------------------------------------
def test_02_reserved_label_raises(tmp_path):

    log = Duo()

    log.configure(log_dir_path=str(tmp_path))

    with pytest.raises(ValueError):

        _create_custom_level_label(
            log,
            "INFO",
            console_style="blue",
            level="INFO",
        )

# --- test_03_invalid_level_raises() -------------------------------------------
def test_03_invalid_level_raises(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    with pytest.raises(ValueError):
        _create_custom_level_label(
            log,
            "NOTE",
            console_style="blue",
            level="BOGUS",
        )


# --- test_04_invalid_color_raises() -------------------------------------------
def test_04_invalid_color_raises(tmp_path):

    log = Duo()

    log.configure(log_dir_path=str(tmp_path))

    with pytest.raises(ValueError):

        _create_custom_level_label(
            log,
            "NOTE",
            console_style="not_a_real_color",
            level="INFO",
        )



# --- test_05_duplicate_label_raises() -----------------------------------------
def test_05_duplicate_label_raises(tmp_path):
    log = Duo()

    log.configure(log_dir_path=str(tmp_path))

    _create_custom_level_label(
        log,
        "NOTE",
        console_style="blue",
        level="INFO",
    )

    with pytest.raises(ValueError):

        _create_custom_level_label(
            log,
            "NOTE",
            console_style="red",
            level="WARNING",
        )


# --- test_06_label_truncation_warning() ---------------------------------------
def test_06_label_truncation_warning(tmp_path, capsys):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    _create_custom_level_label(
        log,
        "THIS_LABEL_IS_WAY_TOO_LONG",
        console_style="blue",
        level="INFO",
    )

    captured = capsys.readouterr()

    assert "truncated" in captured.out.lower()

