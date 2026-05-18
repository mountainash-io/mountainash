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
    from mountainash.pipelines.integration.relation import (
        PipelineStepRelNode,
        ParamsRelNode,
        fold_params,
    )
    from mountainash.pipelines.core.capabilities import ParamSpec
    from mountainash.relations.core.relation_api.optimisation_registry import (
        register_optimisation, _reset_registry,
    )

    _reset_registry()
    register_optimisation(ParamsRelNode, fold_params)

    specs = (ParamSpec(name="start", type=date),)
    pipeline_node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=None,
        executor=None,
        param_specs=specs,
    )
    params_node = ParamsRelNode(
        input=pipeline_node,
        params={"start": date(2024, 1, 1)},
    )
    base = RelationBase(params_node)
    result = base._apply_optimisations(base._node)

    assert isinstance(result, PipelineStepRelNode)
    assert result.bound_params["start"] == date(2024, 1, 1)


def test_pipeline_params_registered_on_import():
    """Importing mountainash.pipelines registers the params optimisation pass."""
    import mountainash.pipelines  # noqa: F401
    from mountainash.relations.core.relation_api.optimisation_registry import get_registered_node_types
    from mountainash.pipelines.integration.relation import ParamsRelNode

    assert ParamsRelNode in get_registered_node_types()


def test_detect_backend_from_uses_provided_node():
    """_detect_backend_from reads from the given node, not self._node."""
    from mountainash.core.constants import CONST_BACKEND

    read = _make_read()
    base = RelationBase(read)
    backend = base._detect_backend_from(read)
    assert backend == CONST_BACKEND.POLARS
