# Vision

## A shared language for data work

The premise of mountainash is small and, we think, correct: **data logic should outlive the engine that ran it**.

A SQL query, written against a particular database in 2010, has likely been rewritten at least once — into a different SQL dialect, into a pandas pipeline, into a Spark job, into a Polars expression, into a dbt model. The mathematics did not change. The data did not change. Only the runtime changed. And each rewrite was paid for in engineer time, in regression risk, in tests rewritten, in subtle behavioural drift that nobody noticed until it broke.

This is the cost we want to retire.

The destination is a Python library where the entire vocabulary of analytical data work — filters, projections, joins, aggregations, window functions, schema casts, validations, transformations, business rules, generation — is expressible in one form that compiles to whichever engine you need today and whichever engine you need next. The form is Polars-shaped because Polars has the cleanest expression model in Python. The internals are Substrait-aligned because Substrait is the closest thing the industry has to a portable algebra. The compilation targets are Polars, Ibis, Narwhals, and — over time — direct backends like DataFusion, DuckDB, Spark, and any SQL warehouse with a serialisable plan format.

## What "virtually any data" means

The library starts with DataFrames because DataFrames are where Python data work happens. But the abstraction is not really about DataFrames. It is about **named, typed, multi-row, multi-column data with a relational algebra over it** — which describes:

- a Polars LazyFrame
- a pandas DataFrame
- an Ibis table (and the SQL warehouse behind it)
- a list of dicts
- a list of dataclasses or Pydantic models
- a Frictionless DataResource pointing at a CSV, Parquet, or remote object
- the rows produced by a generator function
- the rows returned from a paginated HTTP API
- the records inside a NoSQL collection, once you have decided what their schema is
- the events on a stream, once you have decided what a window means

mountainash already supports the first six. The architecture is laid out so the rest are reachable without a rewrite. The relation DAG is a graph of named producers, not a graph of pre-loaded frames. A `DataResource` knows how to load itself when asked, and not before. An executor protocol lets you swap in remote work, queued work, or work that runs inside a database.

The destination is not "mountainash supports streaming." It is **mountainash treats streaming as one of several execution disciplines applied to the same expression tree**, the way Polars treats a streaming query as a different evaluation strategy over the same lazy plan.

## Why this is plausible now

Three things have happened in the last few years that make a project like this feasible:

1. **Substrait stabilised.** A serialisable, vendor-neutral relational algebra exists, with named function keys, parameter conventions, and a growing set of engine implementations. We don't have to invent the wire format.

2. **Polars set a new bar for expression API design in Python.** Polars expressions are composable, inspectable, and lazy in the way pandas chains never were. We model our public API on it because users already know it.

3. **Ibis demonstrated that one frontend over many SQL backends is achievable.** We extend that pattern beyond SQL backends and combine it with native dataframe targets.

mountainash is, in one sentence, **Polars-shaped API on top of a Substrait-aligned AST with Ibis-style backend portability**. None of the three ideas is new. The contribution is the integration, and the discipline to keep the layers separate so each piece can evolve.

## What we are deliberately not building

- **Not a database.** mountainash compiles to databases. It does not store data, schedule queries, or own the execution layer.
- **Not a workflow orchestrator.** Pipelines have step ordering and dependencies because expressions need named producers. We are not competing with Airflow, Prefect, or Dagster.
- **Not a metrics layer.** A metrics layer is one application of composable expressions. We provide the substrate; the metric semantics belong to a higher layer.
- **Not a visualisation tool.** Out of scope.
- **Not a forced abstraction.** If you only use Polars, mountainash should add value through the relation API, conform, and data contracts — but pure Polars code should still be available to you, and dropping into native Polars when you need to should be one method call.

## What success looks like

Concrete five-year markers:

- A working team can write expressions and pipelines in mountainash without knowing which backend the operations team will actually run them on.
- The schema definition for a dataset is also the type specification for its rows, the validation contract for the contract test, the generator for synthetic data, and the input to a `conform()` transformation. Authored once.
- Backend coverage extends to DataFusion, Spark, BigQuery, and Snowflake (via Substrait or Ibis depending on which path matures first).
- The cross-backend divergence catalog shrinks rather than grows as upstream libraries close their gaps.
- The relation DAG handles streaming sources, remote executors, and lazy resource loading as different execution disciplines, not as ad-hoc plumbing.
- The expression IR is stable enough to be a serialisation target — that is, you can store a query plan as a YAML/protobuf document and reload it into a different version of the library.

## What you can use today

The vision above is multi-year. What works in the alpha:

- Polars-shaped expression API across Polars / Narwhals / Ibis
- Relational pipelines (filter, sort, join, group_by, conform, …) cross-backend
- Frictionless DataPackage → RelationDAG round-trip
- Data contracts compiled from TypeSpec / dict / pandera / Pydantic / Frictionless JSON
- Pipeline framework with typed `ParamSpec` parameter binding
- Ternary (TRUE/UNKNOWN/FALSE) logic with automatic booleanization

What is on the near-term roadmap:

- Tightening backend coverage gaps (Narwhals relational ops are the largest remaining)
- Streaming and remote-executor patterns inside the RelationDAG
- Direct Substrait emit/consume (currently the AST is Substrait-aligned but not the wire format)
- DataFusion and direct-SQL targets

And what is further out:

- Streaming semantics as a first-class execution discipline
- Bidirectional translation with Substrait/DMN/FlagD for rule interchange
- A query-plan IR stable enough to publish, store, and version

## Why we are saying this in public while still in alpha

Because the value of mountainash is not in any one feature it has today. It is in the trajectory. We would rather you evaluate the library against where it is going than against where it is. The features that exist now should give you enough to verify the trajectory is real — that the three-layer separation actually works, that the cross-backend tests actually catch regressions, that the alpha you adopt today will not turn into a different library next year.

If that's the kind of bet you make on infrastructure, we'd like to hear from you. The repo is open. The principles are written down. The known divergences are catalogued. Everything is on the table.
