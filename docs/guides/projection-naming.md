# Projection output names and migration

`Relation.select()` and `Relation.with_columns()` assign portable names to
Mountainash expressions whose single output can be established from the AST.
This also applies to DAG relations and accepted raw Mountainash expression nodes.
Naming is decided while building the plan, without compiling or executing it,
and does not mutate expressions that the caller reuses elsewhere.

## Replace a column or add one deliberately

`with_columns` replaces an existing column when an expression has the same output
name. An alias to a new name adds a column and retains the original:

```python
import mountainash as ma
import polars as pl

source = pl.DataFrame({"n": [None, 2, 4]})

# Replace n portably, including when source is an Ibis table:
filled = ma.relation(source).with_columns(ma.col("n").fill_null(0))
assert filled.to_dict() == {"n": [0, 2, 4]}

# Add a new column and retain the original:
added = ma.relation(source).with_columns(ma.col("n").fill_null(0).alias("filled_n"))
assert added.to_dict() == {"n": [None, 2, 4], "filled_n": [0, 2, 4]}

# Membership's intentional name correction now replaces n:
membership = ma.relation(source).with_columns(ma.col("n").is_in([2, 4]))
assert membership.columns == ["n"]

# Preserve a separate membership output deliberately:
separate = ma.relation(source).with_columns(ma.col("n").is_in([2, 4]).alias("is_member"))
assert separate.columns == ["n", "is_member"]
```

A subsequent filter or condition on `n` sees the replacement. To retain a
historical generated name, supply that exact name as an explicit outer alias.
An explicit `.alias("n")` also replaces `n`.

`select` follows expression order. `with_columns` keeps existing columns in their
original positions and appends genuinely new names in expression order. When all
output names are resolvable, `.columns` and `.schema` describe the complete output
names; this naming contract does not add dtype inference guarantees.

## How names are chosen

| Expression | Output name |
| --- | --- |
| `ma.col("n")`, `ma.col("n").fill_null(0)`, `ma.col("n") + 1` | `n` |
| `ma.col("n") + ma.col("m")` | `n` |
| `ma.lit(1)`, `ma.lit(1) + ma.col("n")` | `literal` |
| `ma.col("n").is_in([2, 4])` | `n` (the needle's name) |
| `ma.col("n").alias("z").fill_null(0)` | `z` |
| `ma.col("n").alias("z").name.suffix("_f")` | `z_f` |
| `ma.col("n").name.suffix("_f").alias("q")` | `q` |
| `ma.when(ma.col("n") > 0).then(ma.col("m")).otherwise(ma.col("n"))` | `m` (first `then` result) |
| `ma.col("n").cast("int64")`, `ma.col("n").sum().over("g")` | `n` |

Prefix, suffix, uppercase and lowercase name transformations act on the resolved
inner name. An outer alias chooses the final name. Casts and window wrapping
preserve their input expression's name; partition/order columns do not replace it.
Individual function keys have explicit naming rules, rather than a universal
"first argument" fallback.

An empty alias (`.alias("")`) is a valid AST name, including in schema inference
and duplicate detection. It is not an unresolved name. Materialization still has
existing backend identifier and egress limitations: DuckDB rejects zero-length
quoted identifiers, and some egress paths rename empty columns to names such as
`column_0`. Use a nonempty alias for portable materialized output.

### Duplicate outputs

Two supplied expressions with the same resolved name raise a `ValueError` during
projection building, on every backend. This includes inferred/inferred,
explicit/explicit and inferred/explicit collisions:

```python
try:
    ma.relation(source).with_columns(ma.col("n") + 1, ma.col("n").alias("n"))
except ValueError as error:
    assert "duplicate" in str(error)
else:
    raise AssertionError("duplicate output should be rejected")
```

One output replacing an input column is valid. Two supplied outputs competing for
that name are not. In particular, Narwhals-pandas no longer silently retains the
last expression. Give the outputs distinct aliases or use successive projections
when the second operation should consume the first result. Expansion collisions
are rejected when their names become available; opaque outputs retain native
validation where names cannot be determined before compilation.

### Operations requiring an alias

These operation-specific dispositions are intentional limitations of portable
implicit naming:

| Operation | Why an explicit output alias is required |
| --- | --- |
| `QUANTILE` | The existing boundaries/precision/n/distribution arguments do not establish a portable output name matching backend x/q signatures. |
| `PERCENT_RANK` | The receiver is discarded, there are no value arguments, and the current visitor does not inject an ordering column for this protocol. |
| `CUME_DIST` | The receiver is discarded and there are no value arguments from which to inherit a name. Window ordering controls rows, not the output name. |
| `NTILE` | The retained argument is the bucket count, not the receiver. |
| `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `RANK_AVERAGE`, `RANK_MAX` with absent or unusable first ordering information | These keys normally inherit the first ordering expression's name; missing or opaque ordering cannot establish that name. |

Use an outer `.alias("chosen_name")` on a supported single-output expression.
New or unclassified Mountainash operations also require an alias rather than
silently adopting a backend-generated name. An alias supplies naming intent; it
does not repair operation signatures, add backend support, or prove a selector
has one output. Internal `COLLECT_VALUES` is a membership collection encoder,
not a standalone projectable operation.

## Native expressions, selectors and complete schemas

Raw native expressions and `ma.native(...)` retain their execution passthrough.
Their implicit names are not portable. An explicit Mountainash alias chooses a
name **when the native expression actually produces one output**:

```python
native = ma.relation(source).select(ma.native(pl.col("n").fill_null(0)).alias("filled"))
assert native.to_dict() == {"filled": [0, 2, 4]}

# AST-only introspection cannot prove the native expression's output count.
try:
    native.columns
except ValueError as error:
    assert "incomplete output names/cardinality" in str(error)
else:
    raise AssertionError("opaque native schema should remain incomplete")
```

The same limitation applies to `.schema`. A successful execution or an explicit
alias does not turn opaque AST cardinality into proof of one output: a native
selector can produce zero or many columns. No native-tree inspection or implicit
compilation is performed to answer these schema requests. With Ibis,
`expr.compile(source)` can return a `Deferred`; resolve it against `source` before
passing it to `ma.native`, which accepts concrete Ibis expressions.

Existing wildcard and regex selectors keep their supported expansion behavior.
They are not wrapped in a generated scalar alias. Where AST/input-schema facts
resolve an expansion, inference can report all names, including an empty list for
a zero-match expansion. Otherwise it raises an incomplete-schema error instead of
advertising `"*"` or a partial mapping. A selector or opaque expression in any
output-affecting operand, predicate or result branch can make the whole output
cardinality uncertain, even when another operand has a known name.

Structured-field metadata and owned transport residue sometimes need complete
names to map join collisions (for example, right `x` to `x_right`). If complete
authoritative names are unavailable at the applicable planning/compilation phase,
the affected lineage operation fails explicitly rather than attaching metadata
under a guessed name or discarding it. Plain native passthrough can still execute
when no metadata naming obligation depends on those names.

## Scope and compatibility

This correction is limited to relation `select`/`with_columns` naming and their
schema/lineage consumers. Standalone `expr.compile(source)` naming, grouped
aggregation naming and aggregate schema policy retain their existing behavior,
including existing backend differences. Selector support is not expanded.
Literal-only `select` row counts are unchanged and are **not** covered by a
cross-backend row-count parity claim. Casting/coalesce capability defects are
also outside this naming correction.

The [unreleased changelog](../../CHANGELOG.md) records the compatibility effects:
Ibis generated-name additions can become replacements, membership now uses the
needle's name, duplicate resolved outputs fail, and incomplete schema/lineage
information is reported explicitly. No release version is assigned here.

The local null-to-zero status regression is a minimal Rules witness. Full Rules
Task 10 status/route-equivalence qualification is a separate post-delivery check
against the delivered Mountainash revision and consumer dependency version;
independent join and rounding blockers remain separately owned.
