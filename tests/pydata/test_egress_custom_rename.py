"""Tests for custom-cast field rename handling in egress helpers."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.pydata.egress.egress_helpers import apply_native_conversions_for_egress
from mountainash.typespec.custom_types import CustomTypeRegistry
from mountainash.typespec.spec import FieldDefinition, TableSchema
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
        """A custom-cast field (python-only) whose source differs from its name should be renamed."""
        df = pl.DataFrame({"raw_val": ["hello", "world"]})
        schema = TableSchema(
            fields={
                "val": FieldDefinition(
                    type=UniversalType.STRING,
                    rename_from="raw_val",
                    custom_cast="_test_upper",
                ),
            },
        )
        result_df, python_only = apply_native_conversions_for_egress(df, schema)
        assert "val" in result_df.columns, (
            f"Custom field should be renamed from 'raw_val' to 'val'. "
            f"Got columns: {result_df.columns}"
        )
        # The deferred python-only conversions are keyed by the target name.
        assert set(python_only) == {"val"}

    def test_custom_field_without_rename_unchanged(self):
        """A custom-cast field whose source is its own name needs no rename."""
        df = pl.DataFrame({"val": ["hello", "world"]})
        schema = TableSchema(
            fields={
                "val": FieldDefinition(
                    type=UniversalType.STRING,
                    custom_cast="_test_upper",
                ),
            },
        )
        result_df, python_only = apply_native_conversions_for_egress(df, schema)
        assert "val" in result_df.columns

    def test_mixed_native_and_custom_with_renames(self):
        """Native fields go through conform; custom fields get rename-only projections."""
        df = pl.DataFrame({
            "raw_id": ["1", "2"],
            "raw_label": ["hello", "world"],
        })
        schema = TableSchema(
            fields={
                "id": FieldDefinition(type=UniversalType.INTEGER, rename_from="raw_id"),
                "label": FieldDefinition(
                    type=UniversalType.STRING,
                    rename_from="raw_label",
                    custom_cast="_test_upper",
                ),
            },
        )
        result_df, python_only = apply_native_conversions_for_egress(df, schema)
        assert "id" in result_df.columns
        assert "label" in result_df.columns
        assert result_df["id"].to_list() == [1, 2]

    def test_rename_projection_does_not_mutate_declarations(self):
        """The rename-only projection is a copy; the caller's custom_cast survives."""
        df = pl.DataFrame({"raw_val": ["hello"]})
        label = FieldDefinition(
            type=UniversalType.STRING, rename_from="raw_val", custom_cast="_test_upper",
        )
        schema = TableSchema(fields={"val": label})
        _, python_only = apply_native_conversions_for_egress(df, schema)
        assert schema.fields["val"] is label
        assert label.custom_cast == "_test_upper"
        assert python_only["val"].custom_cast == "_test_upper"

    @pytest.mark.parametrize("rename", [False, True])
    def test_custom_conversion_receives_uncast_source_with_native_fanout(self, rename):
        from mountainash.pydata.egress.egress_helpers import apply_hybrid_egress_conversion

        target = "label" if rename else "raw"
        definition = FieldDefinition(
            type=UniversalType.INTEGER, custom_cast="_test_upper",
            rename_from="raw" if rename else None,
        )
        schema = TableSchema(fields={
            target: definition,
            "id": FieldDefinition(type=UniversalType.INTEGER, rename_from="raw"),
        }, fields_match="open")
        result = apply_hybrid_egress_conversion(
            pl.DataFrame({"keep": ["K"], "raw": ["001"]}),
            schema, extract_func=lambda frame: frame.to_dicts(),
        )
        assert result == [{"keep": "K", target: "001", "id": 1}]
        assert list(result[0]) == ["keep", target, "id"]
        assert definition.custom_cast == "_test_upper"
        assert definition.type is UniversalType.INTEGER
