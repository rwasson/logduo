"""
text_table_layout.py

Resolve table columns, headers, and data rows before rendering.

Last edited: 2026-06-24
"""

from collections.abc import Mapping, Sequence
from typing import Any

from logduo.utils.table.text_table_classes_and_constants import TableLayout


# --- _resolve_table_layout() --------------------------------------------------
def _resolve_table_layout(
    *,
    rows: list[Any],
    columns: Sequence[int | str] | None,
    first_row_is_header: bool,
    header_labels: list[str] | None,
) -> TableLayout | None:

    """Resolve table structure from mapping, sequence, or scalar rows."""

    first_row_index: int | None = None

    for index, row in enumerate(rows):
        if row is not None:
            first_row_index = index
            break

    if first_row_index is None:
        return None

    if header_labels is not None and first_row_is_header:
        raise ValueError(
            "header_labels and first_row_is_header cannot be used together."
        )

    first_row = rows[first_row_index]
    if isinstance(first_row, Mapping):
        return _resolve_mapping_layout(
            rows=rows,
            first_row=first_row,
            first_row_index=first_row_index,
            columns=columns,
            first_row_is_header=first_row_is_header,
            header_labels=header_labels,
        )

    if isinstance(first_row, Sequence) and not isinstance(first_row, (str, bytes)):
        return _resolve_sequence_layout(
            rows=rows,
            first_row=first_row,
            first_row_index=first_row_index,
            columns=columns,
            first_row_is_header=first_row_is_header,
            header_labels=header_labels,
        )

    return _resolve_scalar_layout(
        rows=rows,
        first_row=first_row,
        first_row_index=first_row_index,
        columns=columns,
        first_row_is_header=first_row_is_header,
        header_labels=header_labels,
    )

# === Internal helpers =========================================================

# --- _resolve_mapping_layout() ------------------------------------------------
def _resolve_mapping_layout(
    *,
    rows: list[Any],
    first_row: Mapping[Any, Any],
    first_row_index: int,
    columns: Sequence[int | str] | None,
    first_row_is_header: bool,
    header_labels: list[str] | None,
) -> TableLayout:
    """Resolve layout for dictionary-like rows."""
    available_column_names: list[Any] = []

    for row in rows:
        if not isinstance(row, Mapping):
            continue
        for key in row:
            if key not in available_column_names:
                available_column_names.append(key)

    if columns is None:
        col_selectors: list[int | str] = list(available_column_names)

    else:
        col_selectors = list(columns)
    selected_column_names: list[str] = []

    for selector in col_selectors:
        if isinstance(selector, str):
            if selector not in available_column_names:
                raise ValueError(f"Unknown column name: {selector!r}")
            selected_column_names.append(selector)
            continue

        if not 0 <= selector < len(available_column_names):
            raise ValueError(f"Column index {selector} is out of range.")
        selected_column_names.append(str(available_column_names[selector]))

    if first_row_is_header:
        header_source_row: Mapping[Any, Any] | None = first_row
        data_rows = (rows[:first_row_index] + rows[first_row_index + 1:])
    else:
        header_source_row = None
        data_rows = list(rows)
    if header_labels is not None:
        header_labels_resolved = list(header_labels)
    elif header_source_row is not None:
        header_labels_resolved = [
            str(
                _get_cell_from_row(
                    header_source_row,
                    selector,
                    True,
                )
            )
            for selector in col_selectors
        ]
    else:
        header_labels_resolved = [
            column_name.replace("_", " ").title()
            for column_name in selected_column_names
        ]
    if len(header_labels_resolved) != len(col_selectors):
        raise ValueError(
            "The number of header labels must match "
            "the number of selected columns."
        )

    return TableLayout(
        row_is_mapping=True,
        col_selectors=col_selectors,
        num_cols=len(col_selectors),
        header_labels_resolved=header_labels_resolved,
        data_rows=data_rows,
    )

# --- _resolve_sequence_layout() ----------------------------------------------
def _resolve_sequence_layout(
    *,
    rows: list[Any],
    first_row: Sequence[Any],
    first_row_index: int,
    columns: Sequence[int | str] | None,
    first_row_is_header: bool,
    header_labels: list[str] | None,
) -> TableLayout:
    """Resolve layout for list-like rows."""
    sequence_selectors: list[int] = []

    if columns is None:
        sequence_selectors = list(range(len(first_row)))
    else:
        for selector in columns:
            if not isinstance(selector, int):
                raise ValueError(
                    "Sequence rows require integer column selectors."
                )

            if not 0 <= selector < len(first_row):
                raise ValueError(
                    f"Column index {selector} is out of range."
                )
            sequence_selectors.append(selector)

    if first_row_is_header:
        header_source_row: Sequence[Any] | None = first_row
        data_rows = (rows[:first_row_index] + rows[first_row_index + 1:])
    else:
        header_source_row = None
        data_rows = list(rows)

    if header_labels is not None:
        header_labels_resolved = list(header_labels)
    elif header_source_row is not None:
        header_labels_resolved = []
        for display_index, selector in enumerate(sequence_selectors):
            header_value = header_source_row[selector]
            if header_value is None or header_value == "":
                header_labels_resolved.append(f"col{display_index + 1}")
            else:
                header_labels_resolved.append(str(header_value))
    else:
        header_labels_resolved = [
            f"col{selector + 1}"
            for selector in sequence_selectors
        ]

    if len(header_labels_resolved) != len(sequence_selectors):
        raise ValueError(
            "The number of header labels must match "
            "the number of selected columns."
        )
    col_selectors: list[int | str] = list(sequence_selectors)

    return TableLayout(
        row_is_mapping=False,
        col_selectors=col_selectors,
        num_cols=len(col_selectors),
        header_labels_resolved=header_labels_resolved,
        data_rows=data_rows,
    )

# --- _resolve_scalar_layout() ------------------------------------------------
def _resolve_scalar_layout(
    *,
    rows: list[Any],
    first_row: Any,
    first_row_index: int,
    columns: Sequence[int | str] | None,
    first_row_is_header: bool,
    header_labels: list[str] | None,
) -> TableLayout:
    """Resolve layout for scalar rows."""
    if columns is None:
        col_selectors: list[int | str] = [0]
    else:
        col_selectors = list(columns)
        for selector in col_selectors:
            if selector != 0:
                raise ValueError(
                    "Scalar rows support only column index 0."
                )

    if first_row_is_header:
        header_labels_resolved = [str(first_row)]
        data_rows = (rows[:first_row_index] + rows[first_row_index + 1:])
    elif header_labels is not None:
        header_labels_resolved = list(header_labels)
        data_rows = list(rows)
    else:
        header_labels_resolved = ["col1"]
        data_rows = list(rows)

    if len(header_labels_resolved) != len(col_selectors):
        raise ValueError(
            "The number of header labels must match "
            "the number of selected columns."
        )

    return TableLayout(
        row_is_mapping=False,
        col_selectors=col_selectors,
        num_cols=len(col_selectors),
        header_labels_resolved=header_labels_resolved,
        data_rows=data_rows,
    )


# --- _get_cell_from_row() -----------------------------------------------------
def _get_cell_from_row(  # noqa: PLR0911
    row_obj: Any,
    col_selector: int | str,
    row_is_mapping: bool,
) -> Any:
    """Return one cell using a key or positional column selector."""

    # --- Mapping row ---
    if row_is_mapping:
        if not isinstance(row_obj, Mapping):
            return ""

        if isinstance(col_selector, str):
            return row_obj.get(col_selector, "")

        values = list(row_obj.values())

        if 0 <= col_selector < len(values):
            return values[col_selector]

        return ""

    # --- Sequence row ---
    if isinstance(row_obj, Sequence) and not isinstance(
        row_obj,
        (str, bytes),
    ):
        if not isinstance(col_selector, int):
            return ""

        if 0 <= col_selector < len(row_obj):
            return row_obj[col_selector]

        return ""

    # --- Scalar row ---
    if col_selector == 0:
        return row_obj

    return ""


'''
# --- _resolve_table_layout() --------------------------------------------------
def _resolve_table_layout(
    *,
    rows: list[Any],
    columns: Sequence[int | str] | None,
    first_row_is_header: bool,
    header_labels: list[str] | None,
) -> TableLayout | None:
    """Resolve table structure from mapping, sequence, or scalar rows."""

    # --- Find the first usable row ---
    first_row_index: int | None = None

    for index, row in enumerate(rows):
        if row is not None:
            first_row_index = index
            break

    if first_row_index is None:
        return None

    first_row = rows[first_row_index]

    if header_labels is not None and first_row_is_header:
        raise ValueError(
            "header_labels and first_row_is_header cannot be used together."
        )

    # --- Mapping rows ---
    if isinstance(first_row, Mapping):
        available_column_names: list[Any] = []

        for row in rows:
            if isinstance(row, Mapping):
                for key in row:
                    if key not in available_column_names:
                        available_column_names.append(key)

        if columns is None:
            col_selectors: list[int | str] = list(available_column_names)
        else:
            col_selectors = list(columns)

        selected_column_names: list[str] = []

        for selector in col_selectors:
            if isinstance(selector, str):
                if selector not in available_column_names:
                    raise ValueError(
                        f"Unknown column name: {selector!r}"
                    )

                selected_column_names.append(selector)
                continue

            if not 0 <= selector < len(available_column_names):
                raise ValueError(
                    f"Column index {selector} is out of range."
                )

            selected_column_names.append(
                str(available_column_names[selector])
            )

        if first_row_is_header:
            header_source_row = first_row
            data_rows = (
                rows[:first_row_index]
                + rows[first_row_index + 1:]
            )
        else:
            header_source_row = None
            data_rows = list(rows)

        if header_labels is not None:
            header_labels_resolved = list(header_labels)


        elif header_source_row is not None:
            header_labels_resolved = [
                str(
                    _get_cell_from_row(
                        header_source_row,
                        selector,
                        True,
                    )
                )
                for selector in col_selectors
            ]

        else:
            header_labels_resolved = [
                column_name.replace("_", " ").title()
                for column_name in selected_column_names
            ]

        if len(header_labels_resolved) != len(col_selectors):
            raise ValueError(
                "The number of header labels must match "
                "the number of selected columns."
            )

        return TableLayout(
            row_is_mapping=True,
            col_selectors=col_selectors,
            num_cols=len(col_selectors),
            header_labels_resolved=header_labels_resolved,
            data_rows=data_rows,
        )

    # --- Sequence rows ---
    if isinstance(first_row, Sequence) and not isinstance(
        first_row,
        (str, bytes),
    ):
        if columns is None:
            sequence_selectors = list(range(len(first_row)))
        else:
            sequence_selectors = []

            for selector in columns:
                if not isinstance(selector, int):
                    raise ValueError(
                        "Sequence rows require integer column selectors."
                    )

                if not 0 <= selector < len(first_row):
                    raise ValueError(
                        f"Column index {selector} is out of range."
                    )

                sequence_selectors.append(selector)

        if first_row_is_header:
            header_source_row = first_row
            data_rows = (
                rows[:first_row_index]
                + rows[first_row_index + 1:]
            )
        else:
            header_source_row = None
            data_rows = list(rows)

        if header_labels is not None:
            header_labels_resolved = list(header_labels)


        elif header_source_row is not None:
            header_labels_resolved = []

            for display_index, selector in enumerate(sequence_selectors):
                header_value = header_source_row[selector]

                if header_value is None or header_value == "":
                    header_labels_resolved.append(
                        f"col{display_index + 1}"
                    )
                else:
                    header_labels_resolved.append(str(header_value))


        else:
            header_labels_resolved = [
                f"col{selector + 1}"
                for selector in sequence_selectors
            ]

        if len(header_labels_resolved) != len(sequence_selectors):
            raise ValueError(
                "The number of header labels must match "
                "the number of selected columns."
            )

        col_selectors = list(sequence_selectors)

        return TableLayout(
            row_is_mapping=False,
            col_selectors=col_selectors,
            num_cols=len(col_selectors),
            header_labels_resolved=header_labels_resolved,
            data_rows=data_rows,
        )

    # --- Scalar rows ---
    if columns is None:
        scalar_selectors = [0]
    else:
        scalar_selectors = list(columns)

        for selector in scalar_selectors:
            if selector != 0:
                raise ValueError(
                    "Scalar rows support only column index 0."
                )

    if first_row_is_header:
        header_labels_resolved = [str(first_row)]
        data_rows = (
            rows[:first_row_index]
            + rows[first_row_index + 1:]
        )

    elif header_labels is not None:
        header_labels_resolved = list(header_labels)
        data_rows = list(rows)

    else:
        header_labels_resolved = ["col1"]
        data_rows = list(rows)

    if len(header_labels_resolved) != len(scalar_selectors):
        raise ValueError(
            "The number of header labels must match "
            "the number of selected columns."
        )

    col_selectors = list(scalar_selectors)

    return TableLayout(
        row_is_mapping=False,
        col_selectors=col_selectors,
        num_cols=len(col_selectors),
        header_labels_resolved=header_labels_resolved,
        data_rows=data_rows,
    )
'''