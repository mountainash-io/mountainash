"""Core expression namespaces.

Substrait-aligned namespace implementations.
"""

from .exns_field_reference import FieldReferenceNamespace
from .exns_literal import LiteralNamespace
from .exns_scalar_arithmetic import ScalarArithmeticNamespace
from .exns_scalar_boolean import ScalarBooleanNamespace
from .exns_scalar_comparison import ScalarComparisonNamespace
from .exns_scalar_string import StringNamespace
from .exns_scalar_datetime import DateTimeNamespace
from .exns_scalar_set import ScalarSetNamespace
from .exns_scalar_rounding import ScalarRoundingNamespace
from .exns_scalar_logarithmic import ScalarLogarithmicNamespace
from .exns_scalar_aggregate import ScalarAggregateNamespace
from .exns_cast import CastNamespace
from .exns_conditional import ConditionalNamespace, WhenBuilder, ThenBuilder
from .exns_ternary import TernaryNamespace
from .exns_null import NullNamespace
from .exns_name import NameNamespace
from .exns_native import NativeNamespace

__all__ = [
    # Core nodes
    "FieldReferenceNamespace",
    "LiteralNamespace",
    # Scalar operations
    "ScalarArithmeticNamespace",
    "ScalarBooleanNamespace",
    "ScalarComparisonNamespace",
    "StringNamespace",
    "DateTimeNamespace",
    "ScalarSetNamespace",
    "ScalarRoundingNamespace",
    "ScalarLogarithmicNamespace",
    "ScalarAggregateNamespace",
    # Type operations
    "CastNamespace",
    # Conditional operations
    "ConditionalNamespace",
    "WhenBuilder",
    "ThenBuilder",
    # Ternary operations
    "TernaryNamespace",
    # Null operations
    "NullNamespace",
    # Name operations
    "NameNamespace",
    # Native operations
    "NativeNamespace",
]
