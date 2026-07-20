"""
build_config_table.py

Builds config_table.txt table rows and footnotes from resolved
global configuration and runtime state.

Responsible for:
- compact table display formatting
- value normalization for display
- path/theme footnote expansion

Last edited: 2026-5-27
"""


from pathlib import Path
from typing import Any

from logduo.internals.engine.runtime_classes import RuntimeRecord
from logduo.internals.session_config.session_config_classes import SessionConfig
from logduo.internals.session_config.session_constants import (
    _DARK_THEME_COLORS,
    _DEFAULT_CONFIG_TABLE_WIDTH,
    _LIGHT_THEME_COLORS,
)
from logduo.utils.table.text_table import text_table
from logduo.utils.wrap.wrap_text import strip_ansi, wrap_text

_CONFIG_TABLE_WRAP_WIDTH = 120
_CONFIG_TABLE_DEFAULT_MAX_CELL_LINES = 5
_CONFIG_TABLE_PADDING = 2
_CONFIG_TABLE_PATH_INDENT = 20


# === Constants ===============================================================
TABLE_COLUMNS = [
    "field",
    "group",
    "value",
    "arg_source",
    #  "default",
    "description",
    "allowed",
    #   "type",
]

TABLE_HEADERS = [
    "Field",
    "Group",
    "Value",
    "Source",
    #   "Default",
    "Description",
    "Allowed",
    #   "Type",
]

# fields collapsed to "long" in compact table display
LONG_FIELDS: set[str] = {
    "console_header",
    "console_footer",
    "log_header",
    "log_footer",
    "console_theme_dict",
    "log_dir_path",
    "log_file_path",
    "log_file_name",
    "toml_file_path",
}

# long fields that preserve explicit "off"
OFF_FIELDS: set[str] = {"console_header", "console_footer", "log_header", "log_footer"}


SOURCE_DISPLAY = {
    "default": "default",
    "interactive_forced": "forced",
    "configure": "configure",
    "toml": "toml",
    "cli": "CLI",
    "forced": "forced",  # use for policy override
}

# fields expanded in Footnotes section
FOOTNOTE_PATH_FIELDS: set[str] = {"log_dir_path", "log_file_path", "toml_file_path"}

RESOLVED_FOOTNOTE_PATH_FIELD_MAP = {
    "log_dir_path": "main_sink_log_dir_path_abs",
    "log_file_path": "main_sink_log_file_path_abs",
    "toml_file_path": "toml_path_abs",
}


# --- _build_session_config_class_instance_table_rows() ---------------------------------------
def _build_session_config_class_instance_table_rows(
    *,
    session_config: SessionConfig,
    arg_source_dict: dict[str, str],
    session_config_spec: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Build rows for the logduo session_config table / JSON.

    Each row:
        field | group | type | value | arg_source | default | description | allowed
    """
    grouping: dict[str, list[str]] = session_config_spec.get("grouping", {})
    defaults: dict[str, Any] = session_config_spec.get("defaults", {})
    descriptions: dict[str, str] = session_config_spec.get("descriptions", {})
    allowed_values: dict[str, str] = session_config_spec.get("allowed_values", {})

    def _row(field: str, group: str) -> dict[str, Any]:
        default_val = defaults.get(field, None)
        value = getattr(session_config, field, default_val)

        arg_source = arg_source_dict.get(field)
        if arg_source is None:
            raise RuntimeError(f"LOGDUO INTERNAL ERROR: missing arg_source for field '{field}'")

        return {
            "field": field,
            "group": group,
            "type": type(value).__name__ if value is not None else "NoneType",
            "value": value,
            "arg_source": arg_source,
            "default": default_val,
            "description": descriptions.get(field, ""),
            "allowed": allowed_values.get(field, ""),
        }

    rows: list[dict[str, Any]] = []

    # 1) Fields in the order provided by `grouping`
    for group_name, fields in grouping.items():
        for f in fields:
            rows.append(_row(f, group_name))

    # 2) (Intentionally *not* adding “other” fields – session_config.json  is for user-facing settings.)
    # footnotes = [f for f in session_config.keys() if f not in seen and not f.startswith("__")]
    # for f in sorted(footnotes):
    #     rows.append(_row(f, "other"))

    return rows


# --- _build_session_config_class_instance_txt() ----------------------------------------------
def _build_session_config_class_instance_txt(
    *,
    session_config: SessionConfig,
    runtime: RuntimeRecord,
    toml_record: dict[str, Any],
    rows: list[dict[str, Any]],
    title: str = "Logduo Configuration",
    subtitle: str | None,
    max_col_widths: list[int],
    max_cell_lines: int = _CONFIG_TABLE_DEFAULT_MAX_CELL_LINES,
    wrap_table_width: int = _CONFIG_TABLE_WRAP_WIDTH,
) -> str:
    """Return session_config table text."""

    display_rows = [_format_display_row(row, session_config=session_config) for row in rows]

    table = text_table(
        rows=display_rows,
        columns=TABLE_COLUMNS,
        title=title,
        subtitle=subtitle,
        first_row_is_header=False,
        header_labels=TABLE_HEADERS,
        max_col_widths=max_col_widths,
        max_cell_lines=max_cell_lines,
        wrap_table=True,
        wrap_table_width=wrap_table_width,
        padding=_CONFIG_TABLE_PADDING,
    )

    table_text = strip_ansi(table) if table is not None else ""

    footnotes = _build_footnote_list(
        session_config=session_config, runtime=runtime, toml_record=toml_record
    )

    if not footnotes:
        return table_text

    footnotes_block = "Footnotes\n────────────────────────\n" + "\n".join(footnotes)

    return f"{table_text}\n\n{footnotes_block}\n"


# === Helpers =================================================================
def _format_display_row(row: dict[str, Any], *, session_config: SessionConfig) -> dict[str, Any]:

    display_row = dict(row)
    field = display_row.get("field")
    value = display_row.get("value")

    # --- arg_source display ---
    raw_arg_source = display_row["arg_source"]
    assert isinstance(raw_arg_source, str)

    display_row["arg_source"] = SOURCE_DISPLAY.get(
        raw_arg_source
        #   raw_arg_source,
    )

    display_value: Any
    if field in {"rotation", "retention", "compression"} and value is None:
        display_value = "off"
    else:
        display_value = value
    show_footnote_marker = False

    # --- collapse large values for compact table display ---
    if field in LONG_FIELDS:
        if field in OFF_FIELDS and value == "off":
            display_value = "off"
        else:
            display_value = "..."

        # --- runtime-resolved values shown in footnotes ---
        if field in FOOTNOTE_PATH_FIELDS:
            show_footnote_marker = True

        # --- console theme dict special handling ---
        if field == "console_theme_dict":
            info = _get_theme_dict_display_info(session_config)
            display_row["default"] = "theme_dict"
            if info["is_custom"]:
                display_value = "user_dict"
                show_footnote_marker = True
            else:
                display_value = info["preset_label"]

    if show_footnote_marker:
        display_row["value"] = f"{display_value}*"
    else:
        display_row["value"] = display_value

    type_val = display_row.get("type")
    if type_val == "NoneType":
        display_row["type"] = "off"
    elif type_val in {"mappingproxy", "MappingProxyType"}:
        display_row["type"] = "dict"

    return display_row


# --- _get_runtime_path_value() -----------------------------------------------
def _get_runtime_path_value(field: str, runtime: RuntimeRecord) -> Any:
    """
    Return canonical runtime path value for a config path field.
    """
    runtime_attr = RESOLVED_FOOTNOTE_PATH_FIELD_MAP.get(field)
    if runtime_attr is None:
        return None
    return getattr(runtime, runtime_attr, None)


# --- _get_theme_dict_display_info() ------------------------------------------
def _get_theme_dict_display_info(session_config: SessionConfig) -> dict[str, Any]:
    """
    Return display metadata for console_theme_dict.
    """

    value = session_config.console_theme_dict
    theme = session_config.console_theme

    if theme == "light":
        base_theme = _LIGHT_THEME_COLORS
        preset_label = "light_dict"
    else:
        base_theme = _DARK_THEME_COLORS
        preset_label = "dark_dict"

    is_custom = value != base_theme

    return {"value": value, "is_custom": is_custom, "preset_label": preset_label}


# --- _get_toml_display_value() -----------------------------------------------
def _get_toml_display_value(toml_record: dict[str, Any]) -> str | Path:
    """
    Return human-readable TOML discovery status for config_table.txt.

    Possible states:
        - pyproject.toml not discovered
        - pyproject.toml exists but no [tool.logduo] table
        - valid TOML path in use
    """

    has_pyproject = toml_record.get("has_pyproject", False)
    has_tool_table = toml_record.get("has_tool_table", False)
    toml_file_path = toml_record.get("toml_file_path")

    # --- no pyproject.toml discovered ---
    if not has_pyproject:
        return "not found"

    # --- pyproject.toml exists but no [tool.logduo] table ---
    if not has_tool_table:
        return "no [tool.logduo] table"

    # --- valid TOML config path ---
    if toml_file_path:
        return Path(toml_file_path).resolve()

    return "unknown"


# --- _build_footnote_list() ---------------------------------------------------
def _build_footnote_list(
    *, toml_record: dict[str, Any], session_config: SessionConfig, runtime: RuntimeRecord
) -> list[str]:

    footnotes: list[str] = []

    # --- Note on display of long values  ---
    k = 1
    footnotes.append(
        f"{k}. In the 'Value' column, fields too large to fit in the table are shown as:"
    )
    footnotes.append("    ...  — full value omitted for readability")
    footnotes.append("    ...* — full value shown below")

    # --- Paths ---
    field_width = max(len(f) for f in FOOTNOTE_PATH_FIELDS)
    k += 1
    path_lines: list[str] = []
    path_fields = ["log_dir_path", "log_file_path"]

    project_dir_path_abs = runtime.project_dir_path_abs

    if project_dir_path_abs is None:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: project_dir_path_abs not set."
        )
    path_anchor_dir = project_dir_path_abs.parent

    for field in path_fields:
        raw_val = _get_runtime_path_value(field, runtime)
        if raw_val is None:
            display_value = "None"
        else:
            try:
                display_value = str(
                    raw_val.relative_to(path_anchor_dir)
                )
            except ValueError:
                display_value = str(raw_val)
        path_line = f"{field:<{field_width}} = {display_value}"
        path_lines.extend(
            wrap_text(
                path_line,
                width=_DEFAULT_CONFIG_TABLE_WIDTH - _CONFIG_TABLE_PATH_INDENT,
                continuation_width=_DEFAULT_CONFIG_TABLE_WIDTH - _CONFIG_TABLE_PATH_INDENT,
                hanging_indent=field_width + len(" = ") + 2,
            )
        )

    footnotes.append(f"{k}. Paths*:")
    footnotes.extend(f"    {line}" for line in path_lines)

    # toml_info contains toml status (str) if path not found, or args not used
    toml_info = _get_toml_display_value(toml_record)
    toml_prefix = "    toml_file_path = "

    if isinstance(toml_info, Path):
        try:
            display_toml_value = str(
                toml_info.relative_to(path_anchor_dir)
            )
        except ValueError:
            display_toml_value = str(toml_info)

        footnotes.extend(
            wrap_text(
                toml_prefix + display_toml_value,
                width=_DEFAULT_CONFIG_TABLE_WIDTH,
                continuation_width=_DEFAULT_CONFIG_TABLE_WIDTH,
                hanging_indent=len(toml_prefix) + 2,
            )
        )
    else:
        footnotes.append(toml_prefix + str(toml_info))

    # --- Theme colors (if custom) ---
    k += 1
    theme_info = _get_theme_dict_display_info(session_config)

    if theme_info["is_custom"]:
        footnotes.append(f"{k}. Custom theme colors*:")
        footnotes.append("    console_theme_dict =")
        for color_key, v in dict(theme_info["value"]).items():
            footnotes.append(f"      {color_key:<18} {v}")

    return footnotes
