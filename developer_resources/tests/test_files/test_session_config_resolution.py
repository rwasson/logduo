"""
test_session_config_resolution.py

Last edited: 2026-06-10
"""
from pathlib import Path

import pytest

from logduo import Duo
from logduo.internals.session_config.configure_args_normalizer import _load_toml_args, \
    _normalize_args_from_one_source
from logduo.internals.session_config.session_config_classes import (
    ArgSourceRecord,
    SessionConfig,
    _build_session_config_class_instance,
)
from logduo.internals.session_config.session_config_resolver import (
    _resolve_header_footer_value,
    _resolve_path_conflicts,
    _apply_session_config_policies,
    _derive_console_theme_dict,
)
from logduo.internals.session_config.session_config_spec import (
    DEFAULTS,
    SESSION_CONFIG_SPEC,
    _session_config_hints,
)


# --- duo ---------------------------------------------------------------------
@pytest.fixture
def duo():
    return Duo()

# --- test_01_configure_overrides_toml() ---------------------------------------
def test_01_configure_overrides_toml():

    config = dict(DEFAULTS)

    config["log_verbosity"] = 1
    config["log_verbosity"] = 3

    assert config["log_verbosity"] == 3


# --- test_02_log_file_path_forces_flat_layout() -------------------------------
def test_02_log_file_path_forces_flat_layout(duo):

    arg_source_record = ArgSourceRecord()

    config = dict(DEFAULTS)
    config["log_file_path"] = "/tmp/test.log"
    config["log_dir_layout"] = "run"

    resolved = _resolve_path_conflicts(
        duo,
        normalized_session_config=config,
        arg_source_record=arg_source_record,
    )

    assert resolved["log_dir_layout"] == "flat"
    assert arg_source_record.arg_source_dict["log_dir_layout"] == "forced"


# --- test_03_log_file_path_overrides_log_dir_path() ---------------------------
def test_03_log_file_path_overrides_log_dir_path(duo):

    arg_source_record = ArgSourceRecord()

    config = dict(DEFAULTS)
    config["log_file_path"] = "/tmp/a/test.log"
    config["log_dir_path"] = "/tmp/b"

    _resolve_path_conflicts(
        duo,
        normalized_session_config=config,
        arg_source_record=arg_source_record,
    )

    assert arg_source_record.arg_source_dict["log_dir_path"] == "forced"


# --- test_04_log_file_path_overrides_log_file_name() --------------------------
def test_04_log_file_path_overrides_log_file_name(duo):

    arg_source_record = ArgSourceRecord()

    config = dict(DEFAULTS)
    config["log_file_path"] = "/tmp/test.log"
    config["log_file_name"] = "other.log"

    _resolve_path_conflicts(
        duo,
        normalized_session_config=config,
        arg_source_record=arg_source_record,
    )

    assert arg_source_record.arg_source_dict["log_file_name"] == "forced"


# --- test_05_console_theme_override_merges() ----------------------------------
def test_05_console_theme_override_merges():

    result = _derive_console_theme_dict(
        theme="dark",
        console_theme_dict={
            "warning": "red",
        },
        dark_console_theme_dict={
            "warning": "yellow",
            "info": "green",
        },
        light_console_theme_dict={},
    )

    assert result["warning"] == "red"
    assert result["info"] == "green"


# --- test_06_header_footer_off_normalized() -----------------------------------
def test_06_header_footer_off_normalized():

    result = _resolve_header_footer_value(
        arg_name="log_header",
        value="OFF",
    )

    assert result == "off"


# --- test_07_header_footer_custom_preserved() ---------------------------------
def test_07_header_footer_custom_preserved():

    result = _resolve_header_footer_value(
        arg_name="log_header",
        value="My Header",
    )

    assert result == "My Header"


# --- test_08_header_footer_empty_rejected() -----------------------------------
def test_08_header_footer_empty_rejected():

    with pytest.raises(ValueError):

        _resolve_header_footer_value(
            arg_name="log_header",
            value="   ",
        )


# --- test_09_header_footer_non_string_rejected() ------------------------------
def test_09_header_footer_non_string_rejected():

    with pytest.raises(ValueError):

        _resolve_header_footer_value(
            arg_name="log_header",
            value=123,
        )


# --- test_10_rotation_off_becomes_none() --------------------------------------
def test_10_rotation_off_becomes_none(duo):

    arg_source_record = ArgSourceRecord()

    config = dict(DEFAULTS)
    config["rotation"] = "off"

    resolved = _apply_session_config_policies(
        duo,
        normalized_session_config=config,
        arg_source_record=arg_source_record,
    )

    assert resolved["rotation"] is None


# --- test_11_retention_off_becomes_none() -------------------------------------
def test_11_retention_off_becomes_none(duo):

    arg_source_record = ArgSourceRecord()

    config = dict(DEFAULTS)
    config["retention"] = "off"

    resolved = _apply_session_config_policies(
        duo,
        normalized_session_config=config,
        arg_source_record=arg_source_record,
    )

    assert resolved["retention"] is None


# --- test_12_compression_off_becomes_none() -----------------------------------
def test_12_compression_off_becomes_none(duo):

    arg_source_record = ArgSourceRecord()

    config = dict(DEFAULTS)
    config["compression"] = "off"

    resolved = _apply_session_config_policies(
        duo,
        normalized_session_config=config,
        arg_source_record=arg_source_record,
    )

    assert resolved["compression"] is None


# --- test_13_build_session_config_instance() ----------------------------------
def test_13_build_session_config_instance():

    config = dict(DEFAULTS)

    result = _build_session_config_class_instance(config)

    assert isinstance(result, SessionConfig)
    assert result.log_verbosity == DEFAULTS["log_verbosity"]


# --- test_14_extra_keys_ignored() ---------------------------------------------
def test_14_extra_keys_ignored():

    config = dict(DEFAULTS)

    config["future_field"] = "future"

    result = _build_session_config_class_instance(config)

    assert isinstance(result, SessionConfig)
    assert not hasattr(result, "future_field")


# --- test_15_arg_source_record_defaults() -------------------------------------
def test_15_arg_source_record_defaults():

    record = ArgSourceRecord()

    assert record.arg_source_dict == {}
    assert record.toml_record == {}


# --- test_16_session_config_hints_returns_text() ------------------------------
def test_16_session_config_hints_returns_text():

    hint = _session_config_hints(
        "log_dir_layout",
        DEFAULTS,
    )

    assert isinstance(hint, str)
    assert "flat" in hint


# --- test_17_session_config_spec_contains_required_sections() -----------------
def test_17_session_config_spec_contains_required_sections():

    assert "schema" in SESSION_CONFIG_SPEC
    assert "defaults" in SESSION_CONFIG_SPEC
    assert "grouping" in SESSION_CONFIG_SPEC
    assert "descriptions" in SESSION_CONFIG_SPEC


# --- test_18__session_config_hints_returns_string() ---------------------------
@pytest.mark.parametrize(
    "field",
    [
        "log_file_mode",
        "log_file_path",
        "log_dir_layout",
        "keep",
        "console_wrap_width",
        "rotation",
        "retention",
        "compression",
        "enqueue",
    ]
)
def test_18_session_config_hints_returns_string(field):

    result = _session_config_hints(
        field,
        DEFAULTS,
    )

    assert isinstance(result, str)
    assert result




# --- test_19_session_config_hints_unknown_field() -----------------------------
def test_19_session_config_hints_unknown_field():

    result = _session_config_hints(
        "banana",
        DEFAULTS,
    )

    assert result == "invalid value"


# --- test_20_session_config_hints_bool_field() --------------------------------
def test_20_session_config_hints_bool_field():

    result = _session_config_hints(
        "enqueue",
        DEFAULTS,
    )

    assert isinstance(result, str)
    assert result


# --- test_21_session_config_hints_compression() -------------------------------
def test_21_session_config_hints_compression():

    result = _session_config_hints(
        "compression",
        DEFAULTS,
    )

    assert "zip" in result




# --- test_22_load_toml_args_no_file() -----------------------------------------
def test_22_load_toml_args_no_file():

    args, record = _load_toml_args(
        toml_path_abs=None,
        project_name="logduo",
        schema={},
    )

    assert args == {}
    assert record["has_pyproject"] is False


# --- test_23_load_toml_args_no_tool_table() -----------------------------------
def test_23_load_toml_args_no_tool_table(tmp_path: Path):

    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text(
        """
        [project]
        name = "demo"
        """
    )

    args, record = _load_toml_args(
        toml_path_abs=toml_path,
        project_name="logduo",
        schema={},
    )

    assert args == {}
    assert record["has_pyproject"] is True
    assert record["has_tool_table"] is False


# --- test_24_load_toml_args_unknown_key() ---------------------------------------
def test_24_load_toml_args_unknown_key(tmp_path: Path):

    toml_path = tmp_path / "pyproject.toml"

    toml_path.write_text(
        """
        [tool.logduo]
        banana = 123
        """
            )

    with pytest.raises(RuntimeError):

        _load_toml_args(
            toml_path_abs=toml_path,
            project_name="logduo",
            schema={},
        )


# --- test_25_normalize_args_invalid_source() ----------------------------------
def test_25_normalize_args_invalid_source():

    with pytest.raises(RuntimeError):

        _normalize_args_from_one_source(
            source_label="Test",
            source_name="test",
            source={
                "console_wrap_width": 999,
            },
            schema=SESSION_CONFIG_SPEC["schema"],
            schema_defaults=DEFAULTS,
            session_config_hints=_session_config_hints,
        )


