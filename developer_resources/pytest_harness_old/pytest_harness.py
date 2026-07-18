"""
pytest_harness.py

pytest_harness is an IDE-friendly pytest runner built on Logduo.
It runs test files in isolated subprocesses, captures readable logs,
combines coverage, and produces a compact test dashboard.

Responsibilities:
- run each test file in isolation
- create per-test-file logs
- validate test execution succeeded
- combine per-test-file coverage data
- build aggregate coverage and test summaries

Last edited: 2026-07-11
"""

import tempfile
from pathlib import Path


from developer_resources.pytest_harness.summary_data_builder import (
    _build_summary_data,
    _combine_coverage_data_files
)
from developer_resources.pytest_harness.classes import TestFileRecord
from developer_resources.pytest_harness.test_file_record_builder import _build_test_file_record
from developer_resources.pytest_harness.resolve_test_file_paths import (
    _resolve_test_file_paths
)
from developer_resources.pytest_harness.summary_table_builder import (
    _build_summary_table,
)
from logduo import log

COVERAGE_WARNING_THRESHOLD = .85


# --- pytest_harness() ---------------------------------------------------------
def pytest_harness(
    *,
    test_dir: Path,
    log_dir: Path,
    source_dir: Path,
    include_list: list[str | Path] | None = None,
    exclude_list: list[str | Path] | None = None,
    individual_logs: bool = True,
    debug_pytest_harness: bool = False,
) -> None:

    log_dir_path = log_dir
    test_dir_path = test_dir
    source_dir_path = source_dir

    if not test_dir_path.exists():
        raise RuntimeError(
            f"Test directory does not exist:\n"
            f"    {test_dir_path}"
        )

    if not log_dir_path.exists():
        raise RuntimeError(
            f"Log directory does not exist:\n"
            f"    {log_dir_path}"
        )

    if not source_dir_path.exists():
        raise RuntimeError(
            f"Source directory does not exist:\n"
            f"    {source_dir_path}"
        )

    if debug_pytest_harness:
        print("Settings from pytest_harness_runner.py:")
        print("debug_pytest_harness = True")
        print(f"INDIVIDUAL_LOGS = {individual_logs}")
        print("LOG DIR = ")
        print(log_dir_path)
        print("test_dir = ")
        print(test_dir_path)

    log.configure(
        log_dir_path=log_dir_path,
        log_file_layout="run",
        log_verbosity=3,
        keep=5,
        write_config_table=False,
        console_prefix="off",
        console_wrap_width=150,
        log_prefix="off",
    )

    relative_test_file_paths = _resolve_test_file_paths(
        test_dir_path=test_dir_path,
        include_list=include_list,
        exclude_list=exclude_list,
    )

    if debug_pytest_harness:
        print("\nDEBUG: Exact test files pytest_harness will run:")
        for index, relative_test_file_path in enumerate(relative_test_file_paths, start=1):
            print(f"    {index:>2}. {relative_test_file_path}")
        print(
            f"DEBUG: Exact test-file count: "
            f"{len(relative_test_file_paths)}\n"
        )

    # --- Temporary per-test-file coverage data ---
    coverage_temp_dir = tempfile.TemporaryDirectory(
        prefix="coverage_",
        dir=log.output_dir_path,
    )
    coverage_dir_path = Path(coverage_temp_dir.name)

    # --- Run test files ---
    results: list[TestFileRecord] = []

    test_file_count = len(relative_test_file_paths)
    print(
        f"Running {test_file_count} test files: ",
        end="",
        flush=True,
    )

    for relative_test_file_path in relative_test_file_paths:
        print(".", end="", flush=True)

        test_file_path = test_dir_path / relative_test_file_path

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

        # Keep generated logs flat while preserving nested test-file identity.
        test_file_safe_stem = (
            str(relative_test_file_path.with_suffix(""))
            .replace("/", "__")
            .replace("\\", "__")
        )

        test_file_log_path = log.output_dir_path / f"{test_file_safe_stem}.log"
        coverage_data_file_path = (
            coverage_dir_path / f".coverage.{test_file_safe_stem}"
        )

        # Create temporary coverage config file - do not rely on pyproject.toml
        coverage_config_file_path = coverage_dir_path / "pytest_harness_coveragerc"
        coverage_config_file_path.write_text(
            "[run]\n"
            "branch = true\n"
            f"source = {source_dir_path}\n"
            "relative_files = false\n"
            "parallel = true\n"
            "concurrency = multiprocessing\n"
            "patch = subprocess\n"
            "\n"
            "[report]\n"
            "skip_empty = true\n"
            "show_missing = true\n"
            "precision = 2\n",
            encoding="utf-8",
        )

        result = _build_test_file_record(
            test_file_path=test_file_path,
            test_file_log_path=test_file_log_path,
            source_dir=source_dir_path,
            coverage_data_file_path=coverage_data_file_path,
            # extra_pytest_args=["-q"],    # "-q" already called, extra_pytest_args[] reserved for future args
            coverage_config_file_path=coverage_config_file_path,
            individual_logs=individual_logs,
            debug_pytest_harness=debug_pytest_harness,
        )

        results.append(result)

    # Combine the separate per-test-file data files once.
    combined_coverage_result = _combine_coverage_data_files(
        coverage_dir_path=coverage_dir_path,
        source_dir=source_dir_path,
    )

    # All combined data is now stored in normal Python records.
    coverage_temp_dir.cleanup()

    print(" done", end="", flush=True)
    print(" ")
    print(" ")

    summary_data = _build_summary_data(
        pytest_test_file_records=results,
        combined_coverage_result=combined_coverage_result,
        debug_pytest_harness=debug_pytest_harness,
    )

    summary_text = _build_summary_table(
        summary_data=summary_data,
    )
    log(summary_text)

    if combined_coverage_result.total_coverage_pct < COVERAGE_WARNING_THRESHOLD:
        log.warning(
            f"Total coverage "
            f"({combined_coverage_result.total_coverage_pct:.2f}%) "
            f"is below warning threshold "
            f"{COVERAGE_WARNING_THRESHOLD:.2f}%."

        )





