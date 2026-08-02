"""
log_header_footer_builders.py

Builders for plain-text log footers.

Last edited: 2026-7-31
"""

from pathlib import Path

from logduo.internals.engine.runtime_classes import CreatedFileRecord, RuntimeRecord
from logduo.internals.formatters.header_footer_formatters import (
    _build_auto_footer_generated_file_lists,
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
        - generated-file summary
        - missing-file warnings

    User sink footers render:
        - lightweight artifact metadata only

    session_config is only required for main sink footers because the
    generated-file report uses the main log wrapping policy.
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
    if is_main_sink_log:
        assert session_config is not None, (
            "LOGDUO INTERNAL ERROR: Main sink footer requires session_config."
        )
        return _build_main_sink_log_footer(session_config=session_config, runtime=runtime)

    # === User sink footer ===
    return _build_user_sink_log_footer(cfr=cfr, runtime=runtime)

# --- _build_main_sink_log_footer() -------------------------------------------
def _build_main_sink_log_footer(
    *,
    session_config: SessionConfig,
    runtime: RuntimeRecord,
) -> str:
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

    (
        output_dir_path,
        output_dir_files,
        other_files,
        missing_files,
    ) = _build_auto_footer_generated_file_lists(runtime=runtime)

    auto_footer_info_rows = _build_auto_footer_info_rows(
        runtime=runtime,
        is_main_sink=True,
    )

    divider_line = _RULE_CHAR * _DIVIDER_WIDTH
    lines: list[str] = [divider_line]

    # --- logging-ended and script-path information ---
    for label, value in auto_footer_info_rows:
        if label == "Logging ended":
            label_with_colon = f"{label}:"
            header_label_width = len("Logging started:")
            lines.append(f"{label_with_colon:<{header_label_width}}  {value}")
            continue


        # Full paths use a heading followed by flush-left wrapped path lines.
        lines.append(f"{label}:")
        lines.extend(
            _build_wrapped_lines(
                value=f"    {value}",
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=8,
            )

        )


    # --- files inside output directory ---
    if output_dir_files:
        lines.append("Output directory:")
        lines.extend(
            _build_wrapped_lines(
                value=f"    {output_dir_path}",
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=8,
            )
        )

        lines.append("Log-generated files in output directory:")

        for file_display in output_dir_files:
            lines.extend(
                _build_wrapped_lines(
                    value=f"    {file_display}",
                    width=line_display_width,
                    continuation_width=line_display_width,
                    hanging_indent=4,
                )
            )

    # --- files outside output directory ---
    if other_files:

        lines.append("Other log-generated files:")
        for file_display in other_files:
            lines.extend(
                _build_wrapped_lines(
                    value=f"    {file_display}",
                    width=line_display_width,
                    continuation_width=line_display_width,
                    hanging_indent=8,
                )
            )

    # --- missing-file warning ---
    if missing_files:
        lines.append("")
        lines.append("WARNING: Registered Logduo-managed files missing on disk:")
        for file_display in missing_files:
            lines.extend(
                _build_wrapped_lines(
                    value=f"    {file_display}",
                    width=line_display_width,
                    continuation_width=line_display_width,
                    hanging_indent=8,
                )
            )

    lines.append("")

    return "\n".join(lines)


# --- _build_user_sink_log_footer() -------------------------------------------
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

    auto_footer_info_rows = _build_auto_footer_info_rows(
        runtime=runtime,
        is_main_sink=False,
    )

    divider_line = _RULE_CHAR * _DIVIDER_WIDTH
    lines: list[str] = [divider_line]

    for label, value in auto_footer_info_rows:

        if label == "Logging ended":
            label_with_colon = f"{label}:"
            header_label_width = len("Logging started:")
            lines.append(f"{label_with_colon:<{header_label_width}}  {value}")
            continue

        lines.append(f"{label}:")
        lines.extend(
            _build_wrapped_lines(
                value=f"    {value}",
                width=line_display_width,
                continuation_width=line_display_width,
                hanging_indent=8,
            )
        )

    log_file_path = str(cfr.path.absolute())

    lines.append("Log file path:")
    lines.extend(
        _build_wrapped_lines(
            value=f"    {log_file_path}",
            width=line_display_width,
            continuation_width=line_display_width,
            hanging_indent=8,
        )
    )

    lines.append("")

    return "\n".join(lines)
