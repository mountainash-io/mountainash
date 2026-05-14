from datetime import date

from mountainash.pipelines import step, pipeline
from mountainash.pipelines.core.step import StepContext
from mountainash.pipelines.core.capabilities import (
    StepCapabilities,
    DateRangeCapability,
    PushedPredicates,
)
from mountainash.pipelines.storage.memory import MemoryPipelineStorage
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner


@step(name="extract_data")
def extract_data(ctx: StepContext) -> dict[str, list[dict]]:
    return {
        "sleep": [
            {"date": "2026-01-15", "duration_seconds": 28800},
            {"date": "2026-01-16", "duration_seconds": 25200},
        ],
        "activities": [
            {"date": "2026-01-15", "type": "run", "distance_meters": 5000},
        ],
    }


@step(name="conform_data", depends_on=["extract_data"])
def conform_data(ctx: StepContext, extract_data: dict) -> dict[str, list[dict]]:
    sleep = extract_data["sleep"]
    return {
        "sleep": [
            {**r, "duration_hours": r["duration_seconds"] / 3600}
            for r in sleep
        ],
    }


def test_end_to_end_pipeline():
    spec = (
        pipeline("wearables_test", version="1.0.0")
        .step("extract_data", extract_data, pushdown=StepCapabilities(
            date_range=DateRangeCapability(column="date"),
        ))
        .step("conform_data", conform_data, depends_on=["extract_data"])
        .build()
    )

    storage = MemoryPipelineStorage()
    runner = SimplePipelineRunner(spec=spec, storage=storage)

    results = runner.run(predicates=PushedPredicates(date_start=date(2026, 1, 1)))

    assert "extract_data" in results
    assert "conform_data" in results

    conformed = results["conform_data"].data
    assert "sleep" in conformed
    assert conformed["sleep"][0]["duration_hours"] == 8.0

    results2 = runner.run(predicates=PushedPredicates(date_start=date(2026, 1, 1)))
    assert results2["conform_data"].cache_key == results["conform_data"].cache_key


def test_public_api_imports():
    from mountainash.pipelines import step, pipeline, source
    assert callable(step)
    assert callable(pipeline)
    assert callable(source)
