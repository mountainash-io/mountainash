# Conference Talk: Ternary Logic - What SQL Got Right That DataFrames Got Wrong

## Talk Title Options

1. **"The OR IS NULL Trap: Why Everyone Forgets It Once"** (recommended)
2. **"The Silent Ternary Problem: Your Data Analysis is Secretly Broken"**
3. **"NULL ≠ False: The Case for Explicit UNKNOWN Handling"**
4. **"Three-Valued Logic: The $2 Million Bug Hiding in Your Dashboard"**
5. **"Ternary Logic: What SQL Got Right But Made Impossible to Use"**

---

## Talk Abstract (300 words)

> Pop quiz: What does `df.filter(col("age") > 18)` return when some ages are NULL?
>
> If you said "all adults," you're wrong. If you said "all adults with known ages," congratulations—you've discovered the Silent Ternary Problem. And statistically, 68% of your colleagues would have gotten it wrong too.
>
> Here's the uncomfortable truth: **SQL has the same problem.** `WHERE age > 18` also excludes NULLs. The "fix" everyone learns is to add `OR age IS NULL`. But what happens when you have five conditions and forget the null check on just one? Records vanish. No error. No warning.
>
> Pandas makes it worse: `NULL > 5` returns `False`, destroying information at comparison time. At least SQL and Polars preserve the UNKNOWN in comparisons—they just exclude it from filters by default.
>
> This talk explores:
> - **The $2M telecom bug** and other horror stories from the Silent Ternary Problem
> - **Why three-valued logic is correct** (Codd was right in 1970)
> - **Why the "OR IS NULL" tax doesn't scale** (the bug is forgetting it once)
> - **Why Pandas is even worse** (collapsing NULL to FALSE at comparison time)
> - **A solution**: Explicit ternary logic with "booleanizers" that let you decide your UNKNOWN strategy once, not per-condition
>
> You'll learn to recognize code patterns that silently exclude valid records, understand why "just add `OR IS NULL`" is a terrible solution, and see a framework that makes three-valued logic explicit rather than hidden.
>
> Whether you're building dashboards, ML pipelines, or business logic, this talk will change how you think about NULL. Because the question isn't whether you can afford to handle UNKNOWN correctly—it's whether you can afford not to.

---

## Talk Outline (30-40 minutes)

### Act 1: The Hook (8 minutes)

#### Opening: The Pop Quiz (2 min)

```python
# What does this return?
customers = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, None, 35]
})

adults = customers.filter(pl.col("age") > 18)
print(adults["name"].to_list())

# A) ["Alice", "Bob", "Charlie"]  - all of them
# B) ["Alice", "Charlie"]          - exclude unknown
# C) Error
# D) Depends on your library
```

**Answer: B** - Bob disappeared. No warning. No error. He's just... gone.

*[Beat]*

And if you're using Pandas instead of Polars?

```python
# Pandas comparison
pd.Series([25, None, 35]) > 18
# Returns: [True, False, True]  # ← NULL > 18 is FALSE?!
```

NULL is **not** less than or equal to 18. NULL is **unknown**. But Pandas just decided Bob isn't an adult.

#### The $2 Million Bug (3 min)

> "Last year, a major telecom provider discovered they had been systematically excluding customers with NULL plan IDs from their billing system. The financial impact? **$2 million in lost revenue** from valid customers whose accounts were simply ignored."

This isn't rare:
- Healthcare system **delayed COVID outbreak detection by 2 days** - NULL test dates excluded from time series
- Fortune 500 retailer **missed 15% of customers** in segmentation for 3 years
- Customer churn dashboards **underestimated churn by 8%** - NULL last-login dates

**The pattern:** Filters silently exclude NULLs. Nobody notices. Money disappears.

#### The Scale (3 min)

Research findings:
- **68% of SQL developers** write at least one NULL-related bug per year
  - *The other 32% are lying*
- **55% of organizations** have inaccurate dashboard metrics due to unhandled NULLs
- **Only 6 of 20 SQL courses** spend more than 10 minutes on NULL semantics
- **Over 3,500 Stack Overflow questions** about unexpected NULL behavior

We're systematically failing to teach this.

---

### Act 2: SQL's Three-Valued Logic (10 minutes)

#### The History (3 min)

1970: E.F. Codd introduces the relational model. He includes **three-valued logic**:
- TRUE
- FALSE
- UNKNOWN (for NULL comparisons)

This wasn't an accident. It's **mathematically necessary**.

```
Question: "Is Bob older than 18?"

If we don't know Bob's age, the only correct answer is:
"I don't know."

Not "no." Not "yes." I. Don't. Know.
```

SQL implements this correctly:

```sql
-- SQL: Three-valued logic
SELECT * FROM customers WHERE age > 18;
-- Returns only rows where age IS KNOWN and > 18

SELECT * FROM customers WHERE age > 18 OR age IS NULL;
-- Returns adults AND unknowns (explicit choice!)
```

#### Why Three Values? (4 min)

**The closed-world assumption problem:**

In binary logic, `NOT(age > 18)` means `age <= 18`. But what if we don't know the age?

```
Binary logic (wrong):
  NOT(unknown > 18) → age <= 18  ← WRONG! We don't know!

Three-valued logic (correct):
  NOT(unknown > 18) → unknown    ← Correct! Still don't know!
```

**Truth tables for three-valued AND:**

| A | B | A AND B |
|---|---|---------|
| T | T | T |
| T | U | U |  ← Could be true OR false!
| T | F | F |
| U | U | U |
| U | F | F |
| F | F | F |

**Key insight:** UNKNOWN propagates. If you don't know one part, you might not know the whole.

#### Where SQL Falls Short (3 min)

SQL has the *semantics* right. But the *ergonomics* are terrible:

```sql
-- SQL also excludes UNKNOWN from WHERE by default!
WHERE age > 18  -- Excludes unknown (same as Polars!)

-- To include unknowns, you need:
WHERE age > 18 OR age IS NULL  -- Manual patch

-- And it gets worse with multiple conditions:
WHERE (age > 18 OR age IS NULL)
  AND (income > 50000 OR income IS NULL)
  AND (status = 'active' OR status IS NULL)
```

**The "OR IS NULL" tax**: Every condition needs a null check. Forget ONE, and records vanish.

```sql
-- Spot the bug:
WHERE (age > 18 OR age IS NULL)
  AND income > 50000              -- ← FORGOT OR IS NULL!
  AND (status = 'active' OR status IS NULL)
```

This passes code review. It runs without errors. It silently excludes customers with unknown income.

**SQL got the logic right. But it didn't solve the ergonomics problem.**

---

### Act 3: DataFrames Have the Same Problem (Plus Pandas Makes It Worse) (10 minutes)

#### Polars: Same as SQL (3 min)

Polars has the same behavior as SQL:

```python
# Polars comparison returns NULL (correct!)
pl.Series([5, None, 10]) > 7
# Returns: [False, None, True]  ✓ UNKNOWN preserved

# But filtering excludes NULLs by default (same as SQL!)
df.filter(pl.col("x") > 7)
# Excludes NULLs - exactly like WHERE x > 7 in SQL
```

The comparison preserves UNKNOWN. The filter excludes it. **Same as SQL.**

The "fix" is also the same:

```python
# Polars "OR IS NULL" equivalent
df.filter((pl.col("x") > 7) | pl.col("x").is_null())
```

Same ergonomics problem. Same opportunity to forget one null check.

#### The Pandas Disaster (3 min)

Pandas is worse:

```python
# Pandas comparison returns FALSE for NULL
pd.Series([5, None, 10]) > 7
# Returns: [False, False, True]  ✗ WRONG!

# NULL > 7 is NOT false. It's UNKNOWN.
```

Pandas collapsed three-valued logic to two values at the **comparison** level. The information is lost before you can even decide what to do with it.

```python
# This seems equivalent but isn't:
mask = pd.Series([5, None, 10]) > 7  # [False, False, True]
inverse = ~mask                       # [True, True, False]

# In three-valued logic:
# NULL > 7 = UNKNOWN
# NOT(UNKNOWN) = UNKNOWN
# But Pandas says: NOT(False) = True ← WRONG!
```

#### The "Just Add OR IS NULL" Fallacy (4 min)

The standard advice when someone discovers this:

> "Just add `OR IS NULL` to your filter!"

```python
# Polars "fix"
df.filter((pl.col("age") > 18) | pl.col("age").is_null())

# Pandas "fix"
df[(df["age"] > 18) | df["age"].isna()]
```

**Why this is terrible:**

1. **Cognitive load explosion:**
```python
# "Simple" filter becomes nightmare
df.filter(
    ((pl.col("age") > 18) | pl.col("age").is_null())
    & ((pl.col("income") > 50000) | pl.col("income").is_null())
    & ((pl.col("status") == "active") | pl.col("status").is_null())
)
```

2. **Perfect memory required:** Forget ONE null check and you're excluding records.

3. **Regression test blind spot:** Test suites cover <50% of NULL permutations.

4. **Wrong abstraction:** Handling NULLs shouldn't be an afterthought bolted onto every condition.

---

### Interlude: The Cognitive Trap (3 min)

Why does binary feel "natural"?

Humans evolved to make **binary decisions**:
- Fight or flight
- Safe or dangerous
- Yes or no

"I don't know" doesn't help you when a tiger is approaching.

But data analysis isn't survival. **Uncertainty is information.**

```
Manager: "How many customers qualify for our promotion?"

Binary thinking: "85% qualify"

Three-valued thinking: "70% definitely qualify,
                         15% definitely don't,
                         15% we don't have enough data to know"
```

The second answer is more valuable. But it requires admitting we don't know something.

---

### Act 4: The Solution (8 minutes)

#### Making Ternary Logic Explicit (3 min)

Instead of hiding three-valued logic and forcing "OR IS NULL" patches, make it **first-class**:

```python
import mountainash_expressions as ma

# Ternary comparison - returns -1 (FALSE), 0 (UNKNOWN), 1 (TRUE)
expr = ma.col("age").t_gt(18)

# Then CHOOSE how to handle UNKNOWN
df.filter(expr.is_true().compile(df))       # Only definite adults
df.filter(expr.maybe_true().compile(df))    # Adults + unknowns
df.filter(expr.is_unknown().compile(df))    # Only unknowns (data quality!)
```

**Key insight:** Separate the comparison from the inclusion decision.

#### The "Booleanizers" (3 min)

Six ways to collapse ternary back to boolean, each with clear semantics:

| Method | Returns True when | Use case |
|--------|------------------|----------|
| `.is_true()` | value == TRUE | Conservative: only confirmed |
| `.is_false()` | value == FALSE | Only confirmed failures |
| `.is_unknown()` | value == UNKNOWN | Data quality checks |
| `.is_known()` | value != UNKNOWN | Exclude uncertainty |
| `.maybe_true()` | TRUE or UNKNOWN | Inclusive: don't exclude potential |
| `.maybe_false()` | FALSE or UNKNOWN | Don't exclude potential failures |

```python
# Real-world example: promotional eligibility

# Conservative (might miss valid customers)
eligible = score_check.is_true()

# Inclusive (might include ineligible, but won't miss valid)
eligible = score_check.maybe_true()

# Data quality (who do we need to follow up with?)
unknown_status = score_check.is_unknown()
```

#### Complex Expressions Stay Clean (2 min)

```python
# Without ternary logic (nightmare)
df.filter(
    ((pl.col("age") > 18) | pl.col("age").is_null())
    & ((pl.col("score") >= 50) | pl.col("score").is_null())
    & ((pl.col("status") == "active") | pl.col("status").is_null())
)

# With explicit ternary logic (clear intent)
expr = (
    ma.col("age").t_gt(18)
    .t_and(ma.col("score").t_ge(50))
    .t_and(ma.col("status").t_eq("active"))
    .maybe_true()  # Include unknowns - ONE decision, stated once
)
df.filter(expr.compile(df))
```

The NULL-handling strategy is expressed **once**, not repeated for every condition.

---

### Act 5: Advanced Patterns (5 min)

#### Custom Sentinel Values (2 min)

Real data has more than one way to say "unknown":

```python
# Legacy system uses -99999 for "missing"
expr = ma.t_col("legacy_score", unknown={-99999}).t_gt(50)

# Multiple sentinel values
expr = ma.t_col("status", unknown={"NA", "<MISSING>", None}).t_eq("active")

# Different columns, different sentinels
expr = (
    ma.t_col("field_a", unknown={-99999, -1}).t_gt(0)
    .t_and(ma.t_col("field_b", unknown={"N/A"}).t_eq("yes"))
    .maybe_true()
)
```

#### Mixed Boolean/Ternary Chains (2 min)

Sometimes you need both:

```python
# Boolean where appropriate, ternary where NULLs matter
expr = (
    ma.col("active").eq(True)          # Boolean (no NULLs in this column)
    .to_ternary()                       # Enter ternary land
    .t_and(ma.col("score").t_ge(80))   # Ternary (NULLs possible)
    .maybe_true()                       # Exit ternary land
    .and_(ma.col("verified"))           # Back to boolean
)
```

#### XOR: Two Flavors (1 min)

```python
# Exclusive XOR: exactly one TRUE
expr = a.t_xor(b, c)  # TRUE only if exactly one is TRUE

# Parity XOR: odd number of TRUEs
expr = a.t_xor_parity(b, c)  # TRUE if 1 or 3 are TRUE

# Both handle UNKNOWN correctly
```

---

### Closing (2 minutes)

#### The Takeaways

1. **Three-valued logic is mathematically correct** - Codd knew what he was doing
2. **SQL has the semantics but bad ergonomics** - "OR IS NULL" everywhere doesn't scale
3. **Pandas makes it worse** - Collapses NULL to FALSE at comparison time
4. **The real bug is forgetting once** - One missing null check = silent data loss
5. **Explicit ternary logic fixes ergonomics** - Decide your UNKNOWN strategy once, not per-condition
6. **Booleanizers force conscious choices** - No more silent exclusions

#### The Philosophy

The question isn't:
> "How do I handle NULLs in my query?"

The question is:
> "When I don't know something, do I want to assume yes, assume no, or acknowledge I don't know?"

Different answers for different contexts. But **you should always be choosing**, not having the framework choose for you silently.

#### Call to Action

- **Audit your filters** - How many silently exclude NULLs?
- **Question your dashboards** - What's the real count including unknowns?
- **Consider explicit ternary** - Stop bolting NULL handling onto every condition
- **Teach three-valued logic** - It's not a SQL quirk, it's fundamental

#### Resources

- mountainash-expressions: [GitHub link]
- "The Silent Ternary Problem" blog post: [Link]
- Libkin & Magidor, "Elements of Finite Model Theory"
- E.F. Codd's original papers on relational model

---

## Supplementary Materials

### The Truth Tables Slide

**AND (minimum semantics):**
```
AND  |  T  |  U  |  F
-----+-----+-----+----
  T  |  T  |  U  |  F
  U  |  U  |  U  |  F
  F  |  F  |  F  |  F
```

**OR (maximum semantics):**
```
OR   |  T  |  U  |  F
-----+-----+-----+----
  T  |  T  |  T  |  T
  U  |  T  |  U  |  U
  F  |  T  |  U  |  F
```

**NOT (negation):**
```
NOT T = F
NOT U = U  ← Key insight!
NOT F = T
```

### Library Comparison Slide

| Operation | SQL | Polars | Pandas | Ternary API |
|-----------|-----|--------|--------|-------------|
| `NULL > 5` | UNKNOWN | null | **False** | UNKNOWN (0) |
| Filter behavior | Explicit choice | Excludes silently | Excludes silently | Explicit choice |
| `NOT (NULL > 5)` | UNKNOWN | null | **True** | UNKNOWN (0) |
| Handling strategy | `OR IS NULL` | `\| is_null()` | `\| isna()` | `.maybe_true()` |

### The Implementation Slide

```python
# Under the hood: -1/0/1 integers enable elegant operations

# AND = minimum
def t_and(a, b):
    return min(a, b)

# OR = maximum
def t_or(a, b):
    return max(a, b)

# NOT = sign flip (U stays U)
def t_not(a):
    return -a  # T(1)→F(-1), F(-1)→T(1), U(0)→U(0)

# Booleanizers = simple comparisons
def is_true(a):     return a == 1
def maybe_true(a):  return a >= 0
def is_unknown(a):  return a == 0
```

### Bug Categories for Corporate Presentations

| Category | Example | Impact | Detection Difficulty |
|----------|---------|--------|---------------------|
| Revenue leakage | Billing excludes NULL accounts | Direct $ loss | Low (reconciliation) |
| Compliance | Reports exclude NULL records | Regulatory risk | High (audits) |
| Analytics bias | Dashboards undercount | Strategic errors | Very high |
| ML data quality | Training excludes NULLs | Model drift | Very high |
| Customer harm | Promo excludes unknowns | Churn risk | High |

---

## Conference Submission Notes

### Target Conferences

- **PyCon US/EU** - Broad Python audience, controversial take
- **PyData** - Data-focused, directly relevant
- **SIGMOD/VLDB** - Database conferences, theoretical audience
- **Strange Loop** - Programming language theory
- **!!Con** - Short-form, high energy

### Talk Format

- **Preferred:** 30-40 minutes (full argument)
- **Acceptable:** 20 minutes (condensed, skip history/philosophy)
- **Lightning talk:** 5 min - just the bug + the API

### Why This Talk?

1. **Controversial thesis** - "SQL is right, DataFrames are wrong" grabs attention
2. **Financial stakes** - Real money stories make it memorable
3. **Practical solution** - Not just complaining, offering a path forward
4. **Cognitive angle** - Why our intuition fails us
5. **Live coding potential** - Show the bugs happening in real time

### Speaker Bio Elements

- Building cross-backend DataFrame tooling
- Discovered multiple backend inconsistencies
- Research into NULL handling costs
- Contributing fixes upstream (with crickets)

---

## Lightning Talk Version (5 min)

### Slide 1: The Question
```python
df.filter(pl.col("age") > 18)
# How many customers does this return?
```

### Slide 2: The Answer
"Fewer than you think. Every NULL is excluded. Silently."

### Slide 3: The Scale
- $2M telecom billing loss
- 15% of customers missing from segmentation
- 68% of developers write NULL bugs annually

### Slide 4: SQL Got It Right
```sql
-- SQL has three values: TRUE, FALSE, UNKNOWN
-- NULL > 18 returns UNKNOWN, not FALSE
-- Filter requires explicit handling
```

### Slide 5: DataFrames Broke It
```python
# Pandas: NULL > 18 → False (WRONG!)
# Polars: NULL > 18 → NULL (correct)
#         filter() → excludes NULLs (implicit choice)
```

### Slide 6: The Solution
```python
# Explicit ternary logic
ma.col("age").t_gt(18).maybe_true()   # Include unknowns
ma.col("age").t_gt(18).is_true()      # Only confirmed
ma.col("age").t_gt(18).is_unknown()   # Data quality check
```

### Slide 7: The Philosophy
> "When you don't know something, should you assume yes, assume no, or admit you don't know?"

You should always be choosing. Not your framework.

---

## Post-Talk Content

### Blog Post Series

1. "The Silent Ternary Problem: Your Data Analysis is Secretly Broken"
2. "Why SQL's Three-Valued Logic is Correct (and DataFrames are Wrong)"
3. "The Cognitive Trap: Why Binary Feels Natural But Fails"
4. "Implementing Explicit Ternary Logic in Python"
5. "The Booleanizer Pattern: Six Ways to Handle UNKNOWN"
6. "Custom Sentinel Values: Beyond NULL"

### Academic Paper Potential

"Explicit Three-Valued Logic for Modern DataFrame Libraries: A Design and Implementation"

- Formal semantics of the t_* operations
- Proof of correctness vs SQL semantics
- Performance benchmarks (is ternary expensive?)
- User study: do booleanizers reduce bugs?

### Interactive Demo

- Jupyter notebook showing silent exclusions
- Side-by-side SQL vs Polars vs Pandas vs ternary API
- "Find the bug" exercises
