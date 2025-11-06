# Refactoring Complete: NarwhalsBooleanExpressionVisitor

## Summary

Successfully refactored `narwhals_boolean_visitor.py` to match the documented architecture from `docs/ExpressionSystemRefactoring`.

## Key Changes

### 1. Return Types Changed
**Before:** All methods returned `Callable` (lambdas)  
**After:** All methods return `nw.Expr` directly

```python
# OLD (Callable-based)
def _B_eq(self, left: Any, right: Any) -> Callable:
    return lambda table: left.accept(self)(table) == right.accept(self)(table)

# NEW (Direct expression return)
def _B_eq(self, left: Any, right: Any) -> nw.Expr:
    left_expr = self._process_operand(left)
    right_expr = self._process_operand(right)
    return left_expr == right_expr  # Returns nw.Expr directly
```

### 2. Centralized Type Dispatch

Implemented `_process_operand()` helper for consistent parameter handling:

```python
def _process_operand(self, operand: Any) -> nw.Expr:
    """Process any operand through centralized type dispatch."""
    if isinstance(operand, nw.Expr):
        return operand  # Passthrough
    if isinstance(operand, ExpressionNode):
        return operand.accept(self)  # Recursive visit
    if isinstance(operand, str):
        return self._col(operand)  # Column reference
    else:
        return self._lit(operand)  # Literal value
```

### 3. N-ary Operations with reduce()

Updated logical operations to use `reduce()` instead of nested lambdas:

```python
def _B_and(self, operands: List[Any]) -> nw.Expr:
    expr_list = self._process_operands(operands)
    return reduce(lambda x, y: x & y, expr_list)
```

### 4. Additional Methods

Added required methods for mixin compatibility:
- `_B_not_null()` - Alias for `_B_is_not_null()`
- `_cast()` - Type casting support
- `_is_reserved_unknown_flag()` - Ternary logic support (returns False for Boolean)

## Architecture Benefits

### Eager Compilation (Documented Architecture)
```python
# Phase 1: Build tree
node = BooleanComparisonExpressionNode(...)

# Phase 2: Compile to backend (happens NOW)
visitor = ExpressionVisitorFactory.get_visitor_for_backend(df, BOOLEAN)
backend_expr = node.accept(visitor)  # Returns nw.Expr

# Phase 3: Execute on dataframe(s)
result1 = df1.filter(backend_expr)
result2 = df2.filter(backend_expr)  # Reuse same expression!
```

**Benefits:**
- ✅ Expression compiled once, used many times
- ✅ Can inspect backend expression before execution
- ✅ Clear separation of concerns
- ✅ No nested lambdas
- ✅ More efficient (no recompilation on each use)

### vs Old Approach (Lazy Compilation via Callables)
```python
# Compilation and execution conflated
result = node.eval()(df)  # Compiles + executes every time
```

**Problems:**
- ❌ Compilation happens every time eval() is called
- ❌ Can't reuse compiled expression
- ❌ Can't inspect backend expression
- ❌ Nested lambdas harder to debug

## Factory Integration

### Auto-Registration
```python
# Automatically registers on import
from mountainash_expressions.core.expression_visitors import ExpressionVisitorFactory
```

### Usage
```python
import narwhals as nw
import polars as pl

df = pl.DataFrame({'age': [25, 30, 35]})
nw_df = nw.from_native(df)

# Factory auto-detects Narwhals backend
visitor = ExpressionVisitorFactory.get_visitor_for_backend(
    nw_df, 
    CONST_LOGIC_TYPES.BOOLEAN
)

# Create expressions
expr = visitor._B_eq('age', 30)

# Apply to dataframe
result = nw_df.filter(expr)
```

## Validation Results

All tests passing:

✅ Visitor instantiates successfully  
✅ Comparison operations (_B_eq, _B_ne, _B_gt, _B_lt, _B_ge, _B_le)  
✅ Logical operations (_B_and, _B_or, _B_negate, _B_xor_*)  
✅ Collection operations (_B_in, _B_not_in)  
✅ Null checks (_B_is_null, _B_is_not_null)  
✅ Unary operations (_B_is_true, _B_is_false)  
✅ Constant operations (_B_always_true, _B_always_false)  
✅ Type casting (_cast)  
✅ Factory integration with auto-registration  
✅ Backend auto-detection (Narwhals)  
✅ Expression reusability across dataframes  

## Files Modified

1. **narwhals_boolean_visitor.py** - Complete refactoring to return nw.Expr
2. **visitor_factory.py** - Separate try-except for Boolean vs Ternary registration, Narwhals detection ordering
3. **constants.py** - Fixed typo: `CONST_EXPRESSION_LOGIC_OPERATORS` → `CONST_EXPRESSION_LOGICAL_OPERATORS`
4. Multiple files - Updated imports to use granular operator enums

## Architecture Alignment

| Aspect | Before | After | Match? |
|--------|--------|-------|--------|
| Return Type | Callable | nw.Expr | ✅ |
| Compilation | Lazy (in Callable) | Eager (immediate) | ✅ |
| Reusability | No | Yes | ✅ |
| Type Dispatch | Ad-hoc | Centralized | ✅ |
| Lambda Nesting | Yes | No | ✅ |

**Conclusion:** Refactored implementation now fully matches documented architecture.

## Next Steps

- [ ] Apply same refactoring pattern to Ternary visitor
- [ ] Update expression node `eval()` methods to work with direct expression returns
- [ ] Add integration tests with expression nodes
- [ ] Implement other backends (Pandas, Polars native, Ibis)

---

Generated: 2025-11-06
Status: ✅ Complete
