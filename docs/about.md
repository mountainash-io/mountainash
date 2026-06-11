# About

## Who This Is For

This manual is written for Python developers who work with data: data engineers building pipelines, analysts exploring datasets, and data scientists preparing features for models. The common thread is that you use DataFrames and want your logic to be portable across backends.

Specifically, you'll get the most out of this if you're:

- Building data pipelines that need to run on more than one engine (e.g., Polars locally, SQL in production)
- Standardising data quality across teams using schemas and contracts
- Conforming messy, real-world data to clean, typed outputs
- Looking for a single API that handles expressions, relational operations, and pipeline orchestration together

## What You Should Already Know

- **Python** — Classes, decorators, type hints, and protocols. You don't need to be an expert, but you should be comfortable reading and writing typed Python.
- **DataFrames** — Practical experience with at least one DataFrame library (Polars, pandas, or similar). You should know what a filter, join, and group-by look like.
- **SQL basics** — SELECT, JOIN, GROUP BY, WHERE. You don't need to be a DBA, but the relational concepts should be familiar.
- **DAGs** — A working understanding of directed acyclic graphs and topological ordering. If you've used Airflow, dbt, or any task scheduler, you've seen these.

## What You'll Get Out of This

After working through this manual, you'll be able to:

- Build fluent expression chains that compile to Polars, pandas, PyArrow, or SQL without rewriting
- Construct relational pipelines with filters, joins, aggregations, window functions, and a dozen terminal output formats
- Define portable schemas with TypeSpec and use `conform()` to clean messy data in a single call
- Set up data contracts that validate structure and business rules across environments
- Orchestrate multi-step workflows with the pipeline framework and RelationDAG
- Understand the architecture well enough to extend the library with new operations, backends, or node types

## How to Navigate

- **Read chapters in order** — concepts are introduced in dependency order, so each chapter builds on what came before.
- **Use the search bar** (top right) to jump to a specific term or concept.
- **Try the MicroSims** as you encounter them — they're the fastest way to build intuition for how the architecture works.
- **Check the [Learning Graph](learning-graph/index.md)** when you want to see how a concept fits into the larger picture.
- **Use the [API Reference](api/index.md)** as a companion while reading — it has the module-level detail that chapters summarise.

## About Mountainash

Mountainash is an open-source Python library that provides a backend-portable abstraction layer for data expressions and relational operations. Unlike Ibis (SQL-focused) or Narwhals (a thin DataFrame compatibility layer), mountainash provides a full Substrait-aligned AST with three-valued ternary logic, schema-first data quality via TypeSpec, and declarative pipeline orchestration.

The result is that you can define "abstract data products" — expressions, pipelines, schemas, contracts — that run identically across Polars, pandas, and SQL backends.

- **Source code**: [github.com/mountainash-io/mountainash](https://github.com/mountainash-io/mountainash)
- **Author**: Nathaniel Ramm
