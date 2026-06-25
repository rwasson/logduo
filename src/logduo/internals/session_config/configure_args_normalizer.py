"""
configure_args_normalizer.py

Cerberus Validation + Coercion + merge pipeline

Merge precedence:
schema defaults -> TOML -> configure args (from script or interactive session)

Responsibilities:
- load pyproject.toml
- validate arg sources independently
- normalize/coerce values through Cerberus
- merge resolved arg layers
- track arg source provenance

Last edited: 2026-05-27
"""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import cerberus


# --- _normalize_configure_args_with_defaults_and_toml() -------------------------------------------------
def _normalize_configure_args_with_defaults_and_toml(
    *,
    toml_path_abs: Path | None,
    configure_args: dict[str, Any],
    session_config_spec: dict[str, Any],
    session_config_hints: Callable[[str, dict[str, Any]], str] | None = None,
) -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    """
    Normalize (validate + coerce) and merge logduo args from all session sources.
    Merge order: schema defaults -> TOML -> configure args
    """
    schema = session_config_spec["schema"]
    validator = cerberus.Validator(schema, allow_unknown=False)
    # Apply schema defaults to an empty config - for comparison for each source
    schema_defaults = validator.normalized({}) or {}

    # start with schema_defaults
    normalized_session_args: dict[str, Any] = dict(schema_defaults)
    arg_source_dict: dict[str, str] = {key: "default" for key in schema_defaults}

    # --- session config hints ---
    if session_config_hints is None:

        def session_config_hints(invalid_field: str, default_values: dict[str, Any]) -> str:
            _ = invalid_field
            _ = default_values
            return "invalid value"

    # ---logduo args in pyproject.toml  ---
    toml_args, toml_record = _load_toml_args(
        toml_path_abs=toml_path_abs, project_name="logduo", schema=schema
    )

    normalized_toml_args = _normalize_args_from_one_source(
        source_label="TOML Error",
        source_name="[tool.logduo]",
        source=toml_args,
        schema=schema,
        schema_defaults=schema_defaults,
        session_config_hints=session_config_hints,
    )
    toml_record["toml_args_used"] = bool(normalized_toml_args)

    # --- logduo args from log.configure()  ---
    normalized_configure_args = _normalize_args_from_one_source(
        source_label="Configure Error",
        source_name="configure args",
        source=configure_args,
        schema=schema,
        schema_defaults=schema_defaults,
        session_config_hints=session_config_hints,
    )

    # --- merge args from sources ---
    for key, value in normalized_toml_args.items():
        normalized_session_args[key] = value
        arg_source_dict[key] = "toml"

    for key, value in normalized_configure_args.items():
        normalized_session_args[key] = value
        arg_source_dict[key] = "configure"

    return normalized_session_args, arg_source_dict, toml_record


# --- _load_toml_args() --------------------------------------------------------
def _load_toml_args(
    *, toml_path_abs: Path | None, project_name: str, schema: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:

    toml_record: dict[str, Any] = {
        "toml_file_path": (str(toml_path_abs) if toml_path_abs else None),
        "has_pyproject": False,
        "has_tool_table": False,
        "toml_keys": [],
    }

    if toml_path_abs is None:
        return {}, toml_record

    if not toml_path_abs.is_file():
        return {}, toml_record

    toml_record["has_pyproject"] = True

    try:
        raw_text = toml_path_abs.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as e:
        raise RuntimeError(
            f"TOML Error:\n\nCould not read pyproject.toml:\n  {toml_path_abs}\n\n{e}"
        ) from e

    try:
        data = tomllib.loads(raw_text) or {}
    except tomllib.TOMLDecodeError as e:
        lineno = getattr(e, "lineno", "?")
        colno = getattr(e, "colno", "?")
        raise RuntimeError(
            f"TOML Error:\n\npyproject.toml syntax error (line {lineno}, column {colno}):\n\n{e}"
        ) from e

    tool_table = data.get("tool", {}).get(project_name)

    if tool_table is None:
        return {}, toml_record
    if not isinstance(tool_table, dict):
        raise RuntimeError(f"TOML Error:\n\n[tool.{project_name}] must be a TOML table.")

    toml_record["has_tool_table"] = True
    toml_keys = sorted(str(key) for key in tool_table.keys())

    toml_record["toml_keys"] = toml_keys
    unknown_keys = sorted(key for key in tool_table.keys() if key not in schema)

    if unknown_keys:
        joined = ", ".join(unknown_keys)
        raise RuntimeError(f"TOML Error:\n\nUnknown key(s) in [tool.{project_name}]:\n  {joined}")

    return dict(tool_table), toml_record


# --- _normalize_args_from_one_source() --------------------------------
def _normalize_args_from_one_source(
    *,
    source_label: str,
    source_name: str,
    source: dict[str, Any],
    schema: dict[str, Any],
    schema_defaults: dict[str, Any],
    session_config_hints: Callable[[str, dict[str, Any]], str],
) -> dict[str, Any]:
    """
    Normalize (validate and coerce) args from a single config source (using Cerberus).
    """

    if not source:
        return {}

    validator = cerberus.Validator(schema, allow_unknown=False)
    is_valid = validator.validate(source)

    normalized_full = validator.document or {}
    normalized = {key: normalized_full[key] for key in source if key in normalized_full}

    if is_valid:
        return normalized

    error_lines = [f"{source_label}:", "", f"Invalid values in {source_name}:", ""]

    for field, errors in validator.errors.items():
        value = source.get(field)
        hint = session_config_hints(field, schema_defaults)
        error_lines.append(f"{field} = {value!r}")
        error_lines.append("  Validation error:")
        error_lines.append(f"    {errors}")

        if hint:
            error_lines.append("  Hint:")
            error_lines.append(f"    {hint}")
        error_lines.append("")

    raise RuntimeError("\n".join(error_lines))
