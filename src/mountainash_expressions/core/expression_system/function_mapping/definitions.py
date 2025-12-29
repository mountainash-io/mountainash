"""Function definitions for all supported operations.

This module registers all function definitions with the FunctionRegistry.
Each function maps:
- Internal name (used in ScalarFunctionNode)
- Substrait extension URI and function name (for serialization)
- Backend method name (for compilation)
- Protocol class and method name (for type introspection)

Functions are organized by category for clarity.
"""

from mountainash_expressions.core.expression_protocols.substrait.prtcl_scalar_boolean import ScalarBooleanExpressionProtocol
from .registry import ExpressionFunctionRegistry as FunctionRegistry, ExpressionFunctionDef

from ..function_keys.enums import (

    SubstraitExtension,
    MountainashExtension,

    KEY_CONDITIONAL,
    KEY_CAST,
    KEY_FIELD_REFERENCE,
    KEY_LITERAL,

    KEY_SCALAR_ARITHMETIC,
    KEY_SCALAR_COMPARISON,
    KEY_SCALAR_BOOLEAN,
    KEY_SCALAR_DATETIME,
    KEY_SCALAR_AGGREGATE,
    KEY_SCALAR_LOGARITHMIC,
    KEY_SCALAR_ROUNDING,
    KEY_SCALAR_SET,
    KEY_SCALAR_STRING,

    # Mountainash extension enums
    MOUNTAINASH_ARITHMETIC,
    MOUNTAINASH_COMPARISON,
    MOUNTAINASH_DATETIME,
    MOUNTAINASH_NAME,
    MOUNTAINASH_NULL,
    MOUNTAINASH_TERNARY,
)

# Import protocols for type introspection
from ...expression_protocols.substrait import (
    CastExpressionProtocol,
    ConditionalExpressionProtocol,
    FieldReferenceExpressionProtocol,
    LiteralExpressionProtocol,
    ScalarAggregateExpressionProtocol,
    ScalarArithmeticExpressionProtocol,
    ScalarComparisonExpressionProtocol,
    ScalarDatetimeExpressionProtocol,
    ScalarLogarithmicExpressionProtocol,
    ScalarRoundingExpressionProtocol,
    ScalarSetExpressionProtocol,
    ScalarStringExpressionProtocol,
)

# Import Mountainash extension protocols
from ...expression_protocols.mountainash_extensions import (
    MountainashArithmeticExpressionProtocol,
    MountainashBooleanExpressionProtocol,
    MountainashDatetimeExpressionProtocol,
    MountainashNameExpressionProtocol,
    MountainashNullExpressionProtocol,
    TernaryExpressionProtocol,
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
            function_key=KEY_SCALAR_COMPARISON.EQUAL, # Needs to become an auto() enum
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="equal",
            protocol_method=ScalarComparisonExpressionProtocol.equal, #can be ued to derive the backend method
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.NOT_EQUAL,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="not_equal",
            protocol_method=ScalarComparisonExpressionProtocol.not_equal,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.GT,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="gt",
            protocol_method=ScalarComparisonExpressionProtocol.gt,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.LT,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="lt",
            protocol_method=ScalarComparisonExpressionProtocol.lt,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.GTE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="gte",
            protocol_method=ScalarComparisonExpressionProtocol.gte,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.LTE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="lte",
            protocol_method=ScalarComparisonExpressionProtocol.lte,
        ),

        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.COALESCE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="coalesce",
            protocol_method=ScalarComparisonExpressionProtocol.coalesce,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.GREATEST,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="greatest",
            protocol_method=ScalarComparisonExpressionProtocol.greatest,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.LEAST,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="least",
            protocol_method=ScalarComparisonExpressionProtocol.least,
            # protocol_method_function_key="least",
        ),

        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.IS_NULL,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_null",
            protocol_method=ScalarComparisonExpressionProtocol.is_null,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.IS_NOT_NULL,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_not_null",
            protocol_method=ScalarComparisonExpressionProtocol.is_not_null,
        ),

        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.IS_TRUE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_true",
            protocol_method=ScalarComparisonExpressionProtocol.is_true,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.IS_NOT_TRUE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_not_true",
            protocol_method=ScalarComparisonExpressionProtocol.is_not_true,
        ),

        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.IS_FALSE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_false",
            protocol_method=ScalarComparisonExpressionProtocol.is_false,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.IS_NOT_FALSE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_not_false",
            protocol_method=ScalarComparisonExpressionProtocol.is_not_false,
        ),

        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.IS_FINITE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_finite",
            protocol_method=ScalarComparisonExpressionProtocol.is_finite,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.IS_INFINITE,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_infinite",
            protocol_method=ScalarComparisonExpressionProtocol.is_infinite,
        ),

        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.IS_NAN,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="is_nan",
            protocol_method=ScalarComparisonExpressionProtocol.is_nan,
        ),


        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.BETWEEN,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="between",
            options=("closed",),
            protocol_method=ScalarComparisonExpressionProtocol.between,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.NULL_IF,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="nullif",
            protocol_method=ScalarComparisonExpressionProtocol.nullif,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.LEAST_SKIP_NULL,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="least_skip_null",
            protocol_method=ScalarComparisonExpressionProtocol.least_skip_null,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_COMPARISON.GREATEST_SKIP_NULL,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,
            substrait_name="greatest_skip_null",
            protocol_method=ScalarComparisonExpressionProtocol.greatest_skip_null,
        ),
        # Mountainash extension
        # ExpressionFunctionDef(
        #     function_key="is_close",
        #     substrait_uri=SubstraitExtension.MOUNTAINASH,
        #     substrait_name="is_close",
        #     is_extension=True,
        #     options=("precision",),
        #     protocol_method=ScalarComparisonExpressionProtocol.is_close,
        #     # protocol_method_function_key="is_close",
        # ),
    ]

    # ========================================
    # Boolean Functions (Substrait standard)
    # ========================================

    SCALAR_BOOLEAN_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_BOOLEAN.AND,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,
            substrait_name="and",
            protocol_method=ScalarBooleanExpressionProtocol.and_,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_BOOLEAN.OR,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,
            substrait_name="or",
            protocol_method=ScalarBooleanExpressionProtocol.or_,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_BOOLEAN.NOT,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,
            substrait_name="not",
            protocol_method=ScalarBooleanExpressionProtocol.not_,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_BOOLEAN.XOR,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,
            substrait_name="xor",
            protocol_method=ScalarBooleanExpressionProtocol.xor,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_BOOLEAN.AND_NOT,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,
            substrait_name="and_not",
            protocol_method=ScalarBooleanExpressionProtocol.and_not,
        ),
        # Boolean checks
        # Mountainash extensions
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_COMPARISON.XOR_PARITY,
            substrait_uri=MountainashExtension.COMPARISON,
            substrait_name="xor_parity",
            protocol_method=MountainashBooleanExpressionProtocol.xor_parity,
        ),
    ]

    # ========================================
    # Arithmetic Functions (Substrait standard)
    # ========================================

    SCALAR_ARITHMETIC_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_ARITHMETIC.ADD,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="add",
            protocol_method=ScalarArithmeticExpressionProtocol.add,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_ARITHMETIC.SUBTRACT,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="subtract",
            protocol_method=ScalarArithmeticExpressionProtocol.subtract,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_ARITHMETIC.MULTIPLY,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="multiply",
            protocol_method=ScalarArithmeticExpressionProtocol.multiply,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_ARITHMETIC.DIVIDE,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="divide",
            protocol_method=ScalarArithmeticExpressionProtocol.divide,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_ARITHMETIC.MODULO,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="modulus",
            protocol_method=ScalarArithmeticExpressionProtocol.modulus,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_ARITHMETIC.POWER,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="power",
            protocol_method=ScalarArithmeticExpressionProtocol.power,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_ARITHMETIC.NEGATE,
            substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
            substrait_name="negate",
            protocol_method=ScalarArithmeticExpressionProtocol.negate,
        ),
        # Mountainash extension
        # ExpressionFunctionDef(
        #     function_key="floor_divide",
        #     substrait_uri=SubstraitExtension.MOUNTAINASH,
        #     substrait_name="floor_divide",
        #     is_extension=True,
        #     protocol_method=ArithmeticExpressionProtocol.floor_divide,
        # ),
    ]

    # ========================================
    # String Functions (Substrait standard)
    # ========================================

    SCALAR_STRING_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.UPPER,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="upper",
            protocol_method=ScalarStringExpressionProtocol.upper,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.LOWER,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="lower",
            protocol_method=ScalarStringExpressionProtocol.lower,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.CONCAT,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="concat",
            options=("separator",),
            protocol_method=ScalarStringExpressionProtocol.concat,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.SUBSTRING,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="substring",
            options=("start", "length"),
            protocol_method=ScalarStringExpressionProtocol.substring,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.TRIM,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="trim",
            protocol_method=ScalarStringExpressionProtocol.trim,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.LTRIM,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="ltrim",
            protocol_method=ScalarStringExpressionProtocol.ltrim,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.RTRIM,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="rtrim",
            protocol_method=ScalarStringExpressionProtocol.rtrim,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.CHAR_LENGTH,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="char_length",
            protocol_method=ScalarStringExpressionProtocol.char_length,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.REPLACE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="replace",
            protocol_method=ScalarStringExpressionProtocol.replace,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.SPLIT,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="string_split",
            protocol_method=ScalarStringExpressionProtocol.string_split,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.CONTAINS,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="contains",
            protocol_method=ScalarStringExpressionProtocol.contains,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.STARTS_WITH,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="starts_with",
            protocol_method=ScalarStringExpressionProtocol.starts_with,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.ENDS_WITH,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="ends_with",
            protocol_method=ScalarStringExpressionProtocol.ends_with,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.LIKE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="like",
            protocol_method=ScalarStringExpressionProtocol.like,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.REGEXP_MATCH,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="regexp_match_substring",
            protocol_method=ScalarStringExpressionProtocol.regexp_match_substring,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.REGEXP_SPLIT,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="regexp_string_split",
            protocol_method=ScalarStringExpressionProtocol.regexp_string_split,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_STRING.REGEXP_REPLACE,
            substrait_uri=SubstraitExtension.SCALAR_STRING,
            substrait_name="regexp_replace",
            protocol_method=ScalarStringExpressionProtocol.regexp_replace,
        ),
    ]

    # ========================================
    # Set Functions (Substrait standard)
    # ========================================

    SCALAR_SET_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_SET.INDEX_IN,
            substrait_uri=SubstraitExtension.SCALAR_SET,
            substrait_name="index_in",
            protocol_method=ScalarSetExpressionProtocol.index_in,
        ),
    ]


    # ========================================
    # Temporal Functions (Substrait standard)
    # ========================================

    SCALAR_DATETIME_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_DATETIME.EXTRACT,
            substrait_uri=SubstraitExtension.SCALAR_DATETIME,
            substrait_name="extract",
            options=("component",),  # component="YEAR"
            protocol_method=ScalarDatetimeExpressionProtocol.extract,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_DATETIME.EXTRACT_BOOLEAN,
            substrait_uri=SubstraitExtension.SCALAR_DATETIME,
            substrait_name="extract",
            protocol_method=ScalarDatetimeExpressionProtocol.extract_boolean,
        ),
    ]

    # ========================================
    # Rounding Functions (Substrait standard)
    # ========================================

    SCALAR_ROUNDING_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_ROUNDING.CEIL,
            substrait_uri=SubstraitExtension.SCALAR_ROUNDING,
            substrait_name="ceil",
            protocol_method=ScalarRoundingExpressionProtocol.ceil,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_ROUNDING.FLOOR,
            substrait_uri=SubstraitExtension.SCALAR_ROUNDING,
            substrait_name="floor",
            protocol_method=ScalarRoundingExpressionProtocol.floor,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_ROUNDING.ROUND,
            substrait_uri=SubstraitExtension.SCALAR_ROUNDING,
            substrait_name="round",
            options=("s", "rounding"),
            protocol_method=ScalarRoundingExpressionProtocol.round,
        ),
    ]

    # ========================================
    # Logarithmic Functions (Substrait standard)
    # ========================================

    SCALAR_LOGARITHMIC_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_LOGARITHMIC.LOG,
            substrait_uri=SubstraitExtension.SCALAR_LOGARITHMIC,
            substrait_name="ln",
            protocol_method=ScalarLogarithmicExpressionProtocol.ln,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_LOGARITHMIC.LOG10,
            substrait_uri=SubstraitExtension.SCALAR_LOGARITHMIC,
            substrait_name="log10",
            protocol_method=ScalarLogarithmicExpressionProtocol.log10,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_LOGARITHMIC.LOG2,
            substrait_uri=SubstraitExtension.SCALAR_LOGARITHMIC,
            substrait_name="log2",
            protocol_method=ScalarLogarithmicExpressionProtocol.log2,
        ),
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_LOGARITHMIC.LOGB,
            substrait_uri=SubstraitExtension.SCALAR_LOGARITHMIC,
            substrait_name="logb",
            protocol_method=ScalarLogarithmicExpressionProtocol.logb,
        ),
    ]

    # ========================================
    # Aggregate Functions (Substrait standard)
    # ========================================

    SCALAR_AGGREGATE_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=KEY_SCALAR_AGGREGATE.COUNT,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="count",
            options=("overflow",),
            protocol_method=ScalarAggregateExpressionProtocol.count,
        ),
    ]

    # ========================================
    # Cast Functions (Substrait standard)
    # ========================================

    CAST_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=KEY_CAST.CAST,
            substrait_uri=SubstraitExtension.SCALAR_COMPARISON,  # Cast uses comparison extension
            substrait_name="cast",
            options=("dtype",),
            protocol_method=CastExpressionProtocol.cast,
        ),
    ]

    # ========================================
    # Conditional Functions (Substrait standard)
    # ========================================

    CONDITIONAL_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=KEY_CONDITIONAL.IF_THEN_ELSE,
            substrait_uri=SubstraitExtension.SCALAR_BOOLEAN,  # Conditional uses boolean extension
            substrait_name="if_then",
            protocol_method=ConditionalExpressionProtocol.if_then_else,
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
    #         protocol_method=ScalarComparisonExpressionProtocol.always_true,
    #     ),
    #     ExpressionFunctionDef(
    #         function_key="always_false",
    #         substrait_uri=SubstraitExtension.BOOLEAN,
    #         substrait_name="false",  # Literal false
    #         protocol_method=ScalarComparisonExpressionProtocol.always_false,
    #     ),
    # ]

    # ========================================
    # Ternary Functions (Mountainash extension)
    # ========================================

    TERNARY_FUNCTIONS = [
        # Ternary comparisons (return -1/0/1)
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_EQ,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_equal",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_eq,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_NE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_not_equal",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_ne,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_GT,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_gt",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_gt,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_LT,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_lt",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_lt,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_GE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_gte",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_ge,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_LE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_lte",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_le,
        ),
        # Ternary collection
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_IS_IN,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_in",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_is_in,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_IS_NOT_IN,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_not_in",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_is_not_in,
        ),
        # Ternary logical
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_AND,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_and",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_and,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_OR,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_or",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_or,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_NOT,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_not",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_not,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_XOR,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_xor",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_xor,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.T_XOR_PARITY,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_xor_parity",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.t_xor_parity,
        ),
        # Ternary to boolean conversions
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.IS_TRUE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_true",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.is_true_ternary,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.IS_FALSE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_false",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.is_false_ternary,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.IS_UNKNOWN,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_unknown",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.is_unknown,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.IS_KNOWN,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_is_known",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.is_known,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.MAYBE_TRUE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_maybe_true",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.maybe_true,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.MAYBE_FALSE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="ternary_maybe_false",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.maybe_false,
        ),
        # Boolean to ternary conversion
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.TO_TERNARY,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="to_ternary",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.to_ternary,
        ),
        # Ternary constants
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.ALWAYS_TRUE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="always_true",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.always_true_ternary,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.ALWAYS_FALSE,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="always_false",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.always_false_ternary,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.ALWAYS_UNKNOWN,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="always_unknown",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.always_unknown,
        ),
        # Utility function for collecting values in t_is_in/t_is_not_in
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_TERNARY.LIST,
            substrait_uri=MountainashExtension.TERNARY,
            substrait_name="list",
            is_extension=True,
            protocol_method=TernaryExpressionProtocol.collect_values,
        ),
    ]

    # ========================================
    # Mountainash Arithmetic Extensions
    # ========================================

    MOUNTAINASH_ARITHMETIC_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_ARITHMETIC.FLOOR_DIVIDE,
            substrait_uri=MountainashExtension.ARITHMETIC,
            substrait_name="floor_divide",
            is_extension=True,
            protocol_method=MountainashArithmeticExpressionProtocol.floor_divide,
        ),
    ]

    # ========================================
    # Mountainash Null Extensions
    # ========================================

    MOUNTAINASH_NULL_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_NULL.FILL_NULL,
            substrait_uri=MountainashExtension.NULL,
            substrait_name="fill_null",
            is_extension=True,
            protocol_method=MountainashNullExpressionProtocol.fill_null,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_NULL.NULL_IF,
            substrait_uri=MountainashExtension.NULL,
            substrait_name="null_if",
            is_extension=True,
            protocol_method=MountainashNullExpressionProtocol.null_if,
        ),
    ]

    # ========================================
    # Mountainash Name Extensions
    # ========================================

    MOUNTAINASH_NAME_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_NAME.ALIAS,
            substrait_uri=MountainashExtension.NAME,
            substrait_name="alias",
            is_extension=True,
            protocol_method=MountainashNameExpressionProtocol.alias,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_NAME.PREFIX,
            substrait_uri=MountainashExtension.NAME,
            substrait_name="prefix",
            is_extension=True,
            protocol_method=MountainashNameExpressionProtocol.prefix,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_NAME.SUFFIX,
            substrait_uri=MountainashExtension.NAME,
            substrait_name="suffix",
            is_extension=True,
            protocol_method=MountainashNameExpressionProtocol.suffix,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_NAME.NAME_TO_UPPER,
            substrait_uri=MountainashExtension.NAME,
            substrait_name="name_to_upper",
            is_extension=True,
            protocol_method=MountainashNameExpressionProtocol.name_to_upper,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_NAME.NAME_TO_LOWER,
            substrait_uri=MountainashExtension.NAME,
            substrait_name="name_to_lower",
            is_extension=True,
            protocol_method=MountainashNameExpressionProtocol.name_to_lower,
        ),
    ]

    # ========================================
    # Mountainash Datetime Extensions
    # ========================================

    MOUNTAINASH_DATETIME_FUNCTIONS = [
        # Extraction - Basic
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_YEAR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_year",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.year,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_MONTH,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_month",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.month,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_DAY,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_day",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.day,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_HOUR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_hour",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.hour,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_MINUTE,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_minute",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.minute,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_SECOND,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_second",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.second,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_MILLISECOND,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_millisecond",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.millisecond,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_MICROSECOND,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_microsecond",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.microsecond,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_NANOSECOND,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_nanosecond",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.nanosecond,
        ),
        # Extraction - Calendar
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_QUARTER,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_quarter",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.quarter,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_DAY_OF_YEAR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_day_of_year",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.day_of_year,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_WEEKDAY,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_weekday",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.day_of_week,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_WEEK,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_week",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.week_of_year,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_ISO_YEAR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_iso_year",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.iso_year,
        ),
        # Extraction - Special
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_UNIX_TIME,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_unix_time",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.unix_timestamp,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.EXTRACT_TIMEZONE_OFFSET,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="extract_timezone_offset",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.timezone_offset,
        ),
        # Boolean Extraction
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.IS_LEAP_YEAR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="is_leap_year",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.is_leap_year,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.IS_DST,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="is_dst",
            options=("timezone",),
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.is_dst,
        ),
        # Addition
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.ADD_YEARS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_years",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.add_years,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.ADD_MONTHS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_months",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.add_months,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.ADD_DAYS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_days",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.add_days,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.ADD_HOURS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_hours",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.add_hours,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.ADD_MINUTES,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_minutes",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.add_minutes,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.ADD_SECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_seconds",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.add_seconds,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.ADD_MILLISECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_milliseconds",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.add_milliseconds,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.ADD_MICROSECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="add_microseconds",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.add_microseconds,
        ),
        # Difference
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.DIFF_YEARS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_years",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.diff_years,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.DIFF_MONTHS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_months",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.diff_months,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.DIFF_DAYS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_days",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.diff_days,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.DIFF_HOURS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_hours",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.diff_hours,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.DIFF_MINUTES,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_minutes",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.diff_minutes,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.DIFF_SECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_seconds",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.diff_seconds,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.DIFF_MILLISECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="diff_milliseconds",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.diff_milliseconds,
        ),
        # Truncation / Rounding
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.TRUNCATE,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="truncate",
            options=("unit",),
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.truncate,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.ROUND,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="round",
            options=("unit",),
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.round,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.CEIL,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="ceil",
            options=("unit",),
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.ceil,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.FLOOR,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="floor",
            options=("unit",),
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.floor,
        ),
        # Timezone
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.TO_TIMEZONE,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="to_timezone",
            options=("timezone",),
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.to_timezone,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.ASSUME_TIMEZONE,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="assume_timezone",
            options=("timezone",),
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.assume_timezone,
        ),
        # Formatting
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.STRFTIME,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="strftime",
            options=("format",),
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.strftime,
        ),
        # Flexible Duration Offset
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.OFFSET_BY,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="offset_by",
            options=("offset",),
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.offset_by,
        ),
        # Snapshot
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.TODAY,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="today",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.today,
        ),
        ExpressionFunctionDef(
            function_key=MOUNTAINASH_DATETIME.NOW,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="now",
            is_extension=True,
            protocol_method=MountainashDatetimeExpressionProtocol.now,
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
    )

    for func in all_functions:
        FunctionRegistry.register(func)
