# Ibis Reverse Operator Fix - Quick Start Guide

## TL;DR - The Bug

```python
import ibis

# Works ✅
ibis._['x'] + ibis.literal(5)

# Fails ❌
ibis.literal(5) + ibis._['x']
# Error: InputTypeError: Unable to infer datatype of value _['x']
```

**Fix:** Add `__radd__`, `__rsub__`, etc. to `NumericValue` class in `ibis/expr/types/numeric.py`

---

## Quick Commands

### 1. Fork & Clone
```bash
# Fork on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/ibis.git
cd ibis
git remote add upstream https://github.com/ibis-project/ibis.git
```

### 2. Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pre-commit install
```

### 3. Create Branch
```bash
git checkout main
git pull upstream main
git checkout -b fix/deferred-reverse-operators
```

### 4. Test the Bug
```bash
python << 'EOF'
import ibis
col = ibis._['x']
lit = ibis.literal(5)
print("Forward:", col + lit)  # Works
print("Reverse:", lit + col)  # Fails
EOF
```

### 5. Add Code
**File:** `ibis/expr/types/numeric.py`

```python
from ibis.common.deferred import Deferred

class NumericValue(Value):
    # ... existing methods ...

    def __radd__(self, other):
        if isinstance(other, Deferred):
            return other.__add__(self)
        return _binop(ops.Add, other, self)

    def __rsub__(self, other):
        if isinstance(other, Deferred):
            return other.__sub__(self)
        return _binop(ops.Subtract, other, self)

    def __rmul__(self, other):
        if isinstance(other, Deferred):
            return other.__mul__(self)
        return _binop(ops.Multiply, other, self)

    def __rtruediv__(self, other):
        if isinstance(other, Deferred):
            return other.__truediv__(self)
        return _binop(ops.Divide, other, self)

    def __rmod__(self, other):
        if isinstance(other, Deferred):
            return other.__mod__(self)
        return _binop(ops.Modulus, other, self)

    def __rpow__(self, other):
        if isinstance(other, Deferred):
            return other.__pow__(self)
        return _binop(ops.Power, other, self)

    def __rfloordiv__(self, other):
        if isinstance(other, Deferred):
            return other.__floordiv__(self)
        return _binop(ops.FloorDivide, other, self)
```

### 6. Add Tests
**File:** `ibis/tests/expr/test_deferred_reverse_operators.py`

```python
import pytest
import ibis

def test_radd_literal_plus_deferred():
    col = ibis._['x']
    lit = ibis.literal(5)
    result = lit + col  # Should not raise
    assert result is not None

@pytest.mark.parametrize('op,symbol', [
    (lambda a, b: a + b, '+'),
    (lambda a, b: a - b, '-'),
    (lambda a, b: a * b, '*'),
    (lambda a, b: a / b, '/'),
    (lambda a, b: a % b, '%'),
    (lambda a, b: a ** b, '**'),
    (lambda a, b: a // b, '//'),
])
def test_all_reverse_operators(op, symbol):
    col = ibis._['x']
    lit = ibis.literal(5)
    result = op(lit, col)
    assert result is not None
```

### 7. Run Tests
```bash
# Your new tests
pytest ibis/tests/expr/test_deferred_reverse_operators.py -v

# Existing tests
pytest ibis/tests/expr/test_numeric.py -v
```

### 8. Commit
```bash
git add ibis/expr/types/numeric.py
git add ibis/tests/expr/test_deferred_reverse_operators.py
git commit -m "fix(expr): add reverse operators for Deferred arithmetic

Add __radd__, __rsub__, __rmul__, __rtruediv__, __rmod__, __rpow__,
and __rfloordiv__ to NumericValue to support Deferred on right side.

Fixes: #ISSUE_NUMBER"
```

### 9. Push & PR
```bash
git push origin fix/deferred-reverse-operators
```

Then go to GitHub and click "Create Pull Request"

---

## Issue Template

**Title:** `bug(expr): Reverse arithmetic operators fail with Deferred column references`

**Body:**
```markdown
## What happened?

Arithmetic fails when literal is on left: `ibis.literal(5) + ibis._['x']`

## Minimal Example

```python
import ibis
col = ibis._['x']
lit = ibis.literal(5)

col + lit  # ✅ Works
lit + col  # ❌ InputTypeError
```

## Expected

Both should work (commutativity)

## Root Cause

`NumericValue` lacks `__radd__`, `__rsub__`, etc.

## Solution

Add reverse operators that delegate to Deferred when appropriate.
```

---

## PR Template

**Title:** `fix(expr): add reverse operators for Deferred arithmetic`

**Body:**
```markdown
## Summary

Adds reverse operators to `NumericValue` for Deferred support.

## Problem

`ibis.literal(5) + ibis._['x']` fails with InputTypeError

## Solution

Added `__radd__`, `__rsub__`, etc. that check for Deferred and delegate.

## Changes

- `ibis/expr/types/numeric.py`: Added 7 reverse operators
- `ibis/tests/expr/test_deferred_reverse_operators.py`: Comprehensive tests

## Testing

```bash
pytest ibis/tests/expr/test_deferred_reverse_operators.py -v
```

All tests pass ✅

## Closes

Fixes #ISSUE_NUMBER
```

---

## Verification After Fix

```bash
python << 'EOF'
import ibis

col = ibis._['x']
lit = ibis.literal(5)

print("Testing fix:")
print("col + lit:", col + lit)  # Should work
print("lit + col:", lit + col)  # Should work now!

# Test with real data
import polars as pl
conn = ibis.polars.connect()
df = pl.DataFrame({'x': [1, 2, 3]})
table = conn.create_table('test', df, overwrite=True)

result = table.select((ibis.literal(10) + ibis._['x']).name('result'))
print("Values:", result['result'].execute().tolist())
# Expected: [11, 12, 13]
EOF
```

---

## Checklist

### Pre-Work
- [ ] Verified bug exists
- [ ] Checked no existing issues
- [ ] Tested on latest Ibis

### Development
- [ ] Forked repo
- [ ] Created branch
- [ ] Added reverse operators
- [ ] Added comprehensive tests
- [ ] All tests pass

### Submission
- [ ] Filed issue (do this first!)
- [ ] Waited for acknowledgment
- [ ] Created PR linking to issue
- [ ] Responded to reviews

---

## Files to Edit

1. `ibis/expr/types/numeric.py` - Add reverse operators
2. `ibis/tests/expr/test_deferred_reverse_operators.py` - New test file

**That's it!** Just 2 files.

---

## Common Issues

**Q: Tests fail with import error**
```bash
# Make sure you installed in dev mode:
pip install -e '.[dev]'
```

**Q: Pre-commit hooks fail**
```bash
# Run auto-formatters:
pre-commit run --all-files
```

**Q: Merge conflicts**
```bash
# Rebase on latest main:
git fetch upstream
git rebase upstream/main
```

---

## Timeline

- File issue: **5 min**
- Get response: **1-2 days**
- Code + test: **1-2 hours**
- Create PR: **5 min**
- Review cycle: **3-7 days**
- **Total: ~2 weeks to merge**

---

## Resources

- Full guide: `IBIS_REVERSE_OPERATOR_BUG_FIX.md`
- Ibis contributing: https://github.com/ibis-project/ibis/blob/main/CONTRIBUTING.md
- Python operators: https://docs.python.org/3/reference/datamodel.html#object.__radd__

---

**Good luck!** This is a straightforward, high-impact fix. 🎯
