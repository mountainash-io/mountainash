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

`TypeSpec` and `FieldSpec` are dataclasses carrying names, types, formats, constraints, keys and custom metadata. Their typed representation follows Frictionless Table Schema; lossless raw descriptor storage belongs to `DataResource.table_schema`.

### What's in a `FieldSpec`

- `name` and `type` (Frictionless type names: `string`, `integer`, `number`, `boolean`, `date`, `time`, `datetime`, `array`, `object`, `geojson`, …)
- `format`, `description`, `title`, `example`
- `constraints`: required, unique, min, max, pattern, enum
- `foreign_key`: cross-table reference (drives the DAG's constraint edges)
- `enum_weights`: for weighted enums (used by synthetic-data generators)
- `dtype`: a portable fixed-decimal or lexical numeric refinement, persisted under `x-mountainash.dtype`
- Custom types via `CustomTypeRegistry` for semantic types your domain cares about

`TypeSpec` and `FieldSpec` are deliberately **structurally Frictionless** — flat fields matching the Frictionless layout, not nested custom submodels. If Frictionless gains a property, we add it as a peer field. If we add a property they don't have, it's clearly namespaced.

### Exact numeric declarations

Use `ma.DecimalDtype(precision=p, scale=s)` on a `NUMBER` field, or
`ma.MountainashDtype.LEXICAL_INTEGER` / `LEXICAL_DECIMAL` on a `STRING` field.
The decimal descriptor is immutable and strict: `1 <= p <= 38`, `0 <= s <= p`;
bare `DECIMAL`, Boolean parameters and competing `backend_type` hints are rejected.
Ordinary `NUMBER` still lowers to FP64 without an explicit refinement.

The descriptor survives nested TypeSpec/Frictionless round trips. Native decimal
extraction retains p/s, and `compare_specs` distinguishes changed p/s and FP64.
Native strings do not recover lexical identity: compare stored data against the
declaration's physical lowering, keeping authored semantic identity separate.

Explicit `.cast(dtype, failure_behavior="throw", rounding="TIE_TO_EVEN")`
performs checked conversion; `TIE_AWAY_FROM_ZERO` is also available. It rounds
once before checking decimal range. Lexical results are canonical strings,
including unbounded values, and raw egress preserves Decimal/string carriers.
See the [numeric execution matrix](../../../README.md#exact-decimal-and-lexical-numeric-types)
for backend representations and SQLite's fixed-decimal refusal.

Numeric conform uses the checked conversion contract, including nested OBJECT
and ARRAY-of-OBJECT fields within the existing structured support matrix.
Validated lexical identity survives transparent expression/relation operations
and DAG references. Arithmetic, ordering and incompatible-domain consumers raise
`LexicalNumericUseError`; an explicit numeric cast checks conversion, while a
STRING cast opts out. Native export/rewrap loses live semantic identity.

An explicit numeric TypeSpec also owns model egress; annotations do not silently
replace exact declarations with bounded integer/float types. Model constructors
own decoding. Resource reads may conform data and are not strict verification.
Strict readback checks physical schema first, then compares canonical checked
candidates with unchanged stored lexical values. An inferred frame followed by
conform is not a preserving constructor.

`classify_cast(source, target)` describes the whole source domain:
`SAFE` preserves every value, `NARROWING` preserves fitting values but rejects
others, `LOSSY` can change a successful result, and `UNSAFE` has no established
guarantee. `is_safe_cast` accepts only `SAFE`. Decimal scale loss takes precedence
over range narrowing; I64/U64→FP64 and timestamp→date are lossy. Arbitrary STRING
is not a validated lexical numeric domain. Conform type and foreign-key drift
retain the category rather than reducing every non-safe cast to `"unsafe"`.

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

Building the relation does not read data. It adds a deferred `ConformRelNode`; at execution the backend derives its operations from the TypeSpec fields:

- **Missing column?** Add it as `null` (or as `spec.field.constraints.default` if set).
- **Type mismatch?** Cast to the spec'd type.
- **Extra columns?** By default, drop them. Configurable.
- **Renames?** If a field has `aliases`, normalise to the canonical name.
- **Null handling?** If a field has `null_fill`, fill with it.

The result is a frame whose schema matches the spec, ready for downstream work.

### The relation owns its declaration

`conform()` copies the spec (and any `contract=` override) when the relation is built. Editing the spec afterwards changes only relations built after the edit:

```python
old = ma.relation(df).conform(spec)
spec.fields[0].type = UniversalType.STRING
new = ma.relation(df).conform(spec)   # uses the edited declaration
# `old` still conforms to the original type, on every execution
```

Build a new relation to pick up an edited declaration; there is no live-reference mode.

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
