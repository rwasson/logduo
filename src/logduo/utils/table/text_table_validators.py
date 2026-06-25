"""
test_table_validators.py

Last edited: 2026-1-19
"""
import warnings
from dataclasses import dataclass
from collections.abc import Sequence


from logduo.internals.api_arg_resolvers.api_arg_resolver_helpers import (
    _resolve_bool_arg,
    _resolve_int_arg,
)

from logduo.utils.table.text_table_classes_and_constants import _MIN_COL_WIDTH
from logduo.utils.table.text_table_widths import _visible_len


@dataclass
class WidthSettings:
    max_col_width: int | None
    max_col_widths: list[int] | None
    exact_col_width: int | None
    exact_col_widths: list[int] | None


def _normalize_global_col_widths(
        max_col_widths: int | list[int] | None = None,
        exact_col_widths: int | list[int] | None = None,
) -> WidthSettings:


    if isinstance(max_col_widths, int):
        max_col_width = max_col_widths
        max_col_widths_list = None
    elif max_col_widths is None or isinstance(max_col_widths, list):
        max_col_width = None
        max_col_widths_list = max_col_widths
    else:
        raise ValueError(
          "max_col_widths must be an int or list[int]"
        )

    if isinstance(exact_col_widths, int):
        exact_col_width = exact_col_widths
        exact_col_widths_list = None
    elif exact_col_widths is None or isinstance(exact_col_widths, list):
        exact_col_width = None
        exact_col_widths_list = exact_col_widths
    else:
        raise ValueError(
            "exact_col_widths must be an int or list[int]"
        )

    return WidthSettings(
        max_col_width=max_col_width,
        max_col_widths=max_col_widths_list,
        exact_col_width=exact_col_width,
        exact_col_widths=exact_col_widths_list,
    )


# --- validate_table_args() ----------------------------------------------------
def _validate_table_args(
    *,
    columns: Sequence[int | str] | None,
    first_row_is_header: bool,
    header_labels: list[str] | None,
    padding: int,
    exact_col_width: int | None,
    exact_col_widths: list[int] | None,
    max_col_width: int | None,
    max_col_widths: list[int] | None,
    indent: int | None,
    max_cell_lines: int | None,
    wrap_table_width: int,
    wrap_table: bool,
    title: str | None,
    subtitle: str | None,
) -> None:

    _resolve_bool_arg(arg_name="first_row_is_header", value=first_row_is_header)
    _resolve_bool_arg(arg_name="wrap_table", value=wrap_table)
    _resolve_int_arg(arg_name="padding", value=padding, min_value=0)
    _resolve_int_arg(arg_name="wrap_table_width", value=wrap_table_width, min_value=5)

    if indent is not None:
        _resolve_int_arg(arg_name="indent", value=indent, min_value=0)
    if max_cell_lines is not None:
        _resolve_int_arg(arg_name="max_cell_lines", value=max_cell_lines, min_value=1)

    if columns is not None and len(columns) == 0:
        raise ValueError("columns cannot be empty. Omit instead.")
    if columns is not None:
        for i, value in enumerate(columns):
            if not isinstance(value, (str, int)):
                raise ValueError(f"columns[{i}] must be str or int (not {value!r})")

    _validate_title_and_header(
            title=title,
            subtitle=subtitle,
            wrap_table_width=wrap_table_width,
            header_labels=header_labels,
            columns=columns,
    )

    if exact_col_width is not None:
        _resolve_int_arg(
            arg_name="exact_col_width",
            value=exact_col_width,
            min_value=_MIN_COL_WIDTH,
        )
    if exact_col_widths is not None and not isinstance(exact_col_widths, list):
        raise ValueError("exact_col_widths must be an int or list[int]")
    if exact_col_widths is not None:
        if isinstance(exact_col_widths, list):
            if len(exact_col_widths) == 0:
                raise ValueError("exact_col_widths cannot be empty")
            for i, width in enumerate(exact_col_widths):
                _resolve_int_arg(
                    arg_name=f"exact_col_widths[{i}]",
                    value=width,
                    min_value=1,
                )
        else:
            raise ValueError("exact_col_widths must be an int or list[int]")

    if max_col_width is not None:
        _resolve_int_arg(
            arg_name="max_col_width",
            value=max_col_width,
            min_value=_MIN_COL_WIDTH,
        )
    if max_col_widths is not None:
        if isinstance(max_col_widths, list):
            if len(max_col_widths) == 0:
                raise ValueError("max_col_widths cannot be empty")
            for i, width in enumerate(max_col_widths):
                _resolve_int_arg(
                    arg_name=f"max_col_widths[{i}]",
                    value=width,
                    min_value=1,
                )
        else:
            raise ValueError("max_col_widths must be an int or list[int]")

    has_exact_width = exact_col_width is not None or exact_col_widths is not None
    has_max_width = max_col_width is not None or max_col_widths is not None

    if has_exact_width and has_max_width:
        warnings.warn(
            "max_col_widths ignored because exact widths were provided.",
            stacklevel=2,
        )



# --- _validate_num_cols_args() -----------------------------------------------
def _validate_num_cols_args(
    columns: Sequence[int | str] | None,
    header_labels: list[str] | None,
    max_col_widths: list[int] | None,
    exact_col_widths: list[int] | None,
    num_cols: int,
) -> None:

    if columns is not None and len(columns) != num_cols:
        raise ValueError(
            f"columns must have the same number of entries "
            f"as the number of columns ({num_cols}).\n"
        )
    if header_labels is not None and len(header_labels) != num_cols:
        raise ValueError(
            f"header_labels must have the same number of entries "
            f"as the number of columns ({num_cols}).\n"
        )

    if (
            exact_col_widths is not None
            and len(exact_col_widths) > 1
            and len(exact_col_widths) != num_cols
    ):
        raise ValueError(
            f"exact_col_widths must have either:"
            f" 1 entry (global exact_col_width)"
            f" {num_cols} entries (must match number of columns).\n"
        )

    if (
            max_col_widths is not None
            and len(max_col_widths) > 1
            and len(max_col_widths) != num_cols
    ):
        raise ValueError(
            f"max_col_widths must have either:"
            f" 1 entry (global max_col_width)"
            f" {num_cols} entries (must match number of columns).\n"
        )


def _validate_title_and_header(
    *,
    title: str | None,
    subtitle: str | None,
    wrap_table_width: int,
    header_labels: list[str] | None,
    columns: Sequence[int | str] | None
) -> None:

    if title is not None and not isinstance(title, str):
        raise ValueError(f"title must be a string or None (not {title!r})")
    if title is not None and "\n" in title:
        raise ValueError("title must be a single line")
    if title and _visible_len(title) > wrap_table_width:
        warnings.warn("title exceeds wrap_table_width and will be truncated")

    if subtitle is not None and not isinstance(subtitle, str):
        raise ValueError(f"subtitle must be a string or None (not {title!r})")
    if subtitle is not None and "\n" in subtitle:
        raise ValueError("subtitle must be a single line")
    if subtitle and _visible_len(subtitle) > wrap_table_width:
        warnings.warn("subtitle exceeds wrap_table_width and will be truncated")

    if header_labels is not None and len(header_labels) == 0:
        raise ValueError("header_labels cannot be empty.")
    if header_labels is not None:
        if not isinstance(header_labels, list):
            raise ValueError("header_labels must be a list[str]")
        for i, value in enumerate(header_labels):
            if not isinstance(value, str):
                raise ValueError(f"header_labels[{i}] must be a string (not {value!r})")
    if (
            columns is not None
            and header_labels is not None
            and len(header_labels) != len(columns)
    ):
        raise ValueError(
            "header_labels length must match columns length.\n"
            f"columns has {len(columns)} entries.\n"
            f"header_labels has {len(header_labels)} entries."
        )


