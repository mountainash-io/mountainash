# Window Functions Design Spec

**Status:** APPROVED
**Created:** 2026-03-29
**Layer:** 3.3 (Missing Operations)

## Overview

Add window function support to the mountainash expression system. This covers both Substrait-standard window functions (rank, row_number, lag, lead, etc.) and a Polars-aligned `.over()` modifier that turns any expression into a windowed expression. Both models coexist at the AST level and map to the same backend execution.

## Design Decisions

### Dual model: Substrait functions + Extension `.over()`

**Substrait window functions** are specific operations (rank, row_number, ntile) defined in the Substrait spec. They exist as their own function keys, protocol methods, and backend implementations (all already coded).

**Extension `.over()`** is a modifier on any expression — it wraps an existing expression tree with window context. This follows the Polars/Narwhals pattern where `.over()` is the universal mechanism for windowed computation.

Both produce windowed expressions at the backend level. The difference is AST representation:
- `WindowFunctionNode` carries a function key + window spec
- `OverNode` wraps an arbitrary expression + window spec

### "What" vs "Where" separation

Window functions declare **what** operation (rank, lag, sum) with function-specific arguments (offset, default value). The `.over()` call specifies **where** — partition, ordering, frame bounds. This means:

- `rank()` — declares "ranking", no window context yet
- `lag(1, default=0)` — declares "lag with offset 1", no window context yet
- `.over(partition_by="group", order_by="ts")` — applies window context

### No `.window` namespace

The 11 window functions are flat methods on the expression API (same level as `gt()`, `add()`, `upper()`). No name clashes exist with existing methods. The `.over()` method lives on `BaseExpressionAPI` directly.

### Single path via `.over()`

Window functions **must** be followed by `.over()` to be valid. There is no `rank(partition_by=...)` shortcut. This avoids two paths to the same result and matches the Polars model exactly.

## New AST Nodes

Two new node types (total goes from 7 to 9):

### WindowFunctionNode (Substrait)

```python
class WindowFunctionNode(ExpressionNode):
    """Node for Substrait-standard window functions."""
    function_key: SUBSTRAIT_ARITHMETIC_WINDOW  # ROW_NUMBER, RANK, LAG, etc.
    arguments: list[Any] = []                   # Function-specific args (offset, default)
    window_spec: WindowSpec | None = None       # Populated by .over()
    options: dict = {}
```

Location: `src/mountainash/expressions/core/expression_nodes/substrait/exn_window_function.py`

### OverNode (Extension)

```python
class OverNode(ExpressionNode):
    """Wraps any expression with window context (Polars .over() pattern)."""
    expression: ExpressionNode  # The inner expression tree
    window_spec: WindowSpec
```

Location: `src/mountainash/expressions/core/expression_nodes/extensions_mountainash/exn_ext_ma_over.py`

### WindowSpec (Shared value object)

```python
class WindowSpec(BaseModel, frozen=True):
    """Window specification: partitioning, ordering, and frame bounds."""
    partition_by: list[Any] = []            # Grouping expressions or column names
    order_by: list[SortField] = []          # Uses existing SortField from constants
    lower_bound: WindowBound | None = None  # Frame lower bound
    upper_bound: WindowBound | None = None  # Frame upper bound
```

### WindowBound

```python
class WindowBound(BaseModel, frozen=True):
    """Frame bound specification."""
    bound_type: WindowBoundType  # CURRENT_ROW, PRECEDING, FOLLOWING, UNBOUNDED_PRECEDING, UNBOUNDED_FOLLOWING
    offset: int | None = None    # For PRECEDING/FOLLOWING
```

```python
class WindowBoundType(str, Enum):
    CURRENT_ROW = "current_row"
    PRECEDING = "preceding"
    FOLLOWING = "following"
    UNBOUNDED_PRECEDING = "unbounded_preceding"
    UNBOUNDED_FOLLOWING = "unbounded_following"
```

Location for WindowSpec/WindowBound: `src/mountainash/expressions/core/expression_nodes/substrait/exn_window_spec.py`

WindowBoundType enum: `src/mountainash/core/constants.py`

## API Surface

### Flat window function methods (Substrait API builder)

New file: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py`

All methods build a `WindowFunctionNode` with the appropriate function key. The `window_spec` is left as `None` — it gets populated when `.over()` is called.

**Ranking functions:**
- `row_number()` → `WindowFunctionNode(SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER)`
- `rank()` → `WindowFunctionNode(SUBSTRAIT_ARITHMETIC_WINDOW.RANK)`
- `dense_rank()` → `WindowFunctionNode(SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK)`
- `percent_rank()` → `WindowFunctionNode(SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK)`
- `cume_dist()` → `WindowFunctionNode(SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST)`
- `ntile(n: int)` → `WindowFunctionNode(SUBSTRAIT_ARITHMETIC_WINDOW.NTILE, arguments=[LiteralNode(n)])`

**Value access functions:**
- `lead(offset: int = 1, default=None)` → `WindowFunctionNode(SUBSTRAIT_ARITHMETIC_WINDOW.LEAD, arguments=[self._node, LiteralNode(offset), ...])`
- `lag(offset: int = 1, default=None)` → same pattern with LAG key
- `first_value()` → `WindowFunctionNode(SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE, arguments=[self._node])`
- `last_value()` → `WindowFunctionNode(SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE, arguments=[self._node])`
- `nth_value(n: int)` → `WindowFunctionNode(SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE, arguments=[self._node, LiteralNode(n)])`

### `.over()` method (Extension, on BaseExpressionAPI)

```python
def over(
    self,
    *partition_by: str | ExpressionNode,
    order_by: str | list[str] | SortField | list[SortField] | None = None,
    rows_between: tuple[int | None, int | None] | None = None,
) -> BaseExpressionAPI:
```

Behavior:
- If `self._node` is a `WindowFunctionNode` with `window_spec is None`: populate its `window_spec` directly (no wrapping)
- Otherwise: wrap `self._node` in an `OverNode` with the constructed `WindowSpec`

`partition_by` accepts positional args (strings converted to FieldReferenceNode). `order_by` accepts strings or SortField instances. `rows_between` is sugar for constructing WindowBound objects: `(-3, 0)` → lower=Preceding(3), upper=CurrentRow. `None` in the tuple means unbounded.

## Visitor Handling

Two new visit methods on `UnifiedExpressionVisitor`:

### `visit_window_function(node: WindowFunctionNode)`

1. **Validate**: If `node.window_spec is None`, raise `ValueError("Window function requires .over() — e.g., col('x').rank().over('group')")`. Window functions without context are not compilable.
2. Compile arguments via recursive visit
3. Look up function key in registry → get backend method name
4. Call `getattr(backend, method_name)(*compiled_args)` (existing implementations)
5. Call `_apply_window_spec(result, node.window_spec)`
6. Return windowed native expression

### `visit_over(node: OverNode)`

1. Compile inner expression via `self.visit(node.expression)` → native expression
2. Call `_apply_window_spec(result, node.window_spec)`
3. Return windowed native expression

### `_apply_window_spec(expr, window_spec)` (shared helper)

1. Compile partition_by expressions via recursive visit
2. Compile order_by expressions
3. Convert bounds to backend-native format
4. Delegate to `backend.apply_window(expr, partition_by, order_by, lower, upper)`

## Backend Protocol Addition

New method on the expression system protocol:

```python
def apply_window(
    self,
    expr: SupportedExpressions,
    partition_by: list[SupportedExpressions],
    order_by: list[tuple[SupportedExpressions, bool]],  # (expr, descending)
    lower_bound: WindowBound | None,
    upper_bound: WindowBound | None,
) -> SupportedExpressions: ...
```

### Polars implementation

```python
def apply_window(self, expr, partition_by, order_by, lower_bound, upper_bound):
    # Polars .over() supports partition_by natively
    # order_by and frame bounds have limited support — sort inner expr if needed
    return expr.over(partition_by)
```

Note: Polars `.over()` doesn't natively support `order_by` or frame bounds in the same way SQL does. For order-dependent window functions (lag, lead, rank), the backend methods already handle ordering internally. Frame bounds are a known limitation — xfail tests where Polars can't express them.

### Ibis implementation

```python
def apply_window(self, expr, partition_by, order_by, lower_bound, upper_bound):
    window = ibis.window(
        group_by=partition_by,
        order_by=[col.desc() if desc else col for col, desc in order_by],
        preceding=lower_bound_to_ibis(lower_bound),
        following=upper_bound_to_ibis(upper_bound),
    )
    return expr.over(window)
```

### Narwhals implementation

```python
def apply_window(self, expr, partition_by, order_by, lower_bound, upper_bound):
    # Narwhals .over() supports partition_by and order_by
    # Frame bounds not supported
    order_by_args = [col for col, _ in order_by] if order_by else []
    return expr.over(*partition_by, order_by=order_by_args)
```

## Function Registry Entries

11 new entries in `register_all_functions()`:

```python
ExpressionFunctionDef(
    function_key=SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
    protocol_method=SubstraitWindowArithmeticExpressionSystemProtocol.row_number,
    substrait_uri=SubstraitExtension.WINDOW_ARITHMETIC,
    substrait_name="row_number",
)
# ... repeat for all 11 functions
```

## File Summary

### New files

| File | Layer | Purpose |
|------|-------|---------|
| `expression_nodes/substrait/exn_window_function.py` | Node | WindowFunctionNode |
| `expression_nodes/substrait/exn_window_spec.py` | Node | WindowSpec, WindowBound |
| `expression_nodes/extensions_mountainash/exn_ext_ma_over.py` | Node | OverNode |
| `expression_api/api_builders/substrait/api_bldr_window_arithmetic.py` | API | 11 flat methods |
| `expression_protocols/.../prtcl_expsys_apply_window.py` | Protocol | apply_window() protocol |
| `backends/.../polars/substrait/expsys_pl_apply_window.py` | Backend | Polars apply_window |
| `backends/.../ibis/substrait/expsys_ib_apply_window.py` | Backend | Ibis apply_window |
| `backends/.../narwhals/substrait/expsys_nw_apply_window.py` | Backend | Narwhals apply_window |

### Modified files

| File | Change |
|------|--------|
| `core/constants.py` | Add `WindowBoundType` enum |
| `expression_nodes/__init__.py` | Export new node types |
| `expression_api/api_base.py` or similar | Add `.over()` method |
| `expression_api/api_builders/substrait/__init__.py` | Register window builder |
| `unified_visitor/visitor.py` | Add `visit_window_function`, `visit_over`, `_apply_window_spec` |
| `function_mapping/definitions.py` | Add 11 registry entries |
| Backend composition `__init__.py` files | Include apply_window implementations |

## Testing

### Unit tests (~20)
- `test_window_nodes.py` — WindowFunctionNode, OverNode, WindowSpec, WindowBound construction
- `test_window_api_build.py` — API methods build correct AST shapes

### Cross-backend tests (~50-60, parametrized across Polars/Ibis/Narwhals)
- `test_window_ranking.py` — row_number, rank, dense_rank, percent_rank, cume_dist, ntile
- `test_window_value_access.py` — lead, lag, first_value, last_value, nth_value
- `test_window_over.py` — aggregations via .over() (sum, mean, count), order-dependent ops
- `test_window_frame.py` — rows_between bounds

### Known xfails
- Narwhals: row_number, rank, dense_rank, percent_rank, cume_dist, ntile, nth_value (NotImplementedError)
- Polars: frame bounds in `.over()` (limited support)
- Ibis/SQLite: certain window function limitations

### Integration test
- Full pipeline: ingress → transform → relation with windowed expression → output

**Estimated total: ~70-80 tests**

## API Examples

```python
import mountainash as ma

# Rank within groups
r = ma.relation(df).with_columns(
    ma.col("speed").rank().over("type").name.alias("speed_rank")
)

# Running average
r = ma.relation(df).with_columns(
    ma.col("price").mean().over("ticker", order_by="date", rows_between=(-5, 0))
        .name.alias("rolling_avg")
)

# Lag for change detection
r = ma.relation(df).with_columns(
    (ma.col("value") - ma.col("value").lag(1).over(partition_by="id", order_by="ts"))
        .name.alias("delta")
)

# Multiple window expressions
r = ma.relation(df).with_columns(
    ma.col("salary").mean().over("dept").name.alias("dept_avg"),
    ma.col("salary").row_number().over("dept", order_by="salary").name.alias("salary_rank"),
)
```
