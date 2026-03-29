# How to File the Ibis Reverse Operator Bug

## Quick Summary

**Issue:** Reverse arithmetic operators fail when literal is on left, Deferred column on right
**Affects:** All backends (core expression layer bug)
**Example:** `ibis.literal(5) + ibis._['col']` fails, but `ibis._['col'] + ibis.literal(5)` works

## Files Prepared

1. **`IBIS_GITHUB_ISSUE.md`** - Complete issue text ready to copy/paste
2. **`ibis_reverse_operator_repro_final.py`** - Minimal reproduction script (simple)
3. **`ibis_reverse_operator_minimal_repro.py`** - Full reproduction with cross-backend comparison

## Steps to File Issue

### 1. Go to Ibis Issues Page
https://github.com/ibis-project/ibis/issues/new/choose

### 2. Select "Bug Report"

### 3. Copy Content from IBIS_GITHUB_ISSUE.md

The issue is already formatted following your #11740 format:
- Title: `bug: Reverse arithmetic operators fail with Deferred column references`
- All sections filled out (What happened, Reproduction, Output, Version, etc.)

### 4. Paste the Reproduction Code

The reproduction code is in the issue, but you can test it locally first:

```bash
# Simple version (recommended for issue)
python docs/ibis_reverse_operator_repro_final.py

# Full cross-backend version (for your reference)
python docs/ibis_reverse_operator_minimal_repro.py
```

### 5. Check the Output

You should see:
```
✓ Success: [15, 25, 35]  <- col + lit works
✗ Failed: InputTypeError <- lit + col fails
```

## Issue Structure (Following Your #11740 Format)

✅ **Title:** Short, descriptive, with `bug:` prefix
✅ **The problem:** Clear explanation of the bug
✅ **Possible solution:** Specific code location and fix suggestion
✅ **Reproduction:** Complete, runnable code
✅ **Output:** Table showing the issue across backends
✅ **Version:** 11.0.0
✅ **Backend(s):** All backends (core expression layer)
✅ **Relevant log output:** Full error traceback
✅ **Code of Conduct:** Checkbox marked

## Key Points to Emphasize

1. **Affects ALL backends** - not backend-specific
2. **Core expression layer bug** - missing reverse operators in NumericValue class
3. **Breaks Python expectations** - violates operator commutativity
4. **Specific to Deferred** - `ibis._['col']` not `table.col`
5. **Simple fix** - add `__radd__`, `__rsub__`, etc. methods

## Suggested Fix Location

Point to the exact file in the issue:
```
ibis/expr/types/numeric.py
```

The NumericValue class needs reverse operators that delegate to Deferred when appropriate.

## Related Documentation

If they ask for more context, you can reference:
- Your verification script: `docs/ibis_fix_verification.py`
- Detailed analysis: `docs/_IBIS_REVERSE_OPERATOR_BUG_FIX.md`
- Your warning implementation: `src/mountainash_expressions/backends/ibis/expression_system/ibis_expression_system.py`

## After Filing

1. Note the issue number
2. Reference it in your code comments
3. Update `IBIS_REVERSE_OPERATOR_WORKAROUND.md` with issue link
4. Add issue link to warning message (optional)

## Example of What to Expect

Based on your #11740 experience:
- Maintainers are responsive (1-3 days)
- They may ask clarifying questions
- They may suggest alternative fixes
- Fix timeframe: likely 1-2 weeks if accepted

## If They Ask Questions

Be ready to:
- Explain why you're using Deferred syntax (expression building frameworks)
- Show that it works with bound columns but not Deferred
- Explain impact on your mountainash-expressions library
- Provide additional test cases if needed
