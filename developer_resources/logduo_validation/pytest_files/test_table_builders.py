"""
test_table_builders.py

Last edited: 2026-06-25
"""
from dataclasses import dataclass

import pytest

from logduo import text_table


# used for testing build_dict_table()
@dataclass
class Person:
    name: str
    age: int


# --- test_01_text_table_fixed_col_widths_none_entry_raises() ---
def test_01_text_table_fixed_col_widths_none_entry_raises():
    with pytest.raises(ValueError):
        text_table(
            rows=[{"a": 1}],
            exact_col_widths=[10, None],
        )


# --- test_02_text_table_fixed_col_widths_zero_raises() -----------------------
def test_02_text_table_fixed_col_widths_zero_raises():
    with pytest.raises(ValueError):
        text_table(
            rows=[{"a": 1}],
            exact_col_widths=[0],
        )


# --- test_03_text_table_fixed_col_widths_negative_raises() -------------------
def test_03_text_table_fixed_col_widths_negative_raises():
    with pytest.raises(ValueError):
        text_table(
            rows=[{"a": 1}],
            exact_col_widths=[-5],
        )


# --- test_04_text_table_fixed_col_widths_valid() -----------------------------
def test_04_text_table_fixed_col_widths_valid():
    result = text_table(
        rows=[{"a": "hello"}],
        exact_col_widths=[10],
    )

    assert "hello" in result


# --- test_05_text_table_max_col_widths_applied() ------------------------
def test_05_text_table_max_col_widths_applied():

    result = text_table(
        rows=[{
            "field": "cwd",
            "value": "/very/long/path/that/should/not/be/wrapped"
        }],
        columns=["field", "value"],
        first_row_is_header=False,
        max_col_widths=[20, 50],
    )

    assert "/very/long/path/that/should/not/be/wrapped" in result


# --- test_06_text_table_fixed_and_max_widths_warn() --------------------------
def test_06_text_table_fixed_and_max_widths_warn():

    with pytest.warns(UserWarning):
        text_table(
            rows=[{"a": 1}],
            exact_col_widths=[10],
            max_col_widths=[20],
        )


# --- test_07_text_table_empty_fixed_widths_raises() --------------------------
def test_07_text_table_empty_fixed_widths_raises():

    with pytest.raises(ValueError):
        text_table(
            rows=[{"a": 1}],
            exact_col_widths=[],
        )


# --- test_08_text_table_empty_max_widths_raises() ----------------------------
def test_08_text_table_empty_max_widths_raises():

    with pytest.raises(ValueError):
        text_table(
            rows=[{"a": 1}],
            max_col_widths=[],
        )


# --- test_09_text_table_padding_type_raises() --------------------------------
def test_09_text_table_padding_type_raises():

    with pytest.raises(ValueError):
        text_table(
            rows=[{"a": 1}],
            padding="5",    # noqa, testing an intentional error
        )


# --- test_10_text_table_fixed_widths_override_max_widths_warns() ----------------
def test_10_text_table_fixed_widths_override_max_widths_warns():

    with pytest.warns(UserWarning):

        text_table(
            rows=[{"a": 1}],
            exact_col_widths=[10],
            max_col_widths=[20],

        )


# --- test_11_text_table_dict() ------------------------------------------
def test_11_text_table_dict():

    result = text_table({
        "name": "alice",
        "age": 30,

    })

    assert "name" in result
    assert "alice" in result
    assert "age" in result



# --- test_12_build_dict_table_dataclass_instance() ----------------------------
def test_12_text_table_dataclass_instance():

    result = text_table(
        Person("alice", 30)
    )

    assert "name" in result
    assert "alice" in result


# ---test_13_build_dict_table_dataclass_type() --------------------------------
def test_13_text_table_dataclass_type():

    result = text_table(Person)

    assert "name" in result
    assert "age" in result



# --- test_14_build_dict_table_object() ----------------------------------------
@dataclass
class Demo1:
    x: int = 123

def test_14_text_table_object():
    result = text_table(Demo1())

    assert "x" in result
    assert "123" in result


# --- test_15_text_table_invalid_object_type_raises() ------------------
class Demo2:
    def __init__(self):
        self.x = 123

def test_15_text_table_invalid_object_type_raises():
    with pytest.raises(ValueError) as exc:
        text_table(Demo2())

    assert "rows must be either:" in str(exc.value)
    assert "dataclass instance" in str(exc.value)





# --- test_16_dataclass_type_table() -------------------------------------------
def test_16_dataclass_type_table():

    @dataclass
    class Person2:
        name: str
        age: int
        city: str

    table = text_table(Person2)

    print("")
    print("******************************************")
    print("test_16_dataclass_type_table")
    print(table)

    assert "Field" in table
    assert "Type" in table

    assert "name" in table
    assert "age" in table
    assert "city" in table

    assert "str" in table
    assert "int" in table


# --- test_17_build_dict_table_nested_object_repr() ---------------------------
def test_17_build_dict_table_nested_object_repr():

    result = text_table(
        {
            "demo": Demo2(),
        }
    )

    assert "demo" in result
    assert "Demo2" in result


# --- test_18_build_dict_table_non_string_keys() ------------------------------
def test_18_build_dict_table_non_string_keys():

    result = text_table(
        {
            123: 456,
        }
    )

    assert "123" in result
    assert "456" in result


# --- test_19_text_table_empty_rows_raises() ---------------------------
def test_19_text_table_empty_rows_raises():

    with pytest.raises(ValueError) as exc:
        text_table(rows=[])

    assert "Cannot render empty table" in str(exc.value)


# --- test_20_text_table_all_none_rows_returns_empty() -----------------------
def test_20_text_table_all_none_rows_returns_empty():

    result = text_table(
        rows=[None, None],
    )

    assert result == ""


# --- test_21_text_table_sequence_rows_auto_columns() ------------------------
def test_21_text_table_sequence_rows_auto_columns():

    result = text_table(
        rows=[
            ["name", "age"],
            ["alice", 30],
        ]
    )

    assert "name" in result
    assert "alice" in result
    assert "30" in result


# --- test_22_text_table_title_rendered() ------------------------------------
def test_22_text_table_title_rendered():

    result = text_table(
        rows=[{"a": 1}],
        title="TEST TABLE",
    )


    print("\n----- test_24_text_table_title_rendered: RESULT START -----")
    print(repr(result))
    print(result)
    print("----- RESULT END -----\n")

    assert "TEST TABLE" in result

# --- test_23_text_table_wrap_table_false() ----------------------------------
def test_23_text_table_wrap_table_false():

    result = text_table(
        rows=[
            {
                "a": "one",
                "b": "two",
                "c": "three",
                "d": "four",
            }
        ],
        wrap_table_width=20,
        wrap_table=False,
    )

    assert "one" in result


# --- test_24_build_wrap_table_truncates_with_ellipsis() ----------------------
def test_24_build_wrap_table_truncates_with_ellipsis():

    result = text_table(
        rows=[
            {
                "text": (
                    "This is a very long string that should wrap "
                    "across many lines and eventually truncate."
                )
            }
        ],
        max_col_widths=[10],
        max_cell_lines=2,
    )

    assert "..." in result


# --- test_25_text_table_fallback_scalar_row() -------------------------------
def test_25_text_table_fallback_scalar_row():

    result = text_table(
        rows=[
            "header",
            "value",
        ]
    )

    assert "header" in result
    assert "value" in result


# --- test_26_text_table_empty_columns_raises() ------------------------
def test_26_text_table_empty_columns_raises():

    with pytest.raises(ValueError) as exc:
        text_table(
            rows=[{"a": 1}],
            columns=[],
        )

    assert "columns cannot be empty" in str(exc.value)


# --- test_27_text_table_long_title() -----------------------------------------

def test_27_text_table_long_title():
    result = text_table(
        rows=[{"a": 1}],
        title="THIS IS A VERY LONG TABLE TITLE",
    )

    assert "THIS IS A VERY LONG TABLE TITLE" in result


# --- test_28_text_table_explicit_column_order_and_capitalized() ------------------------------
def test_28_text_table_explicit_column_order_and_capitalized():

    result = text_table(
        rows=[{"b": 2, "a": 1}],
        columns=["a", "b"],
    )

    assert "A" in result
    assert "B" in result


# --- test_29_text_table_missing_column_value() -------------------------------
def test_29_text_table_missing_column_value():

    result = text_table(
        rows=[
            {"a": 1},
            {"a": 2, "b": 3},
        ],
        columns=["a", "b"],
    )
    print(" ")
    print("*******************")
    print("test_29_text_table_missing_column_value")
    print("table output:")
    print(result)

    assert "3" in result


# --- test_30_text_table_wraps_many_columns() --------------------------------
def test_30_text_table_wraps_many_columns():

    result = text_table(
        rows=[
            {
                "a": "1",
                "b": "2",
                "c": "3",
                "d": "4",
                "e": "5",
                "f": "6",
            }
        ],
        wrap_table=True,
        wrap_table_width=20,
    )

    assert "1" in result
    assert "6" in result


# --- test_31_text_table_no_header() ------------------------------------------
def test_31_text_table_no_header():

    result = text_table(
        rows=[
            {"a": 1},
            {"a": 2},
        ],
        first_row_is_header=False,
    )

    assert "1" in result
    assert "2" in result



# --- test_32_text_table_mapping_with_integer_column_selector() --------------
def test_32_text_table_mapping_with_integer_column_selector():

    result = text_table(

        rows=[{"a": "one", "b": "two"}],

        columns=[1],

    )

    assert "two" in result
    assert "one" not in result


# --- test_33_text_table_header_labels_not_padded() ------------------------------
def test_33_text_table_header_labels_not_padded():

    with pytest.raises(ValueError):

        text_table(
            rows=[{"a": 1, "b": 2}],
            header_labels=["A"],
        )


# --- test_34_text_table_empty_header_cell_uses_fallback() -------------------
def test_34_text_table_empty_header_cell_uses_fallback():

    result = text_table(
        rows=[
            ["", ""],
            ["a", "b"],
        ],
        first_row_is_header=True,
    )
    print("")
    print("***********************")
    print("test_34_text_table_empty_header_cell_uses_fallback")
    print("table output:")
    print(result)

    assert "col1" in result
    assert "col2" in result


# --- test_35_text_table_long_title_warns() ----------------------------------
def test_35_text_table_long_title_warns():

    with pytest.warns(UserWarning):

        text_table(
            rows=[{"a": 1}],
            title="X" * 200,
            wrap_table_width=20,
        )


# --- test_36_text_table_long_subtitle_warns() -------------------------------
def test_36_text_table_long_subtitle_warns():

    with pytest.warns(UserWarning):

        text_table(
            rows=[{"a": 1}],
            subtitle="Y" * 200,
            wrap_table_width=20,
        )

# --- test_37_header_labels_and_header_row_conflict_raises() ------------------
def test_37_header_labels_and_header_row_conflict_raises():

    with pytest.raises(ValueError):
        text_table(
            rows=[
                ["name", "age"],
                ["alice", 30],
            ],
            first_row_is_header=True,
            header_labels=["Name", "Age"],
        )


# --- test_38_mapping_unknown_column_name_raises() ----------------------------
def test_38_mapping_unknown_column_name_raises():

    with pytest.raises(ValueError):
        text_table(
            rows=[{"a": 1}],
            columns=["missing"],
        )


# --- test_39_mapping_column_index_out_of_range_raises() ----------------------
def test_39_mapping_column_index_out_of_range_raises():

    with pytest.raises(ValueError):
        text_table(
            rows=[{"a": 1, "b": 2}],
            columns=[2],
        )


# --- test_40_mapping_first_row_used_as_header() ------------------------------
def test_40_mapping_first_row_used_as_header():

    result = text_table(
        rows=[
            {"a": "FIRST", "b": "SECOND"},
            {"a": 1, "b": 2},
        ],
        first_row_is_header=True,
    )

    assert "FIRST" in result
    assert "SECOND" in result
    assert "1" in result
    assert "2" in result


# --- test_41_sequence_columns_selected_by_position() -------------------------
def test_41_sequence_columns_selected_by_position():

    result = text_table(
        rows=[
            ["one", "two", "three"],
        ],
        columns=[2, 0],
    )

    assert "three" in result
    assert "one" in result
    assert "two" not in result


# --- test_42_sequence_string_column_selector_raises() ------------------------
def test_42_sequence_string_column_selector_raises():

    with pytest.raises(ValueError):
        text_table(
            rows=[
                ["one", "two"],
            ],
            columns=["first"],
        )


# --- test_43_sequence_column_index_out_of_range_raises() ---------------------
def test_43_sequence_column_index_out_of_range_raises():

    with pytest.raises(ValueError):
        text_table(
            rows=[
                ["one", "two"],
            ],
            columns=[2],
        )


# --- test_44_scalar_invalid_column_selector_raises() -------------------------
def test_44_scalar_invalid_column_selector_raises():

    with pytest.raises(ValueError):
        text_table(
            rows=["one", "two"],
            columns=[1],
        )


# --- test_45_scalar_first_row_used_as_header() -------------------------------
def test_45_scalar_first_row_used_as_header():

    result = text_table(
        rows=[
            "HEADER",
            "value",
        ],
        first_row_is_header=True,
    )

    assert "HEADER" in result
    assert "value" in result


# --- test_46_first_non_none_row_determines_layout() --------------------------
def test_46_first_non_none_row_determines_layout():

    result = text_table(
        rows=[
            None,
            {"a": 1},
            {"a": 2},
        ],
    )

    assert "A" in result
    assert "1" in result
    assert "2" in result


# --- test_47_sequence_explicit_header_labels() -------------------------------
def test_47_sequence_explicit_header_labels():

    result = text_table(
        rows=[
            ["alice", 30],
        ],
        header_labels=["Person", "Years"],
    )

    assert "Person" in result
    assert "Years" in result
    assert "alice" in result
    assert "30" in result
