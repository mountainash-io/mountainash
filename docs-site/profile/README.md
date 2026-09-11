# mountainash

**Write data logic once, run it on every backend.**

## Vision

Mountainash is the foundation of a composable data engineering ecosystem. At its core is an expression and relation engine that compiles to Polars, pandas, DuckDB, Snowflake, BigQuery, and every backend that Ibis and Narwhals reach. Everything built on these expressions -- rules, validation, conformance, pipelines -- inherits that portability automatically.

Write `col`, `lit`, `when` using Polars-compatible syntax that compiles natively to Polars for performance, through Narwhals for any compatible DataFrame library, and through Ibis for any SQL or analytical engine. The same expression runs in a notebook and in production. The backend is a deployment decision, not a code decision. When results are ready, choose how to get them out -- Polars DataFrames, pandas, dicts, dataclasses, Pydantic models, PyArrow, Narwhals, Ibis tables, and more. Cross-type joins work transparently: combine data from different sources without converting first.

Real data has unknowns -- not just nulls, but sentinel values, unreported fields, and the gap between "zero" and "missing." The ternary expression layer (TRUE, FALSE, UNKNOWN) handles all of this honestly, so every comparison, aggregation, and rule evaluation gives you correct results even when the data is incomplete. TypeSpec schemas define what your data should look like, aligned with the Frictionless Data standard. The conform pipeline handles the messy realities -- sentinel values, multi-format dates, string-encoded booleans, missing value conventions that differ by source. Data arrives messy. It leaves typed, validated, and conformant.

## Installation

```bash
pip install mountainash
```

## Use Cases

### The Portable Analytics Team

A data team writes analysis logic against DuckDB during development. The same expressions deploy to Snowflake in staging and BigQuery in production -- no rewrite, no translation layer. When the organisation adopts a new backend, the logic moves with a config change.

### The Data Quality Programme

TypeSpec schemas define the physical contract for every dataset. Data contracts add business rules as expressions. The same contracts validate local test data during development and production tables in Snowflake. Violation results accumulate into governance dashboards that track trends over time.

### The Data Scientist Handover

A data scientist builds feature engineering in Polars on their laptop. An ML engineer deploys to Snowflake. No rewrite -- the expressions compile through Ibis to whatever backend production requires. Six months later, model updates flow from notebook to production without a translation cycle.

### The Conformed Logic Library

A central team publishes business definitions -- revenue calculations, segment definitions, churn measures -- as a versioned library of named expressions. Analysts import the library and get expressions that compile to whatever backend they're connected to. The SQL views become materialisation targets, not the source of truth.

## Key Capabilities

### Expression API

The starting point for every data transformation. Use `col()`, `lit()`, and `when()` to compose readable, composable expressions that compile to whichever backend your data already lives on. Namespace operations (`.str`, `.dt`, `.name`, `.struct`, `.list`) give you domain-specific fluency, while helpers like `coalesce()`, `greatest()`, and `today()` handle common patterns cleanly. Three-valued logic via `t_col` and `always_true` ensures missing data is handled honestly throughout your pipeline. You can clean a vendor CSV -- parsing dates, trimming whitespace, coalescing fallback columns -- in a single expression chain that works identically whether you're prototyping in pandas or running at scale in Polars.

### Relation API

A fluent pipeline builder that feels like writing Polars but runs on any supported backend. Chain filters, joins, aggregations, and window functions, then land the results wherever you need them. The relation API supports a rich set of terminal methods -- `.to_polars()`, `.to_dicts()`, `.to_dataclasses()`, `.to_pydantic()`, `.to_arrow()` -- so you choose the output format that fits your application. Cross-type joins let you combine a Polars frame with a pandas frame in a single operation, transparently.

### TypeSpec and Data Conformance

TypeSpec defines your data's shape as a portable, Frictionless-aligned schema that works as a contract between teams, systems, and stages of your pipeline. Extract schemas automatically from DataFrames, dataclasses, or Pydantic models, or define them declaratively. The conform pipeline transforms messy, real-world data into clean, schema-aligned output in a single call: `ma.relation(df).conform(spec).to_polars()`. It handles missing value normalisation, boolean casting, numeric parsing, temporal parsing, category enforcement, and list delimiters. `fieldsMatch` modes (exact, equal, subset, superset, partial, open) let you control how strict the schema alignment should be.

### Data Contracts

Define and enforce data quality expectations as composable contracts. Compile contracts from TypeSpec schemas, add custom validation rules via the RuleRegistry, and orchestrate validation across your pipeline. Context-aware rule exclusions let you vary strictness by environment -- tighter in production, relaxed during development. Data contracts validate both physical structure and logical business rules, and both compile to the same expression engine.

### Pipeline Framework

Build multi-step data workflows as declarative pipelines with automatic dependency resolution and DAG ordering. Typed parameters make pipelines self-documenting and safe to compose. Caching and storage integrations let you checkpoint intermediate results, and the `source()` integration connects pipelines directly to the Relation API for end-to-end fluency.

### DataPackage and DAG

Work with multi-resource datasets using the Frictionless DataPackage standard. RelationDAG orchestrates workflows across multiple related tables, with foreign key integrity checks ensuring your relationships stay consistent. Load a DataPackage descriptor and get a validated, queryable graph of your entire dataset.

## Architecture

Mountainash compiles a single expression and relation AST into native operations across Polars, Narwhals (pandas, PyArrow, cuDF), and Ibis (SQL backends). A layered protocol system defines the contract every backend must fulfill -- expression protocols specify the full surface area of supported operations, while relation protocols define the pipeline operations and terminal methods. This separation means adding a new backend is a matter of fulfilling existing contracts, and adding a new operation means extending a protocol that all backends implement.

Each backend is assembled from focused mixins via multiple inheritance, one mixin per operation category. Backend registration decorators wire implementations into a type-safe dispatch system built on function key enums. A known divergences registry tracks where backends genuinely differ, and upstream fix monitoring flags when a backend library update might resolve a tracked limitation. The result is a consistency contract: the same expression produces the same result regardless of backend, within documented boundaries.

## Extending

Mountainash is built to be extended without modifying core code. You can add new operations by defining a function key and implementing backend mixins. Register entirely new backends using system decorators. The RelationVisitRegistry accepts custom relation node types that participate in the full compilation pipeline. The CustomTypeRegistry lets you register new data types with dual-mode converters for TypeSpec, conform, and validation. The pipeline framework exposes extension points for custom execution backends, storage mechanisms, and AST rewriting passes.

## Contributing

Mountainash is designed to make contributions predictable. Consistent file naming conventions (prefixes like `exn_`, `prtcl_`, `api_bldr_`, `pl_`, `ib_`, `nw_`) let you navigate to the right file by prefix alone. Adding a new expression operation follows a well-defined process: define the function key, add the protocol method, implement the API builder, add backend mixins, wire the function mapping, and write cross-backend tests. Tests are parametrised across all backends, and known quirks use `xfail` markers (never skip), so every assertion runs everywhere and regressions are caught even for known limitations.

## Maintaining

The three-layer architecture -- protocols, API surface, and backend implementations -- keeps changes contained and predictable. When a bug report arrives, the layers tell you exactly where to look: check the protocol for ambiguity, the API builder for wiring issues, and the backend mixin for translation errors. A natural review checklist emerges from this structure.

The conform system defers transformation to compile time via ConformRelNode, so conformance operations execute as backend-native expressions with full optimisation opportunities. Terminal methods delegate to the pydata.egress module, which implements a three-tier hybrid conversion strategy balancing native vectorised extraction with structured and custom fallbacks.

Cross-backend testing parametrises every assertion across all supported backends. The KNOWN_EXPR_LIMITATIONS registry documents intentional divergences, and upstream fix monitoring flags when a new library release might resolve a tracked limitation. When a new Polars or Ibis release ships, maintainers check the registry and update accordingly.
