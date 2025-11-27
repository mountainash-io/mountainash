# Complete Investigation Index

## Investigation Summary

This directory contains a comprehensive investigation into the Ibis-Polars integer overflow bug, from initial discovery through root cause analysis to proposed fixes.

---

## Reading Order

### For Quick Understanding

1. **SIMPLE_ANSWER.md** - 5-minute explanation with diagrams
2. **EXECUTIVE_SUMMARY.md** - For decision makers
3. **TLDR_IBIS_IS_THE_CULPRIT.md** - Visual flow diagram

### For Technical Understanding

4. **COMPREHENSIVE_IBIS_POLARS_ANALYSIS.md** - Complete technical analysis
5. **WHY_SQL_BACKENDS_WORK.md** - Why SQL backends don't have this problem
6. **DEEP_DIVE_SUMMARY.md** - Literal vs column type resolution

### For Implementation

7. **Ibis/IBIS_POW_FIX_PROPOSAL.md** - Proposed fix with code
8. **Ibis/LITERAL_VS_COLUMN_TYPE_RESOLUTION.md** - Type system analysis
9. **Ibis/CODE_PATH_COMPARISON.md** - Side-by-side code paths

---

## File Organization

### Root Directory (`docs/Bug Reports/`)

#### Overview Documents
- **INDEX.md** - This file
- **EXECUTIVE_SUMMARY.md** - For decision makers
- **INVESTIGATION_COMPLETE.md** - Full investigation timeline
- **COMPREHENSIVE_IBIS_POLARS_ANALYSIS.md** - Complete technical analysis

#### Key Findings
- **SIMPLE_ANSWER.md** - Quick visual explanation
- **TLDR_IBIS_IS_THE_CULPRIT.md** - Flow diagram
- **WHY_SQL_BACKENDS_WORK.md** - SQL vs Polars comparison
- **POLARS_CORRECTNESS_DEBATE.md** - Technical vs practical correctness

### Ibis Analysis (`Ibis/`)

#### Core Analysis
- **DEEP_DIVE_SUMMARY.md** - Literal vs column type resolution
- **LITERAL_VS_COLUMN_TYPE_RESOLUTION.md** - Detailed type system analysis
- **CODE_PATH_COMPARISON.md** - Side-by-side code paths
- **BACKEND_COMPARISON_RESULTS.md** - Test results across backends

#### Proposals
- **LHS Literals/IBIS_POW_FIX_PROPOSAL.md** - Original fix proposal
- **test_literal_vs_column_types.py** - Demonstration code
- **test_ibis_literal_aggressive_downcast.py** - Type inference test
- **test_sql_backend_literal_generation.py** - SQL generation test
- **comprehensive_backend_comparison.py** - Cross-backend comparison

### Polars Analysis (`Polars/`)

*Early investigation before we discovered it was an Ibis issue*

#### Analysis
- **POLARS_TECHNICAL_ANALYSIS.md** - Power operation analysis
- **CODE_ANALYSIS_SUMMARY.md** - Polars source code analysis
- **FINAL_SUMMARY_BOTH_INT8.md** - Int8 behavior summary
- **BACKEND_INCONSISTENCIES.md** - Backend differences

#### Tests
- **minimal_multiplication_upcast_example.py** - Multiplication vs power
- **exact_upcast_pattern.py** - Type promotion patterns
- **int8_both_sides_comparison.py** - Int8 edge cases
- **test_polars_overflow_behavior.py** - Overflow tests

---

## Key Findings

### The Root Cause

**Ibis aggressively downcasts literals** to the smallest possible type:
- `ibis.literal(2)` → `int8` (8-bit)
- But DataFrames use `int64` (64-bit)

**This creates an asymmetry:**
- `literal(2) ** column(10)` → 0 ❌ (overflow in int8)
- `column(2) ** column(10)` → 1024 ✅ (safe in int64)

### Why SQL Backends Work

SQL backends generate **untyped literals**:
```sql
SELECT POWER(2, x) FROM table;
```

Databases choose INT or BIGINT (32/64-bit), not TINYINT (8-bit).

Polars backend uses **typed API**:
```python
pl.lit(2, dtype=pl.Int8).pow(pl.col('x'))
```

Polars respects the explicit Int8, causing overflow.

### The Fix

**File:** `ibis/backends/polars/compiler.py`

**Current:**
```python
return pl.lit(value, dtype=pl.Int8)
```

**Fixed:**
```python
return pl.lit(value)  # Let Polars choose
```

---

## Test Files

### Runnable Tests

```bash
# Cross-backend comparison
python docs/Bug\ Reports/Ibis/comprehensive_backend_comparison.py

# Literal vs column types
python docs/Bug\ Reports/Ibis/test_literal_vs_column_types.py

# Type inference demonstration
python docs/Bug\ Reports/Ibis/test_ibis_literal_aggressive_downcast.py

# SQL generation
python docs/Bug\ Reports/Ibis/test_sql_backend_literal_generation.py

# Polars direct tests
python docs/Bug\ Reports/Polars/exact_upcast_pattern.py
python docs/Bug\ Reports/Polars/int8_both_sides_comparison.py
```

### Expected Results

All tests show:
1. Ibis infers int8 for small literals
2. DataFrames use int64 by default
3. Polars backend passes explicit Int8
4. SQL backends generate untyped literals
5. Only Polars backend fails (due to explicit types)

---

## Key Source Code Locations

### Ibis

1. **Literal type inference:**
   - `ibis/expr/datatypes/value.py:128-135`
   - Function: `infer_integer()`
   - Issue: Returns smallest type that fits

2. **Polars backend literal translation:**
   - `ibis/backends/polars/compiler.py:85-110`
   - Function: `literal()`
   - Issue: Passes explicit narrow dtype to Polars

3. **SQL backend literal translation:**
   - `ibis/backends/sql/compilers/base.py:778-779`
   - Function: `visit_DefaultLiteral()`
   - Correct: Generates untyped SQL literal

### Polars

1. **Power operation:**
   - `polars/crates/polars-expr/src/dispatch/pow.rs:108-160`
   - Respects explicit dtypes (correct behavior)

2. **Type coercion (for other operations):**
   - `polars/crates/polars-plan/src/plans/conversion/type_coercion/binary.rs:242`
   - Calls `get_supertype()` for multiplication, but not power

---

## Timeline

1. **Initial Discovery:** `literal(2) ** column` returns 0
2. **Polars Investigation:** Found power doesn't promote like multiplication
3. **Polars Team Response:** "This is correct behavior"
4. **Pivot:** Realized Ibis is passing explicit Int8
5. **Ibis Investigation:** Found aggressive type downcasting
6. **Root Cause:** Asymmetry between literal and column types
7. **Solution:** Don't pass explicit types to Polars

---

## Impact

### Affected

- Any Ibis code using Polars backend
- Literals in arithmetic operations
- Power, multiplication with overflow risk
- Financial calculations, scientific computing

### Not Affected

- DuckDB backend (uses SQL)
- SQLite backend (uses SQL)
- Column-only operations
- Operations without overflow

### Severity

- **High:** Silent data corruption
- **Common:** Affects all literal operations
- **Surprising:** Violates user expectations
- **Fixable:** One-line change

---

## Recommendations

### Immediate

1. Use DuckDB backend instead of Polars
2. Cast literals to int64: `ibis.literal(2).cast('int64')`
3. Audit existing code for overflow risk

### Short-term

1. Submit PR to Ibis Polars backend
2. Don't pass explicit dtypes for numeric literals
3. Add tests to prevent regression

### Long-term

1. Change Ibis literal inference to match DataFrames
2. Use int64 by default (like Polars/Pandas)
3. Document the behavior

---

## For Different Audiences

### For Analysts

**Start here:**
- SIMPLE_ANSWER.md
- WHY_SQL_BACKENDS_WORK.md
- POLARS_CORRECTNESS_DEBATE.md

**Key point:** You're right - this is wrong from a business perspective!

### For Developers

**Start here:**
- COMPREHENSIVE_IBIS_POLARS_ANALYSIS.md
- CODE_PATH_COMPARISON.md
- DEEP_DIVE_SUMMARY.md

**Key point:** Literal vs column type asymmetry is the root cause.

### For Decision Makers

**Start here:**
- EXECUTIVE_SUMMARY.md
- INVESTIGATION_COMPLETE.md

**Key point:** Fix is simple, impact is high, solution is clear.

---

## Credits

Investigation conducted through iterative analysis:
1. Polars source code examination
2. Ibis source code examination
3. Cross-backend testing
4. Type system analysis

All files generated during November 2024 investigation.

---

## Next Steps

1. ✅ Investigation complete
2. ⏭️ Submit issue to Ibis project
3. ⏭️ Submit PR with fix
4. ⏭️ Add tests
5. ⏭️ Document workarounds for users

---

## Quick Links

- [Polars Issue #25213](https://github.com/pola-rs/polars/issues/25213)
- Ibis Issue: TBD
- Ibis PR: TBD
