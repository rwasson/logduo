"""
console_header_footer_builders.py

# "_build_auto_*" helpers generate auto-generated info subcomponents

Note: in scrolling console output window environments, line dividers look heavy.
Line dividers are currently commented out in console, but still displayed in logs.


Last edited: 2026-5-27
"""

from collections.abc import Mapping
from pathlib import Path

from rich.errors import MarkupError
from rich.text import Text

from logduo.internals.engine.runtime_classes import RuntimeRecord
from logduo.internals.formatters.header_footer_formatters import (
    _build_auto_footer_created_file_lists,
    _build_auto_footer_info_rows,
    _build_auto_header_info_rows,
    _build_shortened_file_path_display_label,
    _derive_label_pad,
)
from logduo.internals.session_config.session_constants import (
    _DEFAULT_SHORT_PATH_MAX_PARENTS,
    _DIVIDER_WIDTH,
    _RULE_CHAR,
)


# --- _build_console_header() --------------------------------------------------
def _build_console_header(
    *, runtime: RuntimeRecord, console_header: str, styles: Mapping[str, str]
) -> Text | None:
    """
    Build the resolved header payload for console output.

    Returns:
        Text: Fully prepared console header payload.
        None: No header should be emitted.

    Notes
    -----
    This function ONLY builds payload text.
    Actual emission is handled later through:
        _safe_console_print()
    Supports:
        - explicit custom headers
        - auto-generated headers
        - disabled headers ("off")
        - different headers depending on whether session is interactive or script
    """

    # --- resolve console_header policy ---
    console_header_arg = console_header.strip().lower()

    # --- disabled ---
    if console_header_arg == "off":
        return None

    # --- explicit custom header ---
    if console_header_arg != "auto":
        try:
            header_text = Text.from_markup(console_header.rstrip("\n"))

        except MarkupError:
            header_text = Text(console_header.rstrip("\n"))

        return Text("\n").join([header_text, Text("")])

    # --- auto-generated console header ---
    label_style = styles.get("header_label") or "blue"
    value_style = styles.get("header_value") or "black"

    assert runtime.main_sink_log_file_path_abs is not None
    main_log_file_name = Path(runtime.main_sink_log_file_path_abs).name
    rows = _build_auto_header_info_rows(
        runtime=runtime, file_name=main_log_file_name, is_log_file=False
    )
    label_pad = _derive_label_pad(rows)

    lines: list[Text] = []

    for label, value in rows:
        # --- standalone title row ---
        if label is None:
            lines.append(Text(value, style=value_style))

        # --- standard label/value row ---
        else:
            lines.append(
                _render_rich_label_value_row(
                    label,
                    value,
                    label_style=label_style,
                    value_style=value_style,
                    label_pad=label_pad,
                )
            )

    return Text("\n").join(lines)


# --- _build_console_footer() --------------------------------------------------
def _build_console_footer(
    *,
    runtime: RuntimeRecord,
    console_footer: str,
    console_wrap_width: int,
    styles: Mapping[str, str],
    show_created_files: bool,
) -> Text | None:
    """
    Build the resolved footer payload for console output.

    Returns:
        Text: Fully prepared console footer payload.
        None: No footer should be emitted.

    Notes
    -----
    This function ONLY builds payload text.
    Actual emission is handled later through:
        _safe_console_print()
    Supports:
        - explicit custom footers
        - auto-generated footers
        - disabled footers ("off")
        - different footer depending on whether session is interactive or script
    """

    # --- resolve console_footer policy ---
    console_footer_arg = console_footer.strip().lower()

    # --- disabled ---
    if console_footer_arg == "off":
        return None

    # --- explicit custom footer ---
    if console_footer_arg != "auto":
        try:
            footer_text = Text.from_markup(console_footer.rstrip("\n"))
        except MarkupError:
            footer_text = Text(console_footer.rstrip("\n"))

        return Text("\n").join([footer_text, Text("")])

    # --- Auto-generated console footer ---

    # --- created/missing file lists ---
    created_files, missing_files = _build_auto_footer_created_file_lists(runtime)
    created_files = sorted(created_files, key=lambda cf: cf.display_order)
    missing_files = sorted(missing_files, key=lambda cf: cf.display_order)

    # --- formatting ---
    full_line_width = console_wrap_width

    # info block path values begin after padded labels
    info_row_path_display_width = console_wrap_width - len("pyproject.toml path:  ")

    # subtracted from available line width for created and missing file lists
    len_append_suffix = len(" (append)")

    label_style = styles.get("header_label") or "blue"
    value_style = styles.get("header_value") or "black"
    divider_style = styles.get("divider") or "blue"

    divider_line = _RULE_CHAR * _DIVIDER_WIDTH
    divider_text = Text(divider_line, style=divider_style)

    rows = _build_auto_footer_info_rows(
        runtime=runtime,
        path_display_width=info_row_path_display_width,
        anchor_dir=runtime.project_dir_path_abs,
        max_parents=_DEFAULT_SHORT_PATH_MAX_PARENTS,
        is_main_sink=True,
    )
    label_pad = _derive_label_pad(rows)
    lines: list[Text] = [divider_text]

    # --- info footer rows ---
    for label, value in rows:
        lines.append(
            _render_rich_label_value_row(
                label, value, label_style=label_style, value_style=value_style, label_pad=label_pad
            )
        )

    # --- append created files list ---
    if show_created_files and created_files:
        lines.append(Text(""))
        lines.append(Text("Logduo-managed files created this run:", style=label_style))

        # created file block's path values are displayed flush left
        # created_file_path_display_width = full_line_path_display_width
        for cfr in created_files:
            display_anchor_dir = runtime.project_dir_path_abs or cfr.path.parent
            label = _build_shortened_file_path_display_label(
                cfr.path,
                path_display_width=full_line_width - len_append_suffix,
                anchor_dir=display_anchor_dir,
                max_parents=_DEFAULT_SHORT_PATH_MAX_PARENTS,
            )

            if cfr.log_file_mode == "append":
                label = f"{label} (append)"

            lines.append(Text(label, style=value_style))

    # --- append missing files ---
    if missing_files:
        lines.append(Text(""))
        lines.append(Text("WARNING: Some registered files were missing on disk:", style="bold red"))

        # missing file block's path values are displayed flush left
        # missing_file_path_display_width = full_line__width

        for cfr in missing_files:
            display_anchor_dir = runtime.project_dir_path_abs or cfr.path.parent

            label = _build_shortened_file_path_display_label(
                cfr.path,
                path_display_width=full_line_width - len_append_suffix,
                anchor_dir=display_anchor_dir,
                max_parents=_DEFAULT_SHORT_PATH_MAX_PARENTS,
            )

            lines.append(Text(f"  - {label}", style="red"))

    lines.append(Text(""))

    return Text("\n").join(lines)


# === Internal helpers =========================================================


# --- _render_rich_label_value_row() ---------------------------------------------------------
def _render_rich_label_value_row(
    label: str,
    value: str | None,
    *,
    label_style: str | None,
    value_style: str | None,
    label_pad: int,
) -> Text:
    """
    Render one 'Label: Value' line with fixed padding and Rich styles.
    """

    t = Text()
    if label and value is not None:
        t.append(f"{label.strip():<{label_pad}}:  ", style=label_style)

        t.append(str(value).strip(), style=value_style)

    elif label:
        t.append(label.strip(), style=label_style)

    return t
