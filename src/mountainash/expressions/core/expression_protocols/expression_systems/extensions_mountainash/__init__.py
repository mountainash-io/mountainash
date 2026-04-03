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
from __future__ import annotations

# from .prtcl_expsys_ext_ma_scalar_aggregate import  MountainAshScalarAggregateExpressionSystemProtocol
from .prtcl_expsys_ext_ma_scalar_arithmetic import MountainAshScalarArithmeticExpressionSystemProtocol
from .prtcl_expsys_ext_ma_scalar_boolean import   MountainAshScalarBooleanExpressionSystemProtocol
from .prtcl_expsys_ext_ma_scalar_datetime import MountainAshScalarDatetimeExpressionSystemProtocol
from .prtcl_expsys_ext_ma_scalar_ternary import MountainAshScalarTernaryExpressionSystemProtocol
from .prtcl_expsys_ext_ma_null import MountainAshNullExpressionSystemProtocol
from .prtcl_expsys_ext_ma_name import MountainAshNameExpressionSystemProtocol
from .prtcl_expsys_ext_ma_scalar_set import SubstraitScalarSetExpressionSystemProtocol as MountainAshScalarSetExpressionSystemProtocol

__all__ = [
    # Ternary
    # "MountainAshScalarAggregateExpressionSystemProtocol",
    "MountainAshScalarArithmeticExpressionSystemProtocol",
    "MountainAshScalarBooleanExpressionSystemProtocol",
    "MountainAshScalarDatetimeExpressionSystemProtocol",
    "MountainAshScalarTernaryExpressionSystemProtocol",
    "MountainAshNullExpressionSystemProtocol",
    "MountainAshNameExpressionSystemProtocol",
]
