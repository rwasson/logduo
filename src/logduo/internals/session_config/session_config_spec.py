"""
session_config_spec.py

Defines the complete specification for session configuration:
- Cerberus validation schema
- Default values
- Display/grouping metadata (for tables and artifacts)
- Allowed-value hints and descriptions
- Theme presets and passthrough fields

Used by:
- session_config validation (Cerberus)
- Config normalization/resolution layer
- config_table.txt and related artifacts

This file contains no resolution logic.

Last edited: 2026-05-27
"""

from __future__ import annotations

from typing import Any

from logduo.internals.session_config.cerberus_utils import (
    _bool_hint,
    _norm_bool,
    _norm_log_file_mode,
    _norm_path_to_string,
    _norm_str_lower,
    _norm_str_lower_mixed,
    _norm_theme,
)
from logduo.internals.session_config.session_constants import (
    _DARK_THEME_COLORS,
    _DEFAULT_LOG_VERBOSITY,
    _LIGHT_THEME_COLORS,
    _VALID_log_file_layoutS,
    _VALID_LOG_FILE_MODES,
    _VALID_PREFIX,
)

# === Notes ====================================================================
# 1. By policy, None is not accepted as a user-facing configuration value.
#    Use explicit values such as:  "off", {}, False
#
# 2. "auto" is an internal resolution sentinel used only in DEFAULTS.
#    Users should omit the argument instead.
#    Explicitly passing "auto" raises an error.
#
# 3. See "Description" and "Allowed Values" sections for details on each argument.
#    Users can inspect:
#        help(log.configure)
#        config_table.txt
#
# 4. Special fields:
#    a. console_wrap_width
#       Rich auto-detection is unreliable in some environments
#       (especially PyCharm, which often reports width=80).
#
#    b. log_wrap_width
#       Default = "off" to match user expectations for plain-text logs.
#       Recommended starting value if enabling wrapping:  log_wrap_width = 120
#
#    c. log_verbosity
#       Default = _DEFAULT_LOG_VERBOSITY ( = 2) in session_constants.py
#       A global default is needed for main_sink and user_sink
#
#    d. first_instance_owns_console
#       When False, multiple Logduo instances may write to the same console.
#
#       If multiple processes are expected, enabling:
#           show_pid_in_console = True
#           show_pid_in_log = True
#
#       helps identify the originating process.


# === Descriptions used in config_table.txt ==================================
DESCRIPTIONS: dict[str, str] = {
    # --- File Management ---
    "log_file_mode": "Select how log files are created (write, append, timestamped). Independent of log_file_path.",
    "log_file_path": "Specify log file path (forces log_file_layout='flat')",
    "log_file_name": "Specify file name (with extension) for main log file",
    "log_file_layout": "Select: flat (/logs/myfile.log), script (/logs/myfile/myfile.log), "
    "run (/logs/myfile/run_timestamp/myfile.log). If no script found, "
    "uses 'session' instead of 'myfile'",
    "log_dir_path": "Specify root directory for logs",
    "keep": (
        "Specify number of Logduo-created run directories to keep. "
        "Cleanup only applies to directories containing "
        "a .logduo_marker file."
    ),
    # --- Formatting ---
    # console
    "console_verbosity": "Select level of detail in console",
    "console_prefix": "Select line prefix elements",
    "console_wrap_width": "Specify wrap width for console",
    "console_header": "Select session header for console",
    "console_footer": "Select session footer for console",
    "console_color": "Enable colored console output",
    "console_theme": "Select console theme style",
    "console_theme_dict": "Customize console theme dict",
    # log
    "log_verbosity": "Select level of detail in log",
    "log_prefix": "Select line prefix elements",
    "log_wrap_width": "Specify wrap width for log lines",
    "log_header": "Specify session header for log",
    "log_footer": "Specify session footer for log",
    # --- Advanced ---
    "show_debug_source": "Show <file:line> in prefix for DEBUG messages",
    "show_logger_name": "Show logger name in console and main-log line prefixes",
    "show_pid_in_console": "Show process id in console line prefix (for multi-process sessions)",
    "show_pid_in_log": "Show process id in log line prefix (for multi-process sessions)",
    "write_config_table": "Write config_table.txt",
    "write_config_json": "Write config.json (machine-readable config snapshot)",
    "write_jsonl": "Write JSONL file (event record)",
    "first_instance_owns_console": "Restrict console output to the first Logduo instance",
    # --- Loguru ---
    "rotation": "Loguru arg: start new log file when size/time rule is met",
    # If rotation = None, the log file (or 'sink' in Loguru lingo) writes
    # to one file (no rotation)
    "retention": "Loguru arg: remove older rotated log files when rule is met",
    # If retention = None, rotated log files are not pruned.
    # Does NOT prune logs from other runs.
    "compression": "Loguru arg: compress rotated log files (not the active file)",
    "enqueue": "Loguru arg: write logs via a background queue (safer with threads/processes)",
    "catch": "Loguru arg: catch logging errors instead of crashing",
    "backtrace": "Loguru arg: show extended traceback",
    "diagnose": "Loguru arg: include extra context in exception tracebacks",
}


# === Allowed-value (hints for config_table.txt) =============================
# In TOML, booleans are lowercase: true / false, NOT strings, and Cerberus receives True / False
ALLOWED_USER_INPUTS: dict[str, str] = {
    # --- File Management ---
    "log_file_mode": "'write' | 'w' | 'append' | 'a' | 'timestamped' | 't' ",
    "log_file_path": "abs path",
    "log_file_name": "str: valid file name",
    "log_file_layout": "'flat' | 'script' | 'run'",
    "log_dir_path": "str: valid abs path",
    "keep": "'off' | 'int ≥ 1'",

    # --- Formatting ---
    # console
    "console_verbosity": "0 (disabled) | 1 (quiet) | 2 (standard) | 3 (verbose)",
    "console_prefix": "'off' | 'level' | 'timestamp' | 'source'",
    "console_wrap_width": "80 ≤ int ≤ 240",
    "console_header": "Rich str | 'off'",
    "console_footer": "Rich str |'off'",
    "console_color": "True | False",
    "console_theme": "'dark' | 'd' | 'light' | 'l'",
    "console_theme_dict": "dict[str, str]",
    # log
    "log_verbosity": "0 (disabled) | 1 (quiet) | 2 (standard) | 3 (verbose)",
    "log_prefix": "'off' | 'level' | 'timestamp' | 'source'",
    "log_wrap_width": "'off' | 80 ≤ int ≤ 240",
    "log_header": "Rich str | 'off'",
    "log_footer": "Rich str | 'off'",
    # --- Advanced ---
    "show_debug_source": "True | False",
    "show_logger_name": "True | False",
    "show_pid_in_console": "True | False",
    "show_pid_in_log": "True | False",
    "write_config_table": "True | False",
    "write_config_json": "True | False",
    "write_jsonl": "True | False",
    "first_instance_owns_console": "True | False",
    # === Loguru ===
    "rotation": "int (bytes) | str | 'off'",
    "retention": "int (file count) | str | 'off'",
    "compression": "'zip' | 'gz' | 'off'",
    "enqueue": "True | False",
    "catch": "True | False",
    "backtrace": "True | False",
    "diagnose": "True | False",
}


# === Defaults =================================================================
DEFAULTS: dict[str, Any] = {
    # --- File Management ---
    "log_file_mode": "write",
    "log_file_path": "auto",
    "log_file_name": "auto",
    "log_file_layout": "run",
    "log_dir_path": "auto",
    "keep": "off",
    # --- Formatting ---
    # console
    "console_verbosity": 3,
    "console_prefix": "level",
    "console_wrap_width": 120,
    "console_header": "auto",
    "console_footer": "auto",
    "console_color": True,
    "console_theme": "dark",
    "console_theme_dict": {},
    # log
    "log_verbosity": _DEFAULT_LOG_VERBOSITY,
    "log_prefix": "timestamp",
    "log_wrap_width": "off",
    "log_header": "auto",
    "log_footer": "auto",
    # --- Advanced ---
    "show_debug_source": True,
    "show_logger_name": True,
    "show_pid_in_console": False,
    "show_pid_in_log": False,
    "write_config_table": True,
    "write_config_json": False,
    "write_jsonl": False,
    "first_instance_owns_console": False,  # See Notes
    # --- Loguru ---
    "rotation": "off",
    "retention": "off",
    "compression": "off",
    "enqueue": True,
    "catch": True,
    "backtrace": False,
    "diagnose": False,
}


# === CERBERUS_SCHEMA: used by Cerberus to validate user args ==================
# TOML booleans map directly: true → True, false → False
CERBERUS_SCHEMA: dict[str, Any] = {
    # --- File Management ---
    "log_file_mode": {
        "type": "string",
        "allowed": list(_VALID_LOG_FILE_MODES),
        "default": DEFAULTS["log_file_mode"],
        "coerce": _norm_log_file_mode,
    },
    "log_file_path": {
        "type": "string",
        "empty": False,
        "default": DEFAULTS["log_file_path"],
        "coerce": _norm_path_to_string,
    },
    "log_file_name": {"type": "string", "empty": False, "default": DEFAULTS["log_file_name"]},
    "log_file_layout": {
        "type": "string",
        "allowed": list(_VALID_log_file_layoutS),
        "default": DEFAULTS["log_file_layout"],
        "coerce": _norm_str_lower,
    },
    "log_dir_path": {
        "type": "string",
        "empty": False,
        "default": DEFAULTS["log_dir_path"],
        "coerce": _norm_path_to_string,
    },
    "keep": {
        "anyof": [{"type": "string", "allowed": ["off"]}, {"type": "integer", "min": 1}],
        "default": DEFAULTS["keep"],
        "coerce": _norm_str_lower_mixed,
    },
    # --- Formatting ---
    # console
    "console_verbosity": {
        "type": "integer",
        "min": 0,
        "max": 3,
        "default": DEFAULTS["console_verbosity"],
    },
    "console_prefix": {
        "type": "string",
        "allowed": list(_VALID_PREFIX),
        "default": DEFAULTS["console_prefix"],
        "coerce": _norm_str_lower,
    },
    "console_wrap_width": {
        "type": "integer",
        "min": 80,
        "max": 240,
        "default": DEFAULTS["console_wrap_width"],
    },
    "console_header": {"type": "string", "empty": False, "default": DEFAULTS["console_header"]},
    "console_footer": {"type": "string", "empty": False, "default": DEFAULTS["console_footer"]},
    "console_color": {
        "type": "boolean",
        "default": DEFAULTS["console_color"],
        "coerce": _norm_bool,
    },
    "console_theme": {
        "type": "string",
        "allowed": ["dark", "light"],
        "default": DEFAULTS["console_theme"],
        "coerce": _norm_theme,
    },
    "console_theme_dict": {"type": "dict", "default": DEFAULTS["console_theme_dict"]},
    # log
    "log_verbosity": {"type": "integer", "min": 0, "max": 3, "default": DEFAULTS["log_verbosity"]},
    "log_prefix": {
        "type": "string",
        "allowed": list(_VALID_PREFIX),
        "default": DEFAULTS["log_prefix"],
        "coerce": _norm_str_lower,
    },
    "log_wrap_width": {
        "anyof": [
            {"type": "string", "allowed": ["off"]},
            {"type": "integer", "min": 80, "max": 240},
        ],
        "default": DEFAULTS["log_wrap_width"],
        "coerce": _norm_str_lower_mixed,
    },
    "log_header": {"type": "string", "empty": False, "default": DEFAULTS["log_header"]},
    "log_footer": {"type": "string", "empty": False, "default": DEFAULTS["log_footer"]},
    # --- Advanced ---
    "show_debug_source": {
        "type": "boolean",
        "default": DEFAULTS["show_debug_source"],
        "coerce": _norm_bool,
    },
    "show_logger_name": {
        "type": "boolean",
        "default": DEFAULTS["show_logger_name"],
        "coerce": _norm_bool,
    },
    "show_pid_in_console": {
        "type": "boolean",
        "default": DEFAULTS["show_pid_in_console"],
        "coerce": _norm_bool,
    },
    "show_pid_in_log": {
        "type": "boolean",
        "default": DEFAULTS["show_pid_in_log"],
        "coerce": _norm_bool,
    },
    "write_config_table": {
        "type": "boolean",
        "default": DEFAULTS["write_config_table"],
        "coerce": _norm_bool,
    },
    "write_config_json": {
        "type": "boolean",
        "default": DEFAULTS["write_config_json"],
        "coerce": _norm_bool,
    },
    "write_jsonl": {"type": "boolean", "default": DEFAULTS["write_jsonl"], "coerce": _norm_bool},
    "first_instance_owns_console": {
        "type": "boolean",
        "default": DEFAULTS["first_instance_owns_console"],
        "coerce": _norm_bool,
    },
    # --- Loguru ---
    "rotation": {
        "anyof": [{"type": "integer"}, {"type": "string"}],
        "default": DEFAULTS["rotation"],
    },
    "retention": {
        "anyof": [{"type": "integer"}, {"type": "string"}],
        "default": DEFAULTS["retention"],
    },
    "compression": {
        "type": "string",
        "empty": False,
        "allowed": ["zip", "gz", "off"],
        "default": DEFAULTS["compression"],
        "coerce": _norm_str_lower,
    },
    "enqueue": {"type": "boolean", "default": DEFAULTS["enqueue"], "coerce": _norm_bool},
    "catch": {"type": "boolean", "default": DEFAULTS["catch"], "coerce": _norm_bool},
    "backtrace": {"type": "boolean", "default": DEFAULTS["backtrace"], "coerce": _norm_bool},
    "diagnose": {"type": "boolean", "default": DEFAULTS["diagnose"], "coerce": _norm_bool},
}


# === Define groups and order for config_table.txt ===========================
# purposefully left out from groupings:  first_instance_owns_console
GROUPING = {
    # --- Type A: File Management Flags ---
    "file": [
        "log_file_mode",
        "log_file_path",
        "log_file_name",
        "log_file_layout",
        "log_dir_path",
        "keep",

    ],
    # --- Type B: Formatting ---
    "format": [
        # console
        "console_verbosity",
        "console_prefix",
        "console_wrap_width",
        "console_header",
        "console_footer",
        "console_color",
        "console_theme",
        "console_theme_dict",
        # log
        "log_verbosity",
        "log_prefix",
        "log_wrap_width",
        "log_header",
        "log_footer",
    ],
    # --- Type C: Advanced Flags ---
    "advanced": [
        "show_debug_source",
        "show_pid_in_console",
        "show_pid_in_log",
        "show_logger_name",
        "write_config_table",
        "write_config_json",
        "write_jsonl",
        "first_instance_owns_console",
    ],
    # --- Type D: Advanced Engine & Output Control ---
    "loguru": ["rotation", "retention", "compression", "enqueue", "catch", "backtrace", "diagnose"],
}


# === PASSTHROUGHS: reserved for future non-schema keys ========================
PASSTHROUGHS: set[str] = set()


# === SESSION_CONFIG_SPEC: dict of session_config setting dicts and sets =======
SESSION_CONFIG_SPEC = {
    "schema": CERBERUS_SCHEMA,
    "grouping": GROUPING,
    "defaults": DEFAULTS,
    "descriptions": DESCRIPTIONS,
    "allowed_values": ALLOWED_USER_INPUTS,
    "dark_console_theme_dict": _DARK_THEME_COLORS,
    "light_console_theme_dict": _LIGHT_THEME_COLORS,
    "passthroughs": PASSTHROUGHS,
}


# === II. FUNCTIONS ============================================================


# --- logduo_config_hints() ----------------------------------------------------
def _session_config_hints(field: str, defaults: dict) -> str:  # noqa: PLR0911  # many returns
    # --- File Management (bools at end)---
    if field == "log_file_mode":
        return "must be 'write' (or 'w'), 'append' (or 'a'), 'timestamped' (or 't')"
    if field == "log_file_path":
        return "must be an absolute path (str or pathlib.Path)"
    if field == "log_file_layout":
        return "must be 'flat', 'script', or 'run'"
    if field == "log_dir_path":
        return "must be an absolute path (str or pathlib.Path)"
    if field == "log_file_name":
        return (
            "must be a valid file name "
            "(no '/' or '\\', no control characters, "
            "no leading/trailing spaces, and not '.' or '..')"
        )
    if field == "keep":
        return "must be 'off' or an integer ≥ 1"

    # --- Formatting (bools at end) ---
    # console
    if field == "console_verbosity":
        return "must be 0 (off), 1 (minimal), 2 (standard), or 3 (verbose)"
    if field == "console_prefix":
        return "must be 'off', 'level', 'timestamp', or 'source'"
    if field == "console_wrap_width":
        return "must be an integer: 80 ≤ value ≤ 240"
    if field in {"console_header", "console_footer"}:
        return "must be 'off', or a non-empty string"
    if field == "console_theme":
        return "must be 'dark', 'd', 'light', or 'l'"
    if field == "console_theme_dict":
        return (
            "must be a dict mapping semantic keys to style strings "
            "(e.g. {'warning': 'bold yellow'})"
        )
    # log
    if field == "log_verbosity":
        return "must be 0 (off), 1 (minimal), 2 (standard), or 3 (verbose)"
    if field == "log_prefix":
        return "must be 'off', 'level', 'timestamp', or 'source'"
    if field == "log_wrap_width":
        return "must be 'off' or an integer: 80 ≤ value ≤ 240"
    if field in {"log_header", "log_footer"}:
        return "must be 'off', or a non-empty string"

    # -- Advanced (bools at bottom) ---

    # --- Loguru (bools at bottom) ---
    if field == "rotation":
        return (
            "must be an integer (bytes), a size string "
            "(e.g. '16 MB', '500 KB'), or a duration string "
            "(e.g. '1 day', '12 hours')"
        )
    if field == "retention":
        return (
            "must be an integer (file count), a duration string "
            "(e.g. '10 days', '1 week'), or 'off'"
        )
    if field == "compression":
        return "must be 'zip', 'gz', or 'off'"

    # --- Bool Hints ---
    if field in {
        # --- Formatting ---
        "console_color",
        # ---Advanced ---
        "show_debug_source",
        "show_logger_name",
        "show_pid_in_console",
        "show_pid_in_log",
        "write_config_table",
        "write_config_json",
        "write_jsonl",
        "first_instance_owns_console",
        # --- Loguru ---
        "enqueue",
        "catch",
        "backtrace",
        "diagnose",
    }:
        return _bool_hint(field, defaults)

    return "invalid value"
