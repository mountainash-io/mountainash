# Quickstart

Mountainash is a composable logic layer: write expressions and relational pipelines once, run them on Polars, Narwhals (pandas/PyArrow), or Ibis (SQL). This guide walks the public surface.

## Install

```bash
uv pip install mountainash
```

For Ibis backends:

```bash
uv pip install 'mountainash[ibis]'
```

## Two APIs

| API | Returns | Purpose |
|-----|---------|---------|
| `ma.col`, `ma.lit`, `ma.when`, … | `Expression` | Column-level computation (filters, projections, aggregations) |
| `ma.relation(df)`, `ma.concat([…])` | `Relation` | DataFrame-level pipelines (filter, sort, join, group_by, conform, …) |

Both build a backend-agnostic AST. Backend dispatch happens at terminal operations (`.compile(df)` for expressions, `.collect()` / `.to_polars()` / `.to_pandas()` for relations).

## Expressions

```python
import mountainash as ma
import polars as pl

df = pl.DataFrame({"x": [1, 2, 3, 4], "name": ["a", "b", "a", "c"]})

expr = (ma.col("x") * 2).alias("x2")
df.with_columns(expr.compile(df))     # Polars expression compiled at the call site
```

Common entry points (all re-exported on `ma.`):

- **Columns / literals:** `col`, `lit`, `duration`, `native`
- **Conditionals:** `when(cond).then(a).otherwise(b)`
- **Coalesce / extremes:** `coalesce`, `greatest`, `least`, `min_horizontal`, `max_horizontal`
- **Boolean reductions:** `all_horizontal`, `any_horizontal`
- **Aggregations:** `count_records`, `corr`, `median`, `quantile`, `sum_horizontal`
- **Namespaces:** `ma.col("x").str.lower()`, `ma.col("t").dt.year()`, `ma.col("name").name.suffix("_v2")`
- **Ternary logic:** `t_col`, `always_true`, `always_false`, `always_unknown`

## Relations

```python
import mountainash as ma
import polars as pl

df = pl.DataFrame({"age": [25, 32, 19, 45], "name": ["a", "b", "c", "d"]})

result = (
    ma.relation(df)
      .filter(ma.col("age").gt(30))
      .sort("name")
      .select("name", "age")
      .head(10)
      .to_polars()
)
```

The same chain works on a pandas DataFrame (`.to_pandas()`) or an Ibis table (`.execute()`). Backend is detected from the DataFrame you pass to `ma.relation()`.

### Grouped aggregations

```python
ma.relation(df).group_by("category").agg(
    ma.col("sales").sum().alias("total"),
    ma.col("sales").mean().alias("avg"),
)
```

`group_by()` returns a `GroupedRelation` that exposes only `.agg()`.

### Joins (cross-type)

```python
polars_left  = pl.DataFrame({"id": [1, 2], "x": [10, 20]})
pandas_right = pd.DataFrame({"id": [1, 2], "y": [100, 200]})

ma.relation(polars_left).join(pandas_right, on="id", how="inner").to_polars()
```

Cross-type joins automatically coerce; use `execute_on=` for explicit control.

### Struct expansion

```python
ma.relation(df).unnest("address", separator="_")
# columns address_street, address_city, …
```

See [unnest.md](unnest.md). Not yet implemented on Narwhals.

## Schemas (TypeSpec) and Conformance

```python
spec = ma.typespec({"id": "integer", "amount": "number", "ts": "datetime"})

ma.relation(df).conform(spec).to_polars()
```

`conform()` builds a `ProjectRelNode` from TypeSpec fields — cross-backend automatic. The Frictionless Data Package model is the canonical multi-resource form:

```python
pkg = ma.DataPackage.from_descriptor("datapackage.json")
dag = pkg.to_relation_dag()
df  = dag.collect("orders")
```

## Data Contracts

```python
Contract = ma.datacontract(spec)        # compiles TypeSpec → contract class
Contract.validate(df)
```

Accepts: `TypeSpec`, `dict`, pandera `DataFrameModel`, Pydantic `BaseModel`, or a Frictionless JSON path.

## Pipelines

For multi-step pipelines with caching, parameter binding, and orchestration, see [pipelines.md](pipelines.md).

## Where to go next

- [Pipeline framework guide](pipelines.md) — multi-step pipelines, `ParamSpec`, caching
- [`unnest()` reference](unnest.md) — struct column expansion
- [Adding operations](adding-operations.md) — contributor guide for new functions/relations
- [Extension points](extension-points.md) — registries for third-party node types and optimisations
- [Known divergences](../known-divergences.md) — catalog of intentional per-backend differences
