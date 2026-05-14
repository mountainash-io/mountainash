import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from mountainash.pipelines.core.step import step, StepContext
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.capabilities import PushedPredicates, ResolvedPredicates
from mountainash.pipelines.storage.memory import MemoryPipelineStorage

try:
    from dbos import DBOS, DBOSConfig
    from mountainash.pipelines.orchestration.dbos_runner import DbosPipelineRunner
    HAS_DBOS = True
except ImportError:
    HAS_DBOS = False

pytestmark = pytest.mark.skipif(not HAS_DBOS, reason="DBOS not installed")


_dbos_launched = False

@pytest.fixture(autouse=True)
def _ensure_dbos():
    global _dbos_launched
    if not _dbos_launched:
        tmpdir = tempfile.mkdtemp()
        config: DBOSConfig = {
            "name": "mountainash-pipelines-test",
            "system_database_url": f"sqlite:///{tmpdir}/dbos.sqlite",
            "run_admin_server": False,
            "application_version": "0.1.0",
        }
        DBOS(config=config)
        DBOS.launch()
        _dbos_launched = True


@step(name="source")
def source_step(ctx: StepContext) -> list[dict]:
    return [{"id": 1, "value": 10}]


@step(name="transform", depends_on=["source"])
def transform_step(ctx: StepContext, source: list[dict]) -> list[dict]:
    return [{"id": r["id"], "value": r["value"] * 2} for r in source]


def _build_spec() -> PipelineSpec:
    return PipelineSpec(
        name="test_dbos",
        version="1.0.0",
        steps={
            "source": source_step._step_definition,
            "transform": transform_step._step_definition,
        },
    )


def test_dbos_runner_basic():
    spec = _build_spec()
    storage = MemoryPipelineStorage()
    runner = DbosPipelineRunner(spec=spec, storage=storage, user_id="test_user")
    results = runner.run()
    assert "source" in results
    assert "transform" in results
    assert results["transform"].data == [{"id": 1, "value": 20}]


def test_dbos_runner_idempotent():
    spec = _build_spec()
    storage = MemoryPipelineStorage()
    runner = DbosPipelineRunner(spec=spec, storage=storage, user_id="test_user_idem")

    r1 = runner.run()
    r2 = runner.run()

    assert r1["transform"].cache_key == r2["transform"].cache_key


def test_dbos_runner_force_reruns():
    spec = _build_spec()
    storage = MemoryPipelineStorage()
    runner = DbosPipelineRunner(spec=spec, storage=storage, user_id="test_user_force")

    r1 = runner.run()
    r2 = runner.run(force=True)

    assert r1["transform"].data == r2["transform"].data
