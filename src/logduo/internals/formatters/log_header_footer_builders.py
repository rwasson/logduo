"""
log_header_footer_builders.py

Builders for plain-text log footers.

Last edited: 2026-7-19
"""

from pathlib import Path

from logduo.internals.engine.runtime_classes import CreatedFileRecord, RuntimeRecord
from logduo.internals.formatters.header_footer_formatters import (
    _build_auto_footer_created_file_lists,
    _build_auto_footer_info_rows,
    _build_auto_header_info_rows,
    _build_wrapped_lines,
    _derive_label_pad,
    _render_plain_label_value_row,
)
from logduo.internals.formatters.message_prep import _to_plain_log_text
from logduo.internals.session_config.session_config_classes import SessionConfig
from logduo.internals.session_config.session_constants import (
    _DIVIDER_WIDTH,
    _NO_WRAP_WIDTH,
    _RULE_CHAR,
)


# --- _build_log_header() ------------------------------------------------------
def _build_log_header(*, runtime: RuntimeRecord, cfr: CreatedFileRecord) -> str | None:
    """
    Build the resolved header payload for one log-style sink file.
    """

    path = Path(cfr.path)

    # --- disabled header handling ---
    log_header_arg = cfr.log_header.strip().lower()
    if log_header_arg == "off":
        return None

    # --- custom header handling ---
    if log_header_arg != "auto":
        header_text = _to_plain_log_text(cfr.log_header)

        if not header_text.endswith("\n"):
            header_text += "\n"

        return header_text

    # --- auto-generated log headers ---

    divider_line = _RULE_CHAR * _DIVIDER_WIDTH

    # --- auto header for append sessions to existing log ---
    if cfr.log_file_mode == "append":
        try:
            exists = path.exists()
            size = path.stat().st_size if exists else 0

        except OSError:
            exists = False
            size = 0

        if exists and size > 0:
            return (
                f"{divider_line}\n"
                f"New session started at "
                f"{runtime.start_time_display}\n"
                f"{divider_line}\n"
            )

    # --- auto header for new log ---
    rows = _build_auto_header_info_rows(runtime=runtime, file_name=cfr.file_name)
    label_pad = _derive_label_pad(rows)
    lines: list[str] = [divider_line]

    for label, value in rows:
        # --- standalone title row ---
        if label is None:
            lines.append(value)

        # --- standard label/value row ---
        else:
            lines.append(
                _render_plain_label_value_row(label=label, value=value, label_pad=label_pad)
            )

    lines.append(divider_line)
    lines.append("")

    return "\n".join(lines)



# --- _build_log_footer() ------------------------------------------------------
def _build_log_footer(
    *,
    runtime: RuntimeRecord,
    session_config: SessionConfig | None = None,
    cfr: CreatedFileRecord,
    is_main_sink_log: bool,
) -> str | None:
    """
    Build the resolved footer payload for one log-style sink file.

    Main sink footers render:
        - full session metadata
        - created-file summary
        - missing-file warnings

    User sink footers render:
        - lightweight artifact metadata only

    session_config is only required for main sink footers because the
    created-file report uses the main log wrapping policy.
    """

    # --- disabled footer handling ---
    log_footer_arg = cfr.log_footer.strip().lower()
    if log_footer_arg == "off":
        return None

    # --- custom footer handling ---
    if log_footer_arg != "auto":
        footer_text = _to_plain_log_text(cfr.log_footer)
        if not footer_text.endswith("\n"):
            footer_text += "\n"
        return footer_text

    # === Main sink footer ===
    # Compute available width based on longest possible label:
    if is_main_sink_log:
        assert session_config is not None, (
            "LOGDUO INTERNAL ERROR: Main sink footer requires session_config."
        )
        return _build_main_sink_log_footer(session_config=session_config, runtime=runtime)

    # === User sink footer ===
    return _build_user_sink_log_footer(cfr=cfr, runtime=runtime)


# --- _build_main_sink_log_footer()--------------------------------------------------
def _build_main_sink_log_footer(*, session_config: SessionConfig, runtime: RuntimeRecord) -> str:  # noqa: PLR0915

    configured_wrap_width = session_config.log_wrap_width
    if configured_wrap_width == "off":
        line_display_width = _NO_WRAP_WIDTH
    else:
        if not isinstance(configured_wrap_width, int):
            raise RuntimeError(
                "LOGDUO INTERNAL ERROR: resolved log_wrap_width "
                "must be a positive integer or 'off'."
            )
        line_display_width = configured_wrap_width


    # --- created/missing files ---
    (output_dir_files, project_files, external_files, missing_files,
     ) = _build_auto_footer_created_file_lists(runtime=runtime)

    output_dir_path = runtime.main_sink_log_dir_path_abs
    project_dir_path = runtime.project_dir_path_abs

    assert output_dir_path is not None
    assert project_dir_path is not None

    # ---  auto_footer_info_rows (end time + script_path display pairs)  ---
    auto_footer_info_rows = _build_auto_footer_info_rows(
        runtime=runtime,
        is_main_sink=True,
    )

    # label_pad = length of longest label
    label_pad = _derive_label_pad(auto_footer_info_rows, len("output directory"))
    divider_line = _RULE_CHAR * _DIVIDER_WIDTH
    lines: list[str] = [divider_line]

    for label, value in auto_footer_info_rows:
        row = _render_plain_label_value_row(label=label, value=value, label_pad=label_pad)
        hanging_indent = label_pad + 5
        lines.extend(
            _build_wrapped_lines(
                value=row,
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=hanging_indent,
            )
        )

    # --- output directory ---
    try:
        output_dir_display_label = str(output_dir_path.relative_to(project_dir_path.parent))
    except ValueError:
        output_dir_display_label = str(output_dir_path)

    rows = _render_plain_label_value_row(
        label="output directory",
        value=output_dir_display_label,
        label_pad=label_pad,
    )

    lines.extend(
        _build_wrapped_lines(
            value=rows,
            width=line_display_width,
            continuation_width=line_display_width,
            hanging_indent=label_pad + 5,
        )
    )

    # --- files in output directory ---
    # Relative to output dir, so might be file names only
    if output_dir_files:
        lines.append("")
        lines.append("files created this logging session in output directory:")

        for file in output_dir_files:
            file_path_display_label = "    " + str(file.path.relative_to(output_dir_path))
            if file.log_file_mode == "append":
                file_path_display_label += " (append)"
            lines.extend(
                _build_wrapped_lines(
                    value=file_path_display_label,
                    width=line_display_width,
                    continuation_width=line_display_width,
                    hanging_indent=6,
                )
            )

    # --- other files inside project ---
    if project_files:
        lines.append("")
        lines.append("files created this logging session in project directory:")

        for file in project_files:
            file_path_display_label = "    " + str(
                file.path.relative_to(project_dir_path.parent)
            )

            if file.log_file_mode == "append":
                file_path_display_label += " (append)"

            lines.extend(
                _build_wrapped_lines(
                    value=file_path_display_label,
                    width=line_display_width,
                    continuation_width=line_display_width,
                    hanging_indent=6,
                )
            )

    # --- other files outside project ---
    if external_files:
        lines.append("")
        lines.append("files created this logging session outside project directory:")

        for file in external_files:
            file_path_display_label = "    " + str(file.path)

            if file.log_file_mode == "append":
                file_path_display_label += " (append)"

            lines.extend(
                _build_wrapped_lines(
                    value=file_path_display_label,
                    width=line_display_width,
                    continuation_width=line_display_width,
                    hanging_indent=6,
                )
            )

    # --- append footer with missing files list ---
    if missing_files:
        lines.append("")
        lines.append("WARNING: Registered Logduo-managed files missing on disk:")

        for file in missing_files:
            # missing file block displayed flush left (constant line width)
            file_path_display_label = "    " + str(file.path)

            if file.log_file_mode == "append":
                file_path_display_label = f"{file_path_display_label} (append)"

            lines.extend(
                _build_wrapped_lines(
                    value=file_path_display_label,
                    width=line_display_width,
                    continuation_width=line_display_width,
                    hanging_indent=6,
                )
            )

    lines.append("")

    return "\n".join(lines)


# --- _build_user_sink_log_footer()--------------------------------------------------
def _build_user_sink_log_footer(
    *,
    cfr: CreatedFileRecord,
    runtime: RuntimeRecord,
) -> str:

    configured_wrap_width = cfr.log_wrap_width

    if configured_wrap_width == "off":
        line_display_width = _NO_WRAP_WIDTH
    else:
        if not isinstance(configured_wrap_width, int):
            raise RuntimeError(
                "LOGDUO INTERNAL ERROR: resolved log_wrap_width "
                "must be a positive integer or 'off'."
            )
        line_display_width = configured_wrap_width
    assert isinstance(line_display_width, int)

    # --- universal footer rows ---
    auto_footer_info_rows = _build_auto_footer_info_rows(
        runtime=runtime,
        is_main_sink=False,
    )

    # Include the user-sink-specific label when calculating alignment.
    label_pad = max(
        _derive_label_pad(auto_footer_info_rows),
        len("log file path"),
    )

    divider_line = _RULE_CHAR * _DIVIDER_WIDTH
    lines: list[str] = [divider_line]

    # --- render universal footer rows ---
    for label, value in auto_footer_info_rows:
        row = _render_plain_label_value_row(
            label=label,
            value=value,
            label_pad=label_pad,
        )

        lines.extend(
            _build_wrapped_lines(
                value=row,
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=label_pad + 5,
            )

        )

    # --- user-sink log file ---
    project_dir_path = runtime.project_dir_path_abs
    if project_dir_path is None:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: project_dir_path_abs not set."
        )
    anchor_dir = project_dir_path.parent
    try:
        log_file_path_display_label = str(cfr.path.relative_to(anchor_dir))
    except ValueError:
        log_file_path_display_label = str(cfr.path)


    log_file_path_display = _render_plain_label_value_row(
        label="log file path",
        value=log_file_path_display_label,
        label_pad=label_pad,
    )

    lines.extend(
        _build_wrapped_lines(
            value=log_file_path_display,
            width=line_display_width,
            continuation_width=line_display_width,
            hanging_indent=label_pad + 5,
        )
    )

    lines.append("")

    return "\n".join(lines)


