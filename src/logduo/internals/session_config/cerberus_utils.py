"""
cerberus_utils.py

Validation helpers for Cerberus normalization and config validation.

Note:
- Validator normalization avoids string "none" → None coercion.

Last edited: 2026-5-27
"""

from pathlib import Path


# --- _norm_bool() -------------------------------------------------------------
def _norm_bool(v: object) -> bool | None:
    """
    Normalize common boolean-like inputs into Python bool values.
    Return None if input is None or unrecognized.
    """
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s == "true":
            return True
        if s == "false":
            return False
    return None


# --- _bool_hint() -------------------------------------------------------------
def _bool_hint(field: str, defaults: dict) -> str:
    return (
        "must be a boolean "
        "(true/false in TOML, True/False in Python) "
        f"(default: {defaults.get(field)!r})"
    )


# --- _norm_str_lower() --------------------------------------------------------
def _norm_str_lower(v: object) -> str | None:
    """Normalize a single string: strip whitespace and lower-case.
    Return None if input is None or not a string."""
    if v is None:
        return None
    if not isinstance(v, str):
        return None
    s = v.strip().lower()
    return s if s else None


# --- _norm_str_lower_mixed() --------------------------------------------------
def _norm_str_lower_mixed(v: object) -> object:
    if isinstance(v, str):
        return v.strip().lower()
    return v


# --- _norm_theme() ------------------------------------------------------------
def _norm_theme(s: object) -> object:
    if not isinstance(s, str):
        return s
    v = s.strip().lower()
    mapping = {"dark": "dark", "d": "dark", "light": "light", "l": "light"}
    return mapping.get(v, v)


# --- _norm_log_file_mode() ----------------------------------------------------
def _norm_log_file_mode(value: str) -> str:
    """
    Normalize shorthand log_file_mode values.

    Accepted:
        a → append
        w → write
        t → timestamped
    """

    if not isinstance(value, str):
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR: _norm_log_file_mode() expected str, got {type(value).__name__}"
        )
    v = value.strip().lower()

    mapping = {
        "a": "append",
        "append": "append",
        "w": "write",
        "write": "write",
        "t": "timestamped",
        "timestamped": "timestamped",
    }

    return mapping.get(v, v)


# --- _norm_path_to_string() ---------------------------------------------------
def _norm_path_to_string(v: object) -> object:
    """
    Normalize pathlib.Path values to strings for Cerberus validation.

    - Path -> str(path)
    - str  -> unchanged
    - other types -> unchanged
    """
    if isinstance(v, Path):
        return str(v)

    return v
