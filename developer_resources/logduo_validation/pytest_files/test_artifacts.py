"""
test_artifacts.py

"""
from pathlib import Path

from logduo import Duo
from logduo.internals.artifacts.build_config_table import (
    _build_session_config_class_instance_table_rows,
    _get_toml_display_value,
)
from logduo.internals.artifacts.export_logduo_docs import _write_example_scripts, _write_readme_txt
from logduo.internals.artifacts.write_session_artifacts import _make_json_safe
from logduo.internals.session_config.session_config_spec import SESSION_CONFIG_SPEC


# --- test_01_session_artifacts_written() --------------------------------------
def test_01_session_artifacts_written(tmp_path):

    log = Duo()


    log.configure(
        log_dir_path=tmp_path,
        write_config_table=True,
        write_config_json=True,
    )

    out_dir = log.output_dir_path


    assert (out_dir / "config_table.txt").exists()
    assert (out_dir / "config.json").exists()
    log.close()


# --- test_02_make_json_safe_path() --------------------------------------------
def test_make_json_safe_path():

    result = _make_json_safe(
        {"a": Path("/tmp/test.txt")}
    )

    assert result["a"] == "/tmp/test.txt"


# --- test_03_get_toml_display_value_not_found() -------------------------------
def test_03_get_toml_display_value_not_found():
    result = _get_toml_display_value(
        {"has_pyproject": False,
        }
    )

    assert result == "not found"


# --- test_04_get_toml_display_value_no_tool_table() ---------------------------
def test_04_get_toml_display_value_no_tool_table():
    result = _get_toml_display_value(
        {
            "has_pyproject": True,
            "has_tool_table": False,
        }

    )

    assert result == "no [tool.logduo] table"


# --- test_05_build_session_config_class_instance_table_rows() -----------------
def test_05_build_session_config_class_instance_table_rows(tmp_path):

    log = Duo()

    log.configure(log_dir_path=tmp_path)

    rows = _build_session_config_class_instance_table_rows(
        session_config=log.session_config,
        arg_source_dict=log._arg_source_record.arg_source_dict,
        session_config_spec=SESSION_CONFIG_SPEC,

    )

    assert len(rows) > 0

    first_row = rows[0]

    assert "field" in first_row
    assert "value" in first_row
    assert "arg_source" in first_row

    assert any(
        row["field"] == "console_verbosity"
        for row in rows
    )


# --- test_06_write_example_scripts_creates_examples_dir() ------------------------
def test_06_write_example_scripts_creates_examples_dir(
    tmp_path: Path,
) -> None:

    logduo_dir_path = tmp_path / "logduo_docs"

    _write_example_scripts(logduo_dir_path=logduo_dir_path)

    assert (logduo_dir_path / "examples").is_dir()


# --- test_07_write_example_scripts_copies_examples() -----------------------------
def test_07_write_example_scripts_copies_examples(
    tmp_path: Path,
) -> None:
    logduo_dir_path = tmp_path / "logduo_docs"

    _write_example_scripts(
        logduo_dir_path=logduo_dir_path,
    )

    examples_dir = logduo_dir_path / "examples"

    source_examples_dir = (
        Path(__file__).parents[3]
        / "src"
        / "logduo"
        / "internals"
        / "artifacts"
        / "logduo_docs"
        / "example_scripts"
    )

    expected_file_names = sorted(
        path.name
        for path in source_examples_dir.glob("*.py")
    )

    assert expected_file_names

    for file_name in expected_file_names:
        assert (examples_dir / file_name).exists()


# --- test_08_write_example_scripts_preserves_existing_file() ---------------------
def test_08_write_example_scripts_preserves_existing_file(
    tmp_path: Path,
) -> None:

    logduo_dir_path = tmp_path / "logduo_docs"
    examples_dir = logduo_dir_path / "examples"

    examples_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    target_file = examples_dir / "first_script.py"

    target_file.write_text(
        "user modified",
        encoding="utf-8",
    )

    _write_example_scripts(
        logduo_dir_path=logduo_dir_path,
    )

    assert (
        target_file.read_text(encoding="utf-8")
        == "user modified"
    )


# --- test_09_write_readme_txt_preserves_existing_file() -----------------------
def test_09_write_readme_txt_preserves_existing_file(
    tmp_path: Path,
) -> None:

    log = Duo()
    log.configure(log_dir_path=tmp_path)

    logduo_dir_path = tmp_path / "logduo_docs"
    logduo_dir_path.mkdir()

    readme_file_path = logduo_dir_path / "README.md"

    readme_file_path.write_text(
        "user modified",
        encoding="utf-8",
    )

    _write_readme_txt(
        runtime=log._runtime,
        logduo_dir_path=logduo_dir_path,
    )

    assert (
        readme_file_path.read_text(encoding="utf-8")
        == "user modified"
    )

# --- test_10_write_readme_txt_contains_generated_timestamp() ------------------
def test_10_write_readme_txt_contains_generated_timestamp(

    tmp_path: Path,

) -> None:

    log = Duo()
    log.configure(log_dir_path=tmp_path)

    logduo_dir_path = tmp_path / "logduo_docs"
    logduo_dir_path.mkdir()

    _write_readme_txt(runtime=log._runtime, logduo_dir_path=logduo_dir_path)

    text = (logduo_dir_path / "README.txt").read_text(encoding="utf-8")

    assert "Generated on:" in text


# --- test_11_export_logduo_docs_creates_expected_structure() -------------------
def test_11_export_logduo_docs_creates_expected_structure(
    tmp_path: Path,
) -> None:

    log = Duo()
    log.configure(log_dir_path=tmp_path)

    log.export_logduo_docs()

    docs_dir = (log._runtime.project_dir_path_abs / "logduo_docs")


    print(" ")
    print("***********************************")
    print("test_11_export_logduo_docs_creates_expected_structure")
    print("docs_dir")
    print(docs_dir)

    assert docs_dir.is_dir()
    assert (docs_dir / "README.txt").exists()
    assert (docs_dir / "examples").is_dir()
    assert (docs_dir / "examples" / "first_script.py").exists()


# --- test_12_export_logduo_docs_is_idempotent() --------------------------------
def test_12_export_logduo_docs_is_idempotent(
    tmp_path: Path,
) -> None:

    log = Duo()
    log.configure(log_dir_path=tmp_path)

    log.export_logduo_docs()
    log.export_logduo_docs()


# --- test_13_write_example_scripts_preserves_existing_example() ---------------
def test_13_write_example_scripts_preserves_existing_example(
    tmp_path: Path,
) -> None:

    logduo_dir_path = tmp_path / "logduo_docs"
    examples_dir = (logduo_dir_path / "examples")
    examples_dir.mkdir(parents=True, exist_ok=True)

    target_file = (examples_dir / "first_script.py")
    target_file.write_text("user modified", encoding="utf-8")

    _write_example_scripts(logduo_dir_path=logduo_dir_path)

    assert (target_file.read_text(encoding="utf-8") == "user modified")


# --- test_14_export_logduo_docs_custom_path() ----------------------------------
def test_14_export_logduo_docs_custom_path(
    tmp_path: Path,
) -> None:

    log = Duo()
    log.configure(log_dir_path=tmp_path / "logs")

    custom_docs_path = (tmp_path / "my_docs")
    log.export_logduo_docs(path=custom_docs_path)

    assert custom_docs_path.is_dir()
    assert (custom_docs_path / "README.txt").exists()
    assert (custom_docs_path / "examples" / "first_script.py").exists()


# --- test_15_export_logduo_docs_custom_path_not_default() ----------------------
def test_15_export_logduo_docs_custom_path_not_default(
    tmp_path: Path,
) -> None:

    log = Duo()
    log.configure(log_dir_path=tmp_path / "logs")

    custom_docs_path = (tmp_path / "my_docs")
    log.export_logduo_docs(path=custom_docs_path)

    default_docs_path = (tmp_path / "logduo_docs")

    print()
    print("*******************************")
    print("test_15_export_logduo_docs_custom_path_not_default")
    print("log._runtime.project_dir_path_abs")
    print(log._runtime.project_dir_path_abs)
    print("tmp_path")
    print(tmp_path)

    assert custom_docs_path.exists()
    assert not default_docs_path.exists()




