"""
Tests for mountainash.schema.config.schema_config.SchemaConfig and helpers.

Covers:
- SchemaConfig construction and default options
- from_dict / from_json deserialization (four formats)
- from_schemas auto-mapping
- to_dict / to_json serialization and roundtrips
- keep_only_mapped and strict option behaviour
- predict_output_schema
- separate_conversions (three-tier split)
- validate_against_dataframe
- Helper functions: init_column_config, create_rename_config,
  create_cast_config, apply_column_config

NOTE: validate_against_schemas is not covered because compare_schemas()
in universal_schema.py does not accept the 'check_constraints' keyword
that schema_config.py passes; this is a known production-code divergence.
"""
from __future__ import annotations

import json

import pytest
import polars as pl

from mountainash.schema.config.schema_config import (
    SchemaConfig,
    ValidationIssue,
    ValidationResult,
    apply_column_config,
    create_cast_config,
    create_rename_config,
    init_column_config,
)
from mountainash.schema.config.universal_schema import TableSchema


# ============================================================================
# TestSchemaConfigCreation
# ============================================================================

class TestSchemaConfigCreation:
    """Tests for constructing SchemaConfig instances."""

    def test_direct_construction_with_columns(self):
        config = SchemaConfig(columns={
            "user_id": {"rename": "id", "cast": "integer"},
            "full_name": {"rename": "name"},
        })
        assert "user_id" in config.columns
        assert "full_name" in config.columns
        assert config.columns["user_id"]["rename"] == "id"

    def test_default_options(self):
        config = SchemaConfig()
        assert config.columns == {}
        assert config.keep_only_mapped is False
        assert config.strict is False
        assert config.source_schema is None
        assert config.target_schema is None

    def test_with_options(self):
        config = SchemaConfig(
            columns={"x": {"rename": "y"}},
            keep_only_mapped=True,
            strict=True,
        )
        assert config.keep_only_mapped is True
        assert config.strict is True

    # ---- from_dict ----

    def test_from_dict_full_format(self):
        """Full format: has 'columns' key."""
        data = {
            "columns": {"old": {"rename": "new", "cast": "integer"}},
            "keep_only_mapped": True,
            "strict": True,
        }
        config = SchemaConfig.from_dict(data)
        assert config.columns == {"old": {"rename": "new", "cast": "integer"}}
        assert config.keep_only_mapped is True
        assert config.strict is True

    def test_from_dict_columns_only_format(self):
        """Columns-only format: values are dicts, no 'columns' wrapper."""
        data = {
            "old_id": {"rename": "id"},
            "amount": {"cast": "number"},
        }
        config = SchemaConfig.from_dict(data)
        assert config.columns == data
        assert config.keep_only_mapped is False

    def test_from_dict_simple_rename_format(self):
        """Simple rename format: values are strings."""
        data = {"old_name": "name", "old_email": "email"}
        config = SchemaConfig.from_dict(data)
        assert config.columns["old_name"] == {"rename": "name"}
        assert config.columns["old_email"] == {"rename": "email"}
        assert config.keep_only_mapped is True

    def test_from_dict_empty(self):
        config = SchemaConfig.from_dict({})
        assert config.columns == {}
        assert config.keep_only_mapped is False

    # ---- from_json ----

    def test_from_json_full_format(self):
        payload = json.dumps({
            "columns": {"a": {"rename": "b"}},
            "keep_only_mapped": True,
            "strict": False,
        })
        config = SchemaConfig.from_json(payload)
        assert config.columns == {"a": {"rename": "b"}}
        assert config.keep_only_mapped is True
        assert config.strict is False

    def test_from_json_simple_rename_format(self):
        payload = json.dumps({"first_name": "name", "last_name": "surname"})
        config = SchemaConfig.from_json(payload)
        assert config.columns["first_name"] == {"rename": "name"}
        assert config.columns["last_name"] == {"rename": "surname"}
        assert config.keep_only_mapped is True

    # ---- from_schemas ----

    def test_from_schemas_same_names_no_transforms(self, simple_table_schema):
        """When source and target fields have the same names, no transforms needed."""
        config = SchemaConfig.from_schemas(simple_table_schema, simple_table_schema)
        # No renames needed; result may be empty or contain only casts
        for spec in config.columns.values():
            assert "rename" not in spec, "No rename needed when names match"

    def test_from_schemas_rename_mapping(self):
        """Fuzzy-matched fields produce rename entries."""
        source = TableSchema.from_simple_dict({
            "user_name": "string",
        })
        target = TableSchema.from_simple_dict({
            "name": "string",
        })
        config = SchemaConfig.from_schemas(source, target)
        assert "user_name" in config.columns
        assert config.columns["user_name"].get("rename") == "name"

    def test_from_schemas_auto_cast(self):
        """auto_cast=True generates cast entries for type mismatches."""
        source = TableSchema.from_simple_dict({"amount": "string"})
        target = TableSchema.from_simple_dict({"amount": "number"})
        config = SchemaConfig.from_schemas(source, target, auto_cast=True)
        assert config.columns.get("amount", {}).get("cast") == "number"

    def test_from_schemas_no_auto_cast(self):
        """auto_cast=False skips cast entries even when types differ."""
        source = TableSchema.from_simple_dict({"amount": "string"})
        target = TableSchema.from_simple_dict({"amount": "number"})
        config = SchemaConfig.from_schemas(source, target, auto_cast=False)
        assert "cast" not in config.columns.get("amount", {})

    def test_from_schemas_sets_keep_only_mapped(self):
        """from_schemas sets keep_only_mapped based on keep_unmapped_source."""
        source = TableSchema.from_simple_dict({"id": "integer"})
        target = TableSchema.from_simple_dict({"id": "integer"})

        c_drop = SchemaConfig.from_schemas(source, target, keep_unmapped_source=False)
        assert c_drop.keep_only_mapped is True

        c_keep = SchemaConfig.from_schemas(source, target, keep_unmapped_source=True)
        assert c_keep.keep_only_mapped is False


# ============================================================================
# TestSchemaConfigSerialization
# ============================================================================

class TestSchemaConfigSerialization:
    """Tests for to_dict / to_json and roundtrip fidelity."""

    def test_to_dict_roundtrip(self):
        config = SchemaConfig(
            columns={"old": {"rename": "new", "cast": "integer"}},
            keep_only_mapped=True,
            strict=True,
        )
        d = config.to_dict()
        restored = SchemaConfig.from_dict(d)
        assert restored.columns == config.columns
        assert restored.keep_only_mapped == config.keep_only_mapped
        assert restored.strict == config.strict

    def test_to_json_roundtrip(self):
        config = SchemaConfig(
            columns={"score": {"cast": "number", "null_fill": 0.0}},
            keep_only_mapped=False,
            strict=False,
        )
        json_str = config.to_json()
        restored = SchemaConfig.from_json(json_str)
        assert restored.columns == config.columns
        assert restored.keep_only_mapped is False
        assert restored.strict is False

    def test_to_dict_contains_columns_key(self):
        config = SchemaConfig(columns={"a": {"rename": "b"}})
        d = config.to_dict()
        assert "columns" in d
        assert "keep_only_mapped" in d
        assert "strict" in d

    def test_to_dict_includes_source_schema_when_set(self, simple_table_schema):
        config = SchemaConfig(
            columns={},
            source_schema=simple_table_schema,
        )
        d = config.to_dict()
        assert "source_schema" in d

    def test_to_dict_includes_target_schema_when_set(self, simple_table_schema):
        config = SchemaConfig(
            columns={},
            target_schema=simple_table_schema,
        )
        d = config.to_dict()
        assert "target_schema" in d

    def test_to_dict_omits_schemas_when_not_set(self):
        config = SchemaConfig(columns={"x": {"cast": "string"}})
        d = config.to_dict()
        assert "source_schema" not in d
        assert "target_schema" not in d


# ============================================================================
# TestSchemaConfigOptions
# ============================================================================

class TestSchemaConfigOptions:
    """Tests for keep_only_mapped and strict option behaviour."""

    def test_keep_only_mapped_true_drops_extra_columns(self):
        df = pl.DataFrame({"old": ["a"], "extra": [1], "another": [2]})
        config = SchemaConfig(
            columns={"old": {"rename": "new"}},
            keep_only_mapped=True,
        )
        result = config.apply(df)
        assert result.columns == ["new"]

    def test_keep_only_mapped_false_keeps_all_columns(self):
        df = pl.DataFrame({"old": ["a"], "extra": [1]})
        config = SchemaConfig(
            columns={"old": {"rename": "new"}},
            keep_only_mapped=False,
        )
        result = config.apply(df)
        assert "new" in result.columns
        assert "extra" in result.columns

    def test_strict_true_raises_on_missing_column(self):
        df = pl.DataFrame({"id": [1, 2]})
        config = SchemaConfig(
            columns={"missing_col": {"rename": "x"}},
            strict=True,
        )
        with pytest.raises(Exception):
            config.apply(df)

    def test_strict_false_skips_missing_column(self):
        df = pl.DataFrame({"id": [1, 2], "name": ["a", "b"]})
        config = SchemaConfig(
            columns={"missing_col": {"rename": "x"}},
            strict=False,
        )
        # Should not raise; missing column simply not transformed
        result = config.apply(df)
        assert "id" in result.columns


# ============================================================================
# TestSchemaConfigPrediction
# ============================================================================

class TestSchemaConfigPrediction:
    """Tests for predict_output_schema."""

    def test_predict_with_rename(self):
        config = SchemaConfig(columns={"old_id": {"rename": "id"}})
        input_schema = TableSchema.from_simple_dict({"old_id": "integer", "name": "string"})
        output = config.predict_output_schema(input_schema)
        assert "id" in output.field_names
        assert "old_id" not in output.field_names

    def test_predict_with_cast(self):
        config = SchemaConfig(columns={"score": {"cast": "number"}})
        input_schema = TableSchema.from_simple_dict({"score": "string", "name": "string"})
        output = config.predict_output_schema(input_schema)
        score_field = output.get_field("score")
        assert score_field is not None
        assert score_field.type == "number"

    def test_predict_keeps_unmapped_when_not_filtering(self):
        config = SchemaConfig(
            columns={"old_id": {"rename": "id"}},
            keep_only_mapped=False,
        )
        input_schema = TableSchema.from_simple_dict({
            "old_id": "integer",
            "extra": "string",
        })
        output = config.predict_output_schema(input_schema)
        assert "id" in output.field_names
        assert "extra" in output.field_names

    def test_predict_drops_unmapped_when_filtering(self):
        config = SchemaConfig(
            columns={"old_id": {"rename": "id"}},
            keep_only_mapped=True,
        )
        input_schema = TableSchema.from_simple_dict({
            "old_id": "integer",
            "extra": "string",
        })
        output = config.predict_output_schema(input_schema)
        assert "id" in output.field_names
        assert "extra" not in output.field_names

    def test_predict_raises_without_schema(self):
        config = SchemaConfig(columns={"x": {"rename": "y"}})
        with pytest.raises(ValueError, match="No input schema"):
            config.predict_output_schema()

    def test_predict_uses_source_schema_when_no_arg(self, simple_table_schema):
        config = SchemaConfig(
            columns={},
            source_schema=simple_table_schema,
        )
        output = config.predict_output_schema()
        assert output.field_names == simple_table_schema.field_names

    def test_validate_against_dataframe_source_mode(self, simple_table_schema, polars_df):
        """validate_against_dataframe in source mode."""
        # polars_df has id, name, score, active, birth_date — not the same as simple_table_schema
        config = SchemaConfig(columns={}, source_schema=simple_table_schema)
        result = config.validate_against_dataframe(polars_df, mode="source")
        # simple_table_schema has id and name, polars_df has both => valid
        # polars_df has extra columns, but those are not errors in lenient mode
        assert isinstance(result, ValidationResult)
        assert result.valid is True

    def test_validate_against_dataframe_raises_without_schema(self, polars_df):
        config = SchemaConfig(columns={})
        with pytest.raises(ValueError, match="source_schema"):
            config.validate_against_dataframe(polars_df, mode="source")


# ============================================================================
# TestSchemaConfigSeparateConversions
# ============================================================================

class TestSchemaConfigSeparateConversions:
    """Tests for separate_conversions three-tier split."""

    def test_native_only_config(self):
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "name": {"cast": "string"},
        })
        py_custom, nw_custom, native = config.separate_conversions()
        assert "id" in native
        assert "name" in native
        assert not py_custom
        assert not nw_custom

    def test_vectorized_custom_goes_to_narwhals_custom(self):
        """safe_float has a Narwhals implementation → goes to narwhals_custom."""
        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"},
        })
        py_custom, nw_custom, native = config.separate_conversions()
        assert "amount" in nw_custom
        assert "amount" not in py_custom
        assert "amount" not in native

    def test_no_cast_goes_to_native(self):
        """Columns without cast (e.g. rename-only) go to native."""
        config = SchemaConfig(columns={
            "old_name": {"rename": "new_name"},
        })
        py_custom, nw_custom, native = config.separate_conversions()
        assert "old_name" in native
        assert "old_name" not in py_custom
        assert "old_name" not in nw_custom

    def test_python_only_custom(self, clean_custom_registry):
        """Custom type without narwhals converter goes to python_only."""
        registry = clean_custom_registry

        def my_converter(value, *, field_name=None):
            return str(value).upper() if value is not None else None

        registry.register(
            name="my_python_only",
            target_universal_type="string",
            python_converter=my_converter,
            description="Python-only test converter",
        )

        config = SchemaConfig(columns={
            "label": {"cast": "my_python_only"},
        })
        py_custom, nw_custom, native = config.separate_conversions()
        assert "label" in py_custom
        assert "label" not in nw_custom
        assert "label" not in native

    def test_mixed_config_splits_correctly(self):
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # native
            "amount": {"cast": "safe_float"},    # narwhals custom (vectorized)
            "name": {"rename": "full_name"},     # native (no cast)
        })
        py_custom, nw_custom, native = config.separate_conversions()
        assert set(native.keys()) == {"id", "name"}
        assert "amount" in nw_custom
        assert not py_custom


# ============================================================================
# TestSchemaConfigHelpers
# ============================================================================

class TestSchemaConfigHelpers:
    """Tests for module-level helper functions."""

    def test_init_column_config_from_schema_config(self):
        original = SchemaConfig(columns={"a": {"rename": "b"}})
        result = init_column_config(original)
        assert result is original

    def test_init_column_config_from_dict(self):
        result = init_column_config({"x": {"cast": "integer"}})
        assert isinstance(result, SchemaConfig)
        assert "x" in result.columns

    def test_init_column_config_from_json_string(self):
        payload = json.dumps({"columns": {"q": {"rename": "r"}}, "keep_only_mapped": False})
        result = init_column_config(payload)
        assert isinstance(result, SchemaConfig)
        assert "q" in result.columns

    def test_init_column_config_keep_only_mapped_override(self):
        original = SchemaConfig(columns={"a": {"rename": "b"}}, keep_only_mapped=False)
        result = init_column_config(original, keep_only_mapped=True)
        assert result.keep_only_mapped is True

    def test_init_column_config_invalid_raises(self):
        with pytest.raises((ValueError, TypeError)):
            init_column_config(12345)  # type: ignore

    def test_create_rename_config(self):
        config = create_rename_config({"old_id": "user_id", "old_email": "email"})
        assert config.columns["old_id"] == {"rename": "user_id"}
        assert config.columns["old_email"] == {"rename": "email"}
        assert config.keep_only_mapped is False

    def test_create_rename_config_keep_only_mapped(self):
        config = create_rename_config({"a": "b"}, keep_only_mapped=True)
        assert config.keep_only_mapped is True

    def test_create_cast_config(self):
        config = create_cast_config({"user_id": "integer", "score": "number"})
        assert config.columns["user_id"] == {"cast": "integer"}
        assert config.columns["score"] == {"cast": "number"}
        assert config.keep_only_mapped is False

    def test_create_cast_config_keep_only_mapped(self):
        config = create_cast_config({"x": "string"}, keep_only_mapped=True)
        assert config.keep_only_mapped is True

    def test_apply_column_config_with_polars_df(self):
        df = pl.DataFrame({
            "old_name": ["Alice", "Bob"],
            "age": [30, 25],
        })
        config = {"old_name": {"rename": "name"}}
        result = apply_column_config(df, config)
        assert "name" in result.columns
        assert "old_name" not in result.columns
        assert "age" in result.columns

    def test_apply_column_config_with_json_string(self):
        """from_json requires full format (with 'columns' key) for dict-valued specs."""
        df = pl.DataFrame({"user_id": [1, 2], "extra": ["a", "b"]})
        # Must use full format when column specs are dicts, not simple rename strings
        config_str = json.dumps({"columns": {"user_id": {"rename": "id"}}})
        result = apply_column_config(df, config_str)
        assert "id" in result.columns
        assert "user_id" not in result.columns

    def test_apply_column_config_with_schema_config_object(self):
        df = pl.DataFrame({"val": ["1", "2", "3"]})
        config = SchemaConfig(columns={"val": {"cast": "integer"}})
        result = apply_column_config(df, config)
        assert result["val"].dtype == pl.Int32 or result["val"].dtype in (pl.Int64, pl.Int32)
