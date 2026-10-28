"""Tests for RelationBase optimisation walk machinery."""
import polars as pl

from mountainash.relations.core.relation_api.relation_base import RelationBase
from mountainash.relations.core.relation_nodes import ReadRelNode, FilterRelNode
from mountainash.relations.core.relation_nodes.reln_base import RelationNode
from mountainash.expressions.core.expression_nodes.substrait.exn_literal import LiteralNode


def _make_read():
    return ReadRelNode(dataframe=pl.DataFrame({"x": [1, 2, 3]}).lazy())


def test_walk_no_pipeline_node_returns_unchanged():
    """Without pipeline nodes, _apply_optimisations is a no-op."""
    read = _make_read()
    filt = FilterRelNode(input=read, predicate=LiteralNode(value=True))
    base = RelationBase(filt)
    result = base._apply_optimisations(base._node)
    assert result is filt


def test_walk_reconstructs_frozen_nodes():
    """Walk must use model_copy to rebuild frozen nodes with new children."""
    from mountainash.relations.core.relation_api.optimisation_registry import (
        register_optimisation, _reset_registry,
    )

    class OptNode(RelationNode):
        input: RelationNode
        marker: int = 0

        def accept(self, visitor):
            return visitor.visit(self)

    def bump(node):
        if isinstance(node, OptNode) and node.marker == 0:
            return node.model_copy(update={"marker": 1})
        return node

    _reset_registry()
    try:
        register_optimisation(OptNode, bump)
        read = _make_read()
        filt = FilterRelNode(input=OptNode(input=read), predicate=LiteralNode(value=True))
        base = RelationBase(filt)
        result = base._apply_optimisations(base._node)

        assert isinstance(result, FilterRelNode)
        assert isinstance(result.input, OptNode)
        assert result.input.marker == 1
        assert result is not filt
        assert filt.input.marker == 0
    finally:
        _reset_registry()


def test_registered_optimisation_node_type_is_listed():
    from mountainash.relations.core.relation_api.optimisation_registry import (
        get_registered_node_types, register_optimisation, _reset_registry,
    )

    class OptNode(RelationNode):
        input: RelationNode

        def accept(self, visitor):
            return visitor.visit(self)

    _reset_registry()
    try:
        register_optimisation(OptNode, lambda node: node)
        assert OptNode in get_registered_node_types()
    finally:
        _reset_registry()


def test_detect_backend_from_uses_provided_node():
    """_detect_backend_from reads from the given node, not self._node."""
    from mountainash.core.constants import CONST_BACKEND

    read = _make_read()
    base = RelationBase(read)
    backend = base._detect_backend_from(read)
    assert backend == CONST_BACKEND.POLARS
