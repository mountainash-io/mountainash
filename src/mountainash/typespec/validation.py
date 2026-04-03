"""
TypeSpec validation utilities for round-trip testing and schema comparison.

Provides functions for validating that DataFrames match expected TypeSpec schemas.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple
import logging

if TYPE_CHECKING:
    from .spec import TypeSpec
    from mountainash.core.types import SupportedDataFrames

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass


def validate_match(
    df: 'SupportedDataFrames',
    expected_schema: 'TypeSpec',
    strict: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validate that DataFrame matches expected TypeSpec.

    Args:
        df: DataFrame to validate
        expected_schema: Expected TypeSpec
        strict: If True, extra columns are errors. If False, extra columns allowed.

    Returns:
        Tuple of (is_valid, list_of_error_messages)

    Example:
        >>> from mountainash.typespec import TypeSpec
        >>> expected = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        >>> df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        >>> is_valid, errors = validate_match(df, expected)
        >>> assert is_valid
    """
    from .extraction import extract_from_dataframe
    from .spec import compare_specs

    errors = []

    # Extract actual schema
    try:
        actual_schema = extract_from_dataframe(df)
    except Exception as e:
        errors.append(f"Failed to extract schema from DataFrame: {e}")
        return False, errors

    # Compare
    diff = compare_specs(actual_schema, expected_schema, check_constraints=False)

    if diff.missing_columns:
        errors.append(f"Missing required columns: {diff.missing_columns}")

    if diff.extra_columns and strict:
        errors.append(f"Unexpected columns: {diff.extra_columns}")

    if diff.type_mismatches:
        for col, actual_type, expected_type in diff.type_mismatches:
            errors.append(
                f"Type mismatch for '{col}': "
                f"expected {expected_type}, got {actual_type}"
            )

    is_valid = len(errors) == 0
    return is_valid, errors


# Alias for backward compatibility
validate_schema_match = validate_match


def assert_match(
    df: 'SupportedDataFrames',
    expected_schema: 'TypeSpec',
    strict: bool = True
) -> None:
    """
    Assert that DataFrame matches expected TypeSpec.

    Same as validate_match() but raises on failure.

    Args:
        df: DataFrame to validate
        expected_schema: Expected TypeSpec
        strict: If True, extra columns are errors

    Raises:
        SchemaValidationError: If validation fails
    """
    is_valid, errors = validate_match(df, expected_schema, strict)

    if not is_valid:
        error_msg = "Schema validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        raise SchemaValidationError(error_msg)


# Alias for backward compatibility
assert_schema_match = assert_match


__all__ = [
    # Primary validation functions
    "validate_match",
    "assert_match",
    # Legacy aliases
    "validate_schema_match",
    "assert_schema_match",
    # Errors
    "SchemaValidationError",
]
