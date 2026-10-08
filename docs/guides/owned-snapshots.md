# Owned snapshots

`Relation.snapshot()` evaluates a relation into an independently owned native
result and returns a new Relation over it. Later source changes or deletion do
not change the saved values. Ordinary `collect()` keeps its existing behavior:
Ibis returns a deferred native table and pandas may return its original frame.
Use a snapshot when you need a stable result.

```python
import mountainash as ma
import polars as pl

source = ma.relation(pl.DataFrame({"x": [7]}))
saved = source.snapshot()
assert saved.to_dicts() == [{"x": 7}]

with ma.materialization_scope(checkpoint=ma.CheckpointPolicy.every(2)) as scope:
    stage = source
    for _ in range(5):
        stage = scope.checkpoint(
            stage.with_columns((ma.col("x") + 1).alias("x")), replaces=stage,
        )
    result = scope.detach(stage)

assert result.to_dicts() == [{"x": 12}]
```

## Scope and checkpoint lifetime

- `scope.snapshot(rel)` copies immediately. `rel.snapshot()` uses the innermost
  active scope, or reachability-based ownership outside a scope.
- `scope.checkpoint(rel, replaces=previous)` uses the configured policy:
  `EVERY_STAGE` (default), `every(k)`, or `NEVER`. Five calls with `every(2)` copy
  stages 2 and 4. Scope exit never adds an implicit copy.
- Replacement releases the scope's hold on earlier dependencies; a still-live
  sibling relation keeps its physical storage.
- `scope.detach(rel)` transfers all of that scope's snapshots reached by `rel`
  to reachability-based ownership, including dependencies in a join or concat.
  It raises `ValueError` when the relation reaches none of the scope's holdings.
- Scope exit invalidates non-detached snapshots, including derived relations
  and DAG references. Their Mountainash terminals raise
  `MaterializationScopeClosedError`.

Detached and unscoped SQL snapshots remain alive while their native physical
operations or recognized aliases remain reachable. Finalizers only enqueue
deletion. The owning thread drains pending deletion at admitted copy/release
boundaries; active or unobservable transactions defer it. Failed deletion stays
queued until committed cleanup succeeds.

## Batch capture

```python
with ma.materialization_scope() as scope:
    left, right = scope.capture(source, source.filter(ma.col("x") > 0))
    bundle = scope.detach(ma.concat([left, right]))
```

Capture publishes the whole batch only after every copy and terminal check
succeeds. Each input is evaluated once. A failure preserves earlier scope
holdings and retains cleanup ownership of attempted SQL targets. An empty
capture returns `()`.

Inputs must share one backend and, for SQL, one physical connection. SQL capture
uses one transaction. The supported contract is one user with sequential
execution; it makes no concurrent-writer or cross-connection revision guarantee.

## Supported values and SQL preparation

In-process copies cover Polars, pandas, PyArrow, their supported Narwhals
wrappers, and Ibis-Polars. Arrow-backed and nested buffers are copied. Pandas
indexes and categorical storage are independently copied; supported immutable
object cells are retained. Mutable or unsupported object cells/categories and
Polars `Object` columns raise `UnownableSnapshotValueError` rather than publishing
a borrowed or corrupted result.

SQL routes cover SQLite, DuckDB, and PostgreSQL (autocommit enabled or disabled).
They borrow the explicit Ibis connection and use the mountainash-data transaction
adapter. Source-backed qualification does not establish availability of the
required public dependency artifacts.

Public SQL snapshot/capture uses existing compile-only preparation. Plans that
require execution during preparation raise `BackendCapabilityError` with the
original `CompileRequiresExecutionError` cause. Unbound scalar parameters,
unsupported connections, and non-idle/unobservable transaction state are refused.
These operations do not finish or roll back caller-owned transactions.

Internal DAG, validation, logical-terminal, and transport materialization keep
their execution phase and use fresh owned copies where required. Snapshot
finishing retains structured-field restrictions and removes internal diagnostic
markers while preserving user columns.
