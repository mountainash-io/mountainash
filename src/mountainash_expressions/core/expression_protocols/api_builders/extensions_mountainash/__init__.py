"""Mountainash extension protocols.

This module contains protocols for Mountainash-specific operations that extend
beyond the Substrait specification. These extensions include:

- Ternary Logic: Three-valued logic (TRUE/UNKNOWN/FALSE) for NULL-aware comparisons
- Arithmetic Extensions: floor_divide
- Boolean Extensions: xor_parity
- DateTime Extensions: Convenience functions for datetime manipulation
- Null Extensions: fill_null, null_if
- Name Extensions: alias, prefix, suffix

Extension URIs are stored in /extensions/ directory at repository root.
"""

from .prtcl_api_bldr_ext_ma_name import MountainAshNameAPIBuilderProtocol
from .prtcl_api_bldr_ext_ma_native import MountainAshNativeAPIBuilderProtocol
from .prtcl_api_bldr_ext_ma_null import MountainAshNullAPIBuilderProtocol
# from .prtcl_api_bldr_ext_ma_scalar_aggregate import MountainAshScalarAggregateAPIBuilderProtocol
from .prtcl_api_bldr_ext_ma_scalar_arithmetic import MountainAshScalarArithmeticAPIBuilderProtocol
from .prtcl_api_bldr_ext_ma_scalar_datetime import MountainAshScalarDatetimeAPIBuilderProtocol
from .prtcl_api_bldr_ext_ma_scalar_boolean import MountainAshScalarBooleanAPIBuilderProtocol
from .prtcl_api_bldr_ext_ma_scalar_ternary import MountainAshScalarTernaryAPIBuilderProtocol

__all__ = [
    "MountainAshNameAPIBuilderProtocol",
    "MountainAshNativeAPIBuilderProtocol",
    "MountainAshNullAPIBuilderProtocol",
    # "MountainAshScalarAggregateAPIBuilderProtocol",
    "MountainAshScalarArithmeticAPIBuilderProtocol",
    "MountainAshScalarDatetimeAPIBuilderProtocol",
    "MountainAshScalarBooleanAPIBuilderProtocol",
    "MountainAshScalarTernaryAPIBuilderProtocol",
]
