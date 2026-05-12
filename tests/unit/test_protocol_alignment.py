"""
Tests for protocol-implementation alignment.

These tests ensure bidirectional consistency between protocols and their implementations:
1. All protocol methods must have implementations
2. All implementation methods must have protocols (no rogue methods)
3. Method signatures (parameter names) must match between protocol and implementation

This catches architectural drift where protocols and implementations diverge.

Architecture Notes (Substrait-aligned):

ExpressionSystem Protocols (Backend Layer):
- Substrait: core/expression_protocols/expression_systems/substrait/
- Extensions: core/expression_protocols/expression_systems/extensions_mountainash/
- Backend implementations: backends/expression_systems/{polars,ibis,narwhals}/substrait/
- Backend extensions: backends/expression_systems/{polars,ibis,narwhals}/extensions_mountainash/

APIBuilder Protocols (User-Facing Layer):
- Substrait: core/expression_protocols/api_builders/substrait/
- Extensions: core/expression_protocols/api_builders/extensions_mountainash/
- Implementations: core/expression_api/api_builders/substrait/
- Extension implementations: core/expression_api/api_builders/extensions_mountainash/
"""

import pytest
import inspect
import importlib
import pkgutil
from datetime import date
from pathlib import Path
from typing import Protocol, Set, List, Type
from dataclasses import dataclass, field
import warnings

from cross_backend.argument_types._coverage_guard_helpers import (
    KnownGap,
)

pytestmark = pytest.mark.protocol_alignment


# =============================================================================
# Test Infrastructure
# =============================================================================

@dataclass
class SignatureMismatch:
    """Details of a signature mismatch between protocol and implementation."""
    method_name: str
    protocol_params: List[str]
    impl_params: List[str]

    def __str__(self) -> str:
        return (
            f"  {self.method_name}:\n"
            f"    protocol: ({', '.join(self.protocol_params)})\n"
            f"    impl:     ({', '.join(self.impl_params)})"
        )


@dataclass
class AlignmentResult:
    """Result of checking alignment between a protocol and implementation."""
    protocol_name: str
    implementation_name: str
    protocol_only: Set[str]  # Methods in protocol but not implementation
    implementation_only: Set[str]  # Methods in implementation but not protocol
    aligned: Set[str]  # Methods in both
    signature_mismatches: List[SignatureMismatch] = field(default_factory=list)

    @property
    def is_aligned(self) -> bool:
        return (
            len(self.protocol_only) == 0
            and len(self.implementation_only) == 0
            and len(self.signature_mismatches) == 0
        )

    def __str__(self) -> str:
        lines = [f"\n{'='*60}"]
        lines.append(f"Protocol: {self.protocol_name}")
        lines.append(f"Implementation: {self.implementation_name}")
        lines.append(f"{'='*60}")

        if self.is_aligned:
            lines.append(f"ALIGNED: {len(self.aligned)} methods match")
        else:
            if self.protocol_only:
                lines.append(f"\nPROTOCOL METHOD MISSING FROM IMPLEMENTATION ({len(self.protocol_only)}):")
                for method in sorted(self.protocol_only):
                    lines.append(f"  - {method}")

            if self.implementation_only:
                lines.append(f"\nNON-PROTOCOL METHOD DEFINED IN IMPLEMENTATION({len(self.implementation_only)}):")
                for method in sorted(self.implementation_only):
                    lines.append(f"  + {method}")

            if self.signature_mismatches:
                lines.append(f"\nSIGNATURE MISMATCHES ({len(self.signature_mismatches)}):")
                for mismatch in sorted(self.signature_mismatches, key=lambda m: m.method_name):
                    lines.append(str(mismatch))

        return "\n".join(lines)


def get_protocol_methods(protocol_class: Type) -> Set[str]:
    """
    Extract public method names from a Protocol class.

    Only returns methods explicitly defined in the protocol class itself,
    not inherited from Protocol base class.
    """
    methods = set()

    # Get only methods defined directly in this class's __dict__
    for name in protocol_class.__dict__:
        # Skip private methods
        if name.startswith('_'):
            continue

        value = protocol_class.__dict__[name]

        # Check if it's a method stub (function) or property
        if callable(value) or isinstance(value, property):
            methods.add(name)

    return methods


def get_implementation_methods(impl_class: Type, include_inherited: bool = False) -> Set[str]:
    """
    Extract public method names from an implementation class.

    Args:
        impl_class: The implementation class to inspect
        include_inherited: Whether to include methods from parent classes
    """
    methods = set()

    if include_inherited:
        # Walk the MRO to get all methods
        for klass in impl_class.__mro__:
            if klass is object:
                continue
            for name in klass.__dict__:
                if _is_public_method(name, klass.__dict__.get(name)):
                    methods.add(name)
    else:
        # Only methods defined directly on this class
        for name in impl_class.__dict__:
            if _is_public_method(name, impl_class.__dict__.get(name)):
                methods.add(name)

    return methods


def _is_public_method(name: str, value) -> bool:
    """Check if a name/value pair represents a public method."""
    # Skip private methods
    if name.startswith('_'):
        return False

    # Check if it's callable (method, staticmethod, classmethod) or property
    if callable(value):
        return True
    if isinstance(value, (staticmethod, classmethod, property)):
        return True

    return False


def get_method_params(cls: Type, method_name: str, include_inherited: bool = False) -> List[str]:
    """
    Get parameter names for a method, excluding 'self'.
    """
    method = None

    if include_inherited:
        for klass in cls.__mro__:
            if klass is object:
                continue
            if method_name in klass.__dict__:
                method = klass.__dict__[method_name]
                break
    else:
        method = cls.__dict__.get(method_name)

    if method is None:
        return []

    if isinstance(method, (staticmethod, classmethod)):
        method = method.__func__
    elif isinstance(method, property):
        return []

    try:
        sig = inspect.signature(method)
        return [
            name for name in sig.parameters.keys()
            if name != 'self'
        ]
    except (ValueError, TypeError):
        return []


def compare_signatures(
    protocol_class: Type,
    impl_class: Type,
    method_names: Set[str],
    include_inherited: bool = False,
) -> List[SignatureMismatch]:
    """Compare method signatures between protocol and implementation."""
    mismatches = []

    for method_name in method_names:
        protocol_params = get_method_params(protocol_class, method_name, include_inherited=False)
        impl_params = get_method_params(impl_class, method_name, include_inherited=include_inherited)

        if not protocol_params and not impl_params:
            continue

        if protocol_params != impl_params:
            mismatches.append(SignatureMismatch(
                method_name=method_name,
                protocol_params=protocol_params,
                impl_params=impl_params,
            ))

    return mismatches


def check_alignment(
    protocol_class: Type,
    impl_class: Type,
    exclude_from_protocol: Set[str] = None,
    exclude_from_impl: Set[str] = None,
    include_inherited: bool = False,
    check_signatures: bool = True,
) -> AlignmentResult:
    """
    Check alignment between a protocol and its implementation.
    """
    exclude_from_protocol = exclude_from_protocol or set()
    exclude_from_impl = exclude_from_impl or set()

    protocol_methods = get_protocol_methods(protocol_class) - exclude_from_protocol
    impl_methods = get_implementation_methods(impl_class, include_inherited) - exclude_from_impl

    aligned_methods = protocol_methods & impl_methods

    signature_mismatches = []
    if check_signatures and aligned_methods:
        signature_mismatches = compare_signatures(
            protocol_class,
            impl_class,
            aligned_methods,
            include_inherited=include_inherited,
        )

    return AlignmentResult(
        protocol_name=protocol_class.__name__,
        implementation_name=impl_class.__name__,
        protocol_only=protocol_methods - impl_methods,
        implementation_only=impl_methods - protocol_methods,
        aligned=aligned_methods,
        signature_mismatches=signature_mismatches,
    )


# =============================================================================
# Substrait Protocol Imports
# =============================================================================

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitAggregateArithmeticExpressionSystemProtocol,
    SubstraitAggregateBooleanExpressionSystemProtocol,
    SubstraitAggregateGenericExpressionSystemProtocol,
    SubstraitAggregateStringExpressionSystemProtocol,
    SubstraitCastExpressionSystemProtocol,
    SubstraitConditionalExpressionSystemProtocol,
    SubstraitFieldReferenceExpressionSystemProtocol,
    SubstraitLiteralExpressionSystemProtocol,
    # SubstraitScalarAggregateExpressionSystemProtocol,
    SubstraitScalarArithmeticExpressionSystemProtocol,
    SubstraitScalarBooleanExpressionSystemProtocol,
    SubstraitScalarComparisonExpressionSystemProtocol,
    SubstraitScalarDatetimeExpressionSystemProtocol,
    SubstraitScalarGeometryExpressionSystemProtocol,
    SubstraitScalarLogarithmicExpressionSystemProtocol,
    SubstraitScalarRoundingExpressionSystemProtocol,
    SubstraitScalarSetExpressionSystemProtocol,
    SubstraitScalarStringExpressionSystemProtocol,
    SubstraitWindowArithmeticExpressionSystemProtocol,
)

# =============================================================================
# Mountainash Extension Protocol Imports
# =============================================================================

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshNullExpressionSystemProtocol,
    MountainAshNameExpressionSystemProtocol,
    MountainAshScalarArithmeticExpressionSystemProtocol,
    MountainAshScalarBooleanExpressionSystemProtocol,
    MountainAshScalarDatetimeExpressionSystemProtocol,
    MountainAshScalarListExpressionSystemProtocol,
    MountainAshScalarSetExpressionSystemProtocol,
    MountainAshScalarStringExpressionSystemProtocol,
    MountainAshScalarStructExpressionSystemProtocol,
    MountainAshScalarTernaryExpressionSystemProtocol,
    # MountainAshScalarAggregateExpressionSystemProtocol,
    MountainashExtensionAggregateExpressionSystemProtocol,
    MountainashWindowExpressionSystemProtocol,
)

# =============================================================================
# Polars Backend Implementation Imports
# =============================================================================

from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_cast import SubstraitPolarsCastExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_conditional import SubstraitPolarsConditionalExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_field_reference import SubstraitPolarsFieldReferenceExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_literal import SubstraitPolarsLiteralExpressionSystem
# from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_scalar_aggregate import SubstraitPolarsScalarAggregateExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_scalar_arithmetic import SubstraitPolarsScalarArithmeticExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_scalar_boolean import SubstraitPolarsScalarBooleanExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_scalar_comparison import SubstraitPolarsScalarComparisonExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_scalar_datetime import SubstraitPolarsScalarDatetimeExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_scalar_logarithmic import SubstraitPolarsScalarLogarithmicExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_scalar_rounding import SubstraitPolarsScalarRoundingExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_scalar_set import SubstraitPolarsScalarSetExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_scalar_string import SubstraitPolarsScalarStringExpressionSystem

# Polars Mountainash Extensions
from mountainash.expressions.backends.expression_systems.polars.extensions_mountainash.expsys_pl_ext_ma_null import MountainAshPolarsNullExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.extensions_mountainash.expsys_pl_ext_ma_name import MountainAshPolarsNameExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.extensions_mountainash.expsys_pl_ext_ma_scalar_arithmetic import MountainAshPolarsScalarArithmeticExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.extensions_mountainash.expsys_pl_ext_ma_scalar_datetime import MountainAshPolarsScalarDatetimeExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.extensions_mountainash.expsys_pl_ext_ma_scalar_boolean import MountainAshPolarsScalarBooleanExpressionSystem
from mountainash.expressions.backends.expression_systems.polars.extensions_mountainash.expsys_pl_ext_ma_scalar_ternary import MountainAshPolarsScalarTernaryExpressionSystem

# =============================================================================
# Ibis Backend Implementation Imports
# =============================================================================

from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_cast import SubstraitIbisCastExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_conditional import SubstraitIbisConditionalExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_field_reference import SubstraitIbisFieldReferenceExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_literal import SubstraitIbisLiteralExpressionSystem
# from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_scalar_aggregate import SubstraitIbisScalarAggregateExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_scalar_arithmetic import SubstraitIbisScalarArithmeticExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_scalar_boolean import SubstraitIbisScalarBooleanExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_scalar_comparison import SubstraitIbisScalarComparisonExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_scalar_datetime import SubstraitIbisScalarDatetimeExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_scalar_logarithmic import SubstraitIbisScalarLogarithmicExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_scalar_rounding import SubstraitIbisScalarRoundingExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_scalar_set import SubstraitIbisScalarSetExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_scalar_string import SubstraitIbisScalarStringExpressionSystem

# Ibis Mountainash Extensions
from mountainash.expressions.backends.expression_systems.ibis.extensions_mountainash.expsys_ib_ext_ma_null import MountainAshIbisNullExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.extensions_mountainash.expsys_ib_ext_ma_name import MountainAshIbisNameExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.extensions_mountainash.expsys_ib_ext_ma_scalar_arithmetic import MountainAshIbisScalarArithmeticExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.extensions_mountainash.expsys_ib_ext_ma_scalar_datetime import MountainAshIbisScalarDatetimeExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.extensions_mountainash.expsys_ib_ext_ma_scalar_boolean import MountainAshIbisScalarBooleanExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.extensions_mountainash.expsys_ib_ext_ma_scalar_ternary import MountainAshIbisScalarTernaryExpressionSystem

# =============================================================================
# Narwhals Backend Implementation Imports
# =============================================================================

from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_cast import SubstraitNarwhalsCastExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_conditional import SubstraitNarwhalsConditionalExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_field_reference import SubstraitNarwhalsFieldReferenceExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_literal import SubstraitNarwhalsLiteralExpressionSystem
# from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_scalar_aggregate import SubstraitNarwhalsScalarAggregateExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_scalar_arithmetic import SubstraitNarwhalsScalarArithmeticExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_scalar_boolean import SubstraitNarwhalsScalarBooleanExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_scalar_comparison import SubstraitNarwhalsScalarComparisonExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_scalar_datetime import SubstraitNarwhalsScalarDatetimeExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_scalar_logarithmic import SubstraitNarwhalsScalarLogarithmicExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_scalar_rounding import SubstraitNarwhalsScalarRoundingExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_scalar_set import SubstraitNarwhalsScalarSetExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_scalar_string import SubstraitNarwhalsScalarStringExpressionSystem

# Narwhals Mountainash Extensions
from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_null import MountainAshNarwhalsNullExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_name import MountainAshNarwhalsNameExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_arithmetic import MountainAshNarwhalsScalarArithmeticExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_boolean import MountainAshNarwhalsScalarBooleanExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_datetime import MountainAshNarwhalsScalarDatetimeExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_ternary import MountainAshNarwhalsScalarTernaryExpressionSystem

# Composed backend classes (for wiring audit)
from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis import IbisExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals import NarwhalsExpressionSystem


# =============================================================================
# Substrait API Builder Protocol Imports
# =============================================================================

from mountainash.expressions.core.expression_protocols.api_builders.substrait import (
    SubstraitCastAPIBuilderProtocol,
    SubstraitConditionalAPIBuilderProtocol,
    SubstraitFieldReferenceAPIBuilderProtocol,
    SubstraitLiteralAPIBuilderProtocol,
    # SubstraitScalarAggregateAPIBuilderProtocol,
    SubstraitScalarArithmeticAPIBuilderProtocol,
    SubstraitScalarBooleanAPIBuilderProtocol,
    SubstraitScalarComparisonAPIBuilderProtocol,
    SubstraitScalarDatetimeAPIBuilderProtocol,
    SubstraitScalarLogarithmicAPIBuilderProtocol,
    SubstraitScalarRoundingAPIBuilderProtocol,
    SubstraitScalarSetAPIBuilderProtocol,
    SubstraitScalarStringAPIBuilderProtocol,
)

# =============================================================================
# Mountainash API Builder Protocol Imports
# =============================================================================

from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import (
    MountainAshNameAPIBuilderProtocol,
    MountainAshNullAPIBuilderProtocol,
    # MountainAshScalarAggregateAPIBuilderProtocol,
    MountainAshScalarArithmeticAPIBuilderProtocol,
    MountainAshScalarDatetimeAPIBuilderProtocol,
    MountainAshScalarBooleanAPIBuilderProtocol,
    MountainAshScalarTernaryAPIBuilderProtocol,
)

# =============================================================================
# Substrait API Builder Implementation Imports
# =============================================================================

from mountainash.expressions.core.expression_api.api_builders.substrait import (
    SubstraitCastAPIBuilder,
    SubstraitConditionalAPIBuilder,
    SubstraitFieldReferenceAPIBuilder,
    SubstraitLiteralAPIBuilder,
    # SubstraitScalarAggregateAPIBuilder,
    SubstraitScalarArithmeticAPIBuilder,
    SubstraitScalarBooleanAPIBuilder,
    SubstraitScalarComparisonAPIBuilder,
    SubstraitScalarDatetimeAPIBuilder,
    SubstraitScalarLogarithmicAPIBuilder,
    SubstraitScalarRoundingAPIBuilder,
    SubstraitScalarSetAPIBuilder,
    SubstraitScalarStringAPIBuilder,
)

# =============================================================================
# Mountainash API Builder Implementation Imports
# =============================================================================

from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash.api_bldr_ext_ma_name import MountainAshNameAPIBuilder
from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash.api_bldr_ext_ma_null import MountainAshNullAPIBuilder
# from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash.api_bldr_ext_ma_scalar_aggregate import MountainAshScalarAggregateAPIBuilder
from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash.api_bldr_ext_ma_scalar_arithmetic import MountainAshScalarArithmeticAPIBuilder
from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash.api_bldr_ext_ma_scalar_datetime import MountainAshScalarDatetimeAPIBuilder
from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash.api_bldr_ext_ma_scalar_boolean import MountainAshScalarBooleanAPIBuilder
from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash.api_bldr_ext_ma_scalar_ternary import MountainAshScalarTernaryAPIBuilder


# =============================================================================
# Substrait Protocol Alignment Definitions
# =============================================================================

SUBSTRAIT_PROTOCOLS = [
    # Foundation
    (SubstraitCastExpressionSystemProtocol, "cast"),
    (SubstraitConditionalExpressionSystemProtocol, "conditional"),
    (SubstraitFieldReferenceExpressionSystemProtocol, "field_reference"),
    (SubstraitLiteralExpressionSystemProtocol, "literal"),
    # Scalar
    # (SubstraitScalarAggregateExpressionSystemProtocol, "scalar_aggregate"),
    (SubstraitScalarArithmeticExpressionSystemProtocol, "scalar_arithmetic"),
    (SubstraitScalarBooleanExpressionSystemProtocol, "scalar_boolean"),
    (SubstraitScalarComparisonExpressionSystemProtocol, "scalar_comparison"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "scalar_datetime"),
    (SubstraitScalarLogarithmicExpressionSystemProtocol, "scalar_logarithmic"),
    (SubstraitScalarRoundingExpressionSystemProtocol, "scalar_rounding"),
    (SubstraitScalarSetExpressionSystemProtocol, "scalar_set"),
    (SubstraitScalarStringExpressionSystemProtocol, "scalar_string"),
]

POLARS_SUBSTRAIT_IMPLEMENTATIONS = {
    "cast": SubstraitPolarsCastExpressionSystem,
    "conditional": SubstraitPolarsConditionalExpressionSystem,
    "field_reference": SubstraitPolarsFieldReferenceExpressionSystem,
    "literal": SubstraitPolarsLiteralExpressionSystem,
    # "scalar_aggregate": SubstraitPolarsScalarAggregateExpressionSystem,
    "scalar_arithmetic": SubstraitPolarsScalarArithmeticExpressionSystem,
    "scalar_boolean": SubstraitPolarsScalarBooleanExpressionSystem,
    "scalar_comparison": SubstraitPolarsScalarComparisonExpressionSystem,
    "scalar_datetime": SubstraitPolarsScalarDatetimeExpressionSystem,
    "scalar_logarithmic": SubstraitPolarsScalarLogarithmicExpressionSystem,
    "scalar_rounding": SubstraitPolarsScalarRoundingExpressionSystem,
    "scalar_set": SubstraitPolarsScalarSetExpressionSystem,
    "scalar_string": SubstraitPolarsScalarStringExpressionSystem,
}

IBIS_SUBSTRAIT_IMPLEMENTATIONS = {
    "cast": SubstraitIbisCastExpressionSystem,
    "conditional": SubstraitIbisConditionalExpressionSystem,
    "field_reference": SubstraitIbisFieldReferenceExpressionSystem,
    "literal": SubstraitIbisLiteralExpressionSystem,
    # "scalar_aggregate": SubstraitIbisScalarAggregateExpressionSystem,
    "scalar_arithmetic": SubstraitIbisScalarArithmeticExpressionSystem,
    "scalar_boolean": SubstraitIbisScalarBooleanExpressionSystem,
    "scalar_comparison": SubstraitIbisScalarComparisonExpressionSystem,
    "scalar_datetime": SubstraitIbisScalarDatetimeExpressionSystem,
    "scalar_logarithmic": SubstraitIbisScalarLogarithmicExpressionSystem,
    "scalar_rounding": SubstraitIbisScalarRoundingExpressionSystem,
    "scalar_set": SubstraitIbisScalarSetExpressionSystem,
    "scalar_string": SubstraitIbisScalarStringExpressionSystem,
}

NARWHALS_SUBSTRAIT_IMPLEMENTATIONS = {
    "cast": SubstraitNarwhalsCastExpressionSystem,
    "conditional": SubstraitNarwhalsConditionalExpressionSystem,
    "field_reference": SubstraitNarwhalsFieldReferenceExpressionSystem,
    "literal": SubstraitNarwhalsLiteralExpressionSystem,
    # "scalar_aggregate": SubstraitNarwhalsScalarAggregateExpressionSystem,
    "scalar_arithmetic": SubstraitNarwhalsScalarArithmeticExpressionSystem,
    "scalar_boolean": SubstraitNarwhalsScalarBooleanExpressionSystem,
    "scalar_comparison": SubstraitNarwhalsScalarComparisonExpressionSystem,
    "scalar_datetime": SubstraitNarwhalsScalarDatetimeExpressionSystem,
    "scalar_logarithmic": SubstraitNarwhalsScalarLogarithmicExpressionSystem,
    "scalar_rounding": SubstraitNarwhalsScalarRoundingExpressionSystem,
    "scalar_set": SubstraitNarwhalsScalarSetExpressionSystem,
    "scalar_string": SubstraitNarwhalsScalarStringExpressionSystem,
}

# =============================================================================
# Mountainash Extension Alignment Definitions
# =============================================================================

MOUNTAINASH_PROTOCOLS = [
    (MountainAshNullExpressionSystemProtocol, "null"),
    (MountainAshNameExpressionSystemProtocol, "name"),
    (MountainAshScalarArithmeticExpressionSystemProtocol, "scalar_arithmetic"),
    (MountainAshScalarBooleanExpressionSystemProtocol, "scalar_boolean"),
    (MountainAshScalarDatetimeExpressionSystemProtocol, "scalar_datetime"),
    (MountainAshScalarTernaryExpressionSystemProtocol, "scalar_ternary"),
    # (MountainAshScalarAggregateExpressionSystemProtocol, "scalar_aggregate"),
]

POLARS_MOUNTAINASH_IMPLEMENTATIONS = {
    "null": MountainAshPolarsNullExpressionSystem,
    "name": MountainAshPolarsNameExpressionSystem,
    "scalar_arithmetic": MountainAshPolarsScalarArithmeticExpressionSystem,
    "scalar_boolean": MountainAshPolarsScalarBooleanExpressionSystem,
    "scalar_datetime": MountainAshPolarsScalarDatetimeExpressionSystem,
    "scalar_ternary": MountainAshPolarsScalarTernaryExpressionSystem,
}

IBIS_MOUNTAINASH_IMPLEMENTATIONS = {
    "null": MountainAshIbisNullExpressionSystem,
    "name": MountainAshIbisNameExpressionSystem,
    "scalar_arithmetic": MountainAshIbisScalarArithmeticExpressionSystem,
    "scalar_boolean": MountainAshIbisScalarBooleanExpressionSystem,
    "scalar_datetime": MountainAshIbisScalarDatetimeExpressionSystem,
    "scalar_ternary": MountainAshIbisScalarTernaryExpressionSystem,
}

NARWHALS_MOUNTAINASH_IMPLEMENTATIONS = {
    "null": MountainAshNarwhalsNullExpressionSystem,
    "name": MountainAshNarwhalsNameExpressionSystem,
    "scalar_arithmetic": MountainAshNarwhalsScalarArithmeticExpressionSystem,
    "scalar_boolean": MountainAshNarwhalsScalarBooleanExpressionSystem,
    "scalar_datetime": MountainAshNarwhalsScalarDatetimeExpressionSystem,
    "scalar_ternary": MountainAshNarwhalsScalarTernaryExpressionSystem,
}

# =============================================================================
# API Builder Protocol Alignment Definitions
# =============================================================================

SUBSTRAIT_API_BUILDER_PROTOCOLS = [
    # Foundation
    (SubstraitCastAPIBuilderProtocol, "cast"),
    (SubstraitConditionalAPIBuilderProtocol, "conditional"),
    (SubstraitFieldReferenceAPIBuilderProtocol, "field_reference"),
    (SubstraitLiteralAPIBuilderProtocol, "literal"),
    # Scalar
    # (SubstraitScalarAggregateAPIBuilderProtocol, "scalar_aggregate"),
    (SubstraitScalarArithmeticAPIBuilderProtocol, "scalar_arithmetic"),
    (SubstraitScalarBooleanAPIBuilderProtocol, "scalar_boolean"),
    (SubstraitScalarComparisonAPIBuilderProtocol, "scalar_comparison"),
    (SubstraitScalarDatetimeAPIBuilderProtocol, "scalar_datetime"),
    (SubstraitScalarLogarithmicAPIBuilderProtocol, "scalar_logarithmic"),
    (SubstraitScalarRoundingAPIBuilderProtocol, "scalar_rounding"),
    (SubstraitScalarSetAPIBuilderProtocol, "scalar_set"),
    (SubstraitScalarStringAPIBuilderProtocol, "scalar_string"),
]

SUBSTRAIT_API_BUILDER_IMPLEMENTATIONS = {
    "cast": SubstraitCastAPIBuilder,
    "conditional": SubstraitConditionalAPIBuilder,
    "field_reference": SubstraitFieldReferenceAPIBuilder,
    "literal": SubstraitLiteralAPIBuilder,
    # "scalar_aggregate": SubstraitScalarAggregateAPIBuilder,
    "scalar_arithmetic": SubstraitScalarArithmeticAPIBuilder,
    "scalar_boolean": SubstraitScalarBooleanAPIBuilder,
    "scalar_comparison": SubstraitScalarComparisonAPIBuilder,
    "scalar_datetime": SubstraitScalarDatetimeAPIBuilder,
    "scalar_logarithmic": SubstraitScalarLogarithmicAPIBuilder,
    "scalar_rounding": SubstraitScalarRoundingAPIBuilder,
    "scalar_set": SubstraitScalarSetAPIBuilder,
    "scalar_string": SubstraitScalarStringAPIBuilder,
}

MOUNTAINASH_API_BUILDER_PROTOCOLS = [
    (MountainAshNameAPIBuilderProtocol, "name"),
    (MountainAshNullAPIBuilderProtocol, "null"),
    # (MountainAshScalarAggregateAPIBuilderProtocol, "scalar_aggregate"),
    (MountainAshScalarArithmeticAPIBuilderProtocol, "scalar_arithmetic"),
    (MountainAshScalarDatetimeAPIBuilderProtocol, "scalar_datetime"),
    (MountainAshScalarBooleanAPIBuilderProtocol, "scalar_boolean"),
    (MountainAshScalarTernaryAPIBuilderProtocol, "scalar_ternary"),
]

MOUNTAINASH_API_BUILDER_IMPLEMENTATIONS = {
    "name": MountainAshNameAPIBuilder,
    "null": MountainAshNullAPIBuilder,
    # "scalar_aggregate": MountainAshScalarAggregateAPIBuilder,
    "scalar_arithmetic": MountainAshScalarArithmeticAPIBuilder,
    "scalar_datetime": MountainAshScalarDatetimeAPIBuilder,
    "scalar_boolean": MountainAshScalarBooleanAPIBuilder,
    "scalar_ternary": MountainAshScalarTernaryAPIBuilder,
}


# =============================================================================
# Wiring Audit: Protocol Registry
# =============================================================================

# Maps each ExpressionSystem protocol to its category label.
# This is the source of truth for the wiring audit.
WIRING_PROTOCOL_REGISTRY = {
    SubstraitAggregateArithmeticExpressionSystemProtocol: "substrait_aggregate_arithmetic",
    SubstraitAggregateBooleanExpressionSystemProtocol: "substrait_aggregate_boolean",
    SubstraitAggregateGenericExpressionSystemProtocol: "substrait_aggregate_generic",
    SubstraitAggregateStringExpressionSystemProtocol: "substrait_aggregate_string",
    SubstraitScalarComparisonExpressionSystemProtocol: "substrait_scalar_comparison",
    SubstraitScalarBooleanExpressionSystemProtocol: "substrait_scalar_boolean",
    SubstraitScalarArithmeticExpressionSystemProtocol: "substrait_scalar_arithmetic",
    SubstraitScalarStringExpressionSystemProtocol: "substrait_scalar_string",
    SubstraitScalarDatetimeExpressionSystemProtocol: "substrait_scalar_datetime",
    SubstraitScalarGeometryExpressionSystemProtocol: "substrait_scalar_geometry",
    SubstraitScalarRoundingExpressionSystemProtocol: "substrait_scalar_rounding",
    SubstraitScalarLogarithmicExpressionSystemProtocol: "substrait_scalar_logarithmic",
    SubstraitScalarSetExpressionSystemProtocol: "substrait_scalar_set",
    SubstraitWindowArithmeticExpressionSystemProtocol: "substrait_window_arithmetic",
    SubstraitCastExpressionSystemProtocol: "substrait_cast",
    SubstraitConditionalExpressionSystemProtocol: "substrait_conditional",
    SubstraitFieldReferenceExpressionSystemProtocol: "substrait_field_reference",
    SubstraitLiteralExpressionSystemProtocol: "substrait_literal",
    MountainAshScalarTernaryExpressionSystemProtocol: "mountainash_scalar_ternary",
    MountainAshNullExpressionSystemProtocol: "mountainash_null",
    MountainAshNameExpressionSystemProtocol: "mountainash_name",
    MountainAshScalarDatetimeExpressionSystemProtocol: "mountainash_scalar_datetime",
    MountainAshScalarArithmeticExpressionSystemProtocol: "mountainash_scalar_arithmetic",
    MountainAshScalarBooleanExpressionSystemProtocol: "mountainash_scalar_boolean",
    MountainAshScalarListExpressionSystemProtocol: "mountainash_scalar_list",
    MountainAshScalarSetExpressionSystemProtocol: "mountainash_scalar_set",
    MountainAshScalarStringExpressionSystemProtocol: "mountainash_scalar_string",
    MountainAshScalarStructExpressionSystemProtocol: "mountainash_scalar_struct",
    MountainashExtensionAggregateExpressionSystemProtocol: "mountainash_aggregate",
    MountainashWindowExpressionSystemProtocol: "mountainash_window",
}


def _alignment_category(registry_category: str, prefix: str) -> str:
    return registry_category.removeprefix(prefix)


# Keep signature-alignment parametrization in lockstep with the wiring registry.
# Categories without backend implementation classes are still parametrized and
# skipped by the backend-specific alignment tests until those layers exist.
SUBSTRAIT_PROTOCOLS = [
    (protocol_cls, _alignment_category(category, "substrait_"))
    for protocol_cls, category in WIRING_PROTOCOL_REGISTRY.items()
    if category.startswith("substrait_")
]

MOUNTAINASH_PROTOCOLS = [
    (protocol_cls, _alignment_category(category, "mountainash_"))
    for protocol_cls, category in WIRING_PROTOCOL_REGISTRY.items()
    if category.startswith("mountainash_")
]

# Methods that exist in protocols but are intentionally not fully wired yet.
# Each entry maps (protocol_cls, method_name) → known gap details.
# These are xfailed in the wiring audit, not hard failures.
KNOWN_ASPIRATIONAL: dict[tuple[type, str], KnownGap] = {
    # Substrait Aggregate Arithmetic — not yet in function registry
    (SubstraitAggregateArithmeticExpressionSystemProtocol, "sum0"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    # Substrait Aggregate String — not yet in function registry
    (SubstraitAggregateStringExpressionSystemProtocol, "string_agg"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarArithmeticExpressionSystemProtocol, "factorial"): KnownGap(reason="No backend support yet", since="2026-05-12"),
    # Substrait Scalar Comparison — distinct operations
    (SubstraitScalarComparisonExpressionSystemProtocol, "is_not_distinct_from"): KnownGap(reason="No ENUM, no function mapping, no API builder", since="2026-05-12"),
    (SubstraitScalarComparisonExpressionSystemProtocol, "is_distinct_from"): KnownGap(reason="No ENUM, no function mapping, no API builder", since="2026-05-12"),
    # Substrait Scalar Datetime — most methods use Mountainash extension dispatch
    (SubstraitScalarDatetimeExpressionSystemProtocol, "add"): KnownGap(reason="Datetime dispatch via Mountainash extensions", since="2026-05-12"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "subtract"): KnownGap(reason="Datetime dispatch via Mountainash extensions", since="2026-05-12"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "multiply"): KnownGap(reason="Datetime dispatch via Mountainash extensions", since="2026-05-12"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "lt"): KnownGap(reason="Datetime comparisons handled by scalar_comparison", since="2026-05-12"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "lte"): KnownGap(reason="Datetime comparisons handled by scalar_comparison", since="2026-05-12"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "gt"): KnownGap(reason="Datetime comparisons handled by scalar_comparison", since="2026-05-12"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "gte"): KnownGap(reason="Datetime comparisons handled by scalar_comparison", since="2026-05-12"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "local_timestamp"): KnownGap(reason="No function mapping registered", since="2026-05-12"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "strptime_time"): KnownGap(reason="No function mapping registered", since="2026-05-12"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "round_temporal"): KnownGap(reason="No function mapping registered", since="2026-05-12"),
    (SubstraitScalarDatetimeExpressionSystemProtocol, "round_calendar"): KnownGap(reason="No function mapping registered", since="2026-05-12"),
    # Substrait Scalar Geometry — not yet in function registry
    (SubstraitScalarGeometryExpressionSystemProtocol, "buffer"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "centroid"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "collection_extract"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "dimension"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "envelope"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "flip_coordinates"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "geometry_type"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "is_closed"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "is_empty"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "is_ring"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "is_simple"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "is_valid"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "make_line"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "minimum_bounding_circle"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "num_points"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "point"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "remove_repeated_points"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "x_coordinate"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    (SubstraitScalarGeometryExpressionSystemProtocol, "y_coordinate"): KnownGap(reason="No function mapping registered yet", since="2026-05-12"),
    # Substrait Field Reference / Literal — special node types, not ScalarFunctionNode
    (SubstraitFieldReferenceExpressionSystemProtocol, "col"): KnownGap(reason="Special node type (FieldReferenceNode), not dispatched via function registry", since="2026-05-12"),
    (SubstraitLiteralExpressionSystemProtocol, "lit"): KnownGap(reason="Special node type (LiteralNode), not dispatched via function registry", since="2026-05-12"),
    # Mountainash Scalar Datetime — methods not yet in function registry
    (MountainAshScalarDatetimeExpressionSystemProtocol, "assume_timezone"): KnownGap(reason="No function mapping registered", since="2026-05-12"),
    (MountainAshScalarDatetimeExpressionSystemProtocol, "extract"): KnownGap(reason="No function mapping registered", since="2026-05-12"),
    (MountainAshScalarDatetimeExpressionSystemProtocol, "extract_boolean"): KnownGap(reason="No function mapping registered", since="2026-05-12"),
    (MountainAshScalarDatetimeExpressionSystemProtocol, "strftime"): KnownGap(reason="No function mapping registered", since="2026-05-12"),
    (MountainAshScalarDatetimeExpressionSystemProtocol, "to_timezone"): KnownGap(reason="No function mapping registered", since="2026-05-12"),
}

KNOWN_ASPIRATIONAL_AND_TESTED: dict[tuple[type, str], KnownGap] = {
    (SubstraitFieldReferenceExpressionSystemProtocol, "col"): KnownGap(
        reason="Argument channel is tested, but expression node is intentionally not registry-dispatched",
        since="2026-05-12",
    ),
    (SubstraitLiteralExpressionSystemProtocol, "lit"): KnownGap(
        reason="Argument channel is tested, but literal node is intentionally not registry-dispatched",
        since="2026-05-12",
    ),
}


# =============================================================================
# Test Classes
# =============================================================================

class TestSubstraitProtocolAlignment:
    """Test that Substrait backend implementations align with their protocols."""

    # Methods that are infrastructure, not operations
    BACKEND_INFRASTRUCTURE = {'backend_type', 'is_native_expression'}

    @pytest.mark.parametrize("protocol,category", SUBSTRAIT_PROTOCOLS)
    def test_polars_substrait_alignment(self, protocol, category):
        """Polars Substrait implementations should align with protocols."""
        if category not in POLARS_SUBSTRAIT_IMPLEMENTATIONS:
            pytest.skip(f"Polars implementation for {category} not found")

        implementation = POLARS_SUBSTRAIT_IMPLEMENTATIONS[category]
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.BACKEND_INFRASTRUCTURE,
            exclude_from_impl=self.BACKEND_INFRASTRUCTURE,
            include_inherited=False,
            check_signatures=True,
        )

        if not result.is_aligned:
            pytest.fail(str(result))

    @pytest.mark.parametrize("protocol,category", SUBSTRAIT_PROTOCOLS)
    def test_ibis_substrait_alignment(self, protocol, category):
        """Ibis Substrait implementations should align with protocols."""
        if category not in IBIS_SUBSTRAIT_IMPLEMENTATIONS:
            pytest.skip(f"Ibis implementation for {category} not found")

        implementation = IBIS_SUBSTRAIT_IMPLEMENTATIONS[category]
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.BACKEND_INFRASTRUCTURE,
            exclude_from_impl=self.BACKEND_INFRASTRUCTURE,
            include_inherited=False,
            check_signatures=True,
        )

        if not result.is_aligned:
            pytest.fail(str(result))

    @pytest.mark.parametrize("protocol,category", SUBSTRAIT_PROTOCOLS)
    def test_narwhals_substrait_alignment(self, protocol, category):
        """Narwhals Substrait implementations should align with protocols."""
        if category not in NARWHALS_SUBSTRAIT_IMPLEMENTATIONS:
            pytest.skip(f"Narwhals implementation for {category} not found")

        implementation = NARWHALS_SUBSTRAIT_IMPLEMENTATIONS[category]
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.BACKEND_INFRASTRUCTURE,
            exclude_from_impl=self.BACKEND_INFRASTRUCTURE,
            include_inherited=False,
            check_signatures=True,
        )

        if not result.is_aligned:
            pytest.fail(str(result))


class TestMountainashExtensionAlignment:
    """Test that Mountainash extension implementations align with their protocols."""

    BACKEND_INFRASTRUCTURE = {'backend_type', 'is_native_expression'}

    @pytest.mark.parametrize("protocol,category", MOUNTAINASH_PROTOCOLS)
    def test_polars_mountainash_alignment(self, protocol, category):
        """Polars Mountainash implementations should align with protocols."""
        if category not in POLARS_MOUNTAINASH_IMPLEMENTATIONS:
            pytest.skip(f"Polars Mountainash implementation for {category} not found")

        implementation = POLARS_MOUNTAINASH_IMPLEMENTATIONS[category]
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.BACKEND_INFRASTRUCTURE,
            exclude_from_impl=self.BACKEND_INFRASTRUCTURE,
            include_inherited=False,
            check_signatures=True,
        )

        if not result.is_aligned:
            pytest.fail(str(result))

    @pytest.mark.parametrize("protocol,category", MOUNTAINASH_PROTOCOLS)
    def test_ibis_mountainash_alignment(self, protocol, category):
        """Ibis Mountainash implementations should align with protocols."""
        if category not in IBIS_MOUNTAINASH_IMPLEMENTATIONS:
            pytest.skip(f"Ibis Mountainash implementation for {category} not found")

        implementation = IBIS_MOUNTAINASH_IMPLEMENTATIONS[category]
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.BACKEND_INFRASTRUCTURE,
            exclude_from_impl=self.BACKEND_INFRASTRUCTURE,
            include_inherited=False,
            check_signatures=True,
        )

        if not result.is_aligned:
            pytest.fail(str(result))

    @pytest.mark.parametrize("protocol,category", MOUNTAINASH_PROTOCOLS)
    def test_narwhals_mountainash_alignment(self, protocol, category):
        """Narwhals Mountainash implementations should align with protocols."""
        if category not in NARWHALS_MOUNTAINASH_IMPLEMENTATIONS:
            pytest.skip(f"Narwhals Mountainash implementation for {category} not found")

        implementation = NARWHALS_MOUNTAINASH_IMPLEMENTATIONS[category]
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.BACKEND_INFRASTRUCTURE,
            exclude_from_impl=self.BACKEND_INFRASTRUCTURE,
            include_inherited=False,
            check_signatures=True,
        )

        if not result.is_aligned:
            pytest.fail(str(result))


class TestSubstraitAPIBuilderAlignment:
    """Test that Substrait API builder implementations align with their protocols."""

    # Methods that are infrastructure, not operations
    API_BUILDER_INFRASTRUCTURE = {'_api', '_node', '_build', '_to_node_or_value', '_resolve_to_node'}

    @pytest.mark.parametrize("protocol,category", SUBSTRAIT_API_BUILDER_PROTOCOLS)
    def test_substrait_api_builder_alignment(self, protocol, category):
        """Substrait API builder implementations should align with protocols."""
        if category not in SUBSTRAIT_API_BUILDER_IMPLEMENTATIONS:
            pytest.skip(f"Substrait API builder implementation for {category} not found")

        implementation = SUBSTRAIT_API_BUILDER_IMPLEMENTATIONS[category]
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.API_BUILDER_INFRASTRUCTURE,
            exclude_from_impl=self.API_BUILDER_INFRASTRUCTURE,
            include_inherited=True,  # API builders inherit from base
            check_signatures=True,
        )

        if not result.is_aligned:
            pytest.fail(str(result))


class TestMountainashAPIBuilderAlignment:
    """Test that Mountainash API builder implementations align with their protocols."""

    API_BUILDER_INFRASTRUCTURE = {'_api', '_node', '_build', '_to_node_or_value', '_resolve_to_node'}

    @pytest.mark.parametrize("protocol,category", MOUNTAINASH_API_BUILDER_PROTOCOLS)
    def test_mountainash_api_builder_alignment(self, protocol, category):
        """Mountainash API builder implementations should align with protocols."""
        if category not in MOUNTAINASH_API_BUILDER_IMPLEMENTATIONS:
            pytest.skip(f"Mountainash API builder implementation for {category} not found")

        implementation = MOUNTAINASH_API_BUILDER_IMPLEMENTATIONS[category]
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.API_BUILDER_INFRASTRUCTURE,
            exclude_from_impl=self.API_BUILDER_INFRASTRUCTURE,
            include_inherited=True,  # API builders inherit from base
            check_signatures=True,
        )

        if not result.is_aligned:
            pytest.fail(str(result))


# =============================================================================
# Comprehensive Alignment Report (for debugging)
# =============================================================================

class TestGenerateAlignmentReport:
    """Generate a comprehensive alignment report for all protocol layers."""

    def test_generate_full_report(self):
        """
        Generate alignment report for all protocols.

        This test always passes but prints a detailed report.
        Run with: pytest -s tests/unit/test_protocol_alignment.py::TestGenerateAlignmentReport
        """
        print("\n" + "="*80)
        print("SUBSTRAIT-ALIGNED PROTOCOL ALIGNMENT REPORT")
        print("="*80)

        print("\n--- SUBSTRAIT PROTOCOLS: POLARS ---")
        for protocol, category in SUBSTRAIT_PROTOCOLS:
            if category in POLARS_SUBSTRAIT_IMPLEMENTATIONS:
                impl = POLARS_SUBSTRAIT_IMPLEMENTATIONS[category]
                result = check_alignment(protocol, impl, include_inherited=False)
                if not result.is_aligned:
                    print(result)
                else:
                    print(f"  ✓ {category}: {len(result.aligned)} methods aligned")

        print("\n--- SUBSTRAIT PROTOCOLS: IBIS ---")
        for protocol, category in SUBSTRAIT_PROTOCOLS:
            if category in IBIS_SUBSTRAIT_IMPLEMENTATIONS:
                impl = IBIS_SUBSTRAIT_IMPLEMENTATIONS[category]
                result = check_alignment(protocol, impl, include_inherited=False)
                if not result.is_aligned:
                    print(result)
                else:
                    print(f"  ✓ {category}: {len(result.aligned)} methods aligned")

        print("\n--- SUBSTRAIT PROTOCOLS: NARWHALS ---")
        for protocol, category in SUBSTRAIT_PROTOCOLS:
            if category in NARWHALS_SUBSTRAIT_IMPLEMENTATIONS:
                impl = NARWHALS_SUBSTRAIT_IMPLEMENTATIONS[category]
                result = check_alignment(protocol, impl, include_inherited=False)
                if not result.is_aligned:
                    print(result)
                else:
                    print(f"  ✓ {category}: {len(result.aligned)} methods aligned")

        print("\n--- MOUNTAINASH EXTENSIONS: POLARS ---")
        for protocol, category in MOUNTAINASH_PROTOCOLS:
            if category in POLARS_MOUNTAINASH_IMPLEMENTATIONS:
                impl = POLARS_MOUNTAINASH_IMPLEMENTATIONS[category]
                result = check_alignment(protocol, impl, include_inherited=False)
                if not result.is_aligned:
                    print(result)
                else:
                    print(f"  ✓ {category}: {len(result.aligned)} methods aligned")

        print("\n--- MOUNTAINASH EXTENSIONS: IBIS ---")
        for protocol, category in MOUNTAINASH_PROTOCOLS:
            if category in IBIS_MOUNTAINASH_IMPLEMENTATIONS:
                impl = IBIS_MOUNTAINASH_IMPLEMENTATIONS[category]
                result = check_alignment(protocol, impl, include_inherited=False)
                if not result.is_aligned:
                    print(result)
                else:
                    print(f"  ✓ {category}: {len(result.aligned)} methods aligned")

        print("\n--- MOUNTAINASH EXTENSIONS: NARWHALS ---")
        for protocol, category in MOUNTAINASH_PROTOCOLS:
            if category in NARWHALS_MOUNTAINASH_IMPLEMENTATIONS:
                impl = NARWHALS_MOUNTAINASH_IMPLEMENTATIONS[category]
                result = check_alignment(protocol, impl, include_inherited=False)
                if not result.is_aligned:
                    print(result)
                else:
                    print(f"  ✓ {category}: {len(result.aligned)} methods aligned")

        print("\n--- SUBSTRAIT API BUILDERS ---")
        for protocol, category in SUBSTRAIT_API_BUILDER_PROTOCOLS:
            if category in SUBSTRAIT_API_BUILDER_IMPLEMENTATIONS:
                impl = SUBSTRAIT_API_BUILDER_IMPLEMENTATIONS[category]
                result = check_alignment(protocol, impl, include_inherited=True)
                if not result.is_aligned:
                    print(result)
                else:
                    print(f"  ✓ {category}: {len(result.aligned)} methods aligned")

        print("\n--- MOUNTAINASH API BUILDERS ---")
        for protocol, category in MOUNTAINASH_API_BUILDER_PROTOCOLS:
            if category in MOUNTAINASH_API_BUILDER_IMPLEMENTATIONS:
                impl = MOUNTAINASH_API_BUILDER_IMPLEMENTATIONS[category]
                result = check_alignment(protocol, impl, include_inherited=True)
                if not result.is_aligned:
                    print(result)
                else:
                    print(f"  ✓ {category}: {len(result.aligned)} methods aligned")

        print("\n" + "="*80)
        print("END REPORT")
        print("="*80)


# =============================================================================
# Inheritance Integrity Checks
# =============================================================================

def _collect_classes_from_package(package_path: str) -> List[tuple]:
    """Collect all classes from a package directory with their module paths.

    Returns list of (class, module_path_string) tuples.
    """
    results = []
    pkg = importlib.import_module(package_path)
    pkg_dir = Path(pkg.__file__).parent

    for _, module_name, _ in pkgutil.iter_modules([str(pkg_dir)]):
        if module_name.startswith("_"):
            continue
        full_module = f"{package_path}.{module_name}"
        try:
            mod = importlib.import_module(full_module)
        except Exception:
            continue
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (
                isinstance(attr, type)
                and attr.__module__ == full_module
                and not attr_name.startswith("_")
            ):
                results.append((attr, full_module))
    return results


def _check_function_registry(protocol_cls: type, method_name: str) -> bool:
    """Check if a FunctionRegistry entry exists that references this protocol method.

    Walks all registered ExpressionFunctionDef entries and checks if any
    has a protocol_method whose __qualname__ matches the protocol class and method.

    Also handles aliased protocol classes (e.g., MountainAshScalarSetExpressionSystemProtocol
    is an alias for SubstraitScalarSetExpressionSystemProtocol) by falling back to
    identity comparison when qualname matching fails.

    Returns True if a matching registration exists, False otherwise.
    """
    from mountainash.expressions.core.expression_system.function_mapping.registry import ExpressionFunctionRegistry

    # Ensure registry is initialized
    all_keys = ExpressionFunctionRegistry.list_all()

    # Get the actual method object from the protocol class for identity comparison
    target_method = getattr(protocol_cls, method_name, None)

    for key in all_keys:
        func_def = ExpressionFunctionRegistry.get(key)
        if func_def.protocol_method is None:
            continue
        pm = func_def.protocol_method

        # Primary check: qualname matching
        qualname = getattr(pm, "__qualname__", "")
        if "." in qualname:
            cls_part, method_part = qualname.rsplit(".", 1)
            if cls_part == protocol_cls.__name__ and method_part == method_name:
                return True

        # Fallback: identity comparison (handles aliased protocol classes)
        if target_method is not None and pm is target_method:
            return True

    return False


def _get_all_enum_classes() -> list:
    """Collect all FKEY_* enum values from function_keys/enums.py.

    Returns a flat list of all enum members across all FKEY_SUBSTRAIT_*
    and FKEY_MOUNTAINASH_* enum classes.
    """
    from enum import Enum as StdEnum
    import mountainash.expressions.core.expression_system.function_keys.enums as enums_module

    all_values = []
    for attr_name in dir(enums_module):
        if not attr_name.startswith("FKEY_"):
            continue
        attr = getattr(enums_module, attr_name)
        if isinstance(attr, type) and issubclass(attr, StdEnum):
            all_values.extend(attr)
    return all_values


class TestInheritanceIntegrity:
    """Verify that classes inherit from the correct protocol layer.

    These checks prevent copy-paste errors where an extension class
    inherits from a Substrait protocol (or vice versa), and naming
    errors where a class name doesn't match its directory location.
    """

    # -----------------------------------------------------------------
    # Check 1: Classes in extensions_mountainash/ must not inherit
    # from Substrait protocols
    # -----------------------------------------------------------------

    def _get_substrait_protocol_names(self) -> set:
        """Get names of all Substrait protocol classes."""
        names = set()
        for protocol, _ in SUBSTRAIT_PROTOCOLS:
            names.add(protocol.__name__)
        for protocol, _ in SUBSTRAIT_API_BUILDER_PROTOCOLS:
            names.add(protocol.__name__)
        return names

    def test_extension_api_builders_do_not_inherit_substrait_protocols(self):
        """Classes in api_builders/extensions_mountainash/ must not inherit Substrait protocols."""
        substrait_names = self._get_substrait_protocol_names()
        violations = []

        classes = _collect_classes_from_package(
            "mountainash.expressions.core.expression_api.api_builders.extensions_mountainash"
        )
        for cls, module_path in classes:
            for base in cls.__mro__[1:]:  # skip the class itself
                if base.__name__ in substrait_names:
                    violations.append(
                        f"{cls.__name__} (in {module_path}) inherits "
                        f"Substrait protocol {base.__name__}"
                    )

        if violations:
            pytest.fail(
                "Extension classes must not inherit Substrait protocols "
                "(likely copy-paste error):\n  " + "\n  ".join(violations)
            )

    def test_extension_backend_impls_do_not_inherit_substrait_protocols(self):
        """Classes in backends/.../extensions_mountainash/ must not inherit Substrait protocols."""
        substrait_names = self._get_substrait_protocol_names()
        violations = []

        for backend in ("polars", "ibis", "narwhals"):
            pkg = f"mountainash.expressions.backends.expression_systems.{backend}.extensions_mountainash"
            try:
                classes = _collect_classes_from_package(pkg)
            except Exception:
                continue
            for cls, module_path in classes:
                for base in cls.__mro__[1:]:
                    if base.__name__ in substrait_names:
                        violations.append(
                            f"{cls.__name__} (in {module_path}) inherits "
                            f"Substrait protocol {base.__name__}"
                        )

        if violations:
            pytest.fail(
                "Extension backend classes must not inherit Substrait protocols "
                "(likely copy-paste error):\n  " + "\n  ".join(violations)
            )

    # -----------------------------------------------------------------
    # Check 2: Class names must match their directory location
    # -----------------------------------------------------------------

    def test_extension_classes_not_named_substrait(self):
        """Classes in extensions_mountainash/ directories must not be named Substrait*."""
        violations = []

        # API builders
        classes = _collect_classes_from_package(
            "mountainash.expressions.core.expression_api.api_builders.extensions_mountainash"
        )
        for cls, module_path in classes:
            if cls.__name__.startswith("Substrait"):
                violations.append(f"{cls.__name__} (in {module_path})")

        # Backend implementations
        for backend in ("polars", "ibis", "narwhals"):
            pkg = f"mountainash.expressions.backends.expression_systems.{backend}.extensions_mountainash"
            try:
                classes = _collect_classes_from_package(pkg)
            except Exception:
                continue
            for cls, module_path in classes:
                if cls.__name__.startswith("Substrait"):
                    violations.append(f"{cls.__name__} (in {module_path})")

        if violations:
            pytest.fail(
                "Classes in extensions_mountainash/ must not be named Substrait* "
                "(likely copy-paste error):\n  " + "\n  ".join(violations)
            )

    def test_substrait_classes_not_named_mountainash(self):
        """Classes in substrait/ directories must not be named MountainAsh*."""
        violations = []

        # API builders
        classes = _collect_classes_from_package(
            "mountainash.expressions.core.expression_api.api_builders.substrait"
        )
        for cls, module_path in classes:
            if cls.__name__.startswith("MountainAsh"):
                violations.append(f"{cls.__name__} (in {module_path})")

        # Backend implementations
        for backend in ("polars", "ibis", "narwhals"):
            pkg = f"mountainash.expressions.backends.expression_systems.{backend}.substrait"
            try:
                classes = _collect_classes_from_package(pkg)
            except Exception:
                continue
            for cls, module_path in classes:
                if cls.__name__.startswith("MountainAsh"):
                    violations.append(f"{cls.__name__} (in {module_path})")

        if violations:
            pytest.fail(
                "Classes in substrait/ must not be named MountainAsh* "
                "(likely copy-paste error):\n  " + "\n  ".join(violations)
            )

    # -----------------------------------------------------------------
    # Check 3: No duplicate class names across sibling directories
    # -----------------------------------------------------------------

    def test_no_duplicate_class_names_across_substrait_and_extension(self):
        """A class name must not appear in both substrait/ and extensions_mountainash/."""
        violations = []

        # API builders
        substrait_classes = _collect_classes_from_package(
            "mountainash.expressions.core.expression_api.api_builders.substrait"
        )
        extension_classes = _collect_classes_from_package(
            "mountainash.expressions.core.expression_api.api_builders.extensions_mountainash"
        )
        substrait_names = {cls.__name__ for cls, _ in substrait_classes}
        for cls, module_path in extension_classes:
            if cls.__name__ in substrait_names:
                violations.append(
                    f"API builder class '{cls.__name__}' exists in both "
                    f"substrait/ and extensions_mountainash/ ({module_path})"
                )

        # Backend implementations
        for backend in ("polars", "ibis", "narwhals"):
            sub_pkg = f"mountainash.expressions.backends.expression_systems.{backend}.substrait"
            ext_pkg = f"mountainash.expressions.backends.expression_systems.{backend}.extensions_mountainash"
            try:
                sub_classes = _collect_classes_from_package(sub_pkg)
                ext_classes = _collect_classes_from_package(ext_pkg)
            except Exception:
                continue
            sub_names = {cls.__name__ for cls, _ in sub_classes}
            for cls, module_path in ext_classes:
                if cls.__name__ in sub_names:
                    violations.append(
                        f"{backend} backend class '{cls.__name__}' exists in both "
                        f"substrait/ and extensions_mountainash/ ({module_path})"
                    )

        if violations:
            pytest.fail(
                "Duplicate class names across substrait/ and extensions_mountainash/ "
                "(likely copy-paste error):\n  " + "\n  ".join(violations)
            )


# =============================================================================
# Wiring Audit
# =============================================================================

class TestWiringAudit:
    """Validate every protocol method is wired through all architecture layers.

    Starting point: ExpressionSystem protocol methods are the source of truth.
    For each protocol method, checks:
    1. Function Registry (ENUM + ExpressionFunctionDef binding)
    2. Backend: Polars (method exists on composed PolarsExpressionSystem)
    3. Backend: Ibis (method exists on composed IbisExpressionSystem)
    4. Backend: Narwhals (method exists on composed NarwhalsExpressionSystem)

    Known aspirational gaps (methods intentionally not yet wired) are
    tested separately with xfail markers.
    """

    BACKENDS = {
        "Polars": PolarsExpressionSystem,
        "Ibis": IbisExpressionSystem,
        "Narwhals": NarwhalsExpressionSystem,
    }

    @pytest.mark.parametrize(
        "protocol_cls",
        list(WIRING_PROTOCOL_REGISTRY.keys()),
        ids=list(WIRING_PROTOCOL_REGISTRY.values()),
    )
    def test_all_protocol_methods_wired(self, protocol_cls):
        """For each protocol, verify all non-aspirational methods are fully wired."""
        methods = get_protocol_methods(protocol_cls)
        gaps = []

        for method_name in sorted(methods):
            key = (protocol_cls, method_name)
            if key in KNOWN_ASPIRATIONAL:
                continue  # Handled by test_aspirational_methods

            missing = []

            # Check function registry
            if not _check_function_registry(protocol_cls, method_name):
                missing.append("FunctionRegistry")

            # Check backends
            for backend_name, backend_cls in self.BACKENDS.items():
                if not hasattr(backend_cls, method_name):
                    missing.append(backend_name)

            if missing:
                gaps.append(f"  {method_name}: missing [{', '.join(missing)}]")

        assert not gaps, (
            f"\n{protocol_cls.__name__} wiring gaps:\n" + "\n".join(gaps)
        )

    @pytest.mark.parametrize(
        "protocol_cls,method_name,gap",
        [
            pytest.param(cls, method, gap, id=f"{cls.__name__}.{method}")
            for (cls, method), gap in KNOWN_ASPIRATIONAL.items()
        ],
    )
    @pytest.mark.xfail(strict=True, reason="Aspirational — not yet fully wired")
    def test_aspirational_method(self, protocol_cls, method_name, gap):
        """Aspirational methods: document and track wiring gaps."""
        missing = []

        if not _check_function_registry(protocol_cls, method_name):
            missing.append("FunctionRegistry")

        for backend_name, backend_cls in self.BACKENDS.items():
            if not hasattr(backend_cls, method_name):
                missing.append(backend_name)

        assert not missing, (
            f"{protocol_cls.__name__}.{method_name} ({gap.reason}; since {gap.since}):\n"
            f"  missing [{', '.join(missing)}]"
        )

    def test_no_orphan_enums(self):
        """Every registered ENUM should reference a protocol method."""
        from mountainash.expressions.core.expression_system.function_mapping.registry import ExpressionFunctionRegistry

        all_keys = ExpressionFunctionRegistry.list_all()
        orphans = []

        for key in all_keys:
            func_def = ExpressionFunctionRegistry.get(key)
            if func_def.protocol_method is None:
                orphans.append(f"  {key}: registered but protocol_method is None")

        assert not orphans, (
            f"\nOrphan ENUM values (no protocol method reference):\n"
            + "\n".join(orphans)
        )


# =============================================================================
# Wiring Audit Helpers
# =============================================================================

class TestWiringAuditHelpers:
    """Test the helper functions used by the wiring audit."""

    def test_check_function_registry_finds_registered_method(self):
        """A known registered method (e.g., equal) should be found."""
        found = _check_function_registry(
            SubstraitScalarComparisonExpressionSystemProtocol, "equal"
        )
        assert found is True

    def test_check_function_registry_rejects_unregistered_method(self):
        """A method not in the registry (e.g., is_not_distinct_from) should return False."""
        found = _check_function_registry(
            SubstraitScalarComparisonExpressionSystemProtocol, "is_not_distinct_from"
        )
        assert found is False

    def test_get_all_enum_classes_finds_enums(self):
        """Should discover all FKEY_* enum classes."""
        enums = _get_all_enum_classes()
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_COMPARISON,
            FKEY_MOUNTAINASH_SCALAR_TERNARY,
        )
        enum_types = {type(e) for e in enums}
        assert FKEY_SUBSTRAIT_SCALAR_COMPARISON in enum_types
        assert FKEY_MOUNTAINASH_SCALAR_TERNARY in enum_types
        assert len(enums) > 50

    def test_wiring_protocol_registry_complete(self):
        """Wiring audit registry should include every discovered expression-system protocol."""
        from cross_backend.argument_types._introspection import _iter_protocol_classes

        discovered = {protocol_cls for _, protocol_cls in _iter_protocol_classes()}
        registered = set(WIRING_PROTOCOL_REGISTRY)
        missing = discovered - registered
        extra = registered - discovered
        assert not missing, (
            "Protocols missing from WIRING_PROTOCOL_REGISTRY "
            f"(add them with aspirational entries for unwired methods): "
            f"{sorted(cls.__name__ for cls in missing)}"
        )
        assert not extra, (
            "WIRING_PROTOCOL_REGISTRY contains protocols not discovered by introspection: "
            f"{sorted(cls.__name__ for cls in extra)}"
        )

    def test_signature_alignment_protocol_lists_follow_wiring_registry(self):
        """Signature-alignment protocol lists should cover the same protocols as wiring."""
        substrait_registered = {
            protocol_cls
            for protocol_cls, category in WIRING_PROTOCOL_REGISTRY.items()
            if category.startswith("substrait_")
        }
        mountainash_registered = {
            protocol_cls
            for protocol_cls, category in WIRING_PROTOCOL_REGISTRY.items()
            if category.startswith("mountainash_")
        }
        assert {protocol for protocol, _ in SUBSTRAIT_PROTOCOLS} == substrait_registered
        assert {protocol for protocol, _ in MOUNTAINASH_PROTOCOLS} == mountainash_registered

    def test_known_aspirational_references_valid_protocols(self):
        """Every protocol class in KNOWN_ASPIRATIONAL must be in WIRING_PROTOCOL_REGISTRY."""
        for (protocol_cls, method_name), gap in KNOWN_ASPIRATIONAL.items():
            assert protocol_cls in WIRING_PROTOCOL_REGISTRY, (
                f"KNOWN_ASPIRATIONAL references {protocol_cls.__name__}.{method_name} "
                f"but that protocol is not in WIRING_PROTOCOL_REGISTRY"
            )

    def test_known_aspirational_references_real_methods(self):
        """Every method in KNOWN_ASPIRATIONAL must actually exist on the protocol."""
        for (protocol_cls, method_name), gap in KNOWN_ASPIRATIONAL.items():
            methods = get_protocol_methods(protocol_cls)
            assert method_name in methods, (
                f"KNOWN_ASPIRATIONAL references {protocol_cls.__name__}.{method_name} "
                f"but that method does not exist on the protocol"
            )

    def test_known_aspirational_entries_have_reason_and_since(self):
        for (protocol_cls, method_name), gap in KNOWN_ASPIRATIONAL.items():
            assert gap.reason.strip(), f"{protocol_cls.__name__}.{method_name} has no reason"
            date.fromisoformat(gap.since)

    def test_aspirational_methods_are_not_claimed_tested_without_exception(self):
        from cross_backend.argument_types.test_coverage_guard import (
            _collect_matrix_executed_param_refs,
            _KNOWN_TESTED_ARGUMENT_PARAM_ALIASES,
            _KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_ALIASES,
            _KNOWN_SPECIAL_NODE_UNWIRED_OPS,
        )

        tested_refs = _collect_matrix_executed_param_refs()
        tested_protocol_keys = {
            ref.protocol_param_key
            for ref in tested_refs
            if ref.protocol_name is not None
        }
        unresolved_tested_keys = {
            (ref.op_name, ref.param_name)
            for ref in tested_refs
            if ref.protocol_param_key is None
        }
        tested_param_keys = tested_protocol_keys | {
            target_key
            for source_key, target_key in _KNOWN_TESTED_ARGUMENT_PARAM_ALIASES.items()
            if source_key in tested_protocol_keys
        } | {
            target_key
            for source_key, target_key in _KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_ALIASES.items()
            if source_key in unresolved_tested_keys
        }
        tested_ops = {
            (protocol_name, op_name)
            for protocol_name, op_name, _param_name in tested_param_keys
        }
        tested_ops |= set(_KNOWN_SPECIAL_NODE_UNWIRED_OPS)
        aspirational_ops = {
            (protocol_cls.__name__, method_name)
            for (protocol_cls, method_name) in KNOWN_ASPIRATIONAL
        }
        allowed = {
            (protocol_cls.__name__, method_name)
            for (protocol_cls, method_name) in KNOWN_ASPIRATIONAL_AND_TESTED
        }
        contradictions = (tested_ops & aspirational_ops) - allowed
        stale_allowed = allowed - (tested_ops & aspirational_ops)
        assert not contradictions, (
            "Methods are both aspirational and TESTED_PARAMS-covered without an explicit exception: "
            f"{sorted(contradictions)}"
        )
        assert not stale_allowed, (
            "KNOWN_ASPIRATIONAL_AND_TESTED entries no longer need exceptions: "
            f"{sorted(stale_allowed)}"
        )

    def test_known_aspirational_staleness_warns(self):
        today = date(2026, 5, 12)
        threshold_days = 183
        for (protocol_cls, method_name), gap in KNOWN_ASPIRATIONAL.items():
            age_days = (today - date.fromisoformat(gap.since)).days
            if age_days > threshold_days:
                warnings.warn(
                    (
                        f"{protocol_cls.__name__}.{method_name} has been aspirational "
                        f"for {age_days} days: {gap.reason}"
                    ),
                    UserWarning,
                    stacklevel=2,
                )
