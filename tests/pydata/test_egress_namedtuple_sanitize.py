"""Tests for namedtuple column name sanitization in EgressFromPolars."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.pydata.egress.egress_pydata_from_polars import EgressFromPolars


class TestNamedtupleSanitization:
    def test_python_keyword_column(self):
        df = pl.DataFrame({"class": ["a", "b"], "name": ["x", "y"]})
        result = EgressFromPolars._to_list_of_named_tuples(df)
        assert len(result) == 2
        assert result[0][0] == "a"
        assert result[0][1] == "x"

    def test_digit_leading_column(self):
        df = pl.DataFrame({"1_id": [10, 20], "name": ["a", "b"]})
        result = EgressFromPolars._to_list_of_named_tuples(df)
        assert len(result) == 2
        assert result[0][0] == 10

    def test_dotted_column_name(self):
        df = pl.DataFrame({"user.name": ["Alice", "Bob"], "age": [30, 25]})
        result = EgressFromPolars._to_list_of_named_tuples(df)
        assert len(result) == 2
        assert result[0][0] == "Alice"

    def test_special_chars_in_column(self):
        df = pl.DataFrame({"col-with-dashes": [1, 2], "col with spaces": [3, 4]})
        result = EgressFromPolars._to_list_of_named_tuples(df)
        assert len(result) == 2
        assert result[0][0] == 1
        assert result[0][1] == 3

    def test_duplicate_after_sanitization(self):
        df = pl.DataFrame({"a.b": [1], "a_b": [2]})
        result = EgressFromPolars._to_list_of_named_tuples(df)
        assert len(result) == 1
        assert result[0][0] == 1
        assert result[0][1] == 2

    def test_normal_columns_unchanged(self):
        df = pl.DataFrame({"name": ["Alice"], "age": [30]})
        result = EgressFromPolars._to_list_of_named_tuples(df)
        assert hasattr(result[0], "name")
        assert hasattr(result[0], "age")
        assert result[0].name == "Alice"
        assert result[0].age == 30

    def test_typed_named_tuples_with_keyword_column(self):
        df = pl.DataFrame({"class": ["a", "b"], "name": ["x", "y"]})
        result = EgressFromPolars._to_list_of_typed_named_tuples(df)
        assert len(result) == 2
        assert result[0][0] == "a"

    def test_indexed_named_tuples_with_keyword_column(self):
        df = pl.DataFrame({"class": ["a", "a", "b"], "val": [1, 2, 3]})
        result = EgressFromPolars._to_index_of_named_tuples(df, index_fields="val")
        assert len(result) == 3
