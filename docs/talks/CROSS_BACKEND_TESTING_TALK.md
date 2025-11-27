# Conference Talk: Cross-Backend DataFrame Testing

## Talk Title Options

1. **"I Tested the Same Expression on 6 Backends and Found 47 Bugs"**
2. **"Property-Based Testing for DataFrames: Finding the Lies Libraries Tell"**
3. **"Trust, But Verify: Cross-Backend DataFrame Testing in Production"**
4. **"The Bugs That Unit Tests Can't Find: Cross-Backend DataFrame Verification"**

---

## Talk Abstract (300 words)

> "Works on my machine" is annoying. "Works on my DataFrame library" is terrifying.
>
> When we migrated from Pandas to Polars, we expected syntax changes. What we didn't expect: `-7 % 3` returning `2` in Polars but `-1` in our Ibis-DuckDB pipeline. Same expression. Different answers. No errors.
>
> This talk explores what happens when you run the same logical operations across Polars, Pandas, Narwhals, Ibis-DuckDB, Ibis-SQLite, and Ibis-Polars—and systematically verify they produce identical results. Spoiler: they don't.
>
> We'll cover:
> - **The inconsistencies we found**: Division semantics, modulo behavior, NULL handling, temporal edge cases, and string operations that silently differ
> - **A testing methodology**: Using pytest parametrization and property-based testing (Hypothesis) to systematically verify cross-backend behavior
> - **The bugs we reported**: Real issues filed against major DataFrame libraries, and how maintainers responded
> - **A pattern for backend-agnostic expressions**: How we built an abstraction layer that normalizes these differences
>
> You'll leave with:
> - A healthy skepticism of "just use library X, it's faster"
> - Concrete testing patterns you can apply to your own multi-backend code
> - An understanding of which operations are safe to assume consistent, and which are landmines
> - Tools to verify your own DataFrame pipelines before they corrupt your data
>
> Whether you're migrating between libraries, building backend-agnostic tooling, or just want to understand why your numbers don't match between environments, this talk will change how you think about DataFrame operations.

---

## Talk Outline (30-40 minutes)

### Act 1: The Discovery (8 minutes)

#### Opening Hook (2 min)
```python
# Pop quiz: What does this return?
result = df.filter(col("value") % 3 == 2)
# where value = -7

# A) 2 rows (values that equal 2 after modulo)
# B) 0 rows
# C) Depends on your DataFrame library
# D) Depends on your DATABASE library
```
**Answer: C and D.** And nobody warns you.

#### The Migration Story (3 min)
- "We were migrating from Pandas to Polars for performance"
- "We had tests. They passed."
- "Production numbers didn't match. Silently."
- "Three weeks of debugging later..."

#### The Scope of the Problem (3 min)
Show the matrix of backends tested:
```
                 Polars  Pandas  Narwhals  Ibis-DuckDB  Ibis-SQLite  Ibis-Polars
Modulo (-7%3)      2       2        2          -1           -1           2
Division (20/3)   6.67    6.67     6.67        6.67          6           6.67
NULL > 5          NULL    False    NULL        NULL         NULL         NULL
```

**Key point:** These aren't bugs. They're *documented behavior*. But nobody reads the docs for basic arithmetic.

---

### Act 2: The Methodology (12 minutes)

#### The Testing Stack (3 min)
```python
# Our tools
- pytest (parametrization)
- hypothesis (property-based testing)
- A LOT of patience
```

#### Pattern 1: Parametrized Backend Testing (4 min)

```python
ALL_BACKENDS = ["polars", "pandas", "narwhals", "ibis-duckdb", "ibis-sqlite", "ibis-polars"]

@pytest.fixture(params=ALL_BACKENDS)
def backend_df(request, sample_data):
    """Create the same DataFrame on each backend."""
    if request.param == "polars":
        return pl.DataFrame(sample_data)
    elif request.param == "ibis-duckdb":
        return ibis.memtable(sample_data, backend=ibis.duckdb.connect())
    # ... etc

@pytest.mark.parametrize("a,b,expected", [
    (7, 3, 1),    # Positive modulo
    (-7, 3, 2),   # Negative dividend - HERE BE DRAGONS
    (7, -3, -2),  # Negative divisor
])
def test_modulo_consistency(backend_df, a, b, expected):
    """Modulo should follow Python semantics on all backends."""
    result = select_and_extract(backend_df, col("value") % lit(b),
                                 where=col("value") == a)
    assert result == expected, f"Backend {get_backend_name(backend_df)} disagrees"
```

**Live demo:** Run this test, watch it fail on DuckDB and SQLite.

#### Pattern 2: Property-Based Cross-Verification (5 min)

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=5, max_size=100))
def test_modulo_identical_across_backends(values):
    """Whatever modulo does, it should do the SAME THING everywhere."""

    # Create identical data on all backends
    backends = {
        "polars": pl.DataFrame({"v": values}),
        "duckdb": ibis.memtable({"v": values}),
        "pandas": pd.DataFrame({"v": values}),
    }

    # Apply same operation
    results = {}
    for name, df in backends.items():
        results[name] = apply_modulo(df, "v", 7).to_list()

    # They should all match (even if we don't know what "correct" is)
    first = results["polars"]
    for name, result in results.items():
        assert result == first, f"{name} differs from polars: {result} vs {first}"
```

**Key insight:** Property-based testing finds edge cases you'd never think to test manually.

---

### Act 3: The Bugs We Found (10 minutes)

#### Category 1: Arithmetic Semantics (3 min)

**Modulo vs Remainder:**
```python
# Python/Polars: Modulo (result takes sign of divisor)
-7 % 3 = 2    # Because -7 = -3*3 + 2

# SQL/DuckDB: Remainder (result takes sign of dividend)
-7 % 3 = -1   # Because -7 = -2*3 + (-1)
```

**Integer Division:**
```python
# Most backends
20 / 3 = 6.666...

# SQLite
20 / 3 = 6  # Integer division by default!
```

#### Category 2: NULL Handling (3 min)

```python
# What does NULL > 5 return?

# Polars: NULL (correct three-valued logic)
# Pandas: False (wat?)
# SQL: NULL (correct)

# What about NULL == NULL?
# Polars: NULL
# Pandas: True (double wat?)
# SQL: NULL
```

The rabbit hole: `fill_null()`, `coalesce()`, and `is_null()` all behave subtly differently.

**Issue filed:** [Link to real GitHub issue]

#### Category 3: String Operations (2 min)

```python
# Case sensitivity in contains()
"Hello".contains("HELLO", case_sensitive=???)

# Some backends default to case-sensitive
# Some default to case-insensitive
# Some don't have the parameter at all
```

#### Category 4: Temporal Edge Cases (2 min)

```python
# Adding months to Jan 31
date(2024, 1, 31) + months(1) = ???

# Polars: Feb 29 (clamp to end of month)
# DuckDB: Feb 29
# Pandas: Error? March 2? Depends on version!

# Timezone handling: don't get me started
```

#### Category 5: The Silent Killer - Ibis Type Downcasting (3 min)

**This one deserves its own slide.** It's a bug that lives in the *seam* between two correct systems.

```python
# User writes:
ibis.literal(2) ** table.exponent  # where exponent = 10

# Expected:
2^10 = 1024

# What actually happens:
# Step 1: Ibis infers literal type
infer_integer(2) → int8  # "2 fits in int8!"

# Step 2: Ibis sends to Polars
pl.lit(2, dtype=pl.Int8) ** pl.col('exponent')

# Step 3: Polars respects the explicit dtype
2^10 in Int8 → OVERFLOW → 0

# Result: Silent data corruption. No error. No warning.
```

**The horror:** This affects ALL arithmetic, not just power:
```python
ibis.literal(100) * table.price  # where price is Int8
# 100 * 25 = 2500... but Int8 max is 127
# Result: garbage
```

**Cross-backend comparison:**
| Backend | `literal(100) * int8_column(25)` | Behavior |
|---------|----------------------------------|----------|
| Polars | -12 | Silent corruption |
| DuckDB | Exception | Loud failure (detectable!) |
| SQLite | 2500 | Correct (auto-promotes) |

**The bug lives in the seam:**
- Polars: "You gave me Int8, I respect that" ✅
- Ibis: "I inferred smallest type that fits" ✅
- Together: **Silent data corruption** ❌

---

### Interlude: What Happens After You File Bugs? (3 min)

*[This is the part where you get real with the audience]*

**The issues I filed:**

| Issue | What I Found | What I Provided | Status |
|-------|--------------|-----------------|--------|
| [#11740](https://github.com/ibis-project/ibis/issues/11740) | `pow()` overflow | Root cause + **fix PR** | Open, no response |
| [#11742](https://github.com/ibis-project/ibis/issues/11742) | `lit + col` fails | Code path analysis + one-line fix | Open, no response |
| [#11749](https://github.com/ibis-project/ibis/issues/11749) | Multiplication overflow | Cross-backend repro | Open, no response |

**Two weeks. Crickets.**

*[Beat]*

I'm not complaining—maintainers are busy, it's open source, I get it.

But here's the point: **Even when you find the bugs, even when you document them perfectly, even when you write the fix... you can't always get them merged.**

**This is why abstraction layers matter.**

You can't wait for upstream fixes. You need to:
1. Detect the inconsistency
2. Work around it in YOUR code
3. Document the workaround
4. Move on

```python
# Our workaround in mountainash-expressions:
# Don't let Ibis choose the literal type—normalize it ourselves
def compile_literal(value, backend):
    if backend == "ibis-polars":
        # Force Int64 to avoid overflow
        return ibis.literal(value).cast(ibis.dtype("int64"))
    return ibis.literal(value)
```

---

### Act 4: The Solution Pattern (8 minutes)

#### The Abstraction Layer Approach (3 min)

```python
# Instead of this:
if backend == "polars":
    result = df.filter(pl.col("a") % 3 == 2)
elif backend == "duckdb":
    # Normalize remainder to modulo
    result = df.filter(((ibis._["a"] % 3) + 3) % 3 == 2)

# We built this:
from mountainash_expressions import col

expr = col("a").modulo(3).eq(2)
result = df.filter(expr.compile(df))  # Normalizes per-backend
```

#### The Three-Layer Architecture (3 min)

```
User writes:     col("a").modulo(3)
                      ↓
AST Node:        ModuloNode(left=ColumnNode("a"), right=LiteralNode(3))
                      ↓
Backend compile:
  - Polars: pl.col("a") % 3
  - DuckDB: ((a % 3) + 3) % 3  # Normalized!
  - SQLite: ((a % 3) + 3) % 3  # Normalized!
```

**Key insight:** Abstraction isn't just about syntax—it's about *semantics*.

#### Lessons for Your Own Code (2 min)

1. **Test across backends from day one** - Not just before migration
2. **Use property-based testing** - Edge cases are where bugs hide
3. **Document your assumptions** - "Modulo follows Python semantics" is a requirement
4. **Consider an abstraction layer** - Even a thin one saves pain later

---

### Closing (2 minutes)

#### The Takeaways

1. **DataFrame libraries disagree on basic operations** - And they're all "correct" by their own definitions
2. **Your tests probably don't catch this** - Unit tests use one backend
3. **Cross-backend testing is achievable** - Pytest parametrization + Hypothesis
4. **Abstraction can normalize semantics** - Not just syntax

#### Call to Action

- **If you use multiple backends:** Start cross-backend testing TODAY
- **If you're building libraries:** Consider backend-agnostic expression design
- **If you've found inconsistencies:** Report them! Maintainers appreciate it

#### Resources
- mountainash-expressions: [GitHub link]
- Our test suite: [Link to tests/cross_backend/]
- Issues we've filed: [Links]
- This slide deck: [Link]

---

## Supplementary Materials

### Demo Repository Structure

```
cross-backend-testing-demo/
├── conftest.py              # Backend fixtures
├── test_arithmetic.py       # Modulo, division, power
├── test_null_handling.py    # NULL comparisons, coalesce
├── test_string_ops.py       # Case sensitivity, unicode
├── test_temporal.py         # Date arithmetic, timezones
├── results/
│   └── inconsistency_matrix.csv  # Published results
└── README.md
```

### Inconsistencies Discovered (For Slides)

| Operation | Polars | Pandas | DuckDB | SQLite | Issue Filed |
|-----------|--------|--------|--------|--------|-------------|
| `-7 % 3` | 2 | 2 | -1 | -1 | [link] |
| `20 / 3` (int inputs) | 6.67 | 6.67 | 6.67 | 6 | [link] |
| `NULL == NULL` | null | True | null | null | [link] |
| `NULL > 5` | null | False | null | null | [link] |
| `"A".contains("a")` | False | True | True | varies | [link] |
| `Jan31 + 1month` | Feb29 | varies | Feb29 | error | [link] |
| `floor(-2.5)` | -3 | -3 | -3 | -2 | [link] |
| `round(2.5)` | 2 | 2 | 3 | 3 | - |

### Issues Filed (Real Examples to Include)

*[This section would link to actual GitHub issues you've filed]*

Example format:
- **Ibis #XXXX**: "Modulo operator uses remainder semantics on DuckDB backend"
  - Status: Confirmed, won't fix (by design)
  - Our workaround: Normalize in expression layer

- **Polars #XXXX**: "Inconsistent NULL handling in comparison chains"
  - Status: Fixed in v1.X.X
  - Our workaround: Explicit is_null() checks

---

## Conference Submission Notes

### Target Conferences
- **PyCon US/EU** - Broad Python audience
- **PyData** - Data-focused, perfect fit
- **EuroPython** - Large, diverse audience
- **SciPy** - Scientific computing focus
- **Normconf** - "Normal" data work, very aligned

### Talk Format
- **Preferred:** 30-40 minutes (full session)
- **Acceptable:** 20 minutes (condensed, skip some bug categories)
- **Lightning talk version:** 5 min - just the hook + key findings + resources

### Speaker Bio Elements
- Experience with multi-backend data platforms
- Contributions to open source (issues filed)
- Building mountainash-expressions

### Why This Talk?

1. **Practical value** - Attendees leave with testing patterns they can use Monday
2. **War stories** - Real bugs, real migrations, real pain
3. **Upstream contribution** - Shows healthy OSS engagement
4. **Novel content** - Not "intro to Polars" or "intro to testing"
5. **Live demo potential** - Actually run the failing tests

---

## Bonus: Lightning Talk Version (5 min)

### Slide 1: The Question
```python
# What does -7 % 3 return?
```

### Slide 2: The Answers
| Library | Result |
|---------|--------|
| Polars | 2 |
| DuckDB | -1 |
| SQLite | -1 |
| Python | 2 |

"These are all correct. By their own definitions."

### Slide 3: The Scale
- We tested 6 backends
- 47 behavioral differences found
- 12 issues filed upstream
- 0 warnings from any library

### Slide 4: The Test
```python
@pytest.fixture(params=ALL_BACKENDS)
def backend_df(request):
    ...

def test_modulo(backend_df):
    assert compute(backend_df, -7 % 3) == 2  # Python semantics
```

### Slide 5: The Call to Action
- Test across backends BEFORE migration
- Use property-based testing for edge cases
- github.com/mountainash-io/mountainash-expressions
- "Expressions that mean what they say"

---

## Post-Talk Content

### Blog Post Series
1. "I Tested 6 DataFrame Backends and Here's What I Found" (overview)
2. "The Modulo Problem" (deep dive)
3. "NULL Handling Across DataFrames" (deep dive)
4. "Property-Based Testing for DataFrames" (methodology)
5. "Building a Backend-Agnostic Expression Layer" (solution)

### Interactive Demo
- Google Colab notebook with all tests runnable
- Let readers verify on their own data

### Shareable Artifacts
- Inconsistency matrix (CSV/image)
- Test file templates
- pytest fixtures for backend parametrization
