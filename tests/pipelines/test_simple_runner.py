from datetime import date
from mountainash.pipelines.core.step import step, StepContext
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.capabilities import PushedPredicates
from mountainash.pipelines.storage.memory import MemoryPipelineStorage
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner


@step(name="source")
def source_step(ctx: StepContext) -> list[dict]:
    return [{"id": 1, "value": 10}, {"id": 2, "value": 20}]


@step(name="double", depends_on=["source"])
def double_step(ctx: StepContext, source: list[dict]) -> list[dict]:
    return [{"id": r["id"], "value": r["value"] * 2} for r in source]


@step(name="sum_values", depends_on=["double"])
def sum_step(ctx: StepContext, double: list[dict]) -> list[dict]:
    total = sum(r["value"] for r in double)
    return [{"total": total}]


def _build_spec() -> PipelineSpec:
    return PipelineSpec(
        name="test_pipeline",
        version="1.0.0",
        steps={
            "source": source_step._step_definition,
            "double": double_step._step_definition,
            "sum_values": sum_step._step_definition,
        },
    )


def test_simple_runner_linear():
    spec = _build_spec()
    storage = MemoryPipelineStorage()
    runner = SimplePipelineRunner(spec=spec, storage=storage)
    results = runner.run()
    assert "source" in results
    assert "double" in results
    assert "sum_values" in results
    assert results["sum_values"].data == [{"total": 60}]


def test_simple_runner_caches_results():
    spec = _build_spec()
    storage = MemoryPipelineStorage()
    runner = SimplePipelineRunner(spec=spec, storage=storage)

    results1 = runner.run()
    results2 = runner.run()

    assert results1["sum_values"].cache_key == results2["sum_values"].cache_key


def test_simple_runner_fan_out_fan_in():
    @step(name="root")
    def root(ctx: StepContext) -> list[dict]:
        return [{"x": 5}]

    @step(name="branch_a", depends_on=["root"])
    def branch_a(ctx: StepContext, root: list[dict]) -> list[dict]:
        return [{"a": r["x"] + 1} for r in root]

    @step(name="branch_b", depends_on=["root"])
    def branch_b(ctx: StepContext, root: list[dict]) -> list[dict]:
        return [{"b": r["x"] * 2} for r in root]

    @step(name="merge", depends_on=["branch_a", "branch_b"])
    def merge(ctx: StepContext, branch_a: list[dict], branch_b: list[dict]) -> list[dict]:
        return [{"a": branch_a[0]["a"], "b": branch_b[0]["b"]}]

    spec = PipelineSpec(
        name="fan",
        version="1.0.0",
        steps={
            "root": root._step_definition,
            "branch_a": branch_a._step_definition,
            "branch_b": branch_b._step_definition,
            "merge": merge._step_definition,
        },
    )
    storage = MemoryPipelineStorage()
    runner = SimplePipelineRunner(spec=spec, storage=storage)
    results = runner.run()
    assert results["merge"].data == [{"a": 6, "b": 10}]


def test_simple_runner_respects_predicates():
    @step(name="extract")
    def extract(ctx: StepContext) -> list[dict]:
        return [{"date_start": str(ctx.predicates.date_start)}]

    spec = PipelineSpec(
        name="pred",
        version="1.0.0",
        steps={"extract": extract._step_definition},
    )
    storage = MemoryPipelineStorage()
    runner = SimplePipelineRunner(spec=spec, storage=storage)
    results = runner.run(predicates=PushedPredicates(date_start=date(2026, 1, 1)))
    assert results["extract"].data == [{"date_start": "2026-01-01"}]
