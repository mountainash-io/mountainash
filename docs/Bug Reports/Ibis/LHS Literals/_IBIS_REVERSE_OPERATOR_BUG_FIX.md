# Ibis Reverse Operator Bug - Issue and PR Guide

## Overview

This document outlines a bug in Ibis where reverse arithmetic operators fail when a literal is on the left side and a `Deferred` column reference is on the right side. This violates Python's operator commutativity expectations and breaks expression builders.

**Status:** Undiscovered bug - no existing issues found in Ibis tracker
**Severity:** Medium - breaks operator symmetry, affects expression building frameworks
**Complexity:** Low - straightforward fix adding reverse operators

---

## The Bug

### Problem Statement

Arithmetic operations in Ibis are not commutative when mixing `Deferred` column references (`ibis._['col']`) with literals (`ibis.literal(value)`):

```python
import ibis

col = ibis._['x']
lit = ibis.literal(5)

# This works ✅
result = col + lit  # Deferred + Literal
# Output: (_['x'] + <scalar[int8]>)

# This fails ❌
result = lit + col  # Literal + Deferred
# Error: InputTypeError: Unable to infer datatype of value _['x']
#        with type <class 'ibis.common.deferred.Deferred'>
```

### Affected Operators

All arithmetic operators are affected:
- `+` (`__radd__`)
- `-` (`__rsub__`)
- `*` (`__rmul__`)
- `/` (`__rtruediv__`)
- `%` (`__rmod__`)
- `**` (`__rpow__`)
- `//` (`__rfloordiv__`)

### Impact

1. **Breaks commutativity**: `a + b` should equal `b + a` for numeric types
2. **Expression builders**: Frameworks that generate expressions programmatically fail randomly depending on operand order
3. **User confusion**: Natural expressions like `5 + ibis._['col']` don't work
4. **Python expectations**: Violates Python's numeric type behavior

---

## Reproduction

### Minimal Test Case

```python
import ibis

def test_operator_symmetry():
    """Demonstrate the bug."""
    col = ibis._['x']
    lit = ibis.literal(5)

    print("Testing operator symmetry:")
    print("=" * 50)

    # Addition
    print("\n1. Addition:")
    try:
        result = col + lit
        print(f"   col + lit: ✓ Works - {result}")
    except Exception as e:
        print(f"   col + lit: ✗ Fails - {type(e).__name__}")

    try:
        result = lit + col
        print(f"   lit + col: ✓ Works - {result}")
    except Exception as e:
        print(f"   lit + col: ✗ Fails - {type(e).__name__}: {e}")

    # Test all operators
    operators = [
        ('Subtraction', '-', lambda a, b: a - b),
        ('Multiplication', '*', lambda a, b: a * b),
        ('Division', '/', lambda a, b: a / b),
        ('Modulo', '%', lambda a, b: a % b),
        ('Power', '**', lambda a, b: a ** b),
        ('Floor Division', '//', lambda a, b: a // b),
    ]

    for name, symbol, op in operators:
        print(f"\n{name}:")
        # Forward (works)
        try:
            op(col, lit)
            print(f"   col {symbol} lit: ✓ Works")
        except:
            print(f"   col {symbol} lit: ✗ Fails")

        # Reverse (fails)
        try:
            op(lit, col)
            print(f"   lit {symbol} col: ✓ Works")
        except Exception as e:
            print(f"   lit {symbol} col: ✗ Fails - {type(e).__name__}")

if __name__ == "__main__":
    test_operator_symmetry()
```

**Expected Output:**
```
Testing operator symmetry:
==================================================

1. Addition:
   col + lit: ✓ Works - (_['x'] + <scalar[int8]>)
   lit + col: ✗ Fails - InputTypeError: Unable to infer datatype...

Subtraction:
   col - lit: ✓ Works
   lit - col: ✗ Fails - InputTypeError

... (all reverse operators fail)
```

### Real-World Impact

This breaks expression building frameworks like `mountainash-expressions`:

```python
import mountainash_expressions as ma

# User writes natural Python
expr = 5 + ma.col("price")  # Calls __radd__ internally

# When compiled to Ibis backend:
backend_expr = expr.compile(ibis_table)
# ❌ Fails! Creates ibis.literal(5) + ibis._['price']
```

---

## Root Cause Analysis

### Technical Details

1. **`Deferred` class** (`ibis/common/deferred.py`):
   - Has forward operators: `__add__`, `__sub__`, `__mul__`, etc.
   - These work with `ir.Expr` on the right: `Deferred + ir.Expr` ✅

2. **`ir.Expr` classes** (`ibis/expr/types/numeric.py`):
   - `NumericValue`, `IntegerScalar`, etc. have forward operators
   - **Missing** reverse operators: `__radd__`, `__rsub__`, etc.
   - Cannot handle `Deferred` on the right: `ir.Expr + Deferred` ❌

### Why This Happens

When Python evaluates `literal(5) + ibis._['x']`:

1. Tries `literal(5).__add__(ibis._['x'])`
2. `IntegerScalar.__add__()` doesn't know how to handle `Deferred`
3. Returns `NotImplemented`
4. Python tries `ibis._['x'].__radd__(literal(5))`
5. But `Deferred` doesn't have `__radd__`!
6. Python raises `TypeError` / Ibis raises `InputTypeError`

**The fix:** Add `__radd__` and friends to `NumericValue` that delegate to `Deferred` when appropriate.

---

## Proposed Fix

### Solution Overview

Add reverse operators to `ibis/expr/types/numeric.py` in the `NumericValue` class. These operators should:

1. Check if `other` is a `Deferred` object
2. If yes, delegate to `Deferred.__add__(self)` (swap operands)
3. If no, fall back to normal behavior via `_binop()`

### Code Changes Required

**File:** `ibis/expr/types/numeric.py`

**Location:** Add these methods to the `NumericValue` class (after existing `__add__`, `__sub__`, etc.)

```python
# Add import at top of file
from ibis.common.deferred import Deferred

class NumericValue(Value):
    # ... existing forward operators ...

    # ========================================
    # Reverse Operators for Deferred Support
    # ========================================

    def __radd__(self, other: Any) -> NumericValue:
        """
        Handle other + self, including Deferred + NumericValue.

        This enables commutative addition with Deferred column references:
            ibis.literal(5) + ibis._['col']  # Now works!

        Args:
            other: Left operand (may be Deferred, numeric, or other type)

        Returns:
            NumericValue expression

        Note:
            When other is Deferred, we delegate to Deferred.__add__
            to ensure proper expression construction.
        """
        if isinstance(other, Deferred):
            return other.__add__(self)
        return _binop(ops.Add, other, self)

    def __rsub__(self, other: Any) -> NumericValue:
        """
        Handle other - self, including Deferred - NumericValue.

        Enables: ibis.literal(100) - ibis._['col']
        """
        if isinstance(other, Deferred):
            return other.__sub__(self)
        return _binop(ops.Subtract, other, self)

    def __rmul__(self, other: Any) -> NumericValue:
        """
        Handle other * self, including Deferred * NumericValue.

        Enables: ibis.literal(2) * ibis._['col']
        """
        if isinstance(other, Deferred):
            return other.__mul__(self)
        return _binop(ops.Multiply, other, self)

    def __rtruediv__(self, other: Any) -> NumericValue:
        """
        Handle other / self, including Deferred / NumericValue.

        Enables: ibis.literal(100) / ibis._['col']
        """
        if isinstance(other, Deferred):
            return other.__truediv__(self)
        return _binop(ops.Divide, other, self)

    def __rmod__(self, other: Any) -> NumericValue:
        """
        Handle other % self, including Deferred % NumericValue.

        Enables: ibis.literal(100) % ibis._['col']
        """
        if isinstance(other, Deferred):
            return other.__mod__(self)
        return _binop(ops.Modulus, other, self)

    def __rpow__(self, other: Any) -> NumericValue:
        """
        Handle other ** self, including Deferred ** NumericValue.

        Enables: ibis.literal(2) ** ibis._['col']
        """
        if isinstance(other, Deferred):
            return other.__pow__(self)
        return _binop(ops.Power, other, self)

    def __rfloordiv__(self, other: Any) -> NumericValue:
        """
        Handle other // self, including Deferred // NumericValue.

        Enables: ibis.literal(100) // ibis._['col']
        """
        if isinstance(other, Deferred):
            return other.__floordiv__(self)
        return _binop(ops.FloorDivide, other, self)
```

### Alternative Simpler Approach

If you want minimal code, use `NotImplemented` to let Python handle it:

```python
def __radd__(self, other: Any) -> NumericValue:
    """Handle other + self, including Deferred + NumericValue."""
    if isinstance(other, Deferred):
        # Let Deferred handle it
        return NotImplemented
    return _binop(ops.Add, other, self)
```

However, the explicit delegation approach is clearer and more predictable.

---

## Test Cases

### Test File Location

Create: `ibis/tests/expr/test_deferred_reverse_operators.py`

### Test Code

```python
"""Tests for reverse operators with Deferred column references."""
import pytest
import ibis
from ibis.common.deferred import Deferred


class TestDeferredReverseOperators:
    """Test that reverse operators work with Deferred objects."""

    def test_radd_literal_plus_deferred(self):
        """Test __radd__: literal + deferred column."""
        col = ibis._['x']
        lit = ibis.literal(5)

        # Should not raise
        result = lit + col

        # Verify it's a valid expression
        assert result is not None
        # Check string representation includes both operands
        result_str = str(result)
        assert 'x' in result_str or '_[' in result_str

    def test_rsub_literal_minus_deferred(self):
        """Test __rsub__: literal - deferred column."""
        col = ibis._['x']
        lit = ibis.literal(100)

        result = lit - col
        assert result is not None

    def test_rmul_literal_times_deferred(self):
        """Test __rmul__: literal * deferred column."""
        col = ibis._['x']
        lit = ibis.literal(3)

        result = lit * col
        assert result is not None

    def test_rtruediv_literal_divided_by_deferred(self):
        """Test __rtruediv__: literal / deferred column."""
        col = ibis._['x']
        lit = ibis.literal(100)

        result = lit / col
        assert result is not None

    def test_rmod_literal_modulo_deferred(self):
        """Test __rmod__: literal % deferred column."""
        col = ibis._['x']
        lit = ibis.literal(100)

        result = lit % col
        assert result is not None

    def test_rpow_literal_power_deferred(self):
        """Test __rpow__: literal ** deferred column."""
        col = ibis._['x']
        lit = ibis.literal(2)

        result = lit ** col
        assert result is not None

    def test_rfloordiv_literal_floordiv_deferred(self):
        """Test __rfloordiv__: literal // deferred column."""
        col = ibis._['x']
        lit = ibis.literal(100)

        result = lit // col
        assert result is not None

    def test_operator_symmetry_commutative_ops(self):
        """Test that commutative operations produce equivalent results."""
        col = ibis._['x']
        lit = ibis.literal(5)

        # Addition is commutative
        forward = col + lit
        reverse = lit + col

        # Both should produce valid expressions
        assert forward is not None
        assert reverse is not None

        # String representations should be equivalent (order may differ)
        # This is a basic check - exact equality depends on implementation
        assert str(forward) == str(reverse) or (
            'x' in str(forward) and 'x' in str(reverse)
        )

        # Multiplication is commutative
        forward = col * lit
        reverse = lit * col
        assert forward is not None
        assert reverse is not None

    def test_reverse_ops_work_with_bound_tables(self):
        """Test that reverse operators work with actual table data."""
        # Create a simple table
        import polars as pl
        conn = ibis.polars.connect()
        df = pl.DataFrame({'x': [1, 2, 3, 4, 5]})
        table = conn.create_table('test_table', df, overwrite=True)

        # Use reverse operator
        expr = ibis.literal(10) + ibis._['x']

        # This should compile and execute
        result = table.select(expr.name('result'))
        values = result['result'].execute().tolist()

        # Verify correct computation
        assert values == [11, 12, 13, 14, 15]

    @pytest.mark.parametrize('op_func,symbol,test_value', [
        (lambda a, b: a + b, '+', 5),
        (lambda a, b: a - b, '-', 10),
        (lambda a, b: a * b, '*', 3),
        (lambda a, b: a / b, '/', 100),
        (lambda a, b: a % b, '%', 7),
        (lambda a, b: a ** b, '**', 2),
        (lambda a, b: a // b, '//', 10),
    ])
    def test_all_reverse_operators_parametrized(self, op_func, symbol, test_value):
        """Parametrized test for all reverse operators."""
        col = ibis._['x']
        lit = ibis.literal(test_value)

        # Forward direction (should work before fix)
        result_forward = op_func(col, lit)
        assert result_forward is not None

        # Reverse direction (this is what we're fixing)
        result_reverse = op_func(lit, col)
        assert result_reverse is not None


class TestDeferredReverseOperatorsWithTypes:
    """Test reverse operators with different numeric types."""

    def test_radd_with_float(self):
        """Test reverse add with float literal."""
        col = ibis._['x']
        lit = ibis.literal(5.5)

        result = lit + col
        assert result is not None

    def test_radd_with_int(self):
        """Test reverse add with int literal."""
        col = ibis._['x']
        lit = ibis.literal(5)

        result = lit + col
        assert result is not None

    def test_mixed_type_operations(self):
        """Test reverse operators with mixed int/float types."""
        col_int = ibis._['int_col']
        col_float = ibis._['float_col']

        # Float literal + int column
        result1 = ibis.literal(5.5) + col_int
        assert result1 is not None

        # Int literal + float column
        result2 = ibis.literal(5) + col_float
        assert result2 is not None
```

---

## GitHub Workflow

### Step 1: Fork and Clone

```bash
# 1. Fork the repository on GitHub
# Go to: https://github.com/ibis-project/ibis
# Click "Fork" button (top right)

# 2. Clone YOUR fork (replace YOUR_USERNAME)
git clone https://github.com/YOUR_USERNAME/ibis.git
cd ibis

# 3. Add upstream remote (original ibis repo)
git remote add upstream https://github.com/ibis-project/ibis.git

# 4. Verify remotes
git remote -v
# Should show:
#   origin    https://github.com/YOUR_USERNAME/ibis.git (fetch)
#   origin    https://github.com/YOUR_USERNAME/ibis.git (push)
#   upstream  https://github.com/ibis-project/ibis.git (fetch)
#   upstream  https://github.com/ibis-project/ibis.git (push)
```

### Step 2: Set Up Development Environment

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install Ibis in development mode
pip install -e '.[dev]'

# 3. Install pre-commit hooks
pre-commit install

# 4. Verify installation
python -c "import ibis; print(ibis.__version__)"
```

### Step 3: Create Feature Branch

```bash
# 1. Ensure you're on main and up to date
git checkout main
git pull upstream main

# 2. Create feature branch
git checkout -b fix/deferred-reverse-operators

# Branch naming convention:
#   - fix/ for bug fixes
#   - feat/ for new features
#   - docs/ for documentation
#   - test/ for test additions
```

### Step 4: Make Changes

```bash
# 1. Create the test file first (TDD approach)
touch ibis/tests/expr/test_deferred_reverse_operators.py

# 2. Add test code (from Test Cases section above)
# Edit: ibis/tests/expr/test_deferred_reverse_operators.py

# 3. Run tests to confirm they FAIL (before fix)
pytest ibis/tests/expr/test_deferred_reverse_operators.py -v

# 4. Implement the fix
# Edit: ibis/expr/types/numeric.py
# Add reverse operators (from Code Changes section above)

# 5. Run tests to confirm they PASS (after fix)
pytest ibis/tests/expr/test_deferred_reverse_operators.py -v

# 6. Run full numeric test suite
pytest ibis/tests/expr/test_numeric.py -v

# 7. Run all tests (if you have time)
pytest
```

### Step 5: Commit Changes

```bash
# 1. Check what changed
git status
git diff

# 2. Stage changes
git add ibis/expr/types/numeric.py
git add ibis/tests/expr/test_deferred_reverse_operators.py

# 3. Commit with descriptive message
git commit -m "fix(expr): add reverse operators for Deferred arithmetic

Add __radd__, __rsub__, __rmul__, __rtruediv__, __rmod__, __rpow__,
and __rfloordiv__ methods to NumericValue class to support arithmetic
operations where Deferred is on the right side.

This fixes operator asymmetry where:
- ibis._['col'] + ibis.literal(5) worked
- ibis.literal(5) + ibis._['col'] failed with InputTypeError

The reverse operators check if the left operand is Deferred and
delegate to Deferred's forward operators to ensure proper expression
construction.

Fixes: #ISSUE_NUMBER (will add after filing issue)"

# Commit message format:
#   Line 1: type(scope): brief summary (50 chars max)
#   Line 2: blank
#   Line 3+: detailed explanation
#   Last line: Fixes: #ISSUE_NUMBER
```

### Step 6: Push to Your Fork

```bash
# Push feature branch to your fork
git push origin fix/deferred-reverse-operators

# If you need to make more commits:
git add <files>
git commit -m "message"
git push origin fix/deferred-reverse-operators
```

### Step 7: Create Pull Request

1. **Go to your fork on GitHub:**
   - https://github.com/YOUR_USERNAME/ibis

2. **GitHub will show a banner:**
   - "fix/deferred-reverse-operators had recent pushes"
   - Click **"Compare & pull request"**

3. **Fill out PR form:**

**Title:**
```
fix(expr): add reverse operators for Deferred arithmetic
```

**Description:**
```markdown
## Summary

Adds reverse arithmetic operators (`__radd__`, `__rsub__`, etc.) to `NumericValue` class to support operations where `Deferred` column references are on the right side of the operator.

## Problem

Currently, arithmetic operations with `Deferred` objects are not commutative:

```python
import ibis

col = ibis._['x']
lit = ibis.literal(5)

col + lit  # ✅ Works
lit + col  # ❌ Fails with InputTypeError
```

This violates Python's operator commutativity expectations and breaks expression building frameworks.

## Root Cause

- `Deferred` class has forward operators (`__add__`, etc.) that handle `ir.Expr` on the right
- `NumericValue` class has forward operators but lacks reverse operators
- When Python evaluates `literal + deferred`, it tries:
  1. `literal.__add__(deferred)` → returns `NotImplemented`
  2. `deferred.__radd__(literal)` → doesn't exist, raises error

## Solution

Added reverse operators to `NumericValue` that:
1. Check if left operand is `Deferred`
2. Delegate to `Deferred.__add__(self)` (swap operands)
3. Otherwise use standard `_binop()` logic

## Changes

- **ibis/expr/types/numeric.py**
  - Added `__radd__`, `__rsub__`, `__rmul__`, `__rtruediv__`
  - Added `__rmod__`, `__rpow__`, `__rfloordiv__`
  - All methods include docstrings and handle `Deferred` delegation

- **ibis/tests/expr/test_deferred_reverse_operators.py** (new file)
  - Comprehensive test suite for all reverse operators
  - Tests with literal values (int and float)
  - Tests operator symmetry and commutativity
  - Integration test with actual table data
  - Parametrized tests for all operators

## Testing

```bash
# All new tests pass
pytest ibis/tests/expr/test_deferred_reverse_operators.py -v

# Existing numeric tests still pass
pytest ibis/tests/expr/test_numeric.py -v
```

## Benefits

1. ✅ **Operator symmetry** - `a + b` and `b + a` now both work
2. ✅ **Python compliance** - Follows Python's numeric type behavior
3. ✅ **Framework support** - Enables expression builders to work seamlessly
4. ✅ **User experience** - Natural expressions like `5 + ibis._['col']` work as expected

## Closes

Fixes #ISSUE_NUMBER
```

4. **Select reviewers:**
   - GitHub will auto-suggest reviewers
   - Look for maintainers who work on `expr` module

5. **Add labels:**
   - `bug` (this fixes a bug)
   - `expr` (affects expression system)
   - `needs review`

6. **Click "Create pull request"**

### Step 8: File an Issue (Do This First!)

**Before creating the PR, file an issue to document the bug:**

1. **Go to:** https://github.com/ibis-project/ibis/issues/new

2. **Title:**
```
bug(expr): Reverse arithmetic operators fail with Deferred column references
```

3. **Body:**
```markdown
## What happened?

Arithmetic operations with `Deferred` column references (`ibis._['col']`) fail when the literal is on the left side of the operator.

## What did you expect to happen?

Arithmetic operators should be commutative - both `a + b` and `b + a` should work.

## Minimal Complete Verifiable Example

```python
import ibis

col = ibis._['x']
lit = ibis.literal(5)

# This works ✅
result = col + lit
print(result)  # Output: (_['x'] + <scalar[int8]>)

# This fails ❌
result = lit + col
# Traceback (most recent call last):
#   ...
# ibis.common.exceptions.InputTypeError: Unable to infer datatype of value _['x']
# with type <class 'ibis.common.deferred.Deferred'>
```

## Anything else?

**Affected operators:** All arithmetic operators (+, -, *, /, %, **, //)

**Root cause:** `NumericValue` class in `ibis/expr/types/numeric.py` has forward operators (`__add__`, etc.) but lacks reverse operators (`__radd__`, etc.) to handle `Deferred` objects on the right side.

**Impact:**
- Violates Python's operator commutativity expectations
- Breaks expression building frameworks that generate expressions programmatically
- Confusing user experience when natural expressions like `5 + ibis._['col']` don't work

**Proposed fix:** Add reverse operators (`__radd__`, `__rsub__`, etc.) to `NumericValue` class that check for `Deferred` and delegate appropriately.

I'm happy to submit a PR with tests if this is confirmed as a bug worth fixing.

## Version

```python
import ibis
print(ibis.__version__)
```

**Version:** [Run the code above and paste output here]

## Environment

- **OS:** Linux / macOS / Windows
- **Python version:** 3.12 (or your version)
- **Installation method:** pip / conda / from source
```

4. **Submit issue and wait for response**

5. **Once issue is acknowledged, reference it in your PR**

### Step 9: Respond to Review Feedback

```bash
# 1. Make requested changes
# Edit files as needed

# 2. Commit changes
git add <files>
git commit -m "address review feedback: <description>"

# 3. Push to your branch
git push origin fix/deferred-reverse-operators

# PR will automatically update
```

### Step 10: Squash Commits (if requested)

```bash
# If maintainers ask you to squash commits:

# 1. Interactive rebase
git rebase -i HEAD~3  # Squash last 3 commits (adjust number)

# 2. In editor, change 'pick' to 'squash' for commits to combine
# Save and close editor

# 3. Edit combined commit message
# Save and close editor

# 4. Force push (updates PR)
git push origin fix/deferred-reverse-operators --force
```

### Step 11: After PR is Merged

```bash
# 1. Switch to main
git checkout main

# 2. Pull latest from upstream (includes your changes)
git pull upstream main

# 3. Update your fork's main
git push origin main

# 4. Delete feature branch (optional cleanup)
git branch -d fix/deferred-reverse-operators
git push origin --delete fix/deferred-reverse-operators
```

---

## Checklist

### Before Filing Issue

- [ ] Verify bug with minimal reproducer
- [ ] Check no existing issues for this problem
- [ ] Document all affected operators
- [ ] Test on latest Ibis version

### Before Creating PR

- [ ] Issue filed and acknowledged
- [ ] Fork created
- [ ] Development environment set up
- [ ] Feature branch created

### Code Changes

- [ ] Tests written FIRST (TDD)
- [ ] Tests fail before fix
- [ ] Fix implemented
- [ ] Tests pass after fix
- [ ] Existing tests still pass
- [ ] Code follows Ibis style guide
- [ ] Docstrings added to new methods
- [ ] Import added for `Deferred`

### Git Hygiene

- [ ] Commits are logical and atomic
- [ ] Commit messages are descriptive
- [ ] No merge commits (use rebase)
- [ ] Branch rebased on latest main

### PR Submission

- [ ] PR title follows convention
- [ ] Description is comprehensive
- [ ] Links to issue with "Fixes #XXX"
- [ ] All CI checks pass
- [ ] Ready for review

---

## Additional Resources

### Ibis Documentation

- **Contributing Guide:** https://github.com/ibis-project/ibis/blob/main/CONTRIBUTING.md
- **Development Setup:** https://ibis-project.org/contribute/01_environment
- **Code Style:** https://ibis-project.org/contribute/02_style
- **Testing Guide:** https://ibis-project.org/contribute/03_testing

### Python Operator Overloading

- **Python Data Model:** https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types
- **Reverse Operators:** https://docs.python.org/3/reference/datamodel.html#object.__radd__

### Git Workflow

- **Forking Workflow:** https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow
- **Writing Good Commits:** https://chris.beams.io/posts/git-commit/
- **Interactive Rebase:** https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History

---

## Questions?

If you have questions during the process:

1. **Check Ibis contributing docs first**
2. **Search existing issues/PRs** for similar situations
3. **Ask in Ibis community channels:**
   - Zulip: https://ibis-project.zulipchat.com
   - GitHub Discussions: https://github.com/ibis-project/ibis/discussions

---

## Expected Timeline

- **Issue filing:** 5-10 minutes
- **Issue response:** 1-3 days (maintainers are responsive)
- **Development:** 1-2 hours
- **PR review:** 3-7 days (first round)
- **Revisions:** 1-2 hours
- **Merge:** 1-2 weeks from initial submission

**Total:** ~2 weeks from start to merge (typical for straightforward bug fixes)

Good luck with your first Ibis contribution! 🚀
