"""
text_table_widths.py

Last edited: 2026-06-18
"""
from typing import Any

from logduo.utils.table.text_table_classes_and_constants import (
    _MIN_COL_WIDTH,
    TableLayout,
)
from logduo.utils.table.text_table_layout import _get_cell_from_row
from logduo.utils.wrap.wrap_text import strip_ansi, wrap_text


# --- _visible_len() -----------------------------------------------------------
def _visible_len(s: str) -> int:
    return len(strip_ansi(s))


# --- _stringify_for_table() ----------------------------------------------------
def _stringify_for_table(value: Any) -> str:
    if value is None:
        return ""
    return str(value)



# --- _wrap_cell_text_for_width() ----------------------------------------------
def _wrap_cell_text_for_width(
    text_value: Any, col_width: int, max_cell_lines: int | None
) -> list[str]:
    """Word-wrap a cell using logduo natural wrapping logic."""
    if max_cell_lines is not None and max_cell_lines <= 0:
        return [""]
    if col_width <= 0:
        return [""]

    # Convert to string
    text_str = "" if text_value is None else str(text_value)

    # Use shared wrapping (ANSI-safe, natural breaks, etc.)
    wrapped = wrap_text(text_str, width=col_width)

    # --- HARD CLAMP (critical fix) ---
    # NOTE:
    # Raw slicing is not fully ANSI-safe if escape sequences are present.
    # This utility assumes ANSI-heavy content is uncommon.
    clamped = []
    for line in wrapped:
        if _visible_len(line) > col_width:
            line = line[:col_width]
        clamped.append(line)

    wrapped = clamped

    # Respect max_cell_lines and add ellipsis if truncated
    if max_cell_lines is not None and len(wrapped) > max_cell_lines:
        cutoff = wrapped[:max_cell_lines]
        last = cutoff[-1]
        if col_width >= _MIN_COL_WIDTH:
            if _visible_len(last) > col_width - _MIN_COL_WIDTH:
                last = last[: col_width - _MIN_COL_WIDTH] + "..."
            else:
                last += "..."
            cutoff[-1] = last
        return cutoff

    return wrapped


# --- _compute_auto_col_widths() -----------------------------------------------
def _compute_auto_col_widths(
    *,
    selectors: list[int | str],
    header_labels_resolved: list[str],
    data_rows: list[Any],
    row_is_mapping: bool,
    max_col_width: int | None,
    max_col_widths: list[int] | None,
) -> list[int]:

    widths: list[int] = []

    for col_index, selector in enumerate(selectors):
        # --- Start with header width ---
        max_obs_col_width = _visible_len(str(header_labels_resolved[col_index]))

        # loop through rows to find max_obs_col_width for the col in the table
        for row_obj in data_rows:
            cell_val = _get_cell_from_row(row_obj, selector, row_is_mapping)
            text_str = _stringify_for_table(cell_val)

            for line_text in text_str.splitlines() or [""]:
                max_obs_col_width = max(max_obs_col_width, _visible_len(line_text))

        # --- Apply optional maximum width constraint ---
        if max_col_widths and col_index < len(max_col_widths):
            max_w = max_col_widths[col_index]
        elif max_col_width is not None:
            max_w = max_col_width
        else:
            max_w = None

        if max_w is None:
            col_width = max(max_obs_col_width, _MIN_COL_WIDTH)
        else:
            col_width = max(_MIN_COL_WIDTH, min(max_obs_col_width, max_w))

        widths.append(col_width)

    return widths


# --- _resolve_column_widths() -------------------------------------------------
def _resolve_column_widths(
    *,
    layout: TableLayout,
    exact_col_width: int | None,
    exact_col_widths: list[int] | None,
    max_col_width: int | None,
    max_col_widths: list[int] | None,
) -> list[int]:
    """
    Resolve final column widths.

    exact_col_widths/s takes precedence over automatic sizing.
    """
    # Per-column exact widths
    if exact_col_widths is not None:
        col_widths = exact_col_widths[: layout.num_cols]

        while len(col_widths) < layout.num_cols:
            col_widths.append(_MIN_COL_WIDTH)
        return col_widths

    # Global exact width for all columns
    if exact_col_width is not None:
        return [exact_col_width] * layout.num_cols

    return _compute_auto_col_widths(
        selectors=layout.col_selectors,
        header_labels_resolved=layout.header_labels_resolved,
        data_rows=layout.data_rows,
        row_is_mapping=layout.row_is_mapping,
        max_col_width=max_col_width,
        max_col_widths=max_col_widths,
    )
