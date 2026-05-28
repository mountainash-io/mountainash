# Data contracts vs. pandera and great_expectations

## What we built this to address

Schema validation tools tend to be coupled to a runtime. pandera was historically pandas-only (Polars support is improving but parallel). great_expectations runs on its own infrastructure. pydantic validates one record at a time, not a frame. SQL `CHECK` constraints fire only at insert time and only on the warehouse.

We've seen the resulting state in many projects: the same fields described in three places — a pandera schema for dev, a `CREATE TABLE` for the warehouse, a Pydantic model for the API — kept in sync by hand and drifting silently. The drift is uninteresting until somebody changes one of them and forgets the others.

The deeper friction is that validation tools tend to want to own the schema. So a project ends up with parallel definitions because each tool needs its own. None of them is wrong; together they're a maintenance liability.

## How we approach it

One contract, compiled once from the schema, runs on any backend the relation API supports:

```python
import mountainash as ma

spec = ma.typespec({"id": "integer", "amount": "number", "region": "string"})

Contract = ma.datacontract(spec)
Contract.validate(df)    # works on Polars, pandas (via Narwhals), or Ibis tables
```

The contract is compiled from the schema. The validation expressions go through the same cross-backend engine that compiles ordinary mountainash expressions — there's no second validation path. If the expression system can compile something, the contract can validate it.

## Side-by-side: parallel contracts vs. one contract

```python
# What we've seen in many projects: parallel contracts
class OrdersSchema(pa.DataFrameModel):                  # pandera
    id: int
    amount: float
    region: str = pa.Field(isin=["E", "W", "N", "S"])

# AND
ge_suite = ExpectationSuite(...)                         # great_expectations

# AND, in the warehouse
"""
CREATE TABLE orders (
  id INT NOT NULL,
  amount NUMERIC,
  region TEXT CHECK (region IN ('E','W','N','S'))
)
"""

# AND, in the API layer
class Order(BaseModel):                                   # pydantic
    id: int
    amount: float
    region: Literal["E", "W", "N", "S"]
```

```python
# With mountainash: one contract
spec = ma.typespec({
    "id":     {"type": "integer", "constraints": {"required": True}},
    "amount": "number",
    "region": {"type": "string",  "constraints": {"enum": ["E", "W", "N", "S"]}},
})

Contract = ma.datacontract(spec)
Contract.validate(df)
```

The TypeSpec is the contract. The contract validates on any backend. The same TypeSpec also drives [conformance](typespec-conform.md), can be emitted as a Frictionless `datapackage.json` descriptor (which the warehouse team can consume), and can be derived from pandera, Pydantic, or Frictionless JSON when one of those already exists.

## What mountainash accepts as input

Existing schemas don't have to be discarded:

| Source already in the project | Use it directly |
|-------------------------------|-----------------|
| A pandera `DataFrameModel` subclass | `ma.datacontract(MyModel)` |
| A Pydantic `BaseModel` subclass | `ma.datacontract(MyModel)` |
| A Frictionless `schema.json` file | `ma.datacontract("schema.json")` |
| A plain dict (simple or Frictionless) | `ma.datacontract({"id": "integer", ...})` |
| A `TypeSpec` | `ma.datacontract(spec)` |

This makes the migration path incremental. Lift the existing schema in, get cross-backend validation today, refactor the schema source on whatever timeline makes sense.

## Custom rules

Constraints in the schema cover the common cases (`required`, `unique`, `enum`, `min`, `max`, `pattern`). For business rules that don't fit constraint shapes, subclass:

```python
class OrdersContract(ma.datacontract(spec)):
    @classmethod
    def rules(cls):
        return [
            (ma.col("amount").ge(0), "amount must be non-negative"),
            (ma.col("region").is_in(["E", "W", "N", "S"]), "region must be a cardinal"),
        ]
```

The rules are mountainash expressions, so they run on Polars / pandas / Ibis identically. A rule that runs as a Polars predicate in dev runs as a SQL `WHERE` clause in the warehouse without rewriting.

## On great_expectations

great_expectations is a different shape of tool. It's a framework with its own infrastructure — data docs, checkpoints, store backends, runbook integration — and a lot of operational features mountainash doesn't have and isn't trying to have. For a project that wants a managed validation infrastructure, GE may still be the right answer.

What we're offering is a library-level alternative: a schema and a contract object, no daemon, no store backend, no orchestration. The contract drops into existing code, validates at the boundaries that matter to the caller, and surfaces failures through ordinary exception handling.

## What this costs

- **The failure-report shape is in flux.** Today `.validate()` raises with a structured `.errors` list. Before 1.0, the exact shape of that list is the most likely thing we'll change in this area. Downstream tooling that consumes contract failures should expect to adapt.
- **Constraint coverage.** The native set is the standard Frictionless constraints (required, unique, enum, min, max, pattern) plus expression-based custom rules. A specific pandera or great_expectations check with no obvious expression equivalent will need replacing or porting.

## Where we'd point elsewhere

- **Existing great_expectations infrastructure that's working.** The operational features are out of scope for mountainash. GE for the platform, mountainash for the inline-validation cases — that's a coexistence we expect to be common.
- **Single-runtime projects with pandera in place.** The portability dividend isn't on offer.

## Related

- Technical: [Data contracts](../features-technical/datacontracts.md)
- Comparison: [TypeSpec and conformance](typespec-conform.md)
