"""
test_arg_resolvers.py

"""
from pathlib import Path

import pytest

from logduo import Duo
from logduo.internals.api_arg_resolvers.api_arg_resolver_helpers import (
    _assert_no_none,
    _assert_no_not_given,
    _resolve_int_arg,
    _resolve_log_prefix,
    _resolve_new_logger_target_arg,
)
from logduo.internals.api_arg_resolvers.level_call_args_resolver import _resolve_level_call_args
from logduo.internals.api_arg_resolvers.new_logger_args_resolver import _resolve_new_logger_args
from logduo.internals.session_config.cerberus_utils import (
    _norm_bool,
    _norm_log_file_mode,
    _norm_path_to_string,
    _norm_theme,
)
from logduo.internals.session_config.session_constants import _NOT_GIVEN


class FakeSessionConfig:
    log_verbosity = 2
    log_file_mode = "append"
    log_prefix = "timestamp"
    log_wrap_width = 100
    show_pid_in_log = False

class FakeRuntime:
    main_sink_log_dir_path_abs = Path("/tmp")

class FakeDuo:
    _runtime = FakeRuntime()
    session_config = FakeSessionConfig()


fake_duo = FakeDuo()


# --- test_01_resolve_new_logger_target_dot() ----------------------------------
def test_01_resolve_new_logger_target_dot():

    with pytest.raises(ValueError):
        _resolve_new_logger_target_arg(
            duo=fake_duo,   # noqa, intentional error
            value=".",
        )

# --- test_02_resolve_new_logger_target_path_separator() -----------------------
def test_02_resolve_new_logger_target_path_separator():

    with pytest.raises(ValueError):
        _resolve_new_logger_target_arg(
            duo=fake_duo,     # noqa, intentional error
            value="foo/bar.log",
        )

# --- test_3_resolve_int_arg_allowed_values() ---------------------------------
def test_3_resolve_int_arg_allowed_values():

    assert (
        _resolve_int_arg(
            arg_name="x",
            value=2,
            allowed_values=[1, 2, 3],
        )
        == 2
    )

# --- test_4_resolve_int_arg_invalid_allowed_values() -------------------------
def test_4_resolve_int_arg_invalid_allowed_values():

    with pytest.raises(ValueError):
        _resolve_int_arg(
            arg_name="x",
            value=5,
            allowed_values=[1, 2, 3],
        )


# --- test_5_resolve_int_arg_bad_min_max()-------------------------------------
def test_5_resolve_int_arg_bad_min_max():

    with pytest.raises(RuntimeError):
        _resolve_int_arg(
            arg_name="x",
            value=5,
            min_value=10,
            max_value=1,
        )

# --- test_6_assert_no_not_given_nested() -------------------------------------
def test_6_assert_no_not_given_nested():

    with pytest.raises(RuntimeError):
        _assert_no_not_given(
            {
                "a": {
                    "b": _NOT_GIVEN,
                }
            }
        )


# --- test_7_assert_no_none_nested() ------------------------------------------
def test_7_assert_no_none_nested():

    with pytest.raises(RuntimeError):
        _assert_no_none(
            {
                "a": {
                    "b": None,
                }
            }
        )


# --- test_8_assert_no_none_allowed_field() -----------------------------------
def test_8_assert_no_none_allowed_field():

    _assert_no_none(
        {
            "rotation": None,
        },
        allowed_fields={"rotation"},
    )

# --- test_9_norm_theme() -----------------------------------------------------
def test_9_norm_theme():
    assert _norm_theme("Dark") == "dark"
    assert _norm_theme("d") == "dark"
    assert _norm_theme("LIGHT") == "light"


# --- test_10_norm_theme() -----------------------------------------------------
def test_10_norm_log_file_mode():
    assert _norm_log_file_mode("w") == "write"
    assert _norm_log_file_mode("a") == "append"
    assert _norm_log_file_mode("t") == "timestamped"


# --- test_11_assert_no_not_given_raises() -------------------------------------
def test_11_assert_no_not_given_raises():

    with pytest.raises(RuntimeError):

        _assert_no_not_given(
            {"x": _NOT_GIVEN}
        )

# --- test_12_norm_bool_string_values() ----------------------------------------
def test_12_norm_bool_string_values():

    assert _norm_bool("true") is True
    assert _norm_bool("false") is False


# --- test_13_norm_path_to_string_pathlib() --------------------------------------
def test_13_norm_path_to_string_pathlib(tmp_path: Path):

    result = _norm_path_to_string(tmp_path)

    assert isinstance(result, str)


# --- test_14_resolve_int_arg_min_boundary() ----------------------------------
def test_14_resolve_int_arg_min_boundary():

    assert (
        _resolve_int_arg(
            arg_name="x",
            value=10,
            min_value=10,
        )
        == 10
    )


# --- test_15_resolve_int_arg_max_boundary() ----------------------------------
def test_15_resolve_int_arg_max_boundary():

    assert (
        _resolve_int_arg(
            arg_name="x",
            value=10,
            max_value=10,
        )
        == 10
    )


# --- test_16_resolve_int_arg_below_min() -------------------------------------
def test_16_resolve_int_arg_below_min():

    with pytest.raises(ValueError):
        _resolve_int_arg(
            arg_name="x",
            value=9,
            min_value=10,
        )


# --- test_17_resolve_int_arg_above_max() -------------------------------------
def test_17_resolve_int_arg_above_max():

    with pytest.raises(ValueError):
        _resolve_int_arg(
            arg_name="x",
            value=11,
            max_value=10,
        )


# --- test_18_resolve_int_arg_rejects_bool() ----------------------------------
def test_18_resolve_int_arg_rejects_bool():

    with pytest.raises(ValueError):
        _resolve_int_arg(
            arg_name="x",
            value=True,
        )

# --- test_19_assert_no_not_given_list_nested() -------------------------------
def test_19_assert_no_not_given_list_nested():

    with pytest.raises(RuntimeError):
        _assert_no_not_given(
            [
                {"a": 1},
                _NOT_GIVEN,
            ]
        )

# --- test_20_assert_no_none_list_nested() ------------------------------------
def test_20_assert_no_none_list_nested():

    with pytest.raises(RuntimeError):
        _assert_no_none(
            [
                1,
                None,
            ]
        )

# --- test_21_resolve_new_logger_target_default_extension() -------------------
def test_21_resolve_new_logger_target_default_extension():

    result = _resolve_new_logger_target_arg(
        duo=fake_duo,
        value="audit",
    )

    assert result["base_file_name_with_ext"] == "audit.log"


# --- test_22_resolve_new_logger_target_lowercases_name() ---------------------
def test_22_resolve_new_logger_target_lowercases_name():

    result = _resolve_new_logger_target_arg(
        duo=fake_duo,
        value="Audit.LOG",
    )

    assert result["base_file_name_with_ext"] == "audit.log"


# --- test_23_resolve_new_logger_target_empty_string() ------------------------
def test_23_resolve_new_logger_target_empty_string():

    with pytest.raises(ValueError):
        _resolve_new_logger_target_arg(
            duo=fake_duo,
            value="   ",
        )

# --- test_24_norm_path_to_string_passthrough() -------------------------------
def test_24_norm_path_to_string_passthrough():

    assert _norm_path_to_string("/tmp/foo") == "/tmp/foo"


# --- test_25_norm_bool_case_insensitive() ------------------------------------
def test_25_norm_bool_case_insensitive():

    assert _norm_bool("TRUE") is True
    assert _norm_bool("False") is False


# --- test_26_resolve_new_logger_target_absolute_path() -----------------------
def test_26_resolve_new_logger_target_absolute_path(tmp_path: Path):

    path = tmp_path / "audit.log"

    result = _resolve_new_logger_target_arg(
        duo=fake_duo,
        value=path,
    )

    assert result["value_is_path"] is True
    assert result["file_path"] == path.resolve()
    assert result["base_file_name_with_ext"] == "audit.log"


# --- test_27_resolve_new_logger_target_directory_path() ----------------------
def test_27_resolve_new_logger_target_directory_path(tmp_path: Path):

    with pytest.raises(ValueError):
        _resolve_new_logger_target_arg(
            duo=fake_duo,
            value=tmp_path,
        )

# --- test_28_resolve_new_logger_target_auto() -------------------------------
def test_28_resolve_new_logger_target_auto():

    with pytest.raises(ValueError):
        _resolve_new_logger_target_arg(
            duo=fake_duo,
            value="auto",
        )


# --- test_29_resolve_new_logger_target_bad_type() ---------------------------
def test_29_resolve_new_logger_target_bad_type():

    with pytest.raises(ValueError):
        _resolve_new_logger_target_arg(
            duo=fake_duo,
            value=123,                         # noqa intentional
        )


# --- test_30_assert_no_not_given_tuple_ok() ---------------------------------
def test_30_assert_no_not_given_tuple_ok():

    _assert_no_not_given(
        (
            {"a": 1},
            [2, 3],
        )
    )


# --- test_31_assert_no_none_nested_allowed_field() --------------------------
def test_31_assert_no_none_nested_allowed_field():

    _assert_no_none(
        {
            "a": {
                "rotation": None,
            }
        },
        allowed_fields={"rotation"},
    )


# --- test_32_norm_theme_passthrough() ---------------------------------------
def test_32_norm_theme_passthrough():
    assert _norm_theme("custom_theme") == "custom_theme"



# --- test_33_resolve_log_prefix_rejects_time() -------------------------------
def test_33_resolve_log_prefix_rejects_time():
    class FakeSessionConfig3:
        log_prefix = "timestamp"

    class FakeDuo3:
        session_config = FakeSessionConfig3()

    with pytest.raises(ValueError):
        _resolve_log_prefix(
            duo=FakeDuo3(),
            log_prefix="time",
        )



# --- test_34_resolve_log_prefix_timestamp() ----------------------------------
def test_34_resolve_log_prefix_timestamp():
    class FakeSessionConfig2:
        log_prefix = "timestamp"

    class FakeDuo2:
        session_config = FakeSessionConfig2()

    assert (
        _resolve_log_prefix(
            duo=FakeDuo2(),
            log_prefix="timestamp",
        )
        == "timestamp"
    )


# --- test_35_console_prefix_off_resolves_no_prefix(tmp_path) -----------------
def test_35_console_prefix_off_resolves_no_prefix(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        console_prefix="off",
        log_dir_layout="script",
    )

    resolved = _resolve_level_call_args(
        duo=log,
        is_console_sink=True,
        sink_config=log.session_config,
        call_args={
            "no_prefix": _NOT_GIVEN,
            "log_wrap_width": _NOT_GIVEN,
            "console_style": _NOT_GIVEN,
        },
    )

    assert resolved["no_prefix"] is True


# --- test_36_console_prefix_off_behavior(tmp_path, capsys) -------------------
def test_36_console_prefix_off_behavior(tmp_path, capsys):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        console_prefix="off",
        log_dir_layout="script",
    )

    log("hello world")

    captured = capsys.readouterr()

    assert "| INFO |" not in captured.out
    assert "hello world" in captured.out