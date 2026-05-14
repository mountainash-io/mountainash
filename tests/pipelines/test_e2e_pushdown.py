from datetime import date
import polars as pl
import mountainash as ma
from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.relation_nodes.substrait.reln_filter import FilterRelNode

from mountainash.pipelines import source, pipeline, step
from mountainash.pipelines.core.step import StepContext
from mountainash.pipelines.core.capabilities import StepCapabilities, DateRangeCapability, PushedPredicates
from mountainash.pipelines.storage.memory import MemoryPipelineStorage
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner
from mountainash.pipelines.integration.pushdown import apply_pushdown
from mountainash.pipelines.integration.relation import PipelineStepRelNode


@step(
    name="extract",
    pushdown=StepCapabilities(date_range=DateRangeCapability(column="date")),
)
def extract(ctx: StepContext) -> list[dict]:
    start = ctx.predicates.date_start
    all_data = [
        {"date": "2025-12-15", "value": 1},
        {"date": "2026-01-15", "value": 2},
        {"date": "2026-02-15", "value": 3},
        {"date": "2026-03-15", "value": 4},
    ]
    if start:
        all_data = [r for r in all_data if r["date"] >= str(start)]
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
    """Full end-to-end: filter expression → pushdown → step execution → result collection."""
    spec = pipeline("test", version="1.0.0").step("extract", extract).build()
    executor = PushdownAwareExecutor(spec=spec)

    # Create the relation with the filter
    rel = source("extract", pipeline=spec, executor=executor)
    filtered_rel = rel.filter(ma.col("date").gt(ma.lit("2026-01-01")))

    # Apply pushdown to the AST
    rewritten_node = apply_pushdown(filtered_rel._node)

    # Wrap back into a Relation and collect
    result = Relation(rewritten_node).collect()

    # The extract step only returned records from 2026-01-01 onwards
    assert isinstance(result, pl.DataFrame)
    assert result.shape[0] == 3  # Jan, Feb, Mar 2026
    assert result["date"][0] == "2026-01-15"

    # Verify pushdown happened — executor received the date_start
    assert executor.last_predicates is not None
    assert executor.last_predicates.date_start == date(2026, 1, 1)


def test_pushdown_preserves_filter_semantics():
    """After pushdown, the residual filter still applies — correctness invariant."""
    spec = pipeline("test", version="1.0.0").step("extract", extract).build()
    executor = PushdownAwareExecutor(spec=spec)

    rel = source("extract", pipeline=spec, executor=executor)
    # Use GTE so the filter is: date >= "2026-02-01"
    filtered_rel = rel.filter(ma.col("date").gte(ma.lit("2026-02-01")))

    rewritten_node = apply_pushdown(filtered_rel._node)
    result = Relation(rewritten_node).collect()

    # The step gets date_start=2026-02-01, returns Feb + Mar
    # The residual filter also applies date >= "2026-02-01", keeping Feb + Mar
    assert result.shape[0] == 2
    assert result["date"].to_list() == ["2026-02-15", "2026-03-15"]


def test_no_pushdown_when_no_capability():
    """Steps without DateRangeCapability don't get pushdown."""
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
    # No pushdown, so executor got no predicates
    assert executor.last_predicates is not None
    assert executor.last_predicates.date_start is None
