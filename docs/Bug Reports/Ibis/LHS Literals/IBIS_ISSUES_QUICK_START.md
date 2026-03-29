# Quick Start: Filing Ibis Reverse Operator Issues

Two separate GitHub issues ready to file for the Ibis project.

## Prerequisites

1. GitHub account
2. Navigate to: https://github.com/ibis-project/ibis/issues/new/choose
3. Select "Bug Report"

---

## Issue 1: Numeric Reverse Operators

### Title
```
bug: Reverse arithmetic operators fail with Deferred column references
```

### Issue Body
**Copy from:** `IBIS_GITHUB_ISSUE.md`
- Entire file contents can be used as-is
- Already formatted for GitHub markdown

### Key Points
- **Affects:** IntegerScalar, FloatingScalar (11 operations)
- **Fix:** One line change in `ibis/expr/types/core.py`
- **Error:** `InputTypeError: Unable to infer datatype of value _['value']`

### Minimal Reproduction
```python
import ibis
import polars as pl

conn = ibis.polars.connect()
df = pl.DataFrame({'value': [10]})
table = conn.create_table('test', df, overwrite=True)

lit = ibis.literal(5)
col = ibis._['value']

# This works ✅
expr = col + lit
result = table.select(expr.name('result')).execute()
print(f"col + lit: {result['result'].tolist()}")  # [15]

# This fails ❌
expr = lit + col
result = table.select(expr.name('result')).execute()  # InputTypeError
```

---

## Issue 2: String Concatenation

### Title
```
bug: String concatenation reverse operators fail with Deferred column references
```

### Issue Body
**Copy from:** `IBIS_STRINGVALUE_GITHUB_ISSUE.md`
- Entire file contents can be used as-is
- Already formatted for GitHub markdown

### Key Points
- **Affects:** StringScalar (1 operation: concatenation)
- **Fix:** Three lines (add try/except) in `ibis/expr/types/strings.py`
- **Error:** `SignatureValidationError: Function 'StringConcat' expects ...`

### Minimal Reproduction
```python
import ibis
import polars as pl

conn = ibis.polars.connect()
df = pl.DataFrame({'name': ['hello']})
table = conn.create_table('test', df, overwrite=True)

lit_str = ibis.literal(' world')
col_str = ibis._['name']

# This works ✅
expr = col_str + lit_str
result = table.select(expr.name('result')).execute()
print(f"col + lit: {result['result'].tolist()}")  # ['hello world']

# This fails ❌
expr = lit_str + col_str
result = table.select(expr.name('result')).execute()  # SignatureValidationError
```

---

## Filing Order

### Recommended: Issue 1 First
1. File Issue 1 (numeric operators) first
2. Wait for issue number (e.g., #12345)
3. Update `IBIS_STRINGVALUE_GITHUB_ISSUE.md` line 301 to reference Issue 1
4. File Issue 2 (string concatenation)

**Why this order:**
- Issue 1 affects more operations (11 vs 1)
- Issue 1 is simpler (one line change)
- Issue 2 can reference Issue 1 to show the pattern

### Alternative: File Together
File both issues simultaneously and cross-reference in comments after both are created.

---

## After Filing

### Update Local Documentation
1. Note issue numbers in `IBIS_ISSUES_SUMMARY.md`
2. Add links to actual GitHub issues
3. Update `IBIS_REVERSE_OPERATOR_WORKAROUND.md` with issue links

### Example Update:
```markdown
## Related GitHub Issues
- Issue #12345: Numeric reverse operators
- Issue #12346: String concatenation reverse operators
```

---

## Checklist

### Before Filing Issue 1
- [ ] Have GitHub account and are logged in
- [ ] Have read through `IBIS_GITHUB_ISSUE.md`
- [ ] Can run minimal reproduction locally
- [ ] Ready to copy full issue body

### Before Filing Issue 2
- [ ] Have filed Issue 1 (or ready to file simultaneously)
- [ ] Have read through `IBIS_STRINGVALUE_GITHUB_ISSUE.md`
- [ ] Can run minimal reproduction locally
- [ ] Ready to copy full issue body
- [ ] Updated line 301 reference if filing after Issue 1

### After Filing Both
- [ ] Note issue numbers
- [ ] Update local documentation
- [ ] Remove warning from mountainash-expressions if desired
- [ ] Wait for Ibis team response

---

## Important Notes

### Both Issues Are Well-Documented
- Complete reproductions included
- Fix locations clearly identified
- Safety analysis provided
- Impact assessment included
- Workarounds documented

### Expected Response Time
Based on previous Ibis issues:
- Initial response: 1-3 days
- Fix implementation: 1-2 weeks
- Release: Next Ibis version

### If Asked for More Info
All supporting files are in `docs/`:
- `ibis_reverse_operator_comprehensive_repro.py` - Comprehensive test
- `ibis_reverse_operator_code_path_analysis.py` - Deep dive
- `ibis_stringvalue_concat_fix.py` - StringValue demo
- `IBIS_INPUTTYPEERROR_SAFETY_ANALYSIS.md` - Safety proof

### Labels to Suggest
When filing, you might suggest:
- **Type:** `bug`
- **Area:** `expr` or `expressions`
- **Priority:** `medium` (breaks symmetry but has workarounds)

---

## Quick Commands

### Test Both Issues Locally

**Issue 1 (Numeric):**
```bash
cd /home/nathanielramm/git/mountainash/mountainash-expressions
python docs/ibis_reverse_operator_comprehensive_repro.py
```

**Issue 2 (String):**
```bash
cd /home/nathanielramm/git/mountainash/mountainash-expressions
python docs/ibis_stringvalue_concat_fix.py
```

**Both (Full Analysis):**
```bash
cd /home/nathanielramm/git/mountainash/mountainash-expressions
python docs/ibis_reverse_operator_code_path_analysis.py
```

---

## What to Expect

### Likely Ibis Team Questions
1. ✅ "Can you provide a minimal reproduction?" - Already included
2. ✅ "What version of Ibis?" - 11.0.0 (specified in issues)
3. ✅ "Which backends?" - All (specified in issues)
4. ✅ "Do you have a fix?" - Yes, both fixes are documented
5. ✅ "Is it safe?" - Yes, safety analysis provided

### Possible Outcomes
1. **Quick acceptance** - Issues are well-documented, fixes are clear
2. **Discussion about approach** - May suggest alternative fixes
3. **Request to combine** - May prefer one issue instead of two
4. **Request for PR** - May ask you to submit the fixes

### If Asked to Submit PR
Both fixes are simple and well-documented:
- Fork the Ibis repository
- Create branch: `fix/reverse-operator-deferred`
- Apply fixes from documentation
- Submit PR referencing issues
- All test cases are in the issue for validation

---

## Success Criteria

### Issue 1 Success
After fix is merged:
```python
# All should work
ibis.literal(5) + ibis._['x']      # ✅
ibis.literal(2.5) + ibis._['x']    # ✅
ibis.literal(100) - ibis._['x']    # ✅
# ... all 11 operations
```

### Issue 2 Success
After fix is merged:
```python
# Should work
ibis.literal(' world') + ibis._['name']  # ✅
```

### Overall Success
All 14 operations across all scalar types work correctly with reverse operators! 🎉
