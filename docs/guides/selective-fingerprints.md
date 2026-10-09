# Selective relation fingerprints

`Relation.fingerprint(*, keys, columns, batch_size=5000)` checks every row in a
caller-selected scope and returns a small Polars DataFrame. Use it for practical,
non-adversarial drift detection against a pinned baseline.

```python
import mountainash as ma
import polars as pl

baseline = pl.DataFrame({"axis_a": [1, 1, 2], "axis_b": [10, 11, 10], "value": [7, 8, 9]})
current = baseline.with_columns(pl.when(pl.col("axis_b") == 11).then(88).otherwise(pl.col("value")).alias("value"))

# Full relation, explicit complete key and value selection.
full = ma.relation(baseline).fingerprint(keys=["axis_a", "axis_b"], columns=["value"])

# Both sides independently evaluate the same row predicate.
def selected(source):
    return ma.relation(source).filter(ma.col("axis_a") == 1).fingerprint(
        keys=["axis_a", "axis_b"], columns=["value"], batch_size=5000,
    )

before, after = selected(baseline), selected(current)
domain = ["kind", "column", "profile", "key_schema", "value_schema"]
if not before.select(domain).equals(after.select(domain)):
    raise ValueError("Incompatible fingerprint domains; align schemas/profiles first")
comparison = before.join(after, on=["kind", "column"], nulls_equal=True, suffix="_current")
changed = comparison.filter(
    (pl.col("row_count") != pl.col("row_count_current"))
    | (pl.col("fingerprint") != pl.col("fingerprint_current"))
)
assert changed["column"].to_list() == ["value"]
```

## Selection and interpretation

- `keys` and `columns` are nonempty ordered sequences of names. Bare strings,
  sets, repeated names within either sequence and missing names are errors.
  A key can also appear in `columns`. Derived values can be named before calling.
- Ordinary `.filter(...)` selects rows. All selected rows contribute, including
  duplicates; there is no sampling. Adding a selected value column does not alter
  the fingerprints of its siblings.
- Supply the **complete logical key**. Key uniqueness is not checked. With
  nonunique keys, per-column fingerprints can miss rearrangements between
  equal-key rows. Exact comparison and key-integrity validation are separate.
- A row entering/leaving the predicate changes membership. Narrow predicates to
  drill down, including to one complete key. The result does not enumerate edits.
- Consumers resolve roles/presets into names and own equivalent scopes, baseline
  versions, comparison, storage, caching, scheduling and deployment policy.

## Result and compatibility

One `keys` row is followed by one `column` row per requested value field, in order:

| Column | Meaning |
|---|---|
| `kind` | `keys` or `column` |
| `column` | Value name; null for keys |
| `row_count` | Exact selected count, UInt64 |
| `fingerprint` | Two summed UInt64 lanes as 32 lowercase hexadecimal digits |
| `profile` | `ma-fingerprint/polars-struct-sum64x2/v1;polars=<exact version>` |
| `key_schema` | JSON descriptor of ordered key names/types |
| `value_schema` | JSON descriptor of the value name/type; null for keys |

All fields except `row_count` are String. Typed empty scopes return zero counts
and zero digests with complete descriptors. Descriptors survive Parquet/JSON
serialization; no hidden frame metadata is required.

Compare only matching profiles and descriptors, with equivalent caller scopes.
After a runtime/profile upgrade, recalculate both sides from their pinned data;
recalculation does not create a new baseline version. Equality is probabilistic,
with no cryptographic or numerical collision guarantee. Counts and descriptors
must accompany the digest.

## Types

Supported: Boolean; signed/unsigned integers of 8–64 bits; Float32/64; String;
Binary; Date; Time; Datetime/Duration with declared unit; Decimal with concrete
precision/scale up to 38; recursive Lists and Structs of supported types.

Null, empty string and zero are distinct. Strings are exact. Signed floating zeros
are equal; all NaNs are equal within a type and distinct from null; infinities
remain distinct. Lists preserve order and multiplicity. Struct descriptors retain
field names, order and types. Temporal units/timezones and decimal precision/scale
must match. No implicit normalization is performed.

Object, categorical/enum, fixed arrays, Int128, unspecified Decimal and untyped
Null are rejected, including nested occurrences. Explicitly cast categories to
strings, arrays to lists, or typed nulls to their intended type before checking.
Only choose casts that preserve the intended logical data. Encoded logical
structured fields requiring a full logical snapshot are rejected; native typed
Polars/DuckDB lists and structs are supported.

## Execution and route limits

Qualified routes are native Polars and Ibis-DuckDB. Polars relation compilation
uses lazy plans and requires the public `sink_batches` API; runtimes missing it
raise `BackendCapabilityError`. PostgreSQL is explicitly rejected pending reader
cleanup fixes (backlog 265). Ibis-Polars, SQLite and Narwhals routes also reject;
there is no eager fallback.

Source filters/projection execute before transfer. Shared vectorized Polars
hashing consumes bounded batches, retaining fixed per-column aggregate state.
`batch_size` must be a positive integer, not Boolean; it affects ingestion, not
identity. Caller joins/sorts, upstream DAG materializations and database query
execution have their own memory costs. Already-eager input remains in memory.

Source residue checks run on each batch before hashing. Failure returns no
partial fingerprint. Readers and execution-owned dependencies are released;
borrowed connections and caller transactions retain their ownership.

For reproducible resource checks run `scripts/qualify_fingerprint.py` in fresh
processes with `--source polars|duckdb`, `--rows`, `--batch-size`,
`--columns narrow|wide`, `--slice full|group|small`, and `--output`.
Polars uses a lazy Parquet scan. Receipts include query plans, runtime versions,
timing and process high-water RSS including setup costs. `--profile-vectors`
checks the literal Polars 1.44.2 vectors and rejects other versions explicitly.
