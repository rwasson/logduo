"""
master_test_runner.py

Update setup paths as needed

Last edited: 2026-06-1
"""

from pathlib import Path

from developer_resources.pytest_toolkit.pytest_harness import pytest_harness

_debug_print = False

# --- Path settings ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
test_dir = (
        PROJECT_ROOT
        / "developer_resources"
        / "test_files"
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

'''
test_file_names = [
    "test_arg_resolvers",
]

'''

# --- List of test files (without the .py) ---
test_file_names = [
    "test_arg_resolvers",
    "test_artifacts",
    "test_close",
    "test_console",
    "test_created_file_record",
    "test_dispatcher",
    "test_header_footer_blocks",
    "test_level_entry",
    "test_initialize",
    "test_jsonl",
    "test_logduo",
    "test_loguru_integration",
    "test_main_sink",
    "test_message_prep",
    "test_new_level",
    "test_new_loguru_sink",
    # "test_non_script_mode",
    "test_output_paths",
    "test_path_helpers",
    "test_prune",
    "test_run",
    "test_runtime_warn",

    "test_session_config_resolution",
    "test_short_path",
    "test_system_helpers",
    "test_table_builders",
    "test_user_sink",
    "test_wrap_lines",

    # must be manually cleaned from real log dir
    # "tests_making_real_logs",
]




# === main() DO NOT EDIT BELOW =================================================
def main() -> None:

    pytest_harness(
        test_dir=test_dir,
        log_dir=log_dir,
        source_dir=source_dir,
        test_file_names=test_file_names,
        debug_print=_debug_print,
    )


if __name__ == "__main__":
    main()
