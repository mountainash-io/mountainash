# Polars vs Ibis: Operator Implementation Analysis

## Executive Summary

**Polars works** because forward operators (`__add__`, etc.) accept and handle `Expr` objects
**Ibis fails** because forward operators raise `InputTypeError` when given `Deferred`, which is NOT caught by `_binop`

---

## How Polars Implements It

### Polars Pattern: Forward Operators Handle Everything

```python
class Expr:
    def __add__(self, other: IntoExpr) -> Expr:
        other = parse_into_expression(other, str_as_lit=True)
        return self._from_pyexpr(self._pyexpr + other)
```

**Key function: `parse_into_expression`**

```python
def parse_into_expression(input: IntoExpr, ...) -> PyExpr:
    if isinstance(input, pl.Expr):
        expr = input  # ✅ Already an Expr, use as-is!
    elif isinstance(input, str) and not str_as_lit:
        expr = F.col(input)
    else:
        expr = F.lit(input)

    return expr._pyexpr
```

### What This Means

When you do `pl.lit(5) + pl.col('x')`:

1. Python calls `pl.lit(5).__add__(pl.col('x'))`
2. `parse_into_expression(pl.col('x'))` is called
3. Sees it's already an `Expr`, returns it as-is
4. Performs addition at PyExpr level
5. ✅ **Works!**

When you do `5 + pl.col('x')`:

1. Python tries `(5).__add__(pl.col('x'))` → returns `NotImplemented`
2. Python falls back to `pl.col('x').__radd__(5)`
3. `parse_into_expression(5)` converts to `pl.lit(5)`
4. Performs addition at PyExpr level
5. ✅ **Works!**

**Result:** Both paths produce identical expressions: `[(dyn int: 5) + (col("x"))]`

---

## How Ibis Implements It (and Why It Fails)

### Ibis Pattern: Forward Operators Don't Handle Deferred

```python
class NumericValue(Value):
    def __add__(self, other: NumericValue) -> NumericValue:
        """Add `self` with `other`."""
        return _binop(ops.Add, self, other)
```

**Key function: `_binop`**

```python
def _binop(op_class: type[ops.Binary], left: ir.Value, right: ir.Value) -> ir.Value:
    try:
        node = op_class(left, right)
    except (ValidationError, NotImplementedError):
        return NotImplemented  # ✅ Would let Python try __radd__
    else:
        return node.to_expr()
```

### The Problem

When `ops.Add(literal, deferred)` is constructed, it raises `InputTypeError`:

```
InputTypeError: Unable to infer datatype of value _['x'] with type <class 'ibis.common.deferred.Deferred'>
```

**But `InputTypeError` is NOT caught by `_binop`!**

### Exception Hierarchy

```python
ValidationError (from ibis.common.annotations)
  ├─ Exception
  └─ BaseException

InputTypeError (from ibis.common.exceptions)
  ├─ IbisTypeError
  │   └─ TypeError
  ├─ IbisError
  ├─ Exception
  └─ BaseException
```

**`InputTypeError` is NOT a subclass of `ValidationError`!**

So `_binop` doesn't catch it, and the exception propagates up instead of returning `NotImplemented`.

### What This Means

When you do `ibis.literal(5) + ibis._['x']`:

1. Python calls `literal(5).__add__(ibis._['x'])`
2. `_binop(ops.Add, literal(5), ibis._['x'])` is called
3. `ops.Add(literal(5), ibis._['x'])` tries to construct node
4. Raises `InputTypeError` (Deferred not recognized)
5. `_binop` doesn't catch `InputTypeError` ❌
6. Exception propagates to user
7. ❌ **Fails!**

When you do `5 + ibis._['x']`:

1. Python tries `(5).__add__(ibis._['x'])` → returns `NotImplemented`
2. Python falls back to `ibis._['x'].__radd__(5)` ✅
3. `Deferred` HAS `__radd__` and handles raw values
4. ✅ **Works!**

---

## The Fix Options

### Option 1: Make `_binop` Catch `InputTypeError` (Minimal Change)

```python
def _binop(op_class: type[ops.Binary], left: ir.Value, right: ir.Value) -> ir.Value:
    try:
        node = op_class(left, right)
    except (ValidationError, NotImplementedError, InputTypeError):  # ✅ Add InputTypeError
        return NotImplemented
    else:
        return node.to_expr()
```

**Pros:**
- Minimal code change (one line!)
- Fixes all operators at once
- Lets Python's operator resolution work as designed

**Cons:**
- Might hide other legitimate `InputTypeError` issues
- Doesn't follow Polars' explicit pattern

---

### Option 2: Add Type Checking to Forward Operators (Polars-like)

```python
from ibis.common.deferred import Deferred

class NumericValue(Value):
    def __add__(self, other):
        # Check if other is Deferred - let it handle via __radd__
        if isinstance(other, Deferred):
            return NotImplemented
        return _binop(ops.Add, self, other)
```

**Pros:**
- Explicit and clear
- Follows Polars pattern of checking types
- Doesn't hide errors

**Cons:**
- Need to add to every forward operator
- More code changes

---

### Option 3: Add Reverse Operators to NumericValue (Original Plan)

```python
from ibis.common.deferred import Deferred

class NumericValue(Value):
    def __radd__(self, other):
        if isinstance(other, Deferred):
            return other.__add__(self)
        return _binop(ops.Add, other, self)
```

**Pros:**
- Most explicit about handling reversed operations
- Clear delegation pattern
- BooleanScalar already works (might have these)

**Cons:**
- Need to add 7+ reverse operators
- More code than Option 1

---

## Recommendation

**Use Option 1** (catch `InputTypeError` and `SignatureValidationError` in `_binop`) because:

1. ✅ One-line fix
2. ✅ Fixes all numeric and boolean operators (arithmetic + logical + comparison)
3. ✅ Lets Python's operator resolution protocol work correctly
4. ✅ `Deferred` already has all reverse operators implemented
5. ✅ Most Pythonic solution
6. ✅ **Restores documented contract of `_binop`**

### The Fix

```python
# In ibis/expr/types/generic.py, line ~3168
except (ValidationError, NotImplementedError, com.InputTypeError, SignatureValidationError):
    return NotImplemented
```

## The `_binop` Contract Violation

The `_binop` docstring explicitly states:

> "But returns NotImplemented if we aren't sure"

And provides this example:

```python
>>> _binop(ops.Equals, 5, ibis.table({"a": "int"}))
NotImplemented
```

When given an **unbound table reference**, it correctly returns `NotImplemented`.

### The Inconsistency

```python
# Unbound table reference
_binop(ops.Equals, 5, ibis.table({"a": "int"}))
# → NotImplemented ✅ (follows contract)

# Unbound column reference
_binop(ops.Add, ibis.literal(5), ibis._['x'])
# → InputTypeError ❌ (violates contract)
```

**Both are unbound references, but handled differently!**

This is not about adding new functionality - it's about **fixing a bug** where `_binop` doesn't honor its documented contract.

### The Fix Restores Consistency

Adding `InputTypeError` to the exception handler makes `_binop` behave consistently with its documentation:

```python
except (ValidationError, NotImplementedError, InputTypeError):
    return NotImplemented  # ✅ "if we aren't sure"
```

Now both unbound references return `NotImplemented`, letting Python's operator resolution work correctly.

---

## Test Results: Before and After the Fix

### Before Fix
- **Ibis failures: 11/39** ❌
- **Polars failures: 0/39** ✅

Failed operations:
- IntegerScalar: 7 operators (all `lit op col` patterns)
- FloatingScalar: 3 operators (all `lit op col` patterns)
- StringScalar: 1 operator (`lit + col`)

### After Fix (One-Line Change)
- **Ibis failures: 1/39** ❌
- **Polars failures: 0/39** ✅

**Fixed:** 10 out of 11 failures! 🎉

**Success rate: 97.4%**

Remaining failure:
- StringScalar: `lit + col` (different implementation pattern - doesn't use `_binop`)

All numeric and boolean operators now work correctly:

```python
# IntegerScalar - ALL FIXED ✅
ibis.literal(5) + ibis._['x']    # → (<scalar[int8]> + _['x'])  ✅
ibis.literal(100) - ibis._['x']  # → (<scalar[int8]> - _['x'])  ✅
ibis.literal(5) * ibis._['x']    # → (<scalar[int8]> * _['x'])  ✅
ibis.literal(100) / ibis._['x']  # → (<scalar[int8]> / _['x'])  ✅
ibis.literal(100) % ibis._['x']  # → (<scalar[int8]> % _['x'])  ✅
ibis.literal(2) ** ibis._['x']   # → (<scalar[int8]> ** _['x']) ✅
ibis.literal(100) // ibis._['x'] # → (<scalar[int8]> // _['x']) ✅

# FloatingScalar - ALL FIXED ✅
ibis.literal(2.5) + ibis._['x']  # → (<scalar[float64]> + _['x']) ✅
ibis.literal(20.0) - ibis._['x'] # → (<scalar[float64]> - _['x']) ✅
ibis.literal(2.5) * ibis._['x']  # → (<scalar[float64]> * _['x']) ✅

# BooleanScalar - Already worked ✅
ibis.literal(True) & ibis._['x'] # → (<scalar[boolean]> & _['x']) ✅
ibis.literal(False) | ibis._['x'] # → (<scalar[boolean]> | _['x']) ✅
```

**Order preservation verified for non-commutative operations:**
```python
# Subtraction: 100 - 10 = 90 (not -90)
ibis.literal(100) - ibis._['x']  # → 90 ✅

# Division: 100 / 10 = 10.0 (not 0.1)
ibis.literal(100) / ibis._['x']  # → 10.0 ✅
```

---

## Why BooleanScalar Works

Testing showed `BooleanScalar` reverse operators work:

```python
ibis.literal(True) & ibis._['x']  # ✅ Works!
```

This suggests `BooleanScalar` either:
1. Has reverse operators already, OR
2. Its forward operators return `NotImplemented` for `Deferred`, OR
3. Its operations don't raise `InputTypeError`

**Investigation needed:** Check `BooleanScalar` implementation to see the working pattern.

---

## Test Results Summary

| Test | Ibis | Polars |
|------|------|--------|
| `col + lit` | ✅ Works | ✅ Works |
| `5 + col` | ✅ Works | ✅ Works |
| `lit + col` | ❌ Fails | ✅ Works |

**Ibis failures:** 11/39 tests (all `lit + col` patterns)
**Polars failures:** 0/39 tests

**Affected Ibis types:**
- `IntegerScalar` (7 operators fail)
- `FloatingScalar` (3 operators fail)
- `StringScalar` (1 operator fails)
- `BooleanScalar` (0 operators fail) ✅

---

## Key Insight from User

> "The big clue is in the resolved types for the Polars examples, where numeric literals are converted back to raw numbers."

This observation led to discovering that Polars' `parse_into_expression` handles `Expr` objects uniformly, whether they're literals or column references. Both `5 + col` and `lit(5) + col` produce **identical** expressions.

Ibis could adopt a similar pattern in `_binop` or in the operators themselves.
