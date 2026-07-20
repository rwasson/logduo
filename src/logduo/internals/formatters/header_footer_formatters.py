"""
header_footer_formatters.py

Last edited: 2026-7-19
"""
from collections.abc import Sequence
from pathlib import Path

from logduo.internals.engine.runtime_classes import CreatedFileRecord, RuntimeRecord
from logduo.utils.wrap.wrap_text import wrap_text


# --- _build_header_info_rows() -----------------------------------------------
def _build_auto_header_info_rows(
    *, runtime: RuntimeRecord, file_name: str, is_log_file: bool = True
) -> list[tuple[str | None, str]]:
    """
    Build info header rows.
    Returns:
        List of:
            (None, value)
                -> standalone title row
            (label, value)
                -> standard labeled metadata row
    No renderer-specific formatting is applied here.
    """
    rows: list[tuple[str | None, str]] = []
    if runtime.start_time_display is None:
        raise RuntimeError("LOGDUO INTERNAL ERROR: start_time_display not set.")

    # log files, log file name shown above time
    if is_log_file:
        # log file name
        rows.append((None, file_name))

        # --- started time row ---
        rows.append(("logging started", runtime.start_time_display))

        # --- script name (if Logduo initiated by script) ---
        if runtime.script_name:
            rows.append(("created by", runtime.script_name))

    # console
    else:
        # --- started time row ---
        rows.append(("logging started", runtime.start_time_display))

        # --- script name (if Logduo initiated by script) ---
        if runtime.script_name:
            rows.append(("running script", runtime.script_name))

    return rows


# --- _build_auto_footer_info_rows() -------------------------------------------
def _build_auto_footer_info_rows(
    *,
    runtime: RuntimeRecord,
    is_main_sink: bool,
) -> list[tuple[str, str]]:
    """
    Build footer info rows:

    logging ended:  2026-07-19 18:57:39  (duration 00 sec)
    script path  :  logduo_project/src/logduo/internals/artifacts/logduo_docs/example_scripts/first_script.py

    Only Main sink info footer displays duration.
    script_path not shown for interactive sessions
    """
    project_dir_path_abs = runtime.project_dir_path_abs

    if project_dir_path_abs is None:
        raise RuntimeError(

            "LOGDUO INTERNAL ERROR: project_dir_path_abs not set."

        )

    anchor_dir = project_dir_path_abs.parent

    rows: list[tuple[str, str]] = []
    if runtime.end_time_display is None:
        raise RuntimeError("LOGDUO INTERNAL ERROR: end_time_display not set.")

    # --- ended time row ---
    ended_value = runtime.end_time_display
    if is_main_sink and runtime.duration_display:
        ended_value += f" (duration {runtime.duration_display})"
    rows.append(("logging ended", ended_value))

    # --- script path row ---
    # Not shown for interactive sessions
    if runtime.script_path_abs is not None:
        script_path_display_label = str(runtime.script_path_abs.relative_to(anchor_dir))
        rows.append(("script path", script_path_display_label))

    return rows


# --- _build_auto_footer_created_file_lists() ---------------------------------
def _build_auto_footer_created_file_lists(
    runtime: RuntimeRecord,
    *,
    include_jsonl: bool = True,
) -> tuple[
    list[CreatedFileRecord],
    list[CreatedFileRecord],
    list[CreatedFileRecord],
    list[CreatedFileRecord],
]:
    """
    Group registered Logduo-created files for footer display.

    Returns:
        output_dir_files:
            Existing files inside the main output directory.

        project_files:
            Existing files elsewhere inside the project directory.

        external_files:
            Existing files outside the project directory.

        missing_files:
            Registered files not found on disk.
    """
    output_dir_path = runtime.main_sink_log_dir_path_abs
    project_dir_path = runtime.project_dir_path_abs

    if output_dir_path is None:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: main_sink_log_dir_path_abs not set."
        )

    if project_dir_path is None:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: project_dir_path_abs not set."
        )

    output_dir_files: list[CreatedFileRecord] = []
    project_files: list[CreatedFileRecord] = []
    external_files: list[CreatedFileRecord] = []
    missing_files: list[CreatedFileRecord] = []

    for cfr in runtime._get_file_list_in_cfr():
        try:
            file_exists = cfr.path.exists()

            # JSONL records may be registered before the file is physically
            # visible, so preserve the existing special-case behavior.
            if include_jsonl and cfr.file_kind == "jsonl":
                file_exists = True

        except OSError:
            file_exists = False

        if not file_exists:
            missing_files.append(cfr)
            continue

        if _path_is_within(
            path=cfr.path,
            parent=output_dir_path,
        ):
            output_dir_files.append(cfr)

        elif _path_is_within(
            path=cfr.path,
            parent=project_dir_path,
        ):
            project_files.append(cfr)

        else:
            external_files.append(cfr)

    output_dir_files.sort(
        key=lambda cfr_inner: str(
            cfr_inner.path.relative_to(output_dir_path)).casefold(),
    )

    project_files.sort(
        key=lambda cfr_inner: str(
            cfr_inner.path.relative_to(project_dir_path)).casefold(),
    )

    external_files.sort(
        key=lambda cfr_inner: str(
            cfr_inner.path).casefold(),
    )

    missing_files.sort(
        key=lambda cfr_inner: str(
            cfr_inner.path).casefold(),
    )

    return (
        output_dir_files,
        project_files,
        external_files,
        missing_files,
    )


# --- _path_is_within() -------------------------------------------------------
def _path_is_within(
    *,
    path: Path,
    parent: Path,
) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False

    return True



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


# --- _derive_label_pad() --------------------------------------------------------
def _derive_label_pad(rows: Sequence[tuple[str | None, str]], num: int = 0) -> int:
    labels = [label for label, _ in rows if label is not None]
    if not labels:
        return 0
    max_width = max(max(len(label) for label in labels), num)
    return max_width


# --- _render_plain_label_value_row() -------------------------------------------
def _render_plain_label_value_row(*, label: str, value: str, label_pad: int) -> str:
    return f"{label:<{label_pad}}:  {value}"
