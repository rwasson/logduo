"""
text_table

Plain-text table rendering utilities for logduo.

Provides a lightweight, dependency-free table builder designed for:
  - display of dict, dataclass instances, dataclass types
  - tables that can be rendered with ANSI  colors on console and plain text in logs


Features:
  - Auto detection of dict and dataclass objects
  - Auto column sizing with bounds
  - Optional multi-block column wrapping
  - Per-cell word wrapping with truncation
  - Optional centered title block

This module intentionally avoids third-party table libraries
to keep output deterministic and log-safe.

Public API:
  - text_table()

Last edited: 2026-5-27
"""

from __future__ import annotations

from collections.abc import Sequence
from logduo.utils.table.reshape_dict_rows import  _reshape_dict_obj_to_dict_rows
from logduo.utils.table.text_table_layout import _resolve_table_layout
from logduo.utils.table.text_table_render import (
    _build_table_block_for_column_group,
    _group_columns_to_fit_wrap_table_width,
    _render_title_and_body,
)
from logduo.utils.table.text_table_classes_and_constants import (
    _DEFAULT_PADDING,
    _DEFAULT_WRAP_TABLE_WIDTH,
    _DEFAULT_MAX_CELL_LINES,
)
from logduo.utils.table.text_table_validators import (
    _normalize_global_col_widths,
    _validate_table_args,
    _validate_num_cols_args,
)
from logduo.utils.table.text_table_widths import _resolve_column_widths


__all__ = ["text_table"]


# --- Public API ---------------------------------------------------------------
def text_table(
    rows: object,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    columns: Sequence[int | str] | None = None,
    first_row_is_header: bool = False,
    header_labels: list[str] | None = None,
    max_col_widths: int | list[int]  | None = None,
    exact_col_widths: int | list[int] | None = None,
    indent: int | None = None,
    max_cell_lines: int | None = _DEFAULT_MAX_CELL_LINES,
    wrap_table: bool = True,
    wrap_table_width: int = _DEFAULT_WRAP_TABLE_WIDTH,
    padding: int = _DEFAULT_PADDING,
) -> str:
    """
    Purpose
    -------
    Creates a string that renders as a table when printed or logged.
    ANSI colors supported in console.

    Supported inputs:
    - tabular row data (list of dicts, lists, or tuples)
    - dict
    - dataclass instance
    - dataclass type

    Dicts and dataclass objects are automatically rendered as
    field/value or field/type inspection tables.

    Examples
    --------
    Render a dictionary:
        log(text_table(my_dict))

    Render tabular data:
        log(
            text_table(
                rows,
                columns=["name", "age", "bio"],
                max_col_widths=25,
            )
        )

    Arguments
    ---------
    rows : object
        Data to render.
    title : str | None
        Optional title displayed above the table.
    subtitle: str | None
        Optional subtitle displayed above the table.
    first_row_is_header : bool
        Treat the first row as a header source row.
    columns : Sequence[str | int] | None
        Select columns and display order using keys or column indices.
    header_labels : list[str] | None
        Explicit column labels.
        If omitted, labels are derived from columns or the header row.
    max_col_widths : int | list[int] | None
        Maximum column widths.
        Columns may be narrower if content requires less space.
        A single integer applies to all columns.
        Ignored if exact_col_widths is provided.
    exact_col_widths : int | list[int] | None
        Fixed column widths.
        A single integer applies to all columns.
        Overrides automatic sizing.
    indent: int | None
        Left indent table by specified number of spaces.
    max_cell_lines : int | None
        Maximum displayed lines per cell.
        None disables truncation.
    wrap_table : bool
        Allow wide tables to be split into multiple blocks.
    wrap_table_width : int
        Maximum width of a rendered table block.
    padding : int
        Spaces between columns.

    Notes
    -----
    - Wide tables may be split into multiple blocks when wrap_table=True.
    - ANSI colors supported in console.
    """
    if not rows:
        raise ValueError("Cannot render empty table.")

    widths = _normalize_global_col_widths(
        exact_col_widths=exact_col_widths,
        max_col_widths=max_col_widths,
    )


    # if rows object is not a dictionary, dict_rows is None
    dict_rows, default_header_labels = _reshape_dict_obj_to_dict_rows(rows)
    if dict_rows is not None:
        rows = dict_rows
        if columns is None:
            columns = ["field", "value"]
        if header_labels is None:
            header_labels = default_header_labels
        if max_col_widths is None and exact_col_widths is None:
            widths.max_col_widths = [40, 70]

    if not isinstance(rows, list):
        raise ValueError(
            "rows must be either:\n"
            "    - list of row records\n"
            "    - dict\n"
            "    - dataclass instance\n"
            "    - dataclass type"
        )

    _validate_table_args(
        title=title,
        subtitle=subtitle,
        columns=columns,
        first_row_is_header=first_row_is_header,
        header_labels=header_labels,
        max_col_width=widths.max_col_width,
        max_col_widths=widths.max_col_widths,
        indent=indent,
        max_cell_lines=max_cell_lines,
        exact_col_width=widths.exact_col_width,
        exact_col_widths=widths.exact_col_widths,
        wrap_table_width=wrap_table_width,
        wrap_table=wrap_table,
        padding=padding,
    )

    # layout is an instance of TableLayout
    layout = _resolve_table_layout(
        rows=rows,
        columns=columns,
        first_row_is_header=first_row_is_header,
        header_labels=header_labels,
    )

    if layout is None:
        return ""

    _validate_num_cols_args(
        columns=columns,
        header_labels=header_labels,
        max_col_widths=widths.max_col_widths,
        exact_col_widths=widths.exact_col_widths,
        num_cols=layout.num_cols,
    )

    col_widths = _resolve_column_widths(
        layout=layout,
        exact_col_width=widths.exact_col_width,
        exact_col_widths=widths.exact_col_widths,
        max_col_width=widths.max_col_width,
        max_col_widths=widths.max_col_widths,
    )


    # column_groups = list of lists of column numbers
    # if width of table < wrap_table_width, then len(column_groups) = 1
    column_groups = _group_columns_to_fit_wrap_table_width(
        num_cols=layout.num_cols,
        col_widths=col_widths,
        padding_spaces=padding,
        wrap_table_width=wrap_table_width,
        wrap_table=wrap_table,
    )

    if not column_groups:
        return ""

    blocks: list[str] = []
    assert max_cell_lines is not None

    for group_indices in column_groups:
        if not group_indices:
            continue

        block_text = _build_table_block_for_column_group(
            group_indices=group_indices,
            selectors=layout.col_selectors,
            header_labels_resolved=layout.header_labels_resolved,
            data_rows=layout.data_rows,
            col_widths=col_widths,
            padding_spaces=padding,
            max_cell_lines=max_cell_lines,
            row_is_mapping=layout.row_is_mapping,
        )

        if block_text:
            blocks.append(block_text)

    if not blocks:
        return ""

    body_text = "\n\n".join(blocks)

    table_str = _render_title_and_body(
        body=body_text,
        title=title,
        subtitle=subtitle,
        wrap_table_width=wrap_table_width,
    )

    if indent:
        indent_str = " " * indent
        table_str = "\n".join(
            indent_str + line if line else ""
            for line in table_str.splitlines()
        )

    return table_str + "\n"


# Supported input shapes
#
# Data                                        Python shape                    (rows = N, cols = M)
# ------------------------------------------  ------------------------------  ----------------------------
#
# ["Alice", "Bob"]                            list of scalars                 rows = 2, cols = 1
#
# [["Alice", 30], ["Bob", 25]]                list of sequences               rows = 2, cols = 2
#
# [{"name": "Alice"}, {"name": "Bob"}]        list of mappings                rows = 2, cols = 1
#
# {"name": "Alice", "age": 30}                mapping                         rows = 2, cols = 1
#
# Person(name="Alice", age=30)                dataclass instance              rows = 2, cols = 1
#
# Notes:
# - A mapping is any dict-like object implementing the Mapping protocol.
# - A sequence is an ordered container such as list or tuple.
# - Scalars include str, int, float, bool, Path, datetime, etc.
# - Lists are treated as collections of rows.
# - Mappings and dataclass objects are treated as a single record and
#   rendered as field/value inspection tables.

