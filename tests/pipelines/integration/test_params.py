from __future__ import annotations

from datetime import date

import pytest

from mountainash.pipelines.core.capabilities import ParamSpec
from mountainash.pipelines.integration.relation import (
    PipelineStepRelNode,
    ParamsRelNode,
    fold_params,
)


def _make_pipeline_node(param_specs=()):
    return PipelineStepRelNode(
        step_name="fetch",
        pipeline=None,
        param_specs=param_specs,
    )


class TestParamsRelNode:
    def test_creates_with_params(self):
        inner = _make_pipeline_node()
        node = ParamsRelNode(input=inner, params={"start": date(2026, 4, 1)})
        assert node.params["start"] == date(2026, 4, 1)


class TestFoldParams:
    def test_folds_into_pipeline_node(self):
        specs = (ParamSpec(name="start", type=date), ParamSpec(name="end", type=date))
        inner = _make_pipeline_node(param_specs=specs)
        node = ParamsRelNode(input=inner, params={"start": date(2026, 4, 1), "end": date(2026, 5, 1)})
        result = fold_params(node)
        assert isinstance(result, PipelineStepRelNode)
        assert result.bound_params == {"start": date(2026, 4, 1), "end": date(2026, 5, 1)}

    def test_validates_unknown_param(self):
        specs = (ParamSpec(name="start", type=date),)
        inner = _make_pipeline_node(param_specs=specs)
        node = ParamsRelNode(input=inner, params={"star": date(2026, 4, 1)})
        with pytest.raises(ValueError, match="Unknown parameter.*star"):
            fold_params(node)

    def test_validates_required_missing(self):
        specs = (ParamSpec(name="start", type=date, required=True),)
        inner = _make_pipeline_node(param_specs=specs)
        node = ParamsRelNode(input=inner, params={})
        with pytest.raises(ValueError, match="Required parameter.*start"):
            fold_params(node)

    def test_applies_defaults(self):
        specs = (
            ParamSpec(name="start", type=date, required=True),
            ParamSpec(name="limit", type=int, required=False, default=100),
        )
        inner = _make_pipeline_node(param_specs=specs)
        node = ParamsRelNode(input=inner, params={"start": date(2026, 4, 1)})
        result = fold_params(node)
        assert result.bound_params["limit"] == 100

    def test_no_param_specs_passes_through(self):
        inner = _make_pipeline_node(param_specs=())
        node = ParamsRelNode(input=inner, params={"start": date(2026, 4, 1)})
        result = fold_params(node)
        assert result.bound_params == {"start": date(2026, 4, 1)}

    def test_non_pipeline_input_returns_unchanged(self):
        node = ParamsRelNode(input="not_a_pipeline_node", params={"x": 1})
        result = fold_params(node)
        assert result is node
