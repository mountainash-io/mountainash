# `Relation.unnest()` — struct column expansion

`unnest()` expands one or more struct columns into top-level columns named `{column}{separator}{field}`.

## Signature

```python
Relation.unnest(*columns: str, separator: str) -> Relation
```

| Parameter | Type | Purpose |
|-----------|------|---------|
| `*columns` | `str` (positional, one or more) | Names of struct columns to expand. Raises `ValueError` if empty. |
| `separator` | `str` (keyword-only) | Joins the struct column name and field name. Use `""` to use the field name as-is. |

## Example

```python
import polars as pl
import mountainash as ma

df = pl.DataFrame({
    "id": [1, 2],
    "address": [
        {"street": "1 Main",  "city": "Sydney"},
        {"street": "2 Oak",   "city": "Melbourne"},
    ],
})

ma.relation(df).unnest("address", separator="_").to_polars()
# ┌────┬────────────────┬──────────────────┐
# │ id ┆ address_street ┆ address_city     │
# │ i64┆ str            ┆ str              │
# ╞════╪════════════════╪══════════════════╡
# │ 1  ┆ 1 Main         ┆ Sydney           │
# │ 2  ┆ 2 Oak          ┆ Melbourne        │
# └────┴────────────────┴──────────────────┘
```

## Multiple columns

```python
ma.relation(df).unnest("address", "coords", separator=".").to_polars()
# address.street, address.city, coords.lat, coords.lng
```

Columns are processed in order; each struct column is dropped after its fields are added.

## Backend support

| Backend | Status |
|---------|--------|
| Polars | Native, via `pl.LazyFrame.unnest(columns, separator=…)` |
| Ibis | Synthesized via `mutate({prefix+field: struct_col[field], …}).drop(col)` |
| Narwhals | **Not supported** — raises `NotImplementedError`. Narwhals has no frame-level unnest primitive; full support requires schema introspection synthesis (deferred Phase 2 work). |

If you need unnest on a pandas DataFrame today, route through Polars:

```python
ma.relation(pl.from_pandas(df)).unnest(...).to_pandas()
```

## How it routes through the AST

- API call: `Relation.unnest(*columns, separator)` constructs an `ExtensionRelNode(operation=ExtensionRelOperation.UNNEST, options={"columns": [...], "separator": "..."})`.
- Visitor dispatch lands on `MountainashExtensionRelationSystemProtocol.unnest(relation, /, *, columns, separator)`.
- Each backend implements that protocol method.

To add unnest to a new backend, implement the protocol method on your extension class — see [extension-points.md](extension-points.md) and [adding-operations.md](adding-operations.md).
