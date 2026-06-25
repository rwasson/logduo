"""
log_header_footer_builders.py

Builders for plain-text log headers and footers.

Last edited: 2026-6-7
"""

from pathlib import Path

from logduo.internals.engine.runtime_classes import CreatedFileRecord, RuntimeRecord
from logduo.internals.formatters.header_footer_formatters import (
    _build_auto_footer_created_file_lists,
    _build_auto_footer_info_rows,
    _build_auto_header_info_rows,
    _build_shortened_file_path_display_label,
    _derive_label_pad,
)
from logduo.internals.formatters.message_prep import _to_plain_log_text
from logduo.internals.session_config.session_config_classes import SessionConfig
from logduo.internals.session_config.session_constants import (
    _DEFAULT_SHORT_PATH_WIDTH,
    _DIVIDER_WIDTH,
    _RULE_CHAR,
)
from logduo.utils.wrap.wrap_text import wrap_text


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


# === Internal helpers =========================================================


# --- _build_main_sink_log_footer()--------------------------------------------------
def _build_main_sink_log_footer(*, session_config: SessionConfig, runtime: RuntimeRecord) -> str:

    # --- log wrap width ---
    if session_config.log_wrap_width != "off":
        assert isinstance(session_config.log_wrap_width, int)
        line_display_width = min(session_config.log_wrap_width, _DEFAULT_SHORT_PATH_WIDTH)
    else:
        line_display_width = _DEFAULT_SHORT_PATH_WIDTH

    # --- created/missing files ---
    created_files, missing_files = _build_auto_footer_created_file_lists(runtime=runtime)

    created_files = sorted(created_files, key=lambda cf: cf.display_order)
    missing_files = sorted(missing_files, key=lambda cf: cf.display_order)

    # --- info footer rows (label plus value pair) ---
    auto_footer_info_rows = _build_auto_footer_info_rows(
        runtime=runtime,
        path_display_width="off",
        anchor_dir=None,
        max_parents=None,
        is_main_sink=True,
    )

    # label_pad = length of longest label
    label_pad = _derive_label_pad(auto_footer_info_rows)

    divider_line = _RULE_CHAR * _DIVIDER_WIDTH
    lines: list[str] = [divider_line]

    # --- render info footer rows ---
    for label, value in auto_footer_info_rows:
        row = _render_plain_label_value_row(label=label, value=value, label_pad=label_pad)
        # hanging_indent = len(f"{label}: ") + 3
        hanging_indent = label_pad + 3
        lines.extend(
            _build_wrapped_lines(
                value=row,
                width=session_config.log_wrap_width,
                continuation_width=line_display_width,
                hanging_indent=hanging_indent,
            )
        )

    # --- append footer with created files list ---
    if created_files:
        lines.append("")
        lines.append("Logduo-managed files created this run:")

        for file in created_files:
            # created file block displayed flush left (constant line width)
            file_path_display_label = _build_shortened_file_path_display_label(
                file.path, path_display_width="off", anchor_dir=None, max_parents=None
            )

            if file.log_file_mode == "append":
                file_path_display_label = f"{file_path_display_label} (append)"

            lines.extend(
                _build_wrapped_lines(
                    value=file_path_display_label,
                    width=session_config.log_wrap_width,
                    continuation_width=line_display_width,
                    hanging_indent=4,
                )
            )

    # --- append footer with missing files list ---
    if missing_files:
        lines.append("")
        lines.append("WARNING: Registered Logduo-managed files missing on disk:")

        for file in missing_files:
            # missing file block displayed flush left (constant line width)
            file_path_display_label = _build_shortened_file_path_display_label(
                file.path, path_display_width="off", anchor_dir=None, max_parents=None
            )

            if file.log_file_mode == "append":
                file_path_display_label = f"{file_path_display_label} (append)"

            lines.extend(
                _build_wrapped_lines(
                    value=file_path_display_label,
                    width=session_config.log_wrap_width,
                    continuation_width=line_display_width,
                    hanging_indent=4,
                )
            )

    lines.append("")

    return "\n".join(lines)


# --- _build_user_sink_log_footer()--------------------------------------------------
def _build_user_sink_log_footer(*, cfr: CreatedFileRecord, runtime: RuntimeRecord) -> str:

    if cfr.log_wrap_width != "off":
        line_display_width = min(cfr.log_wrap_width, _DEFAULT_SHORT_PATH_WIDTH)
    else:
        line_display_width = _DEFAULT_SHORT_PATH_WIDTH

    # --- info footer rows (label and value pairs) ---
    auto_footer_info_rows = _build_auto_footer_info_rows(
        runtime=runtime,
        cfr=cfr,
        path_display_width="off",
        anchor_dir=None,
        max_parents=None,
        is_main_sink=False,
    )

    # label_pad = length of longest label
    label_pad = _derive_label_pad(auto_footer_info_rows)

    divider_line = _RULE_CHAR * _DIVIDER_WIDTH
    lines: list[str] = [divider_line]

    # --- render info footer rows ---
    assert isinstance(line_display_width, int)
    for label, value in auto_footer_info_rows:
        hanging_indent = label_pad + 3
        row = _render_plain_label_value_row(label=label, value=value, label_pad=label_pad)
        lines.extend(
            _build_wrapped_lines(
                value=row,
                width=cfr.log_wrap_width,
                continuation_width=line_display_width,
                hanging_indent=hanging_indent,
            )
        )

    lines.append("")

    return "\n".join(lines)


# --- _render_plain_label_value_row() -------------------------------------------
def _render_plain_label_value_row(*, label: str, value: str, label_pad: int) -> str:
    return f"{label:<{label_pad}}:  {value}"


# --- _build_wrapped_lines() ---------------------------------------------------
def _build_wrapped_lines(
    *,
    value: str,
    width: int | str,
    continuation_width: int | None = None,
    hanging_indent: int | None = None,
) -> list[str]:
    if width == "off":
        return [value]
    assert isinstance(width, int)
    return wrap_text(
        value, width=width, continuation_width=continuation_width, hanging_indent=hanging_indent
    )
