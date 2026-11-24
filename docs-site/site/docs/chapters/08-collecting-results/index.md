---
title: Collecting results
---

# Collecting results

A terminal is the call that ends a relation plan. It compiles the plan for the backend that owns the data, runs it, and returns the result in the form requested: the engine's own frame, a frame from another library, Python objects, or a single value. Most code ends with `.to_polars()`, `.to_dicts()`, `.collect()` or a scalar terminal such as `.count_rows()`.

Assumes: [Relations](../07-relations/index.md) and [Aggregates](../05-namespaces-aggregates-and-windows/index.md#aggregates).

## Collect and terminals

<!-- concept:376 -->

Building a relation records a plan (see [Build then compile](../01-what-mountainash-does/index.md#lazy-plans-and-the-ast)). A terminal call executes that plan, and each terminal call runs it again. The terminals fall into these groups:

| Group | Terminals | Returns |
|---|---|---|
| Native | `collect()`, `compile()` | the engine's own result or plan |
| Frames | `to_polars()`, `to_pandas()`, `to_pyarrow()`, `to_narwhals()`, `to_ibis()` | a frame of the named library |
| Python data | `to_dict()`, `to_dicts()`, `to_tuples()`, `to_named_tuples()`, `to_typed_named_tuples()`, `to_dataclasses()`, `to_pydantic()`, `to_dict_of_series_polars()`, `to_dict_of_series_pandas()`, `to_index_of_dicts()`, `to_index_of_tuples()`, `to_index_of_named_tuples()`, `to_index_of_typed_named_tuples()` | Python collections |
| Scalars | `item()`, `count_rows()`, `sum()`, `avg()`, `mean()`, `min()`, `max()`, `product()`, `std_dev()`, `variance()`, `any_value()` | one Python value |
| Inspection | `explain()`, `fingerprint()`, `describe()` | a plan description, a fingerprint table, summary statistics |
| Ownership | `snapshot()` | a relation over an independent copy of the result |

`collect_with_drift()` returns the result together with conformance drift reports; [Drift reporting](../11-conforming-data/index.md#drift-reporting) covers it.

`collect(*, unwrap=True, target=None)` returns the result in the engine's native form. For a Polars source that is a Polars `DataFrame`, for a pandas or PyArrow source it is the pandas frame or Arrow table, and for an Ibis source it is an Ibis table expression that still lives on its connection. Each frame terminal converts to its named library, wherever the plan ran:

```python
import ibis
import polars as pl

import mountainash as ma

orders = pl.DataFrame({
    "order_id": [1, 2, 3],
    "customer_id": [10, 20, 10],
    "amount": [25.0, 40.0, 15.5],
})
con = ibis.duckdb.connect()
orders_db = con.create_table("orders", orders.to_arrow())

large = ma.relation(orders_db).filter(ma.col("amount") > 20)
print(type(large.collect()).__name__)
print(type(large.to_polars()).__name__, large.to_polars().height)
print(type(ma.relation(orders).filter(ma.col("amount") > 20).compile()).__name__)
```

```text
Table
DataFrame 2
LazyFrame
```

On DuckDB, `collect()` returns an Ibis `Table`: a deferred query bound to the connection, with the rows still in the database. That is the native form of an Ibis result, and further Ibis code or `ma.relation` accepts it as input. `to_polars()` executes the query and moves the rows into Polars. `compile()` returns the native plan and leaves it unexecuted; for a Polars source that is a `LazyFrame`. When a plan must move data between engines before it compiles, `compile()` raises `CompileRequiresExecutionError`, and that plan needs a materialising terminal.

`collect` and `collect_with_drift` take a `target` argument that runs the plan on a different family, dialect or connection, and `unwrap=False` keeps a Narwhals result wrapped. [Execution targets and locations](../09-execution-targets-and-capabilities/index.md#execution-targets-and-locations) describes targets.

<!-- concept:382 -->

Some conformed columns take their final values in a resolution step outside the engine. When [conform](../11-conforming-data/index.md#relation-conform) parses JSON text into an `array` or `object` field, that final step resolves the parsed values. A native terminal (`collect()` or `collect_with_drift()`) would return the unresolved representation, so it raises `LogicalTerminalRequired` before executing anything. A logical terminal builds its output through the resolution step and returns the parsed values:

```python
from mountainash.exceptions import LogicalTerminalRequired

events = pl.DataFrame({"id": [1, 2], "payload": ["[1,2]", "[3]"]})
spec = ma.table_schema({"id": "integer", "payload": "array"})
parsed = ma.relation(events).conform(spec, contract={"data_type": "coerce"})
try:
    parsed.collect()
except LogicalTerminalRequired as exc:
    print(exc)
    print(exc.fields, exc.roots)
print(parsed.to_dicts())
```

```text
Logical terminal required for payload (array). Use one of: validation, to_polars, to_pandas, to_dict, to_dicts, to_tuples, item, to_dataclasses, to_pydantic
('payload',) ('array',)
[{'id': 1, 'payload': [1, 2]}, {'id': 2, 'payload': [3]}]
```

The error names each affected field and its structured type, and `exc.supported_terminals` lists the terminals that resolve them. `to_pyarrow()` and `to_ibis()` also resolve them. The error carries field names only and keeps data values out of the message. [Transform stages](../11-conforming-data/index.md#transform-stages) describes the structured transport behind this.

## Egress formats

<!-- concept:377 -->

Each frame terminal fixes the output library, whatever the source. `to_polars()` returns an eager Polars `DataFrame` and moves a non-Polars result through Arrow, bypassing pandas. `to_pandas()` returns a pandas result as is and converts anything else through Arrow. `to_pyarrow()` exports a PyArrow `Table`. `to_narwhals(as_lazy=None)` wraps the Polars result in Narwhals. `to_ibis()` returns an Ibis result unchanged, still on its connection, and loads any other result into an in-memory Ibis table.

```python
for name in ("to_polars", "to_pandas", "to_pyarrow", "to_narwhals", "to_ibis"):
    print(name, type(getattr(large, name)()).__name__)
```

```text
to_polars DataFrame
to_pandas DataFrame
to_pyarrow Table
to_narwhals DataFrame
to_ibis Table
```

The Python data terminals all convert the Polars frame from `to_polars()`, so they behave the same whichever backend ran the plan, and temporal values arrive as Python `date` and `datetime` objects. The conversion code lives in `mountainash.pydata.egress`; the relation terminals are the supported way to reach it.

<!-- concept:483 -->

`to_dict()` returns one list per column, `to_dicts()` one dict per row and `to_tuples()` one tuple per row in column order. `to_dict_of_series_polars()` and `to_dict_of_series_pandas()` return one Series per column.

```python
ordered = ma.relation(orders).sort("order_id")
print(ordered.to_dict())
print(ordered.to_dicts()[0])
print(ordered.to_tuples()[0])
```

```text
{'order_id': [1, 2, 3], 'customer_id': [10, 20, 10], 'amount': [25.0, 40.0, 15.5]}
{'order_id': 1, 'customer_id': 10, 'amount': 25.0}
(1, 10, 25.0)
```

These are the reverse of [Relations from Python data](../07-relations/index.md#relations-from-python-data): passing `to_dicts()` output back to `ma.relation` gives the same table.

<!-- concept:484 -->

`to_dataclasses(cls, *, spec=None, auto_derive_schema=True, apply_defaults=False)` builds one dataclass instance per row, and `to_pydantic(cls, *, spec=None, auto_derive_schema=True)` one Pydantic model per row. Columns match fields by name, and columns with no field are dropped from the output. A field with no matching column receives `None`; `apply_defaults=True` gives it the dataclass default. Pydantic validation applies its usual coercion. A [TableSchema](../10-table-schemas-and-datapackage/index.md#tableschema-and-fields) passed as `spec` can rename columns on the way out with `rename_from`:

```python
from dataclasses import dataclass

import pydantic


@dataclass
class Order:
    order_id: int
    amount: float
    note: str = "none"


class OrderModel(pydantic.BaseModel):
    order_id: str
    amount: float


@dataclass
class Payment:
    id: int
    total: float


print(ordered.to_dataclasses(Order)[0])
print(ordered.to_dataclasses(Order, apply_defaults=True)[0])
print(ordered.to_pydantic(OrderModel)[0])
spec = ma.TableSchema(fields={
    "id": ma.FieldDefinition(type="integer", rename_from="order_id"),
    "total": ma.FieldDefinition(type="number", rename_from="amount"),
})
print(ordered.to_dataclasses(Payment, spec=spec)[0])
```

```text
Order(order_id=1, amount=25.0, note=None)
Order(order_id=1, amount=25.0, note='none')
order_id='1' amount=25.0
Payment(id=1, total=25.0)
```

A missing required field also receives `None`, silently, so check the model against the relation's [columns](../07-relations/index.md#schema-and-columns) when that matters. With `auto_derive_schema=True` and no `spec`, the terminal derives a schema from the class to guide conversion.

<!-- concept:485 -->

`to_named_tuples()` returns rows as named tuples of a generated `Row` type. The terminal turns column names into valid identifiers: other characters become `_`, dots become `__`, a leading digit gets an `f` prefix, a Python keyword gets a trailing `_`, and duplicates get `_2`, `_3`. `to_typed_named_tuples(*, preserve_dates=False)` also sets `Row.__annotations__` from the column dtypes.

The indexed terminals group rows by one or more key columns: `to_index_of_dicts(index_fields)` returns a dict from key value to the list of row dicts with that key, and `to_index_of_tuples`, `to_index_of_named_tuples` and `to_index_of_typed_named_tuples` do the same with the other row types. Each grouped row keeps the key column.

```python
import datetime as dt

awkward = ma.relation(pl.DataFrame({"order id": [1], "class": ["a"], "placed": [dt.date(2026, 1, 1)]}))
print(awkward.to_named_tuples()[0])
typed = awkward.to_typed_named_tuples()[0]
print(type(typed).__annotations__)
by_customer = ordered.to_index_of_dicts("customer_id")
print({key: [row["order_id"] for row in rows] for key, rows in by_customer.items()})
```

```text
Row(order_id=1, class_='a', placed=datetime.date(2026, 1, 1))
{'order_id': <class 'int'>, 'class_': <class 'str'>, 'placed': <class 'str'>}
{10: [1, 3], 20: [2]}
```

By default, `to_typed_named_tuples()` annotates date and time columns as `str`, while the values themselves are `date` and `datetime` objects. `preserve_dates=True` makes the annotations match the values and leaves the values as they are.

## Scalar terminals

<!-- concept:378 -->

A scalar terminal returns one Python value. `item(column, row=0)` returns one cell; it raises `KeyError` for an unknown column and `IndexError` for a row outside the result, and `row` must be zero or positive. `count_rows()` returns the row count. `sum`, `avg` (alias `mean`), `min`, `max`, `product`, `std_dev`, `variance` and `any_value` take a column name and aggregate over the whole relation.

Each aggregate terminal is the matching [aggregate expression](../05-namespaces-aggregates-and-windows/index.md#aggregates) applied with no grouping keys, followed by `item`. The aggregation runs in the source engine, so a DuckDB relation computes its total in SQL and fetches only the single value:

```python
for source in (orders, orders_db):
    rel = ma.relation(source)
    print(rel.count_rows(), rel.sum("amount"), rel.mean("amount"), rel.max("order_id"), rel.item("amount", 1))
```

```text
3 80.5 26.833333333333332 3 40.0
3 80.5 26.833333333333332 3 40.0
```

As in the aggregate expressions, these terminals skip nulls. On an empty relation, `avg`, `min` and `max` return `None` and `sum` returns `0` or `None` depending on the backend. `any_value` returns some value from the column, and which one can differ between backends and runs. Write an aggregate that takes more than one argument, or one missing from the list above, with `select` and `item`:

```python
print(ma.relation(orders).select(ma.col("customer_id").n_unique().alias("customers")).item("customers"))
```

```text
2
```

!!! warning "Backend limit"
    `product()` raises on every Ibis and Narwhals backend, as the `product` aggregate expression does (see [Aggregates](../05-namespaces-aggregates-and-windows/index.md#aggregates)).

`describe()` collects the relation and returns the native result's own `describe()` output: summary statistics as a Polars frame for a Polars source, a pandas frame for a pandas source and an Ibis table for an Ibis source. When the result type has no `describe`, the terminal raises `NotImplementedError`.

## Explain, fingerprint and snapshots

<!-- concept:379 -->

`explain()` returns a string description of the compiled plan and leaves the plan unexecuted. For a Polars plan it is Polars' optimised query plan, and for an Ibis plan it is the SQL that would be sent:

```python
plan = ma.relation(orders).filter(ma.col("amount") > 20).select("order_id", "amount")
print(plan.explain())
print(ma.relation(orders_db).filter(ma.col("amount") > 20).select("order_id", "amount").explain())
```

```text
FILTER col("amount") > 20.0
FROM
  DF ["order_id", "customer_id", "amount"]; PROJECT["order_id", "amount"] 2/3 COLUMNS
SELECT
  "t0"."order_id",
  "t0"."amount"
FROM "memory"."main"."orders" AS "t0"
WHERE
  "t0"."amount" > 20
```

When a plan moves data between engines, reads a resource, or has a source whose location is still unresolved, `explain()` prints the relation tree, with the execution location of each node and each declared transfer. [Relation objects](../07-relations/index.md#relation-objects) shows that form. [Execution targets and backend capabilities](../09-execution-targets-and-capabilities/index.md#execution-targets-and-locations) describes locations and transfers.

<!-- concept:380 -->

`fingerprint(*, keys, columns, batch_size=5000)` summarises the content of a relation as a small Polars frame of hashes. `keys` is the ordered logical key of a row and `columns` names the value columns to check. The result has one `keys` row and one row per value column, each with a row count, a fingerprint and descriptors of the hashing profile and schema. Two relations with equal fingerprints for a column almost certainly hold the same values for each key, wherever they are stored, so comparing the frames checks content across engines while the data stays where it is:

```python
local = ma.relation(orders).fingerprint(keys=["order_id"], columns=["amount", "customer_id"])
remote = ma.relation(orders_db).fingerprint(keys=["order_id"], columns=["amount", "customer_id"])
print(local.select("kind", "column", "row_count"))
print(local.equals(remote))
```

```text
shape: (3, 3)
┌────────┬─────────────┬───────────┐
│ kind   ┆ column      ┆ row_count │
│ ---    ┆ ---         ┆ ---       │
│ str    ┆ str         ┆ u64       │
╞════════╪═════════════╪═══════════╡
│ keys   ┆ null        ┆ 3         │
│ column ┆ amount      ┆ 3         │
│ column ┆ customer_id ┆ 3         │
└────────┴─────────────┴───────────┘
True
```

Filter the relation first to fingerprint a subset of rows. Duplicate rows all contribute. Equal hashes are strong evidence of equal content but fall short of proof, and they leave key uniqueness unchecked. Compare fingerprints only when their profile and schema descriptors match.

!!! warning "Backend limit"
    `fingerprint()` reads the result in bounded batches and supports Polars sources and DuckDB through Ibis. Other backends, including pandas sources, raise `BackendCapabilityError: No qualified bounded fingerprint reader`.

<!-- concept:381 -->

`snapshot()` evaluates the plan now and returns a new relation over an independent native copy of the result. The snapshot keeps the result as it was at that moment, while the original relation keeps reading the live source. On a database the copy is a temporary table that mountainash creates and owns:

```python
live = ma.relation(orders_db).filter(ma.col("amount") > 20)
frozen = live.snapshot()
con.insert("orders", pl.DataFrame({"order_id": [4], "customer_id": [30], "amount": [99.0]}).to_arrow())
print(frozen.count_rows(), live.count_rows())
print(frozen.explain())
```

```text
2 3
SELECT
  *
FROM "ma_owned_ab6ced769b224a1797f20d21ea007c30"
```

mountainash generates the temporary table name. Outside a scope, the copy lives as long as relations derived from it are reachable. `ma.materialization_scope()` gives explicit control: closing the scope releases the snapshots taken through it, and using one afterwards raises `MaterializationScopeClosedError`. [Materialization scopes and checkpoints](../09-execution-targets-and-capabilities/index.md#materialization-scopes-and-checkpoints) describes scopes and checkpoint policies.

!!! warning "Backend limit"
    An Ibis snapshot needs a source bound to a connection, and all of the plan's Ibis inputs must use that one connection. Dialects that cannot create owned temporary tables (MySQL, SingleStoreDB, Exasol) refuse snapshots (`relations/backends/capabilities/ibis/dialects/*/extensions_mountainash/relation.py`).
