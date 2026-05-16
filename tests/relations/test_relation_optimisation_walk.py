"""Tests for RelationBase optimisation walk machinery."""
import polars as pl
from datetime import date

from mountainash.relations.core.relation_api.relation_base import RelationBase
from mountainash.relations.core.relation_nodes import ReadRelNode, FilterRelNode
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
    from mountainash.pipelines.integration.relation import PipelineStepRelNode
    from mountainash.pipelines.integration.pushdown import apply_pushdown
    from mountainash.pipelines.core.capabilities import StepCapabilities, DateRangeCapability
    from mountainash.relations.core.relation_api.optimisation_registry import (
        register_optimisation, _reset_registry,
    )

    _reset_registry()
    register_optimisation(PipelineStepRelNode, apply_pushdown)

    caps = StepCapabilities(date_range=DateRangeCapability(column="start"))
    pipeline_node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=None,
        executor=None,
        capabilities=caps,
    )
    from mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function import ScalarFunctionNode
    from mountainash.expressions.core.expression_nodes.substrait.exn_field_reference import FieldReferenceNode
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON

    pred = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT,
        arguments=[
            FieldReferenceNode(field="start"),
            LiteralNode(value=date(2024, 1, 1)),
        ],
    )
    filt = FilterRelNode(input=pipeline_node, predicate=pred)
    base = RelationBase(filt)
    result = base._apply_optimisations(base._node)

    assert isinstance(result, FilterRelNode)
    assert isinstance(result.input, PipelineStepRelNode)
    assert result.input.pushed_predicates.date_start == date(2024, 1, 1)


def test_detect_backend_from_uses_provided_node():
    """_detect_backend_from reads from the given node, not self._node."""
    from mountainash.core.constants import CONST_BACKEND

    read = _make_read()
    base = RelationBase(read)
    backend = base._detect_backend_from(read)
    assert backend == CONST_BACKEND.POLARS
