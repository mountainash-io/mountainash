"""Expression system module for backend-specific primitives."""
from __future__ import annotations

from .expsys_base import ExpressionSystem, register_expression_system

__all__ = ["ExpressionSystem", "register_expression_system"]
