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

import json
import tempfile
from pathlib import Path

from coverage import Coverage

from developer_resources.pytest_harness.aggregate_summary_data_builder import (
    _build_aggregate_summary_data,
)
from developer_resources.pytest_harness.classes import (
    CombinedCoverageResult,
    PytestTestFileRecord,
    SourceFileCoverageRecord,
)
from developer_resources.pytest_harness.engine import pytest_wrap
from developer_resources.pytest_harness.summary_table_builder import (
    _build_summary_table,
)
from logduo import log


# --- pytest_harness() ---------------------------------------------------------
def pytest_harness(
    *,
    test_dir: Path,
    log_dir: Path,
    source_dir: Path,
    include_file_names: list[str] | None = None,
    exclude_file_names: list[str] | None = None,
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

    test_file_names = _resolve_test_file_names(
        test_dir_path=test_dir_path,
        include_file_names=include_file_names,
        exclude_file_names=exclude_file_names,
    )

    if debug_pytest_harness:
        print("\nDEBUG: Exact test files pytest_harness will run:")
        for index, test_name in enumerate(test_file_names, start=1):
            print(f"    {index:>2}. {test_name}")

        print(f"DEBUG: Exact test-file count: {len(test_file_names)}\n")

    # --- Temporary per-test-file coverage data ---
    coverage_temp_dir = tempfile.TemporaryDirectory(
        prefix="coverage_",
        dir=log.output_dir_path,
    )
    coverage_dir_path = Path(coverage_temp_dir.name)

    # --- Run test files ---
    results: list[PytestTestFileRecord] = []

    test_file_count = len(test_file_names)
    print(
        f"Running {test_file_count} test files: ",
        end="",
        flush=True,
    )

    for test_name in test_file_names:
        print(".", end="", flush=True)

        test_file_path = test_dir_path / f"{test_name}.py"

        if not test_file_path.exists():
            raise RuntimeError(
                "Error in pytest_harness_runner.py\n"
                "Unrecognized test name in test_file_names:\n"
                f"    {test_name}"
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

        test_log_file_path = log.output_dir_path / f"{test_name}.log"

        coverage_data_file_path = (
            coverage_dir_path / f".coverage.{test_name}"
        )

        result = pytest_wrap(
            test_file_path=test_file_path,
            test_log_file_path=test_log_file_path,
            source_dir=source_dir_path,
            coverage_data_file_path=coverage_data_file_path,
            # extra_pytest_args=["-q"],    # "-q" already called, extra_pytest_args[] reserved for future args
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

    summary_data = _build_aggregate_summary_data(
        pytest_test_file_records=results,
        combined_coverage_result=combined_coverage_result,
        debug_pytest_harness=debug_pytest_harness,
    )

    summary_text = _build_summary_table(
        summary_data=summary_data,
    )
    log(summary_text)


# --- _combine_coverage_data_files() ------------------------------------------
def _combine_coverage_data_files(
    *,
    coverage_dir_path: Path,
    source_dir: Path,
) -> CombinedCoverageResult:
    """Combine per-test-file coverage data and return official totals."""

    combined_data_file_path = coverage_dir_path / ".coverage"
    combined_json_file_path = coverage_dir_path / "combined_coverage.json"

    coverage_obj = Coverage(
        data_file=str(combined_data_file_path),
        branch=True,
    )

    coverage_obj.combine(
        data_paths=[str(coverage_dir_path)],
        strict=True,
        keep=True,
    )
    coverage_obj.save()

    coverage_obj.json_report(
        outfile=str(combined_json_file_path),
        pretty_print=False,
    )

    report = json.loads(
        combined_json_file_path.read_text(encoding="utf-8")
    )

    # Official aggregate totals calculated by Coverage.py.
    totals = report["totals"]

    executed_line_count = int(totals["covered_lines"])
    total_line_count = int(totals["num_statements"])
    executed_branch_count = int(totals["covered_branches"])
    total_branch_count = int(totals["num_branches"])

    statement_coverage_pct = (
        100 * executed_line_count / total_line_count
        if total_line_count > 0
        else 0.0
    )

    branch_coverage_pct = (
        100 * executed_branch_count / total_branch_count
        if total_branch_count > 0
        else 0.0
    )

    total_coverage_pct = float(totals["percent_covered"])

    source_dir = source_dir.resolve()
    records: dict[str, SourceFileCoverageRecord] = {}

    for reported_path, file_data in report["files"].items():
        source_file_path = Path(reported_path)

        if not source_file_path.is_absolute():
            source_file_path = Path.cwd() / source_file_path

        source_file_path = source_file_path.resolve()

        if (
            source_file_path != source_dir
            and source_dir not in source_file_path.parents
        ):
            continue

        executed_lines: set[int] = {
            int(line_number)
            for line_number in file_data["executed_lines"]
        }

        missing_lines: set[int] = {
            int(line_number)
            for line_number in file_data["missing_lines"]
        }

        executed_branch_pairs: set[tuple[int, int]] = {
            (int(first_line), int(second_line))
            for first_line, second_line
            in file_data["executed_branches"]
        }

        missing_branch_pairs: set[tuple[int, int]] = {
            (int(first_line), int(second_line))
            for first_line, second_line
            in file_data["missing_branches"]
        }

        total_branch_pairs: set[tuple[int, int]] = (
            executed_branch_pairs
            | missing_branch_pairs
        )

        branch_destinations: dict[int, set[int]] = {}

        for first_line, second_line in total_branch_pairs:
            branch_destinations.setdefault(
                first_line,
                set(),
            ).add(second_line)

        branch_source: set[tuple[int, int]] = {
            (first_line, len(destinations))
            for first_line, destinations
            in branch_destinations.items()
        }

        source_file_path_str = str(source_file_path)

        records[source_file_path_str] = SourceFileCoverageRecord(
            source_file_path=source_file_path_str,
            executed_lines=executed_lines,
            missing_lines=missing_lines,
            total_line_count=int(
                file_data["summary"]["num_statements"]
            ),
            branch_source=branch_source,
            total_branch_pairs=total_branch_pairs,
            executed_branch_pairs=executed_branch_pairs,
        )

    return CombinedCoverageResult(
        source_file_coverage_records=records,
        executed_line_count=executed_line_count,
        total_line_count=total_line_count,
        executed_branch_count=executed_branch_count,
        total_branch_count=total_branch_count,
        statement_coverage_pct=statement_coverage_pct,
        branch_coverage_pct=branch_coverage_pct,
        total_coverage_pct=total_coverage_pct,
    )


# === Internal helpers =========================================================

# --- _resolve_test_file_names() -----------------------------------------------
def _resolve_test_file_names(
    *,
    test_dir_path: Path,
    include_file_names: list[str] | None,
    exclude_file_names: list[str] | None,
) -> list[str]:
    """
    Resolve the final ordered list of pytest test-file stems.

    Rules
    -----
    If include_file_names is None:
        Discover all files matching test_*.py in test_dir_path.

    If include_file_names is provided:
        Use only those names.

    If exclude_file_names is provided:
        Remove those names from the final list.

    File names may be provided with or without the .py suffix.
    Returned names are stems without .py.
    """

    def normalize_file_name(name: str) -> str:
        path = Path(name)
        if path.suffix == ".py":
            return path.stem
        return name

    def assert_test_file_exists(test_file_name: str, *, list_name: str) -> None:
        test_file_path = test_dir_path / f"{test_file_name}.py"

        if not test_file_path.exists():
            raise RuntimeError(
                f"Error in pytest_harness_runner.py\n"
                f"Unrecognized test name in {list_name}:\n"
                f"    {test_name}\n\n"
                f"Expected file:\n"
                f"    {test_file_path}"
            )

    # --- include list or discovery ---
    if include_file_names is None:
        resolved_names = sorted(
            path.stem
            for path in test_dir_path.glob("test_*.py")
            if path.is_file()
        )
    else:
        resolved_names = [
            normalize_file_name(name)
            for name in include_file_names
        ]

        for test_name in resolved_names:
            assert_test_file_exists(
                test_name,
                list_name="include_file_names",
            )

    # --- exclude list ---
    if exclude_file_names is not None:
        excluded_names = {
            normalize_file_name(name)
            for name in exclude_file_names
        }

        for test_name in excluded_names:
            assert_test_file_exists(
                test_name,
                list_name="exclude_file_names",
            )

        resolved_names = [
            test_name
            for test_name in resolved_names
            if test_name not in excluded_names
        ]

    if not resolved_names:
        raise RuntimeError(
            "No pytest test files selected.\n\n"
            f"Test directory:\n"
            f"    {test_dir_path}\n\n"
            f"include_file_names:\n"
            f"    {include_file_names}\n\n"
            f"exclude_file_names:\n"
            f"    {exclude_file_names}"
        )

    return resolved_names
