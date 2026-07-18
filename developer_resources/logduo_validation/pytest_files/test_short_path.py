"""
test_short_path.py

Tests simplified short_path() behavior.

Last edited: 2026-06-04
"""

from pathlib import Path

import pytest

from logduo.utils.short_path.short_path import short_path, short_path_list

_DEBUG_TEST_PRINT = True


# --- test_01_width_too_small() ------------------------------------------------
def test_01_width_too_small():

    path = (
        "/Users/example/project/src/module/"
        "very_long_filename.py"
    )
    width = 10
    caught = "no exception"

    try:
        short_path(path, width=width)
    except ValueError:
        caught = "ValueError"
    except Exception as exc:
        caught = type(exc).__name__

    if _DEBUG_TEST_PRINT:
        print("Showing print results from inside test:")

    _print_test_details(
        test_name="test_01_width_too_small",
        assertion="raises ValueError",
        expected="ValueError",
        actual=caught,
        path=path,
        result="",
        width=width,
        anchor_dir=None,
    )

    with pytest.raises(ValueError):
        short_path(path, width=width)


# --- test_02_long_filename_is_shortened ---------------------------------------
def test_02_long_filename_is_shortened():

    path = (
        "/Users/example/project/src/module/"
        "extremely_long_filename_that_needs_shortening.py"
    )
    width = 20
    print(f"len of '…' = {len('…')}")
    result = short_path(path, width=width)

    _print_test_details(
        test_name="test_02_long_filename_is_shortened",
        assertion="len(result) == 20",
        expected=20,
        actual=len(result),
        path=path,
        result=result,
        width=width,
        anchor_dir=None,
    )

    assert len(result) == 20
    assert result.endswith(".py")
    assert "…" in result


# --- tet_03_adds_parent_when_room_exists_no_anchor() --------------------------
def test_03_adds_parent_when_room_exists_no_anchor():

    path = (
        "/Users/example/project/src/module/file.py"
    )
    width = 30
    result = short_path(path, width=width)

    _print_test_details(
        test_name="test_03_adds_parent_when_room_exists_no_anchor",
        assertion="result= '/project/src/module/file.py'",
        expected='/project/src/module/file.py',
        actual=result,
        path=path,
        result=result,
        width=width,
        anchor_dir=None,
    )

    assert result == "/project/src/module/file.py"


# --- test_04_adds_multiple_parents_when_room_exists_no_anchor() ---------------
def test_04_adds_multiple_parents_when_room_exists_no_anchor():
    path = (
        Path.cwd()
        / "Users"
        / "example"
        / "project"
        / "src"
        / "module"
        / "file.py"
    )

    width = 200
    result = short_path(path, width=width)
    _print_test_details(
        test_name="test_04_adds_multiple_parents_when_room_exists_no_anchor",
        assertion="result == str(path)",
        expected=str(path),
        actual=result,
        path=path,
        result=result,
        width=width,
        anchor_dir=None,
    )

    assert result == str(path)


# --- test_05_stops_at_anchor() ------------------------------------------------
def test_05_stops_at_anchor(tmp_path: Path):

    anchor = tmp_path / "project"
    anchor.mkdir()

    path = anchor / "src" / "module" / "file.py"
    path.parent.mkdir(parents=True)
    path.touch()
    width = 100

    result = short_path(
        path,
        width=width,
        anchor_dir=anchor,
    )

    _print_test_details(
        test_name="test_05_stops_at_anchor",
        assertion="result= '/project/src/module/file.py'",
        expected='/project/src/module/file.py',
        actual=result,
        path=path,
        result=result,
        width=width,
        anchor_dir=None,
    )


    assert result == "/project/src/module/file.py"


# --- test_06_outside_anchor_uses_normal_path() --------------------------------
def test_06_outside_anchor_uses_normal_path(tmp_path: Path):

    anchor = tmp_path / "project"
    anchor.mkdir()

    path = tmp_path / "other" / "file.py"
    path.parent.mkdir()
    path.touch()
    width = 100

    result = short_path(
        path,
        width=width,
        anchor_dir=anchor,
    )

    _print_test_details(
        test_name="test_06_outside_anchor_uses_normal_path",
        assertion="'project' not in result",
        expected=True,
        actual=('project' not in result),
        path=path,
        result=result,
        width=width,
        anchor_dir=None,
    )

    assert "project" not in result


# --- test_07_when_long_filename_exceeds_width_no_anchor -----------------------
@pytest.mark.parametrize("width", [20, 30, 40, 50, 80])
def test_07_when_long_filename_exceeds_width_no_anchor(width: int):

    path = (
        "/Users/example/project/really_long_directory_name/"
        "submodule/another_long_dir/"
        "extremely_long_filename_that_should_be_shortened.txt"
    )

    result = short_path(path, width=width)

    _print_test_details(
        test_name="test_07_when_long_filename_exceeds_width_no_anchor",
        assertion="len(result) <= width",
        expected=True,
        actual=(len(result) <= width),
        path=path,
        result=result,
        width=width,
        anchor_dir=None,
    )

    assert len(result) <= width


# --- test_08_preserves_multi_part_extensions_no_anchor ------------------------
def test_08_preserves_multi_part_extensions_no_anchor():

    path = (
        "/Users/example/archive/"
        "file.with.lots.of.exts.tar.gz"
    )
    width = 25

    result = short_path(path, width=width)

    _print_test_details(
        test_name="test_08_preserves_multi_part_extensions_no_anchor",
        assertion="result.endswith('.with.lots.of.exts.tar.gz')",
        expected=True,
        actual=(result.endswith(".with.lots.of.exts.tar.gz")),
        path=path,
        result=result,
        width=width,
        anchor_dir=None,
    )


    assert result.endswith(".with.lots.of.exts.tar.gz")


# --- test_09_short_path_list_count() ------------------------------------------
def test_09_short_path_list_count(tmp_path: Path):

    paths = [
        tmp_path / "a.py",
        tmp_path / "b.py",
        tmp_path / "c.py",
    ]

    for p in paths:
        p.touch()

    rows = short_path_list(paths)

    if len(rows) == 3:
        test_outcome = "PASS"
    else:
        test_outcome = "FAIL"

    print(" ")
    print("test_09_short_path_list_count")
    print(f"test outcome: {test_outcome}")
    print("assertion: len(rows) == 3")
    print(f"actual: len(rows) == {len(rows)}")
    for idx, (long_path, short_path_value) in enumerate(rows, start=1):
        print(f"{idx}.")
        print(f"long_path  : {long_path}")
        print(f"short_path : {short_path_value}")
        print()


    assert len(rows) == 3


# --- test_10_windows_path() ---------------------------------------------------
def test_10_windows_path():
    path = "C:\project\src\module\file.py"
    width = 80

    result = short_path(path, width=width)

    _print_test_details(
        test_name="test_10_windows_path",
        assertion="result= 'C:\project\src\module\file.py'",
        expected='C:\project\src\module\file.py',
        actual=result,
        path=path,
        result=result,
        width=width,
        anchor_dir=None,
    )

    assert result == "C:\project\src\module\file.py"


# --- test_11_max_parents_limits_path_depth() ----------------------------------
def test_11_max_parents_limits_path_depth():

    path = "/Users/example/project/src/module/file.py"

    result = short_path(
        path,
        width=80,
        max_parents=2,
    )

    _print_test_details(
        test_name="test_11_max_parents_limits_path_depth",
        assertion="result == '/src/module/file.py'",
        expected="/src/module/file.py",
        actual=result,
        path=path,
        result=result,
        width=80,
        anchor_dir=None,
    )

    assert result == "/src/module/file.py"


# --- test_12_anchor_stops_before_max_parents() --------------------------------
def test_12_anchor_stops_before_max_parents(tmp_path: Path):

    anchor = tmp_path / "project"
    anchor.mkdir()

    path = anchor / "src" / "module" / "file.py"
    path.parent.mkdir(parents=True)
    path.touch()

    result = short_path(
        path,
        width=100,
        anchor_dir=anchor,
        max_parents=20,
    )

    _print_test_details(
        test_name="test_12_anchor_stops_before_max_parents",
        assertion="result == '/project/src/module/file.py'",
        expected="/project/src/module/file.py",
        actual=result,
        path=path,
        result=result,
        width=100,
        anchor_dir=anchor,
    )

    assert result == "/project/src/module/file.py"


# --- test_13_max_parents_stops_before_anchor() --------------------------------
def test_13_max_parents_stops_before_anchor(tmp_path: Path):

    anchor = tmp_path / "project"
    anchor.mkdir()

    path = anchor / "src" / "module" / "file.py"
    path.parent.mkdir(parents=True)
    path.touch()

    result = short_path(
        path,
        width=100,
        anchor_dir=anchor,
        max_parents=1,
    )

    _print_test_details(
        test_name="test_13_max_parents_stops_before_anchor",
        assertion="result == '/module/file.py'",
        expected="/module/file.py",
        actual=result,
        path=path,
        result=result,
        width=100,
        anchor_dir=anchor,
    )

    assert result == "/module/file.py"


# --- test_14_max_parents_zero_returns_filename_only ---------------------------
def test_14_max_parents_zero_returns_filename_only():
    path = "/Users/example/project/src/module/file.py"
    anchor = "/Users/example/project"
    result = short_path(
        path,
        width=80,
        max_parents=0,
    )

    _print_test_details(
        test_name="test_14_max_parents_zero_returns_filename_only",
        assertion="result == 'file.py'",
        expected="file.py",
        actual=result,
        path=path,
        result=result,
        width=100,
        anchor_dir=anchor,
    )

    assert result == "file.py"


# === Internal helper ==========================================================
def _print_test_details(
    *,
    test_name: str,
    assertion: str,
    expected: object,
    actual: object,
    path: str | Path,
    result: str,
    width: int,
    anchor_dir: str | Path | None = None,
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


    print(f"    path        : {path}")
    print("    args:")
    print(f"    width       : {width}")
    print(f"    anchor_dir  : {anchor_dir}")
    print("")
    print(f"    result      : {result}")
    print(f"    result_len  : {len(result)}")
    print(" ")

