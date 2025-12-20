"""Substrait-aligned function ENUMs.

This module defines all function identifiers as ENUMs organized by Substrait extension category.
ENUM values correspond to Substrait function names where applicable.

Usage:
    from ..substrait_nodes.enums import SUBSTRAIT_COMPARISON, SUBSTRAIT_BOOLEAN

    node = ScalarFunctionNode(
        function=SUBSTRAIT_COMPARISON.EQ,  # ENUM instead of string!
        arguments=[left_node, right_node],
    )
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Union


# =============================================================================
# Substrait Extension URIs
# =============================================================================

class SubstraitExtension:
    """Substrait extension URIs for serialization."""

    COMPARISON = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_comparison.yaml"
    BOOLEAN = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_boolean.yaml"
    ARITHMETIC = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_arithmetic.yaml"
    STRING = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_string.yaml"
    DATETIME = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_datetime.yaml"
    ROUNDING = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_rounding.yaml"
    # Custom Mountainash extensions
    MOUNTAINASH = "https://mountainash.dev/extensions/functions_custom.yaml"


# =============================================================================
# Comparison Functions (Substrait-aligned)
# =============================================================================

class SUBSTRAIT_COMPARISON(Enum):
    """Substrait comparison functions.

    See: https://substrait.io/extensions/functions_comparison/

    Note: Values match internal function names (registry keys), not Substrait names.
    The FunctionDef stores the Substrait name separately for serialization.
    """

    # Binary comparisons (values match registry names)
    EQ = auto()
    NE = auto()
    GT = auto()
    LT = auto()
    GE = auto()
    LE = auto()
    BETWEEN = auto()

    # Null checks
    IS_NULL = auto()
    IS_NOT_NULL = auto()

    # Coalesce
    COALESCE = auto()
    GREATEST = auto()
    LEAST = auto()


# =============================================================================
# Boolean Functions (Substrait-aligned)
# =============================================================================

class SUBSTRAIT_BOOLEAN(Enum):
    """Substrait boolean functions.

    See: https://substrait.io/extensions/functions_boolean/

    Note: Values match internal function names (registry keys).
    """

    AND = auto()
    OR = auto()
    NOT = auto()
    XOR = auto()
    AND_NOT = auto()  # a AND (NOT b) - more efficient than separate operations
    IS_TRUE = auto()
    IS_FALSE = auto()


# =============================================================================
# Arithmetic Functions (Substrait-aligned)
# =============================================================================

class SUBSTRAIT_ARITHMETIC(Enum):
    """Substrait arithmetic functions.

    See: https://substrait.io/extensions/functions_arithmetic/

    Note: Values match internal function names (registry keys).
    """

    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    POWER = auto()
    NEGATE = auto()
    ABS = auto()
    SIGN = auto()
    SQRT = auto()
    EXP = auto()
    LN = auto()


# =============================================================================
# String Functions (Substrait-aligned)
# =============================================================================

class SUBSTRAIT_STRING(Enum):
    """Substrait string functions.

    See: https://substrait.io/extensions/functions_string/

    Note: Values match internal function names (registry keys).
    """

    # Case conversion
    UPPER = auto()
    LOWER = auto()

    # Trimming
    TRIM = auto()
    LTRIM = auto()
    RTRIM = auto()

    # Substring operations
    SUBSTRING = auto()
    REPLACE = auto()
    CONCAT = auto()
    SPLIT = auto()

    # String info
    CHAR_LENGTH = auto()

    # Pattern matching
    CONTAINS = auto()
    STARTS_WITH = auto()
    ENDS_WITH = auto()
    LIKE = auto()

    # Regex
    REGEXP_MATCH = auto()
    REGEXP_CONTAINS = auto()
    REGEXP_REPLACE = auto()


# =============================================================================
# Datetime Functions (Substrait-aligned)
# =============================================================================

class SUBSTRAIT_DATETIME(Enum):
    """Substrait datetime functions.

    See: https://substrait.io/extensions/functions_datetime/

    Note: Values match internal function names (registry keys).
    """

    # Extraction
    EXTRACT_YEAR = auto()
    EXTRACT_MONTH = auto()
    EXTRACT_DAY = auto()
    EXTRACT_HOUR = auto()
    EXTRACT_MINUTE = auto()
    EXTRACT_SECOND = auto()
    EXTRACT_WEEKDAY = auto()
    EXTRACT_WEEK = auto()
    EXTRACT_QUARTER = auto()

    # Addition
    ADD_YEARS = auto()
    ADD_MONTHS = auto()
    ADD_DAYS = auto()
    ADD_HOURS = auto()
    ADD_MINUTES = auto()
    ADD_SECONDS = auto()

    # Difference
    DIFF_YEARS = auto()
    DIFF_MONTHS = auto()
    DIFF_DAYS = auto()
    DIFF_HOURS = auto()
    DIFF_MINUTES = auto()
    DIFF_SECONDS = auto()
    DIFF_MILLISECONDS = auto()

    # Manipulation
    TRUNCATE = auto()
    OFFSET_BY = auto()

    # Snapshot
    TODAY = auto()
    NOW = auto()


# =============================================================================
# Rounding Functions (Substrait-aligned)
# =============================================================================

class SUBSTRAIT_ROUNDING(Enum):
    """Substrait rounding functions.

    See: https://substrait.io/extensions/functions_rounding/
    """

    CEIL = auto()
    FLOOR = auto()
    ROUND = auto()


# =============================================================================
# Logarithmic Functions (Substrait-aligned)
# =============================================================================

class SUBSTRAIT_LOGARITHMIC(Enum):
    """Substrait logarithmic functions.

    See: https://substrait.io/extensions/functions_logarithmic/
    """

    LN = auto()
    LOG10 = auto()
    LOG2 = auto()
    LOGB = auto()  # log with custom base


# =============================================================================
# Set Functions (Substrait-aligned)
# =============================================================================

class SUBSTRAIT_SET(Enum):
    """Substrait set membership functions.

    See: https://substrait.io/extensions/
    """

    INDEX_IN = auto()  # Returns index of value in set, or -1 if not found
    IS_IN = auto()  # Returns true if value is in set
    IS_NOT_IN = auto()  # Returns true if value is not in set


# =============================================================================
# Aggregate Functions (Substrait-aligned)
# =============================================================================

class SUBSTRAIT_AGGREGATE(Enum):
    """Substrait aggregate functions.

    See: https://substrait.io/extensions/functions_aggregate_generic/
    """

    COUNT = auto()
    ANY_VALUE = auto()


# =============================================================================
# Mountainash Custom Extensions
# =============================================================================

class MOUNTAINASH_ARITHMETIC(Enum):
    """Mountainash arithmetic extensions not in Substrait."""

    FLOOR_DIVIDE = "floor_divide"


class MOUNTAINASH_COMPARISON(Enum):
    """Mountainash comparison extensions not in Substrait."""

    IS_CLOSE = "is_close"
    XOR_PARITY = "xor_parity"


class MOUNTAINASH_NULL(Enum):
    """Mountainash null handling functions.

    Note: IS_NULL and IS_NOT_NULL are in SUBSTRAIT_COMPARISON.
    These are additional null-related functions.
    """

    FILL_NULL = "fill_null"
    NULL_IF = "null_if"
    ALWAYS_NULL = "always_null"


class MOUNTAINASH_NAME(Enum):
    """Mountainash column naming operations."""

    ALIAS = "alias"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    NAME_TO_UPPER = "name_to_upper"
    NAME_TO_LOWER = "name_to_lower"


class MOUNTAINASH_TERNARY(Enum):
    """Mountainash ternary logic operations.

    Ternary logic uses three values:
    - TRUE (1): Definitely true
    - UNKNOWN (0): Cannot determine
    - FALSE (-1): Definitely false
    """

    # Comparison
    T_EQ = "t_eq"
    T_NE = "t_ne"
    T_GT = "t_gt"
    T_LT = "t_lt"
    T_GE = "t_ge"
    T_LE = "t_le"
    T_IS_IN = "t_is_in"
    T_IS_NOT_IN = "t_is_not_in"

    # Logical
    T_AND = "t_and"
    T_OR = "t_or"
    T_NOT = "t_not"
    T_XOR = "t_xor"
    T_XOR_PARITY = "t_xor_parity"

    # Booleanizers
    IS_TRUE = "ternary_is_true"
    IS_FALSE = "ternary_is_false"
    IS_UNKNOWN = "ternary_is_unknown"
    IS_KNOWN = "ternary_is_known"
    MAYBE_TRUE = "ternary_maybe_true"
    MAYBE_FALSE = "ternary_maybe_false"

    # Conversion
    TO_TERNARY = "to_ternary"

    # Helper
    LIST = "list"


# =============================================================================
# Union Types for Type Hints
# =============================================================================

SubstraitFunction = Union[
    SUBSTRAIT_COMPARISON,
    SUBSTRAIT_BOOLEAN,
    SUBSTRAIT_ARITHMETIC,
    SUBSTRAIT_STRING,
    SUBSTRAIT_DATETIME,
    SUBSTRAIT_ROUNDING,
    SUBSTRAIT_LOGARITHMIC,
    SUBSTRAIT_SET,
    SUBSTRAIT_AGGREGATE,
]

MountainashFunction = Union[
    MOUNTAINASH_ARITHMETIC,
    MOUNTAINASH_COMPARISON,
    MOUNTAINASH_NULL,
    MOUNTAINASH_NAME,
    MOUNTAINASH_TERNARY,
]

# All function enums
FunctionEnum = Union[SubstraitFunction, MountainashFunction]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Extension URIs
    "SubstraitExtension",
    # Substrait functions
    "SUBSTRAIT_COMPARISON",
    "SUBSTRAIT_BOOLEAN",
    "SUBSTRAIT_ARITHMETIC",
    "SUBSTRAIT_STRING",
    "SUBSTRAIT_DATETIME",
    "SUBSTRAIT_ROUNDING",
    "SUBSTRAIT_LOGARITHMIC",
    "SUBSTRAIT_SET",
    "SUBSTRAIT_AGGREGATE",
    # Mountainash extensions
    "MOUNTAINASH_ARITHMETIC",
    "MOUNTAINASH_COMPARISON",
    "MOUNTAINASH_NULL",
    "MOUNTAINASH_NAME",
    "MOUNTAINASH_TERNARY",
    # Type unions
    "SubstraitFunction",
    "MountainashFunction",
    "FunctionEnum",
]
