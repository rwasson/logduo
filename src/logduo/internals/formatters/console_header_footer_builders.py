"""
console_header_footer_builders.py

# "_build_auto_*" helpers generate auto-generated info subcomponents

Note: in scrolling console output window environments, line dividers look heavy.
Line dividers are not displayed in console, but still are displayed in logs.

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
def _build_console_footer(  # noqa: PLR0915
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

    # --- console wrap width ---
    line_display_width = console_wrap_width

    # --- styles ---
    label_style = styles.get("header_label") or "blue"
    value_style = styles.get("header_value") or "black"
    divider_style = styles.get("divider") or "blue"

    # --- created/missing files ---
    (
        output_dir_files,
        project_files,
        external_files,
        missing_files,
    ) = _build_auto_footer_created_file_lists(
        runtime=runtime
    )

    output_dir_path = runtime.main_sink_log_dir_path_abs
    project_dir_path = runtime.project_dir_path_abs

    assert output_dir_path is not None
    assert project_dir_path is not None

    # --- auto footer info rows ---
    auto_footer_info_rows = _build_auto_footer_info_rows(
        runtime=runtime,
        is_main_sink=True,
    )

    # Include output-directory label in alignment calculation.
    label_pad = _derive_label_pad(
        auto_footer_info_rows,
        len("output directory"),
    )

    divider_line = _RULE_CHAR * _DIVIDER_WIDTH

    lines: list[Text] = [
        Text(divider_line, style=divider_style)
    ]

    # --- logging ended / script path ---
    for label, value in auto_footer_info_rows:
        lines.extend(
            _build_wrapped_rich_label_value_lines(
                label=label,
                value=value,
                label_pad=label_pad,
                line_display_width=line_display_width,
                label_style=label_style,
                value_style=value_style,
            )
        )

    # --- output directory ---
    try:
        output_dir_display_label = str(output_dir_path.relative_to(project_dir_path.parent))
    except ValueError:
        output_dir_display_label = str(output_dir_path)


    lines.extend(
        _build_wrapped_rich_label_value_lines(
            label="output directory",
            value=output_dir_display_label,
            label_pad=label_pad,
            line_display_width=line_display_width,
            label_style=label_style,
            value_style=value_style,
        )
    )

    # --- files created in output directory ---
    if output_dir_files:
        lines.append(Text(""))
        lines.append(
            Text(
                "files created this logging session in output directory:",
                style=label_style,
            )
        )

        for file in output_dir_files:
            file_path_display_label = (
                "    "
                + str(file.path.relative_to(output_dir_path))
            )

            if file.log_file_mode == "append":
                file_path_display_label += " (append)"

            wrapped_lines = _build_wrapped_lines(
                value=file_path_display_label,
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=6,
            )

            lines.extend(
                Text(line, style=value_style)
                for line in wrapped_lines
            )

    # --- files created in project directory ---
    if project_files:
        lines.append(Text(""))
        lines.append(
            Text(
                "files created this logging session in project directory:",
                style=label_style,
            )
        )

        for file in project_files:
            file_path_display_label = (
                "    "
                + str(
                    file.path.relative_to(project_dir_path.parent)
                )
            )

            if file.log_file_mode == "append":
                file_path_display_label += " (append)"

            wrapped_lines = _build_wrapped_lines(
                value=file_path_display_label,
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=6,
            )

            lines.extend(
                Text(line, style=value_style)
                for line in wrapped_lines
            )

    # --- files created outside project directory ---
    if external_files:
        lines.append(Text(""))
        lines.append(
            Text(
                "files created this logging session outside project directory:",
                style=label_style,
            )
        )

        for file in external_files:
            file_path_display_label = "    " + str(file.path)

            if file.log_file_mode == "append":
                file_path_display_label += " (append)"

            wrapped_lines = _build_wrapped_lines(
                value=file_path_display_label,
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=6,
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

        for file in missing_files:
            file_path_display_label = "    " + str(file.path)

            if file.log_file_mode == "append":
                file_path_display_label += " (append)"

            wrapped_lines = _build_wrapped_lines(
                value=file_path_display_label,
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=6,
            )

            lines.extend(
                Text(line, style="red")
                for line in wrapped_lines
            )

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


# --- _build_wrapped_rich_label_value_lines() ---------------------------------
def _build_wrapped_rich_label_value_lines(
    *,
    label: str,
    value: str,
    label_pad: int,
    line_display_width: int,
    label_style: str | None,
    value_style: str | None,
) -> list[Text]:
    """
    Render and wrap one Rich label/value row.

    Continuation lines begin two spaces beyond the start of the value.
    """
    label_prefix = f"{label:<{label_pad}}:  "
    rendered_line = label_prefix + value

    wrapped_lines = _build_wrapped_lines(
        value=rendered_line,
        width=line_display_width,
        continuation_width=line_display_width,
        hanging_indent=label_pad + 5,
    )

    rich_lines: list[Text] = []

    for line_index, wrapped_line in enumerate(wrapped_lines):
        if line_index == 0:
            rich_line = Text()
            rich_line.append(label_prefix, style=label_style)
            rich_line.append(
                wrapped_line[len(label_prefix):],
                style=value_style,
            )
        else:
            rich_line = Text(
                wrapped_line,
                style=value_style or "",
            )

        rich_lines.append(rich_line)

    return rich_lines
