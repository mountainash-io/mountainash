# TypeSpec and conformance vs. hand-written schema code

## What we built this to address

Every project that loads data from external sources has a conform step somewhere. It typically looks like this:

```python
def conform_orders(df):
    df = df.rename(columns={"customer_id": "id", "amt": "amount"})
    df["amount"] = df["amount"].astype("float64")
    df["ts"]     = pd.to_datetime(df["ts"], errors="coerce")
    df["region"] = df["region"].fillna("UNK")
    return df[["id", "name", "amount", "ts", "region"]]
```

This isn't bad code. It's code that is wholly derivable from a schema which already exists somewhere else in the project — in the data engineer's documentation, in a `CREATE TABLE` statement, in a Pydantic model used by the API, in a Frictionless `datapackage.json` checked into the repo for reference.

The schema lives in two places, sometimes more. We've watched them drift. The drift produces bugs in code paths that the schema document says are impossible. Schema-as-comment is the default state because, without a unifying mechanism, schema-as-code doesn't carry across the validation tool, the conformance code, the API layer, and the warehouse.

## How we approach it

The schema becomes the conformance step:

```python
import mountainash as ma

spec = ma.typespec({
    "id":     "integer",
    "name":   "string",
    "amount": "number",
    "ts":     "datetime",
    "region": "string",
})

ma.relation(raw_df).conform(spec).to_polars()
```

`conform(spec)` compiles to a relation node whose expressions are derived from the spec fields: cast each column to its declared type, add any missing columns as null, drop unexpected columns (configurable), apply renames declared by `aliases`, fill nulls per `null_fill`. The five lines of hand-rolled code go away. The schema is the source of truth — and it's the same schema that drives validation, generation, documentation, and Frictionless interchange.

## Side-by-side

```python
# Hand-rolled
def conform_orders(df):
    df = df.rename(columns={"customer_id": "id", "amt": "amount"})
    df["amount"] = df["amount"].astype("float64")
    df["ts"]     = pd.to_datetime(df["ts"], errors="coerce")
    df["region"] = df["region"].fillna("UNK")
    return df[["id", "name", "amount", "ts", "region"]]

# mountainash, schema-driven
spec = ma.typespec({
    "id":     {"type": "integer", "aliases": ["customer_id"]},
    "name":   "string",
    "amount": {"type": "number",  "aliases": ["amt"]},
    "ts":     "datetime",
    "region": {"type": "string",  "null_fill": "UNK"},
})

ma.relation(raw_df).conform(spec).to_polars()
```

The mountainash form is longer per line but shorter overall — and, more importantly, the spec is the same object that:

- Compiles into a [data contract](datacontracts.md) for validation: `Contract = ma.datacontract(spec)`
- Round-trips through a Frictionless `datapackage.json` file
- Can feed a synthetic-data generator (out of scope for the current package; see [vision](../vision.md))
- Defines the field metadata that the [relation DAG](../features-technical/relations.md#dag-and-frictionless) uses for constraint edges via foreign keys

## On pandera schemas

pandera schemas are good. They're well-designed, they integrate with pandas/Polars, and they catch a lot of real bugs. For a single-backend project that's already on pandera, we wouldn't push a migration.

What mountainash adds is:

- **Cross-backend execution.** The same TypeSpec drives conform and validation on Polars, pandas (via Narwhals), and any Ibis-supported SQL engine.
- **Conformance, not just validation.** A pandera schema reports that the data is wrong. A TypeSpec compiles into a transformation that tries to make it right (cast, fill, rename) and then validates the result.
- **Frictionless round-trip.** TypeSpec is structurally aligned with Frictionless Table Schema. `schema.json` and `datapackage.json` files read and write byte-equivalent.
- **One source for multiple tools.** A pandera schema is for validation. A `CREATE TABLE` is for the warehouse. A Pydantic model is for the API. TypeSpec aspires to be one definition that conform, the data contract, the Frictionless descriptor, and (eventually) the generator all consume.

pandera schemas and Pydantic models can be used as input to `ma.datacontract(...)` directly — they don't have to be discarded to start with TypeSpec.

## On `CREATE TABLE` and warehouse DDL

DDL is for the warehouse. TypeSpec is for the application code that produces and consumes data flowing in and out of the warehouse. They live at different layers and we think both should exist. The honest framing isn't "TypeSpec replaces DDL"; it's "TypeSpec gives the application layer the same level of schema-as-code rigour that the warehouse layer already has."

## What this costs

- **Coverage.** The Frictionless type set is what's natively supported. Custom domain types are supported via `CustomTypeRegistry`, but the converter is hand-written. A project with many bespoke semantic types will do that work.
- **Ibis coalesce strictness.** Mixing string columns with numeric `null_fill` literals can hit Ibis type strictness. Tracked as a divergence with a clear error message; not a silent fault.

## Where we'd point elsewhere

- **Single-runtime projects with pandera already in place.** The migration probably doesn't pay back the cost of doing it.
- **Schemas that change weekly.** TypeSpec works best when the schema is a contract; for highly exploratory work, the schema definitions become as much churn as the code they replaced.

## Related

- Technical: [TypeSpec and conformance](../features-technical/typespec-conform.md)
- Comparison: [Data contracts](datacontracts.md)
- Vision: [What "virtually any data" means](../vision.md#what-virtually-any-data-means)
