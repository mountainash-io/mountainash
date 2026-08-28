# TypeSpec and conformance

A schema is a contract about shape. `TypeSpec` is mountainash's serialisable representation of that contract. `conform()` is a single relation method that turns the contract into a transformation: cast types, rename columns, fill nulls, handle missing fields, on any backend.

## TypeSpec

`TypeSpec` is a flat, Frictionless-aligned type specification:

```python
import mountainash as ma

spec = ma.typespec({
    "id":     "integer",
    "name":   "string",
    "amount": "number",
    "ts":     "datetime",
})
```

Under the hood this is a Pydantic model with a list of `FieldSpec` entries — name, type, format, constraints, foreign keys, custom metadata. The structure matches Frictionless Table Schema, which means you can load and emit `datapackage.json` and `schema.json` files byte-equivalent.

### What's in a `FieldSpec`

- `name` and `type` (Frictionless type names: `string`, `integer`, `number`, `boolean`, `date`, `time`, `datetime`, `array`, `object`, `geojson`, …)
- `format`, `description`, `title`, `example`
- `constraints`: required, unique, min, max, pattern, enum
- `foreign_key`: cross-table reference (drives the DAG's constraint edges)
- `enum_weights`: for weighted enums (used by synthetic-data generators)
- Custom types via `CustomTypeRegistry` for semantic types your domain cares about

`TypeSpec` and `FieldSpec` are deliberately **structurally Frictionless** — flat fields matching the Frictionless layout, not nested custom submodels. If Frictionless gains a property, we add it as a peer field. If we add a property they don't have, it's clearly namespaced.

## Sources

`TypeSpec.from_*` and `ma.typespec(...)` accept many inputs:

```python
ma.typespec({"id": "integer", "name": "string"})    # simple dict
TypeSpec.from_dataframe(df)                          # extract from a DataFrame
TypeSpec.from_dataclass(MyClass)                     # extract from a dataclass
TypeSpec.from_pydantic(MyModel)                      # extract from a Pydantic model
TypeSpec.from_frictionless("schema.json")            # load a Frictionless schema
```

Going the other way:

```python
spec.to_dict()                                       # plain dict
spec.to_frictionless()                               # Frictionless dict
```

## Conformance

`conform(spec)` is a relation method:

```python
ma.relation(df).conform(spec).to_polars()
```

It compiles to a `ProjectRelNode` whose expressions are derived from the TypeSpec fields:

- **Missing column?** Add it as `null` (or as `spec.field.constraints.default` if set).
- **Type mismatch?** Cast to the spec'd type.
- **Extra columns?** By default, drop them. Configurable.
- **Renames?** If a field has `aliases`, normalise to the canonical name.
- **Null handling?** If a field has `null_fill`, fill with it.

The result is a frame whose schema matches the spec, ready for downstream work.

### Why this matters

If you have ever written code that looks like this:

```python
df = df.rename(columns={"customer_id": "id", "amt": "amount"})
df["amount"] = df["amount"].astype("float64")
df["ts"]     = pd.to_datetime(df["ts"], errors="coerce")
df["region"] = df["region"].fillna("UNK")
df = df[["id", "name", "amount", "ts", "region"]]
```

…you have written, by hand, a conformance step that is wholly derivable from the schema. The bug surface in code like this is large: a typo in a column name silently drops it; a cast failure produces NaN instead of NULL; the column order is documented only by the code. Schema-driven conformance replaces that whole block with `relation.conform(spec)` and moves the source of truth into a single document that your validation, contract, and generation steps share.

### Cross-backend

`conform()` is cross-backend automatic. The only known limitation today is Ibis coalesce type strictness when `null_fill` mixes string columns with numeric literals — a tracked divergence, not a silent fault.

### Structured (`array`/`object`) fields

`array` and `object` fields ingress through portable JSON text on every backend, or
through a no-round-trip native `list`/`struct` source column where the backend has
one (Polars, its Narwhals wrappers, Ibis). Pandas and Narwhals-Pandas have no native
list/struct dtype, so a structured field there is always opaque native Python
containers, resolved through logical conversion rather than either path above.

Decoding JSON text opens a **physical/logical boundary**. A decoding action
(`coerce`, `discard_value`, `discard_row`) produces a column whose *logical* value —
the decoded Python `list`/`dict` — drives validation and logical egress, but the
*physical* column is a closed transport carrier for everything else. A transported
field cannot be used as a filter, sort, join, grouping, aggregate, or distinct
input before logical decoding. `to_polars()`, `to_pandas()`, `to_dicts()`,
`to_tuples()`, `to_dataclasses()`, `to_pydantic()`, and `validation` are all
logical terminals: they resolve the decode and return the logical value. Only
DAG-level **native collection** (a bare `dag.collect()`/`dag.collect_with_drift()`)
fails closed — calling it on a relation whose plan still needs that decode raises
`LogicalTerminalRequired`, naming the affected fields. `evolve` (preserve the
physical source, decode only for validation) and a structural-only conform (no
value transform) stay natively collectible — nothing to decode, nothing to fail
closed on.

`dag.validate(specs)` is always a logical terminal: JSON Schema, identity,
uniqueness, and foreign-key checks compare decoded logical values, never raw
transported text — whitespace and object-key order never change the outcome.

## DataPackage

Frictionless `datapackage.json` is the multi-resource container format. mountainash supports it natively:

```python
pkg = ma.DataPackage.from_descriptor("datapackage.json")
dag = pkg.to_relation_dag()
df  = dag.collect("orders")
```

`DataResource` knows how to load its data via the storage facade — local paths bypass it, remote paths (S3, GCS, HTTPS) go through `mountainash-utils-files`'s `StorageFacade` (optional install).

Round-trip:

```python
pkg2 = dag.to_package()
pkg2.write("./out/datapackage.json")
```

The raw Frictionless schema dict is stored verbatim on `DataResource.table_schema`, so the round-trip is byte-equivalent. Conversion to a `TypeSpec` happens lazily inside the visitor when conform actually runs.

## What this enables

A TypeSpec is the same object that:

- drives `.conform(spec)` for transformation,
- compiles to a [data contract](datacontracts.md) for validation,
- emits a Frictionless descriptor,
- feeds a synthetic-data generator (out of scope for the current package; see [vision](../vision.md)),
- defines the foreign-key graph that the [relation DAG](relations.md#dag-and-frictionless) uses for constraint edges.

One schema, all of the above. Authored once.

## Related

- [Relations](relations.md) — `.conform()` is a relation method
- [Data contracts](datacontracts.md) — TypeSpec → validation
- [Cross-backend execution](cross-backend.md) — how conform compiles per-backend
