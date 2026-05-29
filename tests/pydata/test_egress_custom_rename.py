"""Tests for custom-cast field rename handling in egress helpers."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.pydata.egress.egress_helpers import apply_native_conversions_for_egress
from mountainash.typespec.custom_types import CustomTypeRegistry
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


@pytest.fixture(autouse=True)
def register_test_converter():
    """Register a simple non-vectorized (Python-only) converter for tests."""
    name = "_test_upper"
    if not CustomTypeRegistry.has_converter(name):
        CustomTypeRegistry.register(
            name=name,
            target_universal_type="string",
            python_converter=lambda v, **_: str(v).upper() if v is not None else v,
            narwhals_converter=None,
            description="Test converter: upper-case string",
        )
    yield
    CustomTypeRegistry.unregister(name)


class TestCustomCastRename:
    def test_custom_field_with_rename_gets_renamed(self):
        """A custom-cast field (python-only) with source_name != name should be renamed."""
        df = pl.DataFrame({"raw_val": ["hello", "world"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="val",
                    type=UniversalType.STRING,
                    rename_from="raw_val",
                    custom_cast="_test_upper",
                ),
            ],
        )
        result_df, python_only = apply_native_conversions_for_egress(df, spec)
        assert "val" in result_df.columns, (
            f"Custom field should be renamed from 'raw_val' to 'val'. "
            f"Got columns: {result_df.columns}"
        )

    def test_custom_field_without_rename_unchanged(self):
        """A custom-cast field where name == source_name needs no rename."""
        df = pl.DataFrame({"val": ["hello", "world"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="val",
                    type=UniversalType.STRING,
                    custom_cast="_test_upper",
                ),
            ],
        )
        result_df, python_only = apply_native_conversions_for_egress(df, spec)
        assert "val" in result_df.columns

    def test_mixed_native_and_custom_with_renames(self):
        """Native fields go through conform; custom fields get rename-only projections."""
        df = pl.DataFrame({
            "raw_id": ["1", "2"],
            "raw_label": ["hello", "world"],
        })
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER, rename_from="raw_id"),
                FieldSpec(
                    name="label",
                    type=UniversalType.STRING,
                    rename_from="raw_label",
                    custom_cast="_test_upper",
                ),
            ],
        )
        result_df, python_only = apply_native_conversions_for_egress(df, spec)
        assert "id" in result_df.columns
        assert "label" in result_df.columns
        assert result_df["id"].to_list() == [1, 2]
