# Simple Answer: Why SQL Backends Work

## The Key Difference

### SQL Backends (DuckDB, SQLite) ✅

```
User writes: ibis.literal(2) ** table.x
       ↓
Ibis generates SQL: POWER(2, x)
       ↓
SQL database sees: 2  ← NO TYPE!
       ↓
Database chooses: INT or BIGINT (32-bit or 64-bit)
       ↓
Calculation: 2^10 in INT → 1024 ✅
```

**SQL has untyped literals!**

---

### Polars Backend ❌

```
User writes: ibis.literal(2) ** table.x
       ↓
Ibis infers: int8 (2 fits in -128..127)
       ↓
Ibis calls: pl.lit(2, dtype=pl.Int8).pow(x)
       ↓
Polars sees: Int8 ← EXPLICIT TYPE!
       ↓
Polars uses: Int8 (8-bit)
       ↓
Calculation: 2^10 in Int8 → 0 (overflow) ❌
```

**Polars API has explicitly typed literals!**

---

## In Code

### What SQL Looks Like

```sql
-- DuckDB/SQLite
SELECT POWER(2, x) FROM table;
```

Notice: Just `2` - no `CAST(2 AS TINYINT)`

### What Polars API Looks Like

```python
# What Ibis sends to Polars
pl.lit(2, dtype=pl.Int8).pow(pl.col('x'))
```

Notice: Explicit `dtype=pl.Int8`

---

## Why This Matters

| Aspect | SQL Backends | Polars Backend |
|--------|--------------|----------------|
| Literal representation | Untyped string | Typed Python object |
| Type chosen by | Database engine | Ibis |
| Default integer type | INT/BIGINT (32/64-bit) | Int8 (8-bit) |
| Overflow risk | Low | High |
| Result for 2^10 | 1024 ✅ | 0 ❌ |

---

## Analogy

**SQL backends are like Python:**
```python
x = 2  # Python chooses 'int' (unlimited precision)
x ** 10  # 1024 ✅
```

**Polars backend is like C:**
```c
int8_t x = 2;  // Explicit 8-bit type
pow(x, 10);    // Overflow ❌
```

---

## The Fix

Make Polars backend behave like SQL backends:

**Don't pass explicit narrow types!**

```python
# Current (wrong)
return pl.lit(2, dtype=pl.Int8)

# Fixed (correct)
return pl.lit(2)  # Let Polars choose
```

---

## Summary

**Q:** Why do SQL backends work?

**A:** Because SQL has **untyped integer literals**. When you write `2` in SQL, the database chooses a safe type (INT or BIGINT). Polars API has **explicitly typed literals**, and Ibis is telling Polars to use Int8, causing overflow.

**Blame:** Ibis (for aggressively inferring Int8 and explicitly passing it to Polars)

**Not Blame:**
- Polars (correctly respecting explicit types)
- SQL databases (correctly choosing safe types for untyped literals)
- User (never asked for Int8)
