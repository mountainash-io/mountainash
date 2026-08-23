"""End-to-end test exercising all stages of the conform pipeline."""
from __future__ import annotations

import pytest
from datetime import date

import polars as pl
import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestFullPipeline:
    """End-to-end tests that exercise multiple conform pipeline stages in a
    single call, verifying they compose correctly in sequence."""

    def test_all_stages_combined(self):
        """Exercise: source resolve -> missingValues -> numeric parsing -> cast -> alias."""
        df = pl.DataFrame({
            "raw_price": ["1.234,56", "NA", "999,00"],
            "raw_active": ["yes", "no", "NA"],
            "raw_date": ["26/01/2024", "NA", "15/06/2023"],
            "extra_col": [1, 2, 3],
        })
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="price",
                    type=UniversalType.NUMBER,
                    rename_from="raw_price",
                    group_char=".",
                    decimal_char=",",
                ),
                FieldSpec(
                    name="active",
                    type=UniversalType.BOOLEAN,
                    rename_from="raw_active",
                    true_values=["yes"],
                    false_values=["no"],
                ),
                FieldSpec(
                    name="event_date",
                    type=UniversalType.DATE,
                    rename_from="raw_date",
                    format="%d/%m/%Y",
                ),
            ],
            missing_values=["NA"],
        )
        result = ma.relation(df).conform(spec).to_polars()

        # Price: "1.234,56" -> remove "." -> replace "," with "." -> "1234.56" -> cast float
        #        "NA" -> null (missingValues) -> null after cast
        #        "999,00" -> replace "," with "." -> "999.00" -> cast float
        assert result["price"].to_list() == [1234.56, None, 999.0]

        # Active: "yes" -> True, "no" -> False, "NA" -> null (missingValues first)
        assert result["active"].to_list() == [True, False, None]

        # Event date: "26/01/2024" -> date(2024,1,26), "NA" -> null, "15/06/2023" -> date(2023,6,15)
        assert result["event_date"].to_list() == [date(2024, 1, 26), None, date(2023, 6, 15)]

        # Column names: this spec sets fields_match="open", so mapped spec
        # fields plus any unmapped source columns are kept.
        assert "price" in result.columns
        assert "active" in result.columns
        assert "event_date" in result.columns

    def test_bare_number_with_missing_values(self):
        """Exercise: bareNumber strip + groupChar + decimalChar + missingValues."""
        df = pl.DataFrame({
            "amount": ["$1,234.56", "N/A", "€789.00"],
        })
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="amount",
                    type=UniversalType.NUMBER,
                    bare_number=False,
                    group_char=",",
                ),
            ],
            missing_values=["N/A"],
        )
        result = ma.relation(df).conform(spec).to_polars()

        # "$1,234.56" -> strip "$" (bareNumber) -> remove "," (groupChar) -> "1234.56" -> cast
        # "N/A" -> null
        # "€789.00" -> strip "€" (bareNumber) -> "789.00" -> cast
        assert result["amount"].to_list() == [1234.56, None, 789.0]

    def test_null_fill_on_typed_source(self):
        """Null fill works when source data is already the target type."""
        df = pl.DataFrame({
            "score": [1.5, None, 3.5],
        })
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="score",
                    type=UniversalType.NUMBER,
                    null_fill=0.0,
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["score"].to_list() == [1.5, 0.0, 3.5]

    def test_boolean_with_custom_values_and_missing(self):
        """Boolean casting with custom trueValues/falseValues plus missingValues."""
        df = pl.DataFrame({
            "flag": ["Y", "N", "UNKNOWN", "Y"],
        })
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="flag",
                    type=UniversalType.BOOLEAN,
                    true_values=["Y"],
                    false_values=["N"],
                ),
            ],
            missing_values=["UNKNOWN"],
        )
        result = ma.relation(df).conform(spec).to_polars()
        # "UNKNOWN" -> null via missingValues, then boolean cast sees null -> null
        assert result["flag"].to_list() == [True, False, None, True]

    def test_temporal_format_with_missing(self):
        """Temporal format parsing with missingValues."""
        df = pl.DataFrame({
            "dt": ["2024-01-15 10:30:00", "-", "2023-06-20 14:00:00"],
        })
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="dt",
                    type=UniversalType.DATETIME,
                    format="%Y-%m-%d %H:%M:%S",
                ),
            ],
            missing_values=["-"],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"][0] is not None
        assert result["dt"][1] is None
        assert result["dt"][2] is not None

    def test_pipeline_with_fields_match_open(self):
        """Open mode preserves unmapped columns."""
        df = pl.DataFrame({
            "name": ["Alice", "", "Charlie"],
            "age": [30, 25, 35],
        })
        spec = TypeSpec(
            fields=[
                FieldSpec(name="name", type=UniversalType.STRING),
            ],
            fields_match="open",
            missing_values=[""],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["name"].to_list() == ["Alice", None, "Charlie"]
        assert "age" in result.columns  # open mode keeps unmapped

    def test_pipeline_rename_and_alias(self):
        """Verify rename_from -> alias produces correct column names."""
        df = pl.DataFrame({
            "old_a": ["x", "y"],
            "old_b": [1, 2],
        })
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="new_a", type=UniversalType.STRING, rename_from="old_a"),
                FieldSpec(name="new_b", type=UniversalType.INTEGER, rename_from="old_b"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert set(result.columns) == {"new_a", "new_b"}
        assert result["new_a"].to_list() == ["x", "y"]
        assert result["new_b"].to_list() == [1, 2]

    def test_field_level_missing_overrides_schema(self):
        """Field-level missing_values replaces schema-level entirely."""
        df = pl.DataFrame({
            "a": ["NA", "ok"],
            "b": ["BLANK", "ok"],
        })
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="a", type=UniversalType.STRING),
                FieldSpec(
                    name="b",
                    type=UniversalType.STRING,
                    missing_values=["BLANK"],
                ),
            ],
            missing_values=["NA"],
        )
        result = ma.relation(df).conform(spec).to_polars()
        # "a" uses schema-level: "NA" -> null
        assert result["a"].to_list() == [None, "ok"]
        # "b" uses field-level ["BLANK"], NOT schema-level ["NA"]
        assert result["b"].to_list() == [None, "ok"]
