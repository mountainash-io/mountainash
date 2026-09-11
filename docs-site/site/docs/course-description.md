---
title: 'Package Overview'
description: 'Audience, prerequisites, learning outcomes, and chapter syllabus for the Mountainash Core manual'
---

# Package Overview

This page gives a course-style summary of the Mountainash Core manual: who it's designed for, what you should know going in, what you'll be able to do by the end, and how the material is sequenced. For the full narrative introduction and library motivation, see [Home](index.md); for the chapter-by-chapter table of contents, see [Chapters](chapters/index.md).

## Audience

Mountainash Core is written for **Python developers who work with data**: data engineers building pipelines, analysts exploring datasets, and data scientists preparing features for models. The unifying trait across all three is working with DataFrames and wanting that logic to be portable across backends rather than locked to one engine.

You'll get the most from this manual if you are:

- Building data pipelines that need to run on more than one engine (e.g. Polars locally, SQL in production)
- Standardising data quality across teams using schemas and contracts
- Conforming messy, real-world data to clean, typed outputs
- Looking for a single API that unifies expressions, relational operations, and pipeline orchestration

## Prerequisites

- **Python** — classes, decorators, type hints, and protocols. Comfort reading and writing typed Python, not expert-level mastery.
- **DataFrames** — practical experience with at least one DataFrame library (Polars, pandas, or similar), and familiarity with what a filter, join, and group-by look like.
- **SQL basics** — SELECT, JOIN, GROUP BY, WHERE. Relational concepts should be familiar even if you're not a DBA.
- **DAGs** — a working understanding of directed acyclic graphs and topological ordering. Anyone who has used Airflow, dbt, or a task scheduler has already seen the shape of this.

No prior exposure to mountainash, Ibis, or Narwhals is assumed — the manual introduces each as it goes.

## Learning Outcomes

By working through this manual, you will be able to:

- Build fluent expression chains that compile to Polars, pandas, PyArrow, or SQL without rewriting them per backend
- Construct relational pipelines with filters, joins, aggregations, window functions, and a dozen terminal output formats
- Define portable schemas with TypeSpec and use `conform()` to clean messy data in a single call
- Set up data contracts that validate both structure and business rules across environments
- Orchestrate multi-step workflows with the pipeline framework and RelationDAG
- Reason about the architecture well enough to extend the library with new operations, backends, or node types

## Syllabus

The manual is organized into **15 chapters covering 200 concepts**, sequenced so each chapter builds on concepts introduced earlier. The full table with per-chapter concept counts lives on the [Chapters](chapters/index.md) page; the arc is:

1. **Foundations** (Ch. 1–2) — foundation concepts, then core infrastructure: backend detection, type guards, enums, factory patterns, lazy imports
2. **The expression system** (Ch. 3–8) — the fluent expression API, AST nodes, the function key registry, the visitor pattern, and how expressions compile through Polars, Narwhals, and Ibis with cross-backend consistency
3. **Type system** (Ch. 9) — TypeSpec's universal type metadata and its alignment with the Frictionless Table Schema standard
4. **The relation system** (Ch. 10, 11, 14) — core and advanced relational API operations, the Substrait-aligned relational AST, and the unified visitor that drives compilation
5. **Pipelines and orchestration** (Ch. 12–13) — the declarative pipeline framework with typed parameter binding and caching, plus RelationDAG and DataPackage integration
6. **Relation backends** (Ch. 15) — how the relational AST compiles to Polars LazyFrame, Narwhals, and Ibis SQL

Woven throughout — rather than isolated in a single chapter — are two cross-cutting topics: **ternary logic** (three-valued TRUE/FALSE/UNKNOWN semantics for real-world data with sentinel values) and **data conformance** (TypeSpec-driven column transformation), both of which appear wherever they're relevant to the chapter at hand.

## What This Manual Does Not Cover

- Low-level Polars/Ibis/Narwhals internals (implementation details of the upstream libraries themselves)
- Database administration or SQL query optimisation
- Machine learning model training or serving
- Web framework integration
- Deployment and infrastructure concerns

## Where to Go Next

Start at [Home](index.md) for the full introduction, or jump straight into [Chapter 1: Foundation Concepts](chapters/01-foundations/index.md) if you're ready to begin. The [Learning Graph](learning-graph/index.md) shows how the 200 concepts depend on one another if you want to see the reasoning behind the chapter ordering.
