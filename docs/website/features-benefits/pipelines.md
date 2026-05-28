# Pipelines vs. orchestrators for in-process work

## What we built this to address

There's a class of pipeline that's too small for a real orchestrator. Five steps, in-process, possibly inside a Lambda, possibly inside a notebook. It needs explicit dependencies, named outputs, optional caching, and parameter binding. It does not need a scheduler, retries with exponential backoff, a web UI, or a deployment story.

Airflow, Prefect, and Dagster are excellent at what they do, but they aren't sized for this case. Each comes with a service to run, a UI to operate, a deployment story to maintain, a serialisation format to learn. The simplest "Hello World" Airflow DAG is more boilerplate than the actual five steps.

So most teams write it inline. Five function calls, hand-wired dependencies, a `results = {}` dict accumulating outputs, comments where parameters should be:

```python
orders     = fetch_orders(since=..., region=...)
customers  = fetch_customers(tenant_id=...)
enriched   = join(orders, customers)
summary    = summarise(enriched)
report     = format_report(summary, enriched)
```

Fine — until two things happen. First, somebody wants to cache `customers` so it doesn't re-fetch on every run. Second, somebody wants to parameterise `since` and `region` from a config without threading them through every step's call site. At that point the inline code starts growing — a cache dict here, a parameter dict there, a "skip if cached" check — and we've watched teams arrive at 60% of a pipeline framework, accidentally and badly.

## How we approach it

mountainash pipelines are a library-level pipeline framework. No daemon, no UI, no deployment story. They drop into existing code.

```python
from datetime import datetime
import mountainash as ma
from mountainash.pipelines import step, PipelineBuilder, source
from mountainash.pipelines.core.capabilities import ParamSpec

@step(
    "orders",
    params=(
        ParamSpec(name="since",  type=datetime, required=True),
        ParamSpec(name="region", type=str,      required=False, default="ALL"),
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

A step is just a function that takes a `StepContext`. Parameters are declared with `ParamSpec` — typed, validated, with optional defaults. Dependencies are explicit. The builder is immutable.

## The integration the inline version can't give

Pipelines compose with relations. A single step isn't a closed box — it's a relation source:

```python
result = (
    source("orders", pipeline=pipeline)
      .params(since=datetime(2026, 1, 1), region="EMEA")
      .filter(ma.col("amount").gt(100))
      .sort("order_id")
      .to_polars()
)
```

`source(...)` returns a relation. `.params(...)` binds values. Ordinary relation operations chain on top. When the terminal call runs, the pipeline step executes and the rest of the relation chain runs against its output — on whichever backend the caller asked for.

This is the integration the inline version can never have. The output of a step is the same kind of object as everything else in the data code. Filter, project, join, aggregate, conform, dispatch to any backend — all in the same vocabulary.

## Side-by-side: inline pipeline vs. mountainash

```python
# Inline, after the second feature request
_cache = {}

def get_orders(since, region):
    key = ("orders", since, region)
    if key not in _cache:
        _cache[key] = _fetch_orders(since, region)
    return _cache[key]

def get_customers(tenant_id):
    key = ("customers", tenant_id)
    if key not in _cache:
        _cache[key] = _fetch_customers(tenant_id)
    return _cache[key]

def run(since, region, tenant_id):
    orders    = get_orders(since, region)
    customers = get_customers(tenant_id)
    enriched  = join(orders, customers)
    # …
```

```python
# mountainash
@step("orders", params=(ParamSpec("since", datetime), ParamSpec("region", str, default="ALL")))
def fetch_orders(ctx): ...

@step("customers", params=(ParamSpec("tenant_id", str),))
def fetch_customers(ctx): ...

pipeline = PipelineBuilder("sales", "1.0") \
    .step("orders", fetch_orders) \
    .step("customers", fetch_customers) \
    .step("enriched", join_step, depends_on=["orders", "customers"]) \
    .build()

runner = SimplePipelineRunner(pipeline, pipeline_storage=FileSystemPipelineStorage(root="./.cache"))
results = runner.run(initial_params={
    "orders":    {"since": datetime(2026, 1, 1), "region": "EMEA"},
    "customers": {"tenant_id": "acme"},
})
```

The mountainash form is roughly the same line count. The dividend is the implicit list of things that come with it: typed parameters with validation, pluggable cache backend, declared dependencies, structured metadata on each step result (timing, record count, resolved params, upstream cache keys), and the relation integration above.

## What this is not

- **Not a competitor to Airflow.** Crons, retries-with-backoff, distributed orchestration, observability dashboards, alerting — all out of scope. We expect mountainash pipelines to run *inside* an Airflow task or a Prefect flow.
- **Not a streaming framework.** Pipelines are for batch-shaped work. Streaming is on our roadmap as a different execution discipline; see the [vision](../vision.md).
- **Not a dbt replacement.** dbt is about SQL transformations versioned alongside the warehouse. mountainash pipelines are about Python-level orchestration with cross-backend execution at each step. They coexist: a mountainash step can be "run this dbt model".

## On Hamilton

[Hamilton](https://github.com/dagworks-inc/hamilton) is the closest comparison — a library-level dataflow framework where dependencies come from function arguments. The differences worth knowing:

- mountainash pipelines integrate natively into the relation AST. A step's output is a relation node, so downstream operations can compose cross-backend without leaving the framework.
- Hamilton uses function arguments to declare dependencies; mountainash uses explicit `depends_on=` lists. Both shapes have trade-offs.
- mountainash pipelines come bundled with the rest of mountainash (relations, conform, contracts). A project that only wants the pipeline shape may find Hamilton leaner.

For a pipeline shape with no interest in cross-backend execution, Hamilton is a sharper tool. For pipelines that flow into the rest of mountainash's vocabulary, this is the integrated path.

## What this costs

- **Recent redesign.** The current `ParamSpec` system replaced a pushdown-based design in 2026-05. The shape above is current; older code or docs encountered elsewhere will be wrong.
- **Less operational depth than the heavyweight orchestrators.** No web UI, no DAG visualisation tool, no alerting hooks. By design — we scoped this at the library level.

## Where we'd point elsewhere

- **Existing Airflow/Prefect/Dagster setups that are working.** Keep them. Use mountainash relations and contracts *inside* the tasks if that's useful.
- **Pipelines needing real orchestration features.** Crons, retries-with-backoff, distributed workers, observability — out of scope here.

## Related

- Technical: [Pipelines](../features-technical/pipelines.md)
- Comparison: [Relations](relations.md)
