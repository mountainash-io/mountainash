"""End-to-end pushdown tests: filter expression -> pushdown -> step execution -> result."""
from datetime import date
import polars as pl
import mountainash as ma
from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.relation_nodes.substrait.reln_filter import FilterRelNode

from mountainash.pipelines import source, pipeline, step
from mountainash.pipelines.core.step import StepContext
from mountainash.pipelines.core.capabilities import (
    StepCapabilities,
    PushableParam,
    PushedPredicates,
)
from mountainash.pipelines.storage.memory import MemoryPipelineStorage
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner
from mountainash.pipelines.integration.pushdown import apply_pushdown
from mountainash.pipelines.integration.relation import PipelineStepRelNode


@step(
    name="extract",
    pushdown=StepCapabilities(
        pushable_params=(
            PushableParam(column="date", api_param="start", operators=("gt", "gte"), format="iso_datetime"),
            PushableParam(column="date", api_param="end", operators=("lt", "lte"), format="iso_datetime_eod"),
        ),
    ),
)
def extract(ctx: StepContext) -> list[dict]:
    start_param = ctx.predicates.params.get("start")
    all_data = [
        {"date": "2025-12-15", "value": 1},
        {"date": "2026-01-15", "value": 2},
        {"date": "2026-02-15", "value": 3},
        {"date": "2026-03-15", "value": 4},
    ]
    if start_param:
        all_data = [r for r in all_data if r["date"] >= str(start_param.value)]
    return all_data


class PushdownAwareExecutor:
    def __init__(self, spec):
        self._spec = spec
        self._storage = MemoryPipelineStorage()
        self.last_predicates = None

    def execute(self, pipeline, step_name, predicates, data_key=None):
        self.last_predicates = predicates
        runner = SimplePipelineRunner(spec=self._spec, storage=self._storage)
        results = runner.run(predicates=predicates)
        data = results[step_name].data
        if data_key:
            data = data[data_key]
        return pl.DataFrame(data).lazy()


def test_date_filter_pushdown_e2e():
    """Full end-to-end: filter expression -> pushdown -> step execution -> result collection."""
    spec = pipeline("test", version="1.0.0").step("extract", extract).build()
    executor = PushdownAwareExecutor(spec=spec)

    rel = source("extract", pipeline=spec, executor=executor)
    filtered_rel = rel.filter(ma.col("date").gt(ma.lit("2026-01-01")))

    rewritten_node = apply_pushdown(filtered_rel._node)
    result = Relation(rewritten_node).collect()

    assert isinstance(result, pl.DataFrame)
    assert result.shape[0] == 3
    assert result["date"][0] == "2026-01-15"

    assert executor.last_predicates is not None
    assert "start" in executor.last_predicates.params
    assert executor.last_predicates.params["start"].value == "2026-01-01"


def test_pushdown_preserves_filter_semantics():
    """After pushdown, the residual filter still applies."""
    spec = pipeline("test", version="1.0.0").step("extract", extract).build()
    executor = PushdownAwareExecutor(spec=spec)

    rel = source("extract", pipeline=spec, executor=executor)
    filtered_rel = rel.filter(ma.col("date").gte(ma.lit("2026-02-01")))

    rewritten_node = apply_pushdown(filtered_rel._node)
    result = Relation(rewritten_node).collect()

    assert result.shape[0] == 2
    assert result["date"].to_list() == ["2026-02-15", "2026-03-15"]


def test_no_pushdown_when_no_capability():
    """Steps without pushable_params don't get pushdown."""
    @step(name="plain")
    def plain(ctx: StepContext) -> list[dict]:
        return [{"date": "2026-01-15", "value": 1}]

    spec = pipeline("test", version="1.0.0").step("plain", plain).build()
    executor = PushdownAwareExecutor(spec=spec)

    rel = source("plain", pipeline=spec, executor=executor)
    filtered_rel = rel.filter(ma.col("date").gt(ma.lit("2026-01-01")))

    rewritten_node = apply_pushdown(filtered_rel._node)
    result = Relation(rewritten_node).collect()

    assert isinstance(result, pl.DataFrame)
    assert executor.last_predicates is not None
    assert executor.last_predicates.params == {}
