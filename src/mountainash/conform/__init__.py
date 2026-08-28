"""Conform — shared expression builder for TypeSpec conformance.

The primary API is Relation.conform(spec). This module provides the
internal _build_conform_exprs helper used by both Relation.conform()
and the DAG visitor's apply_conform.
"""
from __future__ import annotations

from mountainash.conform.expressions import (
    ConformResult,
    FieldBuildResult,
    _build_conform_exprs,
)
from mountainash.conform.errors import (
    ConformError,
    MissingFieldsError,
    ExtraFieldsError,
    ExactFieldsMismatchError,
    NoMatchingFieldsError,
    ConformTransformError,
    SchemaDriftError,
    UnresolvedSourceTypeError,
    IncompatibleSourceTypeError,
    UnsupportedStructuredTransportUse,
)
from mountainash.conform.drift import (
    TypeDrift,
    ColumnDrift,
    KeyDrift,
    ConformDrift,
    ConformCollection,
)

__all__ = [
    "ConformResult",
    "FieldBuildResult",
    "_build_conform_exprs",
    "ConformError",
    "MissingFieldsError",
    "ExtraFieldsError",
    "ExactFieldsMismatchError",
    "NoMatchingFieldsError",
    "ConformTransformError",
    "SchemaDriftError",
    "UnresolvedSourceTypeError",
    "IncompatibleSourceTypeError",
    "UnsupportedStructuredTransportUse",
    "TypeDrift",
    "ColumnDrift",
    "KeyDrift",
    "ConformDrift",
    "ConformCollection",
]
