"""RelationT TypeVar exists alongside ExpressionT (spec §3.3)."""
from __future__ import annotations

from typing import TypeVar


def test_relation_typevar_exists_and_is_bound():
    from mountainash.core.types import RelationT
    assert isinstance(RelationT, TypeVar)
    assert RelationT.__bound__ == "SupportedRelations" or getattr(
        RelationT.__bound__, "__forward_arg__", None
    ) == "SupportedRelations"


def test_expression_typevar_untouched():
    from mountainash.core.types import ExpressionT
    assert isinstance(ExpressionT, TypeVar)
