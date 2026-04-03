# Is Polars "Correct"? A Philosophical Debate

## The Question

You said: "'correctly' respects is in the opinion of polars - but perhaps not in the opinion of an analyst working at a bank or insurance company!"

This is **absolutely valid**. Let's examine both perspectives.

---

## The Two Philosophies

### Polars' Perspective: "Explicit is Correct"

**Polars team says:**
> When you explicitly pass `dtype=Int8`, we respect it. If you don't want overflow, don't use Int8.

**Their reasoning:**
1. **Explicit types are a promise** - "I want Int8" means "use Int8"
2. **Performance** - Narrow types are faster and use less memory
3. **User control** - Power users should be able to choose narrow types
4. **Consistent behavior** - Always respect explicit types

**Example:**
```python
# User explicitly chooses Int8
pl.lit(2, dtype=pl.Int8) ** pl.col('x')
# Polars: "User said Int8, overflow is their problem"
```

---

### Analyst's Perspective: "Mathematically Correct is Correct"

**Bank/insurance analyst says:**
> 2^10 = 1024. I don't care about types. Give me the right answer.

**Their reasoning:**
1. **Math doesn't lie** - 2^10 is always 1024, not 0
2. **Silent errors are dangerous** - Wrong answers lose money
3. **Type is implementation detail** - I want "2 to the power of 10"
4. **No surprises** - Works in SQL, Excel, Python - should work here

**Example:**
```python
# User writes what looks like simple math
2 ** 10
# Analyst expects: 1024
# Getting 0 is WRONG regardless of "explicit types"
```

---

## The Real Issue: Who Chose Int8?

This is where Polars' argument breaks down:

### If User Explicitly Chose Int8

```python
# User says "I want Int8"
pl.lit(2, dtype=pl.Int8) ** pl.col('x')
# Result: 0
# Polars: "You asked for Int8, overflow is your responsibility" ✅
```

**This is defensible.** User made an explicit choice.

### If Ibis Chose Int8 Without User Knowledge

```python
# User writes
ibis.literal(2) ** table.x

# Ibis does (behind the scenes)
pl.lit(2, dtype=pl.Int8) ** pl.col('x')

# Result: 0
# User: "WTF? I never said Int8!" ❌
```

**This is indefensible.** User never chose Int8!

---

## Analogy: The Explicit vs Implicit Contract

### Scenario 1: Explicit Contract

```
You: "Give me a 1-bedroom apartment"
Landlord: Gives you a 1-bedroom apartment
You: "This is too small!"
Landlord: "You asked for 1-bedroom" ✅
```

**Landlord is correct** - you explicitly asked for it.

### Scenario 2: Implicit Contract (Ibis situation)

```
You: "Give me an apartment for a family of 4"
Real Estate Agent: Gives landlord "1-bedroom is enough"
Landlord: Gives you a 1-bedroom apartment
You: "This is too small!"
Agent: "Well, technically you could fit 4 people..."
You: "I NEVER SAID 1-BEDROOM!" ❌
```

**Landlord followed agent's instructions** but **agent made bad choice**.

This is the Ibis-Polars situation!

---

## What "Correct" Means

### Technical Correctness (Polars' view)

```python
pl.lit(2, dtype=pl.Int8) ** pl.col('x')
```

**Technically correct:**
- User specified Int8 → Use Int8 ✅
- Int8 overflow behavior is defined ✅
- Consistent with Polars' API design ✅

**Mathematically wrong:**
- 2^10 = 1024, not 0 ❌

### Mathematical Correctness (Analyst's view)

```python
ibis.literal(2) ** table.x
```

**Mathematically correct:**
- 2^10 should be 1024 ✅
- Result should match Excel/Python/SQL ✅
- No silent errors ✅

**What happened:**
- Got 0 instead of 1024 ❌
- Silent data corruption ❌
- Financial calculations wrong ❌

---

## Real-World Impact

### Example: Compound Interest Calculation

```python
# Calculate compound interest: P * (1 + r)^t
# P = $1000, r = 0.05, t = 10 years

principal = ibis.literal(1000)
rate = ibis.literal(1.05)
years = ibis.literal(10)

# Ibis might infer int8/int16 for these small numbers
future_value = principal * (rate ** years)

# Expected: $1000 * 1.628 = $1628.89
# With overflow: $0 or negative number
# Result: Bank loses money, customer sues
```

**Analyst perspective:**
> I don't care if it's "technically correct" according to Polars. Giving me $0 for a $1628 calculation is WRONG. Period.

---

## Who Should Prevent This?

### Option 1: Polars Should Auto-Promote

**Argument:** Like NumPy and Python do

```python
# NumPy behavior
import numpy as np
np.int8(2) ** np.int8(10)  # Doesn't return 0
# NumPy promotes to wider type automatically
```

**Polars team response:**
> We designed our API differently. Explicit types are explicit.

**Verdict:** Valid design choice, but arguably less user-friendly.

### Option 2: Ibis Should Not Force Narrow Types

**Argument:** Don't pass types the user didn't ask for

```python
# Current (wrong)
pl.lit(2, dtype=pl.Int8)  # User never asked for Int8!

# Fixed (correct)
pl.lit(2)  # Let Polars choose appropriate type
```

**Verdict:** THIS IS THE RIGHT FIX. ✅

### Option 3: User Should Be More Careful

**Argument:** Users should cast explicitly

```python
# Instead of
ibis.literal(2) ** table.x

# Use
ibis.literal(2).cast('int64') ** table.x
```

**Verdict:** Unreasonable burden. Users shouldn't need to understand integer overflow for simple math. ❌

---

## SQL Databases' Approach

SQL databases have dealt with this for 50+ years:

**Their solution:** Integer literals default to safe types

```sql
-- SQL doesn't make you say INT, BIGINT, TINYINT
SELECT 2, 1000, 1000000;

-- Database chooses appropriate types automatically
-- Usually INT (32-bit) or BIGINT (64-bit)
```

**Why this works:**
- Safety by default
- Users don't need to think about overflow
- Matches mathematical expectations
- Can still explicitly narrow if needed

**Example of explicit narrowing in SQL:**
```sql
-- If you REALLY want TINYINT
SELECT CAST(2 AS TINYINT);
```

---

## The Principle of Least Surprise

**User expectation:**
```python
2 ** 10  # Python: 1024
```

```sql
SELECT POWER(2, 10);  -- SQL: 1024
```

```python
ibis.literal(2) ** table.x  -- Should be: 1024
```

**Actual result:**
```python
ibis.literal(2) ** table.x  -- Actual: 0 ❌
```

**Principle violated!** Ibis behaves differently than:
- Python
- SQL
- Excel
- R
- Every calculator on Earth

---

## Conclusion

### Is Polars "Correct"?

**From a type system perspective:** Yes ✅
- They do what they said they'd do
- API documentation is clear
- Behavior is consistent

**From a mathematical perspective:** No ❌
- 2^10 ≠ 0
- Silent errors are always wrong
- Users expect correct math

**From a user perspective:** No ❌
- User never chose Int8
- Violates principle of least surprise
- Breaks financial calculations

### Who Should Fix This?

**Ibis is responsible:**
1. User wrote `ibis.literal(2)` - no type specified
2. Ibis chose Int8 - aggressive inference
3. Ibis told Polars to use Int8 - explicit dtype
4. Polars respected Int8 - "technically correct"
5. Result wrong - user's perspective

**The fix:** Ibis should behave like SQL compilers - generate untyped literals (or wide-typed) and let Polars choose safe defaults.

---

## For the Analyst

You're **absolutely right** to question whether Polars' behavior is "correct."

**Technically correct ≠ Practically correct**

Your calculations need to be **mathematically correct**, not just "technically correct according to API design."

**Your responsibility:**
- Get the right answer
- Protect your company from bad data

**Not your responsibility:**
- Understand Int8 vs Int64 overflow semantics
- Debug why simple arithmetic returns 0
- Work around library design quirks

**The fix should be in Ibis**, not in your code.
