# Ibis Reverse Operator Bug - Documentation

## Overview

This directory contains complete documentation for contributing a bug fix to the Ibis project.

**Bug:** Reverse arithmetic operators fail with `Deferred` column references
**Impact:** Breaks operator commutativity and expression builders
**Status:** Undiscovered - no existing issues in Ibis tracker
**Difficulty:** Low - straightforward fix with clear solution

---

## Files in This Directory

### 📘 IBIS_REVERSE_OPERATOR_BUG_FIX.md
**The comprehensive guide** - Everything you need to know:
- Detailed bug description and reproduction
- Root cause technical analysis
- Complete proposed fix with code
- Full GitHub workflow (fork, clone, branch, commit, PR)
- Test cases and verification
- Issue and PR templates
- Timeline and checklist

**When to use:** Full reference guide, first-time contributors

---

### ⚡ IBIS_PR_QUICK_START.md
**The quick reference** - Essential commands and steps:
- TL;DR of the bug
- Copy-paste commands
- Minimal code snippets
- Quick checklist
- 2-page printable guide

**When to use:** Quick lookup, experienced contributors

---

### 🔬 ibis_reverse_operator_reproducer.py
**The executable reproducer** - Automated bug demonstration:
- Runs comprehensive operator tests
- Tests with real data
- Shows exact error messages
- Suggests fix preview
- Perfect for GitHub issue attachments

**Usage:**
```bash
python docs/ibis_reverse_operator_reproducer.py
```

**Output:** Clear bug demonstration with ✅/❌ indicators

---

## Quick Start

### Option 1: I want step-by-step guidance
→ Read `IBIS_REVERSE_OPERATOR_BUG_FIX.md`

### Option 2: I know Git workflows, give me the code
→ Read `IBIS_PR_QUICK_START.md`

### Option 3: Show me the bug first
→ Run `python docs/ibis_reverse_operator_reproducer.py`

---

## The Bug in 30 Seconds

```python
import ibis

# This works ✅
ibis._['x'] + ibis.literal(5)

# This fails ❌
ibis.literal(5) + ibis._['x']
# InputTypeError: Unable to infer datatype of value _['x']
```

**Why:** `NumericValue` class lacks `__radd__`, `__rsub__`, etc.

**Fix:** Add reverse operators that delegate to `Deferred`

**Impact:** Affects all 7 arithmetic operators (+, -, *, /, %, **, //)

---

## Repository Structure

```
docs/
├── IBIS_BUG_README.md                          # This file
├── IBIS_REVERSE_OPERATOR_BUG_FIX.md            # Complete guide
├── IBIS_PR_QUICK_START.md                      # Quick reference
└── ibis_reverse_operator_reproducer.py         # Automated reproducer
```

---

## Workflow Summary

1. **Verify bug** → Run reproducer script
2. **Read guide** → Choose comprehensive or quick start
3. **File issue** → Use template from guide
4. **Fork & clone** → Follow git workflow
5. **Add code** → Copy from guide (2 files)
6. **Run tests** → Verify fix works
7. **Create PR** → Use template from guide
8. **Get reviewed** → Respond to feedback
9. **Get merged** → Celebrate! 🎉

**Estimated time:** 2-3 hours of work, ~2 weeks to merge

---

## Key Changes Required

### File 1: `ibis/expr/types/numeric.py`
Add 7 reverse operators to `NumericValue` class:
- `__radd__`, `__rsub__`, `__rmul__`, `__rtruediv__`
- `__rmod__`, `__rpow__`, `__rfloordiv__`

**Lines of code:** ~70 (with docstrings)

### File 2: `ibis/tests/expr/test_deferred_reverse_operators.py`
New test file with comprehensive coverage:
- Individual tests for each operator
- Parametrized tests
- Integration test with real data
- Type variant tests

**Lines of code:** ~150

**Total:** 2 files, ~220 lines (including docs)

---

## Why This Matters

### For Ibis
- ✅ Fixes operator symmetry bug
- ✅ Improves Python compliance
- ✅ Better user experience
- ✅ Enables expression builder frameworks

### For You
- 🎯 High-impact, low-risk contribution
- 📚 Great learning experience
- 🤝 Join active open-source community
- ⭐ Recognized contribution to popular project

### For mountainash-expressions
- 🔧 Fixes our Ibis backend completely
- ✅ Enables all reverse operator tests to pass
- 🚀 Full cross-backend compatibility achieved

---

## Testing the Fix Locally

Before submitting PR, verify the fix works:

```bash
# 1. Apply the fix to your local Ibis clone
# (Edit ibis/expr/types/numeric.py)

# 2. Run the reproducer again
python docs/ibis_reverse_operator_reproducer.py

# Expected: ✅ All operators working correctly!

# 3. Run mountainash-expressions tests
cd /home/nathanielramm/git/mountainash/mountainash-expressions
hatch run test:test-quick tests/cross_backend/test_expression_builder_api.py

# Expected: All reverse operator tests pass!
```

---

## Resources

- **Ibis Repository:** https://github.com/ibis-project/ibis
- **Ibis Contributing:** https://github.com/ibis-project/ibis/blob/main/CONTRIBUTING.md
- **Ibis Docs:** https://ibis-project.org
- **Python Operators:** https://docs.python.org/3/reference/datamodel.html#object.__radd__

---

## Support

If you have questions:

1. Check the comprehensive guide first
2. Search existing Ibis issues/PRs
3. Ask in Ibis community:
   - Zulip: https://ibis-project.zulipchat.com
   - Discussions: https://github.com/ibis-project/ibis/discussions

---

## Success Criteria

✅ Issue filed and acknowledged
✅ PR created with tests
✅ All CI checks pass
✅ Code review feedback addressed
✅ PR merged to main
✅ Fix available in next Ibis release

---

## Timeline (Typical)

- **Day 1:** File issue, fork repo, create branch
- **Day 1-2:** Implement fix and tests
- **Day 2:** Create PR
- **Day 3-5:** Initial review
- **Day 5-7:** Address feedback
- **Week 2:** PR merged
- **Week 4-8:** Released in next version

---

## After Your PR is Merged

1. Update mountainash-expressions to use new Ibis version
2. Remove any workarounds for reverse operators
3. Re-run all cross-backend tests
4. Celebrate your contribution! 🎊

---

**Ready to contribute?** Start with `IBIS_REVERSE_OPERATOR_BUG_FIX.md`!

**Need quick reference?** Use `IBIS_PR_QUICK_START.md`!

**Want to see the bug?** Run `ibis_reverse_operator_reproducer.py`!
