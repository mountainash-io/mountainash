# mountainash examples

These recipes are focused, independently runnable scripts built on one small dataset. Read them in order, or jump to the question you have. Each folder holds a script and a README with the expected output.

mountainash 0.1.0 is experimental and not yet ready for production use. Its APIs can change between versions, and it is not yet published on PyPI.

## Setup

Use Python 3.12 or later. From the repository root:

```bash
uv pip install -e ".[pandas,ibis]"
# or
python -m pip install -e ".[pandas,ibis]"
```

Run each recipe with `python examples/<name>/example.py`. The scripts assert their results, so run them without `-O`. Nothing contacts the network: SQL recipes use in-process DuckDB or SQLite in temporary directories.

## Shared example data

Recipes take these tables, or a subset of them, wherever they need data.

`orders`

| order_id | customer_id | amount | status | ordered_at |
|---|---|---|---|---|
| 1 | 10 | 120.0 | shipped | 2026-01-05 |
| 2 | 11 | 80.0 | pending | 2026-01-09 |
| 3 | 10 | null | shipped | 2026-02-02 |
| 4 | 12 | 200.0 | cancelled | 2026-02-14 |
| 5 | 11 | 50.0 | shipped | 2026-03-01 |
| 6 | 12 | 95.0 | pending | 2026-03-20 |

`customers`

| customer_id | name | region |
|---|---|---|
| 10 | Avery | north |
| 11 | Blake | south |
| 12 | Casey | east |

`targets`

| region | target |
|---|---|
| north | 100.0 |
| south | 150.0 |
| east | 250.0 |

## Start here

| Recipe | Question |
|---|---|
| [First plan](first_plan/) | How do I build a plan and collect the result? |
| [One plan, many backends](one_plan_many_backends/) | How do I run the same plan on Polars, pandas and a SQL engine? |
| [Develop locally, run in production](dev_to_prod/) | How do I test a plan on a small extract and run it on the full table? |
| [Many sources, one plan](many_sources_one_plan/) | How do I combine a database table, a file and plain Python data? |

## Expressions

| Recipe | Question |
|---|---|
| [Expressions](expressions/) | How do I compute, branch, cast and handle nulls in a column expression? |
| [Namespaces](namespaces/) | How do I use string and date methods on a column? |
| [Aggregates and windows](aggregates_and_windows/) | How do I total per group and attach the group total to every row? |
| [Ternary logic](ternary_logic/) | How do I keep rows whose comparison is unknown instead of dropping them silently? |

## Relations and results

| Recipe | Question |
|---|---|
| [Joins and set operations](joins_and_set_operations/) | How do I join two relations, find unmatched rows and stack relations? |
| [Results and egress](results_and_egress/) | How do I get rows out of a relation as dicts, dataclasses or Pydantic models? |
| [Python data in](python_data_in/) | How do I start a relation from Python records? |
| [Explain and snapshots](explain_and_snapshots/) | How do I inspect a plan, compare data across engines and freeze a result? |
| [Execution targets and limits](execution_targets_and_limits/) | How do I choose where a join runs, and what happens when a backend refuses an operation? |

## Schemas and data quality

| Recipe | Question |
|---|---|
| [Table schemas](table_schemas/) | How do I declare a schema, extract one from data and write it as a Frictionless descriptor? |
| [Conform and drift](conform_and_drift/) | How do I conform messy input to a schema and see what changed? |
| [Data contracts](data_contracts/) | How do I declare a contract on a table and read the result for each check? |
| [Validation rules](validation_rules/) | How do I run row, scalar and relation rules and check a foreign key? |

## Multi-table work

| Recipe | Question |
|---|---|
| [DataPackage as a DAG](datapackage_dag/) | How do I load a multi-table package, derive a relation, check its foreign key and export it again? |
| [Pipelines](pipelines/) | How do I run a chain of units with a checkpoint and resume without redoing finished work? |

## Extending

| Recipe | Question |
|---|---|
| [Custom validation rule](custom_validation_rule/) | How do I write a reusable check and run it on more than one backend? |
