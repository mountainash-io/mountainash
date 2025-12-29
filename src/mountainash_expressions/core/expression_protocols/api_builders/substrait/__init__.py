"""Substrait-aligned expression protocols.

This module exports APIBuilderProtocols (backend primitives) and APIBuilderProtocols
(user-facing fluent API) aligned with the Substrait specification.

APIBuilderProtocols define the backend-specific operations.
APIBuilderProtocols define the user-facing API methods that create expression nodes.
"""

# Foundation protocols
from .prtcl_api_bldr_cast import SubstraitCastAPIBuilderProtocol
from .prtcl_api_bldr_conditional import (
    SubstraitConditionalAPIBuilderProtocol,
    SubstraitWhenAPIBuilderProtocol,
    SubstraitThenAPIBuilderProtocol,
)
from .prtcl_api_bldr_field_reference import SubstraitFieldReferenceAPIBuilderProtocol
from .prtcl_api_bldr_literal import SubstraitLiteralAPIBuilderProtocol

# Scalar protocols - comparison and boolean
from .prtcl_api_bldr_scalar_comparison import (
    SubstraitScalarComparisonAPIBuilderProtocol,
)
from .prtcl_api_bldr_scalar_boolean import (
    SubstraitScalarBooleanAPIBuilderProtocol,
)

# Scalar protocols - arithmetic and math
from .prtcl_api_bldr_scalar_arithmetic import (
    SubstraitScalarArithmeticAPIBuilderProtocol,
)
from .prtcl_api_bldr_scalar_rounding import (
    SubstraitScalarRoundingAPIBuilderProtocol,
)
from .prtcl_api_bldr_scalar_logarithmic import (
    SubstraitScalarLogarithmicAPIBuilderProtocol,
)

# Scalar protocols - string and datetime
from .prtcl_api_bldr_scalar_string import (
    SubstraitScalarStringAPIBuilderProtocol,
)
from .prtcl_api_bldr_scalar_datetime import (
    SubstraitScalarDatetimeAPIBuilderProtocol,
)

# Scalar protocols - set and aggregate
from .prtcl_api_bldr_scalar_set import (
    SubstraitScalarSetAPIBuilderProtocol,
)
from .prtcl_api_bldr_scalar_aggregate import (
    SubstraitScalarAggregateAPIBuilderProtocol,
)

__all__ = [
    # Foundation - Expression Protocols
    "SubstraitCastAPIBuilderProtocol",
    "SubstraitConditionalAPIBuilderProtocol",
    "SubstraitFieldReferenceAPIBuilderProtocol",
    "SubstraitLiteralAPIBuilderProtocol",
    # Foundation - Builder Protocols
    "SubstraitCastAPIBuilderProtocol",
    "SubstraitConditionalAPIBuilderProtocol",
    "SubstraitWhenAPIBuilderProtocol",
    "SubstraitThenAPIBuilderProtocol",
    # Scalar Comparison - Expression & Builder
    "SubstraitScalarComparisonAPIBuilderProtocol",
    # Scalar Boolean - Expression & Builder
    "SubstraitScalarBooleanAPIBuilderProtocol",
    # Scalar Arithmetic - Expression & Builder
    "SubstraitScalarArithmeticAPIBuilderProtocol",
    # Scalar Rounding - Expression & Builder
    "SubstraitScalarRoundingAPIBuilderProtocol",
    # Scalar Logarithmic - Expression & Builder
    "SubstraitScalarLogarithmicAPIBuilderProtocol",
    # Scalar String - Expression & Builder
    "SubstraitScalarStringAPIBuilderProtocol",
    # Scalar Datetime - Expression & Builder
    "SubstraitScalarDatetimeAPIBuilderProtocol",
    # Scalar Set - Expression & Builder
    "SubstraitScalarSetAPIBuilderProtocol",
    # Scalar Aggregate - Expression & Builder
    "SubstraitScalarAggregateAPIBuilderProtocol",
]
