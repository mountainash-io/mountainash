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

mountainash pipelines are a library-level macro-orchestrator. No daemon, no UI, no deployment story. They drop into existing code.

```python
import ibis
import mountainash as ma
from mountainash.pipelines import (
    CallableSource, DagUnit, FileCheckpoint, IbisTableSink, Pipeline, Runner, WriteMode,
)
from mountainash.relations.dag import RelationDAG

template = RelationDAG()
template.add("enriched", template.ref("orders").join(template.ref("customers"), on="customer_id"))

pipeline = (
    Pipeline("sales")
    .add(CallableSource(fetch_orders, name="orders"))
    .add(CallableSource(fetch_customers, name="customers"))
    .add(DagUnit(template, "enriched", name="enriched", inputs={"orders": "orders", "customers": "customers"}))
    .add(IbisTableSink(con, "enriched_orders", name="sink", depends_on=("enriched",),
                       mode=WriteMode.UPSERT, keys=("order_id",)))
)
result = Runner(pipeline, checkpoint=FileCheckpoint("./.checkpoint")).run(params={"since": "2026-01-01"})
```

The mountainash form is roughly the same line count. The dividend is what comes with it: explicit dependencies, resumable incremental sources (failed partitions are retried on the next run; successful ones are not refetched), idempotent sinks, a file-backed checkpoint that survives restarts, and relation work that stays on its native backend between steps.

## What this is not

- **Not a competitor to Airflow.** Crons, retries-with-backoff, distributed orchestration, observability dashboards, alerting — all out of scope. We expect mountainash pipelines to run *inside* an Airflow task or a Prefect flow.
- **Not a streaming framework.** Pipelines are for batch-shaped work. Streaming is on our roadmap as a different execution discipline; see the [vision](../vision.md).
- **Not a dbt replacement.** dbt is about SQL transformations versioned alongside the warehouse. mountainash pipelines are about Python-level orchestration with cross-backend execution at each step. They coexist: a mountainash step can be "run this dbt model".

## On Hamilton

[Hamilton](https://github.com/dagworks-inc/hamilton) is the closest comparison — a library-level dataflow framework where dependencies come from function arguments. The differences worth knowing:

- mountainash pipelines run relation DAG targets as units and hand native frames across, so cross-backend work flows through without leaving the framework.
- Hamilton uses function arguments to declare dependencies; mountainash uses explicit `depends_on=` / `inputs=` declarations. Both shapes have trade-offs.
- mountainash pipelines come bundled with the rest of mountainash (relations, conform, contracts). A project that only wants the pipeline shape may find Hamilton leaner.

For a pipeline shape with no interest in cross-backend execution, Hamilton is a sharper tool. For pipelines that flow into the rest of mountainash's vocabulary, this is the integrated path.

## What this costs

- **Recent, breaking redesign.** Pipelines were rewritten in 2026-10 (`PipelineBuilder`, `@step`, `source()`, `SimplePipelineRunner` and `Relation.params()` are gone). The shape above is current; older code or docs encountered elsewhere will be wrong.
- **Less operational depth than the heavyweight orchestrators.** No web UI, no DAG visualisation tool, no alerting hooks. By design — we scoped this at the library level.

## Where we'd point elsewhere

- **Existing Airflow/Prefect/Dagster setups that are working.** Keep them. Use mountainash relations and contracts *inside* the tasks if that's useful.
- **Pipelines needing real orchestration features.** Crons, retries-with-backoff, distributed workers, observability — out of scope here.

## Related

- Technical: [Pipelines](../features-technical/pipelines.md)
- Comparison: [Relations](relations.md)
