"""Substrait-aligned expression protocols.

This module exports APIBuilderProtocols (backend primitives) and APIBuilderProtocols
(user-facing fluent API) aligned with the Substrait specification.

APIBuilderProtocols define the backend-specific operations.
APIBuilderProtocols define the user-facing API methods that create expression nodes.
"""
from __future__ import annotations

# Foundation protocols
from .prtcl_api_bldr_cast import SubstraitCastAPIBuilderProtocol
from .prtcl_api_bldr_conditional import (
    SubstraitConditionalAPIBuilderProtocol,
    SubstraitWhenAPIBuilderProtocol,
    SubstraitThenAPIBuilderProtocol,
)
from .prtcl_api_bldr_field_reference import SubstraitFieldReferenceAPIBuilderProtocol
from .prtcl_api_bldr_literal import SubstraitLiteralAPIBuilderProtocol

from .prtcl_api_bldr_scalar_aggregate import SubstraitScalarAggregateAPIBuilderProtocol
from .prtcl_api_bldr_scalar_arithmetic import SubstraitScalarArithmeticAPIBuilderProtocol
from .prtcl_api_bldr_scalar_boolean import SubstraitScalarBooleanAPIBuilderProtocol
from .prtcl_api_bldr_scalar_comparison import SubstraitScalarComparisonAPIBuilderProtocol
from .prtcl_api_bldr_scalar_datetime import SubstraitScalarDatetimeAPIBuilderProtocol
from .prtcl_api_bldr_scalar_logarithmic import SubstraitScalarLogarithmicAPIBuilderProtocol
from .prtcl_api_bldr_scalar_rounding import SubstraitScalarRoundingAPIBuilderProtocol
from .prtcl_api_bldr_scalar_set import SubstraitScalarSetAPIBuilderProtocol
from .prtcl_api_bldr_scalar_string import  SubstraitScalarStringAPIBuilderProtocol
from .prtcl_api_bldr_window_arithmetic import SubstraitWindowArithmeticAPIBuilderProtocol


__all__ = [
    # Foundation - Expression Protocols
    "SubstraitCastAPIBuilderProtocol",
    "SubstraitConditionalAPIBuilderProtocol",
    "SubstraitFieldReferenceAPIBuilderProtocol",
    "SubstraitLiteralAPIBuilderProtocol",

    "SubstraitWhenAPIBuilderProtocol",
    "SubstraitThenAPIBuilderProtocol",

    "SubstraitScalarAggregateAPIBuilderProtocol",
    "SubstraitScalarArithmeticAPIBuilderProtocol",
    "SubstraitScalarBooleanAPIBuilderProtocol",
    "SubstraitScalarComparisonAPIBuilderProtocol",
    "SubstraitScalarDatetimeAPIBuilderProtocol",
    "SubstraitScalarLogarithmicAPIBuilderProtocol",
    "SubstraitScalarRoundingAPIBuilderProtocol",
    "SubstraitScalarSetAPIBuilderProtocol",
    "SubstraitScalarStringAPIBuilderProtocol",
    "SubstraitWindowArithmeticAPIBuilderProtocol",
]
