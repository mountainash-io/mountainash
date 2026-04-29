"""Function definitions for all supported operations.

This module registers all function definitions with the FunctionRegistry.
Each function maps:
- Internal name (used in ScalarFunctionNode)
- Substrait extension URI and function name (for serialization)
- Backend method name (for compilation)
- Protocol class and method name (for type introspection)

Functions are organized by category for clarity.
"""
from __future__ import annotations

from .registry import ExpressionFunctionRegistry as FunctionRegistry, ExpressionFunctionDef

from ..function_keys.enums import (

    SubstraitExtension,
    MountainashExtension,

    FKEY_SUBSTRAIT_CONDITIONAL,
    FKEY_SUBSTRAIT_CAST,
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
    FKEY_SUBSTRAIT_SCALAR_COMPARISON,
    FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC,
    FKEY_SUBSTRAIT_SCALAR_ROUNDING,
    FKEY_SUBSTRAIT_SCALAR_SET,
    FKEY_SUBSTRAIT_SCALAR_STRING,
    SUBSTRAIT_ARITHMETIC_WINDOW,
    FKEY_MOUNTAINASH_WINDOW,

    # Mountainash extension enums
    FKEY_MOUNTAINASH_SCALAR_AGGREGATE,
    FKEY_MOUNTAINASH_NAME,
    FKEY_MOUNTAINASH_NULL,
    FKEY_MOUNTAINASH_SCALAR_ARITHMETIC,
    FKEY_MOUNTAINASH_SCALAR_BOOLEAN,
    FKEY_MOUNTAINASH_SCALAR_STRING,
    FKEY_MOUNTAINASH_SCALAR_DATETIME,
    FKEY_MOUNTAINASH_SCALAR_SET,
    FKEY_MOUNTAINASH_SCALAR_STRUCT,
    FKEY_MOUNTAINASH_SCALAR_LIST,
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
)

# Import protocols for type introspection
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (

    SubstraitCastExpressionSystemProtocol,
    SubstraitConditionalExpressionSystemProtocol,
    SubstraitAggregateGenericExpressionSystemProtocol,
    SubstraitAggregateArithmeticExpressionSystemProtocol,   # NEW
    SubstraitAggregateBooleanExpressionSystemProtocol,
    SubstraitScalarArithmeticExpressionSystemProtocol,
    SubstraitScalarBooleanExpressionSystemProtocol,
    SubstraitScalarComparisonExpressionSystemProtocol,
    SubstraitScalarDatetimeExpressionSystemProtocol,
    SubstraitScalarLogarithmicExpressionSystemProtocol,
    SubstraitScalarRoundingExpressionSystemProtocol,
    SubstraitScalarSetExpressionSystemProtocol,
    SubstraitScalarStringExpressionSystemProtocol,
    SubstraitWindowArithmeticExpressionSystemProtocol,
)


# Import Mountainash extension protocols
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (

    MountainashExtensionAggregateExpressionSystemProtocol,
    MountainAshNameExpressionSystemProtocol,
    MountainAshNullExpressionSystemProtocol,
    MountainAshScalarArithmeticExpressionSystemProtocol,
    MountainAshScalarBooleanExpressionSystemProtocol,
    MountainAshScalarStringExpressionSystemProtocol,
    MountainAshScalarDatetimeExpressionSystemProtocol,
    MountainAshScalarSetExpressionSystemProtocol,
    MountainAshScalarStructExpressionSystemProtocol,
    MountainAshScalarListExpressionSystemProtocol,
    MountainAshScalarTernaryExpressionSystemProtocol,
    MountainashWindowExpressionSystemProtocol,
)


def register_all_functions() -> None:
    """Register all function definitions with the registry."""

    # ========================================
    # Core Functions
    # ========================================
    # Note: col and lit are handled specially by FieldReferenceNode and LiteralNode,
    # not ScalarFunctionNode. They don't need registry entries.

    # ========================================
    # Comparison Functions (Substrait standard)
    # ========================================

    SCALAR_COMPARISON_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL, # Needs to become an auto() enum
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="equal",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.equal, #can be ued to derive the backend method
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.NOT_EQUAL,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="not_equal",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.not_equal,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="gt",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.gt,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LT,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="lt",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.lt,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GTE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="gte",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.gte,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="lte",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.lte,
        ),

        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.COALESCE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="coalesce",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.coalesce,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GREATEST,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="greatest",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.greatest,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="least",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.least,
            # protocol_method_function_key="least",
        ),

        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_null",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.is_null,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_NULL,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_not_null",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.is_not_null,
        ),

        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_TRUE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_true",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.is_true,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_TRUE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_not_true",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.is_not_true,
        ),

        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FALSE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_false",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.is_false,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_FALSE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_not_false",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.is_not_false,
        ),

        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FINITE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_finite",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.is_finite,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_INFINITE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_infinite",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.is_infinite,
        ),

        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NAN,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_nan",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.is_nan,
        ),


        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.BETWEEN,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="between",
            options=("closed",),
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.between,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.NULL_IF,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="nullif",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.nullif,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST_SKIP_NULL,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="least_skip_null",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.least_skip_null,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GREATEST_SKIP_NULL,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="greatest_skip_null",
            protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.greatest_skip_null,
        ),
        # Mountainash extension
        # ExpressionFunctionDef(
        #     function_key="is_close",
        #     substrait_uri=SubstraitExtension.MOUNTAINASH,
        #     substrait_name="is_close",
        #     is_extension=True,
        #     options=("precision",),
        #     protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.is_close,
        #     # protocol_method_function_key="is_close",
        # ),
    ]

    # ========================================
    # Boolean Functions (Substrait standard)
    # ========================================

    SCALAR_BOOLEAN_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,
            substrait_name="and",
            protocol_method=SubstraitScalarBooleanExpressionSystemProtocol.and_,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.OR,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,
            substrait_name="or",
            protocol_method=SubstraitScalarBooleanExpressionSystemProtocol.or_,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,
            substrait_name="not",
            protocol_method=SubstraitScalarBooleanExpressionSystemProtocol.not_,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.XOR,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,
            substrait_name="xor",
            protocol_method=SubstraitScalarBooleanExpressionSystemProtocol.xor,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND_NOT,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,
            substrait_name="and_not",
            protocol_method=SubstraitScalarBooleanExpressionSystemProtocol.and_not,
        ),
        # Boolean checks
        # Mountainash extensions
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_BOOLEAN.XOR_PARITY,
            substrait_uri=MountainashExtension.COMPARISON,
            substrait_name="xor_parity",
            protocol_method=MountainAshScalarBooleanExpressionSystemProtocol.xor_parity,
        ),
    ]

    # ========================================
    # Arithmetic Functions (Substrait standard)
    # ========================================

    SCALAR_ARITHMETIC_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="add",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.add,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="subtract",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.subtract,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="multiply",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.multiply,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="divide",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.divide,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="modulus",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.modulus,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="power",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.power,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="negate",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.negate,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="abs",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.abs,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIGN,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="sign",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.sign,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="sqrt",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.sqrt,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="exp",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.exp,
        ),
        # Trigonometric
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="sin",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.sin,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="cos",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.cos,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="tan",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.tan,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="asin",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.asin,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="acos",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.acos,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="atan",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.atan,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="atan2",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.atan2,
        ),
        # Hyperbolic
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="sinh",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.sinh,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="cosh",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.cosh,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="tanh",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.tanh,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="asinh",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.asinh,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="acosh",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.acosh,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="atanh",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.atanh,
        ),
        # Angular conversion
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="radians",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.radians,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="degrees",
            protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.degrees,
        ),
    ]

    # ========================================
    # String Functions (Substrait standard)
    # ========================================

    SCALAR_STRING_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="upper",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.upper,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="lower",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.lower,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="concat",
            options=("separator",),
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.concat,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="substring",
            options=("start", "length"),
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.substring,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TRIM,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="trim",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.trim,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="ltrim",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.ltrim,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="rtrim",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.rtrim,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CHAR_LENGTH,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="char_length",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.char_length,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="replace",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.replace,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SPLIT,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="string_split",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.string_split,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="contains",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.contains,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="starts_with",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.starts_with,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="ends_with",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.ends_with,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="like",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.like,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="regexp_match_substring",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.regexp_match_substring,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="regexp_string_split",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.regexp_string_split,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="regexp_replace",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.regexp_replace,
        ),
        # Case conversion (aspirational)
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SWAPCASE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="swapcase",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.swapcase,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="capitalize",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.capitalize,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TITLE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="title",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.title,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="initcap",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.initcap,
        ),
        # Padding
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="lpad",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.lpad,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RPAD,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="rpad",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.rpad,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="center",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.center,
        ),
        # Extraction
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LEFT,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="left",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.left,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RIGHT,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="right",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.right,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="replace_slice",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.replace_slice,
        ),
        # Search
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="strpos",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.strpos,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="count_substring",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.count_substring,
        ),
        # Length variants
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.BIT_LENGTH,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="bit_length",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.bit_length,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.OCTET_LENGTH,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="octet_length",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.octet_length,
        ),
        # Manipulation
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT_WS,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="concat_ws",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.concat_ws,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="repeat",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.repeat,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REVERSE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="reverse",
            protocol_method=SubstraitScalarStringExpressionSystemProtocol.reverse,
        ),
        # Mountainash string extensions
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS,
            substrait_uri=MountainashExtension.STRING,
            substrait_name="regex_contains",
            protocol_method=MountainAshScalarStringExpressionSystemProtocol.regex_contains,
            options=("pattern",),
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.STRIP_SUFFIX,
            substrait_uri=MountainashExtension.STRING,
            substrait_name="strip_suffix",
            protocol_method=MountainAshScalarStringExpressionSystemProtocol.strip_suffix,
            options=("suffix",),
        ),
    ]

    # ========================================
    # Set Functions (Substrait standard)
    # ========================================

    SCALAR_SET_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_SET.INDEX_IN,
            substrait_uri=SubstraitExtension.SCALAR_SET,
            substrait_name="index_in",
            protocol_method=SubstraitScalarSetExpressionSystemProtocol.index_in,
        ),
        # Mountainash set extensions
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_SET.IS_IN,
            substrait_uri=MountainashExtension.COMPARISON,
            substrait_name="is_in",
            is_extension=True,
            protocol_method=MountainAshScalarSetExpressionSystemProtocol.is_in,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_SET.IS_NOT_IN,
            substrait_uri=MountainashExtension.COMPARISON,
            substrait_name="is_not_in",
            is_extension=True,
            protocol_method=MountainAshScalarSetExpressionSystemProtocol.is_not_in,
        ),
    ]


    # ========================================
    # Temporal Functions (Substrait standard)
    # ========================================

    SCALAR_DATETIME_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
            substrait_uri=SubstraitExtension.SCALAR_DATETIME,
            substrait_name="extract",
            options=("component",),  # component="YEAR"
            protocol_method=SubstraitScalarDatetimeExpressionSystemProtocol.extract,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN,
            substrait_uri=SubstraitExtension.SCALAR_DATETIME,
            substrait_name="extract",
            protocol_method=SubstraitScalarDatetimeExpressionSystemProtocol.extract_boolean,
        ),
    ]

    # ========================================
    # Rounding Functions (Substrait standard)
    # ========================================

    SCALAR_ROUNDING_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ROUNDING.CEIL,
            substrait_uri=SubstraitExtension.SCALAR_ROUNDING,
            substrait_name="ceil",
            protocol_method=SubstraitScalarRoundingExpressionSystemProtocol.ceil,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ROUNDING.FLOOR,
            substrait_uri=SubstraitExtension.SCALAR_ROUNDING,
            substrait_name="floor",
            protocol_method=SubstraitScalarRoundingExpressionSystemProtocol.floor,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
            substrait_uri=SubstraitExtension.SCALAR_ROUNDING,
            substrait_name="round",
            options=("s", "rounding"),
            protocol_method=SubstraitScalarRoundingExpressionSystemProtocol.round,
        ),
    ]

    # ========================================
    # Logarithmic Functions (Substrait standard)
    # ========================================

    SCALAR_LOGARITHMIC_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG,
            substrait_uri=SubstraitExtension.SCALAR_LOGARITHMIC,
            substrait_name="ln",
            protocol_method=SubstraitScalarLogarithmicExpressionSystemProtocol.ln,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG10,
            substrait_uri=SubstraitExtension.SCALAR_LOGARITHMIC,
            substrait_name="log10",
            protocol_method=SubstraitScalarLogarithmicExpressionSystemProtocol.log10,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG2,
            substrait_uri=SubstraitExtension.SCALAR_LOGARITHMIC,
            substrait_name="log2",
            protocol_method=SubstraitScalarLogarithmicExpressionSystemProtocol.log2,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOGB,
            substrait_uri=SubstraitExtension.SCALAR_LOGARITHMIC,
            substrait_name="logb",
            protocol_method=SubstraitScalarLogarithmicExpressionSystemProtocol.logb,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG1P,
            substrait_uri=SubstraitExtension.SCALAR_LOGARITHMIC,
            substrait_name="log1p",
            protocol_method=SubstraitScalarLogarithmicExpressionSystemProtocol.log1p,
        ),
    ]

    # ========================================
    # Aggregate Functions (Substrait standard)
    # ========================================

    SCALAR_AGGREGATE_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="count",
            options=("overflow",),
            protocol_method=SubstraitAggregateGenericExpressionSystemProtocol.count,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="count",   # ← SAME Substrait function as COUNT above;
                                      #   distinguished by arity (this is the 0-arg impl)
            options=("overflow",),
            protocol_method=SubstraitAggregateGenericExpressionSystemProtocol.count_records,
        ),
        # --- generic ---
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="any_value",
            options=("ignore_nulls",),
            protocol_method=SubstraitAggregateGenericExpressionSystemProtocol.any_value,
        ),
        # --- arithmetic, single-arg ---
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="sum",
            options=("overflow",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.sum,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.AVG,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="avg",
            options=("overflow",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.avg,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MIN,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="min",
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.min,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MAX,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="max",
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.max,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.PRODUCT,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="product",
            options=("overflow",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.product,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.STD_DEV,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="std_dev",
            options=("rounding", "distribution"),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.std_dev,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.VARIANCE,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="variance",
            options=("rounding", "distribution"),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.variance,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="mode",
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.mode,
        ),
        # --- arithmetic, multi-arg (free functions only) ---
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="corr",
            options=("rounding",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.corr,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="median",
            options=("rounding",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.median,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="quantile",
            options=("rounding",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.quantile,
        ),
        # --- boolean ---
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.BOOL_AND,
            substrait_uri="https://github.com/substrait-io/substrait/blob/main/extensions/functions_boolean.yaml",
            substrait_name="bool_and",
            protocol_method=SubstraitAggregateBooleanExpressionSystemProtocol.bool_and,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.BOOL_OR,
            substrait_uri="https://github.com/substrait-io/substrait/blob/main/extensions/functions_boolean.yaml",
            substrait_name="bool_or",
            protocol_method=SubstraitAggregateBooleanExpressionSystemProtocol.bool_or,
        ),
    ]

    # ========================================
    # Cast Functions (Substrait standard)
    # ========================================

    CAST_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_CAST.CAST,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,  # Cast uses comparison extension
            substrait_name="cast",
            options=("dtype",),
            protocol_method=SubstraitCastExpressionSystemProtocol.cast,
        ),
    ]

    # ========================================
    # Conditional Functions (Substrait standard)
    # ========================================

    CONDITIONAL_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,  # Conditional uses boolean extension
            substrait_name="if_then",
            protocol_method=SubstraitConditionalExpressionSystemProtocol.if_then_else,
        ),
    ]

        # # Extraction functions
        # ExpressionFunctionDef(
        #     function_key="extract_year",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="extract",
        #     options=("component",),  # component="YEAR"
        #     protocol_method=TemporalExpressionProtocol.dt_year,
        # ),
        # ExpressionFunctionDef(
        #     function_key="extract_month",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="extract",
        #     protocol_method=TemporalExpressionProtocol.dt_month,
        # ),
        # ExpressionFunctionDef(
        #     function_key="extract_day",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="extract",
        #     protocol_method=TemporalExpressionProtocol.dt_day,
        # ),
        # ExpressionFunctionDef(
        #     function_key="extract_hour",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="extract",
        #     protocol_method=TemporalExpressionProtocol.dt_hour,
        # ),
        # ExpressionFunctionDef(
        #     function_key="extract_minute",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="extract",
        #     protocol_method=TemporalExpressionProtocol.dt_minute,
        # ),
        # ExpressionFunctionDef(
        #     function_key="extract_second",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="extract",
        #     protocol_method=TemporalExpressionProtocol.dt_second,
        # ),
        # ExpressionFunctionDef(
        #     function_key="extract_weekday",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="extract",
        #     protocol_method=TemporalExpressionProtocol.dt_weekday,
        # ),
        # ExpressionFunctionDef(
        #     function_key="extract_week",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="extract",
        #     protocol_method=TemporalExpressionProtocol.dt_week,
        # ),
        # ExpressionFunctionDef(
        #     function_key="extract_quarter",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="extract",
        #     protocol_method=TemporalExpressionProtocol.dt_quarter,
        # ),
        # # Addition functions
        # ExpressionFunctionDef(
        #     function_key="add_days",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="add",
        #     protocol_method=TemporalExpressionProtocol.dt_add_days,
        # ),
        # ExpressionFunctionDef(
        #     function_key="add_months",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="add",
        #     protocol_method=TemporalExpressionProtocol.dt_add_months,
        # ),
        # ExpressionFunctionDef(
        #     function_key="add_years",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="add",
        #     protocol_method=TemporalExpressionProtocol.dt_add_years,
        # ),
        # ExpressionFunctionDef(
        #     function_key="add_hours",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="add",
        #     protocol_method=TemporalExpressionProtocol.dt_add_hours,
        # ),
        # ExpressionFunctionDef(
        #     function_key="add_minutes",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="add",
        #     protocol_method=TemporalExpressionProtocol.dt_add_minutes,
        # ),
        # ExpressionFunctionDef(
        #     function_key="add_seconds",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="add",
        #     protocol_method=TemporalExpressionProtocol.dt_add_seconds,
        # ),
        # # Difference functions
        # ExpressionFunctionDef(
        #     function_key="diff_years",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="subtract",
        #     protocol_method=TemporalExpressionProtocol.dt_diff_years,
        # ),
        # ExpressionFunctionDef(
        #     function_key="diff_months",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="subtract",
        #     protocol_method=TemporalExpressionProtocol.dt_diff_months,
        # ),
        # ExpressionFunctionDef(
        #     function_key="diff_days",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="subtract",
        #     protocol_method=TemporalExpressionProtocol.dt_diff_days,
        # ),
        # ExpressionFunctionDef(
        #     function_key="diff_hours",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="subtract",
        #     protocol_method=TemporalExpressionProtocol.dt_diff_hours,
        # ),
        # ExpressionFunctionDef(
        #     function_key="diff_minutes",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="subtract",
        #     protocol_method=TemporalExpressionProtocol.dt_diff_minutes,
        # ),
        # ExpressionFunctionDef(
        #     function_key="diff_seconds",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="subtract",
        #     protocol_method=TemporalExpressionProtocol.dt_diff_seconds,
        # ),
        # ExpressionFunctionDef(
        #     function_key="diff_milliseconds",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="subtract",
        #     protocol_method=TemporalExpressionProtocol.dt_diff_milliseconds,
        # ),
        # # Manipulation functions
        # ExpressionFunctionDef(
        #     function_key="truncate",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="round_temporal",  # Substrait uses round
        #     options=("unit",),
        #     protocol_method=TemporalExpressionProtocol.dt_truncate,
        # ),
        # ExpressionFunctionDef(
        #     function_key="offset_by",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="add",
        #     options=("offset",),
        #     protocol_method=TemporalExpressionProtocol.dt_offset_by,
        # ),
        # # Snapshot functions
        # ExpressionFunctionDef(
        #     function_key="today",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="local_timestamp",  # Approximate
        #     protocol_method=TemporalExpressionProtocol.dt_today,
        # ),
        # ExpressionFunctionDef(
        #     function_key="now",
        #     substrait_uri=SubstraitExtension.DATETIME,
        #     substrait_name="local_timestamp",
        #     protocol_method=TemporalExpressionProtocol.dt_now,
        # ),
    # ]

    # ========================================
    # Null Functions (Substrait comparison)
    # ========================================

    # NULL_FUNCTIONS = [
    #     ExpressionFunctionDef(
    #         function_key="fill_null",
    #         substrait_uri=SubstraitExtension.COMPARISON,
    #         substrait_name="coalesce",  # fill_null(a, b) = coalesce(a, b)
    #         protocol_method=NullExpressionProtocol.fill_null,
    #     ),
    #     ExpressionFunctionDef(
    #         function_key="null_if",
    #         substrait_uri=SubstraitExtension.COMPARISON,
    #         substrait_name="nullif",
    #         protocol_method=NullExpressionProtocol.null_if,
    #     ),
    #     ExpressionFunctionDef(
    #         function_key="always_null",
    #         substrait_uri=SubstraitExtension.COMPARISON,
    #         substrait_name="null",  # Literal null
    #         protocol_method=NullExpressionProtocol.always_null,
    #     ),
    # ]

    # ========================================
    # Name Functions (Mountainash extension)
    # ========================================

    # NAME_FUNCTIONS = [
    #     ExpressionFunctionDef(
    #         function_key="alias",
    #         substrait_uri=SubstraitExtension.MOUNTAINASH,
    #         substrait_name="alias",
    #         is_extension=True,
    #         options=("name",),
    #         protocol_method=NameExpressionProtocol.alias,
    #     ),
        # ExpressionFunctionDef(
        #     function_key="prefix",
        #     substrait_uri=SubstraitExtension.MOUNTAINASH,
        #     substrait_name="prefix",
        #     is_extension=True,
        #     options=("prefix",),
        #     protocol_method=NameExpressionProtocol.prefix,
        # ),
        # ExpressionFunctionDef(
        #     function_key="suffix",
        #     substrait_uri=SubstraitExtension.MOUNTAINASH,
        #     substrait_name="suffix",
        #     is_extension=True,
        #     options=("suffix",),
        #     protocol_method=NameExpressionProtocol.suffix,
        # ),
        # ExpressionFunctionDef(
        #     function_key="name_to_upper",
        #     substrait_uri=SubstraitExtension.MOUNTAINASH,
        #     substrait_name="name_to_upper",
        #     is_extension=True,
        #     protocol_method=NameExpressionProtocol.to_upper,
        # ),
        # ExpressionFunctionDef(
        #     function_key="name_to_lower",
        #     substrait_uri=SubstraitExtension.MOUNTAINASH,
        #     substrait_name="name_to_lower",
        #     is_extension=True,
        #     protocol_method=NameExpressionProtocol.to_lower,
        # ),
    # ]

    # ========================================
    # Type Functions (Substrait comparison)
    # ========================================

    # TYPE_FUNCTIONS = [
    #     # Cast is handled specially by CastNode, but we register for completeness
    #     ExpressionFunctionDef(
    #         function_key="cast",
    #         substrait_uri=SubstraitExtension.COMPARISON,
    #         substrait_name="cast",
    #         options=("dtype",),
    #         protocol_method=TypeExpressionProtocol.cast,
    #     ),
    # ]

    # # ========================================
    # # Boolean Constants (Substrait boolean)
    # # ========================================

    # CONSTANT_FUNCTIONS = [
    #     ExpressionFunctionDef(
    #         function_key="always_true",
    #         substrait_uri=SubstraitExtension.BOOLEAN,
    #         substrait_name="true",  # Literal true
    #         protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.always_true,
    #     ),
    #     ExpressionFunctionDef(
    #         function_key="always_false",
    #         substrait_uri=SubstraitExtension.BOOLEAN,
    #         substrait_name="false",  # Literal false
    #         protocol_method=SubstraitScalarComparisonExpressionSystemProtocol.always_false,
    #     ),
    # ]

    # ========================================
    # Ternary Functions (Mountainash extension)
    # ========================================

    TERNARY_FUNCTIONS = [
        # Ternary comparisons (return -1/0/1)
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_EQ,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_equal",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_eq,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_NE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_not_equal",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_ne,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GT,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_gt",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_gt,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_LT,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_lt",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_lt,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_gte",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_ge,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_LE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_lte",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_le,
        ),
        # Ternary collection
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_IN,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_in",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_is_in,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_NOT_IN,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_not_in",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_is_not_in,
        ),
        # Ternary logical
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_AND,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_and",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_and,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_OR,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_or",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_or,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_NOT,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_not",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_not,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_XOR,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_xor",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_xor,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_XOR_PARITY,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_xor_parity",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.t_xor_parity,
        ),
        # Ternary to boolean conversions
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_TRUE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_true",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.is_true_ternary,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_FALSE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_false",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.is_false_ternary,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_UNKNOWN,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_unknown",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.is_unknown,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_KNOWN,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_known",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.is_known,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_TRUE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_maybe_true",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.maybe_true,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_FALSE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_maybe_false",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.maybe_false,
        ),
        # Boolean to ternary conversion
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.TO_TERNARY,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="to_ternary",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.to_ternary,
        ),
        # Ternary constants
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_TRUE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="always_true",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.always_true_ternary,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_FALSE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="always_false",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.always_false_ternary,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_UNKNOWN,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="always_unknown",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.always_unknown,
        ),
        # Utility function for collecting values in t_is_in/t_is_not_in
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.LIST,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="list",
            is_extension=True,
            protocol_method=MountainAshScalarTernaryExpressionSystemProtocol.collect_values,
        ),
    ]

    # ========================================
    # Mountainash Arithmetic Extensions
    # ========================================

    MOUNTAINASH_ARITHMETIC_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_ARITHMETIC.FLOOR_DIVIDE,
            substrait_uri=MountainashExtension.ARITHMETIC,
            substrait_name="floor_divide",
            is_extension=True,
            protocol_method=MountainAshScalarArithmeticExpressionSystemProtocol.floor_divide,
        ),
    ]

    # ========================================
    # Mountainash Null Extensions
    # ========================================

    MOUNTAINASH_NULL_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_NULL.FILL_NULL,
            substrait_uri=MountainashExtension.NULL,
            substrait_name="fill_null",
            is_extension=True,
            protocol_method=MountainAshNullExpressionSystemProtocol.fill_null,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_NULL.NULL_IF,
            substrait_uri=MountainashExtension.NULL,
            substrait_name="null_if",
            is_extension=True,
            protocol_method=MountainAshNullExpressionSystemProtocol.null_if,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_NULL.FILL_NAN,
            substrait_uri=MountainashExtension.NULL,
            substrait_name="fill_nan",
            is_extension=True,
            protocol_method=MountainAshNullExpressionSystemProtocol.fill_nan,
        ),
    ]

    # ========================================
    # Mountainash Name Extensions
    # ========================================

    MOUNTAINASH_NAME_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
            substrait_uri=MountainashExtension.NAME,
            substrait_name="alias",
            is_extension=True,
            protocol_method=MountainAshNameExpressionSystemProtocol.alias,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_NAME.PREFIX,
            substrait_uri=MountainashExtension.NAME,
            substrait_name="prefix",
            is_extension=True,
            protocol_method=MountainAshNameExpressionSystemProtocol.prefix,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_NAME.SUFFIX,
            substrait_uri=MountainashExtension.NAME,
            substrait_name="suffix",
            is_extension=True,
            protocol_method=MountainAshNameExpressionSystemProtocol.suffix,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_NAME.NAME_TO_UPPER,
            substrait_uri=MountainashExtension.NAME,
            substrait_name="name_to_upper",
            is_extension=True,
            protocol_method=MountainAshNameExpressionSystemProtocol.name_to_upper,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_NAME.NAME_TO_LOWER,
            substrait_uri=MountainashExtension.NAME,
            substrait_name="name_to_lower",
            is_extension=True,
            protocol_method=MountainAshNameExpressionSystemProtocol.name_to_lower,
        ),
    ]

    # ========================================
    # Mountainash Datetime Extensions
    # ========================================

    MOUNTAINASH_DATETIME_FUNCTIONS = [
        # Extraction - Basic
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_YEAR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_year",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.year,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MONTH,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_month",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.month,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_DAY,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_day",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.day,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_HOUR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_hour",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.hour,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MINUTE,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_minute",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.minute,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_SECOND,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_second",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.second,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MILLISECOND,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_millisecond",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.millisecond,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MICROSECOND,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_microsecond",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.microsecond,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_NANOSECOND,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_nanosecond",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.nanosecond,
        ),
        # Extraction - Calendar
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_QUARTER,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_quarter",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.quarter,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_DAY_OF_YEAR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_day_of_year",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.day_of_year,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEKDAY,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_weekday",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.day_of_week,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEK,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_week",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.week_of_year,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_ISO_YEAR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_iso_year",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.iso_year,
        ),
        # Extraction - Special
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_UNIX_TIME,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_unix_time",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.unix_timestamp,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_TIMEZONE_OFFSET,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_timezone_offset",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.timezone_offset,
        ),
        # Boolean Extraction
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_LEAP_YEAR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="is_leap_year",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.is_leap_year,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="is_dst",
            options=("timezone",),
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.is_dst,
        ),
        # Addition
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_years",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.add_years,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_months",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.add_months,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_days",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.add_days,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_HOURS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_hours",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.add_hours,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MINUTES,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_minutes",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.add_minutes,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_SECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_seconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.add_seconds,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MILLISECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_milliseconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.add_milliseconds,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MICROSECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_microseconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.add_microseconds,
        ),
        # Difference
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_YEARS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_years",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.diff_years,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_MONTHS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_months",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.diff_months,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_DAYS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_days",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.diff_days,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_HOURS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_hours",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.diff_hours,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_MINUTES,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_minutes",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.diff_minutes,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_SECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_seconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.diff_seconds,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_MILLISECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_milliseconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.diff_milliseconds,
        ),
        # Truncation / Rounding
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="truncate",
            options=("unit",),
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.truncate,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="round",
            options=("unit",),
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.round,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="ceil",
            options=("unit",),
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.ceil,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="floor",
            options=("unit",),
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.floor,
        ),
        # Timezone
        # TODO: to_timezone not yet defined in any protocol
        # ExpressionFunctionDef(
        #     function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TO_TIMEZONE,
        #     substrait_uri=MountainashExtension.DATETIME,
        #     substrait_name="to_timezone",
        #     options=("timezone",),
        #     is_extension=True,
        #     protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.to_timezone,
        # ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ASSUME_TIMEZONE,
            substrait_uri=SubstraitExtension.SCALAR_DATETIME,
            substrait_name="assume_timezone",
            options=("timezone",),
            protocol_method=SubstraitScalarDatetimeExpressionSystemProtocol.assume_timezone,
        ),
        # Formatting
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.STRFTIME,
            substrait_uri=SubstraitExtension.SCALAR_DATETIME,
            substrait_name="strftime",
            options=("format",),
            protocol_method=SubstraitScalarDatetimeExpressionSystemProtocol.strftime,
        ),
        # Flexible Duration Offset
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="offset_by",
            options=("offset",),
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.offset_by,
        ),
        # Snapshot
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="today",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.today,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.NOW,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="now",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.now,
        ),
        # Component extraction
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DATE,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="date",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.date,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="time",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.time,
        ),
        # Calendar helpers
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="month_start",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.month_start,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="month_end",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.month_end,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="days_in_month",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.days_in_month,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_SECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="total_seconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.total_seconds,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MINUTES,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="total_minutes",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.total_minutes,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MILLISECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="total_milliseconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.total_milliseconds,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MICROSECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="total_microseconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.total_microseconds,
        ),
    ]

    # ========================================
    # Window Functions (Substrait standard)
    # ========================================

    WINDOW_ARITHMETIC_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="row_number",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.row_number,
        ),
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="rank",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.rank,
        ),
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="dense_rank",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.dense_rank,
        ),
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="percent_rank",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.percent_rank,
        ),
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="cume_dist",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.cume_dist,
        ),
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.NTILE,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="ntile",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.ntile,
        ),
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="first_value",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.first_value,
        ),
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="last_value",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.last_value,
        ),
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="nth_value",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.nth_value,
        ),
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.LEAD,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="lead",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.lead,
        ),
        ExpressionFunctionDef(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.LAG,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="lag",
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.lag,
        ),
    ]

    # ========================================
    # Window Functions (Mountainash extension)
    # ========================================

    MOUNTAINASH_WINDOW_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.rank,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_WINDOW.RANK_MAX,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.rank,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_WINDOW.DIFF,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=MountainashWindowExpressionSystemProtocol.diff,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_WINDOW.CUM_SUM,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=MountainashWindowExpressionSystemProtocol.cum_sum,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_WINDOW.CUM_MAX,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=MountainashWindowExpressionSystemProtocol.cum_max,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_WINDOW.CUM_MIN,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=MountainashWindowExpressionSystemProtocol.cum_min,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_WINDOW.CUM_COUNT,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=MountainashWindowExpressionSystemProtocol.cum_count,
        ),
    ]

    # ========================================
    # Mountainash Struct Extensions
    # ========================================

    MOUNTAINASH_STRUCT_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD,
            substrait_uri=None,
            substrait_name=None,
            is_extension=True,
            options=("field_name",),
            protocol_method=MountainAshScalarStructExpressionSystemProtocol.struct_field,
        ),
    ]

    # ========================================
    # Mountainash List Extensions
    # ========================================

    MOUNTAINASH_LIST_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SUM,
            substrait_uri=None, substrait_name=None, is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_sum,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MIN,
            substrait_uri=None, substrait_name=None, is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_min,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MAX,
            substrait_uri=None, substrait_name=None, is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_max,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MEAN,
            substrait_uri=None, substrait_name=None, is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_mean,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.LEN,
            substrait_uri=None, substrait_name=None, is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_len,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS,
            substrait_uri=None, substrait_name=None, is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_contains,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SORT,
            substrait_uri=None, substrait_name=None, is_extension=True,
            options=("descending",),
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_sort,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.UNIQUE,
            substrait_uri=None, substrait_name=None, is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_unique,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.EXPLODE,
            substrait_uri=None, substrait_name=None, is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_explode,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.JOIN,
            substrait_uri=None, substrait_name=None, is_extension=True,
            options=("separator",),
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_join,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.GET,
            substrait_uri=None, substrait_name=None, is_extension=True,
            options=("index",),
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_get,
        ),
    ]

    # ========================================
    # Mountainash Aggregate Extensions
    # ========================================

    MOUNTAINASH_AGGREGATE_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_AGGREGATE.COUNT_DISTINCT,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=MountainashExtensionAggregateExpressionSystemProtocol.n_unique,
        ),
    ]

    # ========================================
    # Register All Functions
    # ========================================

    all_functions = (
        SCALAR_COMPARISON_FUNCTIONS
        + SCALAR_BOOLEAN_FUNCTIONS
        + SCALAR_ARITHMETIC_FUNCTIONS
        + SCALAR_STRING_FUNCTIONS
        + SCALAR_DATETIME_FUNCTIONS
        + SCALAR_SET_FUNCTIONS
        + SCALAR_ROUNDING_FUNCTIONS
        + SCALAR_LOGARITHMIC_FUNCTIONS
        + SCALAR_AGGREGATE_FUNCTIONS
        + WINDOW_ARITHMETIC_FUNCTIONS  # Substrait window functions
        + MOUNTAINASH_WINDOW_FUNCTIONS  # Mountainash extension window functions
        + CAST_FUNCTIONS
        + CONDITIONAL_FUNCTIONS
        # + NULL_FUNCTIONS
        # + NAME_FUNCTIONS
        # + TYPE_FUNCTIONS
        # + CONSTANT_FUNCTIONS
        + TERNARY_FUNCTIONS  # Mountainash extension
        + MOUNTAINASH_ARITHMETIC_FUNCTIONS  # Mountainash extension
        + MOUNTAINASH_DATETIME_FUNCTIONS  # Mountainash extension
        + MOUNTAINASH_NULL_FUNCTIONS  # Mountainash extension
        + MOUNTAINASH_NAME_FUNCTIONS  # Mountainash extension
        + MOUNTAINASH_STRUCT_FUNCTIONS  # Mountainash extension
        + MOUNTAINASH_LIST_FUNCTIONS  # Mountainash extension
        + MOUNTAINASH_AGGREGATE_FUNCTIONS  # Mountainash aggregate extensions
    )

    for func in all_functions:
        FunctionRegistry.register(func)
