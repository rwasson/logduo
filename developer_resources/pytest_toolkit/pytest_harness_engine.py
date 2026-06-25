"""
pytest_harness_engine.py

A pytest-based framework for unit tests, integration tests,
and artifact-driven smoke/visual testing.


Reusable development-mode pytest runner engine for logduo.

NOTE:
1. Coverage source is supplied by source_dir and may be
either a package directory or source tree root.

Example:
    source_dir=PROJECT_ROOT / "src" / "logduo"

2. Pytest execution policy is intentionally defined here rather than
pyproject.toml so the development test harness remains self-contained
and reproducible regardless of project-level pytest configuration.

Last edited: 2026-03-18
"""

from __future__ import annotations


import json
import subprocess
import sys
import time
from pathlib import Path

import tempfile

from coverage import Coverage

from developer_resources.pytest_toolkit.pytest_harness_classes import (
    PytestTestFileRecord,
    SourceFileCoverageRecord,
)



# --- pytest_wrap() ------------------------------------------------------------
def pytest_wrap(
    *,
    test_file_path: Path,
    test_log_file_path: Path,
    source_dir: Path,
    extra_pytest_args: list[str] | None = None,

) -> PytestTestFileRecord:
    """
    Dev-mode pytest runner using subprocess.

    Guarantees correct coverage instrumentation.
    """

    if not source_dir.exists():
        raise RuntimeError(
            f"Source directory does not exist:\n"
            f"    {source_dir}"
        )


    # Lazy imports (after subprocess design decision)
    from logduo import log
    from logduo.utils.wrap.wrap_text import strip_ansi

    log.join()

    test_logger = log.new_logger(
        test_log_file_path,
        to_console=False,
        to_main_log=False,
        log_prefix="off"
    )


    # --- temporary JSON to record pass and fail count ---
    with tempfile.NamedTemporaryFile(
            suffix=".json",
            delete=False,
    ) as temp_file:
        test_file_report_path = Path(temp_file.name)

    '''
    alternative setup to consider
    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        # "-vv",   #  only when want very verbose tracebacks
        "-v",
        "-rA",     # info on passed and failed tests
        # "-rfe"   # failed tests only
        "--maxfail=0",
        "--capture=no",
        "--tb=short",
        "--color=yes",
        "--cov=logduo",
        # "--cov-test_file_report=term",   # only when want full list of covered files for each test file
        # "--cov-test_file_report=term-missing",   # only when want above + full list of missing lines
        "--cov-test_file_report=",
        str(test_file_path),
        "--json-test_file_report",
        f"--json-test_file_report-file={test_file_report_path}",
    ]
    '''

    pytest_cmd = [
        sys.executable,

        "-m",
        "pytest",

        # Ignore addopts from pyproject.toml.
        "-o",
        "addopts=",

        # --- Output ---
        "-q",  # quieter pytest output
        "-rA",  # summary for all test outcomes
        "--color=yes",  # preserve colored output
        "--capture=no",  # allow test print() output
        "--tb=short",  # compact tracebacks
        # "--showlocals",  # include local variables in failures, too big
        "--durations=10",  # show 10 slowest tests

        # --- Execution policy ---
        "--maxfail=0",  # run all tests
        "--strict-markers",  # reject unknown pytest markers
        "--disable-warnings",  # suppress warning summary
        "--reruns=0",  # do not rerun failures

        # --- Coverage ---
        f"--cov={source_dir}",  # measure coverage for logduo package
        "--cov-branch",  # include branch coverage
        # "--cov-test_file_report=",  # suppress pytest coverage table in individual test files
        "--cov-report=term-missing",

        # --- Test file path ---
        str(test_file_path),

        # --- JSON test_file_report ---
        "--json-report",  # emit machine-readable test results
        f"--json-report-file={test_file_report_path}",
    ]
    # pytest_cmd += ["--cov-config=pyproject.toml"]  # causes crash

    if extra_pytest_args:
        pytest_cmd.extend(extra_pytest_args)

    start = time.time()

    process = subprocess.Popen(
        pytest_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    captured: list[str] = []

    assert process.stdout is not None

    for line in process.stdout:
        # print(line, end="")  # duplicates to console
        captured.append(line)

    process.wait()
    duration = time.time() - start

    '''
    DEBUG print section
    print(test_file_path.name)
    print("coverage size:", Path(".coverage").stat().st_size)
    for p in sorted(Path(".").glob(".coverage*")):
        print(
            p.name,
            p.stat().st_size,
        )
    '''

    cleaned = strip_ansi("".join(captured))
    test_logger(cleaned)
    test_logger(f"pytest exit code: {process.returncode}")
    test_logger(f"duration: {duration:.2f} seconds")


    # --- Store and return Coverage class info ---
    # coverage_obj = Coverage(data_file=".coverage")  # TODO verify
    coverage_obj = Coverage()
    coverage_obj.load()

    coverage_data = coverage_obj.get_data()
    source_file_coverage_records: dict[str, SourceFileCoverageRecord] = {}

    source_dir = source_dir.resolve()

    for source_file_path in coverage_data.measured_files():

        path_obj = Path(source_file_path).resolve()

        if source_dir not in path_obj.parents and path_obj != source_dir:
            continue

        analysis = coverage_obj._analyze(source_file_path)

        '''
         DEBUG print section
        print(f"test_file_name: {Path(test_file_path).name}")
        print(f"source_file_name: {Path(source_file_path).name}")
        print("analysis.branch_stats()")
        print(analysis.branch_stats())
        print("arc_possibilities:")
        print(sorted(analysis.arc_possibilities)[:50])
        # print("arcs_executed:")
        # print(sorted(analysis.arcs_executed)[:50])
        if Path(test_file_path).name == "test_non_script_mode.py":
            print()
            print("================================")
            print(f"test_file_name: {Path(test_file_path).name}")
            print(f"source_file_name: {Path(source_file_path).name}")
            print("analysis.branch_stats()")
            print(analysis.branch_stats())
            print("executed lines:", len(analysis.executed))
            print("branch stats:", len(analysis.branch_stats()))
            print("has_arcs:", analysis.has_arcs)
            print("statements:", len(analysis.statements))
            print("executed:", len(analysis.executed))
            print("missing:", len(analysis.missing))
            print("numbers:", analysis.numbers)
            print( )
        '''

        branch_source = {
            (branch_line, destination_count)
            for branch_line, (destination_count, _covered_count)
            in analysis.branch_stats().items()
        }
        branch_first_lines = {
            first_line
            for first_line, _destination_count in branch_source
        }
        total_branch_pairs = {
            pair
            for pair in analysis.arc_possibilities_set
            if pair[0] in branch_first_lines
        }
        executed_branch_pairs = {
            pair
            for pair in analysis.arcs_executed_set
            if pair[0] in branch_first_lines
        }

        # Safety check
        expected_branch_count = sum(
            _destination_count
            for first_line, _destination_count in branch_source
        )
        assert expected_branch_count == len(total_branch_pairs)


        source_file_coverage_records[source_file_path] = (
            SourceFileCoverageRecord(
                source_file_path=source_file_path,
                executed_lines=set(analysis.executed),
                missing_lines=set(analysis.missing),
                total_line_count=len(analysis.statements),
                branch_source=branch_source,
                total_branch_pairs=total_branch_pairs,
                executed_branch_pairs=executed_branch_pairs,
            )
        )


    # -- read JSON for pass/fail counts, then delete file ---
    passed_test_function_names: list[str] = []
    failed_test_function_names: list[str] = []
    error_test_function_names: list[str] = []
    skipped_test_function_names: list[str] = []
    xfailed_test_function_names: list[str] = []
    xpassed_test_function_names: list[str] = []


    try:
        test_file_report = json.loads(test_file_report_path.read_text())
        summary = test_file_report["summary"]


        passed_test_function_count = summary.get("passed", 0)
        failed_test_function_count = summary.get("failed", 0)
        error_test_function_count = (
                summary.get("error", 0)
                or summary.get("errors", 0)
        )
        skipped_test_function_count = summary.get("skipped", 0)
        xfailed_test_function_count = summary.get("xfailed", 0)
        xpassed_test_function_count = summary.get("xpassed", 0)

        for test_record in test_file_report.get("tests", []):
            nodeid = test_record["nodeid"]
            test_function_name = nodeid.rsplit("::", maxsplit=1)[-1]
            outcome = test_record["outcome"]


            if outcome == "passed":
                passed_test_function_names.append(test_function_name)
            elif outcome == "failed":
                failed_test_function_names.append(test_function_name)
            elif outcome in ("error", "errors"):
                error_test_function_names.append(test_function_name)
            elif outcome == "skipped":
                skipped_test_function_names.append(test_function_name)
            elif outcome == "xfailed":
                xfailed_test_function_names.append(test_function_name)
            elif outcome == "xpassed":
                xpassed_test_function_names.append(test_function_name)
            else:
                raise RuntimeError(
                    f"Unexpected pytest outcome: {outcome!r}\n"
                    f"Test: {nodeid}"
                )

            if outcome in ("error", "errors"):
                print(f"DEBUG 328 ERROR OUTCOME: {outcome!r}")

        assert passed_test_function_count == len(passed_test_function_names)
        assert failed_test_function_count == len(failed_test_function_names)
        assert error_test_function_count == len(error_test_function_names)
        assert skipped_test_function_count == len(skipped_test_function_names)
        assert xfailed_test_function_count == len(xfailed_test_function_names)
        assert xpassed_test_function_count == len(xpassed_test_function_names)

    finally:
        test_file_report_path.unlink(missing_ok=True)

    return PytestTestFileRecord(
        test_file_path=str(test_file_path),
        exit_code=process.returncode,
        passed_test_function_count=passed_test_function_count,
        failed_test_function_count=failed_test_function_count,
        error_test_function_count=error_test_function_count,
        skipped_test_function_count=skipped_test_function_count,
        xfailed_test_function_count=xfailed_test_function_count,
        xpassed_test_function_count=xpassed_test_function_count,
        duration_seconds=duration,
        source_file_coverage_records=source_file_coverage_records,
        passed_test_function_names=passed_test_function_names,
        failed_test_function_names=failed_test_function_names,
        error_test_function_names=error_test_function_names,
        skipped_test_function_names=skipped_test_function_names,
        xfailed_test_function_names=xfailed_test_function_names,
        xpassed_test_function_names=xpassed_test_function_names,
    )

