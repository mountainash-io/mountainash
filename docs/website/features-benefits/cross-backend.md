# Cross-backend execution vs. picking one library

## What we built this to address

We've watched the same arc play out in team after team. A codebase picks pandas because pandas is the default, then discovers Polars and budgets nine months for the rewrite. A team picks Polars for speed and then absorbs a stream of contractors who arrive expecting pandas. An analytics group migrates to a DuckDB-backed warehouse and somebody is now responsible for translating the existing validation logic into SQL.

None of these rewrites changed what the code *meant*. The mathematics didn't move. The data didn't change shape. Only the dialect did — and the cost was paid in engineer time, in regression risk, in tests rewritten, in subtle behavioural drift that nobody noticed until it broke.

Picking Ibis up-front gets some of this back, but in practice many projects still need pandas locally for tests, plus Polars on the box where speed matters, plus the production warehouse for actual reporting. Three runtimes; one logic; three implementations.

This is the cost we set out to retire.

## How we approach it

The logic is written once. The runtime is the terminal call.

```python
result = (
    ma.relation(df)
      .filter(ma.col("amount").gt(100))
      .group_by("region")
      .agg(ma.col("amount").sum().alias("total"))
      .to_polars()    # ← only this line knows the target
)
```

When the terminal call runs, mountainash detects the backend from the input frame (or accepts an explicit `execute_on=`) and compiles the AST to native operations: Polars frame → native `pl.Expr` chains; pandas frame → Narwhals operations; Ibis table → SQL pushed to whichever engine that table is connected to.

The compilation is mechanical and inspectable. We didn't build a shadow execution engine. The output of compilation is what someone would have written by hand against that library, which keeps the runtime cost predictable and the debugging story sane.

## Side-by-side

The same filter + groupby + sum, written three times by hand vs. once through mountainash:

```python
# Polars
df.filter(pl.col("amount") > 100).group_by("region").agg(pl.col("amount").sum().alias("total"))

# pandas
(df.loc[df["amount"] > 100]
   .groupby("region", as_index=False)["amount"]
   .sum()
   .rename(columns={"amount": "total"}))

# Ibis
t.filter(t.amount > 100).group_by("region").aggregate(total=t.amount.sum())

# mountainash — same chain regardless of which of the three above is the input
(ma.relation(input)
   .filter(ma.col("amount").gt(100))
   .group_by("region")
   .agg(ma.col("amount").sum().alias("total")))
```

The mountainash form is the same length as the Polars form. We didn't invent a new dialect; we lifted Polars conventions because we think they're the cleanest in Python and inventing a different shape would have been gratuitous.

## What this costs

- **A small per-call overhead.** Compilation walks the AST. For a non-trivial expression, count it as a few hundred microseconds. Interactive work and ordinary batch pipelines absorb it without notice; per-record dispatch loops don't, and those should call the backend directly.
- **Per-backend gaps.** Some operations aren't supported on every backend (Narwhals is the largest gap; Ibis-Polars has interval limitations; SQLite has no datetime type). We catalog every gap — ≈ 94 entries today — and surface a clear error at the call site. The discipline is: no silent wrong answers.

## Where we'd point elsewhere

- **Single-runtime projects.** If a codebase will live and die on Polars (or pandas, or DuckDB), the abstraction tax buys nothing. Use the library directly.
- **Per-record dispatch loops.** Compile-once-call-many is fine; compile-per-record is not what mountainash is for.
- **An operation that's missing on the required target backend.** The divergence catalog is the place to check before committing.

## What this enables downstream

Once a relation chain is backend-agnostic, the rest of the library can be:

- [Schemas](typespec-conform.md) authored once; conform works on any backend.
- [Data contracts](datacontracts.md) validating on any backend.
- [Pipelines](pipelines.md) composed with relations, so a pipeline step's output flows into a relation that ends on the backend the caller needs.
- [Expressions](expressions.md) — the building blocks — themselves cross-backend.

The portability isn't a feature on top; it's the substrate everything else stands on.

## Related

- Technical: [Cross-backend execution](../features-technical/cross-backend.md)
- Technical: [Known divergences guide](../../guides/known-divergences.md)
