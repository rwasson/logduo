"""
reshape_dict_rows.py


NOTE:
    This is a lightweight inspection helper, not a general-purpose
    object pretty-printer.

    Intended for:
        - small config objects
        - dataclasses
        - dict-like objects
        - debugging helpers
        - log-safe structured inspection

    Supported inputs:
        - dict
        - dataclass instances
        - dataclass types

    Nested objects are intentionally rendered using repr()
    rather than recursively expanded.

    This module is designed to produce deterministic,
    plain-text-safe output suitable for logs and artifacts.


Last edited: 2026-5-27
"""

from collections.abc import Iterable
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path
from typing import Any, cast


# --- _reshape_dict_obj_to_dict_rows() ---------------------------------------------------
def _reshape_dict_obj_to_dict_rows(
    obj: object,
) -> tuple[list[dict[str, str]] | None, list[str] | None]:
    items: Iterable[tuple[str, object]]
    if isinstance(obj, dict):
        items = obj.items()
        header_labels = ["Field", "Value"]
    elif is_dataclass(obj) and not isinstance(obj, type):
        obj_dataclass_instance = cast(Any, obj)
        items = asdict(obj_dataclass_instance).items()
        header_labels = ["Field", "Value"]
    elif isinstance(obj, type) and is_dataclass(obj):
        obj_dataclass_type = cast(Any, obj)
        items = ((f.name, f.type) for f in fields(obj_dataclass_type))
        header_labels = ["Field", "Type"]
    else:
        return None, None


    rows: list[dict[str, str]] = []

    for key, value in items:
        rows.append(
            {
                "field": str(key),
                "value": _display_dict_value(value),
            }
        )

    return rows, header_labels


# === Internal  helpers ========================================================

# --- _display_dict_value() ----------------------------------------------------
def _display_dict_value(value: Any) -> str:  # noqa: PLR0911
    if value is None:
        return "None"

    if isinstance(value, type):
        return value.__name__

    if isinstance(value, (int, float, bool, Path)):
        return str(value)

    if isinstance(value, str):
        if "\n" in value:
            return f"<str ({len(value.splitlines())} lines)>"
        return value

    if isinstance(value, dict):
        return f"<dict ({len(value)})>"

    if isinstance(value, (list, tuple, set)):
        return f"<{type(value).__name__} ({len(value)})>"

    return f"<{type(value).__name__}>"
