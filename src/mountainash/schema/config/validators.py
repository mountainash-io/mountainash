"""
Schema validation utilities for round-trip testing and schema comparison.

Provides functions for validating that schema transformations work correctly
and can be reversed without data loss.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple, Optional
import logging

if TYPE_CHECKING:
    from .schema_config import SchemaConfig
    from .universal_schema import TableSchema, SchemaDiff
    from mountainash.core.types import SupportedDataFrames

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass


def validate_round_trip(
    target_df: 'SupportedDataFrames',
    source_df: 'SupportedDataFrames',
    config: 'SchemaConfig',
    tolerance: float = 1e-10
) -> Tuple[bool, List[str]]:
    """
    Validate that transformation produces expected output schema.

    Compares the actual output DataFrame schema with the predicted schema
    from the SchemaConfig. Does NOT reverse-transform (that's often lossy).

    Args:
        target_df: Transformed DataFrame (output of transformation)
        source_df: Original DataFrame (input to transformation)
        config: SchemaConfig used for transformation
        tolerance: Tolerance for floating point comparisons (not currently used)

    Returns:
        Tuple of (is_valid, list_of_error_messages)

    Example:
        >>> config = SchemaConfig(columns={"old": {"rename": "new", "cast": "integer"}})
        >>> source = pl.DataFrame({"old": ["1", "2", "3"]})
        >>> target = transform(source, config)
        >>> is_valid, errors = validate_round_trip(target, source, config)
        >>> assert is_valid
    """
    from .extractors import from_dataframe
    from .universal_schema import compare_schemas

    errors = []

    # Extract actual schemas
    try:
        source_schema = from_dataframe(source_df)
        target_schema = from_dataframe(target_df)
    except Exception as e:
        errors.append(f"Failed to extract schemas: {e}")
        return False, errors

    # Predict what the output schema should be
    try:
        predicted_schema = config.predict_output_schema(source_schema)
    except Exception as e:
        errors.append(f"Failed to predict output schema: {e}")
        return False, errors

    # Compare predicted vs actual
    diff = compare_schemas(target_schema, predicted_schema, check_constraints=False)

    if diff.missing_columns:
        errors.append(f"Missing expected columns: {diff.missing_columns}")

    if diff.extra_columns:
        # Extra columns might be ok if keep_only_mapped=False
        if config.keep_only_mapped:
            errors.append(f"Unexpected extra columns: {diff.extra_columns}")
        else:
            logger.debug(f"Extra columns present (allowed): {diff.extra_columns}")

    if diff.type_mismatches:
        for col, actual_type, expected_type in diff.type_mismatches:
            errors.append(
                f"Type mismatch for '{col}': "
                f"expected {expected_type}, got {actual_type}"
            )

    is_valid = len(errors) == 0
    return is_valid, errors


def assert_round_trip(
    target_df: 'SupportedDataFrames',
    source_df: 'SupportedDataFrames',
    config: 'SchemaConfig',
    tolerance: float = 1e-10
) -> None:
    """
    Assert that transformation produces expected output schema.

    Same as validate_round_trip() but raises SchemaValidationError on failure.
    Useful for testing.

    Args:
        target_df: Transformed DataFrame
        source_df: Original DataFrame
        config: SchemaConfig used for transformation
        tolerance: Tolerance for floating point comparisons

    Raises:
        SchemaValidationError: If validation fails

    Example:
        >>> config = SchemaConfig(columns={"old": {"rename": "new"}})
        >>> source = pl.DataFrame({"old": [1, 2, 3]})
        >>> target = transform(source, config)
        >>> assert_round_trip(target, source, config)  # Raises if invalid
    """
    is_valid, errors = validate_round_trip(target_df, source_df, config, tolerance)

    if not is_valid:
        error_msg = "Round-trip validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        raise SchemaValidationError(error_msg)


def validate_schema_match(
    df: 'SupportedDataFrames',
    expected_schema: 'TableSchema',
    strict: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validate that DataFrame matches expected schema.

    Args:
        df: DataFrame to validate
        expected_schema: Expected TableSchema
        strict: If True, extra columns are errors. If False, extra columns allowed.

    Returns:
        Tuple of (is_valid, list_of_error_messages)

    Example:
        >>> expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        >>> df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        >>> is_valid, errors = validate_schema_match(df, expected)
        >>> assert is_valid
    """
    from .extractors import from_dataframe
    from .universal_schema import compare_schemas

    errors = []

    # Extract actual schema
    try:
        actual_schema = from_dataframe(df)
    except Exception as e:
        errors.append(f"Failed to extract schema from DataFrame: {e}")
        return False, errors

    # Compare
    diff = compare_schemas(actual_schema, expected_schema, check_constraints=False)

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


def assert_schema_match(
    df: 'SupportedDataFrames',
    expected_schema: 'TableSchema',
    strict: bool = True
) -> None:
    """
    Assert that DataFrame matches expected schema.

    Same as validate_schema_match() but raises on failure.

    Args:
        df: DataFrame to validate
        expected_schema: Expected TableSchema
        strict: If True, extra columns are errors

    Raises:
        SchemaValidationError: If validation fails
    """
    is_valid, errors = validate_schema_match(df, expected_schema, strict)

    if not is_valid:
        error_msg = "Schema validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        raise SchemaValidationError(error_msg)


def validate_transformation_config(
    config: 'SchemaConfig',
    source_schema: Optional['TableSchema'] = None,
    target_schema: Optional['TableSchema'] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that SchemaConfig is internally consistent and compatible with schemas.

    This is a convenience wrapper around SchemaConfig.validate_against_schemas()
    that allows passing schemas as parameters.

    Args:
        config: SchemaConfig to validate
        source_schema: Optional source schema (overrides config.source_schema)
        target_schema: Optional target schema (overrides config.target_schema)

    Returns:
        Tuple of (is_valid, list_of_error_messages)

    Example:
        >>> source = TableSchema.from_simple_dict({"old_id": "string"})
        >>> target = TableSchema.from_simple_dict({"id": "integer"})
        >>> config = SchemaConfig(columns={"old_id": {"rename": "id", "cast": "integer"}})
        >>> is_valid, errors = validate_transformation_config(config, source, target)
        >>> assert is_valid
    """
    # Use provided schemas or fall back to config's schemas
    if source_schema:
        config.source_schema = source_schema
    if target_schema:
        config.target_schema = target_schema

    return config.validate_against_schemas(
        check_source=config.source_schema is not None,
        check_target=config.target_schema is not None
    )


def assert_transformation_config(
    config: 'SchemaConfig',
    source_schema: Optional['TableSchema'] = None,
    target_schema: Optional['TableSchema'] = None
) -> None:
    """
    Assert that SchemaConfig is valid.

    Same as validate_transformation_config() but raises on failure.

    Args:
        config: SchemaConfig to validate
        source_schema: Optional source schema
        target_schema: Optional target schema

    Raises:
        SchemaValidationError: If validation fails
    """
    is_valid, errors = validate_transformation_config(config, source_schema, target_schema)

    if not is_valid:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        raise SchemaValidationError(error_msg)
