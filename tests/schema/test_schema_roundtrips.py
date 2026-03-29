"""
Tests for schema extract → apply → validate roundtrips.

Covers:
- Extract schema from a Polars df, apply cast config to a string df, verify types match
- from_schemas auto-maps type differences, apply → verify output types
- predict_output_schema → apply → extract → field names match prediction
"""
from __future__ import annotations

import pytest
import polars as pl

from mountainash.schema.config.extractors import extract_schema_from_dataframe
from mountainash.schema.config.schema_config import SchemaConfig
from mountainash.schema.config.universal_schema import TableSchema


# ============================================================================
# TestExtractApplyRoundTrip
# ============================================================================

class TestExtractApplyRoundTrip:
    """extract_schema_from_dataframe → SchemaConfig.apply roundtrip."""

    def test_cast_from_string_matches_extracted_types(self):
        """Extract integer/number schema, apply casts to string df, verify types match."""
        source_df = pl.DataFrame({
            "id": [1, 2, 3],
            "score": [1.5, 2.5, 3.5],
        })
        # Create all-string version
        str_df = source_df.select([pl.col(c).cast(pl.Utf8) for c in source_df.columns])

        # Config that casts back to original types
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "score": {"cast": "number"},
        })
        result_df = config.apply(str_df)

        # Extract schema from result and compare to original
        original_schema = extract_schema_from_dataframe(source_df)
        result_schema = extract_schema_from_dataframe(result_df)

        for field_name in ["id", "score"]:
            original_field = original_schema.get_field(field_name)
            result_field = result_schema.get_field(field_name)
            assert original_field is not None
            assert result_field is not None
            assert original_field.type == result_field.type, (
                f"Type mismatch for '{field_name}': "
                f"original={original_field.type}, result={result_field.type}"
            )

    def test_passthrough_config_preserves_all_columns(self):
        """Empty config → all source columns appear in output."""
        df = pl.DataFrame({"a": [1], "b": ["x"], "c": [True]})
        config = SchemaConfig()
        result = config.apply(df)
        result_schema = extract_schema_from_dataframe(result)
        assert set(result_schema.field_names) == {"a", "b", "c"}

    def test_rename_config_field_names_updated(self):
        """Rename config → output has new field names."""
        df = pl.DataFrame({"old_id": [1, 2], "old_name": ["a", "b"]})
        config = SchemaConfig(columns={
            "old_id": {"rename": "id"},
            "old_name": {"rename": "name"},
        })
        result = config.apply(df)
        result_schema = extract_schema_from_dataframe(result)
        assert "id" in result_schema.field_names
        assert "name" in result_schema.field_names
        assert "old_id" not in result_schema.field_names


# ============================================================================
# TestFromSchemasApplyRoundTrip
# ============================================================================

class TestFromSchemasApplyRoundTrip:
    """SchemaConfig.from_schemas + apply roundtrip."""

    def test_auto_cast_changes_type(self):
        """from_schemas with type difference generates cast rule, apply changes type."""
        source = TableSchema.from_simple_dict({"value": "string"})
        target = TableSchema.from_simple_dict({"value": "integer"})

        config = SchemaConfig.from_schemas(source, target)

        df = pl.DataFrame({"value": ["1", "2", "3"]})
        result = config.apply(df)

        result_schema = extract_schema_from_dataframe(result)
        field = result_schema.get_field("value")
        assert field is not None
        assert field.type == "integer"

    def test_exact_match_schemas_produce_empty_config(self):
        """from_schemas with identical schemas → no transformations needed."""
        schema = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        config = SchemaConfig.from_schemas(schema, schema)
        # No columns need transformation
        assert config.columns == {}

    def test_fuzzy_match_maps_similar_names(self):
        """from_schemas fuzzy-matches user_id → id."""
        source = TableSchema.from_simple_dict({"user_id": "integer", "user_name": "string"})
        target = TableSchema.from_simple_dict({"user_id": "integer", "user_name": "string"})
        config = SchemaConfig.from_schemas(source, target)
        # Exact matches → no transforms needed
        assert config.columns == {}


# ============================================================================
# TestPredictValidateRoundTrip
# ============================================================================

class TestPredictValidateRoundTrip:
    """predict_output_schema → apply → extract field names match."""

    def test_predicted_names_match_actual_output(self):
        """After apply, extracted schema field names match prediction."""
        source_df = pl.DataFrame({
            "old_col": ["1", "2", "3"],
            "keep_col": [10, 20, 30],
        })
        config = SchemaConfig(columns={
            "old_col": {"rename": "new_col", "cast": "integer"},
        })

        source_schema = extract_schema_from_dataframe(source_df)
        predicted = config.predict_output_schema(source_schema)

        result_df = config.apply(source_df)
        result_schema = extract_schema_from_dataframe(result_df)

        assert set(predicted.field_names) == set(result_schema.field_names), (
            f"Predicted: {predicted.field_names}, Actual: {result_schema.field_names}"
        )

    def test_predict_with_keep_only_mapped(self):
        """keep_only_mapped=True → only mapped columns in prediction and output."""
        source_df = pl.DataFrame({
            "keep": [1, 2],
            "drop": ["a", "b"],
        })
        config = SchemaConfig(
            columns={"keep": {"cast": "integer"}},
            keep_only_mapped=True,
        )

        source_schema = extract_schema_from_dataframe(source_df)
        predicted = config.predict_output_schema(source_schema)

        result_df = config.apply(source_df)
        result_schema = extract_schema_from_dataframe(result_df)

        # Predicted should only include 'keep'
        assert "keep" in predicted.field_names
        assert "drop" not in predicted.field_names

        # Actual should also only include 'keep'
        assert set(result_schema.field_names) == set(predicted.field_names)

    def test_predict_output_type_matches_applied_type(self):
        """Type predicted for a cast column matches the actual extracted type."""
        source_df = pl.DataFrame({"val": ["1", "2", "3"]})
        config = SchemaConfig(columns={"val": {"cast": "integer"}})

        source_schema = extract_schema_from_dataframe(source_df)
        predicted = config.predict_output_schema(source_schema)

        result_df = config.apply(source_df)
        result_schema = extract_schema_from_dataframe(result_df)

        predicted_field = predicted.get_field("val")
        result_field = result_schema.get_field("val")

        assert predicted_field is not None
        assert result_field is not None
        # Both should be "integer"
        assert str(predicted_field.type) == "integer"
        assert result_field.type == "integer"
