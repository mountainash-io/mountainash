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

A **declaration** can use any precision up to 38. A **cast target** is limited to precision 16 (`.cast(DecimalDtype(17, ...))` raises when the expression is built). Polars aborts the whole process (a Rust panic that `except Exception` does not catch) when its own `Decimal.round` carries out of a type's integer width, and a decimal parse wider than 18 digits costs DuckDB about 330 times more (17 s against 0.05 s per million rows). Casts to 17 or more digits are available once Polars fixes `Decimal.round`.

### How a conversion rounds

The value is rounded **once, from the text you wrote**, using the engine's own text-to-decimal cast. There is no preliminary rounding stage, so the result does not depend on the target precision: `"1.2451"` gives `1.25` at both `DecimalDtype(10, 2)` and `DecimalDtype(16, 2)`, and `"0.0045"` gives `0.004` or `0.005` according to the mode, however many digits follow.

- **`half_to_even` and `half_away_from_zero`:** the engine's cast does the rounding. Polars breaks an exact tie to even and DuckDB away from zero, so exact ties are resolved from the text instead, which makes every backend agree. This reads plain decimal text, so an exact tie **written with an exponent** (`"5e-11"` at scale 10) takes the engine's own tie rule (see the limits below).
- **`to_zero`:** truncates on the decimal, with no text reading, so exponent text is interpreted by the engine. Polars parses into a wide decimal and truncates natively. DuckDB cannot (see the limits below).

### Sources

- **Text** is trimmed and `_` separators are removed before parsing, on every backend, so `" 1_000.5 "` becomes `1000.5`. A leading `+` or `.` (`".5"` is `0.5`) and a trailing `.` parse; a lone `.` does not. This applies to decimal-target casts only, not to ordinary values.
- **Exponents** (`"1e2"`, `"1.5e-3"`) are not interpreted by mountainash: they go to the backend's own cast, which parses them exactly on Polars and Ibis-Polars. DuckDB has two documented limits for exponent text (below).
- **Floats** convert by their shortest displayed form, not their binary value: `2.675` with `half_to_even` at scale 2 gives `2.68`, and with `to_zero` gives `2.67`. Converting the exact binary value would give `2.67` for both and differ between engines. The text is produced by the engine, and a float below `1e-4` is written with an exponent on DuckDB (`9.99e-05`) but in plain digits on Polars, so such a float takes the exponent path, with its limits below, on DuckDB only. A native `Float64` column therefore reaches those limits without any text in the input.
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

The conversion is one vectorised native expression with no per-row checks, so some edge cases follow the engine's own behaviour. They are documented rather than detected:

1. **`to_zero` on the Ibis backends (Ibis-DuckDB and Ibis-Polars).** DuckDB has no truncate-to-places, so `to_zero` rounds on a 64-bit decimal parse and steps back one unit when that rounded away from zero. The parse keeps `17 - p + s` fractional digits, so an input is exact when it has at most `17 - p` digits beyond the target scale `s` (`16` extra at `p = 1`, `5` at `p = 12`, `1` at `p = 16`). A value that already fits the target has no digits to discard, so it is never changed. Past the window the parse rounds first: at `DecimalDtype(16, 2)`, `"1.99999"` gives `2.00` instead of `1.99`. Polars cuts plain text after `s` fractional digits, so it is exact for plain text of any length; its parse of exponent text is exact while the value fits a 38-digit decimal. The other two modes have no such window.
2. **An exact tie written with an exponent takes the engine's own tie rule.** Mountainash resolves exact ties by reading plain decimal text, so for `"5e-11"` to `DecimalDtype(10, 10)` Polars and Ibis-Polars (half to even) give `0E-10` under `half_away_from_zero` (the exact answer is `1E-10`), and DuckDB (half away from zero) gives the wrong result under `half_to_even`. This affected 3 of 1,234 random exponent inputs. Write the value without an exponent when an exact tie matters.
3. **DuckDB rounds exponent text below the last place by its mantissa digit.** `"7e-11"` to `DecimalDtype(10, 3)` gives `0.001`, where the exact value rounds to `0.000`; `"4e-11"` gives `0.000`. The error is always exactly one unit in the last place and only turns a true zero into `±0.001`. It applies to a `Float64` too: a value below one unit of the target's last place (`7e-11` and `9.99e-05` at scale 3) is affected, and about half of floats below `1e-4` at scale 3 round up by one unit on DuckDB, none on Polars. The same float is exact at a scale where it is not below one unit (3 of 6,000 at scale 6). Exponent text at or above the last place is exact, as is the same value written without an exponent (`"0.00000000007"`).
4. **DuckDB cannot parse some valid exponent text at a large target scale.** With a target scale of 12 or more, DuckDB's own parse returns nothing for a valid in-range number whose mantissa and exponent need many digits (8% of random exponent inputs at scale 12, 26% at scale 16, none up to scale 10). Under `half_to_even` and `half_away_from_zero` the conversion raises, naming the value, under both `"throw"` and `"null"`; `to_zero` falls back to a smaller parse and is unaffected. Plain text at the same scale is unaffected.
5. **A number too large for the target raises, in both failure behaviours.** Whether text is a number is decided by its shape (digits, one point, an exponent), not by a float parse, so `"1e309"` and a 400-digit integer raise rather than becoming null. `nan`, `inf`, `infinity` and any other text are invalid: null under `"null"`, an error under `"throw"`.
6. **Separator normalisation is lenient.** Removing `_` means `"1__0"` and `"_1"` convert to `10` and `1`.

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
