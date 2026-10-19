# TypeSpec and conformance

A schema is a contract about shape. `TypeSpec` represents that contract, and `conform()` applies its casts, renames, null handling and missing-field policies. Portable declarations serialize to Frictionless descriptors; backend-native dtype objects are supported only in memory.

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

`TypeSpec` owns an insertion-ordered mapping from local field names to immutable, unnamed `FieldSpec` definitions. The mapping supplies names and order; the definitions are reusable across schemas, contracts and collection elements. Constructor input is copied, so later edits to caller-owned mappings do not mutate field declarations. `TypeSpec.from_simple_dict` remains a concise adapter for simple schemas.

### Reusable fields and composition

```python
from mountainash.datacontracts import BaseDataContract
from mountainash.typespec import FieldSpec, TypeSpec, UniversalType

Quantity = FieldSpec(type=UniversalType.INTEGER, minimum=0, description="Unit count")
BulkQuantity = Quantity.variant(minimum=10)  # independent declaration; Quantity unchanged

orders = TypeSpec(fields={"quantity": Quantity, "bulk": BulkQuantity})
shipments = TypeSpec(fields={"shipped_quantity": Quantity})  # same definition, new local name

Order = FieldSpec(fields={"quantity": Quantity, "reference": FieldSpec(type=UniversalType.STRING)})
Orders = FieldSpec(element=Order)
Quantities = FieldSpec(element=Quantity)
ThreeQuantities = FieldSpec(element=Quantity, dimensions=(3,))

class OrderContract(BaseDataContract):
    quantity = Quantity.variant(severity="blocking")
```

`FieldSpec` has no name. Names come from TypeSpec mapping keys, contract member names, or the source's local context; they are not copied into shared definitions. `fields` is an ordered mapping of named child declarations. `element` is one complete unnamed declaration, including for scalar elements. Container constraints belong to the container; element constraints belong to each element. Omitted dimensions means variable-length list; `dimensions` selects a fixed array. Composed object/list/array dtypes are projections of declarations, not a separately maintained nested dtype tree. Bare structured dtype values remain available when only a type is needed.

Definitions and their nested metadata are immutable and owned. Reuse a library definition directly, or derive a distinct use with `.variant(...)`; variants retain unspecified properties, can relax requirements, and never mutate their source. Concise constraints (`minimum`, `maximum`, `exclusive_minimum`, `enum`, `pattern`, and supported contract checks such as `eq` or `str_contains`) use the shared `FieldConstraints` representation. An existing immutable constraints object can be shared with `constraints=`.

`rename_from` is a use's source binding: the field's local mapping/member name remains the output name. Without it, local name is the source name. Contract severity is specialized on the shared declaration via `.variant(severity=...)`; conform and casts do not interpret severity. Direct contract field checks remain available on the definition (`definition.to_checks(local_name)`).

### Precise dtype declarations

Use a canonical dtype when a broad Frictionless type such as `integer` is insufficient:

```python
short = FieldSpec(dtype=ma.MountainashDtype.I8)
explicit = FieldSpec(type=UniversalType.INTEGER, dtype=ma.MountainashDtype.I8)
spec = TypeSpec(fields={"id": short})
```

Both forms declare an 8-bit signed integer. Broad-only declarations keep their existing behavior. An incompatible pair, such as `STRING` with `I8`, raises `InvalidDtypeDeclaration`.

Canonical enums persist as a field extension:

```json
{"name": "id", "type": "integer", "x-mountainash": {
  "dtype": {"kind": "canonical", "name": "i8"}
}}
```

Decimal declarations retain their `kind: "decimal"` precision/scale encoding. Dtype-only `JSON` and native `DURATION` retain broad `ANY` semantics: JSON scalars and arrays do not become GeoJSON, and native durations do not become lexical XSD duration strings. Explicit semantic declarations still apply their parsing rules.

### Parameterized targets

The existing descriptors in `mountainash.core.dtypes` can be used in `ma.lit`,
both cast builders, and `FieldSpec.dtype`: `TimestampDtype`, `TimeDtype`,
`DurationDtype`, `ListDtype`, `ArrayDtype`, `StructDtype`, and `DecimalDtype`.
Use `fields=`/`element=` when complete child declarations are needed; use a bare
structured dtype when only type shape is required.

```python
from mountainash.core.dtypes import TimestampDtype

at = TimestampDtype(precision=6, timezone_aware=True, timezone=None)
schema = TypeSpec(fields={"at": FieldSpec(dtype=at)})
padding = ma.lit(None, dtype=at)
converted = ma.col("at").cast(at)
```

An aware target with `timezone=None` uses UTC where the backend requires a name.
Explicit timezone names remain authoritative. `None` and `SchemaTypeStatus.UNKNOWN`
are not interchangeable:

- In source metadata, UNKNOWN means missing knowledge.
- In a target, UNKNOWN leaves that parameter unspecified. Compatible source
  parameters are retained where available; native construction supplies defaults
  only when needed. Those defaults do not change the authored descriptor.
- A whole UNKNOWN cast target leaves the operand unchanged; a whole UNKNOWN
  literal target uses ordinary inference. UNCONSTRAINED remains a schema status,
  not a native construction target.

Portable descriptor structure persists under `x-mountainash.fields`,
`x-mountainash.element`, and (for fixed arrays) `x-mountainash.dimensions`;
exact leaf dtypes retain `x-mountainash.dtype`. Native refinements remain
in-memory only. Standard lexical type, `itemType`, and `delimiter` remain
distinct from JSON arrays and element declarations.

### Explicit persisted-descriptor migration

The ordinary typed reader does not interpret retired `object_fields` or
`item_object_fields`; it reports a typed descriptor error naming the migration
function. Migrate persisted schema mappings explicitly before typed access:

```python
from mountainash.typespec.frictionless import migrate_nested_field_declarations

migrated_schema = migrate_nested_field_declarations(old_schema_mapping)
spec = TypeSpec.from_frictionless(migrated_schema)
```

The function is a pure mapping-to-mapping conversion: it returns a fresh mapping,
does not mutate input, read/write files, follow references, resolve packages or
run backends. Call it at the existing storage boundary, then pass the migrated
mapping through the ordinary typed reader. Raw `DataPackage` storage and
preserve/canonical descriptor writing do not automatically migrate or normalize
raw documents. Existing dtype-only descriptors remain readable without this
migration. This cutover does not change cross-field rules or make descriptor
decoding evidence that dataset constraints were validated.

Native type construction does not prove execution support. Item 340 is still in
qualification; the following boundaries are not a blanket backend support claim.

| Route or operation | Exercised behavior / remaining boundary |
|---|---|
| Scalar-only projection | Typed and untyped scalar expressions preserve input cardinality, including empty input. Aggregate projections retain their existing behavior. Public Polars, pandas and DuckDB smoke exercised zero and three input rows. |
| Logical typed containers | Declared Array width is enforced at logical egress; native Polars and pandas output retain the fixed width and child dtype. Structured conversion failures participate in discard-value/discard-row policies. Bare ARRAY/OBJECT declarations retain their existing object-carrier behavior. |
| DuckDB aware timestamps | TIMESTAMPTZ stores microseconds even when Ibis advertises ns. Sub-microsecond loss is explicitly accepted for now (345); native execution remains available without a new refusal. Naive TIMESTAMP_NS is a distinct, working representation. |
| Time precision | Polars and Narwhals Time represent ns only; UNKNOWN uses native behavior. Ibis Time has no precision parameter, so an explicitly requested precision is not representable through that logical dtype. Python carriers likewise cannot certify parameters absent from their type representation. |
| Existing native failures | SQLite Time export (131), SQLite fractional timestamp casts (298), DuckDB interval export (314), pandas nested-null literal broadcast (342), DuckDB fixed-array CASE (343), and Ibis-Polars null fixed-array export (344) remain separately attributed. The last case is isolated from the test process because it can crash native Arrow export. |
| Empty nested literals | Narwhals Arrow List/Array broadcast fails on empty input (346); Narwhals pandas non-null List/Array/Struct construction has a separate empty-index failure (348). Nonempty controls work. |
| Additional Narwhals providers | Arrow and DuckDB public terminals exercised partial Time (including nested Time), List, fixed Array, Struct and Decimal with null/non-null and empty/populated inputs. Arrow empty non-null List/Array remains item346. Arrow fixed-duration literals work; DuckDB exports calendar intervals that Polars cannot import (349), with a native panic on empty import. No interval-as-Struct fallback is enabled. |
| Permissive temporal parsing | Native ISO parsing retains ns in typed logical output. Non-ISO `format="any"` fallback uses the existing dateutil/Python datetime policy, which loses sub-microsecond digits and fractional-minute precision (350). Exact expected values remain unqualified; no precision-reconstruction workaround or waiver is provided. |
| Native structured child conversions | Narwhals Struct conversion uses its native `nw.struct` constructor; native list-element conversion remains unsupported. Ibis-DuckDB supports element-bound List-of-Struct conversion, but deferred outer-column references are explicitly unsupported. Ibis-Polars lacks native `ArrayMap` translation. These boundaries do not trigger emulation or backend switching. |
| Logical structured conversion | Decoded cells use direct Arrow casts and existing Python temporal parsing. Opaque native refinements and conversion metadata requiring per-cell backend execution are explicitly unsupported. No one-row Polars/Pandas execution or alternate Polars parser is used to emulate support. Native structured conform retains the selected backend's supported conversions. |
| Additional SQL dialects | Literal and both-cast rendering was exercised through MySQL, SingleStoreDB, Exasol and Postgres compilers, with explicit native container limitations. Physical execution remains unverified without configured services. Exasol timestamp literals visibly lose fractional digits in native compiler output (347). |

No backend-switching workaround or silent widening is provided. In particular,
an advertised timestamp unit is not evidence that its fractional value survived
native storage, parsing or export.

### Native overrides

`backend_type` takes precedence over `dtype`, including decimal declarations:

```python
import polars as pl

integer = FieldSpec(dtype=ma.MountainashDtype.I8, backend_type="Int64")
timestamp = FieldSpec(backend_type=pl.Datetime("ns", "UTC"))
schema = TypeSpec(fields={"id": integer, "at": timestamp})
```

The first field produces Int64 on Polars and emits a `UserWarning` because its canonical declaration is I8. Overrides also warn when equivalence cannot be verified, including parameterized temporal and semantic carriers. Proven equivalent representations do not warn. Invalid strings and objects belonging to a different target raise; they do not fall back to the canonical declaration.

Native strings remain serializable and are interpreted by the selected backend. Native objects retain their parameters in owned conform/validation snapshots but cannot be serialized, including when nested in an object or array-item declaration. Use a native string for a persisted override. Native fingerprints are runtime-local identities, with no stability guarantee across dependency versions.

Schema inspection uses native metadata first and retains detailed dtype parameters. SQLite reports its physical integer/real affinities even when a precise declaration produces narrower typed Polars/Arrow egress. AST fallback inference uses the effective target when known; an unresolved native override reports `UNKNOWN`. `evolve` retains the source's detailed identity; `freeze` compares native parameters when source evidence is available.

Bare canonical timestamp/duration casts retain the existing backend unit defaults. They do not promise nanosecond fidelity; backlog 334 tracks inherited sub-microsecond loss. Use an explicit native target with the required unit when that precision is needed.

### Downstream Structuremap adoption

Structuremap is a downstream consumer of the named-field and nested-type APIs. Its table-layout, preparation, cast/projection, codec, and reconstruction paths must migrate together to ordered name-to-definition mappings and recursive `fields`/`element` declarations; mutable renaming must instead construct a new immutable definition or use contextual names. This dependency remains part of the cutover: core documentation here does not imply a released Structuremap version or completed downstream qualification.


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

`conform()` selects the source's execution backend. Schema conversion is separate from runtime capability: Polars, pandas, Arrow and Ibis have schema converters, while Narwhals uses the existing runtime registry. Null-on-failure casts remain unsupported on Narwhals-routed identities and Ibis-SQLite; decimal limits are listed below. NumPy-backed pandas float/NaN to integer conversion still fails through Narwhals (backlog 252). This pre-existing limitation remains separately tracked and is not repaired by canonical declarations. Ibis also requires compatible types when `null_fill` coalesces values.

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
spec = TypeSpec(fields={"amount": FieldSpec(type=UniversalType.NUMBER, dtype=d)})

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

A **declaration** can use any precision up to 38. A **cast target** remains limited to precision 16 (`.cast(DecimalDtype(17, ...))` raises when the expression is built). That guard originated in a Polars 1.x native rounding-carry panic and the measured cost of wider DuckDB decimal parsing (17 s against 0.05 s per million rows). On Polars 2.0.0, native Decimal(4,3) rounding of `±9.995` to two places preserves `±10.000` as Decimal(5,3); this migration evidence does not qualify wider authored casts or remove the existing guard. Arrow-backed pandas retains fixed-width overflow errors for this native carry, while Ibis-Polars returns the fitting Decimal(4,2) result.

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

### Authored arithmetic

Working types, intermediate casts, final precision/scale and rounding belong to
the expression author. Mountainash does not widen Decimal arithmetic
automatically. An explicit Float64 working expression can be followed by one
final Decimal conversion; this does not change native Decimal arithmetic or
remove the conversion limits below.

```python
from decimal import Decimal as D
import polars as pl
import mountainash as ma

frame = pl.DataFrame(
    {"a": [D("1.235"), D("-2.345"), D("0"), None],
     "b": [D("2.50"), D("3.00"), D("4.00"), D("5.00")]},
    schema={"a": pl.Decimal(12, 3), "b": pl.Decimal(10, 2)},
)
source = ma.relation(frame)
a, b = ma.col("a").cast("fp64"), ma.col("b").cast("fp64")
result = source.select(
    (a * b + a).cast(ma.DecimalDtype(16, 5), rounding="half_to_even").alias("r")
).to_polars()
# Decimal(16,5): [4.32250, -9.38000, 0.00000, null]
```

For reductions, aggregate globally before the final conversion. A scalar
projection of a reducer is not a substitute for `group_by().agg()`.

```python
frame = pl.DataFrame(
    {"a": [D("1.001"), D("1.002"), None]},
    schema={"a": pl.Decimal(12, 3)},
)
working = ma.relation(frame).select(ma.col("a").cast("fp64").alias("a"))
reduced = working.group_by().agg(ma.col("a").mean().alias("r"))
result = reduced.select(
    ma.col("r").cast(ma.DecimalDtype(16, 6), rounding="half_to_even").alias("r")
).to_polars()
# Decimal(16,6): [1.001500]
```

#### Arithmetic support and regression owners

Observed with Polars 1.44.2, Ibis 12.0.0, DuckDB 1.5.6, Narwhals 2.27.1,
pandas 3.0.6 and PyArrow 26.0.0. These are tested versions, not dependency
pins. “Authored” below means **Decimal source → explicit Float64 working
operation → explicit final Decimal cast**. A passing refusal test is not
support for the calculation. Expected failures remain unqualified.

For all rows, Narwhals-Polars eager/lazy and pandas/Narwhals-pandas refuse the
authored route at final conversion (`NW-MATH-11`), even where native Decimal
arithmetic works. SQLite has no native fixed-precision Decimal admission and
refuses the final cast. Product refusal is tested before final conversion.

| Operation / inputs | Direct Decimal computation or extraction | Authored route | Test owner |
|---|---|---|---|
| Add/subtract/multiply/divide; signs, zero, null; different declarations | Polars eager/lazy and its Narwhals wrappers return Decimal(38,max scale). Arrow pandas promotes Decimal precision/scale. Ibis add/subtract/multiply extract its declared Decimal; division extracts Float64. | Exact final Decimal values/type on Polars eager/lazy and Ibis DuckDB/Polars for covered inputs. | `test_arithmetic.py::test_declared_decimal_binary` |
| Floor division/remainder/power | On Polars 2.0.0 with Narwhals 2.27.1 (and Ibis 12.0.0 for Ibis-Polars), eager/lazy Polars, Narwhals-Polars eager/lazy and Ibis-Polars execute Decimal floor division and remainder; native Decimal power/rpower remain unsupported. Arrow pandas lacks remainder; power is Float64. DuckDB floor division is Int64; signed remainder follows the dividend (`IB-MATH-05`); Ibis power extraction narrows to operand scale. | Floor division/remainder execute on Polars-backed identities and Ibis routes; DuckDB signed remainder still differs from Python. | `test_declared_decimal_binary` |
| Typed Decimal literals on either side; reversed subtraction/division/floor division/remainder/power; mixed integer/float columns and literals | On Polars 2.0.0 with Narwhals 2.27.1 (and Ibis 12.0.0 for Ibis-Polars), Polars eager/lazy, Narwhals-Polars eager/lazy and Ibis-Polars execute reversed floor division and remainder; native Decimal rpower remains unsupported. Ibis reverse-power extraction also rounds. Reversed division may return Float64 rather than Decimal. | Supported on the four cast-capable identities, subject to operation restrictions above. | `test_decimal_operand_arrangements` |
| Original equal-declaration multiplication witnesses; fractional chain | Polars retains operand scale; Ibis-DuckDB extraction can raise rescaling loss. Ibis-Polars also fails extraction when its declared capacity cannot hold the native product (author capacity, item 305). | Original products and `(a*b)+a` reach the exact authored final values on all four cast-capable identities. | `test_decimal_multiplication_fractional_witnesses`, `test_authored_decimal_chain` |
| Divide/floor-divide/remainder by zero | On Polars 2.0.0 with Narwhals 2.27.1 (and Ibis 12.0.0 for Ibis-Polars), Polars-backed Decimal division/floor-division/remainder raise `ComputeError` at computation; nonzero controls establish exact values. Other backend outcomes vary by operation: errors, null, or infinity. | Float computation can produce infinity/NaN; pandas Arrow floor-divide and SQLite division can produce null. Ibis floor-divide can fail converting infinity to Int64. | `test_decimal_zero_divisor_computation_boundary`; cast tests below |
| Negate/abs/sign/ceil/floor/round(2); signed fractional/zero/null and carry rounding | Native Decimal types remain except Narwhals sign (Int64); pandas/Narwhals negation may promote precision. Ibis round changes scale. DuckDB ties use half-away (244); Ibis-Polars ceil/floor fail Arrow extraction (309). `Decimal(4,3)` ±9.995 rounding to ±10.000 verifies capacity carry without pinning incidental precision. | Explicit Float64 then final Decimal works on the four cast-capable identities. Native `.round()` and final-cast rounding are separate operations. | `test_arithmetic_essentials.py::test_declared_decimal_unary`, `test_decimal_rounding_carries_integer_capacity`; `TestDeclaredDecimalMath::test_authored_float_math_then_decimal_cast` |
| sqrt, cbrt | sqrt returns Float64 on Polars/Narwhals; Ibis extracts Decimal. Polars-backed direct Decimal cbrt has no power kernel; Arrow pandas computes Float64; Ibis-DuckDB narrows its result (307). | Positive roots execute on the four cast-capable identities. Negative cbrt retains the existing `power(1/3)` NaN limitation; it is not qualified as a correct real cube root. | `test_math_extension_results.py::TestDeclaredDecimalMath::test_direct_decimal_roots`, `test_direct_decimal_math_method`, `test_authored_float_math_then_decimal_cast`; existing `TestCbrt::test_cbrt_negative` |
| exp, ln, log10, log2, log1p, log(base) | Polars/Narwhals native results are Float64. Ibis exp and fixed-base logs extract operand-scale Decimal, narrowing results (307); explicit `log(base)` is Float64. | Execute on all four cast-capable identities; tests distinguish log base and exact authored final values. | `test_direct_decimal_math_method`, `test_authored_float_math_then_decimal_cast` |
| sin/cos/tan/cot, asin/acos/atan, radians/degrees, atan2 | Polars Decimal trig kernels reject inputs; Narwhals methods are unsupported. Ibis-DuckDB trig/angular extraction narrows to Decimal (307), except cot/atan2 Float64. Ibis-Polars trig kernels reject Decimal; angular extraction narrows; atan2 is Float64. | Polars eager/lazy and both Ibis routes execute Float64 trig/angular cases with final Decimal casts. | `test_direct_decimal_math_method`, `test_authored_float_math_then_decimal_cast` |
| sinh/cosh/tanh/asinh/acosh/atanh | Polars Decimal kernels reject these; Narwhals and Ibis implementations explicitly refuse the methods. | Polars eager/lazy execute the authored route; Ibis method refusals remain, independently of final cast. | `test_direct_decimal_math_method`, `test_authored_float_math_then_decimal_cast` |
| factorial; bitwise_not/and/or/xor, shift_left/right/right_unsigned | Factorial is explicitly unsupported. Integer-only operations reject Decimal or have existing capability refusals; no implicit integer coercion is added. | Float64 does not make integer-only operations available; their computation refusals remain explicit. | `test_factorial_is_an_explicit_unsupported_operation`, `test_integer_only_operations_do_not_coerce_decimal` |
| pct_change(n=1,2), partition/order/null semantics | Polars and Arrow-pandas families retain native Decimal results; Ibis-DuckDB returns Float64. Narwhals diff(n>1) and Ibis-Polars windows remain unsupported. An enclosing `.over()` now reaches the composed lag. | Polars eager/lazy and Ibis-DuckDB execute the final-cast case; other identities retain cast/window refusals. | `test_decimal_pct_change_keeps_partition_and_order_semantics`, `test_authored_pct_change_then_decimal_cast`, `test_pct_change_window_does_not_bind_unrelated_lag_sibling` |
| Invalid sqrt/log/inverse-trig domains | Native kernels may raise, return NaN/infinity or null, or fail Ibis Decimal extraction. Negative and zero log inputs are tested separately so one error cannot mask the other. | Float computation and final conversion have separate assertions; no domain-normalization policy is introduced. | `test_direct_decimal_invalid_sqrt_domain`, `test_direct_decimal_invalid_log_domains`, `test_authored_float_inverse_trig_domain`, `test_invalid_sqrt_separates_float_domain_from_final_decimal_cast` |
| Global sum/min/max/mean; singleton, signed/zero/null, typed empty/all-null | Polars Decimal mean is Float64; Arrow pandas mean is Decimal; Ibis mean extraction narrows fractional results. Empty/all-null sum is zero on Polars/Narwhals and null on Ibis; min/max/mean are null. | Sum/min/max/mean yield authored Decimal(16,6) on Polars eager/lazy and both Ibis routes. | `test_aggregate_results.py::TestDeclaredDecimalAggregateArithmetic` |
| Global product; same input boundaries | Direct Polars product retains operand scale; fractional product need not be exact. All Ibis/Narwhals variants retain explicit `PRODUCT` refusal (239). | Polars eager/lazy yield the authored fractional product; other identities refuse, without substitute reducers. | `TestDeclaredDecimalAggregateArithmetic` |
| Three rounding modes, two scales, signed even/odd ties and non-ties, carry and overflow after arithmetic | Final-conversion contract, not a claim about native intermediate rounding. | Every rounding mode has a distinct expected result vector. Executed target precision/scale checked; capacity overflow raises under both failure modes. | `test_decimal_cast.py::test_arithmetic_then_final_cast_honors_rounding_mode`, `test_arithmetic_rounding_carry_and_overflow` |
| Arithmetic-generated infinity/NaN, small and high-scale exponent results | Computation output checked before conversion. Existing exponent-conversion limitations (287) remain. | `throw`/`null` options exercised separately. DuckDB's sub-last-place exponent result remains expected-failing, not certified correct. | `test_arithmetic_generated_nonfinite_reaches_final_cast`, `test_small_arithmetic_result_uses_existing_exponent_cast_behavior`, `test_high_scale_exponent_result_after_arithmetic` |

Computed public schema may report `UNKNOWN` (303). Tests check that any concrete
inferred type agrees with execution, and independently assert the final cast's
executed Decimal precision and scale. Existing direct-cast tests remain the
owners for invalid options, missing rounding, precision caps, plain-text
overflow and high-scale exponent parsing.

### Known limits

The conversion is one vectorised native expression with no per-row checks, so some edge cases follow the engine's own behaviour. They are documented rather than detected:

1. **`to_zero` on the Ibis backends (Ibis-DuckDB and Ibis-Polars).** DuckDB has no truncate-to-places, so `to_zero` rounds on a 64-bit decimal parse and steps back one unit when that rounded away from zero. The parse keeps `17 - p + s` fractional digits, so an input is exact when it has at most `17 - p` digits beyond the target scale `s` (`16` extra at `p = 1`, `5` at `p = 12`, `1` at `p = 16`). A value that already fits the target has no digits to discard, so it is never changed. Past the window the parse rounds first: at `DecimalDtype(16, 2)`, `"1.99999"` gives `2.00` instead of `1.99`. Polars cuts plain text after `s` fractional digits, so it is exact for plain text of any length; its parse of exponent text is exact while the value fits a 38-digit decimal. The other two modes have no such window.
2. **An exact tie written with an exponent takes the engine's own tie rule.** Mountainash resolves exact ties by reading plain decimal text, so for `"5e-11"` to `DecimalDtype(10, 10)` Polars and Ibis-Polars (half to even) give `0E-10` under `half_away_from_zero` (the exact answer is `1E-10`), and DuckDB (half away from zero) gives the wrong result under `half_to_even`. This affected 3 of 1,234 random exponent inputs. Write the value without an exponent when an exact tie matters.
3. **DuckDB rounds exponent text below the last place by its mantissa digit.** `"7e-11"` to `DecimalDtype(10, 3)` gives `0.001`, where the exact value rounds to `0.000`; `"4e-11"` gives `0.000`. The error is always exactly one unit in the last place and only turns a true zero into `±0.001`. It applies to a `Float64` too: a value below one unit of the target's last place (`7e-11` and `9.99e-05` at scale 3) is affected, and about half of floats below `1e-4` at scale 3 round up by one unit on DuckDB, none on Polars. The same float is exact at a scale where it is not below one unit (3 of 6,000 at scale 6). Exponent text at or above the last place is exact, as is the same value written without an exponent (`"0.00000000007"`).
4. **DuckDB cannot parse some valid exponent text at a large target scale.** With a target scale of 12 or more, DuckDB's own parse returns nothing for a valid in-range number whose mantissa and exponent need many digits (8% of random exponent inputs at scale 12, 26% at scale 16, none up to scale 10). Under `half_to_even` and `half_away_from_zero` the conversion raises, naming the value, under both `"throw"` and `"null"`; `to_zero` falls back to a smaller parse and is unaffected. Plain text at the same scale is unaffected.
5. **A number too large for the target raises, in both failure behaviours.** Whether text is a number is decided by its shape (digits, one point, an exponent), not by a float parse, so `"1e309"` and a 400-digit integer raise rather than becoming null. `nan`, `inf`, `infinity` and any other text are invalid: null under `"null"`, an error under `"throw"`.
6. **Separator normalisation is lenient.** Removing `_` means `"1__0"` and `"_1"` convert to `10` and `1`.

### Conform

Declare `FieldSpec.rounding` to let `conform()` convert a **top-level** field to its exact decimal type:

```python
spec = TypeSpec(fields={"amount": FieldSpec(
    type=UniversalType.NUMBER,
    dtype=ma.DecimalDtype(precision=5, scale=2),
    rounding="half_to_even",
)})
result = ma.relation({"amount": ["12.345", "bad", None]}).conform(
    spec, contract={"data_type": "discard_row"},
).to_polars()
# amount: [Decimal("12.34"), None], dtype Decimal(5, 2)
```

The instruction accepts the three cast modes above. There is no default rounding mode or
per-call override. When conversion is needed and the instruction is absent,
`DecimalConversionRequiredError` points to `FieldSpec.rounding` or the explicit `.cast(...)`
alternative. Unknown/non-string modes or rounding without a decimal target raise
`InvalidDtypeDeclaration`.

The Frictionless reader/writer persist the instruction alongside dtype, not inside it:

```json
{"name": "amount", "type": "number", "x-mountainash": {
  "dtype": {"kind": "decimal", "precision": 5, "scale": 2},
  "rounding": "half_to_even"
}}
```

Absent or null rounding reads as `None` and is omitted on write. Rounding is a conversion
instruction, not type identity: changing it alone does not create dtype drift.

For a mismatching source, `coerce` throws on invalid input, `discard_value` replaces it
with null, and `discard_row` removes failed non-null conversions. Source nulls and declared
missing sentinels are retained. Existing lexical missing-value, numeric-text and `null_fill`
instructions run before the native decimal cast. Overflow still raises under both discard
policies. Converted output, inferred schema and effective schema retain exact precision/scale.

A matching decimal column passes unchanged, **including nulls even when `null_fill` is set**.
`evolve` retains a mismatching source type and values; `freeze` raises `SchemaDriftError`.
Structural-only conform does not convert. A missing declared column under the
`missing_columns="null_fill"` policy becomes a typed decimal null. These paths need no rounding.

Conform reuses the existing cast, including its backend support and all limits above:
conversion targets allow precision up to 16, while an already matching decimal can have
precision up to 38. Nested field declarations can persist rounding, but nested conversion
is not supported by this operation.

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
