# Pipelines

mountainash pipelines are declarative, multi-step data flows with explicit dependencies, typed parameters, optional caching, and native integration into the relation AST.

> **Status:** Recently redesigned. The current `ParamSpec` parameter system replaced a pushdown-based design in 2026-05. The shape below is current; treat anything you read elsewhere as out of date.

## The shape

```python
from datetime import datetime
import mountainash as ma
from mountainash.pipelines import step, PipelineBuilder, source
from mountainash.pipelines.core.capabilities import ParamSpec

@step(
    "orders",
    params=(
        ParamSpec(name="since", type=datetime, required=True),
        ParamSpec(name="region", type=str, required=False, default="ALL"),
    ),
)
def fetch_orders(ctx):
    return _fetch(since=ctx.params["since"], region=ctx.params["region"])


pipeline = (
    PipelineBuilder("sales", version="1.0")
      .step("orders", fetch_orders)
      .step("customers", fetch_customers)
      .step("enriched", join_step, depends_on=["orders", "customers"])
      .build()
)
```

Three things to notice:

1. **A step is just a function** that takes a `StepContext`. There's no inheritance, no decoration of complex framework objects.
2. **Parameters are typed and declared.** `ParamSpec(name=..., type=..., required=..., default=...)` is the entire surface. The pipeline knows what each step expects.
3. **Dependencies are explicit.** The builder is immutable; `depends_on` declares the DAG.

## Pipelines compose with relations

You don't have to run the whole pipeline as a black box. A single step can be lifted into a relation:

```python
result = (
    source("orders", pipeline=pipeline)
      .params(since=datetime(2026, 1, 1), region="EMEA")
      .filter(ma.col("amount").gt(100))
      .sort("order_id")
      .to_polars()
)
```

`source(...)` returns a `Relation` wrapping a `PipelineStepRelNode`. You bind parameters with `.params(...)`. You chain ordinary relation operations on top. When you call `.to_polars()`, the pipeline step executes and the rest of the relation chain runs against its output.

This means a pipeline step is not a closed box. It's a node in the same AST that ordinary relation operations live in, and the same visitor compiles both.

## What `ParamSpec` does

`ParamSpec` is a frozen dataclass:

```python
@dataclass(frozen=True)
class ParamSpec:
    name: str
    type: type
    required: bool = True
    default: Any = None
```

When you call `.params(...)`, mountainash:

1. Validates each name against the step's declared `ParamSpec`s. Unknown parameters raise.
2. Applies defaults for missing optional parameters.
3. Raises if a required parameter is unsupplied and has no default.
4. Merges the resolved values into the pipeline node's bound parameters.

The step's function receives the resolved values in `ctx.params` (a plain `dict[str, Any]`). No magic, no decorators on the function body, no globals.

## End-to-end runner

For the case where you want to run the entire pipeline and collect every step's result:

```python
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner

runner = SimplePipelineRunner(pipeline)
results = runner.run(initial_params={
    "orders":    {"since": datetime(2026, 1, 1), "region": "EMEA"},
    "customers": {"tenant_id": "acme"},
})

orders_df = results["orders"].data
```

`StepResult` carries the data and a `StepMetadata` (timings, record count, resolved params, upstream cache keys).

A DBOS-based runner is also available for durable execution on top of DBOS workflows.

## Caching

```python
from mountainash.pipelines.storage import FileSystemPipelineStorage

runner = SimplePipelineRunner(
    pipeline,
    pipeline_storage=FileSystemPipelineStorage(root="./.cache"),
)
```

Cache keys are derived from `(pipeline name, step name, version, bound params, upstream cache keys)`. If you re-run with the same params and unchanged upstream, the cached value is returned.

`PipelineStorage` is a protocol — bring your own (Redis, S3, content-addressed). The built-ins are `MemoryPipelineStorage`, `FileSystemPipelineStorage`, and `DualPipelineStorage` (memory + disk fallback).

## Executors

A `source()` call accepts `executor=`. By default, the step function runs in-process. You can swap in:

- a remote executor that submits to a queue,
- a database executor that translates the upstream relation into SQL,
- anything else implementing the `PipelineExecutor` protocol.

The protocol is small:

```python
class PipelineExecutor(Protocol):
    def execute(self, pipeline, step_name, params, data_key) -> Any: ...
```

## Why not Airflow / Prefect / Dagster?

mountainash pipelines are not a competitor to those orchestrators. They are a **library-level abstraction over named, parameter-bound, possibly cached data producers** — small enough to embed inside a notebook, a unit test, or a single function. The DAG ordering and dependency tracking exist because relations need named producers, not because we want to be a scheduler.

If you want crons, retries-with-backoff, distributed orchestration, observability dashboards, then run mountainash pipelines *inside* an Airflow task or a Prefect flow. That works fine.

## Migration from the old pushdown API

Before 2026-05, mountainash had a different parameter mechanism: capability-based pushdown, where filter predicates above a pipeline step were rewritten into pushed predicates that the step received. That design has been removed entirely. The new design — explicit `ParamSpec` plus caller-supplied values via `.params(...)` — is simpler, more typeable, and more honest about where the parameter values come from.

If you have code using `StepCapabilities`, `PushableParam`, `PushedPredicates`, `apply_pushdown`, or `register_pipeline_optimisations`, it will not import. See [`docs/guides/pipelines.md`](../../guides/pipelines.md#migration-from-the-old-pushdown-api) for the migration table.

## Related

- [Relations](relations.md) — `.params()` and `source()` are relation-level
- [TypeSpec and conformance](typespec-conform.md) — schema-aware steps
- [Cross-backend execution](cross-backend.md) — pipelines work on any backend the relation API supports
