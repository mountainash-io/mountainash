---
title: 'mountainash'
description: 'Write tabular data logic once with a Polars-style API and run it on Polars, on the libraries Narwhals reaches and on SQL engines through Ibis, with Frictionless-aligned schemas, conformance and validation on the same plan.'
---

[← Back to Ecosystem](https://docs.mountainash.io/)

# mountainash

**Tabular data logic written once with a Polars-style API, compiled to Polars, to the libraries Narwhals reaches and to SQL engines through Ibis.**

Data logic rarely stays on one engine. A filter and an aggregate get written against Polars for a notebook, then again in pandas for a service that already uses it, then as SQL when the same table moves into DuckDB or PostgreSQL. The cleaning rules and quality checks follow, each copy drifting a little from the others, and no one can say which version is the reference.

mountainash keeps that logic in one place. You describe expressions and relational plans with Polars method names, and the package compiles them for whichever engine holds the data when you ask for a result. Table schemas follow the Frictionless Table Schema shape, and conforming data to a schema, data contracts and validation are built on the same plans, so they run wherever the data does. What each backend and SQL dialect can do is recorded in a capability registry, and a call that a dialect's declarations forbid is refused before it runs.

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

    Combine named relations into a graph, collect it in dependency order, and round-trip it through a Frictionless DataPackage, with foreign keys kept as checks rather than build steps.

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

## See it work

One function describes a plan. It runs on a Polars frame and on a DuckDB table opened through Ibis, without changes:

```python
import ibis
import polars as pl

import mountainash as ma

orders = pl.DataFrame(
    {
        "region": ["north", "south", "north", "south", "east"],
        "amount": [120.0, 80.0, None, 200.0, 50.0],
    }
)


def revenue_by_region(source):
    return (
        ma.relation(source)
        .filter(ma.col("amount") > 60)
        .group_by("region")
        .agg(ma.col("amount").sum().alias("revenue"))
        .sort("region")
    )


con = ibis.duckdb.connect()
duck_orders = con.create_table("orders", orders.to_arrow())

print(revenue_by_region(orders).to_dicts())
print(revenue_by_region(duck_orders).to_dicts())
```

```text
[{'region': 'north', 'revenue': 120.0}, {'region': 'south', 'revenue': 280.0}]
[{'region': 'north', 'revenue': 120.0}, {'region': 'south', 'revenue': 280.0}]
```

The first call ran on Polars and the second ran as SQL inside DuckDB; the plan code was the same and so was the result.

## Where to go next

- Start with [What mountainash does](chapters/01-what-mountainash-does/index.md). It assumes Python 3.12 and dataframe basics (columns, rows, filters, joins, group-by), and introduces lazy plans and three-valued logic where they first appear.
- [Installation and the package surface](chapters/02-installation-and-package-surface/index.md) lists the extras each backend needs.
- The [chapter list](chapters/index.md) shows everything the documentation covers.
- [About](about.md) has the design ideas, authorship, the license and the link to the code repository.

!!! note "Release status"
    mountainash has no supported public PyPI release yet, and its APIs can change between versions. Work from a source checkout as described in [Installation and the package surface](chapters/02-installation-and-package-surface/index.md#base-install-and-extras).
