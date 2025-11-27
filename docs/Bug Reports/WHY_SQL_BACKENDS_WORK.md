# Why SQL Backends Work But Polars Doesn't

## The Answer

**SQL backends generate untyped literal values in SQL**, allowing the database engine to choose appropriate types. **Polars backend uses a typed API**, explicitly passing narrow types like Int8.

---

## The Evidence

### What SQL is Generated

**DuckDB/SQLite backends generate:**
```sql
SELECT POWER(2, "t0"."x") FROM "test" AS "t0"
```

**Notice:** Just `2` - no type specification!

### What SQL Databases Do With Untyped Literals

When DuckDB or SQLite sees the literal `2` in SQL:
1. It's **not explicitly typed**
2. The database **infers an appropriate type**
3. Typically chooses **INT** or **BIGINT** (32-bit or 64-bit)
4. These are **wide enough** to hold results like 1024

**Result:** `POWER(2, 10)` in SQL → 1024 ✅

---

## How Polars Backend is Different

### Polars Uses a Direct API (Not SQL)

The Polars backend doesn't generate SQL strings. It calls Polars Python API directly:

```python
pl.lit(2, dtype=pl.Int8).pow(pl.col('x'))
```

**Notice:** Explicit `dtype=pl.Int8`!

### Why This Matters

1. SQL literal `2` → **Database chooses type** (usually INT/BIGINT)
2. Polars API `pl.lit(2, dtype=Int8)` → **Type is explicit and fixed**

---

## Code Comparison

### SQL Backend Code Path

**File:** `ibis/backends/sql/compilers/base.py:778-779`

```python
def visit_DefaultLiteral(self, op, *, value, dtype):
    if dtype.is_integer():
        return sge.convert(value)  # ← Just converts value to SQL!
```

**Result:** Generates SQL `2` (untyped)

### Polars Backend Code Path

**File:** `ibis/backends/polars/compiler.py:~54`

```python
@translate.register(ops.Literal)
def literal(op, **_):
    # ...
    typ = PolarsType.from_ibis(dtype)
    return pl.lit(op.value, dtype=typ)  # ← Explicit dtype!
```

**Result:** Generates `pl.lit(2, dtype=pl.Int8)` (explicitly typed)

---

## Why SQL Databases Choose Wider Types

### SQL Standards and Integer Literals

In SQL, untyped integer literals are typically treated as:
- **INTEGER** (32-bit) for small values
- **BIGINT** (64-bit) for larger values
- Never as **TINYINT** (8-bit) or **SMALLINT** (16-bit)

This is a **safe default** to avoid overflow in common operations.

**Example in DuckDB:**
```sql
-- No explicit type
SELECT TYPEOF(2);
-- Result: "INTEGER" (32-bit)

-- Explicitly typed (if you forced it)
SELECT TYPEOF(CAST(2 AS TINYINT));
-- Result: "TINYINT" (8-bit)
```

### Why This Makes Sense

1. **Safety first:** Better to use more memory than get wrong results
2. **User expectation:** SQL users expect literals to "just work"
3. **Legacy compatibility:** SQL databases have decades of this behavior
4. **Performance:** Modern systems have plenty of memory

---

## The Polars Philosophy

Polars takes a different approach:

1. **Explicit over implicit:** If you specify a type, it respects it
2. **Memory efficiency:** Narrower types use less memory
3. **User control:** You can choose Int8 if you want compact storage
4. **Performance:** Operations on narrow types can be faster

This is **not wrong** - it's a different design philosophy!

---

## The Mismatch

The problem occurs when you combine:

1. **Ibis's aggressive type inference** (chooses Int8 for `literal(2)`)
2. **Polars' explicit type API** (respects the Int8)
3. **User expectation from SQL** (expects literals to "just work")

```
Ibis: "2 fits in Int8, so dtype=int8"
    ↓
Polars: "User said Int8, I'll use Int8"
    ↓
User: "Why did 2^10 return 0?!" ← Surprise!
```

---

## Analogy: Typed vs Untyped Languages

**SQL backends (like Python):**
```python
x = 2  # Python chooses type (int)
result = x ** 10  # Works: 1024
```

**Polars backend (like C with explicit types):**
```c
int8_t x = 2;  // Explicit 8-bit type
int8_t result = pow(x, 10);  // Overflow! (1024 doesn't fit in int8_t)
```

SQL behaves like Python - **infers wide types**.
Polars API behaves like C - **uses explicit types**.

---

## Why Ibis is At Fault

**The user wrote:**
```python
ibis.literal(2) ** table.x
```

**What the user expected:**
- Like Python: `2 ** 10` → 1024 ✅
- Like SQL: `POWER(2, 10)` → 1024 ✅

**What Ibis did:**
- Inferred `int8` without user asking
- Told Polars to use Int8 explicitly
- Polars respected it (correct behavior for explicit types)
- Result: 0 ❌

**Who's responsible?**
- ❌ Not the user (never asked for Int8)
- ❌ Not Polars (correctly respects explicit types)
- ✅ Ibis (chose Int8 and forced it on Polars)

---

## The Fix

**Ibis Polars backend should behave like SQL backends:**

**Current (wrong):**
```python
return pl.lit(value, dtype=pl.Int8)  # Explicit narrow type
```

**Fixed (correct):**
```python
return pl.lit(value)  # Let Polars choose (like SQL does)
```

**Result:**
- Polars will choose Int32 or Int64 (safe)
- Matches SQL backend behavior
- Matches user expectations
- No overflow!

---

## Test Evidence

**Run:** `python docs/Bug\ Reports/Ibis/test_sql_backend_literal_generation.py`

**SQL Generated:**
```sql
-- DuckDB
SELECT POWER(2, "t0"."x") FROM "test"

-- SQLite
SELECT POWER(2, "t0"."x") FROM "test"
```

Notice: Just `2`, not `CAST(2 AS TINYINT)`!

**Results:**
```
DuckDB:  1024 ✅
SQLite:  1024 ✅
Polars:  0    ❌
```

---

## Conclusion

**SQL backends work because:**
1. They generate untyped SQL literals (`2`)
2. SQL databases choose safe types (INT/BIGINT)
3. Operations don't overflow

**Polars backend fails because:**
1. Ibis explicitly types literals (`dtype=Int8`)
2. Polars respects the explicit type
3. Operations overflow in narrow type

**The fix:** Make Polars backend behave like SQL backends - don't pass explicit narrow types for numeric literals.

---

## For the Bank/Insurance Analyst

You asked: "Why do the other backends generate the correct answer?"

**Short answer:** Because SQL databases don't have the concept of "explicitly typed literal integers" in the way Polars' Python API does.

**What this means for you:**
1. This is an Ibis bug, not a Polars bug
2. The fix should be in Ibis
3. Workaround: Use `.cast('int64')` on literals
4. Or use DuckDB backend instead of Polars for now

**Example workaround:**
```python
# Instead of:
ibis.literal(2) ** table.x  # May overflow

# Use:
ibis.literal(2).cast('int64') ** table.x  # Safe
```

**The real answer:** Ibis shouldn't make you do this. It should pass untyped (or wide-typed) literals to Polars, just like it generates untyped literals in SQL for DuckDB/SQLite.
