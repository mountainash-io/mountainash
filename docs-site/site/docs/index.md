---
title: 'mountainash'
description: 'Write tabular data logic once with a Polars-style API and run it on local files, dataframes and databases: develop on Polars against a local extract and run the same plan in a SQL engine, or mix sources in one plan, with schemas, conformance and validation on the same plans.'
---

[← Back to Ecosystem](https://docs.mountainash.io/)

# mountainash

**One Polars-style plan for every place your data lives: local files, dataframes and databases.**

!!! warning "Experimental"
    mountainash 0.1.0 is experimental and not yet ready for production use. Its APIs can change between versions, and it is not yet published on PyPI.

Most data work spans several sources and engines. A model starts in a notebook on a Parquet extract, joins a reference CSV that someone keeps by hand, and ends up running against a database table. Each step usually means rewriting the same filters, joins and aggregates in another API, and the copies drift apart.

mountainash lets you write that logic once. You build expressions and relational plans with Polars method names, and the package compiles each plan for the engine that holds the data: native Polars, the libraries Narwhals reaches (pandas, PyArrow and others) or SQL engines through Ibis. Schemas, conformance, data contracts and validation run on the same plans, so the rules travel with the logic.

## Develop locally, run in production

Build a model against a small local extract on Polars, then point the same function at the full table in the database. The plan code stays the same; only the source changes:

```python
import ibis
import polars as pl

import mountainash as ma

def customer_revenue(orders):
    return (
        ma.relation(orders)
        .filter(ma.col("amount").is_not_null())
        .group_by("customer_id")
        .agg(ma.col("amount").sum().alias("revenue"))
        .sort("customer_id")
    )

# Development: a local Parquet extract, run on Polars.
dev_orders = pl.read_parquet("orders_extract.parquet")
print(customer_revenue(dev_orders).to_dicts())

# Production: the full table in the database, run as SQL.
warehouse = ibis.duckdb.connect("warehouse.duckdb")
prod_orders = warehouse.table("orders")
print(customer_revenue(prod_orders).to_dicts())
```

```text
[{'customer_id': 10, 'revenue': 120.0}, {'customer_id': 11, 'revenue': 80.0}, {'customer_id': 12, 'revenue': 200.0}]
[{'customer_id': 10, 'revenue': 120.0}, {'customer_id': 11, 'revenue': 130.0}, {'customer_id': 12, 'revenue': 295.0}]
```

The first call ran on Polars over the four orders in the extract. The second compiled the same plan to SQL and ran it inside DuckDB over all six orders. Promoting the model from development to production is a change of input, and the logic you tested is the logic that runs.

Among SQL engines, DuckDB and SQLite run mountainash's full cross-backend test suite, as do native Polars and, through Narwhals, pandas, Polars and lazy frames. PostgreSQL, MySQL, Exasol and SingleStoreDB have capability declarations of their own. [Backend support and known limits](chapters/16-backend-support-and-limits/index.md) lists the support level and known differences for each dialect.

## Mix sources in one plan

A plan can combine a database table, a local file and plain Python data. Here orders live in a DuckDB database, the customer list comes from a CSV file, and the revenue targets are a list of dicts:

```python
import ibis
import polars as pl

import mountainash as ma

orders = ibis.duckdb.connect("warehouse.duckdb").table("orders")  # database table
customers = pl.read_csv("customers.csv")                          # local file
targets = [                                                       # plain Python data
    {"region": "north", "target": 100.0},
    {"region": "south", "target": 150.0},
    {"region": "east", "target": 250.0},
]

report = (
    ma.relation(orders)
    .join(customers, on="customer_id")
    .group_by("region")
    .agg(ma.col("amount").sum().alias("revenue"))
    .join(targets, on="region")
    .with_columns((ma.col("revenue") >= ma.col("target")).alias("on_target"))
    .sort("region")
)
print(report.to_polars())
```

```text
shape: (3, 4)
┌────────┬─────────┬────────┬───────────┐
│ region ┆ revenue ┆ target ┆ on_target │
│ ---    ┆ ---     ┆ ---    ┆ ---       │
│ str    ┆ f64     ┆ f64    ┆ bool      │
╞════════╪═════════╪════════╪═══════════╡
│ east   ┆ 295.0   ┆ 250.0  ┆ true      │
│ north  ┆ 120.0   ┆ 100.0  ┆ true      │
│ south  ┆ 130.0   ┆ 150.0  ┆ false     │
└────────┴─────────┴────────┴───────────┘
```

A join runs where its left side lives, so the whole plan ran inside DuckDB. mountainash moved the CSV frame and the targets into the DuckDB connection through Arrow before running it, and `report.explain()` lists both moves as `transfer` lines. `execute_on=` chooses the other side when you want the work done locally. [Joins](chapters/07-relations/index.md#joins) and [Operand transfer and owned copies](chapters/09-execution-targets-and-capabilities/index.md#operand-transfer-and-owned-copies) describe the rules.

## Rules that travel with the data

Table schemas follow the Frictionless Table Schema shape, and a DataPackage reads and writes Frictionless descriptors. `conform()` turns raw input into the typed columns a schema declares, and its drift report shows where the source differed. Data contracts and validation rules compile to the same plans as everything else, so a quality check written against the local extract runs unchanged in the database.

A capability registry records what each backend and SQL dialect can do. When a dialect's declarations forbid a call, mountainash stops it before it runs and names the backend in the error, so a difference between development and production shows up as a clear refusal.

## Who it's for

<div class="grid cards" markdown>

-   **Data engineers and analysts**

    ---

    Write filters, joins, group-bys and window expressions once and run them on a Polars frame, a pandas frame or a database table. Join a Polars frame to a pandas frame or a Python dict in one plan, and get rows back as dicts, dataclasses or Pydantic models.

    [What mountainash does](chapters/01-what-mountainash-does/index.md)

-   **Teams that own data quality**

    ---

    Declare a table schema once, then use it to convert messy input into typed columns, report how the data drifted, and check values with data contracts and validation rules on any supported backend.

    [Conforming data to a schema](chapters/11-conforming-data/index.md)

-   **Teams building multi-table data products**

    ---

    Combine named relations into a graph, collect it in dependency order, and round-trip it through a Frictionless DataPackage, with foreign keys kept as checks, separate from build order.

    [RelationDAG](chapters/14-relationdag/index.md)

-   **People evaluating backend reach**

    ---

    See which backend families and SQL dialects are declared, which ones run the cross-backend test suite, and the known differences between them, generated from the package's own capability registry.

    [Backend support and known limits](chapters/16-backend-support-and-limits/index.md)

-   **Contributors and extension authors**

    ---

    Add operations, relation nodes, capability declarations, type adapters, ingress handlers, pipeline units and validation rules through the same layers the built-in features use.

    [Architecture](chapters/17-architecture/index.md)

</div>

## Where to go next

- Start with [What mountainash does](chapters/01-what-mountainash-does/index.md). It assumes Python 3.12 and dataframe basics (columns, rows, filters, joins, group-by), and introduces lazy plans and three-valued logic where they first appear.
- [Installation and the package surface](chapters/02-installation-and-package-surface/index.md) lists the extras each backend needs.
- The [chapter list](chapters/index.md) shows everything the documentation covers.
- The [examples folder](https://github.com/mountainash-io/mountainash/tree/develop/examples) holds runnable recipes with their expected output.
- [About](about.md) has the design ideas, authorship, the license and the link to the code repository.
