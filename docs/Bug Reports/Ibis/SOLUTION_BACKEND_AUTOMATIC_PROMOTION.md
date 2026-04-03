# Solution: Automatic Type Promotion in Polars Backend

## The Right Place to Fix This

**User's insight:** Don't make users cast manually. **Automatically upcast narrow integers in the backend translation layer.**

---

## Where The Fix Goes

### Current Code Structure

**File:** `ibis/backends/polars/compiler.py`

```python
# Line 1383: Generic binary operations (*, +, -, /, etc.)
@translate.register(ops.Binary)
def binop(op, **kw):
    left = translate(op.left, **kw)
    right = translate(op.right, **kw)
    func = _binops.get(type(op))
    if func is None:
        raise com.OperationNotDefinedError(f"{type(op).__name__} not supported")
    return func(left, right)  # ← operator.mul, operator.add, etc.

# Line 766: Power operation
@translate.register(ops.Power)
def power(op, **kw):
    left = translate(op.left, **kw)
    right = translate(op.right, **kw)
    return left.pow(right)  # ← Just calls .pow()
```

**Problem:** No type promotion before arithmetic!

---

## The Fix

### Helper Function: Promote Narrow Integers

```python
def _promote_for_arithmetic(expr: pl.Expr, min_width: int = 32) -> pl.Expr:
    """
    Promote narrow integer types for safe arithmetic.

    Parameters:
    -----------
    expr : pl.Expr
        The Polars expression to potentially promote
    min_width : int
        Minimum bit width (default 32 = Int32)

    Returns:
    --------
    pl.Expr
        Original expression or promoted version

    Examples:
    ---------
    # Int8 → Int32
    _promote_for_arithmetic(pl.lit(2, dtype=pl.Int8))

    # Int64 → Int64 (unchanged)
    _promote_for_arithmetic(pl.col('x'))  # if x is int64
    """
    # Get the dtype metadata if available
    # Note: Polars expressions don't always have dtype until evaluated
    # We need to handle this at translation time

    # For now, we can use a simple heuristic:
    # If it's a literal with explicit narrow type, cast it
    # This requires checking the Ibis operation type

    return expr  # Placeholder - see below for full implementation


def _maybe_promote_operand(op_node, translated_expr: pl.Expr) -> pl.Expr:
    """
    Check if the operand is a narrow integer literal and promote it.

    Parameters:
    -----------
    op_node : ops.Node
        The Ibis operation node (before translation)
    translated_expr : pl.Expr
        The translated Polars expression

    Returns:
    --------
    pl.Expr
        Promoted expression if needed
    """
    # Check if it's a literal with narrow integer type
    if isinstance(op_node, ops.Literal):
        dtype = op_node.dtype
        if dtype.is_integer() and dtype.bitwidth < 32:
            # Promote to Int32 (minimum safe width)
            return translated_expr.cast(pl.Int32)

    return translated_expr
```

### Modified Binary Operations

```python
@translate.register(ops.Binary)
def binop(op, **kw):
    # Translate operands
    left = translate(op.left, **kw)
    right = translate(op.right, **kw)

    # Promote narrow integer literals for arithmetic operations
    if isinstance(op, (ops.Multiply, ops.Add, ops.Subtract, ops.Divide)):
        left = _maybe_promote_operand(op.left, left)
        right = _maybe_promote_operand(op.right, right)

    # Apply the operation
    func = _binops.get(type(op))
    if func is None:
        raise com.OperationNotDefinedError(f"{type(op).__name__} not supported")
    return func(left, right)
```

### Modified Power Operation

```python
@translate.register(ops.Power)
def power(op, **kw):
    left = translate(op.left, **kw)
    right = translate(op.right, **kw)

    # Promote narrow integers (power has higher overflow risk)
    left = _maybe_promote_operand(op.left, left)
    right = _maybe_promote_operand(op.right, right)

    return left.pow(right)
```

---

## What This Achieves

### Before (Current Behavior)

```python
# User code
ibis.literal(100) * table.x

# Ibis stores
Literal(value=100, dtype=int8)  ← Efficient storage ✅

# Polars backend translates
100.strict_cast(Int8)  ← Narrow type passed through ❌

# Result
Overflow in Int8 ❌
```

### After (With Automatic Promotion)

```python
# User code
ibis.literal(100) * table.x

# Ibis stores
Literal(value=100, dtype=int8)  ← Efficient storage ✅

# Polars backend translates with promotion
_maybe_promote_operand() checks:
  - Is it a literal? Yes
  - Is it narrow integer (int8/int16)? Yes
  - Promote to Int32 ✅

# Polars receives
100.strict_cast(Int32) * col('x')  ← Safe type ✅

# Result
No overflow ✅
```

---

## Benefits

### User Experience

✅ **No manual casting required**
```python
# Just works!
ibis.literal(100) * table.x
```

✅ **No need to learn workarounds**
```python
# Don't need this anymore:
ibis.literal(100).cast('int64') * table.x
```

✅ **Works with raw numbers too**
```python
# Also works (raw numbers become literals):
100 * table.x
```

### Technical Benefits

✅ **Memory efficient storage** (int8 for literals)
✅ **Safe calculations** (promoted to int32/int64)
✅ **Backend-specific solution** (doesn't affect other backends)
✅ **Transparent to users** (happens automatically)
✅ **Localized fix** (only in Polars backend translator)

---

## Implementation Details

### Which Operations Need Promotion?

**High Priority (overflow risk):**
- `ops.Multiply` - Can overflow easily
- `ops.Power` - Very high overflow risk
- `ops.Add` - Can overflow with repeated additions
- `ops.Subtract` - Can overflow

**Medium Priority:**
- `ops.Divide` - Less risk but good to be consistent
- `ops.FloorDivide` - Similar to divide
- `ops.Modulus` - Can have unexpected behavior with narrow types

**Low Priority (comparison operations):**
- `ops.Equals`, `ops.NotEquals`, etc. - Comparisons handle mixed types well

### What About Columns?

**Columns should NOT be promoted automatically!**

```python
def _maybe_promote_operand(op_node, translated_expr: pl.Expr) -> pl.Expr:
    # Only promote LITERALS, not columns
    if isinstance(op_node, ops.Literal):
        dtype = op_node.dtype
        if dtype.is_integer() and dtype.bitwidth < 32:
            return translated_expr.cast(pl.Int32)

    # Columns keep their original types (from DataFrame schema)
    return translated_expr
```

**Why?**
- Columns reflect the user's explicit schema choice
- Optimized DataFrames (int8 columns) are intentional
- Users might want to keep narrow types for memory
- Only the **literals** are the problem (aggressive inference)

### Minimum Width: Int32 or Int64?

**Option 1: Int32 (Recommended)**
```python
return translated_expr.cast(pl.Int32)
```

**Pros:**
- Matches SQL `INT` type
- Prevents most overflow cases
- Smaller than int64
- Balances safety and efficiency

**Cons:**
- Can still overflow at 2^31 (2.1 billion)

**Option 2: Int64**
```python
return translated_expr.cast(pl.Int64)
```

**Pros:**
- Maximum safety
- Matches DataFrame defaults
- Consistent with Pandas/Polars column types

**Cons:**
- More memory during calculations
- Might be overkill for small values

**Recommendation:** Start with Int32, can increase to Int64 if needed.

---

## Testing Strategy

### Test Cases

```python
# Test 1: Multiplication with narrow column
df = pl.DataFrame({'x': pl.Series([100], dtype=pl.Int8)})
result = (ibis.literal(100) * table.x).execute()
assert result[0] == 10000  # Should work now!

# Test 2: Power operation
result = (ibis.literal(2) ** table.y).execute()
assert result[0] == 1024  # Should work now!

# Test 3: Raw numbers
result = (100 * table.x).execute()
assert result[0] == 10000  # Should work now!

# Test 4: Columns not promoted
# User's int8 columns should stay int8 (not promoted)
result = (table.x * table.y).execute()
# Should respect user's schema choice

# Test 5: Mixed operations
result = (ibis.literal(10) * table.x + ibis.literal(5)).execute()
assert result[0] == 1005  # Should work now!
```

---

## Comparison with Other Approaches

| Approach | Storage | Calculation | User Action | Scope |
|----------|---------|-------------|-------------|-------|
| **Change literal inference to int64** | int64 ❌ | Safe ✅ | None ✅ | All backends |
| **Don't pass dtype to Polars** | int8 ✅ | Partial ⚠️ | None ✅ | Polars only |
| **Backend automatic promotion (THIS)** | int8 ✅ | Safe ✅ | None ✅ | Polars only |
| **User manual casting** | int8 ✅ | Safe ✅ | Required ❌ | All backends |

**This approach wins on all criteria!**

---

## Implementation Steps

### Phase 1: Core Promotion Logic

1. Add `_maybe_promote_operand()` helper function
2. Modify `@translate.register(ops.Power)` to use promotion
3. Test power operations

### Phase 2: Binary Operations

1. Modify `@translate.register(ops.Binary)` to use promotion
2. Test multiplication, addition, subtraction
3. Test with Parquet files (real-world scenario)

### Phase 3: Edge Cases

1. Test with different column types (int8, int16, int32, int64)
2. Test mixed operations (literal + column + literal)
3. Test with casting operations
4. Test backward compatibility

---

## Example PR Description

```
Fix: Automatic type promotion for narrow integer literals in Polars backend

Problem:
- Ibis infers int8 for small literals (memory efficient)
- But int8 causes overflow in arithmetic operations
- Users must manually cast: literal(100).cast('int64')

Solution:
- Automatically promote int8/int16 literals to int32 during translation
- Only affects literals (not columns - respects user schema)
- Happens transparently in Polars backend translator
- Users don't need to change their code

Changes:
- Add _maybe_promote_operand() helper
- Modify binop() to promote before arithmetic
- Modify power() to promote before exponentiation

Result:
- literal(100) * table.x now works correctly
- No user action required
- Backward compatible (only fixes broken cases)
```

---

## Conclusion

**This is the right fix because:**

1. ✅ **Efficient storage** - Keeps int8 for literals
2. ✅ **Safe calculations** - Promotes to int32 for arithmetic
3. ✅ **Zero user burden** - Automatic and transparent
4. ✅ **Backend-specific** - Doesn't affect other backends
5. ✅ **Respects user intent** - Columns keep their types
6. ✅ **Localized change** - Only modifies Polars translator
7. ✅ **Matches language semantics** - Like C, Java, Python promotion

**This is exactly what you suggested** - promoting types at runtime in the backend, not at storage time or requiring user action!
