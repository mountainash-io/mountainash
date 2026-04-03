"""Substrait-aligned function ENUMs.

Auto-generated from Substrait extension YAMLs.
DO NOT EDIT MANUALLY - regenerate with: python scripts/generate_from_substrait.py

To add custom extensions, use MOUNTAINASH_* enums in a separate section.

Naming convention:
- SUBSTRAIT_{CATEGORY}_{TYPE}: e.g., SUBSTRAIT_ARITHMETIC_SCALAR, SUBSTRAIT_ARITHMETIC_AGGREGATE
"""

from __future__ import annotations

from enum import Enum


# =============================================================================
# Substrait Extension URIs
# =============================================================================

class SubstraitExtension:
    """Substrait extension URIs for serialization."""
    AGGREGATE_APPROX = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_approx.yaml"
    AGGREGATE_GENERIC = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_generic.yaml"
    AGGREGATE_DECIMAL = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_decimal_output.yaml"
    ARITHMETIC = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml"
    ARITHMETIC_DECIMAL = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml"
    BOOLEAN = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml"
    COMPARISON = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml"
    DATETIME = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml"
    GEOMETRY = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml"
    LOGARITHMIC = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml"
    ROUNDING = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml"
    ROUNDING_DECIMAL = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding_decimal.yaml"
    SET = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_set.yaml"
    STRING = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml"


# =============================================================================
# Aggregate_Approx Functions
# =============================================================================

class SUBSTRAIT_AGGREGATE_APPROX_AGGREGATE(str, Enum):
    """Substrait aggregate_approx aggregate functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_approx.yaml
    Generated: 2025-12-30T19:58:00.694816
    """

    # Calculates the approximate number of rows that contain distinct values...
    APPROX_COUNT_DISTINCT = "approx_count_distinct"



# =============================================================================
# Aggregate_Generic Functions
# =============================================================================

class SUBSTRAIT_AGGREGATE_GENERIC_AGGREGATE(str, Enum):
    """Substrait aggregate_generic aggregate functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_generic.yaml
    Generated: 2025-12-30T19:58:00.694871
    """

    # Count a set of values
    COUNT = "count"

    # Count a set of records (not field referenced)
    COUNT = "count"

    # Selects an arbitrary value from a group of values.
If the input is emp...
    ANY_VALUE = "any_value"



# =============================================================================
# Aggregate_Decimal Functions
# =============================================================================

class SUBSTRAIT_AGGREGATE_DECIMAL_AGGREGATE(str, Enum):
    """Substrait aggregate_decimal aggregate functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_decimal_output.yaml
    Generated: 2025-12-30T19:58:00.694891
    """

    # Count a set of values. Result is returned as a decimal instead of i64.
    COUNT = "count"

    # Count a set of records (not field referenced). Result is returned as a...
    COUNT = "count"

    # Calculates the approximate number of rows that contain distinct values...
    APPROX_COUNT_DISTINCT = "approx_count_distinct"



# =============================================================================
# Arithmetic Functions
# =============================================================================

class SUBSTRAIT_ARITHMETIC_SCALAR(str, Enum):
    """Substrait arithmetic scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
    Generated: 2025-12-30T19:58:00.694908
    """

    # Add two values.
    ADD = "add"

    # Subtract one value from another.
    SUBTRACT = "subtract"

    # Multiply two values.
    MULTIPLY = "multiply"

    # Divide x by y. In the case of integer division, partial values are tru...
    DIVIDE = "divide"

    # Negation of the value
    NEGATE = "negate"

    # Calculate the remainder (r) when dividing dividend (x) by divisor (y)....
    MODULUS = "modulus"

    # Take the power with x as the base and y as exponent.
    POWER = "power"

    # Square root of the value
    SQRT = "sqrt"

    # The mathematical constant e, raised to the power of the value.
    EXP = "exp"

    # Get the cosine of a value in radians.
    COS = "cos"

    # Get the sine of a value in radians.
    SIN = "sin"

    # Get the tangent of a value in radians.
    TAN = "tan"

    # Get the hyperbolic cosine of a value in radians.
    COSH = "cosh"

    # Get the hyperbolic sine of a value in radians.
    SINH = "sinh"

    # Get the hyperbolic tangent of a value in radians.
    TANH = "tanh"

    # Get the arccosine of a value in radians.
    ACOS = "acos"

    # Get the arcsine of a value in radians.
    ASIN = "asin"

    # Get the arctangent of a value in radians.
    ATAN = "atan"

    # Get the hyperbolic arccosine of a value in radians.
    ACOSH = "acosh"

    # Get the hyperbolic arcsine of a value in radians.
    ASINH = "asinh"

    # Get the hyperbolic arctangent of a value in radians.
    ATANH = "atanh"

    # Get the arctangent of values given as x/y pairs.
    ATAN2 = "atan2"

    # Converts angle `x` in degrees to radians.

    RADIANS = "radians"

    # Converts angle `x` in radians to degrees.

    DEGREES = "degrees"

    # Calculate the absolute value of the argument.
Integer values allow the...
    ABS = "abs"

    # Return the signedness of the argument.
Integer values return signednes...
    SIGN = "sign"

    # Return the factorial of a given integer input.
The factorial of 0! is ...
    FACTORIAL = "factorial"

    # Return the bitwise NOT result for one integer input.

    BITWISE_NOT = "bitwise_not"

    # Return the bitwise AND result for two integer inputs.

    BITWISE_AND = "bitwise_and"

    # Return the bitwise OR result for two given integer inputs.

    BITWISE_OR = "bitwise_or"

    # Return the bitwise XOR result for two integer inputs.

    BITWISE_XOR = "bitwise_xor"

    # Bitwise shift left. The vacant (least-significant) bits are filled wit...
    SHIFT_LEFT = "shift_left"

    # Bitwise (signed) shift right. The vacant (most-significant) bits are f...
    SHIFT_RIGHT = "shift_right"

    # Bitwise unsigned shift right. The vacant (most-significant) bits are f...
    SHIFT_RIGHT_UNSIGNED = "shift_right_unsigned"

class SUBSTRAIT_ARITHMETIC_AGGREGATE(str, Enum):
    """Substrait arithmetic aggregate functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
    Generated: 2025-12-30T19:58:00.694969
    """

    # Sum a set of values. The sum of zero elements yields null.
    SUM = "sum"

    # Sum a set of values. The sum of zero elements yields zero.
Null values...
    SUM0 = "sum0"

    # Average a set of values. For integral types, this truncates partial va...
    AVG = "avg"

    # Min a set of values.
    MIN = "min"

    # Max a set of values.
    MAX = "max"

    # Product of a set of values. Returns 1 for empty input.
    PRODUCT = "product"

    # Calculates standard-deviation for a set of values.
    STD_DEV = "std_dev"

    # Calculates variance for a set of values.
    VARIANCE = "variance"

    # Calculates the value of Pearson's correlation coefficient between `x` ...
    CORR = "corr"

    # Calculates mode for a set of values. If there is no input, null is ret...
    MODE = "mode"

    # Calculate the median for a set of values.
Returns null if applied to z...
    MEDIAN = "median"

    # Calculates quantiles for a set of values.
This function will divide th...
    QUANTILE = "quantile"

class SUBSTRAIT_ARITHMETIC_WINDOW(str, Enum):
    """Substrait arithmetic window functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
    Generated: 2025-12-30T19:58:00.694990
    """

    # the number of the current row within its partition, starting at 1
    ROW_NUMBER = "row_number"

    # the rank of the current row, with gaps.
    RANK = "rank"

    # the rank of the current row, without gaps.
    DENSE_RANK = "dense_rank"

    # the relative rank of the current row.
    PERCENT_RANK = "percent_rank"

    # the cumulative distribution.
    CUME_DIST = "cume_dist"

    # Return an integer ranging from 1 to the argument value,dividing the pa...
    NTILE = "ntile"

    # Returns the first value in the window.

    FIRST_VALUE = "first_value"

    # Returns the last value in the window.

    LAST_VALUE = "last_value"

    # Returns a value from the nth row based on the `window_offset`. `window...
    NTH_VALUE = "nth_value"

    # Return a value from a following row based on a specified physical offs...
    LEAD = "lead"

    # Return a column value from a previous row based on a specified physica...
    LAG = "lag"



# =============================================================================
# Arithmetic_Decimal Functions
# =============================================================================

class SUBSTRAIT_ARITHMETIC_DECIMAL_SCALAR(str, Enum):
    """Substrait arithmetic_decimal scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
    Generated: 2025-12-30T19:58:00.695007
    """

    # Add two decimal values.
    ADD = "add"

    SUBTRACT = "subtract"

    MULTIPLY = "multiply"

    DIVIDE = "divide"

    MODULUS = "modulus"

    # Calculate the absolute value of the argument.
    ABS = "abs"

    # Return the bitwise AND result for two decimal inputs. In inputs scale ...
    BITWISE_AND = "bitwise_and"

    # Return the bitwise OR result for two given decimal inputs. In inputs s...
    BITWISE_OR = "bitwise_or"

    # Return the bitwise XOR result for two given decimal inputs. In inputs ...
    BITWISE_XOR = "bitwise_xor"

    # Square root of the value. Sqrt of 0 is 0 and sqrt of negative values w...
    SQRT = "sqrt"

    # Return the factorial of a given decimal input. Scale should be 0 for f...
    FACTORIAL = "factorial"

    # Take the power with x as the base and y as exponent. Behavior for comp...
    POWER = "power"

class SUBSTRAIT_ARITHMETIC_DECIMAL_AGGREGATE(str, Enum):
    """Substrait arithmetic_decimal aggregate functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
    Generated: 2025-12-30T19:58:00.695021
    """

    # Sum a set of values.
    SUM = "sum"

    # Average a set of values.
    AVG = "avg"

    # Min a set of values.
    MIN = "min"

    # Max a set of values.
    MAX = "max"

    # Sum a set of values. The sum of zero elements yields zero.
Null values...
    SUM0 = "sum0"



# =============================================================================
# Boolean Functions
# =============================================================================

class SUBSTRAIT_BOOLEAN_SCALAR(str, Enum):
    """Substrait boolean scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
    Generated: 2025-12-30T19:58:00.695032
    """

    # The boolean `or` using Kleene logic.
This function behaves as follows ...
    OR_ = "or"

    # The boolean `and` using Kleene logic.
This function behaves as follows...
    AND_ = "and"

    # The boolean `and` of one value and the negation of the other using Kle...
    AND_NOT = "and_not"

    # The boolean `xor` of two values using Kleene logic.
When a null is enc...
    XOR = "xor"

    # The `not` of a boolean value.
When a null is input, a null is output.

    NOT_ = "not"

class SUBSTRAIT_BOOLEAN_AGGREGATE(str, Enum):
    """Substrait boolean aggregate functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
    Generated: 2025-12-30T19:58:00.695042
    """

    # If any value in the input is false, false is returned. If the input is...
    BOOL_AND = "bool_and"

    # If any value in the input is true, true is returned. If the input is e...
    BOOL_OR = "bool_or"



# =============================================================================
# Comparison Functions
# =============================================================================

class SUBSTRAIT_COMPARISON_SCALAR(str, Enum):
    """Substrait comparison scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
    Generated: 2025-12-30T19:58:00.695050
    """

    # Whether two values are not_equal.
`not_equal(x, y) := (x != y)`
If eit...
    NOT_EQUAL = "not_equal"

    # Whether two values are equal.
`equal(x, y) := (x == y)`
If either/both...
    EQUAL = "equal"

    # Whether two values are equal.
This function treats `null` values as co...
    IS_NOT_DISTINCT_FROM = "is_not_distinct_from"

    # Whether two values are not equal.
This function treats `null` values a...
    IS_DISTINCT_FROM = "is_distinct_from"

    # Less than.
lt(x, y) := (x < y)
If either/both of `x` and `y` are `null...
    LT = "lt"

    # Greater than.
gt(x, y) := (x > y)
If either/both of `x` and `y` are `n...
    GT = "gt"

    # Less than or equal to.
lte(x, y) := (x <= y)
If either/both of `x` and...
    LTE = "lte"

    # Greater than or equal to.
gte(x, y) := (x >= y)
If either/both of `x` ...
    GTE = "gte"

    # Whether the `expression` is greater than or equal to `low` and less th...
    BETWEEN = "between"

    # Whether a value is true.
    IS_TRUE = "is_true"

    # Whether a value is not true.
    IS_NOT_TRUE = "is_not_true"

    # Whether a value is false.
    IS_FALSE = "is_false"

    # Whether a value is not false.
    IS_NOT_FALSE = "is_not_false"

    # Whether a value is null. NaN is not null.
    IS_NULL = "is_null"

    # Whether a value is not null. NaN is not null.
    IS_NOT_NULL = "is_not_null"

    # Whether a value is not a number.
If `x` is `null`, `null` is returned....
    IS_NAN = "is_nan"

    # Whether a value is finite (neither infinite nor NaN).
If `x` is `null`...
    IS_FINITE = "is_finite"

    # Whether a value is infinite.
If `x` is `null`, `null` is returned.

    IS_INFINITE = "is_infinite"

    # If two values are equal, return null. Otherwise, return the first valu...
    NULLIF = "nullif"

    # Evaluate arguments from left to right and return the first argument th...
    COALESCE = "coalesce"

    # Evaluates each argument and returns the smallest one. The function wil...
    LEAST = "least"

    # Evaluates each argument and returns the smallest one. The function wil...
    LEAST_SKIP_NULL = "least_skip_null"

    # Evaluates each argument and returns the largest one. The function will...
    GREATEST = "greatest"

    # Evaluates each argument and returns the largest one. The function will...
    GREATEST_SKIP_NULL = "greatest_skip_null"



# =============================================================================
# Datetime Functions
# =============================================================================

class SUBSTRAIT_DATETIME_SCALAR(str, Enum):
    """Substrait datetime scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
    Generated: 2025-12-30T19:58:00.695075
    """

    # Extract portion of a date/time value. * YEAR Return the year. * ISO_YE...
    EXTRACT = "extract"

    # Extract boolean values of a date/time value. * IS_LEAP_YEAR Return tru...
    EXTRACT_BOOLEAN = "extract_boolean"

    # Add an interval to a date/time type.
Timezone strings must be as defin...
    ADD = "add"

    # Multiply an interval by an integral number.
    MULTIPLY = "multiply"

    # Add two intervals together.
    ADD_INTERVALS = "add_intervals"

    # Subtract an interval from a date/time type.
Timezone strings must be a...
    SUBTRACT = "subtract"

    # less than or equal to
    LTE = "lte"

    # less than
    LT = "lt"

    # greater than or equal to
    GTE = "gte"

    # greater than
    GT = "gt"

    # Convert local timestamp to UTC-relative timestamp_tz using given local...
    ASSUME_TIMEZONE = "assume_timezone"

    # Convert UTC-relative timestamp_tz to local timestamp using given local...
    LOCAL_TIMESTAMP = "local_timestamp"

    # Parse string into time using provided format, see https://man7.org/lin...
    STRPTIME_TIME = "strptime_time"

    # Parse string into date using provided format, see https://man7.org/lin...
    STRPTIME_DATE = "strptime_date"

    # Parse string into timestamp using provided format, see https://man7.or...
    STRPTIME_TIMESTAMP = "strptime_timestamp"

    # Convert timestamp/date/time to string using provided format, see https...
    STRFTIME = "strftime"

    # Round a given timestamp/date/time to a multiple of a time unit. If the...
    ROUND_TEMPORAL = "round_temporal"

    # Round a given timestamp/date/time to a multiple of a time unit. If the...
    ROUND_CALENDAR = "round_calendar"

class SUBSTRAIT_DATETIME_AGGREGATE(str, Enum):
    """Substrait datetime aggregate functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
    Generated: 2025-12-30T19:58:00.695095
    """

    # Min a set of values.
    MIN = "min"

    # Max a set of values.
    MAX = "max"



# =============================================================================
# Geometry Functions
# =============================================================================

class SUBSTRAIT_GEOMETRY_SCALAR(str, Enum):
    """Substrait geometry scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
    Generated: 2025-12-30T19:58:00.695104
    """

    # Returns a 2D point with the given `x` and `y` coordinate values.

    POINT = "point"

    # Returns a linestring connecting the endpoint of geometry `geom1` to th...
    MAKE_LINE = "make_line"

    # Return the x coordinate of the point.  Return null if not available.

    X_COORDINATE = "x_coordinate"

    # Return the y coordinate of the point.  Return null if not available.

    Y_COORDINATE = "y_coordinate"

    # Return the number of points in the geometry.  The geometry should be a...
    NUM_POINTS = "num_points"

    # Return true is the geometry is an empty geometry.

    IS_EMPTY = "is_empty"

    # Return true if the geometry's start and end points are the same.

    IS_CLOSED = "is_closed"

    # Return true if the geometry does not self intersect.

    IS_SIMPLE = "is_simple"

    # Return true if the geometry's start and end points are the same and it...
    IS_RING = "is_ring"

    # Return the type of geometry as a string.

    GEOMETRY_TYPE = "geometry_type"

    # Return the minimum bounding box for the input geometry as a geometry.
...
    ENVELOPE = "envelope"

    # Return the dimension of the input geometry.  If the input is a collect...
    DIMENSION = "dimension"

    # Return true if the input geometry is a valid 2D geometry.
For 3 dimens...
    IS_VALID = "is_valid"

    # Given the input geometry collection, return a homogenous multi-geometr...
    COLLECTION_EXTRACT = "collection_extract"

    # Return a version of the input geometry with the X and Y axis flipped.
...
    FLIP_COORDINATES = "flip_coordinates"

    # Return a version of the input geometry with duplicate consecutive poin...
    REMOVE_REPEATED_POINTS = "remove_repeated_points"

    # Compute and return an expanded version of the input geometry. All the ...
    BUFFER = "buffer"

    # Return a point which is the geometric center of mass of the input geom...
    CENTROID = "centroid"

    # Return the smallest circle polygon that contains the input geometry.

    MINIMUM_BOUNDING_CIRCLE = "minimum_bounding_circle"



# =============================================================================
# Logarithmic Functions
# =============================================================================

class SUBSTRAIT_LOGARITHMIC_SCALAR(str, Enum):
    """Substrait logarithmic scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
    Generated: 2025-12-30T19:58:00.695125
    """

    # Natural logarithm of the value
    LN = "ln"

    # Logarithm to base 10 of the value
    LOG10 = "log10"

    # Logarithm to base 2 of the value
    LOG2 = "log2"

    # Logarithm of the value with the given base
logb(x, b) => log_{b} (x)

    LOGB = "logb"

    # Natural logarithm (base e) of 1 + x
log1p(x) => log(1+x)

    LOG1P = "log1p"



# =============================================================================
# Rounding Functions
# =============================================================================

class SUBSTRAIT_ROUNDING_SCALAR(str, Enum):
    """Substrait rounding scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
    Generated: 2025-12-30T19:58:00.695134
    """

    # Rounding to the ceiling of the value `x`.

    CEIL = "ceil"

    # Rounding to the floor of the value `x`.

    FLOOR = "floor"

    # Rounding the value `x` to `s` decimal places.

    ROUND = "round"



# =============================================================================
# Rounding_Decimal Functions
# =============================================================================

class SUBSTRAIT_ROUNDING_DECIMAL_SCALAR(str, Enum):
    """Substrait rounding_decimal scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding_decimal.yaml
    Generated: 2025-12-30T19:58:00.695142
    """

    # Rounding to the ceiling of the value `x`.

    CEIL = "ceil"

    # Rounding to the floor of the value `x`.

    FLOOR = "floor"

    # Rounding the value `x` to `s` decimal places.

    ROUND = "round"



# =============================================================================
# Set Functions
# =============================================================================

class SUBSTRAIT_SET_SCALAR(str, Enum):
    """Substrait set scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_set.yaml
    Generated: 2025-12-30T19:58:00.695150
    """

    # Checks the membership of a value in a list of values
Returns the first...
    INDEX_IN = "index_in"



# =============================================================================
# String Functions
# =============================================================================

class SUBSTRAIT_STRING_SCALAR(str, Enum):
    """Substrait string scalar functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
    Generated: 2025-12-30T19:58:00.695157
    """

    # Concatenate strings.
The `null_handling` option determines whether or ...
    CONCAT = "concat"

    # Are two strings like each other.
The `case_sensitivity` option applies...
    LIKE = "like"

    # Extract a substring of a specified `length` starting from position `st...
    SUBSTRING = "substring"

    # Extract a substring that matches the given regular expression pattern....
    REGEXP_MATCH_SUBSTRING = "regexp_match_substring"

    # Extract a substring that matches the given regular expression pattern....
    REGEXP_MATCH_SUBSTRING = "regexp_match_substring"

    # Extract all substrings that match the given regular expression pattern...
    REGEXP_MATCH_SUBSTRING_ALL = "regexp_match_substring_all"

    # Whether the `input` string starts with the `substring`.
The `case_sens...
    STARTS_WITH = "starts_with"

    # Whether `input` string ends with the substring.
The `case_sensitivity`...
    ENDS_WITH = "ends_with"

    # Whether the `input` string contains the `substring`.
The `case_sensiti...
    CONTAINS = "contains"

    # Return the position of the first occurrence of a string in another str...
    STRPOS = "strpos"

    # Return the position of an occurrence of the given regular expression p...
    REGEXP_STRPOS = "regexp_strpos"

    # Return the number of non-overlapping occurrences of a substring in an ...
    COUNT_SUBSTRING = "count_substring"

    # Return the number of non-overlapping occurrences of a regular expressi...
    REGEXP_COUNT_SUBSTRING = "regexp_count_substring"

    # Return the number of non-overlapping occurrences of a regular expressi...
    REGEXP_COUNT_SUBSTRING = "regexp_count_substring"

    # Replace all occurrences of the substring with the replacement string.
...
    REPLACE = "replace"

    # Concatenate strings together separated by a separator.
    CONCAT_WS = "concat_ws"

    # Repeat a string `count` number of times.
    REPEAT = "repeat"

    # Returns the string in reverse order.
    REVERSE = "reverse"

    # Replace a slice of the input string.  A specified 'length' of characte...
    REPLACE_SLICE = "replace_slice"

    # Transform the string to lower case characters. Implementation should f...
    LOWER = "lower"

    # Transform the string to upper case characters. Implementation should f...
    UPPER = "upper"

    # Transform the string's lowercase characters to uppercase and uppercase...
    SWAPCASE = "swapcase"

    # Capitalize the first character of the input string. Implementation sho...
    CAPITALIZE = "capitalize"

    # Converts the input string into titlecase. Capitalize the first charact...
    TITLE = "title"

    # Capitalizes the first character of each word in the input string, incl...
    INITCAP = "initcap"

    # Return the number of characters in the input string.  The length inclu...
    CHAR_LENGTH = "char_length"

    # Return the number of bits in the input string.
    BIT_LENGTH = "bit_length"

    # Return the number of bytes in the input string.
    OCTET_LENGTH = "octet_length"

    # Search a string for a substring that matches a given regular expressio...
    REGEXP_REPLACE = "regexp_replace"

    # Search a string for a substring that matches a given regular expressio...
    REGEXP_REPLACE = "regexp_replace"

    # Remove any occurrence of the characters from the left side of the stri...
    LTRIM = "ltrim"

    # Remove any occurrence of the characters from the right side of the str...
    RTRIM = "rtrim"

    # Remove any occurrence of the characters from the left and right sides ...
    TRIM = "trim"

    # Left-pad the input string with the string of 'characters' until the sp...
    LPAD = "lpad"

    # Right-pad the input string with the string of 'characters' until the s...
    RPAD = "rpad"

    # Center the input string by padding the sides with a single `character`...
    CENTER = "center"

    # Extract `count` characters starting from the left of the string.
    LEFT = "left"

    # Extract `count` characters starting from the right of the string.
    RIGHT = "right"

    # Split a string into a list of strings, based on a specified `separator...
    STRING_SPLIT = "string_split"

    # Split a string into a list of strings, based on a regular expression p...
    REGEXP_STRING_SPLIT = "regexp_string_split"

class SUBSTRAIT_STRING_AGGREGATE(str, Enum):
    """Substrait string aggregate functions.

    Auto-generated from: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
    Generated: 2025-12-30T19:58:00.695192
    """

    # Concatenates a column of string values with a separator.
    STRING_AGG = "string_agg"


# =============================================================================
# Union Types
# =============================================================================

# All scalar functions
SubstraitScalarFunction = SUBSTRAIT_ARITHMETIC_SCALAR | SUBSTRAIT_ARITHMETIC_DECIMAL_SCALAR | SUBSTRAIT_BOOLEAN_SCALAR | SUBSTRAIT_COMPARISON_SCALAR | SUBSTRAIT_DATETIME_SCALAR | SUBSTRAIT_GEOMETRY_SCALAR | SUBSTRAIT_LOGARITHMIC_SCALAR | SUBSTRAIT_ROUNDING_SCALAR | SUBSTRAIT_ROUNDING_DECIMAL_SCALAR | SUBSTRAIT_SET_SCALAR | SUBSTRAIT_STRING_SCALAR

# All aggregate functions
SubstraitAggregateFunction = SUBSTRAIT_AGGREGATE_APPROX_AGGREGATE | SUBSTRAIT_AGGREGATE_GENERIC_AGGREGATE | SUBSTRAIT_AGGREGATE_DECIMAL_AGGREGATE | SUBSTRAIT_ARITHMETIC_AGGREGATE | SUBSTRAIT_ARITHMETIC_DECIMAL_AGGREGATE | SUBSTRAIT_BOOLEAN_AGGREGATE | SUBSTRAIT_DATETIME_AGGREGATE | SUBSTRAIT_STRING_AGGREGATE

# All window functions
SubstraitWindowFunction = SUBSTRAIT_ARITHMETIC_WINDOW

# All functions combined
SubstraitFunction = SUBSTRAIT_AGGREGATE_APPROX_AGGREGATE | SUBSTRAIT_AGGREGATE_GENERIC_AGGREGATE | SUBSTRAIT_AGGREGATE_DECIMAL_AGGREGATE | SUBSTRAIT_ARITHMETIC_SCALAR | SUBSTRAIT_ARITHMETIC_AGGREGATE | SUBSTRAIT_ARITHMETIC_WINDOW | SUBSTRAIT_ARITHMETIC_DECIMAL_SCALAR | SUBSTRAIT_ARITHMETIC_DECIMAL_AGGREGATE | SUBSTRAIT_BOOLEAN_SCALAR | SUBSTRAIT_BOOLEAN_AGGREGATE | SUBSTRAIT_COMPARISON_SCALAR | SUBSTRAIT_DATETIME_SCALAR | SUBSTRAIT_DATETIME_AGGREGATE | SUBSTRAIT_GEOMETRY_SCALAR | SUBSTRAIT_LOGARITHMIC_SCALAR | SUBSTRAIT_ROUNDING_SCALAR | SUBSTRAIT_ROUNDING_DECIMAL_SCALAR | SUBSTRAIT_SET_SCALAR | SUBSTRAIT_STRING_SCALAR | SUBSTRAIT_STRING_AGGREGATE
