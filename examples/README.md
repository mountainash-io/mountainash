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

## Expressions

| Recipe | Question |
|---|---|

## Relations and results

| Recipe | Question |
|---|---|

## Schemas and data quality

| Recipe | Question |
|---|---|

## Multi-table work

| Recipe | Question |
|---|---|

## Extending

| Recipe | Question |
|---|---|
