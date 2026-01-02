"""Core expression APIBuilders.

Substrait-aligned APIBuilder implementations.
"""

from .api_bldr_cast import SubstraitCastAPIBuilder
from .api_bldr_conditional import SubstraitConditionalAPIBuilder, SubstraitWhenAPIBuilder, SubstraitThenAPIBuilder
from .api_bldr_field_reference import SubstraitFieldReferenceAPIBuilder
from .api_bldr_literal import SubstraitLiteralAPIBuilder
# from .api_bldr_scalar_aggregate import SubstraitScalarAggregateAPIBuilder
from .api_bldr_scalar_arithmetic import SubstraitScalarArithmeticAPIBuilder
from .api_bldr_scalar_boolean import SubstraitScalarBooleanAPIBuilder
from .api_bldr_scalar_comparison import SubstraitScalarComparisonAPIBuilder
from .api_bldr_scalar_datetime import SubstraitScalarDatetimeAPIBuilder
from .api_bldr_scalar_logarithmic import SubstraitScalarLogarithmicAPIBuilder
from .api_bldr_scalar_rounding import SubstraitScalarRoundingAPIBuilder
from .api_bldr_scalar_set import SubstraitScalarSetAPIBuilder
from .api_bldr_scalar_string import SubstraitScalarStringAPIBuilder
# from .api_bldr_ternary import TernaryAPIBuilder
# from .api_bldr_null import NullAPIBuilder
# from .api_bldr_name import NameAPIBuilder
# from .api_bldr_native import NativeAPIBuilder

__all__ = [
    # Core nodes
    "SubstraitCastAPIBuilder",
    "SubstraitFieldReferenceAPIBuilder",
    "SubstraitLiteralAPIBuilder",

    "SubstraitConditionalAPIBuilder",
    "SubstraitWhenAPIBuilder",
    "SubstraitThenAPIBuilder",


    # Scalar operations
    # "SubstraitScalarAggregateAPIBuilder",
    "SubstraitScalarArithmeticAPIBuilder",
    "SubstraitScalarBooleanAPIBuilder",
    "SubstraitScalarComparisonAPIBuilder",
    "SubstraitScalarDatetimeAPIBuilder",
    "SubstraitScalarLogarithmicAPIBuilder",
    "SubstraitScalarRoundingAPIBuilder",
    "SubstraitScalarSetAPIBuilder",
    "SubstraitScalarStringAPIBuilder",
]
