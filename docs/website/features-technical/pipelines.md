# Pipelines

mountainash pipelines are a **macro-orchestrator**: they run heterogeneous units — relation DAG targets, Python functions, external-data sources, data sinks — one at a time, pass values between them, and record enough runner-owned state to resume after a partial failure.

> **Status:** Rewritten in 2026-10 (breaking). Everything on this page is the current shape; the earlier `PipelineBuilder`/`@step`/`source()` API and `Relation.params()` no longer exist. The full guide is [`docs/guides/pipelines.md`](../../guides/pipelines.md).

## The shape

```python
import ibis
import mountainash as ma
from mountainash.pipelines import (
    CallableSource, DagUnit, FileCheckpoint, IbisTableSink, Pipeline, Runner, WriteMode,
)
from mountainash.relations.dag import RelationDAG

template = RelationDAG()
template.add("big", template.ref("orders").filter(ma.col("amt").gt(15)))

pipeline = (
    Pipeline("sales")
    .add(CallableSource(fetch_orders, name="orders"))                       # external data, incremental
    .add(DagUnit(template, "big", name="big", inputs={"orders": "orders"}))  # a relation target
    .add(IbisTableSink(con, "big_orders", name="sink", depends_on=("big",),
                       mode=WriteMode.UPSERT, keys=("id",)))                 # authored business output
)
result = Runner(pipeline, checkpoint=FileCheckpoint(".checkpoint")).run()
```

Three things to notice:

1. **Units are small objects with one job.** `@unit` wraps a plain function into a `PythonUnit` and keeps the function directly testable.
2. **Macro drives micro.** A `DagUnit` binds upstream values into a `RelationDAG` template and collects one target; the relation never calls back into the pipeline. Native frames (including Ibis expressions) are handed over without an Arrow hop.
3. **Checkpoint and sink are different things.** The runner-owned checkpoint stores execution state (identity, status, cursor, coverage). A `SinkUnit` is your authored output. A pipeline can have either, both, or neither.

## Resuming after partial failure

A `SourceUnit` returns a value plus `Coverage` (which partitions were attempted, succeeded, failed) and a proposed `next_cursor`. The runner commits source progress only after every downstream unit completed; until then the attempt stays pending and is replayed on the next run. Partitions that failed are fed back to the source as `outstanding`; partitions that already succeeded are not refetched. A pending attempt whose configuration changed raises `IncompatibleResume` before anything runs.

Sink modes interact with coverage: `REPLACE` refuses an incomplete value, `REPLACE_PARTITION` replaces exactly the partitions that succeeded, `APPEND` and `UPSERT` accept anything.

**Known limit:** a non-retained TABULAR pending attempt (always the case with `FileCheckpoint`) is regenerated on replay and may differ from the first fetch, so an `APPEND` sink downstream may duplicate rows. Retain the source output as RECORDS, or sink and read back.

## Built-in sinks

- `IbisTableSink(connection, table, mode=…)` — DuckDB, SQLite and PostgreSQL; `APPEND`, `UPSERT` (single and composite keys), `REPLACE_PARTITION`, `REPLACE`; same-connection inputs write natively, including inputs that read the destination. PostgreSQL cells need a service (`MA_PG_URL`); they have been run locally against `postgres:16`, with no CI result observed yet.
- `ParquetDirectorySink(path, mode=…)` — `APPEND`, `REPLACE`, `REPLACE_PARTITION`; `UPSERT` is explicitly unsupported.

See the support matrix in the guide.

## Nested pipelines, parallelism, policy

- `PipelineUnit(inner, "target")` runs a pipeline as one unit against a scoped checkpoint; the outermost runner commits inner source progress.
- `Runner(workers=n)` runs independent units on a thread pool; `workers=1` runs inline on the caller thread. `affinity=Affinity.MAIN` pins a unit to the caller thread (thread-affine connections).
- The capability policy active at `run()` is frozen and applied around every unit, on workers too.

## Why not Airflow / Prefect / Dagster?

mountainash pipelines are a library-level abstraction — small enough to embed in a notebook, a unit test or a single function. They do not schedule, alert or distribute. If you need that, run one `Runner.run()` *inside* an Airflow task or a Prefect flow; checkpointing is optional and runner-owned, so it does not conflict with the outer system.

## Migration

Removed with no replacement alias: `PipelineBuilder`, `source()`, `@step`, `StepContext`, `StepResult`, `PipelineSpec`, `SimplePipelineRunner`, the DBOS runner, `PipelineStorage` implementations, the pipeline relation nodes, `Relation.params()` (full list in `CHANGELOG.md`). `ParamSpec`, `ParamAxis`, `expand_axes`, `EmptyPolicy` and `RetryConfig` keep their names and import paths.

## Related

- [Relations](relations.md) — `RelationDAG` is the micro-orchestrator that `DagUnit` drives
- [Cross-backend execution](cross-backend.md) — values keep their native location through the pipeline
