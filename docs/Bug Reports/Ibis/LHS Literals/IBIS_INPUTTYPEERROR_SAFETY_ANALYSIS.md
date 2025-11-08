# Safety Analysis: Catching InputTypeError in _binop

## Question

Is it safe to catch `InputTypeError` in `_binop`? Could it hide legitimate type errors?

## Answer: YES, it's safe

**`InputTypeError` is ONLY raised for unbound references**, not for type mismatches.

---

## Evidence: What Raises What Exception?

### Invalid Type Combinations (NOT InputTypeError)

| Operation | Exception | Still Caught? |
|-----------|-----------|---------------|
| `literal("hi") + literal(5)` | `SignatureValidationError` | ❌ No (raises to user) |
| `literal(None) + literal(5)` | `TypeError` | ❌ No (raises to user) |
| `literal([1,2,3]) + literal(5)` | `SignatureValidationError` | ❌ No (raises to user) |
| `literal(True) + literal(5)` | `IbisTypeError` | ❌ No (raises to user) |
| `literal("foo") == literal(2)` | `IbisTypeError` | ❌ No (raises to user) |
| `date('2024-01-01') + literal("hi")` | `SignatureValidationError` | ❌ No (raises to user) |

### Unbound References (InputTypeError)

| Operation | Exception | Currently Returns | Should Return |
|-----------|-----------|-------------------|---------------|
| `literal(5) + table({'a': 'int'})` | `InputTypeError` | `NotImplemented` ✅ | `NotImplemented` ✅ |
| `literal(5) + _['x']` | `InputTypeError` | **RAISES** ❌ | `NotImplemented` ✅ |

---

## What is InputTypeError?

From testing, `InputTypeError` is specifically raised when:

> "Unable to infer datatype of value X with type Y"

Where X is an **unbound reference**:
- `Deferred` (unbound column reference like `_['x']`)
- `UnboundTable` (unbound table reference)

**It is NOT raised for:**
- Type mismatches between known types
- Invalid operations
- Incompatible types

---

## Current _binop Exception Handling

```python
def _binop(op_class, left, right):
    try:
        node = op_class(left, right)
    except (ValidationError, NotImplementedError):
        return NotImplemented
    else:
        return node.to_expr()
```

**What this catches:**
- `ValidationError` - validation failures
- `NotImplementedError` - explicitly unimplemented operations

**What this misses:**
- `InputTypeError` - unbound references (INCONSISTENT!)

---

## Proposed Fix

```python
def _binop(op_class, left, right):
    try:
        node = op_class(left, right)
    except (ValidationError, NotImplementedError, InputTypeError):
        return NotImplemented
    else:
        return node.to_expr()
```

---

## Safety Analysis

### ✅ SAFE: Type errors still caught

All actual type mismatches raise **different exceptions** that are NOT caught:

```python
# String + Number
literal("hello") + literal(5)
# → SignatureValidationError (NOT caught, raises to user) ✅

# Bool + Number
literal(True) + literal(5)
# → IbisTypeError (NOT caught, raises to user) ✅

# None + Number
literal(None) + literal(5)
# → TypeError (NOT caught, raises to user) ✅
```

### ✅ SAFE: Only affects unbound references

`InputTypeError` is ONLY raised when trying to infer the datatype of unbound references:

```python
# Unbound table (already returns NotImplemented)
_binop(ops.Equals, 5, table({'a': 'int'}))
# → InputTypeError → caught → NotImplemented ✅

# Unbound column (currently raises, should return NotImplemented)
_binop(ops.Add, literal(5), _['x'])
# → InputTypeError → caught → NotImplemented ✅
```

### ✅ SAFE: Consistent with documented behavior

The `_binop` docstring states:

> "But returns NotImplemented if we aren't sure"

And demonstrates with an unbound table:

```python
>>> _binop(ops.Equals, 5, ibis.table({"a": "int"}))
NotImplemented
```

Catching `InputTypeError` makes **unbound columns** behave like **unbound tables**.

---

## Unintended Consequences: NONE IDENTIFIED

### Could it hide string/number mixing?

**No.** String + Number raises `SignatureValidationError`, not `InputTypeError`.

```python
literal("hello") + literal(5)
# → SignatureValidationError ✅ (still raises)
```

### Could it hide invalid operations?

**No.** Invalid operations raise `IbisTypeError`, `TypeError`, or `SignatureValidationError`.

```python
literal(True) + literal(5)
# → IbisTypeError ✅ (still raises)

literal(None) + literal(5)
# → TypeError ✅ (still raises)
```

### Could it hide future type errors?

**Unlikely.** `InputTypeError` is specifically for "unable to infer datatype", which is fundamentally about unbound references, not type mismatches.

For `InputTypeError` to be raised incorrectly in the future, someone would need to:
1. Have a type mismatch error
2. Choose to raise `InputTypeError` instead of `IbisTypeError` or `TypeError`
3. Use the "unable to infer datatype" message incorrectly

This is highly unlikely and would violate Ibis' existing exception conventions.

---

## What Happens After the Fix?

### Before (Inconsistent)

```python
# Unbound table
literal(5) + table({'a': 'int'})
# → NotImplemented → Python tries table.__radd__(literal(5)) ✅

# Unbound column
literal(5) + _['x']
# → InputTypeError ❌ (Python never gets to try _['x'].__radd__)
```

### After (Consistent)

```python
# Unbound table
literal(5) + table({'a': 'int'})
# → NotImplemented → Python tries table.__radd__(literal(5)) ✅

# Unbound column
literal(5) + _['x']
# → NotImplemented → Python tries _['x'].__radd__(literal(5)) ✅
```

---

## Conclusion

**Catching `InputTypeError` in `_binop` is SAFE because:**

1. ✅ `InputTypeError` is ONLY for unbound references
2. ✅ Type mismatches raise different exceptions (still caught by user)
3. ✅ Restores consistency with documented behavior
4. ✅ Makes `Deferred` behave like `UnboundTable`
5. ✅ No identified unintended consequences

**The fix is a one-line change that:**
- Fixes a contract violation
- Restores consistency
- Enables Python's operator resolution protocol
- Does NOT hide type errors

---

## Recommendation

**Proceed with the fix.** The evidence strongly supports that this is safe and correct.

```python
except (ValidationError, NotImplementedError, InputTypeError):
    return NotImplemented
```
