"""
pytest_harness_runner.py

Update debug toggle settings and paths as needed.

Last edited: 2026-07-14
"""

from pathlib import Path

from developer_resources.pytest_harness.pytest_harness import pytest_harness

# --- Toggle settings ---
DEBUG_PRINT = False
INDIVIDUAL_LOGS = False

# Run all test_*.py files if include_file_names is None.
include_file_names: list[str] | None = None

# Exclude specific test_*.py files if needed.
# exclude_file_names: list[str] | None = None
exclude_file_names  = ["test_make_real_default_logs"]



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
        include_file_names=include_file_names,
        exclude_file_names=exclude_file_names,
        individual_logs=INDIVIDUAL_LOGS,
        debug_print=DEBUG_PRINT,
    )


if __name__ == "__main__":
    main()
