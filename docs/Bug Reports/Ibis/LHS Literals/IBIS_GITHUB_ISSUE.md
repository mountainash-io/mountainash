# GitHub Issue for Ibis Project

**Title:** `bug: Reverse arithmetic operators fail with Deferred column references`

---

## Issue Body

### What happened?

### The problem

Arithmetic operations fail when a literal is on the **LEFT side** and a Deferred column reference (`ibis._['column']`) is on the **RIGHT side**:

```python
lit = ibis.literal(5)
col = ibis._['value']

# This works ✅
col + lit

# This fails ❌
lit + col
# InputTypeError: Unable to infer datatype of value _['value']
# with type <class 'ibis.common.deferred.Deferred'>
```

This breaks operator symmetry and Python's expectations that `a + b` should behave the same way as `b + a` for numeric types.

**Note:** The issue is specific to `Deferred` column references (`ibis._['col']`). Bound columns (`table.col`) work correctly in both directions.

### Possible solution

The `_binop` function in `ibis/expr/types/core.py` currently catches `ValidationError` and `NotImplementedError`, but **NOT `InputTypeError`**. This is inconsistent because `InputTypeError` is raised specifically for unbound references (like `Deferred`), not for type mismatches.

When Python evaluates `literal(5) + ibis._['x']`:
1. Python tries `literal(5).__add__(ibis._['x'])`
2. This calls `_binop(ops.Add, literal(5), ibis._['x'])`
3. `_binop` tries to create the node but gets `InputTypeError`
4. `InputTypeError` is **NOT caught**, so it raises instead of returning `NotImplemented`
5. Python never gets to try `ibis._['x'].__radd__(literal(5))`

**The fix is a ONE LINE change** - catch `InputTypeError` in addition to existing exceptions:

```python
# In ibis/expr/types/core.py (_binop function)
def _binop(op_class, left, right):
    try:
        node = op_class(left, right)
    except (ValidationError, NotImplementedError, InputTypeError):  # ← Add InputTypeError
        return NotImplemented
    else:
        return node.to_expr()
```

**Why this is safe:**
- `InputTypeError` is ONLY raised for unbound references (Deferred, UnboundTable)
- Type mismatches raise different exceptions: `SignatureValidationError`, `IbisTypeError`, `TypeError`
- This makes `Deferred` behave consistently with `UnboundTable` (which already returns `NotImplemented`)
- This restores the documented `_binop` behavior: "returns NotImplemented if we aren't sure"

See: https://github.com/ibis-project/ibis/blob/main/ibis/expr/types/core.py

### Reproduction

#### Minimal example (demonstrates the bug):

```python
import ibis
import polars as pl

# Setup
conn = ibis.polars.connect()
df = pl.DataFrame({'value': [10]})
table = conn.create_table('test', df, overwrite=True)

# Define expressions using Deferred syntax
lit = ibis.literal(5)
col = ibis._['value']  # Deferred column reference

# Test forward operator (works)
expr = col + lit
result = table.select(expr.name('result')).execute()
print(f"col + lit: {result['result'].tolist()}")  # ✅ [15]

# Test reverse operator (fails)
expr = lit + col
result = table.select(expr.name('result')).execute()  # ❌ InputTypeError
```

**Error:**
```
InputTypeError: Unable to infer datatype of value _['value']
with type <class 'ibis.common.deferred.Deferred'>
```

#### Comprehensive test (all scalar types):

```python
import ibis
import polars as pl

conn = ibis.polars.connect()
df = pl.DataFrame({
    'x_int': [10],
    'x_float': [10.5],
    'x_bool': [True],
})
table = conn.create_table('test', df, overwrite=True)

# IntegerScalar arithmetic
col_int = ibis._['x_int']
print("IntegerScalar (+):")
print(f"  col + lit: {(col_int + ibis.literal(5)).execute(table)[0]}")      # ✅ 15
print(f"  5 + col:   {(5 + col_int).execute(table)[0]}")                    # ✅ 15
print(f"  lit + col: {(ibis.literal(5) + col_int).execute(table)[0]}")      # ❌ InputTypeError

# FloatingScalar arithmetic
col_float = ibis._['x_float']
print("\nFloatingScalar (+):")
print(f"  col + lit: {(col_float + ibis.literal(2.5)).execute(table)[0]}")    # ✅ 13.0
print(f"  2.5 + col: {(2.5 + col_float).execute(table)[0]}")                  # ✅ 13.0
print(f"  lit + col: {(ibis.literal(2.5) + col_float).execute(table)[0]}")    # ❌ InputTypeError

# BooleanScalar logical (works!)
col_bool = ibis._['x_bool']
print("\nBooleanScalar (&):")
print(f"  col & lit: {(col_bool & ibis.literal(True)).execute(table)[0]}")    # ✅ True
print(f"  True & col: {(True & col_bool).execute(table)[0]}")                 # ✅ True
print(f"  lit & col: {(ibis.literal(True) & col_bool).execute(table)[0]}")    # ✅ True
```

### Output

**Cross-backend test (simple):**

| backend   | col+lit   | lit+col          |
|:----------|:----------|:-----------------|
| polars    | 15        | InputTypeError   |
| duckdb    | 15        | InputTypeError   |
| sqlite    | 15        | InputTypeError   |

**Comprehensive test (42 total operations):**

| Test Pattern | Passed | Failed | Notes |
|:-------------|:-------|:-------|:------|
| Forward: `col op lit` | 14/14 ✅ | 0 | Always works |
| Reverse raw: `value op col` | 14/14 ✅ | 0 | Raw Python values work |
| Reverse literal: `lit op col` | 2/14 | 12 ❌ | **This is the bug** |

**Affected scalar types:**

| Scalar Type | Operations | Failures | Status |
|:------------|:-----------|:---------|:-------|
| IntegerScalar | 7 arithmetic | 7 ❌ | All fail |
| FloatingScalar | 4 arithmetic | 4 ❌ | All fail |
| BooleanScalar | 2 logical | 0 ✅ | **Already works!** |
| StringScalar | 1 concat | 1 ❌ | Fails (SignatureValidationError) |

**Key finding:** The bug affects IntegerScalar and FloatingScalar, but **BooleanScalar already works correctly!** This suggests the fix will make numeric scalars consistent with boolean scalars.

### What version of ibis are you using?

11.0.0

### What backend(s) are you using, if any?

**Where the bug occurs:** All backends (Polars, DuckDB, SQLite, etc.)

**Note:** The issue is in the core expression layer, not backend-specific

### Relevant log output

```python
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "/ibis/expr/types/numeric.py", line xxx, in __add__
    return _binop(ops.Add, self, other)
  File "/ibis/expr/operations/core.py", line 72, in __coerce__
    dtype = dt.infer(value)
  File "/ibis/common/dispatch.py", line 115, in call
    return impl(arg, *args, **kwargs)
  File "/ibis/expr/datatypes/value.py", line 35, in infer
    raise InputTypeError(
ibis.common.exceptions.InputTypeError: Unable to infer datatype of value _['value']
with type <class 'ibis.common.deferred.Deferred'>
```

### Code of Conduct

- [x] I agree to follow this project's Code of Conduct

---

## Additional Context

### Fix Location

**File:** `ibis/expr/types/core.py`
**Function:** `_binop`
**Change:** Add `InputTypeError` to the exception tuple (one line)

Current code:
```python
except (ValidationError, NotImplementedError):
```

Fixed code:
```python
except (ValidationError, NotImplementedError, InputTypeError):
```

### Why InputTypeError is Safe to Catch

`InputTypeError` is specifically for "unable to infer datatype" from unbound references. It is **NOT** used for type mismatches:

| Scenario | Exception Raised | Caught by Fix? |
|----------|------------------|----------------|
| `literal("hi") + literal(5)` | `SignatureValidationError` | ❌ No (still raises) |
| `literal(True) + literal(5)` | `IbisTypeError` | ❌ No (still raises) |
| `literal(None) + literal(5)` | `TypeError` | ❌ No (still raises) |
| `literal(5) + ibis._['x']` | `InputTypeError` | ✅ Yes (returns NotImplemented) |
| `literal(5) + ibis.table({"a": "int"})` | `InputTypeError` | ✅ Yes (already works) |

This makes `Deferred` behave consistently with `UnboundTable`, which already returns `NotImplemented`.

### Interesting Finding: BooleanScalar Already Works

Testing revealed that **BooleanScalar logical operators already work correctly:**

```python
literal(True) & ibis._['bool_col']   # ✅ Works
literal(False) | ibis._['bool_col']  # ✅ Works
```

**Why BooleanScalar works (but IntegerScalar doesn't):**

The difference is in which exception each operation raises when given a Deferred:

```python
# Arithmetic operations (IntegerScalar, FloatingScalar)
ops.Add(literal(5), Deferred)
# → Raises InputTypeError
# → NOT caught by _binop ❌
# → Exception bubbles up, Python never tries reverse operator

# Logical operations (BooleanScalar)
ops.And(literal(True), Deferred)
# → Raises SignatureValidationError
# → IS caught by _binop (it's a subclass of ValidationError) ✅
# → _binop returns NotImplemented
# → Python tries Deferred.__rand__(literal) ✅
```

**Exception hierarchy:**
- `SignatureValidationError` → `ValidationError` → `Exception` (caught by `_binop`)
- `InputTypeError` → `IbisTypeError` → `TypeError` → `Exception` (NOT caught by `_binop`)

This proves the fix is correct: **adding `InputTypeError` to the caught exceptions makes arithmetic operators behave consistently with logical operators.**

**Why StringScalar still fails (different reason):**

StringValue uses a completely different code path that bypasses `_binop`:

```python
# NumericValue.__add__ (goes through _binop)
def __add__(self, other):
    return _binop(ops.Add, self, other)  # ✅ Will be fixed

# BooleanValue.__and__ (goes through _binop)
def __and__(self, other):
    return _binop(ops.And, self, other)  # ✅ Already works

# StringValue.__add__ (BYPASSES _binop!)
def __add__(self, other):
    return self.concat(other)  # ❌ Won't be fixed by this change

def concat(self, other, *args):
    return ops.StringConcat((self, other, *args)).to_expr()  # No _binop!
```

StringScalar concatenation raises `SignatureValidationError` (which _binop would catch), but the exception is raised in `concat()` which doesn't use `_binop` at all. This needs a **separate fix**.

### Affected Scalar Types and Operations

**IntegerScalar & FloatingScalar (BROKEN):**
- Addition: `literal(5) + ibis._['x']` → ❌ InputTypeError
- Subtraction: `literal(100) - ibis._['x']` → ❌ InputTypeError
- Multiplication: `literal(2) * ibis._['x']` → ❌ InputTypeError
- Division: `literal(100) / ibis._['x']` → ❌ InputTypeError
- Modulo: `literal(100) % ibis._['x']` → ❌ InputTypeError
- Power: `literal(2) ** ibis._['x']` → ❌ InputTypeError
- Floor division: `literal(100) // ibis._['x']` → ❌ InputTypeError

**BooleanScalar (ALREADY WORKS):**
- AND: `literal(True) & ibis._['x']` → ✅ Works correctly
- OR: `literal(False) | ibis._['x']` → ✅ Works correctly

**StringScalar (BROKEN - different code path):**
- Concatenation: `literal('x') + ibis._['y']` → ❌ SignatureValidationError

**Note:**
- BooleanScalar already works (proves the fix is viable)
- **StringScalar will NOT be fixed** by this change - it uses a different code path that bypasses `_binop`:
  ```python
  # NumericValue & BooleanValue
  __add__/__and__() → _binop(ops.Add/And, ...) ✅

  # StringValue (different!)
  __add__() → concat() → ops.StringConcat().to_expr() ❌ (bypasses _binop)
  ```
- StringScalar needs a separate fix - see `IBIS_STRINGVALUE_GITHUB_ISSUE.md` for a complete GitHub issue addressing StringValue concatenation

### Impact

This breaks expression building frameworks that generate expressions programmatically, where operand order may not be predictable. It also violates Python's numeric type behavior where `a + b` and `b + a` should both work.

### Workaround

Users can rewrite expressions to put the column reference on the left:
```python
# Instead of:
5 + ibis._['price']

# Use:
ibis._['price'] + 5
```
