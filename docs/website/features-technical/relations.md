# Relations

A relation is a DataFrame-level query plan: filter, sort, join, group_by, aggregate, project, conform. mountainash relations are backend-agnostic — the same chain runs on Polars, pandas (via Narwhals), or any Ibis-supported SQL engine.

## The model

```python
import mountainash as ma
import polars as pl

df = pl.DataFrame({"age": [25, 32, 19, 45], "name": ["a", "b", "c", "d"], "region": ["E", "W", "E", "W"]})

result = (
    ma.relation(df)
      .filter(ma.col("age").gt(30))
      .group_by("region")
      .agg(ma.col("age").mean().alias("avg_age"))
      .sort("region")
      .to_polars()
)
```

`ma.relation(df)` wraps the frame in a `Relation` object — backend-agnostic. Each chained call adds a node to a relational AST. The terminal call (`.to_polars()` here) triggers compilation: the visitor walks the AST, dispatches each node to the detected backend, and returns the result.

### Shared recipes within one execution

Repeated references to the same relation recipe can reuse native compilation and
qualified transfers within a single root compilation. For example,
`ma.concat([branch, branch])` can compile `branch` once rather than rebuilding it
for each occurrence. Independently constructed recipes remain distinct, even if
their data and operations are equal. Physical destinations remain separate.

This is not a persistent result cache. Each terminal invocation starts fresh,
including after a failed execution. Named DAG resources retain their existing
capture and ownership rules.

Reusing a deferred plan does not imply sharing its evaluated rows. Opaque native
lazy plans remain supported, but cross-backend transfers may still evaluate each
occurrence. Sampling, host-clock expressions, custom lowerings and eager readers
retain their evaluation behavior. No cache flag or purity declaration is required.


## The AST

The relation AST has 10 node types, mapped onto Substrait logical relations:

| Node | Operation |
|------|-----------|
| `ReadRelNode` | Source frame |
| `FilterRelNode` | Row predicate |
| `ProjectRelNode` | Column selection / addition / renaming |
| `SortRelNode` | Ordering |
| `FetchRelNode` | Head / tail / slice |
| `JoinRelNode` | Inner / left / right / outer / semi / anti / cross / asof |
| `AggregateRelNode` | Group-by aggregations |
| `SetRelNode` | Union / intersection / difference |
| `ExtensionRelNode` | Mountainash-specific ops (unnest, drop_nans, top_k, …) |
| `ReadResourceRelNode` | Frictionless DataResource load |

Plus two thin orchestration nodes (`RefRelNode`, `ParamsRelNode`) used by the [DAG](#dag-and-frictionless) and the [pipeline framework](pipelines.md).

The minimal AST is deliberate — most operations are parameter values on these nodes, not new node types. Adding a new relation operation is a structured process; see [Adding operations](../../guides/adding-operations.md).

## What's in the API

| Operation | Method |
|-----------|--------|
| Row filter | `.filter(expr)`, `.remove(expr)` |
| Projection | `.select(*cols)`, `.with_columns(*exprs)`, `.drop(*cols)`, `.rename({old: new})` |
| Sort / fetch | `.sort(*by, descending=...)`, `.head(n)`, `.tail(n)`, `.slice(offset, length)` |
| Join | `.join(other, on=... \| left_on=..., right_on=..., how=..., suffix=..., coalesce=..., execute_on=...)`, `.cross_join(other, execute_on=...)`, `.join_asof(..., execute_on=...)` (cross-type allowed) |
| Group / aggregate | `.group_by(*keys).agg(*exprs)` |
| Concatenation | `ma.concat(relations, distinct=False, timezone=None)` |
| Unique / null | `.unique(*cols)`, `.drop_nulls(subset=...)`, `.drop_nans(subset=...)`, `.has_nulls()`, `.null_count()` |
| Sampling | `.sample(n=..., fraction=...)`, `.with_row_index()` |
| Pivots | `.unpivot(on=..., index=...)`, `.pivot(on=..., index=...)` |
| Struct expansion | `.unnest(*cols, separator="_")` |
| Conformance | `.conform(schema)` — see [shared schemas & conformance](typespec-conform.md) |
| Terminal | `.to_polars()`, `.to_pandas()`, `.collect()`, `.execute()`, `.to_dicts()`, `.to_dict()` |
| Pipeline params | `.params(**kwargs)` — see [Pipelines](pipelines.md) |

`.group_by()` returns a `GroupedRelation` that exposes only `.agg()` — by design, so you can't accidentally chain a filter onto a partial group.

### Deferred sampling and positional operations

Sampling lazy inputs stays deferred through construction, schema inspection,
explanation and compilation. Native metadata/catalog inspection is allowed;
evaluating results for schema completion still requires explicit
`collect_schema(allow_execution=True)`.

Native Polars, DuckDB, Spark/Connect and supported SQLFrame plans preserve
whole rows. Dask uses deferred execution over one global partition. Native
collection retains the provider's result format: Arrow for DuckDB and
Spark-like providers, pandas for Dask. Explicit `.to_polars()` remains a conversion.
These implementations use sorting/windows or global partitioning; they do not
promise bounded-memory streaming.

Fixed seeds repeat on stable ordered inputs, but seed-to-row mappings need not
match the former eager sampler. Spark retains its native random-plan and
query-stage reuse behavior; collecting an unseeded plan repeatedly does not
promise a new draw.

Positive-offset slicing on Narwhals/Dask is declared unsupported because the
upstream offset implementation can read source rows during construction.
Checked execution raises `BackendCapabilityError` before source evaluation.
Zero-offset slices, head and tail remain supported. Explicitly disabling the
capability gate does not make positive offsets lazy.

Deferred backlog item 355 tracks an upstream Narwhals-DuckDB projection defect:
`drop`, `rename` and `with_columns` mishandle retained literal `"*"` columns,
dotted names and names containing double quotes. Native-provider sampling
exposes these failures in subsequent projections; no workaround or additional
unsupported declaration is applied. The owner has excluded this follow-up from
item 351's delivery gates; this is not a claim of full Narwhals-backend support.

### Sampling on Ibis SQL

`.sample(n=k)` selects exactly `min(k, row_count)` rows without replacement.
Its random ordering and limit remain deferred; compilation does not execute a
count query. Oversized Python integer requests still return all available rows.
Sorted `.tail(k)` likewise keeps its count and offset inside the deferred query.

Exact-count sampling with `seed` specified is rejected by capability policy for
Ibis DuckDB, SQLite, PostgreSQL, MySQL, SingleStoreDB and Exasol. This includes
`seed=0`. Fractional sampling retains the selected backend's native behavior,
including seeded support where available; it does not promise an exact row count.
Disabling the gate does not make seeded exact-count sampling supported.

Data-contract validation follows the same sampling support:
`contract.validate_datacontract(table, sample=k)` and its `_quick` counterpart
leave an omitted `random_seed` unset. Validation is an explicit terminal: it
holds one native sample snapshot for the run, and failure reporting uses the
validated rows rather than evaluating the sample again. Explicit `random_seed`
values remain unsupported for the Ibis SQL dialects listed above. The old
empty-sample `limit(k)` fallback is no longer needed with exact-count sampling.


### Timestamp concatenation

```python
combined = ma.concat([left, right])                  # Precision widening only
utc_rows = ma.concat([left, right], timezone="UTC")  # Normalize aware columns
unique = ma.concat([left, right], distinct=True, timezone="America/New_York")
```

On Polars, Narwhals (including pandas) and Ibis-DuckDB/Ibis-Polars, concat
widens corresponding top-level timestamp columns to the finest input
precision. By default, aware columns must share a zone for this preparation;
different zones retain native compatibility behavior rather than being
converted implicitly.

An explicit IANA timezone target converts each all-aware column independently,
preserving instants. Naive columns remain naive; a target does not interpret
mixed naive/aware values. Nested timestamps are not traversed. Nulls stay null,
typed empty columns contribute their declared precision, and distinct compares
complete rows after preparation. A single input also honors the timezone target.

SQLite timestamp reconciliation is **unsupported**. Default concat retains
its existing native behavior; an explicit target on an all-aware column raises
`BackendCapabilityError`, including a UTC target. No normalization is performed
at egress to hide this limitation.

Preparation happens after existing execution-location/transfer resolution.
It cannot restore precision already lost at ingestion (notably aware ns values
in DuckDB's us storage), and native timestamp range limits still apply.


### Declared dataclass source schemas

For a flat dataclass instance or homogeneous list of instances, schema inspection
uses declared fields and scalar types without scanning rows or reading field
values. Nullable scalar annotations retain their declared dtype even when every
value is null or the first non-null value occurs after row 100. This allows
dataclass sources to compose through conformance and structured joins without
materializing either input first.

Only instance fields are exposed; `ClassVar` and `InitVar` are excluded. If
annotation extraction fails, known field names remain with `UNKNOWN` types.
Successfully extracted `ANY` declarations, including unresolved multi-type unions,
remain `UNCONSTRAINED`. Nested dataclass ingress is not covered by this guarantee.

No class scan is performed for mixed-class lists. They remain accepted by ingress,
but additional runtime fields may be absent from inferred metadata; accurate
mixed-class schema inference and composition are not guaranteed. The native
100-row inference fallback is unchanged.

### Projection schema introspection

`.schema` uses the plan and available source metadata, without compiling or
executing it. Ordinary field selections retain their source dtype through aliases
and name-only transformations, including selectors whose output names are known.
Computed projections report `SchemaTypeStatus.UNKNOWN`, even when replacing an
existing column with the same name. A cast or Decimal arithmetic expression does
not promise its executed precision through this best-effort metadata.

Decimal conform declarations remain inspectable after such projections: unknown
source evidence does not establish a conversion requirement. Execution still
checks the native type and requires explicit rounding when conversion is needed.
Authors remain responsible for sufficient Decimal precision and explicit widening.

### Row indices and partial schemas

`with_row_index(name="index")` assigns native zero-based ordinals. Its dtype,
column position and name-collision behavior follow the backend. It is not a
persistent row identity: SQL routes promise neither output row order nor
repeatable row-to-ordinal assignment across executions. In particular,
`sort(...).with_row_index()` does not order the SQL numbering window, and
independently indexed chunks do not share a global sequence. Ordered native
frames retain their documented position semantics.

Schema inspection does not execute the plan. When the native route is known,
the ordinal's dtype and column placement are reported. When it is unresolved,
inspection retains known fields and includes the ordinal with `UNKNOWN` dtype.
A new ordinal name is appended to that partial mapping for presentation, not
as a promise of native column order. `.columns` and `.width` then describe
available metadata, not a certified complete source schema. Missing metadata
alone does not add an error; existing invalid-plan errors still apply.


### Projection output names

`select` and `with_columns` use portable names for resolvable single-output
Mountainash expressions. For example,
`.with_columns(ma.col("n").fill_null(0))` replaces `n`, including on Ibis;
`.with_columns(ma.col("n").fill_null(0).alias("filled_n"))` adds `filled_n` and
retains `n`. Membership (`ma.col("n").is_in([2, 4])`) also uses `n`, so alias it
to `is_member` to retain a separate result. Duplicate resolved outputs now fail
on all backends, including Narwhals-pandas.

See [Projection output names and migration](../../guides/projection-naming.md)
for composition rules, requires-alias operations, empty-name limitations and
native/selector schema boundaries. Standalone compilation and grouped aggregation
keep their existing naming behavior.

## Cross-type joins

```python
polars_left  = pl.DataFrame({"id": [1, 2], "x": [10, 20]})
pandas_right = pd.DataFrame({"id": [1, 2], "y": [100, 200]})

ma.relation(polars_left).join(pandas_right, on="id", how="inner").to_polars()
```

The join runs at the left operand's **resulting location** by default;
`execute_on="right"` chooses the right one's actual location without swapping
join operands. The rule also covers `cross_join` and `join_asof`. Nested joins
keep their own targets; a union executes at input zero's resulting location,
transporting other inputs when necessary. For Ibis, this is a specific
connection, not merely `"ibis"` or `"ibis-duckdb"`:

```python
import ibis
import pyarrow as pa
import mountainash as ma

source = ibis.duckdb.connect()
destination = ibis.duckdb.connect()
left = source.create_table("left_ids", pa.table({"id": [1, 2]}))
right = destination.create_table("right_ids", pa.table({"id": [2]}))
plan = ma.relation(left).join(right, on="id", execute_on="right")
assert plan.to_dicts() == [{"id": 2}]
assert plan.collect()._find_backend(use_default=False) is destination
```

`backend="ibis"` is a family override, not a database connection; it cannot
contradict an explicit join target. A selected Ibis memtable plan can borrow a
bound Ibis peer's connection, but with no bound peer it now raises an
unresolved-target error, including for materializing terminals. Supply a bound
table to migrate from an implicit-default memtable authority. `.to_polars()`
chooses output representation, not execution placement.

All three join builders accept the same placement argument:

```python
import polars as pl
import mountainash as ma

left = pl.DataFrame({"id": [1, 2]})
right = pl.DataFrame({"id": [2], "value": [10]})
assert ma.relation(left).join(right, on="id", execute_on="right").to_dicts() == [
    {"id": 2, "value": 10}
]
assert ma.relation(left).cross_join(right, execute_on="left").to_polars().height == 2
events = pl.DataFrame({"time": [2, 4]})
history = pl.DataFrame({"time": [1, 3], "rate": [10, 30]})
assert ma.relation(events).join_asof(
    history, on="time", execute_on="right"
).to_dict()["rate"] == [10, 30]
```

## Join output columns

Keyed joins (`inner`, `left`, `right`, `outer`) produce the same columns on every
backend, and `.columns` matches what collection returns:

- all left columns in left order, then all right columns in right order;
- a right column whose name exists on the left gets `suffix` (default `_right`);
  if that name is also taken, `_1`, `_2`, … is appended and a `UserWarning` is
  emitted at execution;
- `coalesce` decides whether key pairs merge into the left key column. By
  default keys declared with `on` merge, while `left_on`/`right_on` keep both
  keys. For `right`/`outer` joins the merged key holds `coalesce(left, right)`.

```python
import polars as pl
import mountainash as ma

orders = pl.DataFrame({"order_id": [1, 2], "customer_id": [10, 11]})
customers = pl.DataFrame({"id": [10, 12], "name": ["Ada", "Bo"]})

kept = ma.relation(orders).join(customers, left_on="customer_id", right_on="id", how="left")
assert kept.columns == ["order_id", "customer_id", "id", "name"]

merged = ma.relation(orders).join(
    customers, left_on="customer_id", right_on="id", how="outer", coalesce=True
)
assert merged.columns == ["order_id", "customer_id", "name"]
assert sorted(merged.to_dict()["customer_id"]) == [10, 11, 12]
```

Semi and anti joins return left columns only.

## Build-then-collect semantics

Like Polars' LazyFrame, the relation chain is not evaluated until you ask for a result:

```python
r = (
    ma.relation(df)
      .filter(ma.col("amount").gt(100))
      .group_by("region")
      .agg(ma.col("amount").sum())
)
# No work has happened. r is a Relation wrapping an AST.

r.to_polars()    # Now the AST is compiled to pl.LazyFrame ops and .collect()'d.
r.to_pandas()    # Or compile the same AST through Narwhals.
```

`.compile()` does not execute deferred foreign inputs to satisfy a join or
union transfer; it raises a compile-requires-execution error directing you to
`.collect()`. `.explain()` describes target locations and required transfers
without executing them. Already-eager compile-safe conversions remain possible.

You can interrogate the relation between build and collect — print the AST, run an optimisation pass, pickle it, send it to a remote worker.

## DAG and Frictionless

For multi-relation workflows, group relations into a `RelationDAG`:

```python
dag = ma.RelationDAG()
dag.add("orders",    ma.relation(orders_df))
dag.add("customers", ma.relation(customers_df))
dag.add(
    "enriched",
    dag.ref("orders").join(dag.ref("customers"), on="customer_id")
)
enriched_df = dag.collect("enriched")
```

`dag.ref(name)` is a placeholder that resolves at collect time. The DAG topologically sorts producers and materialises each upstream only once.

The DAG bridges in both directions to Frictionless Data Packages:

```python
pkg = ma.DataPackage.from_descriptor("datapackage.json")
dag = pkg.to_relation_dag()
df  = dag.collect("orders")

# Round-trip
pkg2 = dag.to_package()
pkg2.write("./out/datapackage.json")
```

`DataResource.table_schema` stores the raw Frictionless schema dict, so a `datapackage.json` round-trips byte-equivalent.

## Two-edge graph model

Foreign keys in a DataPackage become **constraint edges** in the DAG — metadata about referential relationships. They are deliberately separate from **dependency edges**, which drive collect order. A DataPackage read from disk yields N independently-loadable resources with zero dependency edges; the FK constraints are still present in the graph for whatever wants to consult them.

This separation matters because foreign keys are not "load order." Confusing the two leads to spurious cascades.

## Native fallback

If you need a Polars operation that mountainash doesn't expose:

```python
ma.relation(df).pipe(lambda r: r._compile_polars().filter(pl.col("x") > 0))
```

You drop into native Polars, do the thing, and the rest of your pipeline is still mountainash. This pins that branch to that backend, but it's an honest escape hatch.

## Related

- [Expressions](expressions.md) — what goes inside `.filter()`, `.with_columns()`, `.agg()`
- [Cross-backend execution](cross-backend.md) — how the same relation runs on three backends
- [Shared schemas & conformance](typespec-conform.md) — schema-driven `.conform()`
- [Pipelines](pipelines.md) — named, parameter-bound relations
