"""
test_new_level.py

"""
import pytest

from developer_resources.logduo_validation.pytest_files.pytest_helpers.file_helpers import _find_main_log, _read_file
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


# --- test_07_new_level_returns_none_and_registers_level() ---------------------
def test_07_new_level_returns_none_and_registers_level(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        console_verbosity=0,
    )

    log.new_level(
        "TIP",
        console_style="purple",
    )


    assert log._runtime.new_levels["tip"] == (
        "TIP",
        "purple",
        "INFO",
    )
    assert callable(log.tip)


# --- test_08_new_level_without_style_registers_none() -------------------------
def test_08_new_level_without_style_registers_none(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        console_verbosity=0,
    )

    log.new_level("NOTE")

    assert log._runtime.new_levels["note"] == (
        "NOTE",
        None,
        "INFO",
    )
    assert callable(log.note)


# --- test_09_new_level_with_style_console_and_log_output() -------------------
def test_09_new_level_with_style_console_and_log_output(
    tmp_path,
    monkeypatch,
    capsys,
):

    # Force Rich styling while pytest captures console output.
    monkeypatch.setenv("PYCHARM_HOSTED", "1")

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        log_file_layout="script",
        console_verbosity=2,
        log_verbosity=2,
        console_prefix="level",
        log_prefix="level",
        console_header="off",
        console_footer="off",
        log_header="off",
        log_footer="off",
    )

    log.new_level(
        "TIP",
        console_style="purple",
    )


    assert log._runtime.new_levels["tip"] == (
        "TIP",
        "purple",
        "INFO",
    )
    assert callable(log.tip)  # Is this true TODO check

    log.tip("styled tip message")


    captured = capsys.readouterr()
    console_output = captured.out + captured.err
    log_text = _read_file(_find_main_log(tmp_path))

    print()
    print("************************************************")
    print("test_09_new_level_with_style_console_and_log_output")
    print("console output:")
    print(console_output)
    print()
    print("console output repr:")
    print(repr(console_output))
    print()
    print("log output:")
    print(log_text)
    print("************************************************")
    log.close()

    assert "TIP" in console_output
    assert "styled tip message" in console_output

    assert "TIP" in log_text
    assert "styled tip message" in log_text

    # The custom Rich style is present in terminal output.
    assert "\x1b[" in console_output

    # Console styling must not leak into the plain-text log.
    assert "\x1b[" not in log_text
    assert "purple" not in log_text




# --- test_10_new_level_without_style_console_and_log_output() ----------------
def test_10_new_level_without_style_console_and_log_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    # bold Level style if no console_style given

    monkeypatch.setenv("PYCHARM_HOSTED", "1")

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        log_file_layout="script",
        console_verbosity=2,
        log_verbosity=2,
        console_prefix="level",
        log_prefix="level",
        console_header="off",
        console_footer="off",
        log_header="off",
        log_footer="off",
    )

    log.new_level("NOTE")

    assert log._runtime.new_levels["note"] == (
        "NOTE",
        None,
        "INFO",
    )
    assert callable(log.note)

    log.note("unstyled note message")


    captured = capsys.readouterr()
    console_output = captured.out + captured.err
    log_text = _read_file(_find_main_log(tmp_path))

    print()
    print("************************************************")
    print("test_10_new_level_without_style_console_and_log_output")
    print("console output:")
    print(console_output)
    print()
    print("console output repr:")
    print(repr(console_output))
    print()
    print("log output:")
    print(log_text)
    print("************************************************")


    assert "NOTE" in console_output
    assert "\x1b[1mNOTE" in console_output
    assert "unstyled note message" in console_output

    assert "NOTE" in log_text
    assert "unstyled note message" in log_text

    # No custom style was assigned to NOTE.
    assert log._runtime.new_levels["note"][1] is None


    # ANSI styling must never leak into the log.
    assert "\x1b[" not in log_text
    log.close()
