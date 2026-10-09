"""
TypeSpec validation utilities for round-trip testing and schema comparison.

Provides functions for validating that DataFrames match expected TypeSpec schemas.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple
import logging
from mountainash.core.errors import MountainashError

if TYPE_CHECKING:
    from .spec import FieldSpec, TypeSpec
    from mountainash.core.types import SupportedDataFrames

logger = logging.getLogger(__name__)


class SchemaValidationError(MountainashError):
    """Raised when schema validation fails."""
    pass


def _index_fields(
    fields: List["FieldSpec"], prefix: str = ""
) -> dict[str, "FieldSpec"]:
    indexed = {}
    for field in fields:
        path = f"{prefix}.{field.name}" if prefix else field.name
        indexed[path] = field
        if field.object_fields is not None:
            indexed.update(_index_fields(field.object_fields, path))
        if field.item_object_fields is not None:
            indexed.update(_index_fields(field.item_object_fields, f"{path}[]"))
    return indexed


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
    from mountainash.core.dtypes import MountainashDtype
    from .extraction import extract_from_dataframe
    from .spec import compare_specs
    from .universal_types import UniversalType
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

    actual_fields = _index_fields(actual_schema.fields)
    expected_fields = _index_fields(expected_schema.fields)
    for col, (actual_type, expected_type) in diff.type_changes.items():
        actual_field = actual_fields.get(col)
        expected_field = expected_fields.get(col)
        if (
            actual_field is not None
            and expected_field is not None
            and actual_field.type is expected_field.type
            and actual_field.dtype is None
            and actual_field.type is UniversalType.STRING
            and expected_field.dtype in (
                MountainashDtype.LEXICAL_INTEGER,
                MountainashDtype.LEXICAL_DECIMAL,
            )
        ):
            continue
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
