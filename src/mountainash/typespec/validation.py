"""
TypeSpec validation utilities for round-trip testing and schema comparison.

Provides functions for validating that DataFrames match expected TypeSpec schemas.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple
import logging
from mountainash.core.errors import MountainashError

if TYPE_CHECKING:
    from .spec import TypeSpec
    from mountainash.core.types import SupportedDataFrames

logger = logging.getLogger(__name__)


class SchemaValidationError(MountainashError):
    """Raised when schema validation fails."""
    pass


def _matches_refinements(expected, shape) -> bool:
    """Check precise nested targets without narrowing broad-only declarations."""
    from mountainash.core.dtypes import SchemaTypeStatus, registry
    from mountainash.core.dtypes.canonical import PARAMETERIZED_DTYPES
    from .converters import _resolve_field_target, _native_types_equal, effective_child_fields

    if expected.backend_type or getattr(expected.dtype, "native", None) is not None:
        if shape is None or shape.native_dtype is None:
            return False
        native = shape.native_dtype
        effective = _resolve_field_target(expected, native.target)
        return _native_types_equal(native.value, effective.value, native.target)
    if isinstance(expected.dtype, PARAMETERIZED_DTYPES):
        if shape is None or shape.native_dtype is None:
            return False
        native = shape.native_dtype
        effective = _resolve_field_target(
            expected, native.target, source=shape.detailed_dtype,
        )
        return _native_types_equal(
            native.value, registry.to_native_schema(effective, native.target), native.target,
        )
    broad_valid = True
    if expected.dtype is not None and expected.dtype is not SchemaTypeStatus.UNKNOWN:
        if shape is None:
            broad_valid = False
        else:
            actual = shape.decimal if shape.decimal is not None else shape.canonical_type
            broad_valid = actual == expected.dtype
    children = effective_child_fields(expected)
    source = shape.item_shape if shape is not None and expected.item_object_fields else shape
    actual_children = dict(source.struct_fields) if source is not None else {}
    refinements_valid = all(
        _matches_refinements(child, actual_children.get(child.name))
        for child in children
    )
    return broad_valid and refinements_valid

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
    for expected in expected_schema.fields:
        actual = actual_schema.get_field(expected.name)
        if actual is None:
            continue
        if expected.type is UniversalType.ANY or actual.type is expected.type:
            diff.type_changes.pop(expected.name, None)
        if (
            expected.backend_type or expected.dtype is not None
            or expected.object_fields or expected.item_object_fields
        ):
            if shapes is None:
                shapes = extract_source_shapes(df)
            if _matches_refinements(expected, shapes.get(expected.name)):
                if (
                    expected.dtype is not SchemaTypeStatus.UNKNOWN
                    or expected.backend_type
                    or expected.type is UniversalType.ANY
                    or actual.type is expected.type
                ):
                    diff.type_changes.pop(expected.name, None)
            else:
                diff.type_changes[expected.name] = (actual, expected)

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
