# Code Path Comparison: Literals vs Columns

## Side-by-Side Comparison

### Path 1: Creating a Literal with Value 2

```
USER CODE:
  ibis.literal(2)

       ↓

IBIS CODE (ibis/expr/api.py):
  def literal(value, type=None):
      if type is None:
          type = infer(value)  ← Calls type inference!
      return ops.Literal(value, dtype=type).to_expr()

       ↓

TYPE INFERENCE (ibis/expr/datatypes/value.py:128-135):
  @infer.register(int)
  def infer_integer(value: int) -> dt.Integer:
      types = (dt.int8, dt.int16, dt.int32, dt.int64)
      for dtype in types:
          if dtype.bounds.lower <= value <= dtype.bounds.upper:
              return dtype  ← Returns dt.int8 for value 2

       ↓

LITERAL OPERATION CREATED:
  ops.Literal(value=2, dtype=int8)

       ↓

POLARS BACKEND (ibis/backends/polars/compiler.py:~54):
  @translate.register(ops.Literal)
  def literal(op, **_):
      typ = PolarsType.from_ibis(dtype)  # int8 → pl.Int8
      return pl.lit(op.value, dtype=typ)  ← Explicit dtype!

       ↓

POLARS RECEIVES:
  pl.lit(2, dtype=pl.Int8)

FINAL TYPE: Int8 (8-bit)
```

---

### Path 2: Creating a Column with Value 2

```
USER CODE:
  pl.DataFrame({'x': [2]})
  conn.create_table('t', df)
  table.x

       ↓

POLARS DATAFRAME CREATION:
  pl.DataFrame({'x': [2]})
  # Python int 2 → Polars chooses Int64

       ↓

POLARS SCHEMA:
  Schema({'x': Int64})

       ↓

IBIS TABLE CREATION:
  conn.create_table('t', df)
  # Reads Polars schema

       ↓

IBIS SCHEMA:
  ibis.Schema({'x': int64})  ← Preserves Polars type!

       ↓

COLUMN REFERENCE:
  table.x
  # Type: int64 (from schema)

       ↓

POLARS BACKEND:
  # Column reference, no translation needed
  pl.col('x')  # Already Int64

       ↓

POLARS RECEIVES:
  pl.col('x')  # Type: Int64

FINAL TYPE: Int64 (64-bit)
```

---

## The Key Difference

| Stage | Literal Path | Column Path |
|-------|-------------|-------------|
| User Input | Python int: 2 | Python int: 2 |
| Initial Handler | Ibis `literal()` | Polars `DataFrame()` |
| Type Decision | **Ibis infers int8** | **Polars chooses Int64** |
| Schema Storage | ops.Literal(dtype=int8) | Schema({'x': Int64}) |
| Backend Translation | pl.lit(2, dtype=pl.Int8) | pl.col('x') |
| Final Type | **Int8 (8-bit)** | **Int64 (64-bit)** |

---

## Why The Difference?

### Literals: Ibis Controls Type

```python
ibis.literal(2)
    ↓
Ibis says: "I'll infer the type"
    ↓
Ibis algorithm: "Smallest type that fits"
    ↓
Result: int8
```

**Decision maker:** Ibis
**Philosophy:** Optimize for memory
**Result:** Narrow type (int8)

### Columns: DataFrame Library Controls Type

```python
pl.DataFrame({'x': [2]})
    ↓
Polars says: "I'll choose the type"
    ↓
Polars algorithm: "Safe default for Python ints"
    ↓
Result: Int64
```

**Decision maker:** Polars
**Philosophy:** Safety and convenience
**Result:** Wide type (Int64)

---

## Code Locations

### Literal Type Inference

**File 1:** `ibis/expr/api.py` (literal() function)
```python
def literal(value, type=None):
    """Create a scalar expression from a Python value."""
    if type is None:
        type = infer(value)  # ← Infers type
    return ops.Literal(value, dtype=type).to_expr()
```

**File 2:** `ibis/expr/datatypes/value.py:128-135` (inference logic)
```python
@infer.register(int)
def infer_integer(value: int, prefer_unsigned: bool = False) -> dt.Integer:
    """Infer the smallest integer type that can hold this value."""
    types = (dt.int8, dt.int16, dt.int32, dt.int64)
    for dtype in types:
        if dtype.bounds.lower <= value <= dtype.bounds.upper:
            return dtype
    return dt.int64
```

**File 3:** `ibis/backends/polars/compiler.py:85-110` (Polars translation)
```python
@translate.register(ops.Literal)
def literal(op, **_):
    value = op.value
    dtype = op.dtype
    # ...
    typ = PolarsType.from_ibis(dtype)
    return pl.lit(op.value, dtype=typ)
```

### Column Type Preservation

**File 1:** `ibis/backends/polars/__init__.py` (table creation)
```python
def create_table(self, name, obj):
    # Registers Polars DataFrame
    # Schema is read from DataFrame
    self._tables[name] = obj
```

**File 2:** Polars itself
```python
pl.DataFrame({'x': [2]})
# Internally: Python int → Int64
```

No Ibis inference - just reads what Polars decided!

---

## Visual Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER CREATES VALUE 2                      │
└──────────────┬────────────────────────────┬──────────────────┘
               │                            │
               ▼                            ▼
    ┌──────────────────┐        ┌─────────────────────┐
    │  ibis.literal(2) │        │ DataFrame({'x':[2]})│
    └──────────┬───────┘        └──────────┬──────────┘
               │                           │
               ▼                           ▼
    ┌──────────────────┐        ┌─────────────────────┐
    │  IBIS INFERS     │        │  POLARS CHOOSES     │
    │  Type: int8      │        │  Type: Int64        │
    │  (smallest)      │        │  (safe default)     │
    └──────────┬───────┘        └──────────┬──────────┘
               │                           │
               ▼                           ▼
    ┌──────────────────┐        ┌─────────────────────┐
    │ ops.Literal(     │        │ Ibis reads schema:  │
    │   value=2,       │        │ {'x': int64}        │
    │   dtype=int8)    │        │ (preserved)         │
    └──────────┬───────┘        └──────────┬──────────┘
               │                           │
               ▼                           ▼
    ┌──────────────────────────────────────────────────┐
    │         POLARS BACKEND TRANSLATION                │
    ├──────────────────┬───────────────────────────────┤
    │ pl.lit(2,        │        pl.col('x')            │
    │   dtype=pl.Int8) │        (already Int64)        │
    └──────────┬───────┴───────────────┬───────────────┘
               │                       │
               ▼                       ▼
         ┌─────────┐             ┌─────────┐
         │  Int8   │             │  Int64  │
         │  (8-bit)│             │ (64-bit)│
         └─────────┘             └─────────┘
               │                       │
               └───────────┬───────────┘
                           ▼
                  ┌─────────────────┐
                  │  OPERATION:     │
                  │  2 ** 10        │
                  │                 │
                  │  Int8 → 0 ❌    │
                  │  Int64 → 1024 ✅│
                  └─────────────────┘
```

---

## Why This Matters

### Same Value, Different Paths

```python
value = 2

# As literal
ibis.literal(value)  # → int8

# In DataFrame
pl.DataFrame({'x': [value]})  # → Int64
table.x
```

**Both represent "2" but get different types!**

### When They Meet

```python
ibis.literal(2) ** table.x
# int8 ** int64 → int8 (uses base type) → overflow!

table.x ** ibis.literal(10)
# int64 ** int8 → ??? (depends on Polars rules)
```

---

## The Design Flaw

### Literals Should Match Columns

**Principle of Substitutability:**

```python
# Should be equivalent
x = 2
table.x ** ibis.literal(10)  # ✓ Works
ibis.literal(x) ** ibis.literal(10)  # ✗ Fails
```

**They're not!** Different code paths = different types.

### The Fix

**Make literals follow the same philosophy as DataFrames:**

```python
# Current
def infer_integer(value: int) -> dt.Integer:
    # Return smallest type
    return dt.int8  # for value 2

# Fixed
def infer_integer(value: int) -> dt.Integer:
    # Match DataFrame defaults
    return dt.int64
```

Or don't pass type to Polars:

```python
# Current
return pl.lit(2, dtype=pl.Int8)

# Fixed
return pl.lit(2)  # Let Polars choose (will be Int32/Int64)
```

---

## Summary

**Two code paths for same value (2):**

1. **Literal path:**
   - Ibis controls type
   - Chooses int8 (smallest)
   - Passes to Polars explicitly
   - Result: 8-bit integer

2. **Column path:**
   - Polars controls type
   - Chooses Int64 (safe default)
   - Ibis preserves it
   - Result: 64-bit integer

**The mismatch creates bugs when literals and columns interact!**

**The solution: Make literals behave like columns.**
