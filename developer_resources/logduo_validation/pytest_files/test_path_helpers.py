"""
test_path_helpers.py

pytest_files modules: path_finders, path_validators, callsite_utils,

Last edited: 2026-06-08
"""
import sys
from pathlib import Path

import pytest

from logduo.internals.filesystem.callsite_utils import (
    _shorten_callsite_for_prefix,
    _shorten_middle_with_ellipsis,
    _trim_stack_lines,
)
from logduo.internals.filesystem.path_finders import (
    _apply_timestamp_to_filename,
    _derive_session_log_paths,
    _get_script_path_abs,
    _get_toml_path_abs,
    _normalize_path_candidate,
)
from logduo.internals.filesystem.path_validators import (
    _is_abs_dir_path_writable,
    _raise_if_invalid_config_arg_log_dir_path,
    _raise_if_invalid_config_arg_log_file_name,
    _raise_if_invalid_config_arg_log_file_path,
    _raise_if_invalid_session_config_path_fields,
)


# --- test_01_apply_timestamp_to_filename() ------------------------------------
def test_01_apply_timestamp_to_filename():
    result = _apply_timestamp_to_filename(
        filename="audit.log",
        session_timestamp="2026_06_08__14_00_00",
    )

    assert result == "audit_2026_06_08__14_00_00.log"


# --- test_02_trim_stack_lines_elides_middle() ---------------------------------
def test_02_trim_stack_lines_elides_middle():
    lines = [f"{i}\n" for i in range(10)]

    result = _trim_stack_lines(
        lines,
        head=2,
        tail=2,
    )

    assert result[0] == "0\n"
    assert result[1] == "1\n"

    assert "... (elided) ..." in result[2]

    assert result[-2] == "8\n"
    assert result[-1] == "9\n"


# --- test_03_shorten_middle_with_ellipsis() -----------------------------------
def test_03_shorten_middle_with_ellipsis():
    result = _shorten_middle_with_ellipsis(
        "abcdefghijklmnopqrstuvwxyz",    # noqa
        10,
    )

    assert len(result) == 10
    assert "..." in result



# --- test_04_shorten_callsite_for_prefix() --------------------------------------
def test_04_shorten_callsite_for_prefix():
    result = _shorten_callsite_for_prefix(
        "very_long_filename.py",
        123,
        max_chars=10,

    )

    assert result.endswith(":123")


# --- test_05_input_file_returns_blank() ---------------------------------------
def test_05_input_file_returns_blank():
    result = _shorten_callsite_for_prefix(
        "<input>",
        1,
    )

    assert result == ""



# --- test_06_normalize_path_candidate() ---------------------------------------
def test_06_normalize_path_candidate(tmp_path: Path):
    f = tmp_path / "sample.py"
    f.write_text("print('hi')")

    result = _normalize_path_candidate(f)

    assert result == f.resolve()



# --- test_7_get_toml_path_abs() ----------------------------------------------
def test_7_get_toml_path_abs(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()

    pyproject = root / "pyproject.toml"
    pyproject.write_text("[project]")

    nested = root / "a" / "b"
    nested.mkdir(parents=True)

    toml_path, warn_msg = _get_toml_path_abs(
        cwd_path_abs=nested,
    )

    assert warn_msg is None
    assert toml_path == pyproject.resolve()


# --- test_08_shorten_middle_no_change() ---------------------------------------
def test_08_shorten_middle_no_change():
    result = _shorten_middle_with_ellipsis(
        "abc",
        10,
    )

    assert result == "abc"


# --- test_09_shorten_middle_tiny_limit() --------------------------------------
def test_09_shorten_middle_tiny_limit():
    result = _shorten_middle_with_ellipsis(
        "abcdef",
        2,
    )

    assert result == "ab"



# --- test_10_normalize_path_candidate_none() ----------------------------------
def test_10_normalize_path_candidate_none():
    result = _normalize_path_candidate(None)
    assert result is None


# --- test_11_normalize_path_candidate_not_py() --------------------------------
def test_11_normalize_path_candidate_not_py(tmp_path: Path):

    f = tmp_path / "sample.txt"
    f.write_text("hello")

    result = _normalize_path_candidate(f)

    assert result is None


# --- test_12_get_toml_path_abs_not_found() ------------------------------------
def test_12_get_toml_path_abs_not_found(tmp_path: Path):

    toml_path, warn_msg = _get_toml_path_abs(

        cwd_path_abs=tmp_path,

    )

    assert toml_path is None
    assert warn_msg is None


# --- test_13_derive_paths_run_layout() ----------------------------------------
def test_13_derive_paths_run_layout(tmp_path: Path):
    result = _derive_session_log_paths(
        project_dir_path_abs=tmp_path,
        session_name="myscript",
        log_file_layout="run",
        log_file_mode="write",
        session_timestamp="2026_06_08__12_00_00",
        log_file_path="auto",
        log_dir_path="auto",
        log_file_name="auto",
    )

    assert (
        result["main_sink_log_dir_path_abs"].name
        == "run_2026_06_08__12_00_00"
    )

    assert (
        result["main_sink_log_file_path_abs"].name
        == "myscript.log"
    )


# --- test_14_derive_paths_timestamped_filename() ------------------------------
def test_14_derive_paths_timestamped_filename(tmp_path: Path):
    result = _derive_session_log_paths(
        project_dir_path_abs=tmp_path,
        session_name="myscript",
        log_file_layout="script",
        log_file_mode="timestamped",
        session_timestamp="2026_06_08__12_00_00",
        log_file_path="auto",
        log_dir_path="auto",
        log_file_name="auto",
    )

    assert (
        result["main_sink_log_file_path_abs"].name
        == "myscript_2026_06_08__12_00_00.log"
    )


# --- test_15_derive_paths_explicit_file_path() --------------------------------
def test_15_derive_paths_explicit_file_path(tmp_path: Path):
    result = _derive_session_log_paths(
        project_dir_path_abs=tmp_path,
        session_name="myscript",
        log_file_layout="run",
        log_file_mode="write",
        session_timestamp="2026_06_08__12_00_00",
        log_file_path=str(tmp_path / "custom.log"),
        log_dir_path="auto",
        log_file_name="auto",
    )

    assert (
        result["main_sink_log_file_path_abs"].name
        == "custom.log"
    )

    assert (
        result["log_dir_path_abs"]
        == tmp_path.resolve()
    )


# --- test_16_derive_paths_explicit_file_path_timestamped() --------------------
def test_16_derive_paths_explicit_file_path_timestamped(tmp_path: Path):
    result = _derive_session_log_paths(
        project_dir_path_abs=tmp_path,
        session_name="myscript",
        log_file_layout="run",
        log_file_mode="timestamped",
        session_timestamp="2026_06_08__12_00_00",
        log_file_path=str(tmp_path / "custom.log"),
        log_dir_path="auto",
        log_file_name="auto",
    )

    assert (
        result["main_sink_log_file_path_abs"].name
        == "custom_2026_06_08__12_00_00.log"
    )

# --- test_17_derive_paths_invalid_timestamp() ---------------------------------
def test_17_derive_paths_invalid_timestamp(tmp_path: Path):

    with pytest.raises(ValueError):

        _derive_session_log_paths(
            project_dir_path_abs=tmp_path,
            session_name="myscript",
            log_file_layout="run",
            log_file_mode="write",
            session_timestamp="2026-06-08 12:00:00",
            log_file_path="auto",
            log_dir_path="auto",
            log_file_name="auto",
        )

# --- test_18_log_file_name_empty_raises() -------------------------------------
def test_18_log_file_name_empty_raises():
    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_file_name("")


# --- test_19_log_file_name_with_directory_component_raises() ------------------
def test_19_log_file_name_with_directory_component_raises():
    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_file_name("logs/test.log")


# --- test_20_log_file_name_dot_raises() ---------------------------------------
def test_20_log_file_name_dot_raises():
    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_file_name(".")


# --- test_21_log_file_name_valid() --------------------------------------------
def test_log_file_name_valid():
    result = _raise_if_invalid_config_arg_log_file_name("test.log")

    assert result == "test.log"


# --- test_22_session_config_path_fields_auto_passthrough() --------------------
def test_22_session_config_path_fields_auto_passthrough():

    cfg = {
        "log_file_path": "auto",
        "log_file_name": "auto",
        "log_dir_path": "auto",
    }

    result = _raise_if_invalid_session_config_path_fields(cfg)

    assert result["log_file_path"] == "auto"
    assert result["log_file_name"] == "auto"
    assert result["log_dir_path"] == "auto"


# --- test_23_session_config_path_fields_valid() -------------------------------
def test_23_session_config_path_fields_valid(tmp_path):

    cfg = {
        "log_file_path": str(tmp_path / "test.log"),
        "log_file_name": "test.log",
        "log_dir_path": str(tmp_path),
    }

    result = _raise_if_invalid_session_config_path_fields(cfg)

    assert result["log_file_name"] == "test.log"


# --- test_24_is_abs_dir_path_writable_existing_dir() --------------------------
def test_24_is_abs_dir_path_writable_existing_dir(tmp_path):

    assert _is_abs_dir_path_writable(tmp_path) is True



# --- test_25_is_abs_dir_path_writable_relative_path() -------------------------
def test_25_is_abs_dir_path_writable_relative_path():

    assert _is_abs_dir_path_writable("relative/path") is False


# --- test_26_is_abs_dir_path_writable_tilde_path() ----------------------------
def test_26_is_abs_dir_path_writable_tilde_path():

    assert _is_abs_dir_path_writable("~/logs") is False



# --- test_27_is_abs_dir_path_writable_existing_file() -------------------------
def test_27_is_abs_dir_path_writable_existing_file(tmp_path):

    file_path = tmp_path / "file.txt"
    file_path.write_text("x")

    assert _is_abs_dir_path_writable(file_path) is False


# --- test_28_is_abs_dir_path_writable_missing_parent_allowed() ----------------
def test_28_is_abs_dir_path_writable_missing_parent_allowed(tmp_path):

    path = tmp_path / "a" / "b" / "c"

    assert (
        _is_abs_dir_path_writable(
            path,
            allow_missing_parent=True,
        )
        is True
    )


# --- test_29_is_abs_dir_path_writable_missing_parent_not_allowed() ------------
def test_29_is_abs_dir_path_writable_missing_parent_not_allowed(tmp_path):

    path = tmp_path / "a" / "b" / "c"

    assert (
        _is_abs_dir_path_writable(
            path,
            allow_missing_parent=False,
        )
        is False
    )


# --- test_30_log_dir_path_empty_raises() -------------------------------------
def test_30_log_dir_path_empty_raises():

    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_dir_path("")


# --- test_31_log_dir_path_relative_raises() ----------------------------------
def test_31_log_dir_path_relative_raises():

    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_dir_path("logs")


# --- test_32_log_dir_path_valid() --------------------------------------------
def test_32_log_dir_path_valid(tmp_path):

    result = _raise_if_invalid_config_arg_log_dir_path(tmp_path)

    assert result == str(tmp_path.resolve())


# --- test_33_log_file_path_empty_raises() ------------------------------------
def test_33_log_file_path_empty_raises():

    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_file_path("")


# --- test_34_log_file_path_relative_raises() ---------------------------------
def test_34_log_file_path_relative_raises():

    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_file_path("audit.log")



# --- test_35_log_file_path_valid() -------------------------------------------
def test_35_log_file_path_valid(tmp_path):

    path = tmp_path / "audit.log"

    result = _raise_if_invalid_config_arg_log_file_path(path)

    assert result == str(path.resolve())


# --- test_36_is_abs_dir_path_writable_with_reasons() -------------------------
def test_36_is_abs_dir_path_writable_with_reasons(tmp_path):

    ok, reasons = _is_abs_dir_path_writable(
        tmp_path,
        with_reasons=True,
    )

    assert ok is True
    assert reasons == []


# --- test_37_is_abs_dir_path_writable_existing_not_allowed() -----------------
def test_37_is_abs_dir_path_writable_existing_not_allowed(tmp_path):

    ok, reasons = _is_abs_dir_path_writable(
        tmp_path,
        allow_existing=False,
        with_reasons=True,
    )

    assert ok is False
    assert reasons


# --- test_38_log_file_name_dotdot_raises() -----------------------------------
def test_38_log_file_name_dotdot_raises():

    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_file_name("..")


# --- test_39_normalize_path_candidate_bad_extension_main_py() ----------------
def test_39_normalize_path_candidate_main_py(tmp_path):

    f = tmp_path / "__main__.py"
    f.write_text("print('x')")

    assert _normalize_path_candidate(f) is None


# --- test_40_normalize_path_candidate_venv_path() ----------------------------
def test_40_normalize_path_candidate_venv_path(tmp_path):
    venv_dir = tmp_path / ".venv" / "lib"
    venv_dir.mkdir(parents=True)
    script = venv_dir / "script.py"
    script.write_text("x")

    assert _normalize_path_candidate(script) is None


# --- test_41_get_script_path_abs_no_main_file() ------------------------------
def test_41_get_script_path_abs_no_main_file(monkeypatch):


    monkeypatch.delattr(sys.modules["__main__"], "__file__", raising=False)

    path, source = _get_script_path_abs()

    assert path is None
    assert source is None


# --- test_42_get_toml_path_abs_unreadable() ----------------------------------
def test_42_get_toml_path_abs_unreadable(
    tmp_path,
    monkeypatch,
):

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]")

    original_open = Path.open

    def boom(self, *args, **kwargs):
        if self.name == "pyproject.toml":
            raise OSError("denied")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(
        Path,
        "open",
        boom,
    )

    toml_path, warn_msg = _get_toml_path_abs(
        cwd_path_abs=tmp_path,
    )

    assert toml_path is None
    assert "not readable" in warn_msg


# --- test_43_get_toml_path_abs_none_cwd() ------------------------------------
def test_43_get_toml_path_abs_none_cwd():

    toml_path, warn_msg = _get_toml_path_abs(
        cwd_path_abs=None,
    )

    assert toml_path is None
    assert warn_msg is None


# --- test_44_derive_paths_custom_file_name_without_suffix() ------------------
def test_44_derive_paths_custom_file_name_without_suffix(tmp_path):

    result = _derive_session_log_paths(
        project_dir_path_abs=tmp_path,
        session_name="myscript",
        log_file_layout="flat",
        log_file_mode="write",
        session_timestamp="2026_06_08__12_00_00",
        log_file_path="auto",
        log_dir_path="auto",
        log_file_name="audit",
    )

    assert (
        result["main_sink_log_file_path_abs"].name
        == "audit.log"
    )


# --- test_45_derive_paths_custom_dir_path() ----------------------------------
def test_45_derive_paths_custom_dir_path(tmp_path):

    custom_dir = tmp_path / "custom_logs"

    result = _derive_session_log_paths(
        project_dir_path_abs=tmp_path,
        session_name="myscript",
        log_file_layout="flat",
        log_file_mode="write",
        session_timestamp="2026_06_08__12_00_00",
        log_file_path="auto",
        log_dir_path=str(custom_dir),
        log_file_name="auto",
    )

    assert result["log_dir_path_abs"] == custom_dir.resolve()


# --- test_46_log_file_path_invalid_filename() -------------------------------
def test_46_log_file_path_invalid_filename():

    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_file_path(
            "/tmp/bad:name.log"
        )


# --- test_46b_log_file_path_invalid_windows_filename() -------------------------------
@pytest.mark.parametrize(
    "name",
    [
        "bad:name.log",
        "bad*name.log",
        "bad?name.log",
        "bad|name.log",
        'bad"name.log',
        "bad<name.log",
        "bad>name.log",
    ],
)
def test_log_file_name_windows_invalid_chars(name):
    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_file_name(name)


# --- test_47_log_file_path_dot_segment() -------------------------------------
def test_47_log_file_path_dot_segment():

    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_file_path(
            "/tmp/."
        )

# --- test_49_is_abs_dir_path_writable_with_reasons_relative() ----------------
def test_49_is_abs_dir_path_writable_with_reasons_relative():

    ok, reasons = _is_abs_dir_path_writable(
        "relative/path",
        with_reasons=True,
    )

    assert ok is False
    assert reasons


# --- test_50_session_config_path_fields_invalid_file_name() ------------------
def test_50_session_config_path_fields_invalid_file_name():

    cfg = {
        "log_file_path": "auto",
        "log_file_name": "bad/name.log",
        "log_dir_path": "auto",
    }

    with pytest.raises(ValueError):
        _raise_if_invalid_session_config_path_fields(cfg)


# --- test_51_existing_ancestor_not_directory() --------------------------------
def test_51_existing_ancestor_not_directory(tmp_path):

    file_parent = tmp_path / "not_a_dir"
    file_parent.write_text("x")

    path = file_parent / "a" / "b"

    ok, reasons = _is_abs_dir_path_writable(
        path,
        allow_missing_parent=True,
        with_reasons=True,
    )

    assert ok is False
    assert reasons


# --- test_52_probe_ancestor_creation_failure() --------------------------------
def test_52_probe_ancestor_creation_failure(
    tmp_path,
    monkeypatch,
):

    import tempfile

    def boom(*args, **kwargs):
        raise OSError("forced")

    monkeypatch.setattr(
        tempfile,
        "TemporaryDirectory",
        boom,
    )

    path = tmp_path / "a" / "b"

    ok, reasons = _is_abs_dir_path_writable(
        path,
        allow_missing_parent=True,
        with_reasons=True,
    )

    assert ok is False
    assert reasons


# --- test_53_existing_directory_not_writable() --------------------------------
def test_53_existing_directory_not_writable(
    tmp_path,
    monkeypatch,
):

    import tempfile

    def boom(*args, **kwargs):
        raise OSError("forced")

    monkeypatch.setattr(
        tempfile,
        "NamedTemporaryFile",
        boom,
    )

    ok, reasons = _is_abs_dir_path_writable(
        tmp_path,
        with_reasons=True,
    )

    assert ok is False
    assert reasons

# --- test_54_log_dir_path_invalid_type_raises() -------------------------------
def test_54_log_dir_path_invalid_type_raises():

    with pytest.raises(
        ValueError,
        match="must be an absolute path",
    ):
        _raise_if_invalid_config_arg_log_dir_path(
            123,  # type: ignore[arg-type]
        )

# --- test_55_log_file_path_invalid_type_raises() ------------------------------
def test_55_log_file_path_invalid_type_raises():

    with pytest.raises(
        ValueError,
        match="must be an absolute path",
    ):
        _raise_if_invalid_config_arg_log_file_path(
            123,  # type: ignore[arg-type]
        )


# --- test_56_missing_directory_with_existing_parent_is_writable() -------------
def test_56_missing_directory_with_existing_parent_is_writable(
    tmp_path: Path,
):

    candidate = tmp_path / "new_directory"

    ok, reasons = _is_abs_dir_path_writable(
        candidate,
        allow_missing_parent=False,
        with_reasons=True,
    )

    assert ok is True
    assert reasons == []
    assert not candidate.exists()


# --- test_57_missing_directory_existing_parent_not_writable() -----------------
def test_57_missing_directory_existing_parent_not_writable(
    tmp_path: Path,
    monkeypatch,
):

    import tempfile

    candidate = tmp_path / "new_directory"

    def fail_temporary_directory(*args, **kwargs):  # noqa
        raise OSError("simulated parent write failure")

    monkeypatch.setattr(
        tempfile,
        "TemporaryDirectory",
        fail_temporary_directory,
    )

    ok, reasons = _is_abs_dir_path_writable(
        candidate,
        allow_missing_parent=False,
        with_reasons=True,
    )

    assert ok is False
    assert "Cannot create in parent directory" in reasons[0]["reason"]
