"""Substrait-aligned expression protocols.

This module exports ExpressionSystemProtocols (backend primitives) and BuilderProtocols
(user-facing fluent API) aligned with the Substrait specification.

ExpressionSystemProtocols define the backend-specific operations.
BuilderProtocols define the user-facing API methods that create expression nodes.
"""

# Foundation protocols
from .prtcl_expsys_cast import SubstraitCastExpressionSystemProtocol #, CastBuilderProtocol
from .prtcl_expsys_conditional import (
    SubstraitConditionalExpressionSystemProtocol,
    # ConditionalBuilderProtocol,
    # WhenBuilderProtocol,
    # ThenBuilderProtocol,
)
from .prtcl_expsys_field_reference import SubstraitFieldReferenceExpressionSystemProtocol
from .prtcl_expsys_literal import SubstraitLiteralExpressionSystemProtocol

# Scalar protocols - comparison and boolean
from .prtcl_expsys_scalar_comparison import (
    SubstraitScalarComparisonExpressionSystemProtocol,
    # ScalarComparisonBuilderProtocol,
)
from .prtcl_expsys_scalar_boolean import (
    SubstraitScalarBooleanExpressionSystemProtocol,
    # ScalarBooleanBuilderProtocol,
)

# Scalar protocols - arithmetic and math
from .prtcl_expsys_scalar_arithmetic import (
    SubstraitScalarArithmeticExpressionSystemProtocol,
    # ScalarArithmeticBuilderProtocol,
)
from .prtcl_expsys_scalar_rounding import (
    SubstraitScalarRoundingExpressionSystemProtocol,
    # ScalarRoundingBuilderProtocol,
)
from .prtcl_expsys_scalar_logarithmic import (
    SubstraitScalarLogarithmicExpressionSystemProtocol,
    # ScalarLogarithmicBuilderProtocol,
)

# Scalar protocols - string and datetime
from .prtcl_expsys_scalar_string import (
    SubstraitScalarStringExpressionSystemProtocol,
    # ScalarStringBuilderProtocol,
)
from .prtcl_expsys_scalar_datetime import (
    SubstraitScalarDatetimeExpressionSystemProtocol,
    # ScalarDatetimeBuilderProtocol,
)

# Scalar protocols - set and aggregate
from .prtcl_expsys_scalar_set import (
    SubstraitScalarSetExpressionSystemProtocol,
    # ScalarSetBuilderProtocol,
)
from .prtcl_expsys_scalar_aggregate import (
    SubstraitScalarAggregateExpressionSystemProtocol,
    # ScalarAggregateBuilderProtocol,
)

__all__ = [
    # Foundation - Expression Protocols
    "SubstraitCastExpressionSystemProtocol",
    "SubstraitConditionalExpressionSystemProtocol",
    "SubstraitFieldReferenceExpressionSystemProtocol",
    "SubstraitLiteralExpressionSystemProtocol",

    "SubstraitScalarComparisonExpressionSystemProtocol",
    "SubstraitScalarBooleanExpressionSystemProtocol",
    "SubstraitScalarArithmeticExpressionSystemProtocol",
    "SubstraitScalarRoundingExpressionSystemProtocol",
    "SubstraitScalarLogarithmicExpressionSystemProtocol",
    "SubstraitScalarStringExpressionSystemProtocol",
    "SubstraitScalarDatetimeExpressionSystemProtocol",
    "SubstraitScalarSetExpressionSystemProtocol",
    "SubstraitScalarAggregateExpressionSystemProtocol",
]
