"""
pytest_harness_runner.py

Update file settings and paths as needed.

Runs automatically in macOS, Ubuntu and Windows when changes pushed to GitHub.
    called by:  .github/workflows/tests.yml

Last edited: 2026-07-14
"""

from pathlib import Path

from developer_resources.pytest_harness.pytest_harness import pytest_harness

# --- File settings ---
INDIVIDUAL_LOGS = True

# Run all test_*.py files if include_list is None.
include_list: list[str] | None = None
# include_list = ["test_header_footer_blocks"]

# Exclude specific test_*.py files if needed.
# exclude_list: list[str] | None = None
exclude_list  = ["test_make_real_default_logs"]



# --- Path settings ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]

test_dir = (
    PROJECT_ROOT
    / "developer_resources"
    / "logduo_validation"
    / "pytest_files"
)

log_dir = (
    PROJECT_ROOT
    / "developer_resources"
    / "logduo_validation"
    / "logs"
)

source_dir = (
    PROJECT_ROOT
    / "src"
    / "logduo"
)


# === main() DO NOT EDIT BELOW =================================================
def main() -> None:
    pytest_harness(
        test_dir=test_dir,
        log_dir=log_dir,
        source_dir=source_dir,
        include_list=include_list,
        exclude_list=exclude_list,
        individual_logs=INDIVIDUAL_LOGS,
        log_keep=3,
        debug_pytest_harness=False,
        console_wrap_width=100,
    )


if __name__ == "__main__":
    main()
