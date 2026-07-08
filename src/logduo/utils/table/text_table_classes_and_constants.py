"""
text_table_classes_and_constants.py

Shared classes and constants

Last edited: 2026_06-18
"""
from dataclasses import dataclass
from typing import Any

_RULE_CHAR = "─"
_MIN_COL_WIDTH = 3
_DEFAULT_MAX_CELL_LINES = 3
_DEFAULT_PADDING = 3
_DEFAULT_WRAP_TABLE_WIDTH = 120

ANSI_DIM = "\033[2m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"
_DEFAULT_BORDER_STYLE = ANSI_DIM
_DEFAULT_HEADER_STYLE = ANSI_BOLD


@dataclass
class TableLayout:
    """
    Resolved table structure used by the rendering pipeline.
    Contains the normalized table shape after row inspection,
    column resolution, and header resolution.
    """
    row_is_mapping: bool
    col_selectors: list[int | str]
    num_cols: int
    header_labels_resolved: list[str]
    data_rows: list[Any]


