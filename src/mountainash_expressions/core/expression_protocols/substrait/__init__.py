"""Substrait-aligned expression protocols.

This module exports ExpressionProtocols (backend primitives) and BuilderProtocols
(user-facing fluent API) aligned with the Substrait specification.

ExpressionProtocols define the backend-specific operations.
BuilderProtocols define the user-facing API methods that create expression nodes.
"""

# Foundation protocols
from .prtcl_cast import CastExpressionProtocol, CastBuilderProtocol
from .prtcl_conditional import (
    ConditionalExpressionProtocol,
    ConditionalBuilderProtocol,
    WhenBuilderProtocol,
    ThenBuilderProtocol,
)
from .prtcl_field_reference import FieldReferenceExpressionProtocol
from .prtcl_literal import LiteralExpressionProtocol

# Scalar protocols - comparison and boolean
from .prtcl_scalar_comparison import (
    ScalarComparisonExpressionProtocol,
    ScalarComparisonBuilderProtocol,
)
from .prtcl_scalar_boolean import (
    ScalarBooleanExpressionProtocol,
    ScalarBooleanBuilderProtocol,
)

# Scalar protocols - arithmetic and math
from .prtcl_scalar_arithmetic import (
    ScalarArithmeticExpressionProtocol,
    ScalarArithmeticBuilderProtocol,
)
from .prtcl_scalar_rounding import (
    ScalarRoundingExpressionProtocol,
    ScalarRoundingBuilderProtocol,
)
from .prtcl_scalar_logarithmic import (
    ScalarLogarithmicExpressionProtocol,
    ScalarLogarithmicBuilderProtocol,
)

# Scalar protocols - string and datetime
from .prtcl_scalar_string import (
    ScalarStringExpressionProtocol,
    ScalarStringBuilderProtocol,
)
from .prtcl_scalar_datetime import (
    ScalarDatetimeExpressionProtocol,
    ScalarDatetimeBuilderProtocol,
)

# Scalar protocols - set and aggregate
from .prtcl_scalar_set import (
    ScalarSetExpressionProtocol,
    ScalarSetBuilderProtocol,
)
from .prtcl_scalar_aggregate import (
    ScalarAggregateExpressionProtocol,
    ScalarAggregateBuilderProtocol,
)

__all__ = [
    # Foundation - Expression Protocols
    "CastExpressionProtocol",
    "ConditionalExpressionProtocol",
    "FieldReferenceExpressionProtocol",
    "LiteralExpressionProtocol",
    # Foundation - Builder Protocols
    "CastBuilderProtocol",
    "ConditionalBuilderProtocol",
    "WhenBuilderProtocol",
    "ThenBuilderProtocol",
    # Scalar Comparison - Expression & Builder
    "ScalarComparisonExpressionProtocol",
    "ScalarComparisonBuilderProtocol",
    # Scalar Boolean - Expression & Builder
    "ScalarBooleanExpressionProtocol",
    "ScalarBooleanBuilderProtocol",
    # Scalar Arithmetic - Expression & Builder
    "ScalarArithmeticExpressionProtocol",
    "ScalarArithmeticBuilderProtocol",
    # Scalar Rounding - Expression & Builder
    "ScalarRoundingExpressionProtocol",
    "ScalarRoundingBuilderProtocol",
    # Scalar Logarithmic - Expression & Builder
    "ScalarLogarithmicExpressionProtocol",
    "ScalarLogarithmicBuilderProtocol",
    # Scalar String - Expression & Builder
    "ScalarStringExpressionProtocol",
    "ScalarStringBuilderProtocol",
    # Scalar Datetime - Expression & Builder
    "ScalarDatetimeExpressionProtocol",
    "ScalarDatetimeBuilderProtocol",
    # Scalar Set - Expression & Builder
    "ScalarSetExpressionProtocol",
    "ScalarSetBuilderProtocol",
    # Scalar Aggregate - Expression & Builder
    "ScalarAggregateExpressionProtocol",
    "ScalarAggregateBuilderProtocol",
]
