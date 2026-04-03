# Ibis Reverse Operator Bug - Important Clarifications

## Key Finding: The Bug is Specific to `ibis.literal()` Wrapped Values

### What Works ✅

```python
import ibis

col = ibis._['x']

# Raw Python values work because Deferred has __radd__
5 + col          # ✅ Works - uses Deferred.__radd__(5)
100 - col        # ✅ Works - uses Deferred.__rsub__(100)
2 * col          # ✅ Works - uses Deferred.__rmul__(2)
100 / col        # ✅ Works - uses Deferred.__rtruediv__(100)
```

**Why it works:** `Deferred` class already has reverse operators!
```python
# In ibis.common.deferred.Deferred:
def __radd__(self, other):
    # Handles: raw_int + Deferred
    return Deferred(...)
```

### What Fails ❌

```python
import ibis

col = ibis._['x']
lit = ibis.literal(5)

# ibis.literal() wrapped values FAIL
lit + col        # ❌ Fails - IntegerScalar lacks __radd__
ibis.literal(100) - col   # ❌ Fails - IntegerScalar lacks __rsub__
ibis.literal(2) * col     # ❌ Fails - IntegerScalar lacks __rmul__
ibis.literal(100) / col   # ❌ Fails - IntegerScalar lacks __rtruediv__
```

**Why it fails:** `IntegerScalar` (and other `ir.Expr` types) lack reverse operators!

---

## Why This Bug Matters (Even Though Raw Ints Work)

### Expression Builders Must Use `ibis.literal()`

When building expressions programmatically (like in `mountainash-expressions`), you **must** wrap raw values in `ibis.literal()` to ensure proper type handling:

```python
# In an expression builder:
def build_expression(left_value, operator, right_column):
    # We can't just use raw Python values
    left_expr = ibis.literal(left_value)  # Must wrap for type safety
    right_expr = ibis._[right_column]

    if operator == '+':
        return left_expr + right_expr  # ❌ FAILS!
```

**Why we need `ibis.literal()`:**
- Type inference (int vs float vs string)
- NULL handling
- Consistent SQL generation
- Backend compatibility

**The problem:** Once wrapped, reverse operators stop working!

---

## Reverse Operators ARE Needed for Non-Commutative Operations

### Common Misconception

> "Reverse operators are for commutative operations like addition and multiplication."

**❌ FALSE!** Reverse operators are for **Python's operator resolution protocol**, not commutativity.

### How Python Resolves Operators

When Python evaluates `a - b`:

1. Try `a.__sub__(b)`
2. If that returns `NotImplemented`, try `b.__rsub__(a)`
3. If that also fails, raise `TypeError`

### Example: Subtraction (Non-Commutative)

```python
# Subtraction is NOT commutative: 5 - 10 ≠ 10 - 5

col = ibis._['x']  # Contains [10, 20, 30]

# Forward operator
col - 5
# Uses: Deferred.__sub__(5)
# Computes: [10-5, 20-5, 30-5] = [5, 15, 25]

# Reverse operator
5 - col
# Uses: Deferred.__rsub__(5)
# Computes: [5-10, 5-20, 5-30] = [-5, -15, -25]
# NOT the same as col - 5!
```

### The `__rsub__` Implementation

```python
def __rsub__(self, other):
    """Handle other - self (NOT self - other)"""
    # This computes: other - self
    # When called as: 5 - col
    # Computes: 5 - col (correct!)
    # NOT: col - 5 (wrong!)
    return other - self
```

**Key insight:** `__rsub__(self, other)` means "compute `other - self`", which gives the correct order for the expression.

---

## Verification: Non-Commutative Operators Work Correctly

### Test with Real Data

```python
import ibis
import polars as pl

conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10, 20, 30]})
table = conn.create_table('test', df, overwrite=True)

# Test subtraction
expr1 = ibis._['x'] - 5
result1 = table.select(expr1.name('r1'))
print(result1['r1'].execute().tolist())
# Output: [5, 15, 25]  (10-5, 20-5, 30-5)

expr2 = 5 - ibis._['x']
result2 = table.select(expr2.name('r2'))
print(result2['r2'].execute().tolist())
# Output: [-5, -15, -25]  (5-10, 5-20, 5-30)

# ✅ Different results - correctly handles non-commutativity!
```

### Test Division

```python
# Test division
expr1 = ibis._['x'] / 2
result1 = table.select(expr1.name('r1'))
print(result1['r1'].execute().tolist())
# Output: [5.0, 10.0, 15.0]  (10/2, 20/2, 30/2)

expr2 = 100 / ibis._['x']
result2 = table.select(expr2.name('r2'))
print(result2['r2'].execute().tolist())
# Output: [10.0, 5.0, 3.333...]  (100/10, 100/20, 100/30)

# ✅ Different results - correctly handles non-commutativity!
```

---

## Complete Test Results

### Raw Python Values (Work)

| Expression | Calls | Result | Status |
|------------|-------|--------|--------|
| `5 + col` | `Deferred.__radd__(5)` | `5 + col` | ✅ |
| `5 - col` | `Deferred.__rsub__(5)` | `5 - col` | ✅ |
| `5 * col` | `Deferred.__rmul__(5)` | `5 * col` | ✅ |
| `100 / col` | `Deferred.__rtruediv__(100)` | `100 / col` | ✅ |

### `ibis.literal()` Wrapped Values (Fail)

| Expression | Calls | Result | Status |
|------------|-------|--------|--------|
| `lit(5) + col` | `IntegerScalar.__radd__`? | ERROR | ❌ |
| `lit(5) - col` | `IntegerScalar.__rsub__`? | ERROR | ❌ |
| `lit(5) * col` | `IntegerScalar.__rmul__`? | ERROR | ❌ |
| `lit(100) / col` | `IntegerScalar.__rtruediv__`? | ERROR | ❌ |

**Error:** `InputTypeError: Unable to infer datatype of value _['x']`

---

## Why Both `Deferred` and `ir.Expr` Need Reverse Operators

### Current State

```python
# ✅ Deferred has reverse operators
class Deferred:
    def __radd__(self, other): ...  # ✅ Exists
    def __rsub__(self, other): ...  # ✅ Exists
    # etc.

# ❌ NumericValue lacks reverse operators
class NumericValue(Value):
    def __add__(self, other): ...   # ✅ Exists
    def __sub__(self, other): ...   # ✅ Exists
    # ❌ Missing __radd__, __rsub__, etc.
```

### The Problem

When you do `ibis.literal(5) + ibis._['x']`:

1. Python tries `IntegerScalar.__add__(Deferred)`
2. `IntegerScalar.__add__` doesn't know how to handle `Deferred`
3. Returns `NotImplemented`
4. Python tries `Deferred.__radd__(IntegerScalar)`
5. **But `Deferred` doesn't have `__radd__` for handling `ir.Expr` on left!**
6. Error!

### The Solution

Add reverse operators to `NumericValue` that check for `Deferred`:

```python
class NumericValue(Value):
    def __radd__(self, other):
        if isinstance(other, Deferred):
            # Let Deferred handle it
            return other.__add__(self)
        return _binop(ops.Add, other, self)

    def __rsub__(self, other):
        if isinstance(other, Deferred):
            # Computes: other - self (correct order!)
            return other.__sub__(self)
        return _binop(ops.Subtract, other, self)
```

---

## Updated Documentation Impact

### Reproducer Script

The script should clarify:
- ✅ Raw Python values work
- ❌ `ibis.literal()` wrapped values fail
- 🎯 This is the bug we're fixing

### Issue Description

Should emphasize:
- Expression builders need `ibis.literal()`
- Raw values work, but that's not enough
- Affects programmatic expression generation

### PR Description

Should explain:
- Reverse operators ≠ commutative operators
- They handle operator resolution protocol
- Correctly preserve order for non-commutative ops

---

## Test Case: Verify Order Preservation

Add this test to ensure reverse operators preserve order:

```python
def test_reverse_operators_preserve_order():
    """Verify that reverse operators compute 'other op self', not 'self op other'."""
    import polars as pl

    conn = ibis.polars.connect()
    df = pl.DataFrame({'x': [10]})
    table = conn.create_table('test', df, overwrite=True)

    # Test subtraction order
    expr = ibis.literal(5) - ibis._['x']  # Should be 5 - 10 = -5
    result = table.select(expr.name('result'))
    value = result['result'].execute().tolist()[0]

    assert value == -5, f"Expected -5 (5 - 10), got {value}"

    # Test division order
    expr = ibis.literal(100) - ibis._['x']  # Should be 100 / 10 = 10.0
    result = table.select(expr.name('result'))
    value = result['result'].execute().tolist()[0]

    assert value == 10.0, f"Expected 10.0 (100 / 10), got {value}"
```

---

## Summary

### Q1: Do expressions pass when the number is not a literal?

**A:** YES! `5 + ibis._['x']` works because `Deferred` already has `__radd__`.

**But:** Expression builders must use `ibis.literal()`, which breaks reverse operators.

### Q2: Do reverse operators make sense for non-commutative operations?

**A:** ABSOLUTELY YES! Reverse operators are about **operator resolution**, not commutativity.

- `__rsub__(self, other)` computes `other - self` (correct order)
- `__rtruediv__(self, other)` computes `other / self` (correct order)
- They preserve the intended mathematical operation

### The Real Bug

**Not:** "Reverse operators don't work at all"
**But:** "Reverse operators don't work for `ibis.literal()` wrapped values"

**Impact:** Breaks expression builders that need type-safe literal wrapping

---

## Updated Reproducer

The reproducer should test BOTH:

1. Raw Python values (should work) ✅
2. `ibis.literal()` wrapped values (should fail, then pass after fix) ❌→✅

This clearly shows the bug is specific to the `ir.Expr` types, not `Deferred`.
