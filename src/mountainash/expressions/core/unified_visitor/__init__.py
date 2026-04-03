"""Unified expression visitor for Substrait-aligned nodes.

This module provides a single visitor that handles all node types,
replacing the previous category-specific visitors.
"""
from __future__ import annotations

from .visitor import UnifiedExpressionVisitor


__all__ = [
    "UnifiedExpressionVisitor",
]
