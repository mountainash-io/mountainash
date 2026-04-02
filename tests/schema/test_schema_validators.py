"""
Tests for mountainash.schema.config.validators.

Covers:
- validate_schema_match / assert_schema_match

Note: validate_round_trip and validate_transformation_config tests were removed
because those functions depended on the deleted schema/transform/ backend strategy
system. The conform module replaces that functionality.
"""
from __future__ import annotations

import pytest
import polars as pl

from mountainash.schema.config.validators import (
    SchemaValidationError,
    assert_schema_match,
    validate_schema_match,
)
from mountainash.schema.config.universal_schema import TableSchema


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

