---
title: 'About'
description: 'Why mountainash exists, the design ideas behind it, where it fits, and who maintains it'
---

[← Back to Home](index.md)

# About mountainash

**Polars, Narwhals and Ibis execute your data logic. mountainash decides how that logic is described, checked and carried between them.**

## Why it exists

Polars, Narwhals and Ibis each solve part of the portability problem. Polars gives a clear expression API and a fast engine. Narwhals puts a Polars-like API over pandas, PyArrow, Dask, DuckDB and others. Ibis compiles a dataframe API to SQL for many databases. A team that stays on one of them is well served.

Problems start when the same logic has to live in several places. A transformation is prototyped on a Polars frame, then has to run against a pandas frame in an existing service and against a database table in production. Each engine gets its own rewrite, schemas, type conversions and quality checks included, and the copies drift. A gap in a backend surfaces late, as an engine error or a quietly different result.

mountainash answers this with one idea: hold the logic as a backend-agnostic plan and compile it at the moment you request a result. Expressions, relations, schemas, conformance, data contracts and validation all build on that plan, so they move together to whatever engine holds the data.

## What it adds to Polars, Narwhals and Ibis

Those libraries supply the engines and their native APIs. mountainash adds a shared layer over them.

| Area | What you get |
|---|---|
| Portable logic | Expressions and relations with Polars method names that compile to Polars, to Narwhals-reached libraries and to Ibis SQL engines, with the data you pass in choosing the engine |
| Mixed sources | Joins across a Polars frame, a pandas frame, an Arrow table or a Python dict in one plan, with the data moved to one execution location |
| Schemas | `TableSchema` declarations aligned with Frictionless Table Schema, read and written as descriptors, and extracted from dataframes, dataclasses and Pydantic models |
| Conformance | `relation.conform(schema)` converts columns to the declared types and names under a contract, and can report how the input drifted |
| Data quality | Data contracts and a validation engine whose checks compile through the same plans, with row-level failure cases and foreign-key checks |
| Multi-table work | `RelationDAG` for graphs of named relations, round-tripped through a Frictionless `DataPackage`, and pipelines with checkpoints and resume |
| Python data in and out | Relations from dicts, rows, dataclasses and Pydantic models, and results back as dicts, tuples, dataclasses or Pydantic models |

## Design ideas

Build, then compile. Writing `ma.col("age") > 30` or `ma.relation(df).filter(...)` builds a tree of nodes and leaves the data untouched. Compilation detects the backend from the data's type, so an expression defined in a shared module applies to frames from different libraries. See [Lazy plans and the AST](chapters/01-what-mountainash-does/index.md#lazy-plans-and-the-ast).

Polars on the surface, Substrait underneath. Method and parameter names follow Polars, so a Polars user can read the code. The internal tree follows the [Substrait](https://substrait.io/) model of relations and functions, and operations Substrait does not define, such as ternary logic, sit in a separate mountainash namespace. Backends compile from that tree alone. Substrait plan import and export are not available.

The same logic gives the same result, and known differences are named. One expression or relation is designed to produce the same logical result on every backend that supports it, and the cross-backend test suite checks this. Where a backend differs, the package records the difference openly as a known divergence. See [Backend support and known limits](chapters/16-backend-support-and-limits/index.md).

A limit belongs to the call. Capability records cover an operation together with its parameters and option values on a specific dialect. A dialect can run an operation in general and still refuse one parameter or option value. On DuckDB through Ibis, `sample(n=5)` runs, while `sample(n=5, seed=7)` raises `BackendCapabilityError` before it runs, because a seeded exact-count sample is declared unsupported there. `capability_policy` adjusts that protection. See [Capability errors and capability_policy](chapters/09-execution-targets-and-capabilities/index.md#capability-errors-and-capability_policy).

Unknown is a value. Ternary expressions return TRUE (1), UNKNOWN (0) or FALSE (-1), with AND as the minimum and OR as the maximum. A missing value stays visible as UNKNOWN, and you choose at the point of use whether UNKNOWN rows pass a filter. See [Ternary logic and unknown values](chapters/06-ternary-logic/index.md).

Dependencies drive execution; foreign keys describe data. A `RelationDAG` keeps the edges that come from one relation referring to another apart from the edges that come from declared foreign keys. The reference edges alone decide what is collected and in which order. Validation checks the foreign keys, and execution follows the reference edges only. See [RelationDAG](chapters/14-relationdag/index.md).

## Where it fits

mountainash is the core package of the mountainash project. It owns the semantic layer: expressions, relations, schemas, conformance, data contracts, validation and multi-table orchestration. Execution belongs to the engines it compiles to: Polars directly, pandas, PyArrow, Dask and DuckDB through Narwhals, and DuckDB, SQLite, PostgreSQL, MySQL, Polars, SingleStoreDB and Exasol through Ibis, each at the support level the capability registry records.

Sibling packages own the byte-level work. `mountainash-transport` reads resources from remote locations, `mountainash-files` parses file-backed resources such as CSV and Parquet, and `mountainash-data` handles transactions and owned table copies on SQL backends. [Where mountainash sits](chapters/02-installation-and-package-surface/index.md#where-mountainash-sits) shows which extra brings in each one.

## Who maintains it

mountainash is written and maintained by Nathaniel Ramm. The source, tests and this documentation live in the public repository [mountainash-io/mountainash](https://github.com/mountainash-io/mountainash); work happens on the `develop` branch and `main` is the release line.

Every code example in this documentation runs against the package source, and each output block is copied from that run. The repository README carries further short examples, and the test suite under `tests/` exercises each feature across backends.

To correct a page, use the edit icon at its top, which opens the page's source file on GitHub, and propose the change as a pull request following the repository's [contributing guide](https://github.com/mountainash-io/mountainash/blob/main/CONTRIBUTING.md). For anything else, see [Contact](contact.md).

## License

mountainash is Copyright 2024-2026 Mountain Ash Solutions Pty. Ltd. Its first-party code is licensed under the Apache License, Version 2.0. The bundled GeoJSON schema (`src/mountainash/validation/schemas/GeoJSON.json`) is Copyright (c) 2018 Tim Schaub and is licensed under the MIT License, with its original licence and attribution retained. The distribution's SPDX licence expression is `Apache-2.0 AND MIT`, and its MIT part covers the GeoJSON schema alone. See [License](license.md) for the files that state these terms.
