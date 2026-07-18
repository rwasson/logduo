pytest_harness
==============

Purpose
-------
Purpose
-------
pytest_harness is a one-click pytest runner for IDE-centered workflows.

It handles pytest, coverage, subprocess isolation, logs, and summary reporting
so test runs are easier to start and easier to interpret.

pytest_harness is useful when you want:

- one-click test execution from an IDE
- automatic coverage setup with no command-line flags
- readable logs instead of dense raw pytest output
- one summary dashboard for the whole test run
- optional detailed logs for each test file
- test execution to continue even if one test file crashes
- clear separation between test-file outcomes and individual test outcomes
- explicit visibility into files that fail during import or collection
- combined coverage across isolated test-file subprocesses


How It Works
------------
pytest_harness runs each selected pytest test file in its own subprocess.

This means:

- one broken test file does not stop the remaining test files from running
- import errors and collection problems are reported at the file level
- per-file logs stay readable
- coverage data is collected separately and combined after the run
- the final dashboard shows the full test-run result in one place

pytest_harness uses Logduo for logging and output management, but ordinary test
files do not need Logduo setup.


Quick Start
-----------
Create a small runner script in your project:

    from pathlib import Path

    from pytest_harness import pytest_harness

    PROJECT_ROOT = Path(__file__).resolve().parent

    pytest_harness(
        test_dir=PROJECT_ROOT / "tests",
        log_dir=PROJECT_ROOT / "logs",
        source_dir=PROJECT_ROOT / "src" / "my_package",
        include_list=None,
        exclude_list=None,
        individual_logs=True,
        debug_pytest_harness=False,
    )

In PyCharm, right-click the runner script and run it.

pytest_harness will discover tests, run them in isolated subprocesses, collect
coverage, write logs, and print a compact dashboard.


Public API
----------
Main entry point:

    pytest_harness(
        *,
        test_dir: Path,
        log_dir: Path,
        source_dir: Path,
        include_list: list[str | Path] | None = None,
        exclude_list: list[str | Path] | None = None,
        individual_logs: bool = True,
        debug_pytest_harness: bool = False,
    ) -> None

Arguments:

- `test_dir`
    - Directory containing pytest test files.

- `log_dir`
    - Directory where pytest_harness writes run logs.

- `source_dir`
    - Source directory measured for coverage.

- `include_list`
    - Optional list of test files or test directories to run.

- `exclude_list`
    - Optional list of test files or test directories to exclude.

- `individual_logs`
    - If True, writes a detailed log for each selected test file.

- `debug_pytest_harness`
    - If True, prints additional pytest_harness diagnostic information.


Dashboard
---------
The dashboard includes:

- number of source files covered
- number of test files run
- test-file outcomes
- individual pytest test-function outcomes
- aggregate statement, branch, and total coverage
- source files sorted from lowest to highest statement coverage, including
  executed statement count and total statement count

Test-file outcomes show whether each file:

- passed all tests
- had failures
- had errors
- had skipped tests
- had xfailed tests
- had xpassed tests

Individual test-function outcomes show total pytest results:

- passed
- failed
- errors
- skipped
- xfailed
- xpassed

pytest_harness also flags test files that did not execute any test functions,
such as files with import errors, collection problems, or broken test setup.
These can be easy to miss in raw pytest output, especially when running many
files at once.


Runner Script Guidelines
------------------------
The runner script should contain project paths and test-runner settings.

Typical responsibilities:

- define `test_dir`
- define `log_dir`
- define `source_dir`
- optionally define `include_list`
- optionally define `exclude_list`
- call `pytest_harness()`

The runner script is usually the file you run directly from the IDE.


Test File Guidelines
--------------------
Individual test files should contain tests only.

Recommended practices:

- Do not configure pytest_harness or Logduo inside individual test files.
- Use `print()` when diagnostic output should appear in individual test logs.
- Use `tmp_path` when tests create files or logs.
- Keep tests independent.
- Do not rely on test execution order.


Test Selection
--------------
pytest_harness discovers and runs pytest test files under `test_dir`.

Tests execute only once.

Default behavior:

    include_list = None
    exclude_list = None

This discovers all files matching:

    test_*.py

Discovery is recursive, so nested test directories are supported.

Example test tree:

    tests/
        test_config.py
        unit/test_paths.py
        integration/test_run.py

Selected paths are tracked relative to `test_dir`:

    test_config.py
    unit/test_paths.py
    integration/test_run.py


include_list and exclude_list
-----------------------------
`include_list` selects specific test files or test directories.

`exclude_list` removes specific test files or test directories after discovery
or include-list resolution.

Examples:

    include_list = ["test_config"]
    include_list = ["test_config.py"]
    include_list = ["unit"]
    include_list = ["unit/"]
    include_list = ["unit/test_paths"]
    include_list = ["unit/test_paths.py"]

    exclude_list = ["test_make_real_logs"]
    exclude_list = ["integration/slow_tests"]

Selector rules:

1. If a selector ends with `.py`, it is treated as a file path.
   The file must exist.

2. If a selector does not end with `.py`:
   - if only `selector.py` exists, that file is selected.
   - if only `selector/` exists, that directory is expanded recursively.
   - if both `selector.py` and `selector/` exist, the directory is used and a warning is printed.
   - if neither exists, pytest_harness raises an error.

To force file selection, include `.py`:

    unit/test_paths.py

To force directory selection, use the directory path:

    unit/test_paths/


Coverage
--------
pytest_harness generates its own temporary Coverage.py configuration for each
run. It does not use coverage settings from `pyproject.toml`.

The generated coverage configuration includes:

- branch coverage
- source directory selection from `source_dir`
- parallel coverage data files
- multiprocessing support
- subprocess coverage patching
- skipped empty files in reports
- missing-line reporting
- precision = 2

`relative_files = true` is intentionally not used because pytest_harness
combines coverage data from subprocesses and uses absolute source paths
internally.

Each selected test file runs in its own subprocess and writes to its own
temporary Coverage.py data file. Python subprocesses started by those tests are
also included in coverage when they inherit the test process environment.

After all test files finish:

- Coverage.py generates the official aggregate statement and branch counts.
- The aggregate summary uses Coverage.py's reported totals.
- Temporary coverage files are deleted.

Subprocess coverage was validated with a temporary source-file probe: code
executed only inside a nested Python subprocess was included in the combined
Coverage.py totals.


Design Notes
------------
pytest_harness is not a pytest plugin and is not intended to replace pytest's
command-line interface.

It is a pytest workflow tool for projects that benefit from:

- IDE-friendly execution
- isolated per-file pytest runs
- readable logs
- compact aggregate summaries
- explicit detection of failed, errored, skipped, xfailed, and xpassed outcomes
- combined coverage across isolated test-file subprocesses
