"""Per-step param scoping (pointbreak Phase 3.2 upstream fix).

Bug: runners hashed the single global params dict into every step's cache
key, so per-unit parameterised DAGs over-invalidated — one changed unit
re-keyed every step.
"""

from mountainash.pipelines.core.cache_key import compute_cache_key
from mountainash.pipelines.core.params import resolve_step_params
from mountainash.pipelines.core.result import infer_record_count
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.step import StepContext, StepDefinition
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner
from mountainash.pipelines.storage.memory import MemoryPipelineStorage


class TestResolveStepParams:
    def test_merges_step_entry_over_shared(self):
        assert resolve_step_params(
            "s", {"a": 1, "b": 2}, {"s": {"b": 3}},
        ) == {"a": 1, "b": 3}

    def test_no_step_entry_returns_shared(self):
        assert resolve_step_params("s", {"a": 1}, {"other": {"b": 2}}) == {"a": 1}

    def test_all_none(self):
        assert resolve_step_params("s", None, None) == {}


def _two_step_spec():
    def unit(ctx: StepContext) -> list[dict]:
        return [{"tag": ctx.params.get("tag")}]

    return PipelineSpec(
        name="units",
        version="1.0.0",
        steps={
            "scan_a": StepDefinition(name="scan_a", fn=unit),
            "scan_b": StepDefinition(name="scan_b", fn=unit),
        },
    )


def test_step_params_scope_cache_keys_per_step():
    """Changing one step's entry re-keys ONLY that step."""
    spec = _two_step_spec()
    runner = SimplePipelineRunner(spec, MemoryPipelineStorage())

    sp = {"scan_a": {"tag": "v1", "commit": "aaa"},
          "scan_b": {"tag": "v2", "commit": "bbb"}}
    first = runner.run(step_params=sp)
    assert first["scan_a"].cache_key != first["scan_b"].cache_key

    moved = {**sp, "scan_b": {"tag": "v2", "commit": "ccc"}}
    second = runner.run(step_params=moved)
    assert second["scan_a"].cache_key == first["scan_a"].cache_key
    assert second["scan_b"].cache_key != first["scan_b"].cache_key
    assert runner.last_executed == ("scan_b",)


def test_backward_compatible_keys_without_step_params():
    """run(params=P) hashes exactly what it always did."""
    spec = _two_step_spec()
    runner = SimplePipelineRunner(spec, MemoryPipelineStorage())
    results = runner.run(params={"tag": "v1"})
    for name in ("scan_a", "scan_b"):
        assert results[name].cache_key == compute_cache_key(
            "1.0.0", name, {}, {"tag": "v1"},
        )


def test_ctx_receives_effective_params_and_cache_key():
    seen = {}

    def probe(ctx: StepContext) -> list[dict]:
        seen[ctx.step_name] = (dict(ctx.params), ctx.cache_key)
        return [{}]

    spec = PipelineSpec(
        name="probe", version="1.0.0",
        steps={"p": StepDefinition(name="p", fn=probe)},
    )
    runner = SimplePipelineRunner(spec, MemoryPipelineStorage())
    results = runner.run(params={"shared": 1}, step_params={"p": {"own": 2}})

    params_seen, key_seen = seen["p"]
    assert params_seen == {"shared": 1, "own": 2}
    assert key_seen == results["p"].cache_key


def test_last_executed_tracks_cache_hits():
    spec = _two_step_spec()
    runner = SimplePipelineRunner(spec, MemoryPipelineStorage())
    sp = {"scan_a": {"tag": "v1"}, "scan_b": {"tag": "v2"}}
    runner.run(step_params=sp)
    assert set(runner.last_executed) == {"scan_a", "scan_b"}
    runner.run(step_params=sp)
    assert runner.last_executed == ()


class TestInferRecordCount:
    def test_explicit_attribute_wins(self):
        class Ref:
            record_count = 7

        assert infer_record_count(Ref()) == 7

    def test_list_length(self):
        assert infer_record_count([{}, {}]) == 2

    def test_fallback_none(self):
        assert infer_record_count(object()) is None
