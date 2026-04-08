# Scalar Aggregate Batch — Design

**Date:** 2026-04-08
**Status:** Design / approved for planning
**Scope:** Wire the 13 aggregate expression functions whose protocol methods and backend implementations already exist but are unreachable from the public API, add scalar-terminal sugar on `Relation` for the 8 deterministic unary reducers, and codify two recurring API patterns as principles.

## Motivation

Today's `count_rows()` / `item()` work landed a single aggregate (`count` / `count_records`) through the full six-layer wiring matrix and exposed `SubstraitScalarAggregateAPIBuilder` as the real (not stub) instance-method surface for `col("x").<agg>()`. That work revealed two facts that shape this spec:

1. **12 arithmetic aggregates and 1 generic aggregate (`any_value`) already have complete backend implementations.** The files `expsys_{pl,nw,ib}_aggregate_arithmetic.py` contain live method bodies for `sum`, `sum0`, `avg`, `min`, `max`, `product`, `std_dev`, `variance`, `corr`, `mode`, `median`, `quantile`. The `aggregate_generic` backends implement `any_value`. None of them are reachable from the public API because layers 4–6 (function mapping, api-builder protocol, api-builder class) are missing. This is a **wiring-only** gap, not a design gap.

2. **The scalar-terminal composition pattern is reusable.** `Relation.count_rows()` is a 3-line composition: wrap `self._node` in `AggregateRelNode(keys=[], measures=[...])`, compile, extract via `.item(...)`. Any deterministic unary aggregate can become a `Relation.<agg>(col) -> Python scalar` terminal the same way. No per-backend dispatch; all backend variance stays inside the aggregate expression implementations that were already cross-backend-tested.

Both observations are pattern-level. The batch closes the concrete gap *and* writes the patterns down as principles so future contributors inherit the discipline rather than rediscover it.

## What already exists

| Layer | Generic (`any_value`) | Arithmetic (12 methods) |
|---|---|---|
| ENUM `FKEY_SUBSTRAIT_SCALAR_AGGREGATE` | ✓ (`ANY_VALUE`) | ✓ (`SUM`, `SUM0`, `AVG`, `MIN`, `MAX`, `PRODUCT`, `STD_DEV`, `VARIANCE`, `CORR`, `MODE`, `MEDIAN`, `QUANTILE`) |
| Protocol (expression system) | ✓ `prtcl_expsys_aggregate_generic.py` | ✓ `prtcl_expsys_aggregate_arithmetic.py` (12 methods) |
| Backend — Polars | ✓ `expsys_pl_aggregate_generic.py` | ✓ `expsys_pl_aggregate_arithmetic.py` (all 12) |
| Backend — Narwhals | ✓ | ✓ (all 12) |
| Backend — Ibis | ✓ | ✓ (all 12) |
| **Function mapping (`SCALAR_AGGREGATE_FUNCTIONS`)** | **✗** | **✗** |
| **api_builder protocol** | **✗** | **✗** (today's file only declares `count`) |
| **api_builder class** | **✗** | **✗** |

The only missing pieces are layers 4, 5, 6. No protocol changes, no backend changes, no enum additions.

## Design

### Part A — Expression-layer wiring (13 functions)

**Fluent single-arg reducers on `col("x").<name>()` (9 methods).** These become instance methods on `SubstraitScalarAggregateAPIBuilder`:

| Method | Substrait name | Enum | Options |
|---|---|---|---|
| `any_value` | `any_value` | `ANY_VALUE` | `ignore_nulls` |
| `sum` | `sum` | `SUM` | `overflow` |
| `avg` | `avg` | `AVG` | `overflow` |
| `min` | `min` | `MIN` | — |
| `max` | `max` | `MAX` | — |
| `product` | `product` | `PRODUCT` | `overflow` |
| `std_dev` | `std_dev` | `STD_DEV` | `rounding`, `distribution` |
| `variance` | `variance` | `VARIANCE` | `rounding`, `distribution` |
| `mode` | `mode` | `MODE` | — |

Each method builds a `ScalarFunctionNode(function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.<KEY>, arguments=[self._node], options={...})` and wraps via the same `self._build(node)` pattern today's `count` uses.

**Free-function multi-arg aggregates in `entrypoints.py` (3 functions).** These cannot be fluent because no single argument is the natural receiver:

| Free function | Signature | Enum | Options |
|---|---|---|---|
| `ma.corr(x, y)` | `(x, y, *, rounding=None)` | `CORR` | `rounding` |
| `ma.median(precision, x)` | `(precision, x, *, rounding=None)` | `MEDIAN` | `rounding` |
| `ma.quantile(boundaries, precision, n, distribution)` | `(boundaries, precision, n, distribution, *, rounding=None)` | `QUANTILE` | `rounding` |

Each lives in `entrypoints.py` in a new `# Aggregates` section, is re-exported from `mountainash.expressions/__init__.py` and `mountainash/__init__.py`.

**Deferred from this batch:**

- `sum0` — faithful to Substrait but rare in practice; users can `coalesce(col.sum(), lit(0))`. Add when a real consumer asks.
- `first_value` / `last_value` — missing backend impls *and* require ordering propagation through `AggregateRelNode` (Substrait expresses via `sorts` on the aggregate invocation; mountainash's aggregate pipeline doesn't currently thread this through). Separate spec.

**Function mapping.** Append 12 new `ExpressionFunctionDef` entries to `SCALAR_AGGREGATE_FUNCTIONS` in `definitions.py` — one per new enum key. `corr`/`median`/`quantile` take multi-arg signatures; the existing function-mapping machinery already handles multi-arg via `protocol_method=...` (see `if_then_else` in `CONDITIONAL_FUNCTIONS` as a reference).

**API-builder protocol.** Extend `prtcl_api_bldr_scalar_aggregate.py` with the 9 fluent-method signatures. Create `prtcl_api_bldr_scalar_aggregate_arithmetic.py` if the existing file is scoped to generic; otherwise keep them in one protocol for discoverability.

### Part B — `Relation` scalar-terminal sugar (8 methods + 1 alias)

All 8 deterministic unary reducers get a `Relation.<name>(col) -> Python scalar` method, each implemented as a 3-line composition following `count_rows()`:

```python
def sum(self, col: str) -> Any:
    import mountainash as ma
    from mountainash.relations.core.relation_nodes import AggregateRelNode
    aggregated = Relation(
        AggregateRelNode(
            input=self._node,
            keys=[],
            measures=[ma.col(col).sum().alias("__value__")],
        )
    )
    return aggregated.item("__value__")
```

**Methods (8):** `sum`, `avg`, `min`, `max`, `product`, `std_dev`, `variance`, `any_value`.

**Alias (1):** `Relation.mean(col)` → `self.avg(col)`, living in the extension-builder layer per `c.api-design/short-aliases.md`. This is the only divergence from Substrait naming in the batch; it's isolated to one method on one class and explicitly documented as an alias.

**Skipped from the Relation surface:**

- `mode` — returns a *set* in general (multiple modes possible); tie-breaking diverges across backends; not a true scalar. Keep the expression-layer fluent method (`col("x").mode()`), skip the Relation terminal.
- `corr`, `median`, `quantile` — multi-arg; if a future user wants `Relation.quantile(...)` it can be added, but the free-function form already lets them write `relation(df).select(ma.quantile(...).alias("q")).item("q")` in one line. YAGNI.

**Return type:** `Any`. Individual cells carry native Python types via the existing `item()` path (Polars `Series.item()` handles datetime/decimal/etc. coercion). Documenting a precise type per method is overreach — users know whether their column is numeric.

**Empty-relation semantics:** identical to `item()` — `IndexError` if the aggregated result is empty. In practice `AggregateRelNode(keys=[])` always produces one row (even from an empty input, the aggregate returns null/zero/etc. per the backend), so this shouldn't fire; it's the honest fallback.

### Part C — Principle updates (three new/updated docs)

#### New principle: `c.api-design/scalar-terminal-composition.md` (ADOPTED)

Codifies the `count_rows()` → this-batch pattern as the canonical shape for scalar terminals on `Relation`:

1. **Rule.** A scalar terminal on `Relation` is a thin composition over an aggregate expression function — never per-backend dispatch. The method wraps `self._node` in `AggregateRelNode(input=..., keys=[], measures=[<agg>(col).alias("__tmp__")])`, compiles through the existing visitor pipeline, and extracts the single cell via `.item("__tmp__")`.
2. **Why.** Backend variance is a solved problem at the *expression* layer (the aggregate protocol is cross-backend tested). Pushing backend dispatch into `Relation` methods duplicates that work, breaks the "relations compose; backends live in expression systems" separation, and loses lazy evaluation on backends that support it.
3. **Inclusion criteria.** A function qualifies for a Relation scalar terminal if and only if it is (a) deterministic, (b) scalar-output, (c) unary (one column argument). `count_rows` is nullary and therefore uses the `count_records` 0-arg aggregate. `mode` fails (b). `first_value` fails (c)-ish (it needs ordering).
4. **Naming.** Match the Substrait expression-layer name character-for-character. Short aliases (e.g. `mean` → `avg`) go via `c.api-design/short-aliases.md` and live in the extension-builder layer, applied identically to both the expression and Relation surfaces.
5. **Out of scope for terminals.** Multi-arg aggregates (`corr`, `median`, `quantile`) stay in the expression-layer free-function surface. Users needing them as Relation scalars write `relation(df).select(ma.quantile(...).alias("q")).item("q")` — two lines, explicit, not a pattern that warrants a new method per aggregate.

#### New principle: `c.api-design/free-function-entrypoints.md` (ADOPTED)

Codifies the existing but undocumented `entrypoints.py` convention.

**Definition.** A free function is a top-level callable in `mountainash` that produces a `BaseExpressionAPI` (or a DSL builder, e.g. `when`) without a preceding `col(...)` context. Canonical location: `src/mountainash/expressions/core/expression_api/entrypoints.py`. Re-exported from `mountainash.expressions/__init__.py` and `mountainash/__init__.py` via the established pattern.

**When to use a free function (in priority order):**

1. **No natural receiver.** `col`, `lit`, `native`, `count_records`, `t_col`. There is no "subject" column — the function creates one.
2. **Multi-arg combinators with no primary argument.** `coalesce`, `greatest`, `least`, and this batch's `corr`, `median`, `quantile`. All arguments are peers; making one the receiver would be arbitrary.
3. **DSL entry points.** `when(cond).then(...).otherwise(...)`. The free function begins a fluent chain that doesn't fit the column-method shape.
4. **Backend escape hatch.** `native(...)` for backend-specific expressions.

**When a free function is wrong.** Any unary transformation with a natural column receiver. `ma.str_lower(col("x"))` would be wrong; `col("x").str.lower()` is idiomatic. The test: *does one argument dominate the operation?* Yes → fluent. No → free.

**Both forms together.** Allowed, with a clear rule: fluent is canonical, free function is sugar and delegates to the fluent form (or vice versa). The current batch does *not* do this — unary reducers have a single canonical fluent form — but the principle permits it for future cases that warrant it (e.g. `ma.sum("x")` as a Polars-style shortcut, if demand appears).

**Naming consistency.** Free functions match their fluent counterpart's name character-for-character when both exist. No renames at the free-function layer. Short aliases happen once, in the extension-builder layer, and propagate.

**File organisation.** `entrypoints.py` is organised by section comments in priority order: `# Column and literal`, `# Combinators`, `# Control flow`, `# Aggregates`, `# Native / escape hatches`, `# Extension`. New entrypoints go in the appropriate section, not in topic-specific files.

**Future work flagged in the principle itself (non-committing):**

- Audit existing free functions against this principle. Likely all pass.
- Candidate additions when backend support lands: `sum0`, `first_value(order_by=...)`, `last_value(order_by=...)`, `nth_value(n, order_by=...)`.
- `ma.window(...)` as a possible DSL entry to window functions — currently only buildable via `.over(...)` on a column.

#### Update: `a.architecture/wiring-matrix.md`

The Substrait Scalar Aggregate section gains 12 newly-wired arithmetic methods plus `any_value`. Summary row updates: Substrait Scalar Aggregate moves from 2/9 wired to 15/? (where the denominator grows to include `corr`, `median`, `quantile`, `product`, `std_dev`, `variance`, and still-aspirational `sum0`, `first_value`, `last_value`).

#### Update: `f.extension-model/adding-operations.md`

Add a new subsection **"Wiring-only additions"** describing the *bottom-up* path: protocols and backends already exist; only layers 4, 5, 6 (function mapping, api-builder protocol, api-builder class) need work. Today's `count` work and this batch are both examples. Six-layer audits (like Task 1 of the count plan) are the recommended first step for this flow.

#### Update: `h.backlog/polars-alignment-deferred.md`

Strike through `sum`, `avg`, `min`, `max`, `mean` in the Out-of-Scope Aggregation row, matching how `count` was struck through today. Note the closing batch.

#### Update: `CLAUDE.md`

Principles table in `mountainash-expressions/CLAUDE.md` gains two new rows in the `c. API Design` section:

- `scalar-terminal-composition.md` — ADOPTED — Scalar terminals on `Relation` are thin compositions over aggregate expression functions; no per-backend dispatch
- `free-function-entrypoints.md` — ADOPTED — `entrypoints.py` conventions: when to use free functions vs fluent methods

## Risks

**Multi-arg function mapping.** `corr`/`median`/`quantile` are the first aggregate entries with >1 positional argument. Today's `SCALAR_AGGREGATE_FUNCTIONS` uses the same `ExpressionFunctionDef` schema as scalar-comparison multi-arg functions, so the machinery exists. **Mitigation:** verify against the existing multi-arg entry in `SCALAR_COMPARISON_FUNCTIONS` or `CONDITIONAL_FUNCTIONS` (`if_then_else` takes 3 args) before starting.

**`AggregateRelNode(keys=[])` across backends.** Today's `count_rows` work fixed this for all three backends (Polars/Narwhals use `select(measures)` when keys are empty; Ibis uses `table.aggregate(*measures)`). The 8 new Relation terminals reuse this exact path — no further backend fixes expected. **Mitigation:** cross-backend tests on each new terminal will catch regressions.

**`any_value` nondeterminism.** Different backends may return different representative values across runs. This is a documented Substrait semantic. **Mitigation:** test assertions check presence-in-set rather than a specific value; note the nondeterminism in the Relation method docstring.

**Protocol split — generic vs arithmetic.** `any_value` lives in `prtcl_expsys_aggregate_generic.py`; the 12 arithmetic methods live in `prtcl_expsys_aggregate_arithmetic.py`. The api-builder protocol may need to be split similarly, or keep a single `SubstraitScalarAggregateAPIBuilderProtocol` that references both expression-system protocols. **Decision for the plan:** keep a single api-builder protocol and api-builder class covering all aggregate methods — users don't care about the generic/arithmetic internal split, and the api-builder layer is about user-facing discoverability. The expression-protocol split stays as-is.

## Tests

Cross-backend parametrized tests in:

- `tests/expressions/test_aggregate_fluent_reducers.py` — 9 fluent methods × 3 backends, each tested through `relation(df).group_by(k).agg(col.<agg>().alias("v"))`.
- `tests/expressions/test_aggregate_free_functions.py` — `ma.corr`, `ma.median`, `ma.quantile` × 3 backends.
- `tests/relations/test_terminal_scalar_aggregates.py` — 8 Relation scalar terminals × 3 backends, plus the `mean` alias test.
- `tests/relations/test_terminal_scalar_aggregates_empty.py` — empty-relation behaviour for each of the 8 terminals.

Reuse today's `count_rows`/`item` test infrastructure where possible.

## Out of scope

- `sum0`, `first_value`, `last_value` — deferred with explicit notes.
- `Relation.mode(col)` — excluded from the scalar terminal surface; still exposed at the expression layer as `col("x").mode()`.
- `Relation.corr/median/quantile` — deferred; free-function expression surface is the shipped form.
- Any changes to backend impls or the underlying aggregate protocols.
- Promotion of `wiring-matrix.md` or `adding-operations.md` from ADOPTED to ENFORCED.

## Dependencies

- The aggregate foundation landed on `feature/relation-count-and-item` (today). This spec stacks on that branch once merged, or on `develop` after.
- Existing `SubstraitScalarAggregateAPIBuilder` (today's work — the file is now real, not a stub).
- Existing `AggregateRelNode(keys=[])` path in all three backends (today's fix).
- `ma.col("x").alias(...)` via the Name builder (today's work added `MountainAshNameAPIBuilder` to `_FLAT_NAMESPACES`).

No new external dependencies. No new internal protocols.
