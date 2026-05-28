# Relations vs. per-library DataFrame pipelines

## What we built this to address

Every DataFrame library has its own pipeline idiom. Polars chains expressions on `LazyFrame`. pandas chains method calls (with the method-chaining quirks, indexing surprises, and the perennial `inplace=` debate). Ibis chains operations on `Table`. The semantics rhyme — a filter is a filter, an aggregation is an aggregation — but the syntax is different enough that translating a 20-line chain between two of them is a real chunk of work.

We've seen this cost paid repeatedly in cross-team work, in contractor onboarding, and in engine migrations. And it compounds once joins, group-bys, and window functions enter the picture: Polars' `over()` is a different shape from pandas' `.transform()`; Ibis' aggregation grammar uses keyword arguments where Polars uses `.agg()`. Each is fine on its own; together they're noise nobody learned the language to write.

## How we approach it

One pipeline. It runs anywhere.

```python
result = (
    ma.relation(df)
      .filter(ma.col("age").gt(30))
      .group_by("region")
      .agg(
          ma.col("score").mean().alias("avg"),
          ma.col("score").std().alias("sd"),
      )
      .sort("region")
      .to_polars()   # or .to_pandas(), or .execute() on an Ibis table
)
```

The same chain. The same method names. The same expressions inside the aggregation. The only line that knows what runtime it's targeting is the terminal call.

### Cross-type joins

Two frames from two backends, joined without a manual conversion:

```python
ma.relation(polars_left).join(pandas_right, on="id", how="inner").to_polars()
```

One side is coerced. There's a sensible default for the coercion target; `execute_on=` overrides it explicitly.

## Side-by-side: same chain, three ways

```python
# Polars
(df
  .lazy()
  .filter(pl.col("age") > 30)
  .group_by("region")
  .agg(pl.col("score").mean().alias("avg"), pl.col("score").std().alias("sd"))
  .sort("region")
  .collect())

# pandas
(df[df["age"] > 30]
  .groupby("region", as_index=False)
  .agg(avg=("score", "mean"), sd=("score", "std"))
  .sort_values("region"))

# Ibis
(t.filter(t.age > 30)
  .group_by("region")
  .aggregate(avg=t.score.mean(), sd=t.score.std())
  .order_by("region"))

# mountainash — same code regardless of which of the above is the input
(ma.relation(input)
  .filter(ma.col("age").gt(30))
  .group_by("region")
  .agg(ma.col("score").mean().alias("avg"), ma.col("score").std().alias("sd"))
  .sort("region"))
```

The mountainash form's main legibility win is that an engineer who came in from any of the three backgrounds can read it without learning a fourth dialect.

## Build now, execute later

Like Polars' LazyFrame, a relation chain isn't evaluated until requested. We made this explicit because it keeps several downstream things possible:

- The AST can be inspected before running.
- A relation can be passed around as a value — to a function, to a test, to a serialiser.
- Optimisation passes can run before execution.
- The runtime can be chosen at the latest possible moment.

```python
r = ma.relation(df).filter(ma.col("amount").gt(100)).group_by("region").agg(ma.col("amount").sum())

# Decision deferred
r.to_polars()      # local Polars
r.to_pandas()      # convert through Narwhals
# or hand `r` to a worker that owns an Ibis table and can .execute() it there
```

A pandas chain doesn't separate "recipe" from "result." A Polars `LazyFrame` does, but it's pinned to Polars. A relation does, and isn't.

## Why this matters across a team

When half a team uses pandas (notebooks, ad-hoc analysis) and half uses Polars (batch pipelines), the typical state is two libraries' worth of helper code — one pandas helper, one Polars helper, doing the same thing. A relation that wraps either kind of frame collapses that into one helper. Notebook authors and pipeline authors write the same code.

This matters less for small, stable teams. It matters more as teams grow, as contractors come in, and as the project lives long enough to outlast a library generation.

## What this costs

- **Compilation overhead.** Same as for expressions — small but non-zero.
- **Surface coverage.** The relation API covers the operations needed for most analytical pipelines, but it isn't a 1:1 mapping of every Polars feature. The escape hatch below is the honest answer when a gap matters.

### Native fallback

```python
ma.relation(df).pipe(lambda r: r._compile_polars().filter(pl.col("x") > 0))
```

A drop into native Polars for one operation, with the rest of the pipeline staying inside mountainash. The branch becomes Polars-specific, but the rest of the relation chain is portable and the escape is visible in the code.

## Where we'd point elsewhere

- **Single-library projects.** The native path is shorter and the abstraction earns nothing.
- **A required feature outside the relation surface.** The surface table on the [technical relations page](../features-technical/relations.md) is the reference.
- **Exploratory notebook work.** Native is shorter. We'd reach for relations when the code becomes part of something durable.

## Related

- Technical: [Relations](../features-technical/relations.md)
- Comparison: [Expressions](expressions.md)
- Comparison: [Pipelines](pipelines.md)
