"""Conform — shared expression builder for TypeSpec conformance.

The primary API is Relation.conform(spec). This module provides the
internal _build_conform_exprs helper used by both Relation.conform()
and the DAG visitor's apply_conform.
"""
from __future__ import annotations

from mountainash.conform.expressions import ConformResult, _build_conform_exprs
from mountainash.conform.errors import (
    ConformError,
    MissingFieldsError,
    ExtraFieldsError,
    ExactFieldCountError,
    NoMatchingFieldsError,
    ConformTransformError,
    SchemaDriftError,
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
    "_build_conform_exprs",
    "ConformError",
    "MissingFieldsError",
    "ExtraFieldsError",
    "ExactFieldCountError",
    "NoMatchingFieldsError",
    "ConformTransformError",
    "SchemaDriftError",
    "TypeDrift",
    "ColumnDrift",
    "KeyDrift",
    "ConformDrift",
    "ConformCollection",
]
