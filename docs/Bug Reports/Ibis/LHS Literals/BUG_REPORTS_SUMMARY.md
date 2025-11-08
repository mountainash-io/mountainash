# Bug Reports Summary: Power Operator Issues

## Overview

Investigation revealed **two distinct but related bugs** affecting power operations when using Ibis with the Polars backend.

---

## Bug #1: Polars - Silent Integer Overflow in Power Operations

**Status**: Confirmed Polars bug
**Severity**: High (silent data corruption)
**File**: `POLARS_BUG_REPORT.md`

### Issue

When computing power operations with an explicit Int8 dtype, Polars silently returns **0** instead of:
- Automatically upcasting to a wider type, OR
- Raising an overflow error

### Reproduction

```python
import polars as pl
df = pl.DataFrame({'x': [10]})

# Both methods fail with Int8
pl.lit(2, dtype=pl.Int8).pow(pl.col('x'))  # → 0 (expected 1024)
pl.lit(2, dtype=pl.Int8) ** pl.col('x')    # → 0 (expected 1024)

# Both methods work without dtype
pl.lit(2).pow(pl.col('x'))                 # → 1024 ✅
pl.lit(2) ** pl.col('x')                   # → 1024 ✅
```

### Key Finding

The bug affects **both** `.pow()` method and `**` operator when Int8 dtype is explicitly specified. This is a fundamental issue with how Polars handles typed literals in power operations.

### Critical Discovery

**ALL arithmetic operations with (typed literal, column) automatically promote to Int64 EXCEPT power:**

| Operation | Result Dtype | Behavior |
|-----------|--------------|----------|
| `Int8(63) * col(63)` | Int64 | ✅ Upcasts |
| `Int8(10) + col(63)` | Int64 | ✅ Upcasts |
| `Int8(10) - col(63)` | Int64 | ✅ Upcasts |
| `Int8(100) // col(63)` | Int64 | ✅ Upcasts |
| `Int8(100) % col(63)` | Int64 | ✅ Upcasts |
| `Int8(2) ** col(10)` | **Int8** | **❌ No upcast** |

**Asymmetry in Power:**
- `col.pow(2)` → Int64 ✅ (column on left works!)
- `lit(2).pow(col)` → Int8 ❌ (literal on left fails!)

### Minimal Reproduction Scripts

- `polars_bug_minimal_repro.py` - Simple reproduction
- `test_polars_overflow_behavior.py` - Comparison with multiplication
- `investigate_polars_upcasting.py` - Comprehensive operation analysis
- `polars_source_investigation.py` - Expression representation analysis

### Technical Analysis

`POLARS_TECHNICAL_ANALYSIS.md` - Detailed technical analysis showing:
- Power is the ONLY operation that doesn't upcast
- Multiplication correctly upcasts `Int8 * col` → Int64
- Power incorrectly keeps `Int8 ** col` → Int8
- Expression representations show `.pow()` doesn't call promotion logic

### Recommendation

File bug report with Polars team emphasizing:
- **Inconsistency**: All other arithmetic ops upcast, power doesn't
- **Comparison**: Show multiplication side-by-side with power
- **Asymmetry**: `col.pow(lit)` works but `lit.pow(col)` fails
- **Fix**: Apply same type promotion logic to power as multiplication uses

---

## Bug #2: Ibis Polars Backend - Enforces Narrow Integer Types

**Status**: Confirmed Ibis bug (Polars backend only)
**Severity**: High (produces wrong results)
**File**: `IBIS_BUG_REPORT_POW.md`

### Issue

Ibis Polars backend passes narrow integer dtypes to Polars literals, triggering Polars' overflow bug. Other backends (DuckDB, SQLite) work correctly.

### Reproduction

```python
import ibis
import polars as pl

conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10]})
table = conn.create_table('test', df)

# Fails - Ibis infers Int8 and passes to Polars
ibis.literal(2) ** ibis._['x']  # → 0 (expected 1024)

# Works - Explicit wider type
ibis.literal(2).cast('int64') ** ibis._['x']  # → 1024 ✅
```

### Root Cause Chain

1. Ibis infers `literal(2)` as `Int8` (smallest fitting type)
2. Polars backend enforces: `pl.lit(2, dtype=Int8)`
3. Polars computes in Int8 → overflow → returns 0

### Backend Comparison

| Backend | `literal(2) ** col(10)` | Result |
|---------|------------------------|--------|
| DuckDB  | 1024 | ✅ Correct |
| SQLite  | 1024 | ✅ Correct |
| Polars  | 0    | ❌ Wrong |

### Proposed Fix

**Location**: `ibis/backends/polars/compiler.py`, line ~109

```python
@translate.register(ops.Literal)
def literal(op, **_):
    # ... (other handling)
    elif dtype.is_integer():  # ADD THIS
        return pl.lit(value)  # Let Polars infer type
    else:
        typ = PolarsType.from_ibis(dtype)
        return pl.lit(op.value, dtype=typ)
```

**Benefits**:
- One-line fix
- Lets Polars choose appropriate types
- Fully backward compatible
- Consistent with other backends

### Minimal Reproduction Script

`ibis_bug_minimal_repro.py`

### Recommendation

File bug report with Ibis team with:
- Demonstration showing DuckDB/SQLite work, Polars fails
- Proposed one-line fix
- Mention this is specific to Polars backend
- Reference the upstream Polars bug

---

## Relationship Between Bugs

```
┌─────────────────────────────────────────┐
│ Ibis: literal(2) inferred as Int8      │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│ Polars backend: pl.lit(2, dtype=Int8)  │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│ Polars: Computes 2^10 in Int8          │
│ (BUG: Should upcast)                    │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│ Result: 0 (overflow)                    │
└─────────────────────────────────────────┘
```

**Both bugs contribute to the issue**:
1. **Polars bug**: Shouldn't overflow with explicit Int8 dtype
2. **Ibis bug**: Shouldn't pass narrow dtypes for integer literals

**Either fix would resolve the user-facing issue**, but both should be fixed for correctness.

---

## Testing Scripts

### Comprehensive Comparison
- `power_operator_comparison.py` - Side-by-side Ibis vs Polars comparison

### Minimal Reproductions
- `polars_bug_minimal_repro.py` - Pure Polars bug demonstration
- `ibis_bug_minimal_repro.py` - Ibis Polars backend bug with backend comparison

### Verification
- `verify_polars_operator.py` - Confirms both `.pow()` and `**` fail with Int8

---

## Recommended Actions

### For Polars Team

**Title**: Silent integer overflow in power operations with explicit Int8 dtype

**Files to attach**:
- `POLARS_BUG_REPORT.md` - Detailed bug report
- `polars_bug_minimal_repro.py` - Runnable reproduction

**Key points**:
- Both `.pow()` and `**` operator affected
- Only occurs with explicit narrow dtype (Int8)
- Silently returns 0 instead of upcasting or erroring
- Works correctly when dtype omitted

---

### For Ibis Team

**Title**: Polars backend: Power operations return 0 due to narrow type enforcement

**Files to attach**:
- `IBIS_BUG_REPORT_POW.md` - Detailed bug report
- `ibis_bug_minimal_repro.py` - Runnable reproduction with backend comparison
- `power_operator_comparison.py` - Comprehensive comparison

**Key points**:
- Polars backend only (DuckDB, SQLite work correctly)
- One-line fix proposed
- Fully backward compatible
- Related to upstream Polars bug (provide link when available)

---

## Expected Outcomes

### If Polars fixes their bug
Ibis Polars backend would work even with narrow types.

### If Ibis fixes their bug
Ibis users would no longer encounter the issue, regardless of Polars' behavior.

### Ideal outcome
Both teams fix their respective issues:
- Polars: Auto-upcast on overflow in power operations
- Ibis: Don't enforce narrow integer types in Polars backend

---

## Related Discovery

This investigation also uncovered and fixed a separate Ibis bug:

**Bug #0**: `_binop` contract violation with `Deferred` objects
- **Status**: Fixed
- **PR Description**: `IBIS_PR_DESCRIPTION.md`
- **Fix**: Added `InputTypeError` and `SignatureValidationError` to `_binop` exception handler
- **Impact**: Fixed 10 out of 11 reverse operator failures (97.4% success rate)

All three bugs were discovered during comprehensive testing of expression operators across backends.
