"""
test_run.py

Tests run().

Last edited: 2026-06-22
"""

from pathlib import Path

import pytest

from logduo import run

_DEBUG_TEST_PRINT = True


# --- test_01_invalid_type() ---------------------------------------------------
def test_01_invalid_type():

    caught = "no exception"

    try:
        run(123)    # noqa intentional error
    except ValueError:
        caught = "ValueError"
    except Exception as exc:
        caught = type(exc).__name__

    _print_test_details(
        test_name="test_01_invalid_type",
        assertion="raises ValueError",
        expected="ValueError",
        actual=caught,
    )

    with pytest.raises(ValueError):
        run(123)     # noqa  intentional error


# --- test_02_relative_path_rejected() -----------------------------------------
def test_02_relative_path_rejected():

    caught = "no exception"

    try:
        run(Path("example.py"))
    except ValueError:
        caught = "ValueError"
    except Exception as exc:
        caught = type(exc).__name__

    _print_test_details(
        test_name="test_02_relative_path_rejected",
        assertion="raises ValueError",
        expected="ValueError",
        actual=caught,
    )

    with pytest.raises(ValueError):
        run(Path("example.py"))


# --- test_03_missing_file() ---------------------------------------------------
def test_03_missing_file(tmp_path: Path):

    missing_file = tmp_path / "missing.py"

    caught = "no exception"

    try:
        run(missing_file)
    except ValueError:
        caught = "ValueError"
    except Exception as exc:
        caught = type(exc).__name__

    _print_test_details(
        test_name="test_03_missing_file",
        assertion="raises ValueError",
        expected="ValueError",
        actual=caught,
    )

    with pytest.raises(ValueError):
        run(missing_file)


# --- test_04_non_python_file_rejected() ---------------------------------------
def test_04_non_python_file_rejected(tmp_path: Path):

    file = tmp_path / "data.txt"
    file.touch()

    caught = "no exception"

    try:
        run(file)
    except ValueError:
        caught = "ValueError"
    except Exception as exc:
        caught = type(exc).__name__

    _print_test_details(
        test_name="test_04_non_python_file_rejected",
        assertion="raises ValueError",
        expected="ValueError",
        actual=caught,
    )

    with pytest.raises(ValueError):
        run(file)


# --- test_05_path_execution() -------------------------------------------------
def test_05_path_execution(tmp_path: Path):

    script = tmp_path / "example.py"

    script.write_text(
        "value = 123\n",
        encoding="utf-8",
    )

    module = run(script.resolve())

    _print_test_details(
        test_name="test_05_path_execution",
        assertion="module.value == 123",
        expected=123,
        actual=module.value,
    )

    assert module.value == 123


# --- test_06_path_rerun_uses_fresh_execution() --------------------------------
def test_06_path_rerun_uses_fresh_execution(tmp_path: Path):

    script = tmp_path / "example.py"

    script.write_text(
        "x = 1\n"
        "y = 2\n",
        encoding="utf-8",
    )

    module = run(script.resolve())

    script.write_text(
        "x = 10\n",
        encoding="utf-8",
    )

    module = run(script.resolve())

    _print_test_details(
        test_name="test_06_path_rerun_uses_fresh_execution",
        assertion="hasattr(module, 'y') is False",
        expected=False,
        actual=hasattr(module, "y"),
    )

    assert module.x == 10
    assert not hasattr(module, "y")


# --- test_07_module_not_found() -----------------------------------------------
def test_07_module_not_found():

    caught = "no exception"

    try:
        run("module_that_should_not_exist_123456")
    except ValueError:
        caught = "ValueError"
    except Exception as exc:
        caught = type(exc).__name__

    _print_test_details(
        test_name="test_07_module_not_found",
        assertion="raises ValueError",
        expected="ValueError",
        actual=caught,
    )

    with pytest.raises(ValueError):
        run("module_that_should_not_exist_123456")


# --- test_08_run_empty_string_raises() ----------------------------------------
def test_08_run_empty_string_raises():

    with pytest.raises(ValueError):

        run("")


# --- test_09_run_imports_existing_module() ------------------------------------
def test_09_run_imports_existing_module():

    module = run("json")

    assert module.__name__ == "json"


# --- test_10_py_suffix_rejected() ---------------------------------------------

def test_10_py_suffix_rejected():

    with pytest.raises(ValueError):

        run("my_script.py")


# === Internal helper ==========================================================
def _print_test_details(
    *,
    test_name: str,
    assertion: str,
    expected: object,
    actual: object,
) -> None:

    if not _DEBUG_TEST_PRINT:
        return

    passed = (actual == expected)

    print(" ")
    print("********************************************************************************")
    print(test_name)
    print(f"test outcome: {'PASS' if passed else '*** FAIL ***'}")
    print(f"assertion   : {assertion}")
    print(f"expected    : {expected!r}")
    print(f"actual      : {actual!r}")
    print(" ")
