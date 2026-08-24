"""Tests for list parsing (delimiter, itemType) in conform pipeline.

Frictionless Table Schema §list: an ordered one-level depth collection of
primitive values serialised as a delimited string.  delimiter defaults to
","; itemType defaults to "string".
"""
from __future__ import annotations

import polars as pl
import polars.testing as plt
import pytest

import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestListParsingDefaultDelimiter:
    """Default comma delimiter with string items."""

    def test_comma_split_string_items(self):
        df = pl.DataFrame({"tags": ["a,b,c", "d,e"]})
        spec = TypeSpec(
            fields=[FieldSpec(name="tags", type=UniversalType.LIST)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["tags"].to_list() == [["a", "b", "c"], ["d", "e"]]

    def test_single_value_no_delimiter(self):
        df = pl.DataFrame({"tags": ["solo"]})
        spec = TypeSpec(
            fields=[FieldSpec(name="tags", type=UniversalType.LIST)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["tags"].to_list() == [["solo"]]

    def test_empty_string(self):
        df = pl.DataFrame({"tags": [""]})
        spec = TypeSpec(
            fields=[FieldSpec(name="tags", type=UniversalType.LIST)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["tags"].to_list() == [[""]]


class TestListParsingCustomDelimiter:
    """Custom delimiter."""

    def test_pipe_delimiter(self):
        df = pl.DataFrame({"tags": ["a|b|c", "d|e"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="tags", type=UniversalType.LIST, delimiter="|"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["tags"].to_list() == [["a", "b", "c"], ["d", "e"]]

    def test_semicolon_delimiter(self):
        df = pl.DataFrame({"tags": ["x;y;z"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="tags", type=UniversalType.LIST, delimiter=";"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["tags"].to_list() == [["x", "y", "z"]]

    def test_tab_delimiter(self):
        df = pl.DataFrame({"tags": ["a\tb\tc"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="tags", type=UniversalType.LIST, delimiter="\t"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["tags"].to_list() == [["a", "b", "c"]]


class TestListParsingItemType:
    """itemType casts each element after splitting."""

    def test_integer_item_type(self):
        df = pl.DataFrame({"ids": ["1,2,3", "4,5"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="ids", type=UniversalType.LIST, item_type="integer",
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["ids"].to_list() == [[1, 2, 3], [4, 5]]

    def test_number_item_type(self):
        df = pl.DataFrame({"vals": ["1.1,2.2,3.3"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="vals", type=UniversalType.LIST, item_type="number",
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        inner = result["vals"].to_list()[0]
        assert [pytest.approx(v) for v in inner] == [1.1, 2.2, 3.3]

    @pytest.mark.xfail(
        reason="Polars cannot cast Utf8 -> Boolean in list.eval context; "
               "Frictionless list spec only guarantees 'default formats'.",
        strict=True,
    )
    def test_boolean_item_type(self):
        df = pl.DataFrame({"flags": ["true,false,true"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="flags", type=UniversalType.LIST, item_type="boolean",
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["flags"].to_list() == [[True, False, True]]

    def test_string_item_type_is_noop(self):
        """Explicit itemType='string' should produce same result as default."""
        df = pl.DataFrame({"tags": ["a,b,c"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="tags", type=UniversalType.LIST, item_type="string",
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["tags"].to_list() == [["a", "b", "c"]]


class TestListParsingWithOtherStages:
    """List parsing integrates with other conform stages."""

    def test_list_with_rename(self):
        df = pl.DataFrame({"old_tags": ["a,b,c"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="tags",
                    type=UniversalType.LIST,
                    rename_from="old_tags",
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result.columns == ["tags"]
        assert result["tags"].to_list() == [["a", "b", "c"]]

    def test_list_with_null_fill(self):
        """null_fill applies before list split — fills null with a default string."""
        df = pl.DataFrame({"tags": [None, "a,b"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="tags",
                    type=UniversalType.LIST,
                    null_fill="default",
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["tags"].to_list() == [["default"], ["a", "b"]]

    def test_list_with_custom_delimiter_and_integer_items(self):
        """Combined delimiter + itemType."""
        df = pl.DataFrame({"ids": ["1|2|3"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="ids",
                    type=UniversalType.LIST,
                    delimiter="|",
                    item_type="integer",
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["ids"].to_list() == [[1, 2, 3]]
