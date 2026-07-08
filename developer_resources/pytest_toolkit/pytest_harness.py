"""
pytest_harness.py

Execute a configured suite of test files using pytest_harness.

Responsibilities:
- run each test file in isolation
- create per-test-file logs
- validate test execution succeeded
- build aggregate coverage and test summaries

Last edited: 2026-06-11
"""

from pathlib import Path

from developer_resources.pytest_toolkit.build_test_summary_block import _build_test_summary_block
from developer_resources.pytest_toolkit.derive_aggregate_test_summary_data import _derive_aggregate_test_summary_data
from developer_resources.pytest_toolkit.pytest_harness_classes import PytestTestFileRecord
from developer_resources.pytest_toolkit.pytest_harness_engine import pytest_wrap
from logduo import log


# --- pytest_harness() ----------------------------------------------------------
def pytest_harness(
    *,
    test_dir: Path,
    log_dir: Path,
    source_dir: Path,
    test_file_names: list[str] | None = None,
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
            f"    {source_dir}"
        )


    if debug_print:
        print("debug_print = True in master_test_runner.py")
        print("LOG DIR = ")
        print(log_dir)
        print("test_dir = ")
        print(test_dir)

    log.configure(
        log_dir_path=log_dir_path,
        log_dir_layout="run",
        log_verbosity=3,
        keep=5,
        write_config_table=False,
        console_prefix="off",
        console_wrap_width=150,
        log_prefix="off",
    )


    # Check all test_files found in  test_file_names list
    if test_file_names is not None:
        for test_name in test_file_names:
            test_file_path = test_dir_path / f"{test_name}.py"
            if not test_file_path.exists():
                raise RuntimeError(
                    f"Error in master_test_runner.py \n"
                    f"Unrecognized test name in test_file_names:\n"
                    f"    {test_name}"
                )

    if test_file_names is None:
        test_file_names = sorted(
            path.stem
            for path in test_dir.glob("test_*.py")
        )

    if not test_file_names:
        raise RuntimeError("No test files identified.")


    # --- Start loop through test files--
    results: list[PytestTestFileRecord] = []

    test_file_count = len(test_file_names)
    print(f"Running {test_file_count} test files (each dot represents one test file started): ", end="", flush=True)


    for test_name in test_file_names:
        print(".", end="", flush=True)

        test_file_path = test_dir_path / f"{test_name}.py"


        if not test_file_path.exists():
            raise RuntimeError(
                f"Error in master_test_runner.py \n"
                f"Unrecognized test name in test_file_names:\n"
                f"    {test_name}"
            )

        if not test_file_path.is_file():
            raise RuntimeError(
                f"Expected file but found something else:\n"
                f"    {test_file_path}"
            )

        try:
            test_file_path.read_text(encoding="utf-8")
        except OSError as e:
            raise RuntimeError(
                f"Unable to read test file:\n"
                f"    {test_file_path}\n"
                f"    {e}"
            ) from e


        '''
        TODO delete, pytest handles this
        text = test_file_path.read_text(encoding="utf-8")

        if "def test_" not in text:
            raise RuntimeError(
                f"No test functions found in:\n"
                f"    {test_file_path}"
            )
        '''

        test_log_file_path = log.output_dir_path / f"{test_name}.log"
        if debug_print:
            print(f"\ntest_file_path = {test_file_path}")
            print(f"test_log_file_path = {test_log_file_path}")
            print(f"source_dir = {source_dir}")

        result = pytest_wrap(
            test_file_path=test_file_path,
            test_log_file_path=test_log_file_path,
            source_dir=source_dir,
            extra_pytest_args=["-q"],
            debug_print=debug_print,
        )

        results.append(result)


    print(" done", end="", flush=True)
    print(" ")
    print(" ")


    summary_data = _derive_aggregate_test_summary_data(
        pytest_test_file_records=results,
        debug_print=debug_print,
    )


    summary_text = _build_test_summary_block(summary_data=summary_data)
    log(summary_text)

    if debug_print:
        print('DEBUG_PRINT = True in master_test_runner.py')
        print(" ")
        print("Summary counts:")
        print(f"summary.executed_line_count={summary_data.executed_line_count}")
        print(f"summary.total_line_count ={summary_data.total_line_count}")
        print(" ")
        print(f"summary.executed_branch_count={summary_data.executed_branch_count}")
        print(f"summary.total_branch_count={summary_data.total_branch_count}")
        print(" ")
        print(f"summary total executed = {summary_data.executed_line_count + summary_data.executed_branch_count}")
        print(f"summary total statements and branches = {summary_data.total_line_count + summary_data.total_branch_count}")


