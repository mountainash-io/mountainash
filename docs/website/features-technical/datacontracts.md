# Data contracts

A data contract is a runtime check that a DataFrame conforms to a known shape and known rules. mountainash compiles a contract once from any supported schema source, and then validates against any supported backend.

## The shape

```python
import mountainash as ma

spec = ma.typespec({"id": "integer", "amount": "number", "region": "string"})

Contract = ma.datacontract(spec)
Contract.validate(df)
```

`Contract` is a subclass of `BaseDataContract`. Calling `.validate(df)` runs the contract's checks against the frame and either returns successfully or raises with a structured report of failures.

## Schema sources

`ma.datacontract(source)` accepts:

| Source | Example |
|--------|---------|
| `TypeSpec` | `ma.datacontract(spec)` |
| Plain dict (simple) | `ma.datacontract({"id": "integer", "name": "string"})` |
| Plain dict (Frictionless) | `ma.datacontract({"fields": [{"name": "id", "type": "integer"}, ...]})` |
| Pydantic `BaseModel` subclass | `ma.datacontract(MyPydanticModel)` |
| pandera `DataFrameModel` subclass | `ma.datacontract(MyPanderaModel)` |
| Path to a Frictionless JSON file | `ma.datacontract("schema.json")` or `ma.datacontract(Path("schema.json"))` |
| An existing `BaseDataContract` subclass | `ma.datacontract(MyContract)` (returned as-is) |

The common path is `TypeSpec → datacontract`. The pandera and Pydantic paths are convenience for codebases that already have models in those forms.

## What gets validated

The contract checks:

- **Column presence.** Every required field in the schema is present.
- **Column types.** Each field's runtime type is compatible with the schema type.
- **Constraints.** `required`, `unique`, `min`, `max`, `pattern`, `enum` from FieldConstraints.
- **Custom rules.** Any expression-based rule added to the contract subclass.

Validation runs through the cross-backend expression system — the same engine that compiles `ma.col("x").gt(5)` to a native Polars / Ibis / Narwhals expression. There is no second validation path; if the expression system can compile it, the contract can validate it.

## Why this matters

Most data validation tools are tied to a particular runtime:

- pandera was historically pandas-only; the Polars story is improving but parallel.
- great_expectations runs on its own infrastructure.
- SQL `CHECK` constraints only fire at insert time.
- pydantic validates one record at a time, not a frame.

Each is fine in isolation, but a project that needs to validate the same data on multiple backends (e.g. a pandas pipeline in dev, an Ibis-backed warehouse in prod) ends up with two contracts that drift.

mountainash compiles **one** contract definition to **any** backend the relation API supports. The contract is authored at the schema, not at the engine.

## Custom rules

Subclass `BaseDataContract` to add expression-based rules:

```python
from mountainash.datacontracts.contract import BaseDataContract

class OrdersContract(ma.datacontract(spec)):
    @classmethod
    def rules(cls):
        return [
            (ma.col("amount").ge(0), "amount must be non-negative"),
            (ma.col("region").is_in(["E", "W", "N", "S"]), "region must be a cardinal"),
        ]
```

Rules are mountainash expressions, so they compile to whichever backend you're validating against. The same rule that runs as a Polars filter in dev runs as a SQL `WHERE` clause in your warehouse.

## What you get back

A validation result that names the violating column, the rule, and (where the backend supports it) the offending rows. The exact shape of the report is one of the surfaces still being settled in the alpha — the contract API works, but the failure-reporting structure is likely to change before 1.0.

## Composition with conform

Conform and validate are different stages, intentionally:

```python
result = (
    ma.relation(raw_df)
      .conform(spec)            # cast types, rename, fill nulls
      .pipe(lambda r: Contract.validate(r.to_polars()) or r)   # raise if violations
      .to_polars()
)
```

Conform brings raw input into the schema's shape. Validate confirms the schema's invariants. Many tools collapse the two into a single step; mountainash keeps them separate because they fail differently and you typically want different recovery behaviour at each stage.

## Status

The contract compiler is stable for the supported sources listed above. The failure-reporting structure (what `.validate()` raises and how it's shaped) is the most likely thing to change before 1.0 — currently it's an exception with a structured `.errors` list. If you build tooling that consumes contract failures, expect to pin or adapt.

## Related

- [TypeSpec and conformance](typespec-conform.md) — the schema layer underneath
- [Expressions](expressions.md) — what custom rules are made of
- [Cross-backend execution](cross-backend.md) — how rules dispatch per-backend
