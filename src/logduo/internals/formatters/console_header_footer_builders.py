"""
console_header_footer_builders.py

# "_build_auto_*" helpers generate auto-generated info subcomponents

Note: when scrolling console output window, line dividers look heavy.
Line dividers are not displayed in the console header, but are displayed in footer.

Last edited: 2026-7-31
"""

from collections.abc import Mapping
from pathlib import Path

from rich.errors import MarkupError
from rich.text import Text

from logduo.internals.engine.runtime_classes import RuntimeRecord
from logduo.internals.formatters.header_footer_formatters import (
    _build_auto_footer_generated_file_lists,
    _build_auto_footer_info_rows,
    _build_auto_header_info_rows,
    _build_wrapped_lines,
    _derive_label_pad,
)
from logduo.internals.session_config.session_constants import (
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
def _build_console_footer(   # noqa: PLR0915
    *,
    runtime: RuntimeRecord,
    console_footer: str,
    console_wrap_width: int,
    styles: Mapping[str, str],
) -> Text | None:
    """
    Build the resolved console footer payload.
    """

    # --- disabled footer handling ---
    console_footer_arg = console_footer.strip().lower()

    if console_footer_arg == "off":
        return None

    # --- custom footer handling ---
    if console_footer_arg != "auto":
        try:
            footer_text = Text.from_markup(
                console_footer.rstrip("\n")
            )
        except MarkupError:
            footer_text = Text(
                console_footer.rstrip("\n")
            )

        return Text("\n").join(
            [
                footer_text,
                Text(""),
            ]
        )

    line_display_width = console_wrap_width

    # --- styles ---
    label_style = styles.get("header_label") or "blue"
    value_style = styles.get("header_value") or "black"
    divider_style = styles.get("divider") or "blue"

    # --- generated/missing files ---
    (
        output_dir_path,
        output_dir_files,
        other_files,
        missing_files,
    ) = _build_auto_footer_generated_file_lists(
        runtime=runtime
    )

    # --- footer information ---
    auto_footer_info_rows = _build_auto_footer_info_rows(
        runtime=runtime,
        is_main_sink=True,
    )

    divider_line = _RULE_CHAR * _DIVIDER_WIDTH

    lines: list[Text] = [
        Text(divider_line, style=divider_style)
    ]

    # --- logging-ended and script-path information ---
    for label, value in auto_footer_info_rows:
        if label == "Logging ended":
            label_with_colon = f"{label}:"
            header_label_width = len("Logging started:")

            line = Text()
            line.append(
                f"{label_with_colon:<{header_label_width}}  ",
                style=label_style,
            )
            line.append(
                value,
                style=value_style,
            )
            lines.append(line)
            continue

        lines.append(
            Text(
                f"{label}:",
                style=label_style,
            )
        )

        wrapped_lines = _build_wrapped_lines(
            value=f"    {value}",
            width=line_display_width,
            continuation_width=line_display_width,
            hanging_indent=8,
        )

        lines.extend(
            Text(line, style=value_style)
            for line in wrapped_lines
        )


    # --- files inside output directory ---
    if output_dir_files:
        lines.append(
            Text(
                "Output directory:",
                style=label_style,
            )
        )

        wrapped_output_dir = _build_wrapped_lines(
            value=f"    {output_dir_path}",
            width=line_display_width,
            continuation_width=line_display_width,
            hanging_indent=8,
        )

        lines.extend(
            Text(line, style=value_style)
            for line in wrapped_output_dir
        )

        lines.append(
            Text(
                "Log-generated files in output directory:",
                style=label_style,
            )
        )

        for file_display in output_dir_files:
            wrapped_lines = _build_wrapped_lines(
                value=f"    {file_display}",
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=4,
            )

            lines.extend(
                Text(line, style=value_style)
                for line in wrapped_lines
            )

    # --- files outside output directory ---
    if other_files:

        lines.append(
            Text(
                "Other log-generated files:",
                style=label_style,
            )
        )

        for file_display in other_files:
            wrapped_lines = _build_wrapped_lines(
                value=f"    {file_display}",
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=8,
            )

            lines.extend(
                Text(line, style=value_style)
                for line in wrapped_lines
            )

    # --- missing registered files ---
    if missing_files:
        lines.append(Text(""))
        lines.append(
            Text(
                "WARNING: Registered Logduo-managed files missing on disk:",
                style="bold red",
            )
        )

        for file_display in missing_files:
            wrapped_lines = _build_wrapped_lines(
                value=f"    {file_display}",
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=8,
            )

            lines.extend(
                Text(line, style="red")
                for line in wrapped_lines
            )

    lines.append(Text(""))

    return Text("\n").join(lines)



# === Internal helpers =========================================================

# --- _render_rich_label_value_row() -------------------------------------------
def _render_rich_label_value_row(
    label: str,
    value: str | None,
    *,
    label_style: str | None,
    value_style: str | None,
    label_pad: int,
) -> Text:
    """
    Render one aligned ``Label: Value`` line with Rich styles.
    """
    text = Text()
    if label and value is not None:
        label_with_colon = f"{label.strip()}:"
        text.append(
            f"{label_with_colon:<{label_pad + 1}}  ",
            style=label_style,
        )
        text.append(
            str(value).strip(),
            style=value_style,
        )
    elif label:
        text.append(
            label.strip(),
            style=label_style,
        )
    return text
