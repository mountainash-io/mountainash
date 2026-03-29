# TL;DR: Ibis is the Culprit, Not Polars

## The Flow

```
USER WRITES:
  ibis.literal(2) ** table.x

       ↓

IBIS TYPE INFERENCE (value.py:129):
  infer_integer(2)
  → Tries: int8 ✓ (2 fits in -128..127)
  → Returns: int8

       ↓

IBIS POLARS BACKEND (compiler.py:~54):
  typ = PolarsType.from_ibis(dtype)  # int8 → pl.Int8
  return pl.lit(2, dtype=pl.Int8)     # ← EXPLICIT DTYPE!

       ↓

POLARS RECEIVES:
  pl.lit(2, dtype=pl.Int8) ** pl.col('x')

       ↓

POLARS EXECUTES (by design):
  "User specified Int8, I'll stay in Int8"
  2^10 = 1024
  1024 doesn't fit in Int8 (-128..127)
  → Returns 0 (overflow)

       ↓

USER SEES:
  0 ❌ (Expected: 1024)
```

---

## The Problem

**User never asked for Int8!**

Ibis chose it automatically, then told Polars "user wants Int8", and Polars (correctly) respected that choice.

---

## The Evidence

### Test: What dtype does Ibis choose?

```python
ibis.literal(2).type()    # → int8
ibis.literal(63).type()   # → int8
ibis.literal(128).type()  # → int16 (doesn't fit in int8)
```

### Test: What does Polars do?

```python
# WITHOUT explicit dtype (Polars chooses)
pl.lit(2) ** pl.col('x')
# → Polars uses Int64, returns 1024 ✅

# WITH explicit dtype (what Ibis sends)
pl.lit(2, dtype=pl.Int8) ** pl.col('x')
# → Polars stays Int8, returns 0 ❌
```

---

## Polars Team Says:

From https://github.com/pola-rs/polars/issues/25213:

> This is **correct and expected behavior**. When you explicitly specify `dtype=Int8`, Polars respects it. Don't pass dtype if you want automatic type promotion.

---

## The Fix (One Line in Ibis)

**File:** `ibis/backends/polars/compiler.py`

```python
@translate.register(ops.Literal)
def literal(op, **_):
    # ...
    elif dtype.is_integer():
        return pl.lit(value)  # ← Don't pass dtype, let Polars choose!
```

---

## Why This Also Affects Multiplication

```python
# Direct Polars (chooses Int32)
pl.lit(63) * pl.lit(63)  → 3969 ✅

# What Ibis sends (explicit Int8)
pl.lit(63, dtype=pl.Int8) * pl.lit(63, dtype=pl.Int8)  → -127 ❌
```

Polars wraps when you explicitly specify narrow types!

---

## Summary

| Component | Behavior | Verdict |
|-----------|----------|---------|
| **User** | Writes `literal(2)` | Expects Int64 (like Python int) |
| **Ibis** | Infers `int8` automatically | ❌ Too aggressive |
| **Ibis** | Sends `dtype=Int8` to Polars | ❌ Shouldn't specify narrow types |
| **Polars** | Respects `dtype=Int8`, overflows | ✅ Correct behavior |

**Conclusion:** Fix Ibis, not Polars.

---

## Files

- **Analysis:** `COMPREHENSIVE_IBIS_POLARS_ANALYSIS.md`
- **Test:** `test_ibis_literal_aggressive_downcast.py`
- **Proposal:** `IBIS_POW_FIX_PROPOSAL.md`
