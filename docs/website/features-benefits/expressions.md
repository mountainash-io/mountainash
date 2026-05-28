# Expressions vs. per-library DSLs and embedded SQL

## What we built this to address

Every DataFrame library has its own expression DSL, and the dialect is part of the lock-in. Polars expressions don't lift to pandas. pandas `.apply()` is opaque to Polars. Ibis expressions look familiar but carry their own quirks. SQL strings inside Python break refactoring tools, evade linting, and require their own context for type checking.

We watched teams with business logic that needed to run in three of those four worlds settle on one of three uncomfortable patterns: maintain parallel implementations and keep them in sync by hand; pick one library and convert at the boundary, which works until somebody adds an operation on the wrong side; or fall back to SQL strings and give up most of the safety the host language gave them. None of these is broken. All of them cost more than they should.

## How we approach it

A mountainash expression is a small, inspectable Python tree:

```python
expr = (ma.col("price") * ma.col("qty")).alias("revenue")
```

Nothing has happened yet. `expr` is a value. At the call site it compiles against whichever frame is in front of it, and produces a native expression in that library's dialect:

```python
expr.compile(polars_df)    # → pl.Expr
expr.compile(pandas_df)    # → nw.Expr (compiled through Narwhals)
expr.compile(ibis_table)   # → ir.Value
```

The shape of the API is deliberately Polars-shaped. Polars has the cleanest expression model in the Python ecosystem, and we don't think there's a good reason to invent a different one:

```python
# Polars
pl.col("name").str.lower().str.starts_with("a")

# mountainash
ma.col("name").str.lower().str.starts_with("a")
```

The only difference is the leading `pl` / `ma`. The namespacing, the method names, the kwargs — all preserved.

## Side-by-side: embedded SQL vs. mountainash

```python
# Embedded SQL
query = """
SELECT
  customer_id,
  CASE WHEN amount > 100 THEN amount * 0.9 ELSE amount END AS discounted
FROM orders
WHERE region IN ('E', 'W')
"""
# Type-unsafe, refactoring-hostile, no IDE help, hard to compose programmatically.
```

```python
# mountainash
(ma.relation(orders)
   .filter(ma.col("region").is_in(["E", "W"]))
   .with_columns(
       ma.when(ma.col("amount").gt(100))
         .then(ma.col("amount") * 0.9)
         .otherwise(ma.col("amount"))
         .alias("discounted")
   )
   .select("customer_id", "discounted"))
# Typed, refactor-friendly, composable with the rest of the relation chain.
```

The mountainash form is longer than the SQL string. We accept that trade. The Python form carries its own types, integrates with linters, can be composed with other expressions programmatically, and runs on Polars / pandas / Ibis without rewrite.

## What an expression can do that a string can't

- **Be inspected.** The AST is data. We can walk it, transform it, serialise it.
- **Be composed.** Multiple expressions can be combined programmatically; SQL strings can only be string-concatenated.
- **Be type-checked.** Polars/pandas/Ibis errors fire at the right call site; SQL errors fire at execution against a remote engine.
- **Be reused.** A mountainash expression can be `import`'d. A reusable SQL fragment is a template string with all of template strings' problems.
- **Be tested.** A function returning an expression unit-tests naturally. A function returning a SQL string only unit-tests by string comparison.

## Side-by-side: pandas `.apply()` vs. mountainash

```python
# pandas, opaque to other engines
df["score"] = df.apply(lambda r: r["a"] * 2 if r["b"] > 5 else 0, axis=1)
```

```python
# mountainash, lifts to Polars or Ibis identically
expr = ma.when(ma.col("b").gt(5)).then(ma.col("a") * 2).otherwise(0).alias("score")
df.with_columns(expr.compile(df))
```

`.apply()` runs row-by-row in Python and never lowers to vectorised execution. The mountainash form compiles to vectorised native expressions on every backend.

## What this costs

- **A small per-call overhead** to compile the AST.
- **A common API for everyone.** Library-specific features that we haven't exposed can't be reached through the abstraction. `ma.native(pl.col("x").map_batches(...))` is an honest escape hatch for the cases that need it; using it pins that branch to that backend.

## Where we'd point elsewhere

- **Single-library projects with no migration in their future.** The abstraction earns nothing here.
- **A required single-library feature that isn't in the mountainash surface.** Check before committing.
- **Exploratory notebook code.** For "what does this data look like" work, the native library is shorter. We'd reach for `ma.col(...)` when the code is going to live somewhere downstream.

## Related

- Technical: [Expressions](../features-technical/expressions.md)
- Comparison: [Cross-backend execution](cross-backend.md)
