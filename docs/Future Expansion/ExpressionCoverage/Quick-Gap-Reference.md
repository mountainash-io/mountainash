# Quick Gap Reference: mountainash-expressions vs Ibis-Polars

**Last Updated:** 2025-01-09

This document provides a quick, scannable reference of operation gaps between mountainash-expressions and Ibis-Polars.

---

## Summary

| Metric | Value |
|--------|-------|
| **Current Coverage** | ~38-42% |
| **Total Operations** | 170 (Ibis-Polars) |
| **Implemented** | 65 (mountainash) |
| **Gap** | 105 operations (to parity) |
| **ML Metrics** | +12 operations (beyond parity) |
| **Time to 80%+** | 17-27 weeks |
| **Time to 100%+** | 21-34 weeks (with ML) |

---

## Quick Status by Category

| Category | Coverage | Status | Notes |
|----------|----------|--------|-------|
| **Boolean/Logical** | 100%+ | ✅ Excellent | Includes unique XOR parity |
| **Arithmetic** | 87.5% | ✅ Good | Missing unary negation |
| **Comparison** | 75% | ✅ Good | Missing between, identical_to |
| **Null Handling** | 80% | ✅ Good | Missing nullif |
| **String (Basic)** | 100% | ✅ Excellent | All basic ops covered |
| **Pattern/Regex** | 100% | ✅ Excellent | Includes LIKE (unique) |
| **Temporal Arithmetic** | 86% | ✅ Good | Missing generic diff |
| **Temporal Extract** | 60% | ⚠️ Moderate | Missing specialized extracts |
| **Collection/Set** | 67% | ⚠️ Moderate | Missing IN subquery |
| **Type Ops** | 50% | ⚠️ Moderate | Missing try_cast |
| **Conditional** | 20% | ⚠️ Poor | Missing CASE WHEN |
| **String (Advanced)** | 0% | ❌ Missing | 11 operations |
| **Temporal Construct** | 0% | ❌ Missing | 5 operations |
| **Temporal Parse** | 0% | ❌ Missing | 4 operations |
| **Math** | 0% | ❌ **CRITICAL** | 26 operations |
| **Array** | 0% | ❌ **CRITICAL** | 18 operations |
| **Window/Analytic** | 0% | ❌ **CRITICAL** | 17 operations |
| **Bitwise** | 0% | ❌ Missing | 6 operations |
| **ML Metrics (Classification)** | 0% | 🟡 **HIGH** | 5 operations (beyond Ibis) |
| **ML Metrics (Ranking)** | 0% | 🟡 **HIGH** | 3 operations (beyond Ibis) |
| **ML Metrics (Credit Risk)** | 0% | 🟢 MEDIUM | 4 operations (beyond Ibis) |

---

## Critical Gaps (Must Have)

### 🔴 Math Operations (26 missing)

**Why Critical:** Can't do analytical/scientific work without these.

**Quick Wins (10 ops):**
```python
# Basic
.abs()           # Absolute value
.sign()          # Sign (-1, 0, 1)
.sqrt()          # Square root
.round(n)        # Round to n decimals
.floor()         # Round down
.ceil()          # Round up

# Logarithms
.ln()            # Natural log
.log(base)       # Log with base
.log10()         # Base-10 log
.exp()           # e^x

# Checks
.is_nan()        # Check for NaN
.is_inf()        # Check for infinity
```

**Advanced (16 ops):**
```python
# Trigonometry
.sin(), .cos(), .tan()
.asin(), .acos(), .atan(), .atan2(x, y)
.cot()

# Other
.radians(), .degrees()
.clip(lower, upper)

# Constants
ma.pi(), ma.e()
```

---

### 🔴 Array Operations (18 missing)

**Why Critical:** Arrays/lists are fundamental data structures.

**Note:** Backend support varies significantly.

**Essential (5 ops):**
```python
.array_length()           # Get size
.array_index(i)           # Access element
.array_contains(value)    # Check membership
.array_slice(start, stop) # Extract sub-array
ma.array(*values)         # Construct array
```

**High Value (7 ops):**
```python
.array_concat(other)      # Concatenate
.array_union(other)       # Set union
.array_intersect(other)   # Set intersection
.array_distinct()         # Remove duplicates
.array_sum()              # Sum elements
.array_mean()             # Mean of elements
.array_min(), .array_max() # Min/max
```

**Medium Value (6 ops):**
```python
.array_sort()             # Sort array
.array_remove(value)      # Remove element
.array_flatten()          # Flatten nested
.array_any()              # Any element true
.array_all()              # All elements true
```

---

### 🔴 Window/Analytic Functions (17 missing)

**Why Critical:** Essential for ranking, time series analysis, and sequential comparisons.

**Note:** Requires window specification system (PARTITION BY, ORDER BY, frame specs).

**Ranking Functions (6 ops):**
```python
ma.rank().over(group_by="category", order_by=col("sales").desc())
ma.dense_rank().over(...)       # Rank without gaps
ma.row_number().over(...)       # Sequential numbering
ma.percent_rank().over(...)     # Percentile rank
ma.cume_dist().over(...)        # Cumulative distribution
ma.ntile(4).over(...)           # Quartiles/buckets
```

**Offset/Position Functions (5 ops):**
```python
col("sales").lag(1).over(order_by="month")      # Previous value
col("sales").lead(1).over(order_by="month")     # Next value
col("value").nth_value(3).over(...)             # Nth value
col("value").first_value().over(...)            # First in window
col("value").last_value().over(...)             # Last in window
```

**Cumulative Functions (6 ops):**
```python
col("amount").cumsum()          # Running total
col("value").cummean()          # Running average
col("value").cummin()           # Running minimum
col("value").cummax()           # Running maximum
col("flag").cumany()            # Cumulative any
col("flag").cumall()            # Cumulative all
```

**Window Specification:**
```python
# Window with grouping and ordering
.over(group_by="category", order_by="date")

# Moving window (7-day moving average)
.over(rows=(-6, 0), order_by="date")

# Range-based window
.over(range=("-7 days", "0"), order_by="date")
```

**Use Cases:**
```python
# Top 3 per category
products.filter(
    ma.rank().over(group_by="category", order_by=col("sales").desc()) <= 3
)

# 7-day moving average
col("sales").mean().over(rows=(-6, 0), order_by="date")

# Period-over-period change
col("sales") - col("sales").lag(1).over(order_by="month")

# Running total by customer
col("amount").cumsum().over(group_by="customer_id", order_by="date")
```

---

### 🟡 ML/Statistical Metrics (12 missing - BEYOND Ibis-Polars)

**Why Important:** Machine learning model evaluation and credit risk analytics.

**Note:** These operations go BEYOND Ibis-Polars expression parity. They are domain-specific ML metrics.

**Phase 9A: Classification Metrics (5 ops - No Window Functions):**
```python
# Binary classification evaluation
metrics = ma.evaluate_classification(
    df,
    actual=col("actual"),
    prediction=col("pred")
)
# Returns: {"precision": 0.85, "recall": 0.78, "f1": 0.81, "accuracy": 0.82}

# Or individual metrics
ma.precision(col("actual"), col("pred"))
ma.recall(col("actual"), col("pred"))
ma.f1_score(col("actual"), col("pred"))
ma.accuracy(col("actual"), col("pred"))
```

**Phase 9B: Ranking Metrics (3 ops - Requires Window Functions):**
```python
# ROC-AUC and Gini (requires ranking + cumulative sums)
roc_auc = ma.roc_auc(
    actual=col("actual"),
    prediction_proba=col("pred_proba")
).eval()(df)

gini = ma.gini(
    actual=col("actual"),
    prediction_proba=col("pred_proba")
).eval()(df)
# Gini = 2*AUC - 1

log_loss = ma.log_loss(
    actual=col("actual"),
    prediction_proba=col("pred_proba")
).eval()(df)
```

**Phase 9C: Credit Risk Metrics (4 ops - Optional):**
```python
# Information Value (feature selection)
iv = ma.information_value(
    actual=col("default"),
    feature=col("income"),
    bins=10
).eval()(df)

# Weight of Evidence (transformation)
df_woe = ma.with_columns(
    df,
    income_woe=ma.weight_of_evidence(
        actual=col("default"),
        feature=col("income"),
        bins=10
    )
)

# Population Stability Index (drift detection)
psi = ma.psi(
    baseline=col("score_baseline"),
    analysis=col("score_current"),
    bins=10
).eval()(df)

# Marginal IV (change over time)
miv = ma.marginal_iv(
    actual=col("default"),
    feature=col("income"),
    bins=10,
    time_col=col("month")
).eval()(df)
```

**Dependencies:**
- Phase 9A: None (aggregations only)
- Phase 9B: Requires Phase 8 (Window Functions)
- Phase 9C: Independent (optional)

**Reference:**
- Research: `/docs/ML-Statistical-Functions-Research.md`
- User Implementation: `/docs/User-Metrics-Implementation-Analysis.md`
- Framework Analysis: `/docs/Framework-Architecture-Analysis.md`

---

## High Priority Gaps (Should Have)

### 🟡 Advanced Conditionals (5 missing)

**Why Important:** Common SQL patterns for business logic.

```python
# Multi-branch CASE
ma.case(
    when=col("status") == "A", then="Active",
    when=col("status") == "I", then="Inactive",
    otherwise="Unknown"
)

# Min/max of N values
ma.least(col("a"), col("b"), col("c"))
ma.greatest(col("x"), col("y"), col("z"))

# Conditional null
col("value").nullif(0)  # NULL if value == 0
```

---

### 🟡 Temporal Construction (5 missing)

**Why Important:** Essential for ETL - building dates from parts.

```python
# Construct from components
ma.date_from_ymd(2025, 1, 9)
ma.timestamp_from_ymdhms(2025, 1, 9, 14, 30, 0)
ma.time_from_hms(14, 30, 0)

# From Unix timestamp
ma.timestamp_from_unix(1704812400)

# Create interval
ma.interval_from_integer(7, "days")
```

---

### 🟡 Temporal Parsing (4 missing)

**Why Important:** Parse date strings in ETL pipelines.

```python
# Parse strings
col("date_str").string_to_date("%Y-%m-%d")
col("ts_str").string_to_timestamp("%Y-%m-%d %H:%M:%S")
col("time_str").string_to_time("%H:%M:%S")

# Format output
col("timestamp").strftime("%Y-%m-%d %H:%M:%S")
```

---

### 🟡 Temporal Constants (2 missing)

```python
ma.now()      # Current timestamp
ma.today()    # Current date
```

---

## Medium Priority Gaps (Nice to Have)

### 🟠 Advanced String Ops (11 missing)

**High Value (3):**
```python
col("text").split(",")                  # Split to array
col("text").find("substring")           # Find position
col("text").regex_extract(r"(\d+)", 1)  # Extract group
```

**Medium Value (5):**
```python
col("name").capitalize()       # Capitalize first letter
col("text").repeat(3)          # Repeat N times
col("code").lpad(10, "0")      # Left pad
col("code").rpad(10, " ")      # Right pad
ma.join(col("array"), ",")     # Join array to string
```

**Low Value (3):**
```python
col("text").reverse()          # Reverse string
col("text").str_right(5)       # Last N characters
```

---

### 🟠 Comparison Enhancements (2 missing)

```python
col("age").between(18, 65)     # Range check
col("a").identical_to(col("b"))  # Null-safe equality
```

---

### 🟠 Temporal Extractions (6 missing)

```python
col("date").iso_year()         # ISO 8601 year
col("date").day_of_year()      # Day of year (1-366)
col("ts").epoch_seconds()      # Unix timestamp
col("ts").microsecond()        # Microsecond component
col("ts").millisecond()        # Millisecond component
col("date").day_of_week_name() # "Monday", "Tuesday", etc.
```

---

### 🟠 Type Operations (1 missing)

```python
col("value").try_cast("int64")  # Safe cast (null on failure)
```

---

## Low Priority Gaps (Specialized)

### 🟢 Bitwise Operations (6 missing)

```python
col("a").bitwise_and(col("b"))
col("a").bitwise_or(col("b"))
col("a").bitwise_xor(col("b"))
col("a").bitwise_not()
col("value").left_shift(2)
col("value").right_shift(2)
```

---

### 🟢 Misc Operations

```python
col("value").negate()          # Unary negation (-x)
col("a").in_subquery(subquery) # IN with subquery
col("ts").timestamp_bucket("1h") # Bucket into intervals
```

---

## Unique mountainash-expressions Features

**Features we have that Ibis does NOT:**

### 1. Ternary Logic System
```python
# Three-valued logic (TRUE/FALSE/UNKNOWN)
expr.is_unknown()    # Check for UNKNOWN
expr.is_known()      # Check for TRUE or FALSE
expr.maybe_true()    # TRUE or UNKNOWN
expr.maybe_false()   # FALSE or UNKNOWN

# Ternary constants
ALWAYS_TRUE, ALWAYS_FALSE, ALWAYS_UNKNOWN
```

### 2. XOR Parity
```python
# Different from exclusive XOR
col("a").xor_parity(col("b"), col("c"))
```

### 3. SQL LIKE Pattern
```python
col("name").like("John%")
col("email").like("%@%.com")
```

### 4. Regex Full Match
```python
col("code").regex_match(r"^[A-Z]{3}-\d{4}$")
```

### 5. Natural Language Temporal
```python
# Inspired by journalctl/find
within_last(col("timestamp"), "10 minutes")
older_than(col("created"), "7 days")
time_ago("2 hours")
between_last(col("updated"), "1 hour", "3 hours")

# Flexible offset_by
col("date").offset_by("2d")     # 2 days
col("date").offset_by("3mo")    # 3 months
col("date").offset_by("-1y")    # 1 year ago
col("date").offset_by("1h30m")  # 1.5 hours
```

---

## Implementation Priority Matrix

| Priority | Operations | Impact | Effort | Value/Effort |
|----------|-----------|--------|--------|--------------|
| 🔴 P1 | Math (12) | Critical | 2-3 weeks | **Very High** |
| 🔴 P2 | Conditionals (5) | High | 1-2 weeks | **Very High** |
| 🟡 P3 | Strings (10) | Medium | 1-2 weeks | High |
| 🟡 P4 | Temporal (12) | Medium-High | 2-3 weeks | High |
| 🟡 P5 | Math Advanced (14) | Medium | 2-3 weeks | Medium |
| 🔴 P6 | Arrays (18) | High | 4-6 weeks | Medium* |
| 🟢 P7 | Specialized (12) | Low | 1-2 weeks | Low |
| 🔴 P8 | Window Functions (17) | Critical | 3-5 weeks | High** |
| 🟡 P9A | ML Classification (5) | High | 1-2 weeks | **Very High***\*\* |
| 🟡 P9B | ML Ranking (3) | High | 1-2 weeks | High***\*\*\* |
| 🟢 P9C | Credit Risk (4) | Medium | 2-3 weeks | Medium***\*\*\*\* |

*Arrays have high impact but medium value/effort due to complexity and backend compatibility issues.

**Window functions are critical for ranking/time series, but high complexity due to window specification system.

***Phase 9A can start immediately (aggregations only), provides ML evaluation capabilities beyond Ibis-Polars.

****Phase 9B requires Phase 8 (Window Functions) completion first.

*****Phase 9C is optional, domain-specific for credit risk analytics.

---

## Quick Decision Guide

**Question: Should we implement [operation]?**

### ✅ YES - Implement Soon If:
- It's in Priority 1 or 2 (Math, Conditionals)
- Users are asking for it
- It blocks other features
- All backends support it

### ⚠️ MAYBE - Implement Later If:
- It's in Priority 3-5
- Backend support is good
- It fits with current phase

### ❌ NO - Skip or Defer If:
- It's Priority 6+ (specialized)
- Backend support is poor
- Low user demand
- High complexity, low value

---

## Common Questions

### Q: Why is Math Priority 1?
**A:** Can't do analytical/scientific work without basic math. Fundamental operations.

### Q: Why are Arrays so complex?
**A:** Backend support varies significantly. Polars has excellent support, SQLite has almost none.

### Q: What about SQL aggregations (SUM, AVG, etc.)?
**A:** Those are table-level operations, not expression-level. Out of scope for this comparison.

### Q: Can I use mountainash-expressions for production today?
**A:** Yes, for operations that are implemented (40% coverage). Check compatibility before adopting.

### Q: When will we reach feature parity with Ibis?
**A:** Estimated 14-22 weeks for 80%+ coverage, following the roadmap.

---

## Quick Links

- **Full Comparison:** [Ibis-Polars-Comparison.md](./Ibis-Polars-Comparison.md)
- **Detailed Roadmap:** [Implementation-Roadmap.md](./Implementation-Roadmap.md)
- **Project CLAUDE.md:** [../../CLAUDE.md](../../CLAUDE.md)

---

**Document Type:** Quick Reference
**Audience:** Developers, Product Managers
**Maintenance:** Update after each phase completion
