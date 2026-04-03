# Ibis Reverse Operator Limitation - Workaround Implemented

## Summary

**Status**: ⚠️ Known upstream Ibis bug - Warning system implemented  
**Affected versions**: Ibis <= 11.0.0 (and possibly later)  
**Impact**: Expressions like `5 + ma.col("x")` fail with Ibis backends  
**Solution**: Use `ma.col("x") + 5` instead (column on left)

## The Issue

Ibis has a bug where reverse arithmetic operators fail when a literal value is on the left side and a deferred column reference is on the right:

```python
import ibis

# This works ✅
ibis._['x'] + ibis.literal(5)  

# This fails ❌
ibis.literal(5) + ibis._['x']
# InputTypeError: Unable to infer datatype of value _['x'] 
# with type <class 'ibis.common.deferred.Deferred'>
```

### Affected Operations

All arithmetic operators when literal is on left:
- `5 + ma.col("x")` → `__radd__`
- `100 - ma.col("x")` → `__rsub__`
- `2 * ma.col("x")` → `__rmul__`
- `100 / ma.col("x")` → `__rtruediv__`
- `100 % ma.col("x")` → `__rmod__`
- `2 ** ma.col("x")` → `__rpow__`
- `100 // ma.col("x")` → `__rfloordiv__`

## Our Workaround

Instead of implementing a fragile hack, we've added **warning system** that alerts users when this pattern is detected:

### Location

`src/mountainash_expressions/backends/ibis/expression_system/ibis_expression_system.py`

### Implementation

```python
def _warn_if_reverse_operator_bug(self, left: Any, right: Any, operation: str) -> None:
    """Warn if encountering known Ibis bug with reverse operators."""
    is_left_scalar = isinstance(left, (ir.IntegerScalar, ir.FloatingScalar, ir.BooleanScalar, ir.Scalar))
    is_right_deferred = isinstance(right, Deferred)
    
    if is_left_scalar and is_right_deferred:
        warnings.warn(
            f"Detected potential Ibis reverse operator bug: {operation} with literal on left "
            f"and column reference on right may fail with InputTypeError. "
            f"This is a known Ibis bug affecting versions <= 11.0.0. "
            f"Consider rewriting as 'ma.col(x) {operation} value' instead of 'value {operation} ma.col(x)'. "
            f"See docs/_IBIS_REVERSE_OPERATOR_BUG_FIX.md for details.",
            UserWarning,
            stacklevel=4
        )
```

### Warning Output Example

```python
UserWarning: Detected potential Ibis reverse operator bug: + with literal on left 
and column reference on right may fail with InputTypeError. This is a known Ibis bug 
affecting versions <= 11.0.0. Consider rewriting as 'ma.col(x) + value' instead of 
'value + ma.col(x)'. See docs/_IBIS_REVERSE_OPERATOR_BUG_FIX.md for details.
```

## User Guidance

### If You Encounter This Warning

**Option 1: Rewrite the expression (Recommended)**
```python
# Instead of this:
expr = 5 + ma.col("price")

# Write this:
expr = ma.col("price") + 5
```

**Option 2: Switch to a different backend**
```python
# Use Polars, Pandas, or Narwhals instead of Ibis
# All other backends support reverse operators correctly
```

**Option 3: Suppress warnings (Not recommended)**
```python
import warnings
warnings.filterwarnings('ignore', message='.*Ibis reverse operator bug.*')
```

## Test Results

Running `tests/cross_backend/test_expression_builder_api.py::TestReverseArithmeticOperators`:

- ✅ **Polars**: All reverse operators work
- ✅ **Pandas**: All reverse operators work  
- ✅ **Narwhals**: All reverse operators work
- ❌ **Ibis-Polars**: All reverse operators fail (with helpful warnings)
- ❌ **Ibis-SQLite**: All reverse operators fail (with helpful warnings)

## Upstream Issue

This is documented in Ibis:
- See: `docs/_IBIS_REVERSE_OPERATOR_BUG_FIX.md` for detailed analysis
- See: `docs/ibis_fix_verification.py` for reproduction script

To verify the bug still exists:
```bash
python docs/ibis_fix_verification.py
```

## Why Not Implement a Workaround?

We considered implementing automatic operand swapping for commutative operations, but decided against it because:

1. **Fragility**: Would require complex detection logic and edge case handling
2. **Non-commutative ops**: Can't safely swap operands for `-`, `/`, `%`, `**`, `//`
3. **Upstream responsibility**: This is an Ibis bug that should be fixed upstream
4. **Transparency**: Users should be aware of backend limitations
5. **Maintenance burden**: Workarounds add technical debt

## Future

When Ibis fixes this bug upstream:
1. Remove the warning system
2. Update this documentation
3. Verify all tests pass
4. Update version constraints in `pyproject.toml`

## References

- Full bug analysis: `docs/_IBIS_REVERSE_OPERATOR_BUG_FIX.md`
- Verification script: `docs/ibis_fix_verification.py`
- Ibis project: https://github.com/ibis-project/ibis
