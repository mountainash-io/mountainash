"""Expression API namespaces.

Provides namespace classes for organizing expression operations.
Namespaces implement BuilderProtocols for Substrait-aligned operations.
"""
from __future__ import annotations

from .api_builder_base import BaseExpressionAPIBuilder

# # Core Substrait-aligned namespaces
# from .substrait import (
#     FieldReferenceNamespace,
#     LiteralNamespace,
#     ScalarArithmeticNamespace,
#     ScalarBooleanNamespace,
#     ScalarComparisonNamespace,
#     StringNamespace,
#     DateTimeNamespace,
#     ScalarSetNamespace,
#     ScalarRoundingNamespace,
#     ScalarLogarithmicNamespace,
#     ScalarAggregateNamespace,
#     CastNamespace,
#     ConditionalNamespace,
#     WhenBuilder,
#     ThenBuilder,
# )

__all__ = [
    # Base
    "BaseExpressionAPIBuilder",
    # Core nodes
    # "FieldReferenceNamespace",
    # "LiteralNamespace",
    # # Scalar operations
    # "ScalarArithmeticNamespace",
    # "ScalarBooleanNamespace",
    # "ScalarComparisonNamespace",
    # "StringNamespace",
    # "DateTimeNamespace",
    # "ScalarSetNamespace",
    # "ScalarRoundingNamespace",
    # "ScalarLogarithmicNamespace",
    # "ScalarAggregateNamespace",
    # # Type operations
    # "CastNamespace",
    # # Conditional operations
    # "ConditionalNamespace",
    # "WhenBuilder",
    # "ThenBuilder",
]
