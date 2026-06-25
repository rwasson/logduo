"""
header_footer_formatters.py

Renderer-independent helpers used by console and log
header/footer builders.

Responsibilities:
- derive metadata rows
- build divider lines
- prepare path display values
- derive formatting widths/padding

Last edited: 2026-5-27
"""

from collections.abc import Sequence
from pathlib import Path

from logduo.internals.engine.runtime_classes import CreatedFileRecord, RuntimeRecord


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


# --- _build_auto_footer_info_rows() -----------------------------------------------
def _build_auto_footer_info_rows(
    *,
    runtime: RuntimeRecord,
    cfr: CreatedFileRecord | None = None,
    path_display_width: int | str,
    anchor_dir: Path | None = None,
    max_parents: int | None = None,
    is_main_sink: bool,
) -> list[tuple[str, str]]:
    """
    Build footer info rows (does not include created file list).

    Main sink info footer displays end time and script path (if available)
    Info is obtained from runtime (cfr is ignored when is_main_sink=True).
       cfr is used by other function to generate list of created files,
       (shown only in console and main log)

    User sink info footer displays end time and thy user sink's log file path
    -  require a CreatedFileRecord.

    """
    rows: list[tuple[str, str]] = []
    if runtime.end_time_display is None:
        raise RuntimeError("LOGDUO INTERNAL ERROR: end_time_display not set.")

    # --- ended time row ---
    ended_value = runtime.end_time_display
    if runtime.duration_display:
        ended_value += f"  (duration {runtime.duration_display})"
    rows.append(("logging ended", ended_value))

    if is_main_sink:
        # main sink log path

        # --- script path ---
        # not shown for interactive sessions
        if runtime.script_path_abs is not None:
            script_path_display_label = _build_shortened_file_path_display_label(
                runtime.script_path_abs,
                path_display_width=path_display_width,
                anchor_dir=anchor_dir,
                max_parents=max_parents,
            )
            rows.append(("script path", script_path_display_label))

    else:
        # user_sink log path
        assert cfr is not None
        file_path_display_label = _build_shortened_file_path_display_label(
            cfr.path,
            path_display_width=path_display_width,
            anchor_dir=anchor_dir,
            max_parents=max_parents,
        )
        rows.append(("log file path", file_path_display_label))

    return rows


# --- _build_footer_created_file_lists() -------------------------------------------------
def _build_auto_footer_created_file_lists(
    runtime: RuntimeRecord, *, include_jsonl: bool = True
) -> tuple[list[CreatedFileRecord], list[CreatedFileRecord]]:
    """
    Returns:
        visible_files: list of file paths to show in footer
        missing_names: declared but not created
    """

    existing: list[CreatedFileRecord] = []
    missing: list[CreatedFileRecord] = []

    for cfr in runtime._get_file_list_in_cfr():
        try:
            if include_jsonl and cfr.file_kind == "jsonl":
                existing.append(cfr)
                continue

            if cfr.path and cfr.path.exists():
                existing.append(cfr)
            else:
                missing.append(cfr)

        except OSError:
            missing.append(cfr)

    return existing, missing


# --- _build_shortened_file_path_display_label() -----------------------------------------------
def _build_shortened_file_path_display_label(
    path: Path,
    *,
    anchor_dir: Path | None,
    path_display_width: int | str,
    max_parents: int | None = None,
) -> str:
    """
    Returns:
        path display value, based on display width policy.
        May be part of label/value pair in footer

    Policy:
        - "off" -> full path
        - int   -> shortened path
    """
    from logduo.utils.short_path.short_path import short_path

    # --- full path ---
    # path_display_width derives from console_wrap_width or log_wrap_width
    # log_wrap_width can be "off"
    if path_display_width == "off":
        return str(path)

    if isinstance(path_display_width, bool):
        raise RuntimeError("LOGDUO INTERNAL ERROR: path_display_width cannot be bool")

    # --- fitted path ---
    # short_path() contains its own normalization and fallback handling
    # for path-shortening operations and returns a usable display
    # string for normal runtime path cases.
    if isinstance(path_display_width, int):
        return short_path(
            path, anchor_dir=anchor_dir, width=path_display_width, max_parents=max_parents
        )

    raise RuntimeError(f"LOGDUO INTERNAL ERROR: invalid display_width={path_display_width!r}")


# --- _derive_label_pad() --------------------------------------------------------
def _derive_label_pad(rows: Sequence[tuple[str | None, str]]) -> int:
    labels = [label for label, _ in rows if label is not None]
    if not labels:
        return 0
    return max(len(label) for label in labels)
