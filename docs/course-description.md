---
title: Package Overview
description: What mountainash covers, who it's for, and how this manual is structured
---

# Package Overview

Mountainash is a cross-backend data expression and relational pipeline library for Python. It lets you write data transformation logic once and run it on Polars, pandas (via Narwhals), and SQL databases (via Ibis) without rewriting.

## Target Audience

Python developers building data pipelines, analytics workflows, and data quality systems who need backend-portable expressions and relational operations across Polars, pandas, PyArrow, and SQL backends.

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
