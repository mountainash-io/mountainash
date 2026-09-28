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
| Join | `.join(other, on=..., how=..., execute_on=...)`, `.cross_join(other, execute_on=...)`, `.join_asof(..., execute_on=...)` (cross-type allowed) |
| Group / aggregate | `.group_by(*keys).agg(*exprs)` |
| Set ops | `.union(other)`, `.intersection(other)`, `.difference(other)` |
| Unique / null | `.unique(*cols)`, `.drop_nulls(subset=...)`, `.drop_nans(subset=...)`, `.has_nulls()`, `.null_count()` |
| Sampling | `.sample(n=..., fraction=...)`, `.with_row_index()` |
| Pivots | `.unpivot(on=..., index=...)`, `.pivot(on=..., index=...)` |
| Struct expansion | `.unnest(*cols, separator="_")` |
| Conformance | `.conform(spec)` — see [TypeSpec & conformance](typespec-conform.md) |
| Terminal | `.to_polars()`, `.to_pandas()`, `.collect()`, `.execute()`, `.to_dicts()`, `.to_dict()` |
| Pipeline params | `.params(**kwargs)` — see [Pipelines](pipelines.md) |

`.group_by()` returns a `GroupedRelation` that exposes only `.agg()` — by design, so you can't accidentally chain a filter onto a partial group.

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
- [TypeSpec & conformance](typespec-conform.md) — schema-driven `.conform()`
- [Pipelines](pipelines.md) — named, parameter-bound relations
