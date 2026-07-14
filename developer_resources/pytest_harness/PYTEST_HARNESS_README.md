PYTEST_HARNESS_README.md
=========================

Purpose
-------
pytest_harness is an IDE-friendly pytest runner built on Logduo.
It runs test files in isolated subprocesses, captures readable logs,
combines coverage, and produces a compact test dashboard.


General Rules
-------------
1. Run pytest_harness_runner.py by right-clicking its filename in PyCharm.

- Contains project paths, test-runner settings, and optional include/exclude file lists.
- Calls pytest_harness(), which manages test execution, coverage, and logging.
- Generates one summary log.
- Can optionally generate one detailed log per test file.

2. Individual test files:

- Should contain tests only, with no test-runner logging setup.
- May use print() to include diagnostic output in individual test logs.
- Tests that create logs should normally use tmp_path for log_dir_path
  to avoid persistent log clutter.
- Each test must be independent and must not rely on prior test state.

3. Files in /developer_resources/pytest_harness should rarely require modification.

Edit them only when:
    - fixing a bug in the test framework
    - extending pytest_harness functionality

Normal Logduo pytest test development should occur in:
    /developer_resources/logduo_validation/pytest_files
    