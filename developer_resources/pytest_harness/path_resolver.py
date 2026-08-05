"""
path_resolver.py

Last edited: 2026-08-05
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestFilePaths:
    test_file_path: Path
    test_file_log_path: Path
    coverage_data_file_path: Path


def _resolve_test_file_paths_for_run(
    *,
    test_dir: Path,
    relative_test_file_path: Path,
    output_dir_path: Path,
    coverage_dir_path: Path,
) -> TestFilePaths:
    test_file_path = test_dir / relative_test_file_path

    if not test_file_path.exists():
        raise RuntimeError(
            "Error in pytest_harness_runner.py\n"
            "Unrecognized test file:\n"
            f"    {relative_test_file_path}"
        )

    if not test_file_path.is_file():
        raise RuntimeError(
            "Expected file but found something else:\n"
            f"    {test_file_path}"
        )

    try:
        test_file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            "Unable to read test file:\n"
            f"    {test_file_path}\n"
            f"    {e}"
        ) from e

    safe_stem = (
        str(relative_test_file_path.with_suffix(""))
        .replace("/", "__")
        .replace("\\", "__")
    )

    return TestFilePaths(
        test_file_path=test_file_path,
        test_file_log_path=output_dir_path / f"{safe_stem}.log",
        coverage_data_file_path=coverage_dir_path / f".coverage.{safe_stem}",
    )