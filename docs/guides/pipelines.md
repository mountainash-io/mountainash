# Pipeline Framework

Mountainash pipelines are declarative, multi-step data flows with explicit step dependencies, typed parameter binding, optional caching, and first-class integration into the relation AST.

> **Status:** Evolving. The parameter-binding system replaced an earlier "pushdown capabilities" system in PR #160 (2026-05). Examples below reflect the current API.

## Concepts

| Concept | What it is |
|---------|-----------|
| `step` | A named callable that produces a DataFrame-like result. Declared via the `@step(...)` decorator or `PipelineBuilder.step(...)`. |
| `ParamSpec` | A typed parameter declaration on a step. The caller supplies values via `relation.params(...)`. |
| `PipelineBuilder` | Fluent builder that accumulates steps and returns a `PipelineSpec`. |
| `PipelineSpec` | Frozen, hashable spec of the pipeline. |
| `SimplePipelineRunner` | Topological runner that executes a `PipelineSpec` end-to-end. |
| `source()` | Wraps a single step as a `Relation`, so you can compose downstream operations and parameter binding before materialising. |
| `PipelineStorage` | Pluggable cache protocol (`MemoryPipelineStorage`, `FileSystemPipelineStorage`, `DualPipelineStorage`). |

## Defining a step

```python
from datetime import datetime
import polars as pl
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
    since  = ctx.params["since"]
    region = ctx.params["region"]
    # ... your data fetch ...
    return pl.DataFrame({"order_id": [...], "amount": [...]})
```

The decorated function receives a `StepContext` with:

- `ctx.params` — `dict[str, Any]` of resolved parameter values
- `ctx.pipeline_storage` — the cache backend, if configured
- `ctx.storage_facade` — remote-IO facade for files
- `ctx.config`, `ctx.step_name`, `ctx.workflow_id`

## Building a pipeline

```python
pipeline = (
    PipelineBuilder("sales", version="1.0")
      .step("orders", fetch_orders)
      .step("customers", fetch_customers)
      .step("enriched", join_step, depends_on=["orders", "customers"])
      .build()
)
```

`PipelineBuilder` is immutable: each `.step()` returns a new builder. `.build()` returns a `PipelineSpec`.

## Parameter binding via `relation.params(...)`

`source()` returns a `Relation` wrapping a `PipelineStepRelNode`. Use `.params(...)` to bind values **before** the terminal operation:

```python
result = (
    source("orders", pipeline=pipeline)
      .params(since=datetime(2026, 1, 1), region="EMEA")
      .filter(ma.col("amount").gt(100))
      .sort("order_id")
      .to_polars()
)
```

Under the hood:

1. `.params(...)` wraps the upstream node in a `ParamsRelNode`.
2. The `OptimisationRegistry` runs `fold_params`, which validates parameter names against the step's `ParamSpec` tuple, applies defaults, and merges the values into `PipelineStepRelNode.bound_params`.
3. At `.collect()` / `.to_polars()` time, the executor receives `params=` (a plain `dict[str, Any]`) and calls the step function.

### Validation rules

- An unknown parameter (not in any `ParamSpec.name`) raises `ValueError("Unknown parameter '…'")`.
- A required parameter that is not supplied and has no default raises `ValueError("Required parameter '…' not provided.")`.
- A step with no `ParamSpec` tuple accepts any params and passes them through.

### Migration from the old pushdown API

If you have code from before PR #160:

| Old | New |
|-----|-----|
| `step(..., pushdown=StepCapabilities(pushable_params=[PushableParam(...)]))` | `step(..., params=(ParamSpec(name=..., type=..., required=...),))` |
| Filter predicates inferred and pushed into the step | Caller supplies values explicitly via `.params(...)` |
| `StepContext.predicates` (a `ResolvedPredicates` object) | `StepContext.params` (a `dict[str, Any]`) |
| `apply_pushdown` optimiser | `fold_params` optimiser |

The old API has been removed entirely.

## Running an end-to-end pipeline

For non-relation use (just run the whole DAG and get every step's result):

```python
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner

runner = SimplePipelineRunner(pipeline)
results = runner.run(initial_params={
    "orders":    {"since": datetime(2026, 1, 1), "region": "EMEA"},
    "customers": {"tenant_id": "acme"},
})

orders_df = results["orders"].data
```

`StepResult.data` is the step's return value; `.metadata` has timings, record counts, input cache keys, and the resolved `params` dict.

## Caching

```python
from mountainash.pipelines.storage import FileSystemPipelineStorage

runner = SimplePipelineRunner(
    pipeline,
    pipeline_storage=FileSystemPipelineStorage(root="./.cache"),
)
```

Cache keys are derived from `(pipeline name, step name, version, bound params, upstream cache keys)`. The DBOS runner (`mountainash.pipelines.orchestration.dbos_runner`) gives the same shape on top of DBOS workflows.

## Custom executors

`source()` accepts an `executor=` kwarg. If provided, `.collect()` delegates to:

```python
executor.execute(pipeline=…, step_name=…, params=…, data_key=…)
```

This lets you swap out the default in-process runner for remote workers, databases, etc.

## Extension hook: optimisations

The params optimisation is registered via:

```python
from mountainash.pipelines.integration.relation import register_params_optimisation
register_params_optimisation()       # called automatically on import
```

You can add your own AST rewrites against `PipelineStepRelNode` (or any `RelationNode`) — see [extension-points.md](extension-points.md).

## Common pitfalls

- **`.params(...)` with no upstream pipeline step is a no-op except as a parameter dict.** It expects an upstream `PipelineStepRelNode` to fold into; without one the optimiser leaves the `ParamsRelNode` in place and the visitor falls back to `fold_params` at visit time, which raises if there is no `PipelineStepRelNode` below it.
- **Decorated steps cannot also be called directly with positional args.** They wrap the step definition; access the underlying function via `wrapper._step_definition.fn` if you need to.
- **`PipelineBuilder` is immutable** — `b.step(...)` returns a new builder. `b.step(...); b.build()` ignores the first call.
