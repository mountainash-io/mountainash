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

    SCALAR_AGGREGATE = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_aggregate.yaml"
    SCALAR_ARITHMETIC = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_arithmetic.yaml"
    SCALAR_BOOLEAN = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_boolean.yaml"
    SCALAR_COMPARISON = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_comparison.yaml"
    SCALAR_DATETIME = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_datetime.yaml"
    SCALAR_GEOMETRY = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_geometry.yaml"
    SCALAR_LOGARITHMIC = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_logarithmic.yaml"
    SCALAR_ROUNDING = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_rounding.yaml"
    SCALAR_SET = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_set.yaml"
    SCALAR_STRING = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_string.yaml"


class MountainashExtension:
    """Mountainash custom extension URIs - stored in /extensions/ directory."""

    TERNARY = "file://extensions/functions_ternary.yaml"
    DATETIME = "file://extensions/functions_datetime.yaml"
    NULL = "file://extensions/functions_null.yaml"
    NAME = "file://extensions/functions_name.yaml"
    ARITHMETIC = "file://extensions/functions_arithmetic.yaml"
    COMPARISON = "file://extensions/functions_comparison.yaml"



class FKEY_SUBSTRAIT_CONDITIONAL(Enum):
    """Substrait comparison functions.

    See: https://substrait.io/extensions/functions_comparison/

    Note: Values match internal function names (registry keys), not Substrait names.
    The FunctionDef stores the Substrait name separately for serialization.
    """

    # Binary comparisons (values match registry names)
    IF_THEN_ELSE = auto()


class FKEY_SUBSTRAIT_FIELD_REFERENCE(Enum):
    """Substrait comparison functions.

    See: https://substrait.io/extensions/functions_comparison/

    Note: Values match internal function names (registry keys), not Substrait names.
    The FunctionDef stores the Substrait name separately for serialization.
    """

    # Binary comparisons (values match registry names)
    COL = auto()


class FKEY_SUBSTRAIT_CAST(Enum):
    """Substrait comparison functions.

    See: https://substrait.io/extensions/functions_comparison/

    Note: Values match internal function names (registry keys), not Substrait names.
    The FunctionDef stores the Substrait name separately for serialization.
    """

    # Binary comparisons (values match registry names)
    CAST = auto()


class FKEY_SUBSTRAIT_LITERAL(Enum):
    """Substrait comparison functions.

    See: https://substrait.io/extensions/functions_comparison/

    Note: Values match internal function names (registry keys), not Substrait names.
    The FunctionDef stores the Substrait name separately for serialization.
    """

    # Binary comparisons (values match registry names)
    CAST = auto()


# =============================================================================
# Comparison Functions (Substrait-aligned)
# =============================================================================

class FKEY_SUBSTRAIT_SCALAR_AGGREGATE(Enum):
    """Substrait aggregate functions.

    See: https://substrait.io/extensions/functions_aggregate/

    Note: Values match internal function names (registry keys), not Substrait names.
    The FunctionDef stores the Substrait name separately for serialization.
    """

    # Generic aggregate functions
    COUNT = auto()
    ANY_VALUE = auto()

    # Arithmetic aggregate functions
    SUM = auto()
    AVG = auto()
    MIN = auto()
    MAX = auto()
    STD_DEV = auto()
    VARIANCE = auto()
    CORR = auto()
    MODE = auto()
    MEDIAN = auto()
    QUANTILE = auto()
    PRODUCT = auto()
    SUM0 = auto()

    # Boolean aggregate functions
    BOOL_AND = auto()
    BOOL_OR = auto()

    # String aggregate functions
    STRING_AGG = auto()




# =============================================================================
# Arithmetic Functions (Substrait-aligned)
# =============================================================================

class FKEY_SUBSTRAIT_SCALAR_ARITHMETIC(Enum):
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

    # ABS = auto()
    # SIGN = auto()
    # SQRT = auto()
    # EXP = auto()
    # LN = auto()

# =============================================================================
# Comparison Functions (Substrait-aligned)
# =============================================================================

class FKEY_SUBSTRAIT_SCALAR_COMPARISON(Enum):
    """Substrait comparison functions.

    See: https://substrait.io/extensions/functions_comparison/

    Note: Values match internal function names (registry keys), not Substrait names.
    The FunctionDef stores the Substrait name separately for serialization.
    """

    # Binary comparisons (values match registry names)
    EQUAL = auto()
    NOT_EQUAL = auto()
    GT = auto()
    LT = auto()
    GTE = auto()
    LTE = auto()
    BETWEEN = auto()

    # Null checks
    IS_NULL = auto()
    IS_NOT_NULL = auto()

    IS_FALSE = auto()
    IS_NOT_FALSE = auto()

    IS_TRUE = auto()
    IS_NOT_TRUE = auto()

    IS_NAN = auto()
    IS_FINITE = auto()
    IS_INFINITE = auto()

    # Coalesce
    NULL_IF = auto()
    COALESCE = auto()
    GREATEST = auto()
    GREATEST_SKIP_NULL = auto()
    LEAST = auto()
    LEAST_SKIP_NULL = auto()


# =============================================================================
# Boolean Functions (Substrait-aligned)
# =============================================================================

class FKEY_SUBSTRAIT_SCALAR_BOOLEAN(Enum):
    """Substrait boolean functions.

    See: https://substrait.io/extensions/functions_boolean/

    Note: Values match internal function names (registry keys).
    """

    AND = auto()
    OR = auto()
    NOT = auto()
    XOR = auto()
    AND_NOT = auto()
    IS_TRUE = auto()
    IS_FALSE = auto()




# =============================================================================
# String Functions (Substrait-aligned)
# =============================================================================

class FKEY_SUBSTRAIT_SCALAR_STRING(Enum):
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
    REGEXP_SPLIT = auto()



# =============================================================================
# Datetime Functions (Substrait-aligned)
# =============================================================================

class FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC(Enum):
    """Substrait datetime functions.

    See: https://substrait.io/extensions/functions_datetime/

    Note: Values match internal function names (registry keys).
    """

    # Extraction
    LOG = auto()
    LOG10 = auto()
    LOG2 = auto()
    LOGB = auto()

# =============================================================================
# Datetime Functions (Substrait-aligned)
# =============================================================================

class FKEY_SUBSTRAIT_SCALAR_SET(Enum):
    """Substrait datetime functions.

    See: https://substrait.io/extensions/functions_datetime/

    Note: Values match internal function names (registry keys).
    """

    # Extraction
    INDEX_IN = auto()


# =============================================================================
# Datetime Functions (Substrait-aligned)
# =============================================================================

class FKEY_SUBSTRAIT_SCALAR_ROUNDING(Enum):
    """Substrait datetime functions.

    See: https://substrait.io/extensions/functions_datetime/

    Note: Values match internal function names (registry keys).
    """

    # Extraction
    CEIL = auto()
    FLOOR = auto()
    ROUND = auto()

# =============================================================================
# Datetime Functions (Substrait-aligned)
# =============================================================================

class FKEY_SUBSTRAIT_SCALAR_DATETIME(Enum):
    """Substrait datetime functions.

    See: https://substrait.io/extensions/functions_datetime/

    Note: Values match internal function names (registry keys).
    """

    # Extraction
    EXTRACT = auto()
    EXTRACT_BOOLEAN = auto()




class FKEY_MOUNTAINASH_SCALAR_DATETIME(Enum):
    """Mountainash datetime functions.

    Note: Values match internal function names (registry keys).
    """

    # Extraction - Basic
    EXTRACT_YEAR = auto()
    EXTRACT_MONTH = auto()
    EXTRACT_DAY = auto()
    EXTRACT_HOUR = auto()
    EXTRACT_MINUTE = auto()
    EXTRACT_SECOND = auto()
    EXTRACT_MILLISECOND = auto()
    EXTRACT_MICROSECOND = auto()
    EXTRACT_NANOSECOND = auto()

    # Extraction - Calendar
    EXTRACT_QUARTER = auto()
    EXTRACT_DAY_OF_YEAR = auto()
    EXTRACT_WEEKDAY = auto()
    EXTRACT_WEEK = auto()
    EXTRACT_ISO_YEAR = auto()

    # Extraction - Special
    EXTRACT_UNIX_TIME = auto()
    EXTRACT_TIMEZONE_OFFSET = auto()

    # Boolean Extraction
    IS_LEAP_YEAR = auto()
    IS_DST = auto()

    # Addition
    ADD_YEARS = auto()
    ADD_MONTHS = auto()
    ADD_DAYS = auto()
    ADD_HOURS = auto()
    ADD_MINUTES = auto()
    ADD_SECONDS = auto()
    ADD_MILLISECONDS = auto()
    ADD_MICROSECONDS = auto()

    # Difference
    DIFF_YEARS = auto()
    DIFF_MONTHS = auto()
    DIFF_DAYS = auto()
    DIFF_HOURS = auto()
    DIFF_MINUTES = auto()
    DIFF_SECONDS = auto()
    DIFF_MILLISECONDS = auto()

    # Truncation / Rounding
    TRUNCATE = auto()
    ROUND = auto()
    CEIL = auto()
    FLOOR = auto()

    # Timezone
    TO_TIMEZONE = auto()
    ASSUME_TIMEZONE = auto()

    # Formatting
    STRFTIME = auto()

    # Snapshot
    TODAY = auto()
    NOW = auto()

    # Legacy
    OFFSET_BY = auto()


# =============================================================================
# Mountainash Custom Extensions
# =============================================================================

class FKEY_MOUNTAINASH_SCALAR_ARITHMETIC(Enum):
    """Mountainash arithmetic extensions not in Substrait."""

    FLOOR_DIVIDE = "floor_divide"


class FKEY_MOUNTAINASH_SCALAR_COMPARISON(Enum):
    """Mountainash comparison extensions not in Substrait."""

    IS_CLOSE = "is_close"
    XOR_PARITY = "xor_parity"


class FKEY_MOUNTAINASH_NULL(Enum):
    """Mountainash null handling functions.

    Note: IS_NULL and IS_NOT_NULL are in SUBSTRAIT_COMPARISON.
    These are additional null-related functions.
    """

    FILL_NULL = "fill_null"
    NULL_IF = "null_if"
    ALWAYS_NULL = "always_null"


class FKEY_MOUNTAINASH_NAME(Enum):
    """Mountainash column naming operations."""

    ALIAS = "alias"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    NAME_TO_UPPER = "name_to_upper"
    NAME_TO_LOWER = "name_to_lower"


class FKEY_MOUNTAINASH_SCALAR_TERNARY(Enum):
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

    # Constants
    ALWAYS_TRUE = "always_true"
    ALWAYS_FALSE = "always_false"
    ALWAYS_UNKNOWN = "always_unknown"

    # Helper
    LIST = "list"


# =============================================================================
# Ternary Function Categories (Single Source of Truth)
# =============================================================================

# Terminal ternary functions (return boolean, safe to use directly in filters)
MOUNTAINASH_TERNARY_TERMINAL = frozenset({
    FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_TRUE,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_FALSE,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_UNKNOWN,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_KNOWN,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_TRUE,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_FALSE,
})

# Non-terminal ternary functions (return -1/0/1, need booleanization for filters)
MOUNTAINASH_TERNARY_NON_TERMINAL = frozenset({
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_EQ,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_NE,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GT,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_LT,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GE,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_LE,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_IN,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_NOT_IN,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_AND,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_OR,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_NOT,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_XOR,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.T_XOR_PARITY,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.TO_TERNARY,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_TRUE,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_FALSE,
    FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_UNKNOWN,
})

# All ternary functions (terminal + non-terminal)
MOUNTAINASH_TERNARY_ALL = MOUNTAINASH_TERNARY_TERMINAL | MOUNTAINASH_TERNARY_NON_TERMINAL


# =============================================================================
# Union Types for Type Hints
# =============================================================================

SubstraitFunction = Union[
    FKEY_SUBSTRAIT_SCALAR_COMPARISON,
    FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
    FKEY_SUBSTRAIT_SCALAR_STRING,
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
]

MountainashFunction = Union[
    FKEY_MOUNTAINASH_NULL,
    FKEY_MOUNTAINASH_NAME,
    FKEY_MOUNTAINASH_SCALAR_ARITHMETIC,
    FKEY_MOUNTAINASH_SCALAR_COMPARISON,
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
]

# All function enums
FunctionEnum = Union[SubstraitFunction, MountainashFunction]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Extension URIs
    "SubstraitExtension",
    "MountainashExtension",
    # Core function keys
    "FKEY_SUBSTRAIT_CONDITIONAL",
    "FKEY_SUBSTRAIT_FIELD_REFERENCE",
    "FKEY_SUBSTRAIT_CAST",
    "FKEY_SUBSTRAIT_LITERAL",
    # Substrait scalar function keys
    "FKEY_SUBSTRAIT_SCALAR_AGGREGATE",
    "FKEY_SUBSTRAIT_SCALAR_ARITHMETIC",
    "FKEY_SUBSTRAIT_SCALAR_BOOLEAN",
    "FKEY_SUBSTRAIT_SCALAR_COMPARISON",
    "FKEY_SUBSTRAIT_SCALAR_DATETIME",
    "FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC",
    "FKEY_SUBSTRAIT_SCALAR_ROUNDING",
    "FKEY_SUBSTRAIT_SCALAR_SET",
    "FKEY_SUBSTRAIT_SCALAR_STRING",
    # Mountainash extensions
    "FKEY_MOUNTAINASH_SCALAR_ARITHMETIC",
    "FKEY_MOUNTAINASH_SCALAR_COMPARISON",
    "FKEY_MOUNTAINASH_SCALAR_DATETIME",
    "FKEY_MOUNTAINASH_NULL",
    "FKEY_MOUNTAINASH_NAME",
    "FKEY_MOUNTAINASH_SCALAR_TERNARY",
    # Ternary function categories (single source of truth)
    "MOUNTAINASH_TERNARY_TERMINAL",
    "MOUNTAINASH_TERNARY_NON_TERMINAL",
    "MOUNTAINASH_TERNARY_ALL",
    # Type unions
    "SubstraitFunction",
    "MountainashFunction",
    "FunctionEnum",
]
