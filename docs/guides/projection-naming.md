# Projection and aggregate output names

`Relation.select()`, `Relation.with_columns()` and `GroupedRelation.agg()` assign
portable names to Mountainash expressions whose single output can be established
from the AST. This also applies to DAG relations and raw Mountainash AST nodes.
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
This includes selector-shaped strings such as `select("*")` and `select("^n$")`;
ordinary column-name strings still denote one field.
They are not wrapped in a generated scalar alias. Where AST/input-schema facts
resolve an expansion, inference can report all names, including an empty list for
a zero-match expansion. Otherwise it raises an incomplete-schema error instead of
advertising `"*"` or a partial mapping. A selector or opaque expression in any
output-affecting operand, predicate or result branch can make the whole output
cardinality uncertain, even when another operand has a known name.

Computed expansions remain incomplete unless unchanged lowering guarantees their
names. For example, `ma.col("^n$").is_in([2])` retains native expansion lowering:
on Polars its output is named `literal`, so `.columns` raises rather than claiming
it replaces `n`. Composition does not remove this uncertainty. Use an ordinary
field reference for portable scalar naming. Proven zero-match computations still
have known-empty output.

Structured-field metadata and owned transport residue sometimes need complete
names to map join collisions (for example, right `x` to `x_right`). If complete
authoritative names are unavailable at the applicable planning/compilation phase,
the affected lineage operation fails explicitly rather than attaching metadata
under a guessed name or discarding it. Plain native passthrough can still execute
when no metadata naming obligation depends on those names.
Direct selectors and direct field aliases carry structured metadata only when
their source/output mapping is proven; zero-output aliases preserve existing
metadata in `with_columns`. Opaque projections and computed selectors with active
structured transport fail explicitly when their carriage cannot be established,
including in `select`. Materialize the logical values before applying such native
projections if needed.

## Grouped and global aggregation

Aggregate output order is grouping keys followed by measures. The same naming
rules apply at fluent construction and when compiling a direct `AggregateRelNode`:

```python
source = pl.DataFrame({"g": [0, 0, 1], "x": [3, 3, 8]})
grouped = ma.relation(source).group_by("g").agg(ma.col("x").sum().name.suffix("_sum"))
assert grouped.columns == ["g", "x_sum"]
assert sorted(grouped.to_dicts(), key=lambda row: row["g"]) == [
    {"g": 0, "x_sum": 6}, {"g": 1, "x_sum": 8},
]
assert ma.relation(source).group_by().agg(ma.col("x").sum()).to_dicts() == [{"x": 14}]
```

`col("x").alias("renamed").sum()` outputs `renamed`;
`(lit(1) + col("x")).sum()` outputs `literal`. Computed grouping keys retain
their resolved names instead of disappearing from `.columns`.

Keys and measures share one collision namespace. `group_by("x").agg(col("x").sum())`
and `agg(col("x").sum(), col("x").max())` now fail consistently; give each measure
a distinct alias. On Ibis, implicit native names such as `Sum(x)` or `First(x, ())`
are replaced by these AST names. To retain a historical output name, use it as an
explicit outer alias.

Key dtypes follow their source only for ordinary fields under name-only wrappers.
Renaming `g` to `x` keeps the type of `g`, not a same-named input `x`. Computed keys
and measures report `UNKNOWN`; explicitly typeless sources retain `UNCONSTRAINED`.
Naming does not add reducer support, change null/empty-input semantics, or alter
key-only DISTINCT routing.

Native and selector aggregates keep supported execution even when `.schema` or
`.columns` raises `IncompleteProjectionSchemaError`. A known zero-match selector
contributes no names; unknown cardinality is not an empty expansion. Aggregate
selectors require complete source-name evidence. A ref resolver's dtype mapping
or a resource's declared fields alone does not prove all input names. Scalar
names remain available over unresolved refs; selector introspection over those
refs is unavailable. Introspection does not fetch resources or compile native
expressions to discover names.

Inline resource declarations prove names only when schema conform is enabled
and its effective by-name contract rejects/discards extras and freezes/null-fills
missing fields. Open/evolve, non-conformed and referenced schemas remain
unavailable to this evidence walk. Indexed Python dictionaries are not column
mappings. Subset DISTINCT also supplies unavailable evidence: its existing Ibis
path drops non-key columns while Polars/Narwhals retain them. Keyless DISTINCT
preserves input names. These limits affect dependent selector introspection,
not scalar aggregate names or native DISTINCT execution.

`RelationDAG.to_package()` omits unavailable optional schema by default while
retaining the resource. `strict=True` rejects incomplete schema. If omission
would lose explicitly declared foreign keys, **both modes raise
`MissingResourceSchema`**, naming the resource and preservation requirement.
Duplicate names and other malformed-plan errors are never treated as absent
optional metadata. Fully named foreign keys and raw resource descriptors retain
their existing export behavior.

## Scope and compatibility

This correction covers relation projections and grouped/global aggregate naming,
including their schema, export and lineage consumers. Standalone
`expr.compile(source)` naming and selector support are unchanged.
Literal-only `select` row counts are unchanged and are **not** covered by a
cross-backend row-count parity claim. Backend reducer, casting and coalesce
capability limitations remain outside this naming correction.

The [unreleased changelog](../../CHANGELOG.md) records the compatibility effects:
Ibis generated-name additions can become replacements, membership now uses the
needle's name, duplicate resolved outputs fail, and incomplete schema/lineage
information is reported explicitly. No release version is assigned here.

The local null-to-zero status regression is a minimal Rules witness. Full Rules
Task 10 status/route-equivalence qualification is a separate post-delivery check
against the delivered Mountainash revision and consumer dependency version;
independent join and rounding blockers remain separately owned.
