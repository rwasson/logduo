PYTEST_TOOLKIT_README.txt
==============================

Purpose
-------
Run unit and integration tests, inspect generated output,
and validate Logduo behavior.


General Rules
-------------
1. Run a master_test_runner by right-clicking its filename in PyCharm.

- Contains project paths, test-runner settings, and a list of test files.
- Calls pytest_harness(), which manages test execution, coverage, and logging.
- Generates one summary log.
- Can optionally generate one detailed log per test file.

2. Individual test files:

- Should contain tests only, with no test-runner logging setup.
- May use print() to include diagnostic output in individual test logs.
- Tests that create logs should normally use tmp_path for log_dir_path
  to avoid persistent log clutter.
- Each test must be independent and must not rely on prior test state.

3. Files in /developer_resources/pytest_toolkit should rarely require modification.

Edit them only when:
    - fixing a bug in the test framework
    - extending pytest-toolkit functionality

Normal test development should occur in:
    /developer_resources/test_files


Subprocess Execution
--------------------
Each test file runs in its own pytest subprocess.

This provides:
- proper coverage instrumentation
- clean import and module state between test files
- isolated Logduo session and lifecycle behavior
- independent pytest results for each test file


Coverage
--------
Each test-file subprocess writes to its own temporary Coverage.py data file.

After all test files finish:
- Coverage.py combines the separate data files
- Coverage.py generates the official aggregate statement and branch counts
- the temporary coverage files are deleted
- the aggregate summary uses Coverage.py's reported totals

Tests execute only once.

Known limitation:
- Python code executed inside nested subprocesses started by individual tests
  is behaviorally tested but is not currently included in coverage totals.


Individual Logs
---------------
When individual_logs=True:
- one log is created for each test file
- captured pytest output is preserved
- each log includes that test file's coverage report

When individual_logs=False:
- individual test logs and per-file coverage tables are omitted
- test execution, JSON results, and aggregate coverage remain unchanged


Design Philosophy
-----------------
The toolkit is optimized for Logduo development rather than
general-purpose pytest usage.

Benefits:
- Creates an archival record of test results during debugging.
- Optional per-test-file logs make failures and generated output easier
  to inspect without producing one overwhelming combined log.
- The main log acts as a dashboard for test outcomes and aggregate coverage.
- Separate subprocesses reduce accidental state sharing between test files.
- Aggregate coverage is calculated by Coverage.py rather than by custom
  coverage-merging logic.
