"""
test_session_config_resolution.py

Last edited: 2026-06-10
"""
from pathlib import Path

import pytest

from logduo import Duo
from logduo.internals.session_config.configure_args_normalizer import (
    _load_toml_args,
    _normalize_args_from_one_source,
    _normalize_configure_args_with_defaults_and_toml,
)
from logduo.internals.session_config.session_config_classes import (
    _build_session_config_class_instance,
    ArgSourceRecord,
    SessionConfig,
)
from logduo.internals.session_config.session_config_resolver import (
    _apply_session_config_policies,
    _derive_console_theme_dict,
    _resolve_header_footer_value,
    _resolve_path_conflicts,
)
from logduo.internals.session_config.session_config_spec import (
    _session_config_hints,
    DEFAULTS,
    SESSION_CONFIG_SPEC,
)


# --- duo ---------------------------------------------------------------------
@pytest.fixture
def duo():
    return Duo()


# --- test_01_configure_overrides_toml() --------------------------------------
def test_01_configure_overrides_toml(tmp_path: Path):

    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text(
        """
        [tool.logduo]
        log_verbosity = 1
        console_wrap_width = 100
        """,
        encoding="utf-8",
    )

    resolved, source_record, toml_record = (
        _normalize_configure_args_with_defaults_and_toml(
            toml_path_abs=toml_path,
            configure_args={
                "log_verbosity": 3,
            },
            session_config_spec=SESSION_CONFIG_SPEC,
            session_config_hints=_session_config_hints,
        )
    )

    assert resolved["log_verbosity"] == 3
    assert resolved["console_wrap_width"] == 100

    assert source_record["log_verbosity"] == "configure"
    assert source_record["console_wrap_width"] == "toml"

    assert toml_record["toml_args_used"] is True


# --- test_02_log_file_path_forces_flat_layout() -------------------------------
def test_02_log_file_path_forces_flat_layout(duo):

    arg_source_record = ArgSourceRecord()

    config = dict(DEFAULTS)
    config["log_file_path"] = "/tmp/test.log"
    config["log_file_layout"] = "run"

    resolved = _resolve_path_conflicts(
        duo,
        normalized_session_config=config,
        arg_source_record=arg_source_record,
    )

    assert resolved["log_file_layout"] == "flat"
    assert arg_source_record.arg_source_dict["log_file_layout"] == "forced"


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
        "log_file_layout",
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
        "log_file_layout",
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


# --- test_26_load_toml_args_valid_table() ------------------------------------
def test_26_load_toml_args_valid_table(tmp_path: Path):

    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text(
        """
        [tool.logduo]
        log_verbosity = 3
        console_color = false
        """,
        encoding="utf-8",
    )

    args, record = _load_toml_args(
        toml_path_abs=toml_path,
        project_name="logduo",
        schema=SESSION_CONFIG_SPEC["schema"],
    )

    assert args == {
        "log_verbosity": 3,
        "console_color": False,
    }

    assert record["has_pyproject"] is True
    assert record["has_tool_table"] is True
    assert record["toml_keys"] == [
        "console_color",
        "log_verbosity",
    ]


# --- test_27_load_toml_args_invalid_syntax() ---------------------------------
def test_27_load_toml_args_invalid_syntax(tmp_path: Path):

    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text(
        """
        [tool.logduo
        log_verbosity = 3
        """,
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="pyproject.toml syntax error"):
        _load_toml_args(
            toml_path_abs=toml_path,
            project_name="logduo",
            schema=SESSION_CONFIG_SPEC["schema"],
        )


# --- test_28_load_toml_args_tool_entry_must_be_table() -----------------------
def test_28_load_toml_args_tool_entry_must_be_table(tmp_path: Path):

    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text(
        """
        [tool]
        logduo = "invalid"
        """,
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match=r"\[tool\.logduo\] must be a TOML table",
    ):
        _load_toml_args(
            toml_path_abs=toml_path,
            project_name="logduo",
            schema=SESSION_CONFIG_SPEC["schema"],
        )

# --- test_29_console_light_theme_selected() ----------------------------------
def test_29_console_light_theme_selected():

    result = _derive_console_theme_dict(
        theme="light",
        console_theme_dict=None,
        dark_console_theme_dict={
            "info": "dark-info",
        },
        light_console_theme_dict={
            "info": "light-info",
            "warning": "light-warning",
        },
    )

    assert result == {
        "info": "light-info",
        "warning": "light-warning",
    }


# --- test_30_console_theme_invalid_overrides_ignored() -----------------------
def test_30_console_theme_invalid_overrides_ignored():

    result = _derive_console_theme_dict(
        theme="dark",
        console_theme_dict={
            "warning": "bold red",
            123: "invalid key",
            "info": 456,
        },
        dark_console_theme_dict={
            "warning": "yellow",
            "info": "green",
        },
        light_console_theme_dict={},
    )

    assert result["warning"] == "bold red"
    assert result["info"] == "green"
    assert 123 not in result

# --- test_31_header_footer_auto_normalized() ---------------------------------
def test_31_header_footer_auto_normalized():

    assert (
        _resolve_header_footer_value(
            arg_name="log_header",
            value=" AUTO ",
        )
        == "auto"
    )

    assert (
        _resolve_header_footer_value(
            arg_name="console_footer",
            value=" auto ",
        )
        == "auto"
    )


# --- test_32_matching_log_paths_not_marked_forced() --------------------------
def test_32_matching_log_paths_not_marked_forced(duo):

    arg_source_record = ArgSourceRecord()

    config = dict(DEFAULTS)
    config["log_file_path"] = "/tmp/logs/session.log"
    config["log_file_layout"] = "flat"
    config["log_dir_path"] = "/tmp/logs"
    config["log_file_name"] = "session.log"

    resolved = _resolve_path_conflicts(
        duo,
        normalized_session_config=config,
        arg_source_record=arg_source_record,
    )

    assert resolved["log_file_layout"] == "flat"

    assert "log_file_layout" not in arg_source_record.arg_source_dict
    assert "log_dir_path" not in arg_source_record.arg_source_dict
    assert "log_file_name" not in arg_source_record.arg_source_dict


# --- test_33_configure_rejects_explicit_auto() -------------------------------
def test_33_configure_rejects_explicit_auto(duo):

    with pytest.raises(
        ValueError,
        match="auto.*reserved for internal use",
    ):
        duo.configure(
            log_dir_path="auto",
        )


# --- test_34_session_config_hints_specific_fields() --------------------------
@pytest.mark.parametrize(
    ("field", "expected_text"),
    [
        ("log_file_name", "valid file name"),
        ("log_dir_path", "absolute path"),
        ("console_verbosity", "0 (off)"),
        ("console_prefix", "timestamp"),
        ("console_header", "non-empty string"),
        ("console_footer", "non-empty string"),
        ("console_theme", "dark"),
        ("console_theme_dict", "dict"),
        ("log_verbosity", "0 (off)"),
        ("log_prefix", "timestamp"),
        ("log_wrap_width", "80"),
        ("log_header", "non-empty string"),
        ("log_footer", "non-empty string"),
        ("rotation", "integer"),
        ("retention", "duration string"),
    ],
)
def test_34_session_config_hints_specific_fields(
    field: str,
    expected_text: str,
):
    result = _session_config_hints(
        field,
        DEFAULTS,
    )

    assert expected_text in result

# --- test_35_session_config_hints_boolean_fields() ---------------------------
@pytest.mark.parametrize(
    "field",
    [
        "console_color",
        "show_debug_source",
        "show_logger_name",
        "show_pid_in_console",
        "show_pid_in_log",
        "write_config_table",
        "write_config_json",
        "write_jsonl",
        "first_instance_owns_console",
        "enqueue",
        "catch",
        "backtrace",
        "diagnose",
    ],
)
def test_35_session_config_hints_boolean_fields(field: str):

    result = _session_config_hints(
        field,
        DEFAULTS,
    )

    assert isinstance(result, str)
    assert result
    assert "True" in result or "False" in result
