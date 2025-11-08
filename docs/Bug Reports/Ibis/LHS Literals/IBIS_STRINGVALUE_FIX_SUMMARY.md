# StringValue Reverse Operator Fix - Summary

## Problem

StringValue reverse operators fail with `SignatureValidationError` when literal is on the left:

```python
literal('world') + ibis._['x']  # ❌ SignatureValidationError
```

## Root Cause

**Different code path than numeric types:**

```python
# NumericValue (goes through _binop)
NumericValue.__add__() → _binop(ops.Add, ...)

# StringValue (BYPASSES _binop!)
StringValue.__add__() → concat() → ops.StringConcat().to_expr()
```

The `concat()` method directly creates `ops.StringConcat()` which raises `SignatureValidationError` when given a Deferred, but there's no exception handler to catch it and return `NotImplemented`.

## Proposed Fix

**File:** `ibis/expr/types/strings.py`
**Method:** `StringValue.concat()`
**Line:** ~1580

### Approach 1: Exception Handling (RECOMMENDED)

**Current code:**
```python
def concat(
    self, other: str | StringValue, /, *args: str | StringValue
) -> StringValue:
    """Concatenate strings."""
    return ops.StringConcat((self, other, *args)).to_expr()
```

**Fixed code:**
```python
def concat(
    self, other: str | StringValue, /, *args: str | StringValue
) -> StringValue:
    """Concatenate strings."""
    try:
        return ops.StringConcat((self, other, *args)).to_expr()
    except ValidationError:
        return NotImplemented
```

**Required import:**
```python
from ibis.common.annotations import ValidationError
```

### Approach 2: Deferred Check (ALTERNATIVE)

```python
def concat(
    self, other: str | StringValue, /, *args: str | StringValue
) -> StringValue:
    """Concatenate strings."""
    from ibis.common.deferred import Deferred

    # Check if any argument is a Deferred (unbound reference)
    if isinstance(other, Deferred) or any(isinstance(a, Deferred) for a in args):
        return NotImplemented

    return ops.StringConcat((self, other, *args)).to_expr()
```

## Why Approach 1 is Recommended

| Aspect | Approach 1 (Try/Except) | Approach 2 (Deferred Check) |
|--------|------------------------|----------------------------|
| **Consistency** | ✅ Matches `_binop` pattern | ❌ Different pattern |
| **Code complexity** | Low (+3 lines) | Low (+4 lines) |
| **Handles all cases** | ✅ Catches any ValidationError | ⚠️ Only handles Deferred |
| **Performance** | Small exception cost | ✅ No exceptions |
| **Maintainability** | ✅ Standard Ibis pattern | ✅ Explicit and clear |

**Recommendation:** Use Approach 1 for consistency with the existing `_binop` pattern used throughout Ibis.

## Consistency with _binop

This fix makes `concat()` behave like `_binop()`:

```python
# _binop (existing pattern)
def _binop(op_class, left, right):
    try:
        node = op_class(left, right)
    except (ValidationError, NotImplementedError):
        return NotImplemented  # ← Pattern we're following
    else:
        return node.to_expr()

# concat (proposed fix)
def concat(self, other, /, *args):
    try:
        return ops.StringConcat((self, other, *args)).to_expr()
    except ValidationError:
        return NotImplemented  # ← Same pattern
```

## Relationship to Main Fix

**This is a SEPARATE fix** from the main `InputTypeError` fix for numeric types:

| Fix | File | Change | Fixes |
|-----|------|--------|-------|
| **Main fix** | `ibis/expr/types/core.py` | Add `InputTypeError` to `_binop` | IntegerScalar, FloatingScalar |
| **This fix** | `ibis/expr/types/strings.py` | Add exception handling to `concat()` | StringScalar |

Both fixes follow the same principle: **return `NotImplemented`** when encountering unbound references so Python can try the reverse operator.

## Testing

After the fix, all three should work:

```python
col + lit           # ✅ Already works
'world' + col       # ✅ Already works
literal('world') + col  # ✅ Will work after fix
```

## Files for Reference

- **Demonstration:** `docs/ibis_stringvalue_concat_fix.py`
- **Code path analysis:** `docs/ibis_reverse_operator_code_path_analysis.py`
- **Main fix issue:** `docs/IBIS_GITHUB_ISSUE.md`

## Should This Be a Separate GitHub Issue?

**Yes**, for these reasons:

1. **Different file, different method** - Not part of the `_binop` fix
2. **Different exception type** - `SignatureValidationError` vs `InputTypeError`
3. **Can be implemented independently** - Doesn't depend on the main fix
4. **Clear scope** - Focused on string concatenation only

## Suggested Issue Title

```
bug: String concatenation reverse operators fail with Deferred column references
```

Or combine with main issue:

```
(Add to main issue as "Additional Fix Needed")
```
