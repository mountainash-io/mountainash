# mountainash

**Write data logic once. Run it on Polars, pandas, PyArrow, DuckDB, SQLite, or any Ibis-supported database — without rewriting it.**

mountainash is a Python library for authoring DataFrame expressions, relational pipelines, schemas, and data contracts in a backend-agnostic form, then dispatching them to whichever engine you happen to be using. It does not replace Polars, Ibis, or pandas. It sits one layer up, so you don't have to choose between them.

> **Status: alpha.** The architecture is settled and the test surface is large (≈ 3,000 cross-backend tests, ≈ 90 catalogued cross-backend divergences). Public APIs are stabilising but breaking changes still happen between minor versions. We recommend it for prototyping, internal tools, and projects that can absorb the occasional rename. Don't pin a critical production path to a non-pinned version yet.

---

## Why this exists

If you have ever:

- migrated a codebase from pandas to Polars (or in the other direction),
- maintained two parallel implementations of the same business logic — one in SQL, one in Python,
- written a transformation in a notebook and then had to re-implement it inside a warehouse,
- discovered that your validation library, your transformation library, and your ETL framework all want to own the schema definition,
- watched a junior engineer pick the wrong tool because every option in the data ecosystem looks superficially the same,

…then you have already paid the cost mountainash is designed to remove.

The problem is not that any one of these libraries is bad. The problem is that **data logic is portable in principle but coupled to a runtime in practice**. A filter is a filter. A sum is a sum. A cast from string to date is a cast. The mathematics doesn't care whether you run it on Polars, on DuckDB, or in your local pandas REPL. But the *code* does — and so the choice of runtime has become a choice of dialect, and changing your mind costs you a rewrite.

mountainash separates the two. You write expressions and pipelines once, using an API that mirrors Polars conventions, against a small Substrait-aligned AST. At the call site — when you ask for a result — the AST is compiled to native Polars expressions, Ibis table expressions, or Narwhals operations. The result is the same. The code is the same. Only the runtime changes.

---

## What it gives you

### [Cross-backend execution](features/cross-backend.md)

Three backends are supported out of the box: **Polars** (native, lazy), **Narwhals** (pandas/PyArrow), and **Ibis** (DuckDB, SQLite, and any other Ibis-supported SQL engine). Backend detection is automatic from the type of DataFrame you pass in. Cross-backend tests run on every operation, and intentional per-backend divergences are tracked in a [catalogued registry](features/cross-backend.md#known-divergences).

### [Expressions](features/expressions.md)

Column-level computation: `ma.col("price") * ma.col("qty")`, `ma.col("name").str.lower()`, `ma.when(...).then(...).otherwise(...)`, full datetime/string/list/struct namespaces, aggregates, window functions. The API is Polars-shaped. Internally, every operation is a Substrait function key — so the same expression lowers to native Polars, native Ibis, or native Narwhals without behavioural drift.

### [Relations](features/relations.md)

DataFrame-level pipelines: `ma.relation(df).filter(...).sort(...).group_by(...).agg(...).to_polars()`. The relation API mirrors a subset of Polars LazyFrame and pandas. Cross-type joins (Polars left, pandas right) coerce automatically.

### [TypeSpec and conformance](features/typespec-conform.md)

A serializable type specification that maps cleanly onto Frictionless Table Schema. Compile a TypeSpec into a `conform()` transformation that casts, renames, fills nulls, and validates — driven from the schema, not hand-written column by column. Read and write Frictionless `datapackage.json` descriptors directly.

### [Data contracts](features/datacontracts.md)

Compile any schema source — `TypeSpec`, dict, pandera `DataFrameModel`, Pydantic `BaseModel`, or a Frictionless JSON file — into a `BaseDataContract` class with `.validate(df)`. One schema, every backend.

### [Pipelines](features/pipelines.md)

Multi-step pipelines with typed parameters (`ParamSpec`), explicit dependencies, optional caching, and direct integration into the relation AST. Define a step once with `@step(...)`, compose it with `relation.params(...)`, and collect on any backend.

### [Ternary logic](features/ternary-logic.md)

First-class TRUE / FALSE / UNKNOWN semantics for real-world data where "missing" is not "false". Sentinel-based integer encoding (no NULL propagation traps), automatic booleanization at compile time, and bidirectional coercion between boolean and ternary contexts.

---

## What it isn't

- **Not a new query engine.** mountainash compiles to your existing engines. We don't reimplement Polars, Ibis, or DuckDB.
- **Not a pandas replacement.** If pandas is working for you, keep using it. mountainash lets you keep using it while also being able to lift your code to Polars or DuckDB later.
- **Not a heavyweight framework.** No service to run, no DSL to learn, no schema registry to operate. It's a library you `pip install` and `import`.
- **Not finished.** See the [alpha status note](#status-alpha) above.

---

## What it costs

The abstraction has a real cost. Compilation overhead is small but non-zero — typically a few hundred microseconds per expression tree. For interactive analysis on million-row Polars frames, you will not notice. For tight inner loops dispatching one expression per record, you will, and you should use the backend directly.

There is also an ecosystem cost. Some operations are not yet supported on every backend (Narwhals has the largest gap; see the [divergence catalog](features/cross-backend.md#known-divergences)). When you hit one, you get a clear error pointing at the limitation, not silent wrong answers.

---

## Where to next

- **Look at the [vision](vision.md)** — what mountainash is *for*, beyond the current package.
- **Read a feature page** — start with [cross-backend execution](features/cross-backend.md), [expressions](features/expressions.md), or [relations](features/relations.md).
- **Check the alpha status** — what's stable, what's still moving.

```bash
pip install mountainash
```

---

## Status: alpha

The package is in active development. Specifically:

| Area | State |
|------|-------|
| Expression AST and visitor | Settled — 7 node types, function-key dispatch |
| Polars backend | Most complete; covers virtually all of the public API |
| Ibis backend | Settled but evolving with Ibis upstream; some operations xfail per-backend |
| Narwhals backend | Settled for scalar/aggregate; relational coverage growing |
| Public expression API (`ma.col`, `ma.lit`, etc.) | Stable in shape, occasional renames |
| Public relation API (`ma.relation(...).…`) | Stable in shape, occasional renames |
| TypeSpec / DataPackage | Stable; aligned with Frictionless Table Schema |
| Data contracts | Stable for the supported source formats |
| Pipelines | Recently redesigned (parameter system replaced pushdown in 2026-05); evolving |
| Cross-backend test coverage | ≈ 3,000 parametrised tests; new operations require cross-backend coverage |

We commit to: clear errors over silent divergence, semantic versioning once we cut 1.0, and a published catalog of every intentional per-backend deviation.

We do not commit to: zero API churn before 1.0, every operation on every backend, or wire-format stability for the AST.
