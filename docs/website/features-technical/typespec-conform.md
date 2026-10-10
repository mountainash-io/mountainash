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

## Exact decimals

`ma.DecimalDtype(precision, scale)` is an exact decimal: `precision` is the total number of digits, `scale` the digits after the point (`1 <= precision <= 38`, `0 <= scale <= precision`). Declare it on a field, and convert into it with an explicit rounding mode:

```python
from decimal import Decimal

import mountainash as ma
from mountainash.typespec import FieldSpec, TypeSpec, UniversalType

d = ma.DecimalDtype(precision=10, scale=3)

# Declare it (persisted under `x-mountainash.dtype`; the Frictionless type stays `number`)
spec = TypeSpec(fields=[FieldSpec(name="amount", type=UniversalType.NUMBER, dtype=d)])

# Convert into it: `rounding=` is required for a decimal target and rejected for any other
ma.col("amount_text").cast(d, rounding="half_to_even")
ma.col("amount_text").cast(d, rounding="to_zero", failure_behavior="null")

# A typed literal in the same domain, so comparisons are exact
ma.col("amount_text").cast(d, rounding="half_to_even") >= ma.lit(Decimal("0.010"), dtype=d)
```

### Rounding modes

There are exactly three, and no default: a conversion that loses digits should say how.

| Input | `half_to_even` | `half_away_from_zero` | `to_zero` |
|---|---|---|---|
| `"0.00449"` | `0.004` | `0.004` | `0.004` |
| `"0.0045"` | `0.004` | `0.005` | `0.004` |
| `"-0.0045"` | `-0.004` | `-0.005` | `-0.004` |
| `"0.0055"` | `0.006` | `0.006` | `0.005` |
| `"-0.0059"` | `-0.006` | `-0.006` | `-0.005` |

(all to `DecimalDtype(10, 3)`)

### Failures

- **Invalid text** (`"12x"`, `""`, `NaN`, infinity) raises under `failure_behavior="throw"` (the default) and becomes null under `"null"`. Null stays null.
- **Integer-part overflow after rounding raises under both behaviours.** `"9999999.9995"` to `DecimalDtype(10, 3)` rounds up to `10000000.000`, which does not fit, so it raises even with `failure_behavior="null"`. A range mistake in your declaration is never silently turned into nulls. `to_zero` cannot carry, so `"9999999.9995"` gives `9999999.999`.

### Precision limits

A **declaration** can use any precision up to 38. A **cast target** is limited to precision 36 (`.cast(DecimalDtype(37, ...))` raises when the expression is built), because the conversion needs one spare integer digit and one spare fractional digit beyond the target.

### Sources

- **Text** is trimmed and `_` separators are removed before parsing, on every backend, so `" 1_000.5 "` becomes `1000.5`. Exponents (`"1e2"`) and a leading `+` or `.` parse. This applies to decimal-target casts only, not to ordinary values.
- **Floats** convert by their shortest displayed form, not their binary value: `2.675` with `half_to_even` at scale 2 gives `2.68`, and with `to_zero` gives `2.67`. Converting the exact binary value would give `2.67` for both and differ between engines.
- **Integers and decimals** convert exactly.

### Backend support

| Identity | Decimal casts |
|---|---|
| polars, polars-lazy | supported |
| ibis-duckdb, ibis-polars | supported, identical results |
| narwhals-polars, narwhals-lazy, narwhals-pandas, pandas | refused with `BackendCapabilityError`, pending Narwhals [#3698](https://github.com/narwhals-dev/narwhals/issues/3698) (no round mode) and [#3702](https://github.com/narwhals-dev/narwhals/issues/3702) (no non-strict cast) |
| ibis-sqlite | refused with `BackendCapabilityError`: SQLite has no fixed-precision decimal type |

A refusal is a declared capability, raised before any data is read. It never falls back to another engine.

### Known limits

The conversion is one vectorised native expression with no per-row checks, so three edge cases follow the engine's own behaviour. They are documented rather than detected:

1. **Wider than the intermediate.** The text is first parsed into an intermediate decimal of `18` digits (when `precision <= 16`) or `38` digits, with `intermediate_scale = width - (precision - scale) - 1`. A value with more integer digits than that fits raises under `"throw"` and becomes null under `"null"`, indistinguishable from invalid text.
2. **More fractional digits than the intermediate scale** (more than `18 - (p - s) - 1` for `p <= 16`, otherwise `38 - (p - s) - 1`). The parse rounds first, then the mode rounds again, so the result can be rounded twice. For example `"0.00449999999999"` to `DecimalDtype(10, 3)` with `half_away_from_zero` gives `0.005` (the exact answer is `0.004`), because the parse first rounds it to `0.0045`.
3. **Separator normalisation is lenient.** Removing `_` means `"1__0"` and `"_1"` convert to `10` and `1`.

### Conform

`conform()` verifies a declared decimal field and never converts it. An actual column that is exactly that decimal passes unchanged under every `data_type` mode. Any other actual type (text, float, a different precision or scale) follows the policy: `evolve` keeps the actual column, `freeze` raises `SchemaDriftError`, and `coerce`/`discard_value`/`discard_row` raise `DecimalConversionRequiredError`, which names the explicit `.cast(DecimalDtype(...), rounding=...)` to use. A missing declared decimal column under `null_fill` becomes a typed `Decimal(p, s)` null. Conforming by converting is tracked as backlog item 280.

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
