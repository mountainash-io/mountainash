"""Conform — shared expression builder for TypeSpec conformance.

The primary API is Relation.conform(spec). This module provides the
internal _build_conform_exprs helper used by both Relation.conform()
and the DAG visitor's apply_conform.
"""
from __future__ import annotations

from mountainash.conform.expressions import _build_conform_exprs

__all__ = ["_build_conform_exprs"]
