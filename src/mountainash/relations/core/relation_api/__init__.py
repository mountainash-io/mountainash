"""Relation public API — fluent builder and factory functions."""

from .relation import Relation, relation, concat
from .grouped_relation import GroupedRelation

__all__ = ["Relation", "GroupedRelation", "relation", "concat"]
