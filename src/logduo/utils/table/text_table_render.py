"""
text_table_render.py

Last edited: 2026-06-18
"""

from typing import Any

from logduo.utils.table.text_table_classes_and_constants import _RULE_CHAR, ANSI_BOLD, ANSI_DIM, ANSI_RESET
from logduo.utils.table.text_table_layout import _get_cell_from_row
from logduo.utils.table.text_table_widths import (
    _stringify_for_table,
    _visible_len,
    _wrap_cell_text_for_width,
)


# --- _build_table_block_for_column_group() -----------------------------------------------
def _build_table_block_for_column_group(
    *,
    group_indices: list[int],
    selectors: list[int | str],
    header_labels_resolved: list[str],
    data_rows: list[Any],
    col_widths: list[int],
    padding_spaces: int,
    max_cell_lines: int,
    row_is_mapping: bool,
) -> str:
    pad_str = " " * padding_spaces

    # --- Header (multi-line, aligned with data rows) ---
    block_lines: list[str] = []
    wrapped_header_columns: list[list[str]] = []
    header_height = 1

    for col_index in group_indices:
        wrapped = _wrap_cell_text_for_width(
            header_labels_resolved[col_index],
            col_width=col_widths[col_index],
            max_cell_lines=max_cell_lines,
        )

        if not wrapped:
            wrapped = [""]

        wrapped_header_columns.append(wrapped)
        header_height = max(header_height, len(wrapped))

    header_width = _total_width_for_column_group(
        group_indices,
        col_widths,
        padding_spaces,
    )
    rule = _RULE_CHAR * header_width
    block_lines.append(rule)

    for line_number in range(header_height):
        header_line_parts: list[str] = []
        for col_pos, col_index in enumerate(group_indices):
            col_lines = wrapped_header_columns[col_pos]

            part = (
                col_lines[line_number]
                if line_number < len(col_lines)
                else ""
            )

            header_line_parts.append(_visible_ljust(part, col_widths[col_index]))

        header_text = pad_str.join(header_line_parts)
        block_lines.append(f"{ANSI_BOLD}{header_text}{ANSI_RESET}")

    block_lines.append(rule)


    # Data rows
    for row_obj in data_rows:
        wrapped_columns: list[list[str]] = []
        row_height = 1
        for col_index in group_indices:
            selector = selectors[col_index]
            cell_val = _get_cell_from_row(row_obj, selector, row_is_mapping)
            wrapped_cell = _wrap_cell_text_for_width(
                _stringify_for_table(cell_val),
                col_width=col_widths[col_index],
                max_cell_lines=max_cell_lines,
            )
            if not wrapped_cell:
                wrapped_cell = [""]
            wrapped_columns.append(wrapped_cell)
            row_height = max(row_height, len(wrapped_cell))

        for line_number in range(row_height):
            row_line_parts: list[str] = []
            for col_pos, col_index in enumerate(group_indices):
                col_lines = wrapped_columns[col_pos]

                if line_number < len(col_lines):
                    part_text = col_lines[line_number]
                else:
                    part_text = ""  # keep explicit (important for clarity)
                row_line_parts.append(_visible_ljust(part_text, col_widths[col_index]))
            block_lines.append(pad_str.join(row_line_parts))

    return "\n".join(block_lines)


# --- wrap_with_title_block() --------------------------------------------------
def _render_title_and_body(
    *,
    body: str,
    title: str | None,
    subtitle: str | None,
    wrap_table_width: int,
) -> str:
    if not title and not subtitle:
        return body
    parts: list[str] = []
    if title:
        title_text = title
        if _visible_len(title_text) > wrap_table_width:
            title_text = title_text[:wrap_table_width]
        parts.append(f"{ANSI_BOLD}{title_text}{ANSI_RESET}")
    if subtitle:
        subtitle_text = subtitle
        if _visible_len(subtitle_text) > wrap_table_width:
            subtitle_text = subtitle_text[:wrap_table_width]
        parts.append(f"{ANSI_DIM}{subtitle_text}{ANSI_RESET}")
    parts.extend([
        body,
    ])
    return "\n".join(parts)

# --- _group_columns_to_fit_wrap_table_width() ----------------------------------------------
def _group_columns_to_fit_wrap_table_width(
    *,
    num_cols: int,
    col_widths: list[int],
    padding_spaces: int,
    wrap_table_width: int,
    wrap_table: bool,
) -> list[list[int]]:
    """Decide how to split columns into blocks; first column repeats in each."""
    if num_cols == 1:
        return [[0]]

    if not wrap_table:
        return [list(range(num_cols))]

    groups: list[list[int]] = []
    base_index = 0
    remaining_indices = list(range(1, num_cols))

    current_group = [base_index]
    for col_index in remaining_indices:
        trial_group = current_group + [col_index]
        if (
            _total_width_for_column_group(trial_group, col_widths, padding_spaces)
            <= wrap_table_width
        ):
            current_group = trial_group
        else:
            groups.append(current_group)
            current_group = [base_index, col_index]
    groups.append(current_group)

    if not wrap_table:
        if not groups:
            return []
        first_group = groups[0]
        while (
            first_group
            and _total_width_for_column_group(first_group, col_widths, padding_spaces)
            > wrap_table_width
        ):
            if len(first_group) <= 1:
                break
            first_group = first_group[:-1]
        return [first_group] if first_group else []

    return groups


# --- _total_width_for_column_group() ------------------------------------------
def _total_width_for_column_group(
    group_indices: list[int], col_widths: list[int], padding_spaces: int
) -> int:
    if not group_indices:
        return 0
    sum_cols = sum(col_widths[i] for i in group_indices)
    gaps = padding_spaces * (len(group_indices) - 1)
    return sum_cols + gaps


def _visible_ljust(text: str, width: int) -> str:
    return text + (" " * max(0, width - _visible_len(text)))


