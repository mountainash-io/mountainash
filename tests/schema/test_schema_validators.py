"""
Tests for mountainash.schema.config.validators.

Covers:
- validate_round_trip / assert_round_trip
- validate_schema_match / assert_schema_match
- validate_transformation_config
"""
from __future__ import annotations

import pytest
import polars as pl

from mountainash.schema.config.validators import (
    SchemaValidationError,
    assert_round_trip,
    assert_schema_match,
    validate_round_trip,
    validate_schema_match,
    validate_transformation_config,
)
from mountainash.schema.config.schema_config import SchemaConfig
from mountainash.schema.config.universal_schema import TableSchema


# ============================================================================
# Helpers
# ============================================================================

def _polars_source():
    return pl.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})


def _string_source():
    """Source df where all columns are strings."""
    return pl.DataFrame({"id": ["1", "2", "3"], "name": ["a", "b", "c"]})


# ============================================================================
# TestValidateRoundTrip
# ============================================================================

class TestValidateRoundTrip:
    """validate_round_trip() tests."""

    def test_matching_output_passes(self):
        """Applying a cast config and round-tripping should pass."""
        source = pl.DataFrame({"val": ["1", "2", "3"]})
        config = SchemaConfig(columns={"val": {"cast": "integer"}})
        target = config.apply(source)
        is_valid, errors = validate_round_trip(target, source, config)
        assert is_valid is True
        assert errors == []

    def test_missing_column_fails(self):
        """Target DF missing an expected column should report errors."""
        source = pl.DataFrame({"id": [1, 2], "name": ["a", "b"]})
        config = SchemaConfig(columns={"id": {"cast": "integer"}})
        # Build a target that is missing 'name'
        bad_target = pl.DataFrame({"id": [1, 2]})
        is_valid, errors = validate_round_trip(bad_target, source, config)
        assert is_valid is False
        assert len(errors) > 0

    def test_passthrough_config_with_no_transform(self):
        """Empty config → target matches source → should pass."""
        source = pl.DataFrame({"x": [1, 2], "y": ["a", "b"]})
        config = SchemaConfig()
        target = config.apply(source)
        is_valid, errors = validate_round_trip(target, source, config)
        assert is_valid is True

    def test_rename_produces_matching_output(self):
        """Rename config predicts renamed output correctly."""
        source = pl.DataFrame({"old": [10, 20]})
        config = SchemaConfig(columns={"old": {"rename": "new"}})
        target = config.apply(source)
        is_valid, errors = validate_round_trip(target, source, config)
        assert is_valid is True, errors


# ============================================================================
# TestAssertRoundTrip
# ============================================================================

class TestAssertRoundTrip:
    """assert_round_trip() tests."""

    def test_passes_when_valid(self):
        """assert_round_trip should not raise when output matches prediction."""
        source = pl.DataFrame({"val": ["1", "2"]})
        config = SchemaConfig(columns={"val": {"cast": "integer"}})
        target = config.apply(source)
        assert_round_trip(target, source, config)  # no raise

    def test_raises_schema_validation_error_when_invalid(self):
        """assert_round_trip should raise SchemaValidationError on mismatch."""
        source = pl.DataFrame({"id": [1], "name": ["a"]})
        config = SchemaConfig(columns={"id": {"cast": "integer"}})
        bad_target = pl.DataFrame({"id": [1]})  # missing 'name'
        with pytest.raises(SchemaValidationError):
            assert_round_trip(bad_target, source, config)


# ============================================================================
# TestValidateSchemaMatch
# ============================================================================

class TestValidateSchemaMatch:
    """validate_schema_match() tests."""

    def test_matching_schema_passes(self):
        expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        is_valid, errors = validate_schema_match(df, expected)
        assert is_valid is True
        assert errors == []

    def test_missing_column_fails(self):
        expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        df = pl.DataFrame({"id": [1, 2]})  # missing 'name'
        is_valid, errors = validate_schema_match(df, expected)
        assert is_valid is False
        assert len(errors) > 0
        assert any("name" in e for e in errors)

    def test_strict_true_extra_columns_fails(self):
        expected = TableSchema.from_simple_dict({"id": "integer"})
        df = pl.DataFrame({"id": [1, 2], "extra": ["x", "y"]})
        is_valid, errors = validate_schema_match(df, expected, strict=True)
        assert is_valid is False

    def test_strict_false_extra_columns_passes(self):
        expected = TableSchema.from_simple_dict({"id": "integer"})
        df = pl.DataFrame({"id": [1, 2], "extra": ["x", "y"]})
        is_valid, errors = validate_schema_match(df, expected, strict=False)
        assert is_valid is True
        assert errors == []


# ============================================================================
# TestAssertSchemaMatch
# ============================================================================

class TestAssertSchemaMatch:
    """assert_schema_match() tests."""

    def test_passes_when_valid(self):
        expected = TableSchema.from_simple_dict({"id": "integer"})
        df = pl.DataFrame({"id": [1, 2]})
        assert_schema_match(df, expected)  # no raise

    def test_raises_schema_validation_error_when_invalid(self):
        expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        df = pl.DataFrame({"id": [1, 2]})  # missing 'name'
        with pytest.raises(SchemaValidationError):
            assert_schema_match(df, expected)


# ============================================================================
# TestValidateTransformationConfig
# ============================================================================

class TestValidateTransformationConfig:
    """validate_transformation_config() tests."""

    def test_valid_config_with_matching_source_schema(self):
        source_schema = TableSchema.from_simple_dict({"old_id": "string", "name": "string"})
        config = SchemaConfig(
            columns={"old_id": {"rename": "id", "cast": "integer"}},
            source_schema=source_schema,
        )
        is_valid, errors = validate_transformation_config(config)
        assert is_valid is True
        assert errors == []

    def test_config_referencing_nonexistent_source_column_fails(self):
        source_schema = TableSchema.from_simple_dict({"real_col": "string"})
        config = SchemaConfig(
            columns={"nonexistent": {"cast": "integer"}},
            source_schema=source_schema,
        )
        is_valid, errors = validate_transformation_config(config, source_schema=source_schema)
        assert is_valid is False
        assert len(errors) > 0
        assert any("nonexistent" in e for e in errors)

    def test_empty_config_is_valid(self):
        source_schema = TableSchema.from_simple_dict({"id": "integer"})
        config = SchemaConfig(columns={}, source_schema=source_schema)
        is_valid, errors = validate_transformation_config(config)
        assert is_valid is True

    def test_source_schema_passed_as_argument(self):
        """source_schema passed as argument overrides config.source_schema."""
        config = SchemaConfig(columns={"missing_col": {"cast": "integer"}})
        source_schema = TableSchema.from_simple_dict({"id": "integer"})
        is_valid, errors = validate_transformation_config(config, source_schema=source_schema)
        assert is_valid is False
        assert any("missing_col" in e for e in errors)
