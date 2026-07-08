PYTEST_TOOLKIT_README.txt
==============================

Purpose
-------
Conduct unit and integration testing, inspect generated output,
and validate Logduo behavior.

General Rules
-------------
1. Run a master_test_runner (right-click its filename in PyCharm).

- Contains only Path information and a list of test files.
- Calls pytest_harness(), which manages test execution and logging.
- Generates one summary log and one log per test file.

2. Individual test files:

- Individual test files should just contain tests (no logging setup).
- Use print() inside test files to capture output in the individual test logs.
- If a test creates a log, consider setting log_dir_path = tmp_path to avoid log clutter
- Each test should be independent and must not rely on prior test state.

3. Files in /developer_resources/pytest_toolkit should rarely require modification.
Edit only when:
    - fixing a bug in the test framework
    - extending pytest-toolkit functionality

Normal test development should occur in:
    /developer_resources/test_files


Multiprocess Coverage
---------------------
Test files are executed through a subprocess runner to ensure:
• Proper coverage instrumentation
• Clean import state between test files
• Correct Logduo lifecycle behavior

Known limitation:
• Current pytest-toolkit coverage collection does not correctly
  track code executed via `python -c` subprocesses.
  Such behavior must currently be tested manually.


Design Philosophy
-----------------
The toolkit is optimized for Logduo development rather than
general-purpose pytest usage.

Benefits:
- Creates an archival record of test results during debugging.
- Per-test-file logs allow visualization of log output in specific
  scenarios without the overwhelming length of a single combined log.
- The main log serves as a dashboard summarizing test-file results.
- Coverage is collected and aggregated per test file, making it easy
  to identify which test files exercise which areas of the codebase.