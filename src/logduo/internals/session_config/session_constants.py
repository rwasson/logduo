"""
session_constants.py

Last edited: 2026-5-27
"""

import re
from typing import Literal


# === Runtime lifecycle ========================================================
class _NotGiven:
    """
    Sentinel for omitted user arguments.
    """
    pass


_NOT_GIVEN = _NotGiven()


# --- Timestamp formatting ---
_SESSION_TIMESTAMP_FMT = "%Y_%m_%d__%H_%M_%S"
_SESSION_DISPLAY_TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"
_LINE_TIMESTAMP_FMT = "%H:%M:%S.%f"  # microseconds; later trimmed to ms

_VALID_SESSION_STATE = Literal[
    "initializing",
    "setting_up_config",
    "setting_up_sinks",
    "running",
    "closing",  # state cleared after this
]


# === Public API Names =========================================================
_PACKAGE_NAME = "logduo"
_PUBLIC_UTILITY_NAMES = ("run", "table_text")
_PUBLIC_API_NAMES = (
    # session management
    "configure",
    "join",
    "close",

    # logging levels in _VALID_LEVELS

    # logging extensions
    "exception",  # log level ERROR + Traceback
    "new_level",
    "new_logger",
    "new_loguru_sink",

    # discovery helpers
    "export_logduo_docs",
    "session_config",      # immutable config, safe for inspection
    "output_dir_path",     # immutable saved path
    "main_log_file_path"   # immutable saved path
)


# === Loguru  ========================x==========================================
# Logduo validated against Loguru 0.7.x add() arguments.
# Logduo validates and forwards Loguru add() arguments.
# Keep this list synchronized with the bundled/tested
# Loguru version.
_VALID_LOGURU_ADD_KWARGS = {
    "level",
    "format",
    "filter",
    "colorize",
    "serialize",
    "backtrace",
    "diagnose",
    "enqueue",
    "catch",
    "rotation",
    "retention",
    "compression",
    "delay",
    "watch",
    "mode",
    "buffering",
    "encoding",
    "errors",
}


# === Levels and verbosity =====================================================
# --- Levels ---
# tuple (immutable list with display order maintained)
_VALID_LEVELS = {"CRITICAL", "ERROR", "WARNING", "SUCCESS", "INFO", "DEBUG", "TRACE"}
_MAX_LEVEL_WIDTH = max(len(level) for level in _VALID_LEVELS)
_LEVEL_RANK: dict[str, int] = {
    "CRITICAL": 1,
    "ERROR": 1,
    "WARNING": 1,
    "SUCCESS": 2,
    "INFO": 2,
    "DEBUG": 3,
    "TRACE": 3,
}
_VALID_VERBOSITY_LEVELS = {0, 1, 2, 3}
type VerbosityLevelType = Literal[0, 1, 2, 3]
_MAX_VERBOSITY_LEVEL = 3


# === Sink and routing kinds ===================================================
# file_kind is a field in CreatedFileRecord used by dispatcher/setup/close
_VALID_FILE_KIND = {"artifact", "main_sink_log", "user_sink_log", "jsonl", "loguru_log"}
type FileKindType = Literal[
    "artifact", "main_sink_log", "user_sink_log", "jsonl", "loguru_log"
]
type TargetKindType = Literal["console", "main_sink_log", "user_sink_log", "jsonl"]
type LogKindType = Literal["main_sink_log", "user_sink_log"]

_RESERVED_SINK_STEMS = {
    # --- core system / routing ---
    "main_sink",
    "main_sink_log",
    "console",
    "jsonl",
    "system",
    # --- artifacts / generated ---
    "session_config",
    # --- internal grouping (optional, but safer to keep) ---
    "user_sink",
    "user_sink_log",
}


# === Config value domains =====================================================
_DEFAULT_LOG_VERBOSITY = 2
_VALID_PREFIX = {"off", "level", "timestamp", "source"}
_VALID_LOG_FILE_MODES = {"write", "append", "timestamped"}
_VALID_LOG_DIR_LAYOUTS = {"flat", "script", "run"}
type PrefixType = Literal["off", "level", "timestamp", "source"]
type LogFileModeType = Literal["write", "append", "timestamped"]
type LogDirLayoutType = Literal["flat", "script", "run"]


# === Validation and naming ===================================================
_LOG_FILE_NAME_RE = re.compile(r'^(?!\.{1,2}$)[^\x00-\x1f<>:"/\\|?*]+$')
_VALID_SINK_STEM_NAME_RE = re.compile(r"^[a-z0-9_]{1,32}$")  # strict
_RESERVED_LABELS = {"PRINT", "CONSOLE", "EXCEPTION"} | _VALID_LEVELS


# === Layout and wrapping ======================================================
_RULE_CHAR = "─"  # Unicode: "\u2500"   or "═"   # Unicode: "\u2550"
_DIVIDER_WIDTH = 55
_PID_FIELD_WIDTH = 7  # Long enough to fit PID's from any OS
_CALLSITE_MAX_SOURCE_DISPLAY_WIDTH = 25
_CALLSITE_MAX_LINE_NUM_DISPLAY_WIDTH = 9
_SINK_TAG_WIDTH = _MAX_LEVEL_WIDTH + 2
_NO_WRAP_WIDTH = 100000  # log_wrap_width when wrapping not desired
_LOGURU_DISPLAY_ORDER = 100000  # ensure loguru files shown last in created file lists
_MIN_WRAP_WIDTH = 80
_TRACEBACK_PATH_WIDTH = 80
_TRACEBACK_MAX_PARENTS = 4
_DEFAULT_SHORT_PATH_WIDTH = 120
_DEFAULT_SHORT_PATH_MAX_PARENTS = 6


# === Themes ===================================================================
_LIGHT_THEME_COLORS: dict[str, str] = {
    "title": "bold bright_blue",
    "header_label": "bright_blue",
    "header_value": "grey37",
    "text": "black",
    "muted": "grey39",
    "divider": "blue3",
    "pipe": "grey70",
    "sink_tag": "bright_blue",
    "critical": "bold red3",
    "error": "red3",
    "warning": "bold gold3",
    "success": "green",
    "info": "grey39",
    "debug": "bold magenta",
    "trace": "grey39",
}

_DARK_THEME_COLORS = {
    "title": "bold bright_cyan",
    "header_label": "bright_cyan",
    "header_value": "grey70",
    "text": "white",
    "muted": "grey58",
    "divider": "cyan",
    "pipe": "grey50",
    "sink_tag": "bright_cyan",
    "critical": "bold red",
    "error": "bold red",
    "warning": "bold yellow",
    "success": "bold bright_green",
    "info": "grey58",
    "debug": "bold magenta",
    "trace": "bold grey70",
}
