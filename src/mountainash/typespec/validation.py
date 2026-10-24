"""
TableSchema validation utilities for round-trip testing and schema comparison.

Provides functions for validating that DataFrames match expected TableSchema schemas.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple
import logging
from mountainash.core.errors import MountainashError

if TYPE_CHECKING:
    from .spec import FieldDefinition, TableSchema
    from mountainash.core.types import SupportedDataFrames

logger = logging.getLogger(__name__)


class SchemaValidationError(MountainashError):
    """Raised when schema validation fails."""
    pass


def _matches_refinements(
    expected: "FieldDefinition", shape, path: tuple[str, ...] = (),
) -> bool:
    """Check precise nested targets without narrowing broad-only declarations."""
    from mountainash.core.dtypes import SchemaTypeStatus, registry
    from mountainash.core.dtypes.canonical import PARAMETERIZED_DTYPES
    from .converters import compare_resolved_type, resolve_field_type

    if expected.backend_type or getattr(expected.dtype, "native", None) is not None:
        if shape is None or shape.native_dtype is None:
            return False
        native = shape.native_dtype
        effective = resolve_field_type(expected, source=None, target=native.target, path=path)
        return registry.types_equal(native.value, effective.value, native.target)
    if isinstance(expected.dtype, PARAMETERIZED_DTYPES):
        # Nested members and elements resolve (with their own native overrides)
        # inside the parent's dtype, so one whole-type comparison covers them.
        if shape is None or shape.native_dtype is None:
            return False
        native = shape.native_dtype
        effective = resolve_field_type(expected, source=shape, target=native.target, path=path)
        return compare_resolved_type(effective, shape) is True
    if expected.dtype is not None and expected.dtype is not SchemaTypeStatus.UNKNOWN:
        if shape is None:
            return False
        actual = shape.decimal if shape.decimal is not None else shape.canonical_type
        return actual == expected.dtype
    return True


def validate_match(
    df: 'SupportedDataFrames',
    expected_schema: 'TableSchema',
    strict: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validate that DataFrame matches expected TableSchema.

    Args:
        df: DataFrame to validate
        expected_schema: Expected TableSchema
        strict: If True, extra columns are errors. If False, extra columns allowed.

    Returns:
        Tuple of (is_valid, list_of_error_messages)

    Example:
        >>> from mountainash.typespec import TableSchema
        >>> expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        >>> df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        >>> is_valid, errors = validate_match(df, expected)
        >>> assert is_valid
    """
    from .extraction import extract_from_dataframe
    from .spec import compare_specs
    from .source_shape import extract_source_shapes
    from .universal_types import UniversalType
    from mountainash.core.dtypes import SchemaTypeStatus

    errors = []

    # Extract actual schema
    try:
        actual_schema = extract_from_dataframe(df)
    except Exception as e:
        errors.append(f"Failed to extract schema from DataFrame: {e}")
        return False, errors

    # Compare
    diff = compare_specs(actual_schema, expected_schema, check_constraints=False)
    shapes = None
    for name, expected in expected_schema.fields.items():
        actual = actual_schema.get_field(name)
        if actual is None:
            continue
        if expected.type is UniversalType.ANY or actual.type is expected.type:
            diff.type_changes.pop(name, None)
        if expected.backend_type or expected.dtype is not None:
            if shapes is None:
                shapes = extract_source_shapes(df)
            if _matches_refinements(expected, shapes.get(name), (name,)):
                if (
                    expected.dtype is not SchemaTypeStatus.UNKNOWN
                    or expected.backend_type
                    or expected.type is UniversalType.ANY
                    or actual.type is expected.type
                ):
                    diff.type_changes.pop(name, None)
            else:
                diff.type_changes[name] = (actual, expected)

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
    expected_schema: 'TableSchema',
    strict: bool = True
) -> None:
    """
    Assert that DataFrame matches expected TableSchema.

    Same as validate_match() but raises on failure.

    Args:
        df: DataFrame to validate
        expected_schema: Expected TableSchema
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
