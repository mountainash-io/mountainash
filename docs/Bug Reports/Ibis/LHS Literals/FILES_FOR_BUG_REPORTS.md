# Files to Include with Bug Reports

## For Polars Team

### Primary Documents
1. **`POLARS_BUG_REPORT.md`** - Formal bug report with examples
2. **`POLARS_TECHNICAL_ANALYSIS.md`** - Detailed technical analysis

### Reproduction Scripts (Attach All)
1. **`polars_bug_minimal_repro.py`** - Simple 4-case reproduction
   - Shows both `.pow()` and `**` fail
   - Shows without dtype works
   - **New**: Includes multiplication comparison

2. **`test_polars_overflow_behavior.py`** - Overflow behavior comparison
   - Shows multiplication wraps/upcasts correctly
   - Shows power returns 0 incorrectly
   - Demonstrates the critical difference

3. **`investigate_polars_upcasting.py`** - Comprehensive operation analysis
   - Tests ALL arithmetic operations
   - Shows power is the ONLY one that doesn't upcast
   - Clear table format showing the pattern

4. **`polars_source_investigation.py`** - Expression representation
   - Shows internal expression structures
   - Demonstrates schema differences
   - Proves the bug at the expression level

### Key Points to Emphasize

**Subject**: Power operations don't auto-upcast like other arithmetic operations

**Key Evidence**:
```python
# ALL other operations upcast with literal-column:
Int8(63) * col(63)   → Int64: 3969 ✅
Int8(10) + col(63)   → Int64: 73   ✅
Int8(100) // col(63) → Int64: 1    ✅
Int8(100) % col(63)  → Int64: 37   ✅

# Power does NOT upcast:
Int8(2) ** col(10)   → Int8: 0     ❌
```

**The Ask**:
Make power operations use the same type promotion logic as multiplication.

---

## For Ibis Team

### Primary Documents
1. **`IBIS_BUG_REPORT_POW.md`** - Formal bug report with examples
2. **`IBIS_POW_FIX_PROPOSAL.md`** - Detailed fix proposal

### Reproduction Scripts (Attach All)
1. **`ibis_bug_minimal_repro.py`** - Shows Polars backend fails
   - Compares DuckDB (works), SQLite (works), Polars (fails)
   - Shows casting workaround
   - Clear before/after comparison

2. **`power_operator_comparison.py`** - Comprehensive comparison
   - Side-by-side Ibis vs Polars results
   - Tests multiple type widths
   - Shows casting fixes the issue

3. **`ibis_polars_comparison.py`** - Original operator comparison
   - Tests all operators, not just power
   - Shows power as part of larger pattern

### Key Points to Emphasize

**Subject**: Polars backend: Power operator returns 0 due to narrow type enforcement

**Key Evidence**:
```python
# Other backends work:
DuckDB:  literal(2) ** col(10) → 1024 ✅
SQLite:  literal(2) ** col(10) → 1024 ✅
Polars:  literal(2) ** col(10) → 0    ❌

# Root cause:
ibis.literal(2)              → Int8
Polars backend:  pl.lit(2, dtype=Int8)
Polars bug:      Int8 ** col doesn't upcast → 0
```

**The Fix** (one line in `compiler.py`):
```python
elif dtype.is_integer():
    return pl.lit(value)  # Let Polars infer type
```

**The Ask**:
Don't enforce narrow integer types in Polars backend literals.

---

## Additional Reference Documents

### Analysis Documents
- `POWER_OPERATOR_ANALYSIS.md` - Executive summary of the issue
- `BUG_REPORTS_SUMMARY.md` - Overview of both bugs and their relationship

### Supporting Scripts
- `test_ibis_literal_dtype.py` - Shows Ibis type inference
- `test_cast_vs_literal_translation.py` - Shows why casting works
- `test_polars_strict_cast_pow.py` - Investigation into strict_cast

### Related PR
- `IBIS_PR_DESCRIPTION.md` - Separate bug (reverse operators) already fixed

---

## Submission Checklist

### Polars Bug Report
- [ ] Include `POLARS_BUG_REPORT.md` in issue body
- [ ] Attach `polars_bug_minimal_repro.py` (make it easy to run)
- [ ] Reference `POLARS_TECHNICAL_ANALYSIS.md` for details
- [ ] Attach comparison scripts showing inconsistency
- [ ] Emphasize: "Power doesn't upcast like multiplication does"
- [ ] Tags: bug, arithmetic, type-promotion, silent-failure

### Ibis Bug Report
- [ ] Include `IBIS_BUG_REPORT_POW.md` in issue body
- [ ] Attach `ibis_bug_minimal_repro.py` (includes backend comparison)
- [ ] Include one-line fix in `IBIS_POW_FIX_PROPOSAL.md`
- [ ] Attach `power_operator_comparison.py` for comprehensive testing
- [ ] Reference upstream Polars bug (link once created)
- [ ] Tags: bug, polars-backend, type-inference, overflow

---

## Talking Points

### For Polars Team

**Why this matters:**
1. Inconsistent with ALL other arithmetic operations
2. Silent data corruption (returns 0, no warning)
3. Breaks user expectations (multiplication upcasts, power doesn't)
4. Impacts downstream frameworks (Ibis, etc.)

**Expected behavior:**
Power should auto-upcast when operands are `(literal, column)` or `(column, literal)`, just like multiplication does.

### For Ibis Team

**Why this matters:**
1. Only Polars backend affected (DuckDB, SQLite work)
2. Produces silently wrong results (0 instead of 1024)
3. One-line fix available
4. Fully backward compatible

**Why fix in Ibis even if Polars fixes:**
- Immediate relief for users
- Works around any Polars version issues
- Consistent with how other backends handle it
- No downside (Polars infers appropriate types)

---

## Timeline

1. **Submit Polars bug report first** - They own the core issue
2. **Wait for Polars ticket number** - Reference it in Ibis report
3. **Submit Ibis bug report** - Link to Polars issue
4. **Follow up** - Track both issues, offer to test fixes

---

## Expected Questions

### From Polars Team

**Q: Why not just wrap like literal-literal does?**
A: Because multiplication with columns already upcasts to Int64. Power should be consistent.

**Q: Won't this break existing code?**
A: No, it only fixes cases that currently return wrong results (0).

**Q: Why does `col.pow(lit)` work but not `lit.pow(col)`?**
A: Type promotion logic only triggers when base is a column, not when exponent is.

### From Ibis Team

**Q: Can't users just cast to int64?**
A: Yes, but they shouldn't have to. Other backends work without casting.

**Q: Will this change type inference behavior?**
A: No, only for Polars backend, and only to let Polars choose types (which it does correctly).

**Q: What about the upstream Polars bug?**
A: Even when Polars fixes it, this change makes Ibis more robust and consistent.
