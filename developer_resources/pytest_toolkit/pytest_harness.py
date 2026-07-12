"""
pytest_harness.py

Execute a configured suite of test files using pytest_harness.

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

from developer_resources.pytest_toolkit.build_test_summary_block import (
    _build_test_summary_block,
)
from developer_resources.pytest_toolkit.derive_aggregate_test_summary_data import (
    _derive_aggregate_test_summary_data,
)
from developer_resources.pytest_toolkit.pytest_harness_classes import (
    CombinedCoverageResult,
    PytestTestFileRecord,
    SourceFileCoverageRecord,
)
from developer_resources.pytest_toolkit.pytest_harness_engine import pytest_wrap
from logduo import log


# --- pytest_harness() ---------------------------------------------------------
def pytest_harness(
    *,
    test_dir: Path,
    log_dir: Path,
    source_dir: Path,
    test_file_names: list[str] | None = None,
    individual_logs: bool = True,
    debug_print: bool = False,
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

    if debug_print:
        print("Settings form master_test_runner.py:")
        print("DEBUG_PRINT = True")
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

    # Check all test files named in test_file_names.
    if test_file_names is not None:
        for test_name in test_file_names:
            test_file_path = test_dir_path / f"{test_name}.py"

            if not test_file_path.exists():
                raise RuntimeError(
                    "Error in master_test_runner.py\n"
                    "Unrecognized test name in test_file_names:\n"
                    f"    {test_name}"
                )

    if test_file_names is None:
        test_file_names = sorted(
            path.stem
            for path in test_dir_path.glob("test_*.py")
        )

    if not test_file_names:
        raise RuntimeError("No test files identified.")
    if debug_print:
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
        f"Running {test_file_count} test files "
        f"(each dot represents one test file started): ",
        end="",
        flush=True,
    )

    for test_name in test_file_names:
        print(".", end="", flush=True)

        test_file_path = test_dir_path / f"{test_name}.py"

        if not test_file_path.exists():
            raise RuntimeError(
                "Error in master_test_runner.py\n"
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
            debug_print=debug_print,
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

    summary_data = _derive_aggregate_test_summary_data(
        pytest_test_file_records=results,
        combined_coverage_result=combined_coverage_result,
        debug_print=debug_print,
    )

    summary_text = _build_test_summary_block(
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
    )
