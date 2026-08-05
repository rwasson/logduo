"""
test_windows.py

Tests for Windows-specific filename and path behavior.

Filename policy tests run on every operating system by temporarily
simulating the Windows-specific validation branch.

Actual Windows path tests run only on Windows because pathlib.Path uses
the host operating system's path rules.

Last edited: 2026-08-05
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from logduo.internals.api_arg_resolvers import api_arg_resolver_helpers
from logduo.internals.filesystem.path_validators import (
    _raise_if_invalid_config_arg_log_dir_path,
    _raise_if_invalid_config_arg_log_file_name,
    _raise_if_invalid_config_arg_log_file_path,
)


WINDOWS_RESERVED_STEMS = [
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
]


# --- test_01_windows_reserved_stems_raise() ----------------------------------
@pytest.mark.parametrize(
    "stem",
    WINDOWS_RESERVED_STEMS,
)
def test_01_windows_reserved_stems_raise(
    stem: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_arg_resolver_helpers.os,
        "name",
        "nt",
    )

    with pytest.raises(
        ValueError,
        match="reserved on Windows",
    ):
        api_arg_resolver_helpers._validate_windows_filename_stem(
            stem
        )


# --- test_02_windows_reserved_stems_are_case_insensitive() -------------------
@pytest.mark.parametrize(
    "stem",
    [
        "CON",
        "PrN",
        "AuX",
        "NUL",
        "Com1",
        "cOm9",
        "Lpt1",
        "LpT9",
    ],
)
def test_02_windows_reserved_stems_are_case_insensitive(
    stem: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_arg_resolver_helpers.os,
        "name",
        "nt",
    )

    with pytest.raises(
        ValueError,
        match="reserved on Windows",
    ):
        api_arg_resolver_helpers._validate_windows_filename_stem(
            stem
        )


# --- test_03_similar_nonreserved_stems_are_allowed() -------------------------
@pytest.mark.parametrize(
    "stem",
    [
        "console",
        "printer",
        "auxiliary",
        "null",
        "computer1",
        "com0",
        "com10",
        "lpt0",
        "lpt10",
        "audit",
        "events",
        "unit_tests__test_calculator",
    ],
)
def test_03_similar_nonreserved_stems_are_allowed(
    stem: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_arg_resolver_helpers.os,
        "name",
        "nt",
    )

    api_arg_resolver_helpers._validate_windows_filename_stem(
        stem
    )


# --- test_04_windows_reserved_stems_allowed_on_non_windows() -----------------
@pytest.mark.parametrize(
    "stem",
    WINDOWS_RESERVED_STEMS,
)
def test_04_windows_reserved_stems_allowed_on_non_windows(
    stem: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_arg_resolver_helpers.os,
        "name",
        "posix",
    )

    api_arg_resolver_helpers._validate_windows_filename_stem(
        stem
    )


# --- test_05_windows_invalid_filename_characters_raise() ---------------------
@pytest.mark.parametrize(
    "filename",
    [
        "bad:name.log",
        "bad*name.log",
        "bad?name.log",
        "bad|name.log",
        'bad"name.log',
        "bad<name.log",
        "bad>name.log",
        "bad/name.log",
        r"bad\name.log",
    ],
)
def test_05_windows_invalid_filename_characters_raise(
    filename: str,
) -> None:
    with pytest.raises(ValueError):
        _raise_if_invalid_config_arg_log_file_name(
            filename
        )


# --- test_06_normal_log_file_names_are_allowed() -----------------------------
@pytest.mark.parametrize(
    "filename",
    [
        "audit.log",
        "unit_tests__test_calculator.log",
        "report_2026_08_05.log",
    ],
)
def test_06_normal_log_file_names_are_allowed(
    filename: str,
) -> None:
    result = _raise_if_invalid_config_arg_log_file_name(
        filename
    )

    assert result == filename


# --- Actual Windows path tests ------------------------------------------------
# pathlib.Path follows the host operating system. These tests therefore run
# only on Windows; monkeypatching os.name on macOS does not change Path parsing.

@pytest.mark.skipif(
    os.name != "nt",
    reason="Requires Windows pathlib semantics",
)
def test_07_windows_absolute_log_file_path_is_allowed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.log"

    result = _raise_if_invalid_config_arg_log_file_path(
        path
    )

    assert result == str(path.resolve())


@pytest.mark.skipif(
    os.name != "nt",
    reason="Requires Windows pathlib semantics",
)
def test_08_windows_absolute_log_dir_path_is_allowed(
    tmp_path: Path,
) -> None:
    result = _raise_if_invalid_config_arg_log_dir_path(
        tmp_path
    )

    assert result == str(tmp_path.resolve())


@pytest.mark.skipif(
    os.name != "nt",
    reason="Requires Windows pathlib semantics",
)
def test_09_windows_relative_log_file_path_raises() -> None:
    with pytest.raises(
        ValueError,
        match="absolute path",
    ):
        _raise_if_invalid_config_arg_log_file_path(
            Path("logs") / "audit.log"
        )


@pytest.mark.skipif(
    os.name != "nt",
    reason="Requires Windows pathlib semantics",
)
def test_10_windows_relative_log_dir_path_raises() -> None:
    with pytest.raises(
        ValueError,
        match="absolute path",
    ):
        _raise_if_invalid_config_arg_log_dir_path(
            Path("logs")
        )
