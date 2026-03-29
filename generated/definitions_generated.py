"""Function definitions auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

Review and adjust:
- backend_method: May differ from Substrait name (e.g., and_ vs and)
- protocol_method: Verify the protocol class and method exist
- Remove functions you don't plan to implement
- Add is_extension=True for custom functions

Organization:
- Functions are grouped by category (arithmetic, boolean, etc.)
- Within each category, functions are sub-grouped by type (scalar, aggregate, window)
"""

from .registry import FunctionRegistry, FunctionDef, SubstraitExtension
from ..protocols import (
    BooleanExpressionProtocol,
    ArithmeticExpressionProtocol,
    StringExpressionProtocol,
    TemporalExpressionProtocol,
    NullExpressionProtocol,
    HorizontalExpressionProtocol,
)


def register_substrait_functions() -> None:
    """Register all Substrait-standard functions."""

    # ========================================
    # Aggregate_Approx Functions
    # ========================================

    # Aggregate functions (1)
    AGGREGATE_APPROX_AGGREGATE_FUNCTIONS = [
        FunctionDef(
            name="approx_count_distinct",
            substrait_uri=SubstraitExtension.AGGREGATE_APPROX,
            substrait_name="approx_count_distinct",
            backend_method="approx_count_distinct",  # TODO: verify backend method name
            category="aggregate_approx",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.approx_count_distinct,  # TODO: verify exists
            # Calculates the approximate number of rows that contain disti...
        ),
    ]


    # ========================================
    # Aggregate_Generic Functions
    # ========================================

    # Aggregate functions (3)
    AGGREGATE_GENERIC_AGGREGATE_FUNCTIONS = [
        FunctionDef(
            name="count",
            substrait_uri=SubstraitExtension.AGGREGATE_GENERIC,
            substrait_name="count",
            backend_method="count",  # TODO: verify backend method name
            category="aggregate_generic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=UnknownProtocol.count,  # TODO: verify exists
            # Count a set of values...
        ),
        FunctionDef(
            name="count",
            substrait_uri=SubstraitExtension.AGGREGATE_GENERIC,
            substrait_name="count",
            backend_method="count",  # TODO: verify backend method name
            category="aggregate_generic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=0,
            options=('overflow',),
            protocol_method=UnknownProtocol.count,  # TODO: verify exists
            # Count a set of records (not field referenced)...
        ),
        FunctionDef(
            name="any_value",
            substrait_uri=SubstraitExtension.AGGREGATE_GENERIC,
            substrait_name="any_value",
            backend_method="any_value",  # TODO: verify backend method name
            category="aggregate_generic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('ignore_nulls',),
            protocol_method=UnknownProtocol.any_value,  # TODO: verify exists
            # Selects an arbitrary value from a group of values.
If the in...
        ),
    ]


    # ========================================
    # Aggregate_Decimal Functions
    # ========================================

    # Aggregate functions (3)
    AGGREGATE_DECIMAL_AGGREGATE_FUNCTIONS = [
        FunctionDef(
            name="count",
            substrait_uri=SubstraitExtension.AGGREGATE_DECIMAL,
            substrait_name="count",
            backend_method="count",  # TODO: verify backend method name
            category="aggregate_decimal",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=UnknownProtocol.count,  # TODO: verify exists
            # Count a set of values. Result is returned as a decimal inste...
        ),
        FunctionDef(
            name="count",
            substrait_uri=SubstraitExtension.AGGREGATE_DECIMAL,
            substrait_name="count",
            backend_method="count",  # TODO: verify backend method name
            category="aggregate_decimal",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=0,
            options=('overflow',),
            protocol_method=UnknownProtocol.count,  # TODO: verify exists
            # Count a set of records (not field referenced). Result is ret...
        ),
        FunctionDef(
            name="approx_count_distinct",
            substrait_uri=SubstraitExtension.AGGREGATE_DECIMAL,
            substrait_name="approx_count_distinct",
            backend_method="approx_count_distinct",  # TODO: verify backend method name
            category="aggregate_decimal",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.approx_count_distinct,  # TODO: verify exists
            # Calculates the approximate number of rows that contain disti...
        ),
    ]


    # ========================================
    # Arithmetic Functions
    # ========================================

    # Scalar functions (34)
    ARITHMETIC_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="add",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="add",
            backend_method="add",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.add,  # TODO: verify exists
            # Add two values....
        ),
        FunctionDef(
            name="subtract",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="subtract",
            backend_method="subtract",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.subtract,  # TODO: verify exists
            # Subtract one value from another....
        ),
        FunctionDef(
            name="multiply",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="multiply",
            backend_method="multiply",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.multiply,  # TODO: verify exists
            # Multiply two values....
        ),
        FunctionDef(
            name="divide",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="divide",
            backend_method="divide",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow', 'on_domain_error', 'on_division_by_zero'),
            protocol_method=ArithmeticExpressionProtocol.divide,  # TODO: verify exists
            # Divide x by y. In the case of integer division, partial valu...
        ),
        FunctionDef(
            name="negate",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="negate",
            backend_method="negate",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.negate,  # TODO: verify exists
            # Negation of the value...
        ),
        FunctionDef(
            name="modulus",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="modulus",
            backend_method="modulus",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('division_type', 'overflow', 'on_domain_error'),
            protocol_method=ArithmeticExpressionProtocol.modulus,  # TODO: verify exists
            # Calculate the remainder (r) when dividing dividend (x) by di...
        ),
        FunctionDef(
            name="power",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="power",
            backend_method="power",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.power,  # TODO: verify exists
            # Take the power with x as the base and y as exponent....
        ),
        FunctionDef(
            name="sqrt",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="sqrt",
            backend_method="sqrt",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'on_domain_error'),
            protocol_method=ArithmeticExpressionProtocol.sqrt,  # TODO: verify exists
            # Square root of the value...
        ),
        FunctionDef(
            name="exp",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="exp",
            backend_method="exp",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.exp,  # TODO: verify exists
            # The mathematical constant e, raised to the power of the valu...
        ),
        FunctionDef(
            name="cos",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="cos",
            backend_method="cos",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.cos,  # TODO: verify exists
            # Get the cosine of a value in radians....
        ),
        FunctionDef(
            name="sin",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="sin",
            backend_method="sin",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.sin,  # TODO: verify exists
            # Get the sine of a value in radians....
        ),
        FunctionDef(
            name="tan",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="tan",
            backend_method="tan",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.tan,  # TODO: verify exists
            # Get the tangent of a value in radians....
        ),
        FunctionDef(
            name="cosh",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="cosh",
            backend_method="cosh",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.cosh,  # TODO: verify exists
            # Get the hyperbolic cosine of a value in radians....
        ),
        FunctionDef(
            name="sinh",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="sinh",
            backend_method="sinh",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.sinh,  # TODO: verify exists
            # Get the hyperbolic sine of a value in radians....
        ),
        FunctionDef(
            name="tanh",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="tanh",
            backend_method="tanh",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.tanh,  # TODO: verify exists
            # Get the hyperbolic tangent of a value in radians....
        ),
        FunctionDef(
            name="acos",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="acos",
            backend_method="acos",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'on_domain_error'),
            protocol_method=ArithmeticExpressionProtocol.acos,  # TODO: verify exists
            # Get the arccosine of a value in radians....
        ),
        FunctionDef(
            name="asin",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="asin",
            backend_method="asin",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'on_domain_error'),
            protocol_method=ArithmeticExpressionProtocol.asin,  # TODO: verify exists
            # Get the arcsine of a value in radians....
        ),
        FunctionDef(
            name="atan",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="atan",
            backend_method="atan",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.atan,  # TODO: verify exists
            # Get the arctangent of a value in radians....
        ),
        FunctionDef(
            name="acosh",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="acosh",
            backend_method="acosh",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'on_domain_error'),
            protocol_method=ArithmeticExpressionProtocol.acosh,  # TODO: verify exists
            # Get the hyperbolic arccosine of a value in radians....
        ),
        FunctionDef(
            name="asinh",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="asinh",
            backend_method="asinh",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.asinh,  # TODO: verify exists
            # Get the hyperbolic arcsine of a value in radians....
        ),
        FunctionDef(
            name="atanh",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="atanh",
            backend_method="atanh",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'on_domain_error'),
            protocol_method=ArithmeticExpressionProtocol.atanh,  # TODO: verify exists
            # Get the hyperbolic arctangent of a value in radians....
        ),
        FunctionDef(
            name="atan2",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="atan2",
            backend_method="atan2",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('rounding', 'on_domain_error'),
            protocol_method=ArithmeticExpressionProtocol.atan2,  # TODO: verify exists
            # Get the arctangent of values given as x/y pairs....
        ),
        FunctionDef(
            name="radians",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="radians",
            backend_method="radians",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.radians,  # TODO: verify exists
            # Converts angle `x` in degrees to radians.
...
        ),
        FunctionDef(
            name="degrees",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="degrees",
            backend_method="degrees",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.degrees,  # TODO: verify exists
            # Converts angle `x` in radians to degrees.
...
        ),
        FunctionDef(
            name="abs",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="abs",
            backend_method="abs",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.abs,  # TODO: verify exists
            # Calculate the absolute value of the argument.
Integer values...
        ),
        FunctionDef(
            name="sign",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="sign",
            backend_method="sign",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.sign,  # TODO: verify exists
            # Return the signedness of the argument.
Integer values return...
        ),
        FunctionDef(
            name="factorial",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="factorial",
            backend_method="factorial",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.factorial,  # TODO: verify exists
            # Return the factorial of a given integer input.
The factorial...
        ),
        FunctionDef(
            name="bitwise_not",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="bitwise_not",
            backend_method="bitwise_not",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.bitwise_not,  # TODO: verify exists
            # Return the bitwise NOT result for one integer input.
...
        ),
        FunctionDef(
            name="bitwise_and",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="bitwise_and",
            backend_method="bitwise_and",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=ArithmeticExpressionProtocol.bitwise_and,  # TODO: verify exists
            # Return the bitwise AND result for two integer inputs.
...
        ),
        FunctionDef(
            name="bitwise_or",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="bitwise_or",
            backend_method="bitwise_or",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=ArithmeticExpressionProtocol.bitwise_or,  # TODO: verify exists
            # Return the bitwise OR result for two given integer inputs.
...
        ),
        FunctionDef(
            name="bitwise_xor",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="bitwise_xor",
            backend_method="bitwise_xor",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=ArithmeticExpressionProtocol.bitwise_xor,  # TODO: verify exists
            # Return the bitwise XOR result for two integer inputs.
...
        ),
        FunctionDef(
            name="shift_left",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="shift_left",
            backend_method="shift_left",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=ArithmeticExpressionProtocol.shift_left,  # TODO: verify exists
            # Bitwise shift left. The vacant (least-significant) bits are ...
        ),
        FunctionDef(
            name="shift_right",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="shift_right",
            backend_method="shift_right",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=ArithmeticExpressionProtocol.shift_right,  # TODO: verify exists
            # Bitwise (signed) shift right. The vacant (most-significant) ...
        ),
        FunctionDef(
            name="shift_right_unsigned",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="shift_right_unsigned",
            backend_method="shift_right_unsigned",  # TODO: verify backend method name
            category="arithmetic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=ArithmeticExpressionProtocol.shift_right_unsigned,  # TODO: verify exists
            # Bitwise unsigned shift right. The vacant (most-significant) ...
        ),
    ]

    # Aggregate functions (12)
    ARITHMETIC_AGGREGATE_FUNCTIONS = [
        FunctionDef(
            name="sum",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="sum",
            backend_method="sum",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.sum,  # TODO: verify exists
            # Sum a set of values. The sum of zero elements yields null....
        ),
        FunctionDef(
            name="sum0",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="sum0",
            backend_method="sum0",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.sum0,  # TODO: verify exists
            # Sum a set of values. The sum of zero elements yields zero.
N...
        ),
        FunctionDef(
            name="avg",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="avg",
            backend_method="avg",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.avg,  # TODO: verify exists
            # Average a set of values. For integral types, this truncates ...
        ),
        FunctionDef(
            name="min",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="min",
            backend_method="min",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.min,  # TODO: verify exists
            # Min a set of values....
        ),
        FunctionDef(
            name="max",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="max",
            backend_method="max",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.max,  # TODO: verify exists
            # Max a set of values....
        ),
        FunctionDef(
            name="product",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="product",
            backend_method="product",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=ArithmeticExpressionProtocol.product,  # TODO: verify exists
            # Product of a set of values. Returns 1 for empty input....
        ),
        FunctionDef(
            name="std_dev",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="std_dev",
            backend_method="std_dev",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'distribution'),
            protocol_method=ArithmeticExpressionProtocol.std_dev,  # TODO: verify exists
            # Calculates standard-deviation for a set of values....
        ),
        FunctionDef(
            name="variance",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="variance",
            backend_method="variance",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'distribution'),
            protocol_method=ArithmeticExpressionProtocol.variance,  # TODO: verify exists
            # Calculates variance for a set of values....
        ),
        FunctionDef(
            name="corr",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="corr",
            backend_method="corr",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=2,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.corr,  # TODO: verify exists
            # Calculates the value of Pearson's correlation coefficient be...
        ),
        FunctionDef(
            name="mode",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="mode",
            backend_method="mode",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.mode,  # TODO: verify exists
            # Calculates mode for a set of values. If there is no input, n...
        ),
        FunctionDef(
            name="median",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="median",
            backend_method="median",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=2,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.median,  # TODO: verify exists
            # Calculate the median for a set of values.
Returns null if ap...
        ),
        FunctionDef(
            name="quantile",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="quantile",
            backend_method="quantile",  # TODO: verify backend method name
            category="arithmetic",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=4,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.quantile,  # TODO: verify exists
            # Calculates quantiles for a set of values.
This function will...
        ),
    ]

    # Window functions (11)
    ARITHMETIC_WINDOW_FUNCTIONS = [
        FunctionDef(
            name="row_number",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="row_number",
            backend_method="row_number",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=0,
            protocol_method=ArithmeticExpressionProtocol.row_number,  # TODO: verify exists
            # the number of the current row within its partition, starting...
        ),
        FunctionDef(
            name="rank",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="rank",
            backend_method="rank",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=0,
            protocol_method=ArithmeticExpressionProtocol.rank,  # TODO: verify exists
            # the rank of the current row, with gaps....
        ),
        FunctionDef(
            name="dense_rank",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="dense_rank",
            backend_method="dense_rank",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=0,
            protocol_method=ArithmeticExpressionProtocol.dense_rank,  # TODO: verify exists
            # the rank of the current row, without gaps....
        ),
        FunctionDef(
            name="percent_rank",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="percent_rank",
            backend_method="percent_rank",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=0,
            protocol_method=ArithmeticExpressionProtocol.percent_rank,  # TODO: verify exists
            # the relative rank of the current row....
        ),
        FunctionDef(
            name="cume_dist",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="cume_dist",
            backend_method="cume_dist",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=0,
            protocol_method=ArithmeticExpressionProtocol.cume_dist,  # TODO: verify exists
            # the cumulative distribution....
        ),
        FunctionDef(
            name="ntile",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="ntile",
            backend_method="ntile",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.ntile,  # TODO: verify exists
            # Return an integer ranging from 1 to the argument value,divid...
        ),
        FunctionDef(
            name="first_value",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="first_value",
            backend_method="first_value",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.first_value,  # TODO: verify exists
            # Returns the first value in the window.
...
        ),
        FunctionDef(
            name="last_value",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="last_value",
            backend_method="last_value",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.last_value,  # TODO: verify exists
            # Returns the last value in the window.
...
        ),
        FunctionDef(
            name="nth_value",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="nth_value",
            backend_method="nth_value",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=2,
            options=('on_domain_error',),
            protocol_method=ArithmeticExpressionProtocol.nth_value,  # TODO: verify exists
            # Returns a value from the nth row based on the `window_offset...
        ),
        FunctionDef(
            name="lead",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="lead",
            backend_method="lead",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.lead,  # TODO: verify exists
            # Return a value from a following row based on a specified phy...
        ),
        FunctionDef(
            name="lag",
            substrait_uri=SubstraitExtension.ARITHMETIC,
            substrait_name="lag",
            backend_method="lag",  # TODO: verify backend method name
            category="arithmetic",
            function_type="window",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.lag,  # TODO: verify exists
            # Return a column value from a previous row based on a specifi...
        ),
    ]


    # ========================================
    # Arithmetic_Decimal Functions
    # ========================================

    # Scalar functions (12)
    ARITHMETIC_DECIMAL_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="add",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="add",
            backend_method="add",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow',),
            protocol_method=UnknownProtocol.add,  # TODO: verify exists
            # Add two decimal values....
        ),
        FunctionDef(
            name="subtract",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="subtract",
            backend_method="subtract",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow',),
            protocol_method=UnknownProtocol.subtract,  # TODO: verify exists
            # ...
        ),
        FunctionDef(
            name="multiply",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="multiply",
            backend_method="multiply",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow',),
            protocol_method=UnknownProtocol.multiply,  # TODO: verify exists
            # ...
        ),
        FunctionDef(
            name="divide",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="divide",
            backend_method="divide",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow',),
            protocol_method=UnknownProtocol.divide,  # TODO: verify exists
            # ...
        ),
        FunctionDef(
            name="modulus",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="modulus",
            backend_method="modulus",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow',),
            protocol_method=UnknownProtocol.modulus,  # TODO: verify exists
            # ...
        ),
        FunctionDef(
            name="abs",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="abs",
            backend_method="abs",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.abs,  # TODO: verify exists
            # Calculate the absolute value of the argument....
        ),
        FunctionDef(
            name="bitwise_and",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="bitwise_and",
            backend_method="bitwise_and",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=UnknownProtocol.bitwise_and,  # TODO: verify exists
            # Return the bitwise AND result for two decimal inputs. In inp...
        ),
        FunctionDef(
            name="bitwise_or",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="bitwise_or",
            backend_method="bitwise_or",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=UnknownProtocol.bitwise_or,  # TODO: verify exists
            # Return the bitwise OR result for two given decimal inputs. I...
        ),
        FunctionDef(
            name="bitwise_xor",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="bitwise_xor",
            backend_method="bitwise_xor",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=UnknownProtocol.bitwise_xor,  # TODO: verify exists
            # Return the bitwise XOR result for two given decimal inputs. ...
        ),
        FunctionDef(
            name="sqrt",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="sqrt",
            backend_method="sqrt",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.sqrt,  # TODO: verify exists
            # Square root of the value. Sqrt of 0 is 0 and sqrt of negativ...
        ),
        FunctionDef(
            name="factorial",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="factorial",
            backend_method="factorial",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.factorial,  # TODO: verify exists
            # Return the factorial of a given decimal input. Scale should ...
        ),
        FunctionDef(
            name="power",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="power",
            backend_method="power",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('overflow', 'complex_number_result'),
            protocol_method=UnknownProtocol.power,  # TODO: verify exists
            # Take the power with x as the base and y as exponent. Behavio...
        ),
    ]

    # Aggregate functions (5)
    ARITHMETIC_DECIMAL_AGGREGATE_FUNCTIONS = [
        FunctionDef(
            name="sum",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="sum",
            backend_method="sum",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=UnknownProtocol.sum,  # TODO: verify exists
            # Sum a set of values....
        ),
        FunctionDef(
            name="avg",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="avg",
            backend_method="avg",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=UnknownProtocol.avg,  # TODO: verify exists
            # Average a set of values....
        ),
        FunctionDef(
            name="min",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="min",
            backend_method="min",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.min,  # TODO: verify exists
            # Min a set of values....
        ),
        FunctionDef(
            name="max",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="max",
            backend_method="max",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.max,  # TODO: verify exists
            # Max a set of values....
        ),
        FunctionDef(
            name="sum0",
            substrait_uri=SubstraitExtension.ARITHMETIC_DECIMAL,
            substrait_name="sum0",
            backend_method="sum0",  # TODO: verify backend method name
            category="arithmetic_decimal",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            options=('overflow',),
            protocol_method=UnknownProtocol.sum0,  # TODO: verify exists
            # Sum a set of values. The sum of zero elements yields zero.
N...
        ),
    ]


    # ========================================
    # Boolean Functions
    # ========================================

    # Scalar functions (5)
    BOOLEAN_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="or_",
            substrait_uri=SubstraitExtension.BOOLEAN,
            substrait_name="or",
            backend_method="or_",  # TODO: verify backend method name
            category="boolean",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=None,
            protocol_method=BooleanExpressionProtocol.or_,  # TODO: verify exists
            # The boolean `or` using Kleene logic.
This function behaves a...
        ),
        FunctionDef(
            name="and_",
            substrait_uri=SubstraitExtension.BOOLEAN,
            substrait_name="and",
            backend_method="and_",  # TODO: verify backend method name
            category="boolean",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=None,
            protocol_method=BooleanExpressionProtocol.and_,  # TODO: verify exists
            # The boolean `and` using Kleene logic.
This function behaves ...
        ),
        FunctionDef(
            name="and_not",
            substrait_uri=SubstraitExtension.BOOLEAN,
            substrait_name="and_not",
            backend_method="and_not",  # TODO: verify backend method name
            category="boolean",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.and_not,  # TODO: verify exists
            # The boolean `and` of one value and the negation of the other...
        ),
        FunctionDef(
            name="xor",
            substrait_uri=SubstraitExtension.BOOLEAN,
            substrait_name="xor",
            backend_method="xor",  # TODO: verify backend method name
            category="boolean",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.xor,  # TODO: verify exists
            # The boolean `xor` of two values using Kleene logic.
When a n...
        ),
        FunctionDef(
            name="not_",
            substrait_uri=SubstraitExtension.BOOLEAN,
            substrait_name="not",
            backend_method="not_",  # TODO: verify backend method name
            category="boolean",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.not_,  # TODO: verify exists
            # The `not` of a boolean value.
When a null is input, a null i...
        ),
    ]

    # Aggregate functions (2)
    BOOLEAN_AGGREGATE_FUNCTIONS = [
        FunctionDef(
            name="bool_and",
            substrait_uri=SubstraitExtension.BOOLEAN,
            substrait_name="bool_and",
            backend_method="bool_and",  # TODO: verify backend method name
            category="boolean",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.bool_and,  # TODO: verify exists
            # If any value in the input is false, false is returned. If th...
        ),
        FunctionDef(
            name="bool_or",
            substrait_uri=SubstraitExtension.BOOLEAN,
            substrait_name="bool_or",
            backend_method="bool_or",  # TODO: verify backend method name
            category="boolean",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.bool_or,  # TODO: verify exists
            # If any value in the input is true, true is returned. If the ...
        ),
    ]


    # ========================================
    # Comparison Functions
    # ========================================

    # Scalar functions (24)
    COMPARISON_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="not_equal",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="not_equal",
            backend_method="not_equal",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.not_equal,  # TODO: verify exists
            # Whether two values are not_equal.
`not_equal(x, y) := (x != ...
        ),
        FunctionDef(
            name="equal",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="equal",
            backend_method="equal",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.equal,  # TODO: verify exists
            # Whether two values are equal.
`equal(x, y) := (x == y)`
If e...
        ),
        FunctionDef(
            name="is_not_distinct_from",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_not_distinct_from",
            backend_method="is_not_distinct_from",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.is_not_distinct_from,  # TODO: verify exists
            # Whether two values are equal.
This function treats `null` va...
        ),
        FunctionDef(
            name="is_distinct_from",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_distinct_from",
            backend_method="is_distinct_from",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.is_distinct_from,  # TODO: verify exists
            # Whether two values are not equal.
This function treats `null...
        ),
        FunctionDef(
            name="lt",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="lt",
            backend_method="lt",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.lt,  # TODO: verify exists
            # Less than.
lt(x, y) := (x < y)
If either/both of `x` and `y`...
        ),
        FunctionDef(
            name="gt",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="gt",
            backend_method="gt",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.gt,  # TODO: verify exists
            # Greater than.
gt(x, y) := (x > y)
If either/both of `x` and ...
        ),
        FunctionDef(
            name="lte",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="lte",
            backend_method="lte",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.lte,  # TODO: verify exists
            # Less than or equal to.
lte(x, y) := (x <= y)
If either/both ...
        ),
        FunctionDef(
            name="gte",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="gte",
            backend_method="gte",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.gte,  # TODO: verify exists
            # Greater than or equal to.
gte(x, y) := (x >= y)
If either/bo...
        ),
        FunctionDef(
            name="between",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="between",
            backend_method="between",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=3,
            protocol_method=BooleanExpressionProtocol.between,  # TODO: verify exists
            # Whether the `expression` is greater than or equal to `low` a...
        ),
        FunctionDef(
            name="is_true",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_true",
            backend_method="is_true",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.is_true,  # TODO: verify exists
            # Whether a value is true....
        ),
        FunctionDef(
            name="is_not_true",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_not_true",
            backend_method="is_not_true",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.is_not_true,  # TODO: verify exists
            # Whether a value is not true....
        ),
        FunctionDef(
            name="is_false",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_false",
            backend_method="is_false",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.is_false,  # TODO: verify exists
            # Whether a value is false....
        ),
        FunctionDef(
            name="is_not_false",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_not_false",
            backend_method="is_not_false",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.is_not_false,  # TODO: verify exists
            # Whether a value is not false....
        ),
        FunctionDef(
            name="is_null",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_null",
            backend_method="is_null",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.is_null,  # TODO: verify exists
            # Whether a value is null. NaN is not null....
        ),
        FunctionDef(
            name="is_not_null",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_not_null",
            backend_method="is_not_null",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.is_not_null,  # TODO: verify exists
            # Whether a value is not null. NaN is not null....
        ),
        FunctionDef(
            name="is_nan",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_nan",
            backend_method="is_nan",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.is_nan,  # TODO: verify exists
            # Whether a value is not a number.
If `x` is `null`, `null` is...
        ),
        FunctionDef(
            name="is_finite",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_finite",
            backend_method="is_finite",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.is_finite,  # TODO: verify exists
            # Whether a value is finite (neither infinite nor NaN).
If `x`...
        ),
        FunctionDef(
            name="is_infinite",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="is_infinite",
            backend_method="is_infinite",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=BooleanExpressionProtocol.is_infinite,  # TODO: verify exists
            # Whether a value is infinite.
If `x` is `null`, `null` is ret...
        ),
        FunctionDef(
            name="nullif",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="nullif",
            backend_method="nullif",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=BooleanExpressionProtocol.nullif,  # TODO: verify exists
            # If two values are equal, return null. Otherwise, return the ...
        ),
        FunctionDef(
            name="coalesce",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="coalesce",
            backend_method="coalesce",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=None,
            protocol_method=BooleanExpressionProtocol.coalesce,  # TODO: verify exists
            # Evaluate arguments from left to right and return the first a...
        ),
        FunctionDef(
            name="least",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="least",
            backend_method="least",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=None,
            protocol_method=BooleanExpressionProtocol.least,  # TODO: verify exists
            # Evaluates each argument and returns the smallest one. The fu...
        ),
        FunctionDef(
            name="least_skip_null",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="least_skip_null",
            backend_method="least_skip_null",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=None,
            protocol_method=BooleanExpressionProtocol.least_skip_null,  # TODO: verify exists
            # Evaluates each argument and returns the smallest one. The fu...
        ),
        FunctionDef(
            name="greatest",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="greatest",
            backend_method="greatest",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=None,
            protocol_method=BooleanExpressionProtocol.greatest,  # TODO: verify exists
            # Evaluates each argument and returns the largest one. The fun...
        ),
        FunctionDef(
            name="greatest_skip_null",
            substrait_uri=SubstraitExtension.COMPARISON,
            substrait_name="greatest_skip_null",
            backend_method="greatest_skip_null",  # TODO: verify backend method name
            category="comparison",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=None,
            protocol_method=BooleanExpressionProtocol.greatest_skip_null,  # TODO: verify exists
            # Evaluates each argument and returns the largest one. The fun...
        ),
    ]


    # ========================================
    # Datetime Functions
    # ========================================

    # Scalar functions (18)
    DATETIME_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="extract",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="extract",
            backend_method="extract",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=3,
            protocol_method=TemporalExpressionProtocol.extract,  # TODO: verify exists
            # Extract portion of a date/time value. * YEAR Return the year...
        ),
        FunctionDef(
            name="extract_boolean",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="extract_boolean",
            backend_method="extract_boolean",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.extract_boolean,  # TODO: verify exists
            # Extract boolean values of a date/time value. * IS_LEAP_YEAR ...
        ),
        FunctionDef(
            name="add",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="add",
            backend_method="add",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.add,  # TODO: verify exists
            # Add an interval to a date/time type.
Timezone strings must b...
        ),
        FunctionDef(
            name="multiply",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="multiply",
            backend_method="multiply",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.multiply,  # TODO: verify exists
            # Multiply an interval by an integral number....
        ),
        FunctionDef(
            name="add_intervals",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="add_intervals",
            backend_method="add_intervals",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.add_intervals,  # TODO: verify exists
            # Add two intervals together....
        ),
        FunctionDef(
            name="subtract",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="subtract",
            backend_method="subtract",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.subtract,  # TODO: verify exists
            # Subtract an interval from a date/time type.
Timezone strings...
        ),
        FunctionDef(
            name="lte",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="lte",
            backend_method="lte",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.lte,  # TODO: verify exists
            # less than or equal to...
        ),
        FunctionDef(
            name="lt",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="lt",
            backend_method="lt",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.lt,  # TODO: verify exists
            # less than...
        ),
        FunctionDef(
            name="gte",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="gte",
            backend_method="gte",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.gte,  # TODO: verify exists
            # greater than or equal to...
        ),
        FunctionDef(
            name="gt",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="gt",
            backend_method="gt",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.gt,  # TODO: verify exists
            # greater than...
        ),
        FunctionDef(
            name="assume_timezone",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="assume_timezone",
            backend_method="assume_timezone",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.assume_timezone,  # TODO: verify exists
            # Convert local timestamp to UTC-relative timestamp_tz using g...
        ),
        FunctionDef(
            name="local_timestamp",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="local_timestamp",
            backend_method="local_timestamp",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.local_timestamp,  # TODO: verify exists
            # Convert UTC-relative timestamp_tz to local timestamp using g...
        ),
        FunctionDef(
            name="strptime_time",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="strptime_time",
            backend_method="strptime_time",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.strptime_time,  # TODO: verify exists
            # Parse string into time using provided format, see https://ma...
        ),
        FunctionDef(
            name="strptime_date",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="strptime_date",
            backend_method="strptime_date",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.strptime_date,  # TODO: verify exists
            # Parse string into date using provided format, see https://ma...
        ),
        FunctionDef(
            name="strptime_timestamp",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="strptime_timestamp",
            backend_method="strptime_timestamp",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=3,
            protocol_method=TemporalExpressionProtocol.strptime_timestamp,  # TODO: verify exists
            # Parse string into timestamp using provided format, see https...
        ),
        FunctionDef(
            name="strftime",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="strftime",
            backend_method="strftime",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=TemporalExpressionProtocol.strftime,  # TODO: verify exists
            # Convert timestamp/date/time to string using provided format,...
        ),
        FunctionDef(
            name="round_temporal",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="round_temporal",
            backend_method="round_temporal",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=5,
            protocol_method=TemporalExpressionProtocol.round_temporal,  # TODO: verify exists
            # Round a given timestamp/date/time to a multiple of a time un...
        ),
        FunctionDef(
            name="round_calendar",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="round_calendar",
            backend_method="round_calendar",  # TODO: verify backend method name
            category="datetime",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=5,
            protocol_method=TemporalExpressionProtocol.round_calendar,  # TODO: verify exists
            # Round a given timestamp/date/time to a multiple of a time un...
        ),
    ]

    # Aggregate functions (2)
    DATETIME_AGGREGATE_FUNCTIONS = [
        FunctionDef(
            name="min",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="min",
            backend_method="min",  # TODO: verify backend method name
            category="datetime",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=TemporalExpressionProtocol.min,  # TODO: verify exists
            # Min a set of values....
        ),
        FunctionDef(
            name="max",
            substrait_uri=SubstraitExtension.DATETIME,
            substrait_name="max",
            backend_method="max",  # TODO: verify backend method name
            category="datetime",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=TemporalExpressionProtocol.max,  # TODO: verify exists
            # Max a set of values....
        ),
    ]


    # ========================================
    # Geometry Functions
    # ========================================

    # Scalar functions (19)
    GEOMETRY_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="point",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="point",
            backend_method="point",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=UnknownProtocol.point,  # TODO: verify exists
            # Returns a 2D point with the given `x` and `y` coordinate val...
        ),
        FunctionDef(
            name="make_line",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="make_line",
            backend_method="make_line",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=UnknownProtocol.make_line,  # TODO: verify exists
            # Returns a linestring connecting the endpoint of geometry `ge...
        ),
        FunctionDef(
            name="x_coordinate",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="x_coordinate",
            backend_method="x_coordinate",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.x_coordinate,  # TODO: verify exists
            # Return the x coordinate of the point.  Return null if not av...
        ),
        FunctionDef(
            name="y_coordinate",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="y_coordinate",
            backend_method="y_coordinate",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.y_coordinate,  # TODO: verify exists
            # Return the y coordinate of the point.  Return null if not av...
        ),
        FunctionDef(
            name="num_points",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="num_points",
            backend_method="num_points",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.num_points,  # TODO: verify exists
            # Return the number of points in the geometry.  The geometry s...
        ),
        FunctionDef(
            name="is_empty",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="is_empty",
            backend_method="is_empty",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.is_empty,  # TODO: verify exists
            # Return true is the geometry is an empty geometry.
...
        ),
        FunctionDef(
            name="is_closed",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="is_closed",
            backend_method="is_closed",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.is_closed,  # TODO: verify exists
            # Return true if the geometry's start and end points are the s...
        ),
        FunctionDef(
            name="is_simple",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="is_simple",
            backend_method="is_simple",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.is_simple,  # TODO: verify exists
            # Return true if the geometry does not self intersect.
...
        ),
        FunctionDef(
            name="is_ring",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="is_ring",
            backend_method="is_ring",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.is_ring,  # TODO: verify exists
            # Return true if the geometry's start and end points are the s...
        ),
        FunctionDef(
            name="geometry_type",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="geometry_type",
            backend_method="geometry_type",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.geometry_type,  # TODO: verify exists
            # Return the type of geometry as a string.
...
        ),
        FunctionDef(
            name="envelope",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="envelope",
            backend_method="envelope",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.envelope,  # TODO: verify exists
            # Return the minimum bounding box for the input geometry as a ...
        ),
        FunctionDef(
            name="dimension",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="dimension",
            backend_method="dimension",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.dimension,  # TODO: verify exists
            # Return the dimension of the input geometry.  If the input is...
        ),
        FunctionDef(
            name="is_valid",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="is_valid",
            backend_method="is_valid",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.is_valid,  # TODO: verify exists
            # Return true if the input geometry is a valid 2D geometry.
Fo...
        ),
        FunctionDef(
            name="collection_extract",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="collection_extract",
            backend_method="collection_extract",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.collection_extract,  # TODO: verify exists
            # Given the input geometry collection, return a homogenous mul...
        ),
        FunctionDef(
            name="flip_coordinates",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="flip_coordinates",
            backend_method="flip_coordinates",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.flip_coordinates,  # TODO: verify exists
            # Return a version of the input geometry with the X and Y axis...
        ),
        FunctionDef(
            name="remove_repeated_points",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="remove_repeated_points",
            backend_method="remove_repeated_points",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.remove_repeated_points,  # TODO: verify exists
            # Return a version of the input geometry with duplicate consec...
        ),
        FunctionDef(
            name="buffer",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="buffer",
            backend_method="buffer",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=UnknownProtocol.buffer,  # TODO: verify exists
            # Compute and return an expanded version of the input geometry...
        ),
        FunctionDef(
            name="centroid",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="centroid",
            backend_method="centroid",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.centroid,  # TODO: verify exists
            # Return a point which is the geometric center of mass of the ...
        ),
        FunctionDef(
            name="minimum_bounding_circle",
            substrait_uri=SubstraitExtension.GEOMETRY,
            substrait_name="minimum_bounding_circle",
            backend_method="minimum_bounding_circle",  # TODO: verify backend method name
            category="geometry",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.minimum_bounding_circle,  # TODO: verify exists
            # Return the smallest circle polygon that contains the input g...
        ),
    ]


    # ========================================
    # Logarithmic Functions
    # ========================================

    # Scalar functions (5)
    LOGARITHMIC_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="ln",
            substrait_uri=SubstraitExtension.LOGARITHMIC,
            substrait_name="ln",
            backend_method="ln",  # TODO: verify backend method name
            category="logarithmic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'on_domain_error', 'on_log_zero'),
            protocol_method=ArithmeticExpressionProtocol.ln,  # TODO: verify exists
            # Natural logarithm of the value...
        ),
        FunctionDef(
            name="log10",
            substrait_uri=SubstraitExtension.LOGARITHMIC,
            substrait_name="log10",
            backend_method="log10",  # TODO: verify backend method name
            category="logarithmic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'on_domain_error', 'on_log_zero'),
            protocol_method=ArithmeticExpressionProtocol.log10,  # TODO: verify exists
            # Logarithm to base 10 of the value...
        ),
        FunctionDef(
            name="log2",
            substrait_uri=SubstraitExtension.LOGARITHMIC,
            substrait_name="log2",
            backend_method="log2",  # TODO: verify backend method name
            category="logarithmic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'on_domain_error', 'on_log_zero'),
            protocol_method=ArithmeticExpressionProtocol.log2,  # TODO: verify exists
            # Logarithm to base 2 of the value...
        ),
        FunctionDef(
            name="logb",
            substrait_uri=SubstraitExtension.LOGARITHMIC,
            substrait_name="logb",
            backend_method="logb",  # TODO: verify backend method name
            category="logarithmic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('rounding', 'on_domain_error', 'on_log_zero'),
            protocol_method=ArithmeticExpressionProtocol.logb,  # TODO: verify exists
            # Logarithm of the value with the given base
logb(x, b) => log...
        ),
        FunctionDef(
            name="log1p",
            substrait_uri=SubstraitExtension.LOGARITHMIC,
            substrait_name="log1p",
            backend_method="log1p",  # TODO: verify backend method name
            category="logarithmic",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('rounding', 'on_domain_error', 'on_log_zero'),
            protocol_method=ArithmeticExpressionProtocol.log1p,  # TODO: verify exists
            # Natural logarithm (base e) of 1 + x
log1p(x) => log(1+x)
...
        ),
    ]


    # ========================================
    # Rounding Functions
    # ========================================

    # Scalar functions (3)
    ROUNDING_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="ceil",
            substrait_uri=SubstraitExtension.ROUNDING,
            substrait_name="ceil",
            backend_method="ceil",  # TODO: verify backend method name
            category="rounding",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.ceil,  # TODO: verify exists
            # Rounding to the ceiling of the value `x`.
...
        ),
        FunctionDef(
            name="floor",
            substrait_uri=SubstraitExtension.ROUNDING,
            substrait_name="floor",
            backend_method="floor",  # TODO: verify backend method name
            category="rounding",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=ArithmeticExpressionProtocol.floor,  # TODO: verify exists
            # Rounding to the floor of the value `x`.
...
        ),
        FunctionDef(
            name="round",
            substrait_uri=SubstraitExtension.ROUNDING,
            substrait_name="round",
            backend_method="round",  # TODO: verify backend method name
            category="rounding",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('rounding',),
            protocol_method=ArithmeticExpressionProtocol.round,  # TODO: verify exists
            # Rounding the value `x` to `s` decimal places.
...
        ),
    ]


    # ========================================
    # Rounding_Decimal Functions
    # ========================================

    # Scalar functions (3)
    ROUNDING_DECIMAL_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="ceil",
            substrait_uri=SubstraitExtension.ROUNDING_DECIMAL,
            substrait_name="ceil",
            backend_method="ceil",  # TODO: verify backend method name
            category="rounding_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.ceil,  # TODO: verify exists
            # Rounding to the ceiling of the value `x`.
...
        ),
        FunctionDef(
            name="floor",
            substrait_uri=SubstraitExtension.ROUNDING_DECIMAL,
            substrait_name="floor",
            backend_method="floor",  # TODO: verify backend method name
            category="rounding_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=UnknownProtocol.floor,  # TODO: verify exists
            # Rounding to the floor of the value `x`.
...
        ),
        FunctionDef(
            name="round",
            substrait_uri=SubstraitExtension.ROUNDING_DECIMAL,
            substrait_name="round",
            backend_method="round",  # TODO: verify backend method name
            category="rounding_decimal",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('rounding',),
            protocol_method=UnknownProtocol.round,  # TODO: verify exists
            # Rounding the value `x` to `s` decimal places.
...
        ),
    ]


    # ========================================
    # Set Functions
    # ========================================

    # Scalar functions (1)
    SET_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="index_in",
            substrait_uri=SubstraitExtension.SET,
            substrait_name="index_in",
            backend_method="index_in",  # TODO: verify backend method name
            category="set",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('nan_equality',),
            protocol_method=UnknownProtocol.index_in,  # TODO: verify exists
            # Checks the membership of a value in a list of values
Returns...
        ),
    ]


    # ========================================
    # String Functions
    # ========================================

    # Scalar functions (40)
    STRING_SCALAR_FUNCTIONS = [
        FunctionDef(
            name="concat",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="concat",
            backend_method="concat",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=None,
            options=('null_handling',),
            protocol_method=StringExpressionProtocol.concat,  # TODO: verify exists
            # Concatenate strings.
The `null_handling` option determines w...
        ),
        FunctionDef(
            name="like",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="like",
            backend_method="like",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('case_sensitivity',),
            protocol_method=StringExpressionProtocol.like,  # TODO: verify exists
            # Are two strings like each other.
The `case_sensitivity` opti...
        ),
        FunctionDef(
            name="substring",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="substring",
            backend_method="substring",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=3,
            options=('negative_start',),
            protocol_method=StringExpressionProtocol.substring,  # TODO: verify exists
            # Extract a substring of a specified `length` starting from po...
        ),
        FunctionDef(
            name="regexp_match_substring",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="regexp_match_substring",
            backend_method="regexp_match_substring",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=5,
            options=('case_sensitivity', 'multiline', 'dotall'),
            protocol_method=StringExpressionProtocol.regexp_match_substring,  # TODO: verify exists
            # Extract a substring that matches the given regular expressio...
        ),
        FunctionDef(
            name="regexp_match_substring",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="regexp_match_substring",
            backend_method="regexp_match_substring",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('case_sensitivity', 'multiline', 'dotall'),
            protocol_method=StringExpressionProtocol.regexp_match_substring,  # TODO: verify exists
            # Extract a substring that matches the given regular expressio...
        ),
        FunctionDef(
            name="regexp_match_substring_all",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="regexp_match_substring_all",
            backend_method="regexp_match_substring_all",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=4,
            options=('case_sensitivity', 'multiline', 'dotall'),
            protocol_method=StringExpressionProtocol.regexp_match_substring_all,  # TODO: verify exists
            # Extract all substrings that match the given regular expressi...
        ),
        FunctionDef(
            name="starts_with",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="starts_with",
            backend_method="starts_with",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('case_sensitivity',),
            protocol_method=StringExpressionProtocol.starts_with,  # TODO: verify exists
            # Whether the `input` string starts with the `substring`.
The ...
        ),
        FunctionDef(
            name="ends_with",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="ends_with",
            backend_method="ends_with",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('case_sensitivity',),
            protocol_method=StringExpressionProtocol.ends_with,  # TODO: verify exists
            # Whether `input` string ends with the substring.
The `case_se...
        ),
        FunctionDef(
            name="contains",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="contains",
            backend_method="contains",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('case_sensitivity',),
            protocol_method=StringExpressionProtocol.contains,  # TODO: verify exists
            # Whether the `input` string contains the `substring`.
The `ca...
        ),
        FunctionDef(
            name="strpos",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="strpos",
            backend_method="strpos",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('case_sensitivity',),
            protocol_method=StringExpressionProtocol.strpos,  # TODO: verify exists
            # Return the position of the first occurrence of a string in a...
        ),
        FunctionDef(
            name="regexp_strpos",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="regexp_strpos",
            backend_method="regexp_strpos",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=4,
            options=('case_sensitivity', 'multiline', 'dotall'),
            protocol_method=StringExpressionProtocol.regexp_strpos,  # TODO: verify exists
            # Return the position of an occurrence of the given regular ex...
        ),
        FunctionDef(
            name="count_substring",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="count_substring",
            backend_method="count_substring",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('case_sensitivity',),
            protocol_method=StringExpressionProtocol.count_substring,  # TODO: verify exists
            # Return the number of non-overlapping occurrences of a substr...
        ),
        FunctionDef(
            name="regexp_count_substring",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="regexp_count_substring",
            backend_method="regexp_count_substring",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=3,
            options=('case_sensitivity', 'multiline', 'dotall'),
            protocol_method=StringExpressionProtocol.regexp_count_substring,  # TODO: verify exists
            # Return the number of non-overlapping occurrences of a regula...
        ),
        FunctionDef(
            name="regexp_count_substring",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="regexp_count_substring",
            backend_method="regexp_count_substring",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('case_sensitivity', 'multiline', 'dotall'),
            protocol_method=StringExpressionProtocol.regexp_count_substring,  # TODO: verify exists
            # Return the number of non-overlapping occurrences of a regula...
        ),
        FunctionDef(
            name="replace",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="replace",
            backend_method="replace",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=3,
            options=('case_sensitivity',),
            protocol_method=StringExpressionProtocol.replace,  # TODO: verify exists
            # Replace all occurrences of the substring with the replacemen...
        ),
        FunctionDef(
            name="concat_ws",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="concat_ws",
            backend_method="concat_ws",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=None,
            protocol_method=StringExpressionProtocol.concat_ws,  # TODO: verify exists
            # Concatenate strings together separated by a separator....
        ),
        FunctionDef(
            name="repeat",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="repeat",
            backend_method="repeat",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=StringExpressionProtocol.repeat,  # TODO: verify exists
            # Repeat a string `count` number of times....
        ),
        FunctionDef(
            name="reverse",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="reverse",
            backend_method="reverse",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=StringExpressionProtocol.reverse,  # TODO: verify exists
            # Returns the string in reverse order....
        ),
        FunctionDef(
            name="replace_slice",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="replace_slice",
            backend_method="replace_slice",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=4,
            protocol_method=StringExpressionProtocol.replace_slice,  # TODO: verify exists
            # Replace a slice of the input string.  A specified 'length' o...
        ),
        FunctionDef(
            name="lower",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="lower",
            backend_method="lower",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('char_set',),
            protocol_method=StringExpressionProtocol.lower,  # TODO: verify exists
            # Transform the string to lower case characters. Implementatio...
        ),
        FunctionDef(
            name="upper",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="upper",
            backend_method="upper",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('char_set',),
            protocol_method=StringExpressionProtocol.upper,  # TODO: verify exists
            # Transform the string to upper case characters. Implementatio...
        ),
        FunctionDef(
            name="swapcase",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="swapcase",
            backend_method="swapcase",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('char_set',),
            protocol_method=StringExpressionProtocol.swapcase,  # TODO: verify exists
            # Transform the string's lowercase characters to uppercase and...
        ),
        FunctionDef(
            name="capitalize",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="capitalize",
            backend_method="capitalize",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('char_set',),
            protocol_method=StringExpressionProtocol.capitalize,  # TODO: verify exists
            # Capitalize the first character of the input string. Implemen...
        ),
        FunctionDef(
            name="title",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="title",
            backend_method="title",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('char_set',),
            protocol_method=StringExpressionProtocol.title,  # TODO: verify exists
            # Converts the input string into titlecase. Capitalize the fir...
        ),
        FunctionDef(
            name="initcap",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="initcap",
            backend_method="initcap",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            options=('char_set',),
            protocol_method=StringExpressionProtocol.initcap,  # TODO: verify exists
            # Capitalizes the first character of each word in the input st...
        ),
        FunctionDef(
            name="char_length",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="char_length",
            backend_method="char_length",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=StringExpressionProtocol.char_length,  # TODO: verify exists
            # Return the number of characters in the input string.  The le...
        ),
        FunctionDef(
            name="bit_length",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="bit_length",
            backend_method="bit_length",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=StringExpressionProtocol.bit_length,  # TODO: verify exists
            # Return the number of bits in the input string....
        ),
        FunctionDef(
            name="octet_length",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="octet_length",
            backend_method="octet_length",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=1,
            protocol_method=StringExpressionProtocol.octet_length,  # TODO: verify exists
            # Return the number of bytes in the input string....
        ),
        FunctionDef(
            name="regexp_replace",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="regexp_replace",
            backend_method="regexp_replace",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=5,
            options=('case_sensitivity', 'multiline', 'dotall'),
            protocol_method=StringExpressionProtocol.regexp_replace,  # TODO: verify exists
            # Search a string for a substring that matches a given regular...
        ),
        FunctionDef(
            name="regexp_replace",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="regexp_replace",
            backend_method="regexp_replace",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=3,
            options=('case_sensitivity', 'multiline', 'dotall'),
            protocol_method=StringExpressionProtocol.regexp_replace,  # TODO: verify exists
            # Search a string for a substring that matches a given regular...
        ),
        FunctionDef(
            name="ltrim",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="ltrim",
            backend_method="ltrim",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=StringExpressionProtocol.ltrim,  # TODO: verify exists
            # Remove any occurrence of the characters from the left side o...
        ),
        FunctionDef(
            name="rtrim",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="rtrim",
            backend_method="rtrim",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=StringExpressionProtocol.rtrim,  # TODO: verify exists
            # Remove any occurrence of the characters from the right side ...
        ),
        FunctionDef(
            name="trim",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="trim",
            backend_method="trim",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=StringExpressionProtocol.trim,  # TODO: verify exists
            # Remove any occurrence of the characters from the left and ri...
        ),
        FunctionDef(
            name="lpad",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="lpad",
            backend_method="lpad",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=3,
            protocol_method=StringExpressionProtocol.lpad,  # TODO: verify exists
            # Left-pad the input string with the string of 'characters' un...
        ),
        FunctionDef(
            name="rpad",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="rpad",
            backend_method="rpad",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=3,
            protocol_method=StringExpressionProtocol.rpad,  # TODO: verify exists
            # Right-pad the input string with the string of 'characters' u...
        ),
        FunctionDef(
            name="center",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="center",
            backend_method="center",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=3,
            options=('padding',),
            protocol_method=StringExpressionProtocol.center,  # TODO: verify exists
            # Center the input string by padding the sides with a single `...
        ),
        FunctionDef(
            name="left",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="left",
            backend_method="left",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=StringExpressionProtocol.left,  # TODO: verify exists
            # Extract `count` characters starting from the left of the str...
        ),
        FunctionDef(
            name="right",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="right",
            backend_method="right",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=StringExpressionProtocol.right,  # TODO: verify exists
            # Extract `count` characters starting from the right of the st...
        ),
        FunctionDef(
            name="string_split",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="string_split",
            backend_method="string_split",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=StringExpressionProtocol.string_split,  # TODO: verify exists
            # Split a string into a list of strings, based on a specified ...
        ),
        FunctionDef(
            name="regexp_string_split",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="regexp_string_split",
            backend_method="regexp_string_split",  # TODO: verify backend method name
            category="string",
            function_type="scalar",  # scalar, aggregate, or window
            n_args=2,
            options=('case_sensitivity', 'multiline', 'dotall'),
            protocol_method=StringExpressionProtocol.regexp_string_split,  # TODO: verify exists
            # Split a string into a list of strings, based on a regular ex...
        ),
    ]

    # Aggregate functions (1)
    STRING_AGGREGATE_FUNCTIONS = [
        FunctionDef(
            name="string_agg",
            substrait_uri=SubstraitExtension.STRING,
            substrait_name="string_agg",
            backend_method="string_agg",  # TODO: verify backend method name
            category="string",
            function_type="aggregate",  # scalar, aggregate, or window
            n_args=2,
            protocol_method=StringExpressionProtocol.string_agg,  # TODO: verify exists
            # Concatenates a column of string values with a separator....
        ),
    ]

    # ========================================
    # Register All
    # ========================================

    all_functions = (
        AGGREGATE_APPROX_AGGREGATE_FUNCTIONS + AGGREGATE_GENERIC_AGGREGATE_FUNCTIONS + AGGREGATE_DECIMAL_AGGREGATE_FUNCTIONS + ARITHMETIC_SCALAR_FUNCTIONS + ARITHMETIC_AGGREGATE_FUNCTIONS + ARITHMETIC_WINDOW_FUNCTIONS + ARITHMETIC_DECIMAL_SCALAR_FUNCTIONS + ARITHMETIC_DECIMAL_AGGREGATE_FUNCTIONS + BOOLEAN_SCALAR_FUNCTIONS + BOOLEAN_AGGREGATE_FUNCTIONS + COMPARISON_SCALAR_FUNCTIONS + DATETIME_SCALAR_FUNCTIONS + DATETIME_AGGREGATE_FUNCTIONS + GEOMETRY_SCALAR_FUNCTIONS + LOGARITHMIC_SCALAR_FUNCTIONS + ROUNDING_SCALAR_FUNCTIONS + ROUNDING_DECIMAL_SCALAR_FUNCTIONS + SET_SCALAR_FUNCTIONS + STRING_SCALAR_FUNCTIONS + STRING_AGGREGATE_FUNCTIONS
    )

    for func in all_functions:
        FunctionRegistry.register(func)
