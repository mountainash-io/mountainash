"""
Tests for protocol-implementation alignment.

These tests ensure bidirectional consistency between protocols and their implementations:
1. All protocol methods must have implementations
2. All implementation methods must have protocols (no rogue methods)
3. Method signatures (parameter names) must match between protocol and implementation

This catches architectural drift where protocols and implementations diverge.
"""

import pytest
import inspect
from typing import Protocol, get_type_hints, Set, Dict, List, Tuple, Type
from dataclasses import dataclass, field


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
                lines.append(f"\nMISSING IN IMPLEMENTATION ({len(self.protocol_only)}):")
                for method in sorted(self.protocol_only):
                    lines.append(f"  - {method}")

            if self.implementation_only:
                lines.append(f"\nMISSING IN PROTOCOL ({len(self.implementation_only)}):")
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
    # This excludes inherited methods from Protocol base
    for name in protocol_class.__dict__:
        # Skip private methods (but keep operator dunders)
        if name.startswith('_') and not name.startswith('__'):
            continue

        # Skip all dunders except explicit operator overloads we define
        if name.startswith('__') and name.endswith('__'):
            # These are operators we explicitly define in our protocols
            operator_dunders = {
                '__add__', '__radd__', '__sub__', '__rsub__',
                '__mul__', '__rmul__', '__truediv__', '__rtruediv__',
                '__floordiv__', '__rfloordiv__', '__mod__', '__rmod__',
                '__pow__', '__rpow__', '__neg__', '__pos__',
                '__and__', '__rand__', '__or__', '__ror__',
                '__xor__', '__rxor__', '__invert__',
                '__contains__', '__getitem__', '__setitem__',
            }
            if name not in operator_dunders:
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
    # Skip private methods (but keep operator dunders)
    if name.startswith('_') and not name.startswith('__'):
        return False

    # Skip non-operator dunders
    if name.startswith('__') and name.endswith('__'):
        operator_dunders = {
            '__add__', '__radd__', '__sub__', '__rsub__',
            '__mul__', '__rmul__', '__truediv__', '__rtruediv__',
            '__floordiv__', '__rfloordiv__', '__mod__', '__rmod__',
            '__pow__', '__rpow__', '__neg__', '__pos__',
            '__and__', '__rand__', '__or__', '__ror__',
            '__xor__', '__rxor__', '__invert__',
            '__contains__', '__getitem__', '__setitem__',
        }
        if name not in operator_dunders:
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

    Args:
        cls: The class containing the method
        method_name: Name of the method
        include_inherited: Whether to search parent classes

    Returns:
        List of parameter names (excluding 'self')
    """
    method = None

    if include_inherited:
        # Search MRO for the method
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

    # Handle different method types
    if isinstance(method, (staticmethod, classmethod)):
        method = method.__func__
    elif isinstance(method, property):
        # Properties don't have meaningful signatures for comparison
        return []

    try:
        sig = inspect.signature(method)
        # Return all params except 'self'
        return [
            name for name in sig.parameters.keys()
            if name != 'self'
        ]
    except (ValueError, TypeError):
        # Can't get signature (e.g., built-in methods)
        return []


def compare_signatures(
    protocol_class: Type,
    impl_class: Type,
    method_names: Set[str],
    include_inherited: bool = False,
) -> List[SignatureMismatch]:
    """
    Compare method signatures between protocol and implementation.

    Args:
        protocol_class: The Protocol class
        impl_class: The implementation class
        method_names: Set of method names to compare
        include_inherited: Whether to search parent classes for implementation

    Returns:
        List of SignatureMismatch for methods with different parameter names
    """
    mismatches = []

    for method_name in method_names:
        protocol_params = get_method_params(protocol_class, method_name, include_inherited=False)
        impl_params = get_method_params(impl_class, method_name, include_inherited=include_inherited)

        # Skip if we couldn't get signatures (e.g., properties)
        if not protocol_params and not impl_params:
            continue

        # Compare parameter names
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

    Args:
        protocol_class: The Protocol class
        impl_class: The implementation class
        exclude_from_protocol: Methods to ignore in the protocol
        exclude_from_impl: Methods to ignore in the implementation
        include_inherited: Whether to include inherited methods in implementation
        check_signatures: Whether to also check parameter name alignment

    Returns:
        AlignmentResult with details of any misalignment
    """
    exclude_from_protocol = exclude_from_protocol or set()
    exclude_from_impl = exclude_from_impl or set()

    protocol_methods = get_protocol_methods(protocol_class) - exclude_from_protocol
    impl_methods = get_implementation_methods(impl_class, include_inherited) - exclude_from_impl

    aligned_methods = protocol_methods & impl_methods

    # Check signatures for aligned methods
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
# Protocol Imports
# =============================================================================

from mountainash_expressions.core.protocols import (
    # Arithmetic
    ArithmeticVisitorProtocol,
    ArithmeticExpressionProtocol,
    ArithmeticBuilderProtocol,
    # Boolean
    BooleanVisitorProtocol,
    BooleanExpressionProtocol,
    BooleanBuilderProtocol,
    # Core
    CoreVisitorProtocol,
    CoreExpressionProtocol,
    CoreBuilderProtocol,
    # Horizontal
    HorizontalVisitorProtocol,
    HorizontalExpressionProtocol,
    HorizontalBuilderProtocol,
    # Name
    NameVisitorProtocol,
    NameExpressionProtocol,
    NameBuilderProtocol,
    # Null
    NullVisitorProtocol,
    NullExpressionProtocol,
    NullBuilderProtocol,
    # String
    StringVisitorProtocol,
    StringExpressionProtocol,
    StringBuilderProtocol,
    # Temporal
    TemporalVisitorProtocol,
    TemporalExpressionProtocol,
    TemporalBuilderProtocol,
    # Type
    TypeVisitorProtocol,
    TypeExpressionProtocol,
    TypeBuilderProtocol,
    # Native
    NativeVisitorProtocol,
    NativeExpressionProtocol,
    NativeBuilderProtocol,
)

# =============================================================================
# Visitor Implementation Imports
# =============================================================================

from mountainash_expressions.core.expression_visitors import (
    ArithmeticExpressionVisitor,
    BooleanExpressionVisitor,
    CoreExpressionVisitor,
    HorizontalExpressionVisitor,
    NameExpressionVisitor,
    NullExpressionVisitor,
    StringExpressionVisitor,
    TemporalExpressionVisitor,
    TypeExpressionVisitor,
    NativeExpressionVisitor,
)

# =============================================================================
# Namespace Implementation Imports
# =============================================================================

from mountainash_expressions.core.namespaces import (
    ArithmeticNamespace,
    BooleanNamespace,
    HorizontalNamespace,
    NameNamespace,
    NullNamespace,
    StringNamespace,
    DateTimeNamespace,
    TypeNamespace,
    NativeNamespace,
)

# =============================================================================
# Backend Implementation Imports
# =============================================================================

# Polars
from mountainash_expressions.backends.expression_systems.polars.arithmetic import PolarsArithmeticExpressionSystem
from mountainash_expressions.backends.expression_systems.polars.boolean import PolarsBooleanExpressionSystem
from mountainash_expressions.backends.expression_systems.polars.core import PolarsCoreExpressionSystem
from mountainash_expressions.backends.expression_systems.polars.null import PolarsNullExpressionSystem
from mountainash_expressions.backends.expression_systems.polars.string import PolarsStringExpressionSystem
from mountainash_expressions.backends.expression_systems.polars.temporal import PolarsTemporalExpressionSystem
from mountainash_expressions.backends.expression_systems.polars.type import PolarsTypeExpressionSystem
from mountainash_expressions.backends.expression_systems.polars.horizontal import PolarsHorizontalExpressionSystem
from mountainash_expressions.backends.expression_systems.polars.name import PolarsNameExpressionSystem
from mountainash_expressions.backends.expression_systems.polars.native import PolarsNativeExpressionSystem

# Ibis
from mountainash_expressions.backends.expression_systems.ibis.arithmetic import IbisArithmeticExpressionSystem
from mountainash_expressions.backends.expression_systems.ibis.boolean import IbisBooleanExpressionSystem
from mountainash_expressions.backends.expression_systems.ibis.core import IbisCoreExpressionSystem
from mountainash_expressions.backends.expression_systems.ibis.null import IbisNullExpressionSystem
from mountainash_expressions.backends.expression_systems.ibis.string import IbisStringExpressionSystem
from mountainash_expressions.backends.expression_systems.ibis.temporal import IbisTemporalExpressionSystem
from mountainash_expressions.backends.expression_systems.ibis.type import IbisTypeExpressionSystem
from mountainash_expressions.backends.expression_systems.ibis.horizontal import IbisHorizontalExpressionSystem
from mountainash_expressions.backends.expression_systems.ibis.name import IbisNameExpressionSystem
from mountainash_expressions.backends.expression_systems.ibis.native import IbisNativeExpressionSystem

# Narwhals
from mountainash_expressions.backends.expression_systems.narwhals.arithmetic import NarwhalsArithmeticExpressionSystem
from mountainash_expressions.backends.expression_systems.narwhals.boolean import NarwhalsBooleanExpressionSystem
from mountainash_expressions.backends.expression_systems.narwhals.core import NarwhalsCoreExpressionSystem
from mountainash_expressions.backends.expression_systems.narwhals.null import NarwhalsNullExpressionSystem
from mountainash_expressions.backends.expression_systems.narwhals.string import NarwhalsStringExpressionSystem
from mountainash_expressions.backends.expression_systems.narwhals.temporal import NarwhalsTemporalExpressionSystem
from mountainash_expressions.backends.expression_systems.narwhals.type import NarwhalsTypeExpressionSystem
from mountainash_expressions.backends.expression_systems.narwhals.horizontal import NarwhalsHorizontalExpressionSystem
from mountainash_expressions.backends.expression_systems.narwhals.name import NarwhalsNameExpressionSystem
from mountainash_expressions.backends.expression_systems.narwhals.native import NarwhalsNativeExpressionSystem


# =============================================================================
# Test Classes
# =============================================================================

class TestVisitorProtocolAlignment:
    """Test that Visitor implementations align with VisitorProtocols."""

    # Methods that are infrastructure, not operations
    VISITOR_INFRASTRUCTURE = {#'visit_expression_node',
        'backend', 'logic_type'}

    @pytest.mark.parametrize("protocol,implementation", [
        (ArithmeticVisitorProtocol, ArithmeticExpressionVisitor),
        (BooleanVisitorProtocol, BooleanExpressionVisitor),
        (CoreVisitorProtocol, CoreExpressionVisitor),
        (HorizontalVisitorProtocol, HorizontalExpressionVisitor),
        (NameVisitorProtocol, NameExpressionVisitor),
        (NullVisitorProtocol, NullExpressionVisitor),
        (StringVisitorProtocol, StringExpressionVisitor),
        (TemporalVisitorProtocol, TemporalExpressionVisitor),
        (TypeVisitorProtocol, TypeExpressionVisitor),
        (NativeVisitorProtocol, NativeExpressionVisitor),
    ])
    def test_visitor_alignment(self, protocol, implementation):
        """Each visitor implementation should align with its protocol (method presence and signatures)."""
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.VISITOR_INFRASTRUCTURE,
            exclude_from_impl=self.VISITOR_INFRASTRUCTURE | {'_get_expr_op'},
            include_inherited=True,
            check_signatures=True,
        )

        if not result.is_aligned:
            pytest.fail(str(result))


class TestExpressionProtocolAlignment:
    """Test that Backend implementations align with ExpressionProtocols."""

    # Methods that are infrastructure, not operations
    BACKEND_INFRASTRUCTURE = {'backend_type', 'is_native_expression'}

    @pytest.mark.parametrize("protocol,implementation", [
        (ArithmeticExpressionProtocol, PolarsArithmeticExpressionSystem),
        (BooleanExpressionProtocol, PolarsBooleanExpressionSystem),
        (CoreExpressionProtocol, PolarsCoreExpressionSystem),
        (HorizontalExpressionProtocol, PolarsHorizontalExpressionSystem),
        (NameExpressionProtocol, PolarsNameExpressionSystem),
        (NullExpressionProtocol, PolarsNullExpressionSystem),
        (StringExpressionProtocol, PolarsStringExpressionSystem),
        (TemporalExpressionProtocol, PolarsTemporalExpressionSystem),
        (TypeExpressionProtocol, PolarsTypeExpressionSystem),
        (NativeExpressionProtocol, PolarsNativeExpressionSystem),
    ])
    def test_polars_backend_alignment(self, protocol, implementation):
        """Polars backend implementations should align with protocols (method presence and signatures)."""
        # Don't include_inherited because backend classes are composed
        # Each backend class only defines methods for its own protocol
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.BACKEND_INFRASTRUCTURE,
            exclude_from_impl=self.BACKEND_INFRASTRUCTURE,
            include_inherited=False,  # Only check methods defined on this specific class
            check_signatures=True,
        )

        if not result.is_aligned:
            pytest.fail(str(result))

    @pytest.mark.parametrize("protocol,implementation", [
        (ArithmeticExpressionProtocol, IbisArithmeticExpressionSystem),
        (BooleanExpressionProtocol, IbisBooleanExpressionSystem),
        (CoreExpressionProtocol, IbisCoreExpressionSystem),
        (HorizontalExpressionProtocol, IbisHorizontalExpressionSystem),
        (NameExpressionProtocol, IbisNameExpressionSystem),
        (NullExpressionProtocol, IbisNullExpressionSystem),
        (StringExpressionProtocol, IbisStringExpressionSystem),
        (TemporalExpressionProtocol, IbisTemporalExpressionSystem),
        (TypeExpressionProtocol, IbisTypeExpressionSystem),
        (NativeExpressionProtocol, IbisNativeExpressionSystem),
    ])
    def test_ibis_backend_alignment(self, protocol, implementation):
        """Ibis backend implementations should align with protocols (method presence and signatures)."""
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

    @pytest.mark.parametrize("protocol,implementation", [
        (ArithmeticExpressionProtocol, NarwhalsArithmeticExpressionSystem),
        (BooleanExpressionProtocol, NarwhalsBooleanExpressionSystem),
        (CoreExpressionProtocol, NarwhalsCoreExpressionSystem),
        (HorizontalExpressionProtocol, NarwhalsHorizontalExpressionSystem),
        (NameExpressionProtocol, NarwhalsNameExpressionSystem),
        (NullExpressionProtocol, NarwhalsNullExpressionSystem),
        (StringExpressionProtocol, NarwhalsStringExpressionSystem),
        (TemporalExpressionProtocol, NarwhalsTemporalExpressionSystem),
        (TypeExpressionProtocol, NarwhalsTypeExpressionSystem),
        (NativeExpressionProtocol, NarwhalsNativeExpressionSystem),
    ])
    def test_narwhals_backend_alignment(self, protocol, implementation):
        """Narwhals backend implementations should align with protocols (method presence and signatures)."""
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


class TestBuilderProtocolAlignment:
    """Test that Namespace implementations align with BuilderProtocols."""

    # Infrastructure methods not part of the builder API
    NAMESPACE_INFRASTRUCTURE = {'_api', '_node', '_build', '_to_node_or_value'}

    @pytest.mark.parametrize("protocol,implementation,exclude_impl", [
        # ArithmeticBuilderProtocol includes dunders which are on API, not namespace
        (ArithmeticBuilderProtocol, ArithmeticNamespace, {
            '__add__', '__radd__', '__sub__', '__rsub__',
            '__mul__', '__rmul__', '__truediv__', '__rtruediv__',
            '__floordiv__', '__rfloordiv__', '__mod__', '__rmod__',
            '__pow__', '__rpow__', '__neg__',
        }),
        (BooleanBuilderProtocol, BooleanNamespace, set()),
        (HorizontalBuilderProtocol, HorizontalNamespace, set()),
        (NameBuilderProtocol, NameNamespace, set()),
        (NullBuilderProtocol, NullNamespace, set()),
        (StringBuilderProtocol, StringNamespace, set()),
        (TemporalBuilderProtocol, DateTimeNamespace, set()),
        (TypeBuilderProtocol, TypeNamespace, set()),
        (NativeBuilderProtocol, NativeNamespace, set()),
    ])
    def test_namespace_alignment(self, protocol, implementation, exclude_impl):
        """Namespace implementations should align with builder protocols (method presence and signatures)."""
        result = check_alignment(
            protocol,
            implementation,
            exclude_from_protocol=self.NAMESPACE_INFRASTRUCTURE | exclude_impl,
            exclude_from_impl=self.NAMESPACE_INFRASTRUCTURE,
            include_inherited=True,
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
        visitor_pairs = [
            (ArithmeticVisitorProtocol, ArithmeticExpressionVisitor),
            (BooleanVisitorProtocol, BooleanExpressionVisitor),
            (CoreVisitorProtocol, CoreExpressionVisitor),
            (HorizontalVisitorProtocol, HorizontalExpressionVisitor),
            (NameVisitorProtocol, NameExpressionVisitor),
            (NullVisitorProtocol, NullExpressionVisitor),
            (StringVisitorProtocol, StringExpressionVisitor),
            (TemporalVisitorProtocol, TemporalExpressionVisitor),
            (TypeVisitorProtocol, TypeExpressionVisitor),
            (NativeVisitorProtocol, NativeExpressionVisitor),
        ]

        polars_backend_pairs = [
            (ArithmeticExpressionProtocol, PolarsArithmeticExpressionSystem),
            (BooleanExpressionProtocol, PolarsBooleanExpressionSystem),
            (CoreExpressionProtocol, PolarsCoreExpressionSystem),
            (HorizontalExpressionProtocol, PolarsHorizontalExpressionSystem),
            (NameExpressionProtocol, PolarsNameExpressionSystem),
            (NullExpressionProtocol, PolarsNullExpressionSystem),
            (StringExpressionProtocol, PolarsStringExpressionSystem),
            (TemporalExpressionProtocol, PolarsTemporalExpressionSystem),
            (TypeExpressionProtocol, PolarsTypeExpressionSystem),
            (NativeExpressionProtocol, PolarsNativeExpressionSystem),
        ]

        ibis_backend_pairs = [
            (ArithmeticExpressionProtocol, IbisArithmeticExpressionSystem),
            (BooleanExpressionProtocol, IbisBooleanExpressionSystem),
            (CoreExpressionProtocol, IbisCoreExpressionSystem),
            (HorizontalExpressionProtocol, IbisHorizontalExpressionSystem),
            (NameExpressionProtocol, IbisNameExpressionSystem),
            (NullExpressionProtocol, IbisNullExpressionSystem),
            (StringExpressionProtocol, IbisStringExpressionSystem),
            (TemporalExpressionProtocol, IbisTemporalExpressionSystem),
            (TypeExpressionProtocol, IbisTypeExpressionSystem),
            (NativeExpressionProtocol, IbisNativeExpressionSystem),
        ]

        narwhals_backend_pairs = [
            (ArithmeticExpressionProtocol, NarwhalsArithmeticExpressionSystem),
            (BooleanExpressionProtocol, NarwhalsBooleanExpressionSystem),
            (CoreExpressionProtocol, NarwhalsCoreExpressionSystem),
            (HorizontalExpressionProtocol, NarwhalsHorizontalExpressionSystem),
            (NameExpressionProtocol, NarwhalsNameExpressionSystem),
            (NullExpressionProtocol, NarwhalsNullExpressionSystem),
            (StringExpressionProtocol, NarwhalsStringExpressionSystem),
            (TemporalExpressionProtocol, NarwhalsTemporalExpressionSystem),
            (TypeExpressionProtocol, NarwhalsTypeExpressionSystem),
            (NativeExpressionProtocol, NarwhalsNativeExpressionSystem),
        ]

        namespace_pairs = [
            (ArithmeticBuilderProtocol, ArithmeticNamespace),
            (HorizontalBuilderProtocol, HorizontalNamespace),
            (NameBuilderProtocol, NameNamespace),
            (NullBuilderProtocol, NullNamespace),
            (StringBuilderProtocol, StringNamespace),
            (TemporalBuilderProtocol, DateTimeNamespace),
            (TypeBuilderProtocol, TypeNamespace),
            (NativeBuilderProtocol, NativeNamespace),
        ]

        print("\n" + "="*80)
        print("PROTOCOL ALIGNMENT REPORT")
        print("="*80)

        print("\n--- VISITOR LAYER ---")
        for protocol, impl in visitor_pairs:
            result = check_alignment(protocol, impl, include_inherited=True)
            if not result.is_aligned:
                print(result)

        print("\n--- BACKEND LAYER: POLARS ---")
        for protocol, impl in polars_backend_pairs:
            result = check_alignment(protocol, impl, include_inherited=False)
            if not result.is_aligned:
                print(result)

        print("\n--- BACKEND LAYER: IBIS ---")
        for protocol, impl in ibis_backend_pairs:
            result = check_alignment(protocol, impl, include_inherited=False)
            if not result.is_aligned:
                print(result)

        print("\n--- BACKEND LAYER: NARWHALS ---")
        for protocol, impl in narwhals_backend_pairs:
            result = check_alignment(protocol, impl, include_inherited=False)
            if not result.is_aligned:
                print(result)

        print("\n--- NAMESPACE/BUILDER LAYER ---")
        for protocol, impl in namespace_pairs:
            result = check_alignment(protocol, impl, include_inherited=True)
            if not result.is_aligned:
                print(result)

        print("\n" + "="*80)
        print("END REPORT")
        print("="*80)
