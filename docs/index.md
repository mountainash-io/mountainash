---
title: 'Mountainash Core'
description: 'A guided manual for the mountainash cross-backend data expression and relational pipeline library'
---


[← Back to Ecosystem](../)
# Mountainash Core

Write data logic once. Run it on Polars, pandas, PyArrow, DuckDB, Snowflake, BigQuery, and every backend that Ibis and Narwhals reach.

Mountainash is a cross-backend expression and relational pipeline library for Python. It gives you a single, fluent API for expressing data transformations — expressions, pipelines, schemas, conformance, data contracts — that compile natively to whichever engine your data lives on. The backend is a deployment decision, not a code decision.


## What's Inside

API reference tells you *what* a function does. This manual explains *why* the library is designed the way it is, how the pieces fit together, and how to use them effectively in real projects. Chapters are ordered so each concept builds on what came before, with interactive diagrams throughout to make the architecture tangible.

- **[Chapters](chapters/index.md)** — 15 chapters covering the full library, from core infrastructure through expression and relation systems to pipelines and DAG orchestration


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

## Prerequisites

- Intermediate Python programming (classes, decorators, type hints, protocols)
- Familiarity with at least one DataFrame library (Polars, pandas, or similar)
- Basic understanding of SQL concepts (SELECT, JOIN, GROUP BY, WHERE)
- Understanding of directed acyclic graphs (DAGs) and topological ordering

## What This Manual Covers

1. **Core Infrastructure** — Backend detection, type guards, enums, factory patterns, lazy imports
2. **Expression System** — Fluent expression API, AST nodes, function key registry, visitor pattern compilation
3. **Expression Backends** — Polars, Narwhals, and Ibis expression compilation with cross-backend consistency
4. **Relation System** — Relational AST with Substrait-aligned node types, fluent relation builder, unified visitor
5. **Relation Backends** — Polars LazyFrame, Narwhals, and Ibis SQL relation compilation
6. **Type System (TypeSpec)** — Universal type metadata, Frictionless Table Schema alignment, schema extraction and validation
7. **Data Conformance** — TypeSpec-driven column transformation via `Relation.conform()`
8. **Ternary Logic** — Three-valued semantics (TRUE/FALSE/UNKNOWN) with sentinel integers and auto-booleanisation
9. **DAG & DataPackage** — RelationDAG orchestrator, Frictionless DataPackage integration, two-edge graph model
10. **Pipeline Framework** — Declarative multi-step pipelines with typed parameter binding and caching

## What This Manual Does Not Cover

- Low-level Polars/Ibis/Narwhals internals (upstream library implementation details)
- Database administration or SQL optimisation
- Machine learning model training or serving
- Web framework integration
- Deployment and infrastructure concerns

## Key Capabilities

**Expressions that compile everywhere** — Write `col()`, `lit()`, `when()` using Polars-compatible syntax that compiles natively to Polars for performance, through Narwhals for any compatible DataFrame library, and through Ibis for any SQL or analytical engine.

**Pipelines that get data out your way** — The relation builder wraps expressions in a fluent pipeline API. Terminal methods deliver results as Polars DataFrames, pandas, dicts, dataclasses, Pydantic models, PyArrow tables, and more. Cross-type joins work transparently across different sources.

**Schemas that conform messy data** — TypeSpec defines what your data should look like, aligned with the Frictionless Data standard. The conform pipeline handles missing value normalisation, boolean casting, numeric parsing, temporal parsing, category enforcement, and list delimiters.

**Data quality woven into the pipeline** — Data contracts validate both physical structure and logical business rules. Both compile to the same expression engine and run on any backend. Context-aware rule exclusions let you vary strictness by environment.

**Three-valued logic for real-world data** — The ternary expression layer (TRUE, FALSE, UNKNOWN) handles sentinel values, unreported fields, and the gap between "zero" and "missing" — essential for databases that recommend sentinel values over NULLs.

**Frictionless Data as a first-class citizen** — TypeSpec aligns with Frictionless Table Schema. DataPackages and Resources work natively. Multi-resource DAGs validate foreign key integrity across tables.

## Context

Mountainash positions itself as a backend-portable abstraction layer for data expressions and relational operations. Unlike Ibis (SQL-focused) or Narwhals (DataFrame-agnostic thin layer), mountainash provides a full Substrait-aligned AST with three-valued ternary logic, schema-first data quality via TypeSpec, and declarative pipeline orchestration — enabling "abstract data products" that run identically across Polars, pandas, and SQL backends.
