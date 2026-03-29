# Ibis Reverse Operator Issues - Summary

Two separate bugs in Ibis that prevent reverse operators from working with Deferred column references:

## Issue 1: Numeric Reverse Operators (Main Issue)

**File:** `IBIS_GITHUB_ISSUE.md`

**Affects:** IntegerScalar, FloatingScalar
**Root Cause:** `_binop()` doesn't catch `InputTypeError`
**Fix Location:** `ibis/expr/types/core.py` - `_binop()` function
**Fix Type:** One line change
**Operations Fixed:** 11 arithmetic operations (add, subtract, multiply, divide, modulo, power, floor divide)

### Current Code:
```python
def _binop(op_class, left, right):
    try:
        node = op_class(left, right)
    except (ValidationError, NotImplementedError):  # ← Missing InputTypeError
        return NotImplemented
    else:
        return node.to_expr()
```

### Fixed Code:
```python
def _binop(op_class, left, right):
    try:
        node = op_class(left, right)
    except (ValidationError, NotImplementedError, InputTypeError):  # ← Add InputTypeError
        return NotImplemented
    else:
        return node.to_expr()
```

### Example Failure:
```python
ibis.literal(5) + ibis._['x']        # ❌ InputTypeError
ibis._['x'] + ibis.literal(5)        # ✅ Works
```

---

## Issue 2: String Concatenation (Separate Issue)

**File:** `IBIS_STRINGVALUE_GITHUB_ISSUE.md`

**Affects:** StringScalar
**Root Cause:** `concat()` bypasses `_binop()` entirely, no exception handling
**Fix Location:** `ibis/expr/types/strings.py` - `StringValue.concat()` method
**Fix Type:** Three line change (add try/except)
**Operations Fixed:** 1 string concatenation operation

### Current Code:
```python
def concat(
    self, other: str | StringValue, /, *args: str | StringValue
) -> StringValue:
    """Concatenate strings."""
    return ops.StringConcat((self, other, *args)).to_expr()
```

### Fixed Code:
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

### Example Failure:
```python
ibis.literal(' world') + ibis._['name']   # ❌ SignatureValidationError
ibis._['name'] + ibis.literal(' world')   # ✅ Works
```

---

## Why They're Separate Issues

| Aspect | Issue 1 (Numeric) | Issue 2 (String) |
|--------|-------------------|------------------|
| **File** | `ibis/expr/types/core.py` | `ibis/expr/types/strings.py` |
| **Function** | `_binop()` | `concat()` |
| **Exception** | `InputTypeError` | `SignatureValidationError` |
| **Code Path** | Uses `_binop` | Bypasses `_binop` |
| **Fix Type** | Add exception to tuple | Add exception handling |
| **Scalar Types** | IntegerScalar, FloatingScalar | StringScalar |
| **Operations** | 11 arithmetic ops | 1 concatenation op |

## What Already Works

**BooleanScalar** - Already works correctly! ✅
- `ibis.literal(True) & ibis._['x']` works
- `ibis.literal(False) | ibis._['x']` works
- **Why:** Boolean operations raise `SignatureValidationError` (subclass of `ValidationError`) which `_binop()` already catches

## Total Impact

**After both fixes:**
- ✅ 11 numeric operations fixed (IntegerScalar, FloatingScalar)
- ✅ 1 string operation fixed (StringScalar)
- ✅ 2 boolean operations already work (BooleanScalar)
- **Total: 14 operations across all scalar types**

## Test Pattern That Reveals the Bug

For ALL affected types:
- ✅ `col + lit` - Always works
- ✅ `raw_value + col` - Always works
- ❌ `lit + col` - **This is the bug**

Example:
```python
col = ibis._['x']
lit = ibis.literal(5)

col + lit          # ✅ Works
5 + col           # ✅ Works
lit + col         # ❌ Fails (InputTypeError)
```

## Filing the Issues

### Option 1: Two Separate Issues
- File Issue 1 using `IBIS_GITHUB_ISSUE.md`
- File Issue 2 using `IBIS_STRINGVALUE_GITHUB_ISSUE.md`
- **Pro:** Clear separation of concerns, each issue is focused
- **Con:** More overhead for Ibis maintainers

### Option 2: Combined Issue
- File Issue 1 as main issue
- Add Issue 2 as "Additional Fix Needed" section
- **Pro:** Shows complete picture of reverse operator problems
- **Con:** Mixes two different fixes in one issue

**Recommendation:** File as **two separate issues** because:
1. Different files, different functions, different exceptions
2. Can be implemented and reviewed independently
3. Clear, focused scope for each issue
4. Different developers might work on each fix

## Reference Files

**Demonstration Scripts:**
- `ibis_reverse_operator_comprehensive_repro.py` - Tests all 42 operations across all scalar types
- `ibis_reverse_operator_code_path_analysis.py` - Shows why each scalar type behaves differently
- `ibis_stringvalue_concat_fix.py` - Demonstrates StringValue fix approaches

**Documentation:**
- `IBIS_FIX_SUMMARY.md` - Quick reference for main fix
- `IBIS_STRINGVALUE_FIX_SUMMARY.md` - Complete StringValue fix documentation
- `IBIS_INPUTTYPEERROR_SAFETY_ANALYSIS.md` - Proof that InputTypeError is safe to catch
- `IBIS_REVERSE_OPERATOR_WORKAROUND.md` - User-facing documentation
- `HOW_TO_FILE_IBIS_ISSUE.md` - Step-by-step guide for filing issues

**Test/Verification:**
- `ibis_fix_verification.py` - Original verification script showing the bug
