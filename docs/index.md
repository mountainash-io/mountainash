---
title: 'Mountainash Core'
description: 'A guided manual for the mountainash cross-backend data expression and relational pipeline library'
---


[← Back to Ecosystem](../)
# Mountainash Core

Write data logic once. Run it on Polars, pandas, PyArrow, DuckDB, Snowflake, BigQuery, and every backend that Ibis and Narwhals reach.

Mountainash is a cross-backend expression and relational pipeline library for Python. It gives you a single, fluent API for expressing data transformations — expressions, pipelines, schemas, conformance, data contracts — that compile natively to whichever engine your data lives on. The backend is a deployment decision, not a code decision.

## Why a Guided Manual?

API reference tells you *what* a function does. This manual explains *why* the library is designed the way it is, how the pieces fit together, and how to use them effectively in real projects. Chapters are ordered so each concept builds on what came before, with interactive diagrams throughout to make the architecture tangible.

## What's Inside

- **[Chapters](chapters/index.md)** — 15 chapters covering the full library, from core infrastructure through expression and relation systems to pipelines and DAG orchestration

- **[MicroSims](sims/index.md)** — 35 interactive simulations that visualize key concepts: backend routing, AST construction, pipeline architecture, and more

- **[Learning Graph](learning-graph/index.md)** — A dependency map of every concept in the manual, showing how ideas connect and what to read first


## Who This Is For

Python developers building data pipelines, analytics workflows, or data quality systems who want backend portability without giving up expressiveness. You should be comfortable with Python classes, decorators, and type hints, and familiar with at least one DataFrame library. See [About](about.md) for the full picture.
