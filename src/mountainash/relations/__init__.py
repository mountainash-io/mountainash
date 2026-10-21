"""Mountainash Relations — Substrait-aligned relational AST."""
from __future__ import annotations

from .core.errors import LogicalTerminalRequired
from .core.relation_api import Relation, relation, concat, GroupedRelation
from .ingress import from_arrow

# Import backends to trigger registration of relation systems
import mountainash.relations.backends  # noqa: F401

__all__ = ["Relation", "GroupedRelation", "relation", "concat", "from_arrow", "LogicalTerminalRequired"]
