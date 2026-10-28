# Pipeline Framework

`mountainash.pipelines` is a **macro-orchestrator**: it runs heterogeneous *units* — relation DAG targets, Python callables, external-data sources, data sinks — one at a time, passes their values along, and records enough state to resume after a partial failure. It sits on top of the same graph kernel (`mountainash.graph`) as `RelationDAG`.

The two orchestrators have different jobs:

| | `RelationDAG` (micro) | `Pipeline` (macro) |
|---|---|---|
| Execution | one compiled plan per `collect`, refs resolved lazily | step by step over opaque units |
| Unit of work | a relation | a `Unit` (anything that returns a value) |
| Cross-run state | none | runner-owned **checkpoint** |
| Direction | never calls the pipeline | drives `DagUnit`s |

A pipeline drives relation DAGs; a relation never triggers a pipeline. There is no `Relation.params()` and no pipeline relation node.

## Concepts

### Unit kinds

| Unit | Purpose |
|---|---|
| `PythonUnit` / `@unit` | Run a function `fn(*upstream_payloads, ctx) -> Any`. The decorated function stays directly testable (`double.__wrapped__(...)`, `double.fn`). |
| `DagUnit(template, target_name, inputs=…)` | Bind upstream values into a `RelationDAG` template (`template.bind(...)`) and collect one target. Native frames are handed over unchanged; RECORDS become Arrow; a REFERENCE is refused. The template is never mutated, so the unit can run repeatedly. |
| `SourceUnit` / `CallableSource` | Fetch external data incrementally. `fetch(upstream, params, state) -> SourceResult`. |
| `SinkUnit` (`IbisTableSink`, `ParquetDirectorySink`) | Write a value to a destination and return a `LocatorReference`. |
| `PipelineUnit(pipeline, target)` | Run a nested pipeline as one unit. The inner checkpoint is namespaced under the outer unit name. |

A unit only needs `name`, `version`, `affinity`, `lifecycle`, `inputs()`, `identity()` and `run()`; inheriting `BaseUnit` is convenient, not required.

### Values

Everything a unit returns is classified once, by `Value.of(payload, identity, coverage=None)`:

- `TABULAR` — a native frame (Polars, pandas, Arrow, Ibis expression, Narwhals). Its execution location is detected, never relabelled.
- `RECORDS` — `list[Mapping]` or `dict[str, list]`.
- `REFERENCE` — a `LocatorReference` (`locator`, `record_count`) returned by a sink.
- `OPAQUE` — anything else; passed through to whatever ingress the consumer already has.

The runner never converts payloads. Conversion happens in the consuming unit, only at a real representation boundary.

### Identity

Every unit execution has an `Identity`: a stable digest of the unit kind, version, params, the identities of its upstream units and kind-specific extras (for a `DagUnit`, a structural digest of the target and the input bindings; for a sink, the destination and mode). A configuration operand that cannot be serialised raises `UnhashableIdentityInput`. Payloads are never identity operands.

### Lifecycles

The runner is kind-blind; each unit declares a `lifecycle` that decides how it is identified, whether it is reused, how it executes and when it commits.

- **Unit lifecycle** (`PythonUnit`, `DagUnit`, sinks) — if the checkpoint holds a `COMPLETE` record for this identity whose value is retained (and, for a `REFERENCE`, whose destination still `exists`), the unit is `REUSED`; otherwise it runs under `RetryConfig` and `EmptyPolicy`. `force=True` bypasses reuse.
- **Source lifecycle** — adds cross-run progress (cursor, outstanding and succeeded partitions) and a *pending attempt*; see below.
- **Nested lifecycle** — the unit lifecycle applied to the outer unit; the inner pipeline runs against a scoped checkpoint and never commits source progress itself.

`Runner.plan()` identifies the whole graph before anything executes, so `IncompatibleResume` surfaces before any unit runs.

Run statuses are `COMPLETE`, `PARTIAL`, `FAILED`, `SKIPPED` and `REUSED`. A failed unit marks its descendants `SKIPPED`; siblings finish. With `workers=1` everything runs inline on the caller thread; with `workers>1` worker units use a thread pool and units with `affinity=Affinity.MAIN` run on the caller thread (use this for thread-affine resources such as an Ibis-SQLite connection). The capability policy in force at `run()` is frozen and re-entered around every unit, including those on workers.

### Checkpoint versus sink

| | Checkpoint | Sink |
|---|---|---|
| Owner | the runner | you, as a unit in the graph |
| Purpose | execution state: identity, status, cursor, coverage, replayable values | business output |
| Lifetime | resume/replay only | permanent |
| Required | no — a stateless pipeline is legitimate | no |

`MemoryCheckpoint` retains every value by reference. `FileCheckpoint(path)` survives process restarts; it persists RECORDS (JSON) and REFERENCEs and **never serialises TABULAR payloads** — a TABULAR value is recorded without its payload and is regenerated on replay.

### Sources: coverage and cursor

A source returns a `SourceResult(value, next_cursor)`, and the value carries `Coverage(attempted, succeeded, failed, complete)`. The runner treats partitions and cursors as opaque hashables and never orders them.

Per source the checkpoint holds a `SourceState(cursor, outstanding, succeeded)`: `outstanding` are partitions that failed earlier and have not since succeeded; `succeeded` are partitions already fetched beyond the committed cursor. The source must not refetch `succeeded`.

After an attempt, `residual = (outstanding ∪ coverage.failed) − coverage.succeeded`. If `residual` is non-empty the source returns its cursor unchanged; if empty, `next_cursor` must cover everything fetched. Progress is committed **only when every descendant of the source reached `COMPLETE` or `REUSED` in the run**; until then the attempt stays *pending* and is replayed on the next run.

Two-run example (partitions `A`, `B`, `C`; a sink downstream):

1. Run 1: state is empty. The source attempts `{A, B}`; `A` fails. It returns B's rows with `Coverage({A,B}, {B}, {A})` and an unchanged cursor (`None`). The sink writes B. Commit: `residual={A}` is non-empty, so progress becomes `cursor=None, outstanding={A}, succeeded={B}`.
2. Run 2: state `(None, {A}, {B})`. The source fetches exactly `{A}` plus anything new since the cursor (`C`); `B` is not refetched. `A` succeeds, `residual` is empty, so it returns a cursor covering `{A, B, C}`. Commit: `cursor=C`, nothing outstanding.

If the sink fails in run 1, the attempt stays pending; the next run replays the *same* value (no refetch) so the sink gets B again, and progress commits only after the sink succeeds.

A pending attempt whose source configuration changed raises `IncompatibleResume` before any unit runs (the attempt is preserved; `force=True` discards it). Downstream of a `PARTIAL` source receive that run's value as usual; accumulating across runs is the sink's job.

`DagUnit`/`PythonUnit` outputs carry a partial-coverage marker when any upstream is partial, because a transformation may change partition meaning. A unit declared `partitions_preserved=True` passes its single upstream source's coverage through unchanged.

### Sink modes versus coverage

| Mode | Accepts |
|---|---|
| `APPEND`, `UPSERT(keys)` | any coverage |
| `REPLACE` | `coverage is None` or complete — otherwise `IncompleteCoverage` (also through a `DagUnit`) |
| `REPLACE_PARTITION(columns)` | partition sets only (direct from a source or through `partitions_preserved` units); deletes-and-inserts exactly `coverage.succeeded` (a successfully fetched empty partition is cleared) and never touches `failed` |

A sink that fails *after* writing raises `NonRetryable(AmbiguousWrite)` unless `allow_duplicate=True`, so the runner never re-appends blindly.

### The documented limit

A pending attempt whose value is a non-retained TABULAR (always the case under `FileCheckpoint`) is **regenerated** on replay: the source is fetched again with the attempt's original state, and the new fetch may return different data. An `APPEND` sink downstream of it may therefore duplicate rows that were already appended. If that matters, retain the source output as RECORDS, or write it through a sink and read it back with a `SourceUnit`.

## End-to-end example

```python
import ibis
import polars as pl
import mountainash as ma
from mountainash.pipelines import (
    CallableSource, Coverage, DagUnit, FileCheckpoint, IbisTableSink, Identity,
    Pipeline, Runner, SourceResult, Value, WriteMode,
)
from mountainash.relations.dag import RelationDAG

def fetch(upstream, params, state):
    rows = pl.DataFrame({"id": [1, 2, 3], "region": ["eu", "eu", "us"], "amt": [10, 20, 30]})
    cov = Coverage.source({"eu", "us"}, {"eu", "us"}, set())
    return SourceResult(Value.of(rows, Identity.of("orders"), cov), next_cursor="2026-10-28")

template = RelationDAG()
template.add("big", template.ref("orders").filter(ma.col("amt").gt(15)))

con = ibis.duckdb.connect("warehouse.duckdb")
pipeline = (
    Pipeline("sales")
    .add(CallableSource(fetch, name="orders"))
    .add(DagUnit(template, "big", name="big", inputs={"orders": "orders"}))
    .add(IbisTableSink(con, "big_orders", name="sink", depends_on=("big",),
                       mode=WriteMode.UPSERT, keys=("id",)))
)
result = Runner(pipeline, checkpoint=FileCheckpoint(".checkpoint")).run()
print({k: v.value for k, v in result.statuses.items()})   # all 'complete'
```

The source's committed cursor is part of its next identity, so a second run is a fresh attempt and re-executes the chain. `REUSED` applies when a unit's identity is unchanged — for example after a downstream unit failed in an earlier run and the source's pending attempt is replayed — and only while its destination still exists. `run(force=True)` bypasses reuse.

## Sink support matrix

Built-in sinks live under `mountainash/pipelines/units/sinks/`; optional dependencies (Ibis, PyArrow) are imported lazily. Every cell below is exercised by `tests/pipelines/units/sinks/`.

`IbisTableSink` — modes × key shape × self-dependent input (an input expression that reads the destination table, which the sink first stages natively):

| Dialect | APPEND | UPSERT | REPLACE_PARTITION | REPLACE | Composite keys / partitions | Self-dependent input |
|---|---|---|---|---|---|---|
| DuckDB | tested | tested | tested | tested | tested | tested, all modes |
| SQLite | tested | tested | tested | tested | tested | tested, all modes |
| PostgreSQL | requires a PostgreSQL service (`MA_PG_URL`) | requires `MA_PG_URL` | requires `MA_PG_URL` | requires `MA_PG_URL` | requires `MA_PG_URL` | requires `MA_PG_URL` |

PostgreSQL status: the PostgreSQL cells skip with a "blocked" reason when `MA_PG_URL` is unset. They were run locally against `postgres:16` (all cells passing); no CI result for them has been observed, so treat PostgreSQL as locally verified only.

Behaviour that holds for every dialect: same-connection Ibis inputs are written natively with zero exports; a foreign-connection input is exported once and imported; destructive modes run in one transaction; `APPEND` with a post-write failure raises `AmbiguousWrite`.

`ParquetDirectorySink(path, mode=…)`:

| Mode | Behaviour |
|---|---|
| APPEND | new file per write |
| REPLACE | clears the directory, writes one file |
| REPLACE_PARTITION | hive-style `p=a/q=x` directories; composite partition columns supported; empty succeeded partitions are cleared. Values are percent-encoded into path-safe directory names (`a/b` → `p=a%2Fb`, so it can never alias or escape `p=a`); a NULL partition is `p=__HIVE_DEFAULT_PARTITION__` and matches/clears NULL rows |
| UPSERT | not supported — raises `UnsupportedValueKind` |

A file destination has no self-dependent-input case; that column does not apply.

## Retained helpers

`ParamSpec`, `ParamAxis`, `expand_axes`, `EmptyPolicy` and `RetryConfig` keep their names and are exported from `mountainash.pipelines` (and `mountainash.pipelines.core`). `RetryConfig` is the runner's retry policy; a unit raises `NonRetryable` to opt out of retry.

## Removed

`PipelineBuilder`, `source()`, `@step`, `StepContext`, `StepResult`, `PipelineSpec`, `SimplePipelineRunner`, the DBOS runner, `PipelineStorage` and its implementations, the pipeline relation nodes and `Relation.params()` (full list in `CHANGELOG.md`). An external orchestrator wraps one `Runner.run()` call.
