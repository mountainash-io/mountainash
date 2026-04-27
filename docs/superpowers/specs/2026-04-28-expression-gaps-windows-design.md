# Expression Gaps: Window Functions, Case Sensitivity, and Cumulative Operations

> **Date:** 2026-04-28
> **Status:** Approved
> **Backlog ref:** `h.backlog/expression-api-gaps-promptbase-pipeline.md` — Gaps 4, 11, 14, 16

## Motivation

Four expression gaps block common analytical patterns (ranking, sessionization, running totals) in mountainash. These were discovered during the PromptBase pipeline dogfooding. The gaps cluster into two groups:

1. **Quick win** — Gap 4: `case_sensitivity` option accepted by the API but ignored by backends
2. **Analytical windows** — Gaps 11, 14, 16: broken window ordering, missing `.diff()`, missing `cum_sum()`

Gap 11 (Polars `apply_window` discards `order_by`) is the linchpin — fixing it unblocks correct ranking, cumulative operations, and ordered window functions across the board.

## Design Principle: Polars API Surface, Substrait AST Internals

The public API mirrors Polars calling conventions. The internal AST stays Substrait-aligned. The API builder layer is the translation boundary.

**Canonical example — `rank()`:**

```
User writes (Polars-style):
    ma.col("speed").rank(method="dense", descending=True).over("type")

API builder produces (Substrait-aligned AST):
    WindowFunctionNode(
        function_key=SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
        arguments=[],
        window_spec=WindowSpec(
            partition_by=[FieldReferenceNode("type")],
            order_by=[SortField("speed", descending=True)],
        )
    )

Each backend compiles from the AST to native:
    Polars:   pl.col("speed").rank(method="dense", descending=True).over("type")
    Narwhals: nw.col("speed").rank(method="dense", descending=True).over("type")
    Ibis:     ibis.dense_rank().over(order_by=ibis.desc(t.speed), group_by=t.type)
```

This principle will be captured as a new principle document: `c.api-design/polars-api-substrait-ast.md`.

---

## Gap 4: Wire `case_sensitivity` Through Backends

### Current State

The API builder (`api_bldr_scalar_string.py:485`) correctly builds `options={"case_sensitivity": "CASE_INSENSITIVE"}` into the AST node. The visitor passes options to backends via `**options`. All three backends accept `case_sensitivity` as a parameter but **ignore it** — they always perform case-sensitive matching.

### Backend Research

| Backend | Native case-insensitive approach |
|---------|----------------------------------|
| **Polars** | No `case_sensitive` param on `str.contains()`. Use `(?i)` regex flag or `.str.to_lowercase()` |
| **Narwhals** | Same as Polars — `(?i)` regex flag |
| **Ibis** | `ilike("%substr%")` for LIKE patterns, or `.lower()` on both sides |

### Fix

Each backend reads the `case_sensitivity` option and adjusts behavior by **lowercasing both sides**. The `(?i)` regex flag approach was considered but rejected: prepending `(?i)` to a literal substring and switching to regex mode would break on inputs containing regex metacharacters (`.`, `*`, `[`, `|`, `foo|bar`, etc.), introducing false positives or errors. Lowercasing preserves literal semantics regardless of input content.

**All three backends** — `contains`, `starts_with`, `ends_with`:
- When `CASE_INSENSITIVE`: apply `.str.to_lowercase()` (Polars/Narwhals) or `.lower()` (Ibis) on both `input` and `substring`, then perform the original case-sensitive operation on the lowered values.
- When `CASE_SENSITIVE` (default): no change — existing behavior.

**Polars example:**
```python
def contains(self, input, /, substring, case_sensitivity=None):
    if case_sensitivity == "CASE_INSENSITIVE":
        return self._call_with_expr_support(
            lambda: input.str.to_lowercase().str.contains(
                substring.str.to_lowercase(), literal=True
            ),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            substring=substring,
        )
    return self._call_with_expr_support(
        lambda: input.str.contains(substring, literal=True),
        function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
        substring=substring,
    )
```

**When substring is a literal value** (not an expression): the lowercasing of the literal can happen once at compile time rather than per-row, but this is a backend optimization detail.

### Scope

Three methods (`contains`, `starts_with`, `ends_with`) × 3 backends = 9 method updates, each a conditional branch. The `regex_contains` / `regex_match` methods are excluded — users can add `(?i)` to their own regex patterns.

### Test Requirements

Tests must include regex metacharacter strings as needles (e.g., `"foo.bar"`, `"a|b"`, `"test[1]"`) to verify that literal semantics are preserved under case-insensitive mode.

---

## Gap 11: Fix Polars Window `apply_window` and Ranking Functions

### Bug A: `apply_window` Discards `order_by`

**File:** `expsys_pl_window_arithmetic.py:209-231`

**Current code:**
```python
def apply_window(self, expr, partition_by, order_by, lower_bound=None, upper_bound=None):
    if not partition_by:
        return expr
    return expr.over(partition_by)  # order_by, lower_bound, upper_bound all ignored
```

**Narwhals** (correct): passes `order_by` to `.over()` kwargs.
**Ibis** (correct): builds `ibis.window(order_by=..., group_by=...)`.

**Fix:** Wire `order_by` through to Polars' native `.over()`:

```python
def apply_window(self, expr, partition_by, order_by, lower_bound=None, upper_bound=None):
    if not partition_by and not order_by:
        return expr
    over_kwargs: dict[str, Any] = {}
    if order_by:
        over_kwargs["order_by"] = [col for col, _ in order_by]
        descending = [desc for _, desc in order_by]
        if any(descending):
            over_kwargs["descending"] = descending
    if partition_by:
        return expr.over(*partition_by, **over_kwargs)
    return expr.over(**over_kwargs)
```

**Frame bounds note:** Polars' `.over()` does not support `ROWS BETWEEN` frame specifications. Frame-bounded windows require different Polars approaches (`rolling_*`, `group_by_dynamic`). This is a pre-existing limitation across backends — document as a known divergence, do not attempt to solve here.

### Bug B: Ranking Functions Return Sequential Numbers

**File:** `expsys_pl_window_arithmetic.py:38-71`

**Current code:** `rank()`, `dense_rank()`, and `row_number()` all return `pl.int_range(1, pl.len() + 1)` — sequential numbering that ignores values entirely.

**Fix:** Use native `Expr.rank(method=..., descending=...)`:

| Substrait function key | Polars implementation |
|---|---|
| `ROW_NUMBER` | `order_by_col.rank(method="ordinal", descending=descending)` |
| `RANK` | `order_by_col.rank(method="min", descending=descending)` |
| `DENSE_RANK` | `order_by_col.rank(method="dense", descending=descending)` |
| `PERCENT_RANK` | `(order_by_col.rank(method="min", descending=descending) - 1) / (pl.len() - 1)` |

The `order_by` column **and** `descending` flag come from the WindowSpec, resolved by the visitor. Both must be passed to the backend's ranking method — window ordering (which rows are in scope) is a separate concern from rank direction (highest-first vs lowest-first), and the `descending` flag controls rank direction on the native `Expr.rank()` call, not on `apply_window`.

**Implementation detail:** Polars `rank()` is called on the column being ranked and produces the rank values directly — it doesn't need `.over()` for the ranking logic, only for partitioning. The backend's ranking methods need access to both the order_by column and descending flag from the WindowSpec.

**Approach:** The visitor passes `order_by` context (column + descending) to ranking function calls. The visitor already resolves WindowSpec `order_by` before calling `apply_window` — we extend `visit_window_function` to also pass `order_by` to the backend's ranking methods when the function key is a ranking function. The backend method receives `(order_by_col, descending)` and calls `order_by_col.rank(method=..., descending=descending)`. The `descending` flag is consumed by the ranking method and **removed** from the order_by list passed to `apply_window`, since `apply_window` only needs partition context for ranking functions.

**Protocol signature change for ranking functions:**
```python
def rank(self, *, order_by_col: ExpressionT, descending: bool = False) -> ExpressionT:
def dense_rank(self, *, order_by_col: ExpressionT, descending: bool = False) -> ExpressionT:
def row_number(self, *, order_by_col: ExpressionT, descending: bool = False) -> ExpressionT:
```

### Test Requirements

Tests must verify that ascending and descending ranks produce different outputs:
```python
# descending=False: [1, 3, 5] → ranks [1, 2, 3]
# descending=True:  [1, 3, 5] → ranks [3, 2, 1]
```

### New API: `rank()` Method

**User-facing API (Polars-style):**

```python
ma.col("speed").rank(method="dense", descending=True).over("type")
```

**API builder implementation:**
`rank()` on `BaseExpressionAPI` builds a `WindowFunctionNode` with:
- `function_key`: mapped from `method` parameter to Substrait enum
- `arguments`: `[]` (Substrait ranking functions take no args)
- `window_spec`: partially populated with `order_by=[SortField(current_column, descending=descending)]`

When `.over()` is called, it **merges** `partition_by` into the existing WindowSpec rather than replacing it. The current `.over()` code only populates WindowSpec when it's `None` — this needs adjustment to handle the merge case.

**Method-to-function-key mapping:**

| `method` param | Function key |
|---|---|
| `"average"` | `FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE` (extension — no Substrait equivalent) |
| `"min"` | `SUBSTRAIT_ARITHMETIC_WINDOW.RANK` |
| `"max"` | `FKEY_MOUNTAINASH_WINDOW.RANK_MAX` (extension) |
| `"dense"` | `SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK` |
| `"ordinal"` | `SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER` |

**Signature:**
```python
def rank(
    self,
    method: Literal["average", "min", "max", "dense", "ordinal"] = "average",
    *,
    descending: bool = False,
) -> BaseExpressionAPI:
```

---

## Gap 14: `.diff()` — Consecutive Row Difference

### User-Facing API (Polars-style)

```python
ma.col("datetime").diff(n=1).over("channel")
```

### AST Representation

New mountainash extension function key: `FKEY_MOUNTAINASH_SCALAR_ARITHMETIC.DIFF`

This is not a Substrait-standard function. While it could be decomposed to `col - lag(col, n)` using Substrait primitives, a dedicated key is preferred because:
- Polars and Narwhals have optimized native `.diff()` implementations
- The decomposition produces Duration types for datetime columns, which is Gap 15 territory
- Only the Ibis backend needs to decompose

### Backend Implementations

| Backend | Implementation |
|---------|---------------|
| **Polars** | `expr.diff(n=n)` — native |
| **Narwhals** | `expr.diff()` — native, single-step only |
| **Ibis** | `expr - expr.lag(offset=n)` — decomposed using existing LAG |

### Known Divergence

Narwhals `.diff()` accepts no parameters — only single-step differences. If `n > 1` is requested on a Narwhals backend, raise a clear error via `KNOWN_EXPR_LIMITATIONS` registry (per `e.cross-backend/arguments-vs-options.md`).

### Protocol Method

```python
def diff(self, x: ExpressionT, /, n: int = 1) -> ExpressionT:
    """Consecutive difference: value[i] - value[i-n].

    First n elements are null.
    """
```

`n` is universally literal (always an integer, never an expression) → must be an **option**, not an argument, per `e.cross-backend/arguments-vs-options.md`.

---

## Gap 16: `cum_sum()` — Cumulative Sum (and Family)

### User-Facing API (Polars-style)

```python
ma.col("sales").cum_sum().over("store", order_by="date")
ma.col("sales").cum_sum(reverse=True).over("store", order_by="date")
```

### AST Representation — Dedicated Window Function Key

The API exposes `cum_sum()` as a convenience method (Polars convention). Internally it builds a `WindowFunctionNode` — the same node type used by `rank()` — so the existing `.over()` merge path handles it without needing a separate `OverNode` merge codepath.

```
cum_sum()  →  WindowFunctionNode(
    function_key=FKEY_MOUNTAINASH_WINDOW.CUM_SUM,
    arguments=[self._node],
    window_spec=WindowSpec(
        lower_bound=UNBOUNDED_PRECEDING,
        upper_bound=CURRENT_ROW,
    )
)

cum_sum(reverse=True)  →  WindowFunctionNode(
    function_key=FKEY_MOUNTAINASH_WINDOW.CUM_SUM,
    arguments=[self._node],
    options={"reverse": True},
    window_spec=WindowSpec(
        lower_bound=CURRENT_ROW,
        upper_bound=UNBOUNDED_FOLLOWING,
    )
)
```

When `.over()` is called, it merges `partition_by` and `order_by` into the existing WindowSpec — the same merge mechanism as `rank()`, operating on the same `WindowFunctionNode` type.

**Why WindowFunctionNode, not OverNode:** The `.over()` merge semantics (described below) only handle `WindowFunctionNode`. Using `OverNode` would either double-wrap or fail to attach partition/order to the cumulative frame. Using `WindowFunctionNode` keeps a single, consistent merge path for all operations that pre-populate a partial WindowSpec (`rank()`, `cum_sum()`, `cum_max()`, etc.).

### Backend Compilation

Each backend can optimize the aggregate-with-cumulative-frame pattern:

| Backend | Optimization |
|---------|-------------|
| **Polars** | Detect cumulative frame → use native `Expr.cum_sum(reverse=...)` instead of `sum().over(rows_between)` |
| **Narwhals** | Detect cumulative frame → use native `Expr.cum_sum(reverse=...)` |
| **Ibis** | Use `Expr.cumsum(order_by=..., group_by=...)` or `sum().over(ibis.cumulative_window())` |

### Additional Cumulative Operations

Same pattern, low marginal cost — each is an API method that builds an aggregate + cumulative frame:

| Method | Aggregate | Polars native | Narwhals native | Ibis native |
|--------|-----------|---------------|-----------------|-------------|
| `cum_sum()` | SUM | `cum_sum()` | `cum_sum()` | `cumsum()` |
| `cum_max()` | MAX | `cum_max()` | `cum_max()` | `cummax()` |
| `cum_min()` | MIN | `cum_min()` | `cum_min()` | `cummin()` |
| `cum_count()` | COUNT | `cum_count()` | `cum_count()` | N/A — decompose |

### Protocol Methods

New mountainash extension window function keys and protocol methods:

```python
class FKEY_MOUNTAINASH_WINDOW(Enum):
    CUM_SUM = auto()
    CUM_MAX = auto()
    CUM_MIN = auto()
    CUM_COUNT = auto()
```

```python
def cum_sum(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
def cum_max(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
def cum_min(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
def cum_count(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
```

Each backend maps directly to its native cumulative method (Polars `cum_sum()`, Narwhals `cum_sum()`, Ibis `cumsum()`). The `reverse` option is passed as a node option and read by the backend.

### Test Requirements

Tests must verify that `cum_sum().over('store', order_by='date')` correctly applies both partition and ordering — i.e., the cumulative sum resets per partition and follows the specified order. Include a test where removing `order_by` produces different results to prove ordering is effective.

---

## `.over()` Merge Semantics

Both `rank()` and `cum_sum()` pre-populate a partial WindowSpec before `.over()` is called. The current `.over()` implementation (`api_base.py:297`) only sets WindowSpec when it's `None`. This needs to change:

**Current behavior:**
```python
if isinstance(inner_node, WindowFunctionNode) and inner_node.window_spec is None:
    # populate window_spec from .over() args
```

**New behavior:**
```python
if isinstance(inner_node, WindowFunctionNode):
    if inner_node.window_spec is None:
        # create new WindowSpec from .over() args
    else:
        # merge: add partition_by from .over() args into existing WindowSpec
        # preserve existing order_by (from rank()) and bounds (from cum_sum())
```

The merge rule: `.over()` adds `partition_by` and optionally `order_by`. If the existing WindowSpec already has `order_by` (from `rank()`), the `.over()` `order_by` is ignored — the rank column takes precedence. If the existing WindowSpec has no `order_by` (from `cum_sum()`), `.over(order_by=...)` populates it.

---

## Deliverables

| # | Item | Type | Files |
|---|------|------|-------|
| 1 | Case sensitivity wiring | Bug fix | 3 backend string files (Polars, Narwhals, Ibis) |
| 2 | Polars `apply_window` order_by | Bug fix | `expsys_pl_window_arithmetic.py` |
| 3 | Polars rank/dense_rank/row_number | Bug fix | `expsys_pl_window_arithmetic.py` |
| 4 | API `rank()` method | New API | `api_base.py` + 3 backend window files |
| 5 | `.over()` merge semantics | Enhancement | `api_base.py` |
| 6 | `.diff()` operation | New operation | Enum + protocol + API builder + 3 backends |
| 7 | `cum_sum()` family | New operation | Enum + protocol + API builder + 3 backends (WindowFunctionNode) |
| 8 | Principle doc | New principle | `c.api-design/polars-api-substrait-ast.md` |
| 9 | Known divergences | Documentation | `e.cross-backend/known-divergences.md` updates |
| 10 | Tests | Cross-backend | Parametrized tests for each operation |

## Testing Strategy

Per `g.development-practices/testing-philosophy.md`:

- **Cross-backend parametrized tests** for all new operations: Polars, Narwhals, Ibis
- **xfail** for known divergences (Narwhals `diff(n>1)`)
- Each test verifies logical equivalence across backends, not identical output types
- Window ordering tests must verify that `order_by` affects results (not just that it doesn't error)
- Ranking tests must verify gaps (RANK), no-gaps (DENSE_RANK), and ordinal uniqueness (ROW_NUMBER)

## Known Limitations (Not Addressed)

| Limitation | Reason |
|---|---|
| Polars `.over()` has no ROWS BETWEEN frame support | Polars architectural constraint; would require `rolling_*` or `group_by_dynamic` |
| Narwhals `diff()` has no `n` parameter | Narwhals upstream limitation; register in `KNOWN_EXPR_LIMITATIONS` |
| Duration type (Gap 15) | Separate design needed; `.diff()` on datetime produces Duration in Polars |
| `rank(method="average")` has no Substrait equivalent | Extension function key `RANK_AVERAGE`; Ibis doesn't support this method |
| Cumulative operations in Narwhals `.over()` only work on pandas/Polars backends | Narwhals upstream limitation |
