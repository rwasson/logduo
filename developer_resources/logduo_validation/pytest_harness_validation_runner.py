"""
pytest_harness_validation_runner.py

Update file settings and paths as needed.

Runs automatically in macOS, Ubuntu and Windows when changes pushed to GitHub.
    called by:  .github/workflows/tests.yml


NOTE: When copy in a new internal version of pytest_harness package, MUST
update to local path for progress_plugin inside of record_builder.py

Last edited: 2026-08-08
"""
import sys
from pathlib import Path

from developer_resources.pytest_harness import pytest_harness

# Run all test_*.py files if include_list is None.
include_list: list[str] | None = None
# include_list = ["test_header_footer_blocks"]

# Exclude specific test_*.py files if needed.
# exclude_list: list[str] | None = None
exclude_list  = ["test_make_real_default_logs",
                 "test_pytest_harness_empty",
                 "test_pytest_harness_flagged",
                 "test_pytest_harness_import_error",
                 ]


# --- Path settings ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
print(f"From Runner: PROJECT_ROOT is {PROJECT_ROOT}")

test_file_dir = (
    PROJECT_ROOT
    / "developer_resources"
    / "logduo_validation"
    / "test_files"
)

log_dir = (
    PROJECT_ROOT
    / "developer_resources"
    / "logduo_validation"
    / "logs"
)

tested_code_dir = (
    PROJECT_ROOT
    / "src"
    / "logduo"
)



results = pytest_harness(
    test_file_dir=test_file_dir,
    log_dir=log_dir,
    tested_code_dir=tested_code_dir,
    include_list=include_list,
    exclude_list=exclude_list,
    test_file_logs=True,
    log_keep=3,
    debug_harness=False,
    console_theme="light",
    dashboard_width=100,
    show_skipped_and_xfailed=True,
    random_order=False,
    test_function_timeout=100,
)

if results.pytest_harness_exit_code != 0:
    sys.exit(results.pytest_harness_exit_code)

