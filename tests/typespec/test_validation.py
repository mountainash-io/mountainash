"""
Tests for mountainash.typespec.validation.

Covers:
- validate_match / assert_match
- validate_schema_match / assert_schema_match (aliases)
"""
from __future__ import annotations

import pytest
import polars as pl

from mountainash.typespec.validation import (
    SchemaValidationError,
    assert_match,
    assert_schema_match,
    validate_match,
    validate_schema_match,
)
from mountainash.typespec.spec import TypeSpec


from mountainash.core.dtypes import DecimalDtype
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType


@pytest.mark.parametrize(
    "physical_dtype",
    [
        pl.Decimal(precision=20, scale=2),
        pl.Decimal(precision=21, scale=3),
        pl.Float64,
    ],
)
def test_validate_match_rejects_decimal_parameter_or_carrier_mismatch(
    physical_dtype,
) -> None:
    expected = TypeSpec(fields=[FieldSpec(
        name="amount",
        type=UniversalType.NUMBER,
        dtype=DecimalDtype(precision=20, scale=3),
    )])
    frame = pl.DataFrame(schema={"amount": physical_dtype})

    is_valid, errors = validate_match(frame, expected)

    assert is_valid is False
    assert any("amount" in error for error in errors)


# ============================================================================
# TestValidateMatch
# ============================================================================

class TestValidateMatch:
    """validate_match() tests."""

    def test_matching_schema_passes(self):
        expected = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        is_valid, errors = validate_match(df, expected)
        assert is_valid is True
        assert errors == []

    def test_missing_column_fails(self):
        expected = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        df = pl.DataFrame({"id": [1, 2]})  # missing 'name'
        is_valid, errors = validate_match(df, expected)
        assert is_valid is False
        assert len(errors) > 0
        assert any("name" in e for e in errors)

    def test_strict_true_extra_columns_fails(self):
        expected = TypeSpec.from_simple_dict({"id": "integer"})
        df = pl.DataFrame({"id": [1, 2], "extra": ["x", "y"]})
        is_valid, errors = validate_match(df, expected, strict=True)
        assert is_valid is False

    def test_strict_false_extra_columns_passes(self):
        expected = TypeSpec.from_simple_dict({"id": "integer"})
        df = pl.DataFrame({"id": [1, 2], "extra": ["x", "y"]})
        is_valid, errors = validate_match(df, expected, strict=False)
        assert is_valid is True
        assert errors == []


# ============================================================================
# TestAssertMatch
# ============================================================================

class TestAssertMatch:
    """assert_match() tests."""

    def test_passes_when_valid(self):
        expected = TypeSpec.from_simple_dict({"id": "integer"})
        df = pl.DataFrame({"id": [1, 2]})
        assert_match(df, expected)  # no raise

    def test_raises_schema_validation_error_when_invalid(self):
        expected = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        df = pl.DataFrame({"id": [1, 2]})  # missing 'name'
        with pytest.raises(SchemaValidationError):
            assert_match(df, expected)


# ============================================================================
# TestAliases
# ============================================================================

class TestAliases:
    """Backward-compat aliases validate_schema_match / assert_schema_match."""

    def test_validate_schema_match_alias(self):
        expected = TypeSpec.from_simple_dict({"id": "integer"})
        df = pl.DataFrame({"id": [1, 2]})
        is_valid, errors = validate_schema_match(df, expected)
        assert is_valid is True

    def test_assert_schema_match_alias(self):
        expected = TypeSpec.from_simple_dict({"id": "integer"})
        df = pl.DataFrame({"id": [1, 2]})
        assert_schema_match(df, expected)  # no raise
