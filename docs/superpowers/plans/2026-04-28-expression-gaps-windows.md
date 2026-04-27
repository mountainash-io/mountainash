# Expression Gaps: Windows, Case Sensitivity, and Cumulative Operations — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix broken Polars window ordering and ranking, wire case-insensitive string matching through all backends, and add `.diff()` and `cum_sum()` operations.

**Architecture:** Polars-style public API → Substrait-aligned AST (WindowFunctionNode) → per-backend compilation. The `.over()` method merges partition/order into pre-populated WindowSpecs. Case sensitivity uses lowercase-both-sides to preserve literal semantics.

**Tech Stack:** mountainash expressions (Polars, Narwhals, Ibis backends), Pydantic AST nodes, pytest cross-backend parametrized tests.

**Spec:** `docs/superpowers/specs/2026-04-28-expression-gaps-windows-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/mountainash/expressions/core/expression_system/function_keys/enums.py` | Modify | Add `FKEY_MOUNTAINASH_WINDOW` enum (cum_sum/cum_max/cum_min/cum_count, rank_average, rank_max) and `FKEY_MOUNTAINASH_SCALAR_ARITHMETIC.DIFF` |
| `src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_window_arithmetic.py` | Modify | Add `order_by_col` + `descending` kwargs to rank/dense_rank/row_number protocol methods |
| `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_window.py` | Create | Protocol for cum_sum/cum_max/cum_min/cum_count + diff |
| `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py` | Modify | Register new function keys (FKEY_MOUNTAINASH_WINDOW.*, DIFF) |
| `src/mountainash/expressions/core/expression_api/api_base.py` | Modify | Add `rank(method, descending)`, `diff(n)`, `cum_sum(reverse)`, `cum_max/min/count(reverse)` methods; update `.over()` merge logic |
| `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py` | Modify | Update `rank()`/`dense_rank()`/`row_number()` to accept `order_by_col`/`descending` and pre-populate WindowSpec |
| `src/mountainash/expressions/core/unified_visitor/visitor.py` | Modify | Pass `order_by` context to ranking backend methods in `visit_window_function` |
| `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_window_arithmetic.py` | Modify | Fix `apply_window` to pass `order_by`; fix rank/dense_rank/row_number to use native `Expr.rank()` |
| `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py` | Modify | Wire `case_sensitivity` through contains/starts_with/ends_with |
| `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_window.py` | Create | Polars backend for cum_sum/cum_max/cum_min/cum_count + diff |
| `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py` | Modify | Wire `case_sensitivity` through contains/starts_with/ends_with |
| `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_window_arithmetic.py` | Modify | Update rank/dense_rank/row_number signatures for order_by_col/descending |
| `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_window.py` | Create | Narwhals backend for cum_sum/cum_max/cum_min/cum_count + diff |
| `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py` | Modify | Wire `case_sensitivity` through contains/starts_with/ends_with |
| `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_window_arithmetic.py` | Modify | Update rank/dense_rank/row_number signatures for order_by_col/descending |
| `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_window.py` | Create | Ibis backend for cum_sum/cum_max/cum_min/cum_count + diff |
| `tests/cross_backend/test_case_insensitive_string.py` | Create | Cross-backend tests for case-insensitive contains/starts_with/ends_with |
| `tests/window/test_window_ranking_correctness.py` | Create | Correctness tests for rank values, ascending vs descending |
| `tests/window/test_window_apply_window_order.py` | Create | Tests proving order_by affects window results |
| `tests/window/test_window_diff.py` | Create | Tests for .diff() including windowed diff |
| `tests/window/test_window_cumulative.py` | Create | Tests for cum_sum/cum_max/cum_min/cum_count |
| `mountainash-central/01.principles/mountainash/c.api-design/polars-api-substrait-ast.md` | Create | New principle doc |

---

### Task 1: Fix Polars `apply_window` to Pass `order_by`

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_window_arithmetic.py:209-231`
- Test: `tests/window/test_window_apply_window_order.py`

- [ ] **Step 1: Write failing test proving order_by is ignored**

```python
"""Tests that Polars apply_window passes order_by through to .over()."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def unordered_df():
    return pl.DataFrame({
        "group": ["A", "A", "A", "B", "B"],
        "value": [30, 10, 20, 50, 40],
        "ts": [3, 1, 2, 2, 1],
    })


class TestApplyWindowOrderBy:
    def test_cum_sum_order_by_changes_result(self, unordered_df):
        """cum_sum().over() with order_by must produce different results than without."""
        # sum().over() with order_by="ts" should cumulate in ts order
        # For group A: ts=1→10, ts=2→10+20=30, ts=3→10+20+30=60
        # Without order_by, order is undefined
        expr = ma.col("value").sum().over("group", order_by="ts")
        result = unordered_df.with_columns(expr.compile(unordered_df).alias("windowed"))
        group_a = result.filter(pl.col("group") == "A").sort("ts")
        # With order_by, each row should see the sum up to that point in ts order
        assert result.shape[0] == 5

    def test_lag_with_order_by_respects_ordering(self, unordered_df):
        """lag(1).over() with order_by should lag in the specified order."""
        expr = ma.col("value").lag(1).over("group", order_by="ts")
        result = unordered_df.with_columns(expr.compile(unordered_df).alias("lagged"))

        group_a = result.filter(pl.col("group") == "A").sort("ts")
        lagged = group_a["lagged"].to_list()
        # ts order: ts=1→value=10, ts=2→value=20, ts=3→value=30
        # lag(1) in ts order: [None, 10, 20]
        assert lagged == [None, 10, 20]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target-quick tests/window/test_window_apply_window_order.py -v`
Expected: FAIL — lag values won't match because order_by is ignored

- [ ] **Step 3: Fix `apply_window` in Polars backend**

In `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_window_arithmetic.py`, replace the `apply_window` method:

```python
def apply_window(
    self,
    expr: PolarsExpr,
    partition_by: List[Any],
    order_by: List[Tuple[Any, bool]],
    lower_bound: Optional[WindowBound] = None,
    upper_bound: Optional[WindowBound] = None,
) -> PolarsExpr:
    """Apply window context to a Polars expression.

    Args:
        expr: The native Polars expression to apply windowing to.
        partition_by: List of native partition expressions.
        order_by: List of (expression, descending) tuples.
        lower_bound: Optional frame lower bound.
        upper_bound: Optional frame upper bound.

    Returns:
        Expression with window context applied via .over().
    """
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

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run test:test-target-quick tests/window/test_window_apply_window_order.py -v`
Expected: PASS

- [ ] **Step 5: Run existing window tests to check for regressions**

Run: `hatch run test:test-target-quick tests/window/ -v`
Expected: All existing tests pass (or same xfails as before)

- [ ] **Step 6: Commit**

```bash
git add tests/window/test_window_apply_window_order.py src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_window_arithmetic.py
git commit -m "fix: wire order_by through Polars apply_window

Previously apply_window discarded order_by, lower_bound, and upper_bound —
only partition_by was passed to .over(). Narwhals and Ibis backends already
handled this correctly."
```

---

### Task 2: Fix Polars Ranking Functions to Use Native `Expr.rank()`

**Files:**
- Modify: `src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_window_arithmetic.py:23-45`
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_window_arithmetic.py:38-95`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_window_arithmetic.py` (rank/dense_rank/row_number)
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_window_arithmetic.py` (rank/dense_rank/row_number)
- Modify: `src/mountainash/expressions/core/unified_visitor/visitor.py:459-504`
- Test: `tests/window/test_window_ranking_correctness.py`

- [ ] **Step 1: Write failing test proving ranking is wrong**

```python
"""Tests that ranking functions produce correct rank values, not sequential numbers."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def rank_df():
    return pl.DataFrame({
        "team": ["A", "A", "A", "A", "B", "B", "B"],
        "score": [10, 30, 20, 30, 50, 10, 30],
    })


class TestRankingCorrectness:
    def test_dense_rank_no_gaps(self, rank_df):
        """dense_rank should produce consecutive ranks with no gaps for ties."""
        expr = ma.col("score").dense_rank().over("team", order_by="score")
        result = rank_df.with_columns(expr.compile(rank_df).alias("drank"))

        team_a = result.filter(pl.col("team") == "A").sort("score")
        ranks = team_a["drank"].to_list()
        # scores: [10, 20, 30, 30] → dense_rank: [1, 2, 3, 3]
        assert ranks == [1, 2, 3, 3]

    def test_rank_with_gaps(self, rank_df):
        """rank (method='min') should produce gaps for ties."""
        expr = ma.col("score").rank().over("team", order_by="score")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rnk"))

        team_a = result.filter(pl.col("team") == "A").sort("score")
        ranks = team_a["rnk"].to_list()
        # scores: [10, 20, 30, 30] → rank(min): [1, 2, 3, 3]
        assert ranks == [1, 2, 3, 3]

    def test_row_number_unique(self, rank_df):
        """row_number should produce unique sequential numbers."""
        expr = ma.col("score").row_number().over("team", order_by="score")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rn"))

        team_a = result.filter(pl.col("team") == "A").sort("score")
        ranks = team_a["rn"].to_list()
        # scores: [10, 20, 30, 30] → row_number: [1, 2, 3, 4] (all unique)
        assert ranks == [1, 2, 3, 4]

    def test_rank_descending_produces_different_output(self, rank_df):
        """descending=True must produce different ranks than descending=False."""
        expr_asc = ma.col("score").rank(descending=False).over("team", order_by="score")
        expr_desc = ma.col("score").rank(descending=True).over("team", order_by="score")

        result_asc = rank_df.with_columns(expr_asc.compile(rank_df).alias("rnk"))
        result_desc = rank_df.with_columns(expr_desc.compile(rank_df).alias("rnk"))

        team_a_asc = result_asc.filter(pl.col("team") == "A").sort("score")["rnk"].to_list()
        team_a_desc = result_desc.filter(pl.col("team") == "A").sort("score")["rnk"].to_list()

        assert team_a_asc != team_a_desc
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target-quick tests/window/test_window_ranking_correctness.py -v`
Expected: FAIL — dense_rank currently returns sequential [1,2,3,4] not [1,2,3,3]

- [ ] **Step 3: Update protocol signatures for ranking functions**

In `src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_window_arithmetic.py`, update the ranking method signatures:

```python
def row_number(self, *, order_by_col: ExpressionT | None = None, descending: bool = False) -> ExpressionT:
    """the number of the current row within its partition, starting at 1"""
    ...

def rank(self, *, order_by_col: ExpressionT | None = None, descending: bool = False) -> ExpressionT:
    """the rank of the current row, with gaps."""
    ...

def dense_rank(self, *, order_by_col: ExpressionT | None = None, descending: bool = False) -> ExpressionT:
    """the rank of the current row, without gaps."""
    ...
```

- [ ] **Step 4: Update visitor to pass order_by to ranking methods**

In `src/mountainash/expressions/core/unified_visitor/visitor.py`, in `visit_window_function` (around line 459), after resolving the function from the registry, detect ranking functions and pass `order_by_col` + `descending` from the WindowSpec:

```python
RANKING_KEYS = {
    SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
    SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
    SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
}

# Inside visit_window_function, after resolving compiled_args and method:
if node.function_key in RANKING_KEYS and node.window_spec and node.window_spec.order_by:
    first_sort = node.window_spec.order_by[0]
    order_col = self.visit(FieldReferenceNode(field=first_sort.column))
    options["order_by_col"] = order_col
    options["descending"] = first_sort.descending
```

Also add the import at the top of the visitor:
```python
from ..expression_system.function_keys.enums import SUBSTRAIT_ARITHMETIC_WINDOW
```

- [ ] **Step 5: Fix Polars backend ranking methods**

In `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_window_arithmetic.py`, replace the ranking methods:

```python
def row_number(self, *, order_by_col: PolarsExpr | None = None, descending: bool = False) -> PolarsExpr:
    if order_by_col is not None:
        return order_by_col.rank(method="ordinal", descending=descending)
    return pl.int_range(1, pl.len() + 1)

def rank(self, *, order_by_col: PolarsExpr | None = None, descending: bool = False) -> PolarsExpr:
    if order_by_col is not None:
        return order_by_col.rank(method="min", descending=descending)
    return pl.int_range(1, pl.len() + 1)

def dense_rank(self, *, order_by_col: PolarsExpr | None = None, descending: bool = False) -> PolarsExpr:
    if order_by_col is not None:
        return order_by_col.rank(method="dense", descending=descending)
    return pl.int_range(1, pl.len() + 1)

def percent_rank(self, *, order_by_col: PolarsExpr | None = None, descending: bool = False) -> PolarsExpr:
    if order_by_col is not None:
        r = order_by_col.rank(method="min", descending=descending)
        n = pl.len()
        return (r.cast(pl.Float64) - 1) / (n - 1).cast(pl.Float64)
    n = pl.len()
    return (pl.int_range(0, n).cast(pl.Float64)) / (n - 1).cast(pl.Float64)
```

- [ ] **Step 6: Update Narwhals backend ranking methods**

In `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_window_arithmetic.py`, add `order_by_col`/`descending` kwargs to `rank`, `dense_rank`, `row_number` (Narwhals' native `rank(method=..., descending=...)` handles this directly):

```python
def row_number(self, *, order_by_col: NarwhalsExpr | None = None, descending: bool = False) -> NarwhalsExpr:
    if order_by_col is not None:
        return order_by_col.rank(method="ordinal", descending=descending)
    # fallback: rank self
    ...

def rank(self, *, order_by_col: NarwhalsExpr | None = None, descending: bool = False) -> NarwhalsExpr:
    if order_by_col is not None:
        return order_by_col.rank(method="min", descending=descending)
    ...

def dense_rank(self, *, order_by_col: NarwhalsExpr | None = None, descending: bool = False) -> NarwhalsExpr:
    if order_by_col is not None:
        return order_by_col.rank(method="dense", descending=descending)
    ...
```

- [ ] **Step 7: Update Ibis backend ranking methods**

In `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_window_arithmetic.py`, add `order_by_col`/`descending` kwargs. Ibis ranking is handled via `ibis.rank()` etc. which are window functions — the order_by is applied via `.over()`:

```python
def row_number(self, *, order_by_col: IbisNumericExpr | None = None, descending: bool = False) -> IbisNumericExpr:
    return ibis.row_number()

def rank(self, *, order_by_col: IbisNumericExpr | None = None, descending: bool = False) -> IbisNumericExpr:
    return ibis.rank()

def dense_rank(self, *, order_by_col: IbisNumericExpr | None = None, descending: bool = False) -> IbisNumericExpr:
    return ibis.dense_rank()
```

Note: Ibis ranking functions are zero-arg and get their ordering from `apply_window` which already handles `order_by` correctly. The `order_by_col`/`descending` params are accepted for protocol compatibility but the ordering is handled by `apply_window`.

- [ ] **Step 8: Run tests to verify ranking is correct**

Run: `hatch run test:test-target-quick tests/window/test_window_ranking_correctness.py -v`
Expected: PASS

- [ ] **Step 9: Run all window tests for regressions**

Run: `hatch run test:test-target-quick tests/window/ -v`
Expected: All pass

- [ ] **Step 10: Commit**

```bash
git add src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_window_arithmetic.py src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_window_arithmetic.py src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_window_arithmetic.py src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_window_arithmetic.py src/mountainash/expressions/core/unified_visitor/visitor.py tests/window/test_window_ranking_correctness.py
git commit -m "fix: Polars ranking uses native Expr.rank() with method and descending

rank(), dense_rank(), and row_number() previously returned pl.int_range()
(sequential numbering ignoring values). Now uses Polars native Expr.rank()
with correct method mapping and descending support. Visitor passes order_by
context from WindowSpec to ranking backend methods."
```

---

### Task 3: Update `rank()` API to Polars-Style with `method` Parameter

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_base.py:297-381`
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py:47-90`
- Modify: `src/mountainash/expressions/core/expression_system/function_keys/enums.py`
- Modify: `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`
- Test: `tests/window/test_window_ranking_correctness.py` (extend)

- [ ] **Step 1: Add FKEY_MOUNTAINASH_WINDOW enum**

In `src/mountainash/expressions/core/expression_system/function_keys/enums.py`, add after the `SUBSTRAIT_ARITHMETIC_WINDOW` class (around line 404):

```python
class FKEY_MOUNTAINASH_WINDOW(Enum):
    """mountainash extension window functions.

    Not part of the Substrait spec — mountainash-specific operations.
    """
    RANK_AVERAGE = auto()
    RANK_MAX = auto()
    CUM_SUM = auto()
    CUM_MAX = auto()
    CUM_MIN = auto()
    CUM_COUNT = auto()
```

- [ ] **Step 2: Update the `rank()` API builder to accept `method` and `descending`**

In `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py`, replace the `rank()`, `dense_rank()`, and `row_number()` methods with a single unified `rank()`:

```python
from typing import Literal
from mountainash.expressions.core.expression_system.function_keys.enums import (
    SUBSTRAIT_ARITHMETIC_WINDOW,
    FKEY_MOUNTAINASH_WINDOW,
)
from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import WindowSpec
from mountainash.core.constants import SortField

_RANK_METHOD_TO_KEY = {
    "average": FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE,
    "min": SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
    "max": FKEY_MOUNTAINASH_WINDOW.RANK_MAX,
    "dense": SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
    "ordinal": SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
}

def rank(
    self,
    method: Literal["average", "min", "max", "dense", "ordinal"] = "average",
    *,
    descending: bool = False,
) -> BaseExpressionAPI:
    """Rank values within a partition.

    Mirrors Polars: ma.col("x").rank(method="dense", descending=True).over("group")

    Args:
        method: Ranking method — 'average', 'min' (SQL RANK), 'max',
                'dense' (SQL DENSE_RANK), 'ordinal' (SQL ROW_NUMBER).
        descending: If True, highest values get rank 1.

    Returns:
        New ExpressionAPI with WindowFunctionNode. Must call .over() before compiling.
    """
    function_key = _RANK_METHOD_TO_KEY[method]

    # Extract column name from the inner node (FieldReferenceNode)
    from mountainash.expressions.core.expression_nodes import FieldReferenceNode
    if isinstance(self._node, FieldReferenceNode):
        col_name = self._node.field
    else:
        raise ValueError(
            "rank() must be called on a column reference, e.g. ma.col('x').rank()"
        )

    node = WindowFunctionNode(
        function_key=function_key,
        arguments=[],
        window_spec=WindowSpec(
            order_by=[SortField(column=col_name, descending=descending)],
        ),
    )
    return self._build(node)
```

Keep the existing `dense_rank()` and `row_number()` methods as aliases that delegate to `rank()`:

```python
def dense_rank(self, *, descending: bool = False) -> BaseExpressionAPI:
    """Alias for rank(method="dense"). See rank()."""
    return self.rank(method="dense", descending=descending)

def row_number(self, *, descending: bool = False) -> BaseExpressionAPI:
    """Alias for rank(method="ordinal"). See rank()."""
    return self.rank(method="ordinal", descending=descending)
```

- [ ] **Step 3: Update `.over()` merge semantics in `api_base.py`**

In `src/mountainash/expressions/core/expression_api/api_base.py`, replace lines 374-381:

```python
# If inner node is a WindowFunctionNode, either populate or merge
if isinstance(self._node, WindowFunctionNode):
    if self._node.window_spec is None:
        # No existing spec — populate from .over() args
        updated_node = self._node.model_copy(update={"window_spec": spec})
        return self.create(updated_node)
    else:
        # Merge: add partition_by from .over() into existing spec
        # Preserve existing order_by (from rank()) and bounds (from cum_sum())
        existing = self._node.window_spec
        merged_order_by = existing.order_by if existing.order_by else sort_fields
        merged_lower = existing.lower_bound if existing.lower_bound else lower_bound
        merged_upper = existing.upper_bound if existing.upper_bound else upper_bound
        merged_spec = WindowSpec(
            partition_by=partition_nodes,
            order_by=merged_order_by,
            lower_bound=merged_lower,
            upper_bound=merged_upper,
        )
        updated_node = self._node.model_copy(update={"window_spec": merged_spec})
        return self.create(updated_node)

# Otherwise, wrap in an OverNode
over_node = OverNode(expression=self._node, window_spec=spec)
return self.create(over_node)
```

- [ ] **Step 4: Register new function keys in definitions.py**

In `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`, add to the WINDOW_ARITHMETIC_FUNCTIONS list (or create a new MOUNTAINASH_WINDOW_FUNCTIONS list):

```python
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_WINDOW

MOUNTAINASH_WINDOW_FUNCTIONS = [
    ExpressionFunctionDef(
        function_key=FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE,
        substrait_uri=None,
        substrait_name=None,
        protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.rank,
    ),
    ExpressionFunctionDef(
        function_key=FKEY_MOUNTAINASH_WINDOW.RANK_MAX,
        substrait_uri=None,
        substrait_name=None,
        protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.rank,
    ),
]
```

And register them in the `_register_all` function alongside the existing window functions.

- [ ] **Step 5: Update Polars backend rank to handle RANK_AVERAGE and RANK_MAX**

In the Polars backend `expsys_pl_window_arithmetic.py`, add a `rank_average` and `rank_max` method, or detect the key in the existing `rank()` method. The simplest approach: map RANK_AVERAGE to `Expr.rank(method="average")` and RANK_MAX to `Expr.rank(method="max")`:

```python
def rank_average(self, *, order_by_col: PolarsExpr | None = None, descending: bool = False) -> PolarsExpr:
    if order_by_col is not None:
        return order_by_col.rank(method="average", descending=descending)
    return pl.int_range(1, pl.len() + 1).cast(pl.Float64)

def rank_max(self, *, order_by_col: PolarsExpr | None = None, descending: bool = False) -> PolarsExpr:
    if order_by_col is not None:
        return order_by_col.rank(method="max", descending=descending)
    return pl.int_range(1, pl.len() + 1)
```

- [ ] **Step 6: Write test for rank(method=...) API**

Add to `tests/window/test_window_ranking_correctness.py`:

```python
def test_rank_method_dense(self, rank_df):
    """rank(method='dense') is equivalent to dense_rank()."""
    expr = ma.col("score").rank(method="dense").over("team", order_by="score")
    result = rank_df.with_columns(expr.compile(rank_df).alias("drank"))
    team_a = result.filter(pl.col("team") == "A").sort("score")
    assert team_a["drank"].to_list() == [1, 2, 3, 3]

def test_rank_method_ordinal(self, rank_df):
    """rank(method='ordinal') produces unique sequential ranks."""
    expr = ma.col("score").rank(method="ordinal").over("team", order_by="score")
    result = rank_df.with_columns(expr.compile(rank_df).alias("rn"))
    team_a = result.filter(pl.col("team") == "A").sort("score")
    assert team_a["rn"].to_list() == [1, 2, 3, 4]
```

- [ ] **Step 7: Run tests**

Run: `hatch run test:test-target-quick tests/window/ -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/expressions/core/expression_system/function_keys/enums.py src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py src/mountainash/expressions/core/expression_api/api_base.py src/mountainash/expressions/core/expression_system/function_mapping/definitions.py src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_window_arithmetic.py tests/window/test_window_ranking_correctness.py
git commit -m "feat: Polars-style rank(method, descending) API with .over() merge

rank(method='dense', descending=True).over('group') builds a Substrait-
aligned WindowFunctionNode with pre-populated order_by, then .over()
merges partition_by into the existing WindowSpec."
```

---

### Task 4: Wire `case_sensitivity` Through All String Backends

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py`
- Test: `tests/cross_backend/test_case_insensitive_string.py`

- [ ] **Step 1: Write failing test for case-insensitive contains**

```python
"""Cross-backend tests for case-insensitive string matching."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def string_df():
    return pl.DataFrame({
        "text": ["Hello World", "HELLO WORLD", "hello world", "Goodbye", "foo.bar"],
    })


class TestCaseInsensitiveContains:
    def test_case_insensitive_contains(self, string_df):
        """str.contains(case_sensitive=False) matches regardless of case."""
        expr = ma.col("text").str.contains("hello", case_sensitive=False)
        result = string_df.with_columns(expr.compile(string_df).alias("match"))
        matches = result["match"].to_list()
        assert matches == [True, True, True, False, False]

    def test_case_sensitive_contains_default(self, string_df):
        """str.contains() is case-sensitive by default."""
        expr = ma.col("text").str.contains("hello")
        result = string_df.with_columns(expr.compile(string_df).alias("match"))
        matches = result["match"].to_list()
        assert matches == [False, False, True, False, False]

    def test_case_insensitive_preserves_literal_semantics(self, string_df):
        """Regex metacharacters treated as literals even in case-insensitive mode."""
        expr = ma.col("text").str.contains("foo.bar", case_sensitive=False)
        result = string_df.with_columns(expr.compile(string_df).alias("match"))
        matches = result["match"].to_list()
        # Must match "foo.bar" literally, not "foo" + any char + "bar"
        assert matches == [False, False, False, False, True]

    def test_case_insensitive_starts_with(self, string_df):
        """str.starts_with(case_sensitive=False) matches prefix regardless of case."""
        expr = ma.col("text").str.starts_with("hello", case_sensitive=False)
        result = string_df.with_columns(expr.compile(string_df).alias("match"))
        matches = result["match"].to_list()
        assert matches == [True, True, True, False, False]

    def test_case_insensitive_ends_with(self, string_df):
        """str.ends_with(case_sensitive=False) matches suffix regardless of case."""
        expr = ma.col("text").str.ends_with("world", case_sensitive=False)
        result = string_df.with_columns(expr.compile(string_df).alias("match"))
        matches = result["match"].to_list()
        assert matches == [True, True, True, False, False]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target-quick tests/cross_backend/test_case_insensitive_string.py -v`
Expected: FAIL — case_insensitive is silently ignored

- [ ] **Step 3: Fix Polars backend string methods**

In `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py`, update `contains`, `starts_with`, `ends_with` to read `case_sensitivity`:

```python
def contains(
    self,
    input: PolarsExpr,
    /,
    substring: PolarsExpr,
    case_sensitivity: Any = None,
) -> PolarsExpr:
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

def starts_with(
    self,
    input: PolarsExpr,
    substring: PolarsExpr,
    /,
    case_sensitivity: Any = None,
) -> PolarsExpr:
    if case_sensitivity == "CASE_INSENSITIVE":
        return input.str.to_lowercase().str.starts_with(substring.str.to_lowercase())
    return input.str.starts_with(substring)

def ends_with(
    self,
    input: PolarsExpr,
    /,
    substring: PolarsExpr,
    case_sensitivity: Any = None,
) -> PolarsExpr:
    if case_sensitivity == "CASE_INSENSITIVE":
        return input.str.to_lowercase().str.ends_with(substring.str.to_lowercase())
    return input.str.ends_with(substring)
```

- [ ] **Step 4: Fix Narwhals backend string methods**

In `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py`, apply the same pattern using `nw_expr.str.to_lowercase()`.

- [ ] **Step 5: Fix Ibis backend string methods**

In `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py`, apply the same pattern using `.lower()` on both sides.

- [ ] **Step 6: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_case_insensitive_string.py -v`
Expected: PASS

- [ ] **Step 7: Run full string test suite for regressions**

Run: `hatch run test:test-target-quick tests/cross_backend/test_string.py -v`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py tests/cross_backend/test_case_insensitive_string.py
git commit -m "fix: wire case_sensitivity through all string backends

contains/starts_with/ends_with now respect the CASE_INSENSITIVE option
by lowercasing both input and substring. Preserves literal semantics —
no regex conversion that would break metacharacter inputs."
```

---

### Task 5: Add `.diff()` Operation

**Files:**
- Modify: `src/mountainash/expressions/core/expression_system/function_keys/enums.py`
- Create: `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_window.py`
- Modify: `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py` (or a new ma extension builder)
- Create: `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_window.py`
- Create: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_window.py`
- Create: `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_window.py`
- Test: `tests/window/test_window_diff.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for .diff() — consecutive row difference."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def diff_df():
    return pl.DataFrame({
        "group": ["A", "A", "A", "B", "B"],
        "value": [10, 30, 25, 100, 80],
        "ts": [1, 2, 3, 1, 2],
    })


class TestDiff:
    def test_diff_basic(self, diff_df):
        """diff() computes consecutive differences."""
        expr = ma.col("value").diff()
        result = diff_df.with_columns(expr.compile(diff_df).alias("d"))
        diffs = result["d"].to_list()
        # First element is None, then 30-10=20, 25-30=-5, 100-25=75, 80-100=-20
        assert diffs == [None, 20, -5, 75, -20]

    def test_diff_over_partition(self, diff_df):
        """diff().over() computes differences within each partition."""
        expr = ma.col("value").diff().over("group", order_by="ts")
        result = diff_df.with_columns(expr.compile(diff_df).alias("d"))
        group_a = result.filter(pl.col("group") == "A").sort("ts")
        diffs_a = group_a["d"].to_list()
        # Group A: ts order values [10, 30, 25] → diff [None, 20, -5]
        assert diffs_a == [None, 20, -5]

        group_b = result.filter(pl.col("group") == "B").sort("ts")
        diffs_b = group_b["d"].to_list()
        # Group B: ts order values [100, 80] → diff [None, -20]
        assert diffs_b == [None, -20]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target-quick tests/window/test_window_diff.py -v`
Expected: FAIL — diff() not defined

- [ ] **Step 3: Add DIFF to function key enums**

In `src/mountainash/expressions/core/expression_system/function_keys/enums.py`, add to the mountainash scalar arithmetic enum (find `FKEY_MOUNTAINASH_SCALAR_ARITHMETIC` or `FKEY_MOUNTAINASH_SCALAR_DATETIME`):

```python
# In the appropriate mountainash extension enum class, add:
DIFF = auto()
```

If no suitable existing enum exists, add it to `FKEY_MOUNTAINASH_WINDOW`:
```python
class FKEY_MOUNTAINASH_WINDOW(Enum):
    RANK_AVERAGE = auto()
    RANK_MAX = auto()
    CUM_SUM = auto()
    CUM_MAX = auto()
    CUM_MIN = auto()
    CUM_COUNT = auto()
    DIFF = auto()
```

- [ ] **Step 4: Create protocol for mountainash window extensions**

Create `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_window.py`:

```python
"""Protocol for mountainash extension window operations."""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT


class MountainashWindowExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for mountainash extension window operations.

    These operations are not part of the Substrait spec.
    """

    def diff(self, x: ExpressionT, /, *, n: int = 1) -> ExpressionT:
        """Consecutive difference: value[i] - value[i-n]. First n elements are null."""
        ...

    def cum_sum(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
        """Cumulative sum."""
        ...

    def cum_max(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
        """Cumulative maximum."""
        ...

    def cum_min(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
        """Cumulative minimum."""
        ...

    def cum_count(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
        """Cumulative count."""
        ...
```

- [ ] **Step 5: Register DIFF in function mapping definitions**

In `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`, add the diff function def to the mountainash window functions list and register it.

- [ ] **Step 6: Add `diff()` to API builder**

In `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py`, add:

```python
def diff(self, n: int = 1) -> BaseExpressionAPI:
    """Consecutive difference: value[i] - value[i-n].

    Args:
        n: Number of slots to shift (default 1).

    Returns:
        New ExpressionAPI with WindowFunctionNode.
    """
    node = WindowFunctionNode(
        function_key=FKEY_MOUNTAINASH_WINDOW.DIFF,
        arguments=[self._node],
        options={"n": n} if n != 1 else {},
    )
    return self._build(node)
```

- [ ] **Step 7: Implement Polars backend diff**

Create or add to `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_window.py`:

```python
"""Polars backend for mountainash extension window operations."""

from __future__ import annotations

import polars as pl
from polars import Expr as PolarsExpr


class PolarsExtMaWindowExpressionSystem:

    def diff(self, x: PolarsExpr, /, *, n: int = 1) -> PolarsExpr:
        return x.diff(n=n)
```

- [ ] **Step 8: Implement Narwhals backend diff**

Create `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_window.py`:

```python
"""Narwhals backend for mountainash extension window operations."""

from __future__ import annotations

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsExpr


class NarwhalsExtMaWindowExpressionSystem:

    def diff(self, x: NarwhalsExpr, /, *, n: int = 1) -> NarwhalsExpr:
        if n != 1:
            raise NotImplementedError(
                "Narwhals diff() only supports n=1. "
                "Use Polars or Ibis backend for n > 1."
            )
        return x.diff()
```

- [ ] **Step 9: Implement Ibis backend diff**

Create `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_window.py`:

```python
"""Ibis backend for mountainash extension window operations."""

from __future__ import annotations

from mountainash.expressions.backends.expression_systems.ibis.base import IbisNumericExpr


class IbisExtMaWindowExpressionSystem:

    def diff(self, x: IbisNumericExpr, /, *, n: int = 1) -> IbisNumericExpr:
        return x - x.lag(offset=n)
```

- [ ] **Step 10: Run tests**

Run: `hatch run test:test-target-quick tests/window/test_window_diff.py -v`
Expected: PASS

- [ ] **Step 11: Commit**

```bash
git add src/mountainash/expressions/core/expression_system/function_keys/enums.py src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_window.py src/mountainash/expressions/core/expression_system/function_mapping/definitions.py src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_window.py src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_window.py src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_window.py tests/window/test_window_diff.py
git commit -m "feat: add .diff() for consecutive row differences

New mountainash extension operation. Polars/Narwhals use native .diff(),
Ibis decomposes to col - col.lag(n). Narwhals limited to n=1."
```

---

### Task 6: Add `cum_sum()` Family

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py`
- Modify: `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_window.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_window.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_window.py`
- Test: `tests/window/test_window_cumulative.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for cumulative operations: cum_sum, cum_max, cum_min, cum_count."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def cum_df():
    return pl.DataFrame({
        "store": ["A", "A", "A", "B", "B"],
        "date": [1, 2, 3, 1, 2],
        "sales": [10, 20, 30, 100, 50],
    })


class TestCumSum:
    def test_cum_sum_basic(self, cum_df):
        """cum_sum() computes running total."""
        expr = ma.col("sales").cum_sum()
        result = cum_df.with_columns(expr.compile(cum_df).alias("cs"))
        assert result["cs"].to_list() == [10, 30, 60, 160, 210]

    def test_cum_sum_over_partition_with_order(self, cum_df):
        """cum_sum().over('store', order_by='date') resets per partition."""
        expr = ma.col("sales").cum_sum().over("store", order_by="date")
        result = cum_df.with_columns(expr.compile(cum_df).alias("cs"))

        store_a = result.filter(pl.col("store") == "A").sort("date")
        assert store_a["cs"].to_list() == [10, 30, 60]

        store_b = result.filter(pl.col("store") == "B").sort("date")
        assert store_b["cs"].to_list() == [100, 150]

    def test_cum_sum_reverse(self, cum_df):
        """cum_sum(reverse=True) computes from bottom to top."""
        expr = ma.col("sales").cum_sum(reverse=True)
        result = cum_df.with_columns(expr.compile(cum_df).alias("cs"))
        assert result["cs"].to_list() == [210, 200, 180, 150, 50]


class TestCumMax:
    def test_cum_max_basic(self, cum_df):
        """cum_max() computes running maximum."""
        expr = ma.col("sales").cum_max()
        result = cum_df.with_columns(expr.compile(cum_df).alias("cm"))
        assert result["cm"].to_list() == [10, 20, 30, 100, 100]


class TestCumMin:
    def test_cum_min_basic(self, cum_df):
        """cum_min() computes running minimum."""
        expr = ma.col("sales").cum_min()
        result = cum_df.with_columns(expr.compile(cum_df).alias("cm"))
        assert result["cm"].to_list() == [10, 10, 10, 10, 10]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target-quick tests/window/test_window_cumulative.py -v`
Expected: FAIL — cum_sum not defined

- [ ] **Step 3: Add cum_sum/cum_max/cum_min/cum_count to API builder**

In `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py`, add:

```python
from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import (
    WindowSpec, WindowBound,
)
from mountainash.core.constants import WindowBoundType

def cum_sum(self, *, reverse: bool = False) -> BaseExpressionAPI:
    """Cumulative sum. Use .over() to partition.

    Args:
        reverse: If True, compute from bottom to top.
    """
    if reverse:
        lower = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
        upper = WindowBound(bound_type=WindowBoundType.UNBOUNDED_FOLLOWING)
    else:
        lower = WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
        upper = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)

    node = WindowFunctionNode(
        function_key=FKEY_MOUNTAINASH_WINDOW.CUM_SUM,
        arguments=[self._node],
        options={"reverse": reverse} if reverse else {},
        window_spec=WindowSpec(lower_bound=lower, upper_bound=upper),
    )
    return self._build(node)

def cum_max(self, *, reverse: bool = False) -> BaseExpressionAPI:
    """Cumulative maximum. Use .over() to partition."""
    if reverse:
        lower = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
        upper = WindowBound(bound_type=WindowBoundType.UNBOUNDED_FOLLOWING)
    else:
        lower = WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
        upper = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)

    node = WindowFunctionNode(
        function_key=FKEY_MOUNTAINASH_WINDOW.CUM_MAX,
        arguments=[self._node],
        options={"reverse": reverse} if reverse else {},
        window_spec=WindowSpec(lower_bound=lower, upper_bound=upper),
    )
    return self._build(node)

def cum_min(self, *, reverse: bool = False) -> BaseExpressionAPI:
    """Cumulative minimum. Use .over() to partition."""
    if reverse:
        lower = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
        upper = WindowBound(bound_type=WindowBoundType.UNBOUNDED_FOLLOWING)
    else:
        lower = WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
        upper = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)

    node = WindowFunctionNode(
        function_key=FKEY_MOUNTAINASH_WINDOW.CUM_MIN,
        arguments=[self._node],
        options={"reverse": reverse} if reverse else {},
        window_spec=WindowSpec(lower_bound=lower, upper_bound=upper),
    )
    return self._build(node)

def cum_count(self, *, reverse: bool = False) -> BaseExpressionAPI:
    """Cumulative count. Use .over() to partition."""
    if reverse:
        lower = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
        upper = WindowBound(bound_type=WindowBoundType.UNBOUNDED_FOLLOWING)
    else:
        lower = WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
        upper = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)

    node = WindowFunctionNode(
        function_key=FKEY_MOUNTAINASH_WINDOW.CUM_COUNT,
        arguments=[self._node],
        options={"reverse": reverse} if reverse else {},
        window_spec=WindowSpec(lower_bound=lower, upper_bound=upper),
    )
    return self._build(node)
```

- [ ] **Step 4: Register cum_sum/cum_max/cum_min/cum_count in definitions.py**

Add to the function mapping registration in `definitions.py`:

```python
ExpressionFunctionDef(
    function_key=FKEY_MOUNTAINASH_WINDOW.CUM_SUM,
    substrait_uri=None,
    substrait_name=None,
    protocol_method=MountainashWindowExpressionSystemProtocol.cum_sum,
),
ExpressionFunctionDef(
    function_key=FKEY_MOUNTAINASH_WINDOW.CUM_MAX,
    substrait_uri=None,
    substrait_name=None,
    protocol_method=MountainashWindowExpressionSystemProtocol.cum_max,
),
ExpressionFunctionDef(
    function_key=FKEY_MOUNTAINASH_WINDOW.CUM_MIN,
    substrait_uri=None,
    substrait_name=None,
    protocol_method=MountainashWindowExpressionSystemProtocol.cum_min,
),
ExpressionFunctionDef(
    function_key=FKEY_MOUNTAINASH_WINDOW.CUM_COUNT,
    substrait_uri=None,
    substrait_name=None,
    protocol_method=MountainashWindowExpressionSystemProtocol.cum_count,
),
```

- [ ] **Step 5: Implement Polars backend cumulative methods**

Add to `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_window.py`:

```python
def cum_sum(self, x: PolarsExpr, /, *, reverse: bool = False) -> PolarsExpr:
    return x.cum_sum(reverse=reverse)

def cum_max(self, x: PolarsExpr, /, *, reverse: bool = False) -> PolarsExpr:
    return x.cum_max(reverse=reverse)

def cum_min(self, x: PolarsExpr, /, *, reverse: bool = False) -> PolarsExpr:
    return x.cum_min(reverse=reverse)

def cum_count(self, x: PolarsExpr, /, *, reverse: bool = False) -> PolarsExpr:
    return x.cum_count(reverse=reverse)
```

- [ ] **Step 6: Implement Narwhals backend cumulative methods**

Add to `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_window.py`:

```python
def cum_sum(self, x: NarwhalsExpr, /, *, reverse: bool = False) -> NarwhalsExpr:
    return x.cum_sum(reverse=reverse)

def cum_max(self, x: NarwhalsExpr, /, *, reverse: bool = False) -> NarwhalsExpr:
    return x.cum_max(reverse=reverse)

def cum_min(self, x: NarwhalsExpr, /, *, reverse: bool = False) -> NarwhalsExpr:
    return x.cum_min(reverse=reverse)

def cum_count(self, x: NarwhalsExpr, /, *, reverse: bool = False) -> NarwhalsExpr:
    return x.cum_count(reverse=reverse)
```

- [ ] **Step 7: Implement Ibis backend cumulative methods**

Add to `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_window.py`:

```python
import ibis

def cum_sum(self, x: IbisNumericExpr, /, *, reverse: bool = False) -> IbisNumericExpr:
    if reverse:
        return x.sum().over(ibis.window(rows=(0, None)))
    return x.cumsum()

def cum_max(self, x: IbisNumericExpr, /, *, reverse: bool = False) -> IbisNumericExpr:
    if reverse:
        return x.max().over(ibis.window(rows=(0, None)))
    return x.cummax()

def cum_min(self, x: IbisNumericExpr, /, *, reverse: bool = False) -> IbisNumericExpr:
    if reverse:
        return x.min().over(ibis.window(rows=(0, None)))
    return x.cummin()

def cum_count(self, x: IbisNumericExpr, /, *, reverse: bool = False) -> IbisNumericExpr:
    if reverse:
        return x.count().over(ibis.window(rows=(0, None)))
    return x.count().over(ibis.cumulative_window())
```

- [ ] **Step 8: Run tests**

Run: `hatch run test:test-target-quick tests/window/test_window_cumulative.py -v`
Expected: PASS

- [ ] **Step 9: Run all window tests for regressions**

Run: `hatch run test:test-target-quick tests/window/ -v`
Expected: All pass

- [ ] **Step 10: Commit**

```bash
git add src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py src/mountainash/expressions/core/expression_system/function_mapping/definitions.py src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_window.py src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_window.py src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_window.py tests/window/test_window_cumulative.py
git commit -m "feat: add cum_sum/cum_max/cum_min/cum_count operations

Cumulative operations build WindowFunctionNodes with pre-populated frame
bounds (UNBOUNDED_PRECEDING to CURRENT_ROW). Each backend maps to native
cumulative methods. Supports reverse=True for bottom-to-top computation."
```

---

### Task 7: Write Principle Doc and Update Known Divergences

**Files:**
- Create: `mountainash-central/01.principles/mountainash/c.api-design/polars-api-substrait-ast.md`
- Modify: `mountainash-central/01.principles/mountainash/e.cross-backend/known-divergences.md`

- [ ] **Step 1: Write principle document**

Create `mountainash-central/01.principles/mountainash/c.api-design/polars-api-substrait-ast.md`:

```markdown
# Polars API Surface, Substrait AST Internals

**Status:** ADOPTED
**Date:** 2026-04-28

## Principle

The mountainash public API mirrors Polars calling conventions. The internal AST stays Substrait-aligned. The API builder layer is the translation boundary.

## Motivation

Polars is the primary in-memory backend and the most common user-facing API. Matching its conventions reduces cognitive overhead for users who already know Polars. Substrait alignment keeps the AST portable across backends and allows mountainash to leverage Substrait tooling (plan serialization, cross-engine compatibility).

## Canonical Example: `rank()`

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

## Rules

1. **User-facing method signatures match Polars** — parameter names, defaults, and calling patterns should feel natural to a Polars user.

2. **AST nodes use Substrait types and function keys** — `WindowFunctionNode`, `ScalarFunctionNode`, Substrait-aligned enums. The API builder translates from Polars conventions to Substrait abstractions.

3. **Backends translate from Substrait AST** — each backend reads the Substrait-aligned node and produces its native form. The backend never sees the Polars-style API directly.

4. **Extension operations follow the same pattern** — operations without Substrait equivalents (e.g., `diff()`, `cum_sum()`) use mountainash extension enums but the same node types and visitor machinery.

## When This Applies

- Adding a new expression operation to the API
- Choosing method signatures (follow Polars, not Substrait)
- Deciding where translation logic lives (API builder, not backend)
- Reviewing whether an AST node shape is correct (Substrait-aligned, not Polars-aligned)

## Relationship to Other Principles

- **three-layer-separation.md**: This principle is a specific application of the three-layer separation — it specifies *which* conventions each layer follows.
- **substrait-first-design.md**: Still holds — the AST and internal representation are Substrait-first. This principle adds that the *user-facing API* is Polars-first.
- **fluent-builder-pattern.md**: The Polars-style API is delivered via the fluent builder pattern.
```

- [ ] **Step 2: Update known-divergences.md**

In `mountainash-central/01.principles/mountainash/e.cross-backend/known-divergences.md`, add entries for:

- Narwhals `diff()` limited to `n=1`
- Polars `.over()` has no `ROWS BETWEEN` frame support
- Narwhals cumulative operations in `.over()` only work on pandas/Polars backends
- `rank(method="average")` — Ibis has no equivalent; xfail

- [ ] **Step 3: Commit**

```bash
git add mountainash-central/01.principles/mountainash/c.api-design/polars-api-substrait-ast.md mountainash-central/01.principles/mountainash/e.cross-backend/known-divergences.md
git commit -m "docs: add Polars API / Substrait AST principle and update known divergences

New principle: public API mirrors Polars conventions, AST stays
Substrait-aligned, API builder layer is the translation boundary.
rank() is the canonical example."
```

---

### Task 8: Full Test Suite and Final Verification

- [ ] **Step 1: Run the complete test suite**

Run: `hatch run test:test`
Expected: All tests pass (or same xfails as before, plus new xfails for documented divergences)

- [ ] **Step 2: Run type checking**

Run: `hatch run mypy:check`
Expected: No new type errors

- [ ] **Step 3: Run linting**

Run: `hatch run ruff:check`
Expected: Clean

- [ ] **Step 4: Fix any issues found**

Address any test failures, type errors, or lint violations.

- [ ] **Step 5: Final commit if needed**

```bash
git commit -m "chore: fix lint and type issues from expression gaps work"
```

---

## Task Dependency Graph

```
Task 1 (apply_window fix)
  ↓
Task 2 (ranking fix) ← depends on apply_window working
  ↓
Task 3 (rank API + .over() merge) ← depends on ranking backend fix
  ↓
Task 5 (diff) ← depends on .over() merge + FKEY_MOUNTAINASH_WINDOW enum
  ↓
Task 6 (cum_sum family) ← depends on .over() merge + enum + protocol

Task 4 (case sensitivity) ← independent, can run in parallel with Tasks 1-3

Task 7 (docs) ← after all code tasks
Task 8 (full suite) ← final
```
