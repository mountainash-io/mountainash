# Shared schemas and conformance vs. hand-written schema code

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

spec = ma.table_schema({
    "id":     "integer",
    "name":   "string",
    "amount": "number",
    "ts":     "datetime",
    "region": "string",
})

ma.relation(raw_df).conform(spec).to_polars()
```

`conform(spec)` builds a deferred relation node. At execution it applies conversion, missing-column and extra-column policies, `rename_from` bindings and `null_fill` instructions. The same declarations can be compiled into validation checks; conversion alone does not assert that their constraints passed.

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
import mountainash as ma
from mountainash.typespec import UniversalType

spec = ma.TableSchema(fields={
    "id": ma.FieldDefinition(type=UniversalType.INTEGER, rename_from="customer_id"),
    "name": ma.FieldDefinition(type=UniversalType.STRING),
    "amount": ma.FieldDefinition(type=UniversalType.NUMBER, rename_from="amt"),
    "ts": ma.FieldDefinition(type=UniversalType.DATETIME),
    "region": ma.FieldDefinition(type=UniversalType.STRING, null_fill="UNK"),
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

- **Cross-backend execution.** The same TableSchema drives conform and validation through the supported Polars, Narwhals and Ibis paths, subject to their declared capabilities.
- **Conformance and validation stay separate.** Conformance applies casts, fills and renames; contract checks assess constraints on the resulting values.
- **Interchange without format-owned declarations.** Frictionless codecs preserve supported declaration semantics. Raw DataPackage storage has a separate lossless contract.
- **Reusable definitions.** An unnamed FieldDefinition can be attached under several local names. `.variant(...)` makes an independent copy with changed requirements or source binding.

Dataclass and Pydantic extraction remain supported schema inputs. Pydantic models can also be passed to `ma.datacontract(...)`; existing Python models do not need to become Mountainash contracts.

## On `CREATE TABLE` and warehouse DDL

DDL describes the warehouse. TableSchema describes requirements used by the application. Native schema adapters translate representable type information; they do not claim that a warehouse type enforces every application constraint.

## What this costs

- **Representation boundaries.** A backend or interchange format cannot necessarily express every declaration. Native overrides and unsupported operations retain explicit outcomes rather than silently switching engines.
- **Qualification.** Schema construction, native type construction, conversion and validation are distinct capabilities. A successful schema conversion is not evidence that every operation executes on that backend.

## Where we'd point elsewhere

- **Single-runtime projects with pandera already in place.** The migration probably doesn't pay back the cost of doing it.
- **Schemas that change weekly.** Explicit requirements are most useful when consumers need a shared contract; unconstrained exploration may not need them.

## Related

- Technical: [Shared schemas and conformance](../features-technical/typespec-conform.md)
- Comparison: [Data contracts](datacontracts.md)
- Vision: [What "virtually any data" means](../vision.md#what-virtually-any-data-means)
