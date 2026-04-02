"""DEPRECATED: Use mountainash.typespec.validation instead.

Re-exports with old names for backward compatibility with pydata.
"""
from mountainash.typespec.validation import (  # noqa: F401
    SchemaValidationError,
    validate_match as validate_schema_match,
    assert_match as assert_schema_match,
)

# validate_round_trip, assert_round_trip, validate_transformation_config,
# assert_transformation_config were not moved to typespec.
# Raise NotImplementedError for any callers relying on them.


def validate_round_trip(df, config, strict: bool = True):  # noqa: F401
    """
    DEPRECATED: validate_round_trip is no longer supported.

    Use mountainash.typespec.validation.validate_match instead.
    """
    raise NotImplementedError(
        "validate_round_trip is deprecated and not available in the typespec-based stack. "
        "Use mountainash.typespec.validation.validate_match instead."
    )


def assert_round_trip(df, config, strict: bool = True) -> None:  # noqa: F401
    """DEPRECATED: assert_round_trip is no longer supported."""
    raise NotImplementedError(
        "assert_round_trip is deprecated and not available in the typespec-based stack. "
        "Use mountainash.typespec.validation.assert_match instead."
    )


def validate_transformation_config(config, df=None):  # noqa: F401
    """DEPRECATED: validate_transformation_config is no longer supported."""
    raise NotImplementedError(
        "validate_transformation_config is deprecated. "
        "Use mountainash.typespec.validation.validate_match instead."
    )


def assert_transformation_config(config, df=None) -> None:  # noqa: F401
    """DEPRECATED: assert_transformation_config is no longer supported."""
    raise NotImplementedError(
        "assert_transformation_config is deprecated. "
        "Use mountainash.typespec.validation.assert_match instead."
    )
