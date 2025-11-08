# GitHub Issue for Ibis Project - StringValue Concatenation

**Title:** `bug: String concatenation reverse operators fail with Deferred column references`

---

## Issue Body

### What happened?

### The problem

String concatenation fails when a literal is on the **LEFT side** and a Deferred column reference (`ibis._['column']`) is on the **RIGHT side**:

```python
lit_str = ibis.literal(' world')
col_str = ibis._['name']

# This works ✅
col_str + lit_str

# This fails ❌
lit_str + col_str
# SignatureValidationError: Function 'StringConcat' expects ...
```

This breaks operator symmetry - `a + b` should behave the same way as `b + a` for string concatenation.

**Note:** The issue is specific to `Deferred` column references (`ibis._['col']`). Bound columns (`table.col`) work correctly in both directions.

### Possible solution

The issue is that **StringValue uses a different code path** than NumericValue and BooleanValue:

```python
# NumericValue & BooleanValue (use _binop)
NumericValue.__add__() → _binop(ops.Add, ...) → catches exceptions → returns NotImplemented ✅

# StringValue (BYPASSES _binop!)
StringValue.__add__() → self.concat(other) → ops.StringConcat(...).to_expr() ❌
```

The `concat()` method in `ibis/expr/types/strings.py` directly creates `ops.StringConcat()` which raises `SignatureValidationError` when given a Deferred, but there's **no exception handler** to catch it and return `NotImplemented`.

**The fix is a 3-LINE change** - add exception handling to `concat()`:

**File:** `ibis/expr/types/strings.py`
**Method:** `StringValue.concat()`
**Line:** ~1580

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

**Why this is safe:**
- `ValidationError` is the base class for validation errors in Ibis
- `SignatureValidationError` is a subclass of `ValidationError`
- This matches the existing pattern in `_binop()` which already catches `ValidationError`
- When `concat()` returns `NotImplemented`, Python will try the reverse operator on the Deferred
- This makes StringValue consistent with NumericValue and BooleanValue

### Reproduction

#### Minimal example (demonstrates the bug):

```python
import ibis
import polars as pl

# Setup
conn = ibis.polars.connect()
df = pl.DataFrame({'name': ['hello']})
table = conn.create_table('test', df, overwrite=True)

# Define expressions using Deferred syntax
lit_str = ibis.literal(' world')
col_str = ibis._['name']  # Deferred column reference

# Test forward operator (works)
expr = col_str + lit_str
result = table.select(expr.name('result')).execute()
print(f"col + lit: {result['result'].tolist()}")  # ✅ ['hello world']

# Test reverse operator (fails)
expr = lit_str + col_str
result = table.select(expr.name('result')).execute()  # ❌ SignatureValidationError
```

**Error:**
```
SignatureValidationError: Function 'StringConcat' expects argument #1 to
have type <class 'ibis.expr.types.strings.StringValue'> but got argument
with type <class 'ibis.common.deferred.Deferred'>
```

#### Comprehensive test:

```python
import ibis
import polars as pl

conn = ibis.polars.connect()
df = pl.DataFrame({'x_str': ['hello']})
table = conn.create_table('test', df, overwrite=True)

col_str = ibis._['x_str']
lit_str = ibis.literal(' world')

print("String concatenation:")
# Forward: col + lit
try:
    expr = col_str + lit_str
    result = table.select(expr.name('r'))['r'].execute().tolist()[0]
    print(f"  ✅ col + lit        → '{result}'")  # ✅ Works
except Exception as e:
    print(f"  ❌ col + lit        → {type(e).__name__}")

# Reverse with raw Python string
try:
    expr = ' world' + col_str
    result = table.select(expr.name('r'))['r'].execute().tolist()[0]
    print(f"  ✅ ' world' + col   → '{result}'")  # ✅ Works
except Exception as e:
    print(f"  ❌ ' world' + col   → {type(e).__name__}")

# Reverse with literal (THIS IS THE BUG)
try:
    expr = lit_str + col_str
    result = table.select(expr.name('r'))['r'].execute().tolist()[0]
    print(f"  ✅ lit + col        → '{result}'")
except Exception as e:
    print(f"  ❌ lit + col        → {type(e).__name__}")  # ❌ Fails
```

### Output

**Cross-backend test:**

| backend   | col+lit   | lit+col                    |
|:----------|:----------|:---------------------------|
| polars    | 'hello world' | SignatureValidationError |
| duckdb    | 'hello world' | SignatureValidationError |
| sqlite    | 'hello world' | SignatureValidationError |

**Pattern:**
- Forward: `col + lit` → ✅ Always works
- Reverse raw: `'world' + col` → ✅ Works
- Reverse literal: `lit + col` → ❌ **This is the bug**

### What version of ibis are you using?

11.0.0

### What backend(s) are you using, if any?

**Where the bug occurs:** All backends (Polars, DuckDB, SQLite, etc.)

**Note:** The issue is in the core expression layer, not backend-specific

### Relevant log output

```python
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "/ibis/expr/types/strings.py", line xxx, in __add__
    return self.concat(other)
  File "/ibis/expr/types/strings.py", line xxx, in concat
    return ops.StringConcat((self, other, *args)).to_expr()
  File "/ibis/expr/operations/...", line xxx, in __init__
    ...
ibis.common.exceptions.SignatureValidationError: Function 'StringConcat' expects
argument #1 to have type <class 'ibis.expr.types.strings.StringValue'> but got
argument with type <class 'ibis.common.deferred.Deferred'>
```

### Code of Conduct

- [x] I agree to follow this project's Code of Conduct

---

## Additional Context

### Fix Location

**File:** `ibis/expr/types/strings.py`
**Method:** `StringValue.concat()`
**Line:** ~1580
**Change:** Add exception handling (3 lines)

Current code:
```python
def concat(
    self, other: str | StringValue, /, *args: str | StringValue
) -> StringValue:
    """Concatenate strings."""
    return ops.StringConcat((self, other, *args)).to_expr()
```

Fixed code:
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

Required import (add to top of file):
```python
from ibis.common.annotations import ValidationError
```

### Why This Fix is Safe

**ValidationError is specifically for validation issues:**
- `SignatureValidationError` inherits from `ValidationError`
- This is NOT a type mismatch error (those raise `IbisTypeError`, `TypeError`)
- This matches the existing pattern in `_binop()` which catches `ValidationError`

**What happens after the fix:**

When Python evaluates: `literal(' world') + ibis._['name']`

1. Python tries `literal(' world').__add__(ibis._['name'])`
   - Calls `StringValue.__add__(Deferred)`
   - Calls `concat(Deferred)`
   - `ops.StringConcat((self, Deferred))` raises `SignatureValidationError`
   - **NOW:** `concat()` catches it and returns `NotImplemented` ✅

2. Because `__add__` returned `NotImplemented`, Python tries reverse operator:
   - Calls `ibis._['name'].__radd__(literal(' world'))`
   - Deferred creates the expression ✅
   - Success!

### Consistency with _binop Pattern

This fix makes `StringValue.concat()` behave consistently with `_binop()`:

```python
# _binop (in ibis/expr/types/core.py) - existing pattern
def _binop(op_class, left, right):
    try:
        node = op_class(left, right)
    except (ValidationError, NotImplementedError):
        return NotImplemented  # ← Pattern we're following
    else:
        return node.to_expr()

# concat (proposed fix) - same pattern
def concat(self, other, /, *args):
    try:
        return ops.StringConcat((self, other, *args)).to_expr()
    except ValidationError:
        return NotImplemented  # ← Same pattern!
```

### Alternative Fix Approach (Not Recommended)

Instead of exception handling, could check for Deferred explicitly:

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

**Why exception handling is preferred:**
- ✅ Consistent with existing `_binop` pattern used throughout Ibis
- ✅ Handles all validation errors, not just Deferred
- ✅ Standard Python pattern for handling unsupported operations
- ⚠️ Deferred check is more explicit but diverges from Ibis patterns

### Relationship to Other Scalar Types

**StringValue is the only scalar type that bypasses `_binop`:**

| Scalar Type | Code Path | Works? | Fix Needed |
|:------------|:----------|:-------|:-----------|
| IntegerScalar | `__add__` → `_binop(ops.Add, ...)` | ✅ | No (after #XXXX) |
| FloatingScalar | `__add__` → `_binop(ops.Add, ...)` | ✅ | No (after #XXXX) |
| BooleanScalar | `__and__` → `_binop(ops.And, ...)` | ✅ | No |
| **StringScalar** | `__add__` → `concat()` → `ops.StringConcat()` | ❌ | **Yes (this issue)** |

**Note:** There's a separate issue (#XXXX) for numeric scalar reverse operators that fixes the `_binop` code path. This issue is specifically for StringValue which uses a different code path.

### Impact

This breaks expression building frameworks that generate string concatenation expressions programmatically, where operand order may not be predictable. It also violates Python's expectations that `a + b` and `b + a` should both work for concatenation.

### Workaround

Users can rewrite expressions to put the column reference on the left:

```python
# Instead of:
ibis.literal(' world') + ibis._['name']

# Use:
ibis._['name'] + ibis.literal(' world')
```

Or use raw Python strings:
```python
# Instead of:
ibis.literal(' world') + ibis._['name']

# Use:
' world' + ibis._['name']
```
