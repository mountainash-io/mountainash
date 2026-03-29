# mountainash-expressions Implementation Roadmap

**Date:** 2025-01-09
**Current Coverage:** ~40-45% of Ibis-Polars capabilities
**Target Coverage:** 80%+
**Total Gap:** 88 operations
**Estimated Effort:** 14-22 weeks

## Overview

This roadmap outlines the implementation plan to expand mountainash-expressions from ~40% coverage to 80%+ coverage of Ibis-Polars expression operations. The plan is organized into 7 phases, prioritized by impact and implementation complexity.

---

## Phase 1: Essential Math Operations

**Duration:** 2-3 weeks
**Priority:** 🔴 CRITICAL
**Operations:** 10-12
**Complexity:** Medium

### Objectives
Enable basic analytical and scientific workloads by implementing fundamental math operations.

### Operations to Implement

#### Basic Math (6 operations)
- [x] `abs()` - Absolute value
- [x] `sign()` - Sign of number (-1, 0, 1)
- [x] `sqrt()` - Square root
- [x] `round(decimals)` - Round to N decimal places
- [x] `floor()` - Round down to integer
- [x] `ceil()` - Round up to integer

#### Logarithms & Exponential (5 operations)
- [x] `ln()` - Natural logarithm (base e)
- [x] `log(base)` - Logarithm with custom base
- [x] `log10()` - Base-10 logarithm
- [x] `log2()` - Base-2 logarithm
- [x] `exp()` - Exponential (e^x)

#### Special Checks (2 operations)
- [x] `is_nan()` - Check for NaN values
- [x] `is_inf()` - Check for infinity

### Implementation Checklist

**1. Constants & Enums**
- [ ] Add `CONST_MATH_OPERATORS` enum to `core/constants.py`
- [ ] Define all math operation types

**2. Node Types**
- [ ] Create `core/expression_nodes/math_expression_nodes.py`
- [ ] Implement `MathUnaryExpressionNode`
- [ ] Implement `MathBinaryExpressionNode`

**3. Visitor Mixin**
- [ ] Create `core/expression_visitors/math_mixins/basic_math_visitor.py`
- [ ] Implement visitor methods for all operations
- [ ] Add property `math_ops` mapping

**4. ExpressionSystem Interface**
- [ ] Extend `core/expression_system/base.py` with math methods:
  - [ ] `abs(arg)`
  - [ ] `sign(arg)`
  - [ ] `sqrt(arg)`
  - [ ] `round(arg, decimals)`
  - [ ] `floor(arg)`
  - [ ] `ceil(arg)`
  - [ ] `ln(arg)`
  - [ ] `log(arg, base)`
  - [ ] `log10(arg)`
  - [ ] `log2(arg)`
  - [ ] `exp(arg)`
  - [ ] `is_nan(arg)`
  - [ ] `is_inf(arg)`

**5. Backend Implementations**
- [ ] Implement all methods in `PolarsExpressionSystem`
- [ ] Implement all methods in `NarwhalsExpressionSystem`
- [ ] Implement all methods in `IbisExpressionSystem`

**6. ExpressionBuilder API**
- [ ] Add methods to `api/expression_builder.py`:
  - [ ] `.abs()`
  - [ ] `.sign()`
  - [ ] `.sqrt()`
  - [ ] `.round(decimals=0)`
  - [ ] `.floor()`
  - [ ] `.ceil()`
  - [ ] `.ln()`
  - [ ] `.log(base=10)`
  - [ ] `.log10()`
  - [ ] `.log2()`
  - [ ] `.exp()`
  - [ ] `.is_nan()`
  - [ ] `.is_inf()`

**7. Universal Visitor Integration**
- [ ] Add `BasicMathExpressionVisitor` to `UniversalBooleanExpressionVisitor` mixins
- [ ] Test visitor composition

**8. Testing**
- [ ] Create `tests/cross_backend/test_math_basic.py`
- [ ] Test all operations across all backends
- [ ] Test edge cases (negative numbers, zero, NaN, infinity)
- [ ] Test with NULL values
- [ ] Verify numerical precision across backends

**9. Documentation**
- [ ] API reference for each operation
- [ ] Usage examples
- [ ] Backend compatibility matrix
- [ ] Update CLAUDE.md

### Success Criteria
- ✅ All 12 math operations work across Polars, Narwhals, Ibis-Polars
- ✅ Consistent numerical results (within tolerance)
- ✅ NULL handling correct
- ✅ 100% test coverage
- ✅ Complete documentation

### Dependencies
- None (can start immediately)

### Risk Assessment
- **Low Risk:** Math operations are straightforward
- **Backend Compatibility:** All backends support these operations
- **Testing:** Need to establish numerical tolerance for floating-point comparisons

---

## Phase 2: Advanced Conditionals

**Duration:** 1-2 weeks
**Priority:** 🔴 HIGH
**Operations:** 5
**Complexity:** Medium

### Objectives
Support complex business logic patterns with multi-branch conditionals and min/max operations.

### Operations to Implement

- [x] `case()` - Multi-branch CASE expression
- [x] `when(condition).then(value)` - CASE WHEN builder (enhance existing)
- [x] `least(*values)` - Minimum of N values
- [x] `greatest(*values)` - Maximum of N values
- [x] `nullif(value, null_value)` - Return NULL if values match

### Implementation Checklist

**1. Node Types**
- [ ] Create `CaseExpressionNode` for multi-branch logic
- [ ] Create `LeastGreatestExpressionNode` for min/max
- [ ] Create `NullIfExpressionNode`

**2. Visitor Mixin**
- [ ] Extend `conditional_mixins/conditional_operators_visitor.py`
- [ ] Implement `visit_case_expression`
- [ ] Implement `visit_least_greatest_expression`
- [ ] Implement `visit_nullif_expression`

**3. ExpressionSystem Interface**
- [ ] Add methods to `base.py`:
  - [ ] `case(cases, results, default)`
  - [ ] `least(*args)`
  - [ ] `greatest(*args)`
  - [ ] `nullif(value, null_value)`

**4. Backend Implementations**
- [ ] Implement in all backend ExpressionSystems
- [ ] Handle variable argument counts for least/greatest

**5. ExpressionBuilder API**
- [ ] Add `ma.case()` function
- [ ] Enhance `ma.when().then().otherwise()` chain
- [ ] Add `ma.least(*exprs)` function
- [ ] Add `ma.greatest(*exprs)` function
- [ ] Add `.nullif(value)` method

**6. Testing**
- [ ] Create `tests/cross_backend/test_conditional_advanced.py`
- [ ] Test multi-branch CASE with 2-10 branches
- [ ] Test nested CASE expressions
- [ ] Test least/greatest with 2-10 arguments
- [ ] Test NULL handling in all operations

**7. Documentation**
- [ ] CASE expression guide
- [ ] Examples for common patterns
- [ ] Migration guide from SQL CASE WHEN

### Success Criteria
- ✅ Multi-branch CASE works correctly
- ✅ Least/greatest handle variable argument counts
- ✅ All operations NULL-safe
- ✅ Works across all backends

### Dependencies
- None

---

## Phase 3: String Enhancements

**Duration:** 1-2 weeks
**Priority:** 🟡 MEDIUM
**Operations:** 8-10
**Complexity:** Low-Medium

### Operations to Implement

#### High Value (3 operations)
- [x] `split(delimiter)` - Split string into array
- [x] `find(substring)` - Find position of substring
- [x] `regex_extract(pattern, group)` - Extract regex match group

#### Medium Value (5 operations)
- [x] `capitalize()` - Capitalize first letter
- [x] `repeat(n)` - Repeat string N times
- [x] `lpad(length, pad_char)` - Left pad to length
- [x] `rpad(length, pad_char)` - Right pad to length
- [x] `join(separator)` - Join array to string

#### Low Value (2 operations)
- [x] `reverse()` - Reverse string
- [x] `str_right(n)` - Last N characters

### Implementation Checklist

**1. Extend String Mixins**
- [ ] Add operations to `string_mixins/`
- [ ] Note: `split()` requires array support

**2. Extend Pattern Mixins**
- [ ] Add `regex_extract` to `pattern_mixins/`
- [ ] Handle capture groups

**3. Testing**
- [ ] Create `tests/cross_backend/test_string_advanced.py`
- [ ] Test edge cases (empty strings, special characters)

**4. Documentation**
- [ ] String operations reference
- [ ] Regex extraction examples

### Success Criteria
- ✅ All string operations work
- ✅ StringSplit returns arrays (cross-backend)
- ✅ Regex extraction handles groups correctly

### Dependencies
- **StringSplit:** Requires array support (may need to wait for Phase 6 on some backends)

---

## Phase 4: Temporal Construction & Parsing

**Duration:** 2-3 weeks
**Priority:** 🟡 MEDIUM-HIGH
**Operations:** 12
**Complexity:** Medium

### Operations to Implement

#### Construction (5 operations)
- [x] `date_from_ymd(year, month, day)` - Build date
- [x] `timestamp_from_ymdhms(y, m, d, h, min, s)` - Build timestamp
- [x] `time_from_hms(hour, minute, second)` - Build time
- [x] `timestamp_from_unix(seconds, unit)` - From Unix timestamp
- [x] `interval_from_integer(value, unit)` - Create interval

#### Parsing (4 operations)
- [x] `string_to_date(format)` - Parse date string
- [x] `string_to_timestamp(format)` - Parse timestamp string
- [x] `string_to_time(format)` - Parse time string
- [x] `strftime(format)` - Format datetime as string

#### Constants (2 operations)
- [x] `now()` - Current timestamp
- [x] `today()` - Current date

#### Other (1 operation)
- [x] `timestamp_bucket(interval, offset)` - Bucket into intervals

### Implementation Checklist

**1. Create Temporal Construction Mixin**
- [ ] Create `temporal_mixins/construction/`
- [ ] Implement all construction operations

**2. Create Temporal Parsing Mixin**
- [ ] Create `temporal_mixins/parsing/`
- [ ] Implement all parsing operations

**3. Backend Implementations**
- [ ] Handle format string differences across backends
- [ ] Document format string compatibility

**4. Testing**
- [ ] Test common date formats (ISO 8601, US, EU)
- [ ] Test edge cases (leap years, DST, timezones)

**5. Documentation**
- [ ] Format string reference
- [ ] Timezone handling guide

### Success Criteria
- ✅ Can construct dates from components
- ✅ Can parse common formats
- ✅ Format strings work across backends
- ✅ Timezone handling correct

### Dependencies
- None

---

## Phase 5: Advanced Math

**Duration:** 2-3 weeks
**Priority:** 🟡 MEDIUM
**Operations:** 14
**Complexity:** Low-Medium

### Operations to Implement

#### Trigonometry (8 operations)
- [x] `sin()` - Sine
- [x] `cos()` - Cosine
- [x] `tan()` - Tangent
- [x] `asin()` - Arcsine
- [x] `acos()` - Arccosine
- [x] `atan()` - Arctangent
- [x] `atan2(x, y)` - Two-argument arctangent
- [x] `cot()` - Cotangent

#### Other Math (4 operations)
- [x] `radians()` - Degrees to radians
- [x] `degrees()` - Radians to degrees
- [x] `clip(lower, upper)` - Clip values to range

#### Constants (2 operations)
- [x] `pi()` - Pi constant
- [x] `e()` - Euler's number constant

### Implementation Checklist

**1. Extend Math Mixins**
- [ ] Create `math_mixins/trigonometry_visitor.py`
- [ ] Implement all trigonometric functions

**2. Constants**
- [ ] Add math constants as literal expressions
- [ ] `ma.pi()` returns literal PI
- [ ] `ma.e()` returns literal E

**3. Testing**
- [ ] Test trigonometric identities (sin²+cos²=1, etc.)
- [ ] Test angle conversions
- [ ] Test constants precision

**4. Documentation**
- [ ] Trigonometry reference
- [ ] Common formulas and identities

### Success Criteria
- ✅ All trigonometric functions work
- ✅ Angle conversion correct
- ✅ Constants available

### Dependencies
- **Phase 1** (basic math)

---

## Phase 6: Array Operations

**Duration:** 4-6 weeks
**Priority:** 🔴 HIGH (with caveats)
**Operations:** 18
**Complexity:** High

### Operations to Implement

#### Critical (5 operations)
- [x] `array_length()` - Get array size
- [x] `array_index(i)` - Access element by index
- [x] `array_contains(value)` - Check membership
- [x] `array_slice(start, stop)` - Extract sub-array
- [x] `array(*values)` - Construct array

#### High Value (7 operations)
- [x] `array_concat(other)` - Concatenate arrays
- [x] `array_union(other)` - Set union
- [x] `array_intersect(other)` - Set intersection
- [x] `array_distinct()` - Remove duplicates
- [x] `array_sum()` - Sum of elements
- [x] `array_mean()` - Mean of elements
- [x] `array_min()` / `array_max()` - Min/max of elements

#### Medium Value (6 operations)
- [x] `array_sort()` - Sort array
- [x] `array_remove(value)` - Remove element
- [x] `array_flatten()` - Flatten nested arrays
- [x] `array_any()` - Any element true
- [x] `array_all()` - All elements true

### Implementation Checklist

**1. Backend Capability System**
- [ ] Create `backends/capabilities.py`
- [ ] Define `BackendCapabilities` class
- [ ] Add `supports_arrays` flag
- [ ] Implement capability checking in factory

**2. Array Mixins**
- [ ] Create `array_mixins/` directory
- [ ] Implement array operation visitors
- [ ] Add capability checks

**3. Backend Implementations**
- [ ] Implement in PolarsExpressionSystem (full support)
- [ ] Implement in NarwhalsExpressionSystem
- [ ] Implement in IbisExpressionSystem
- [ ] Document unsupported backends

**4. Testing**
- [ ] Create `tests/cross_backend/test_array_operations.py`
- [ ] Mark tests for backends without array support
- [ ] Test nested arrays

**5. Documentation**
- [ ] Array operations guide
- [ ] Backend compatibility matrix
- [ ] Migration from Polars/Ibis

### Success Criteria
- ✅ All array operations work on Polars
- ✅ Graceful errors for unsupported backends
- ✅ Clear compatibility documentation

### Dependencies
- None (but affects StringSplit from Phase 3)

### Risk Assessment
- **High Complexity:** Backend support varies significantly
- **Testing Challenge:** Need to handle unsupported backends gracefully
- **Documentation Critical:** Users need clear compatibility information

---

## Phase 7: Specialized Operations

**Duration:** 1-2 weeks
**Priority:** 🟢 LOW
**Operations:** 10-12
**Complexity:** Low

### Operations to Implement

#### Bitwise (6 operations)
- [x] `bitwise_and(other)` - Bitwise AND
- [x] `bitwise_or(other)` - Bitwise OR
- [x] `bitwise_xor(other)` - Bitwise XOR
- [x] `bitwise_not()` - Bitwise NOT
- [x] `left_shift(n)` - Left shift
- [x] `right_shift(n)` - Right shift

#### Comparison Enhancements (2 operations)
- [x] `between(lower, upper)` - Range check
- [x] `identical_to(other)` - Null-safe equality

#### Type Operations (1 operation)
- [x] `try_cast(dtype)` - Safe cast with null on failure

#### Arithmetic (1 operation)
- [x] `negate()` - Unary negation (-x)

#### Temporal Extractions (3 operations)
- [x] `iso_year()` - ISO 8601 year
- [x] `day_of_year()` - Day of year (1-366)
- [x] `epoch_seconds()` - Unix timestamp

### Implementation Checklist

**1. Bitwise Mixins**
- [ ] Create `bitwise_mixins/`
- [ ] Implement all bitwise operations

**2. Extend Existing Mixins**
- [ ] Add remaining operations to appropriate mixins

**3. Testing**
- [ ] Test bitwise operations
- [ ] Test edge cases

**4. Documentation**
- [ ] Complete operation reference
- [ ] Final compatibility matrix

### Success Criteria
- ✅ All operations implemented
- ✅ 80%+ Ibis-Polars coverage achieved
- ✅ Complete documentation

### Dependencies
- None

---

## Phase 8: Window/Analytic Functions

**Duration:** 3-5 weeks
**Priority:** 🔴 CRITICAL
**Operations:** 17
**Complexity:** High

### Objectives
Enable window/analytic functions for ranking, time series analysis, and sequential comparisons.

### Operations to Implement

#### Ranking Functions (6 operations)
- [x] `rank()` - Rank with gaps (1, 2, 2, 4)
- [x] `dense_rank()` - Rank without gaps (1, 2, 2, 3)
- [x] `row_number()` - Sequential row number (1, 2, 3, 4)
- [x] `percent_rank()` - Percentile rank (0.0 to 1.0)
- [x] `cume_dist()` - Cumulative distribution
- [x] `ntile(n)` - Divide into n buckets

#### Offset/Position Functions (5 operations)
- [x] `lag(offset, default)` - Previous row value
- [x] `lead(offset, default)` - Next row value
- [x] `nth_value(n)` - Nth value in window
- [x] `first_value()` - First value in window
- [x] `last_value()` - Last value in window

#### Cumulative Functions (6 operations)
- [x] `cumsum()` - Cumulative sum
- [x] `cummean()` - Cumulative mean
- [x] `cummin()` - Cumulative minimum
- [x] `cummax()` - Cumulative maximum
- [x] `cumany()` - Cumulative any (boolean)
- [x] `cumall()` - Cumulative all (boolean)

#### Window Specification (Infrastructure)
- [x] `.over(group_by, order_by)` - Window specification
- [x] `ROWS BETWEEN` - Row-based frame
- [x] `RANGE BETWEEN` - Range-based frame

### Implementation Checklist

**1. Window Specification System**
- [ ] Create `core/window/` directory
- [ ] Implement `WindowSpecification` class
- [ ] Implement `WindowFrame` class (ROWS/RANGE)
- [ ] Implement `WindowBoundary` (PRECEDING/FOLLOWING/CURRENT ROW)

**2. Window Node Types**
- [ ] Create `core/expression_nodes/window_expression_nodes.py`
- [ ] Implement `WindowFunctionNode` base class
- [ ] Implement `RankingFunctionNode`
- [ ] Implement `OffsetFunctionNode`
- [ ] Implement `CumulativeFunctionNode`

**3. Window Visitor Mixin**
- [ ] Create `core/expression_visitors/window_mixins/`
- [ ] Implement `RankingFunctionsVisitor`
- [ ] Implement `OffsetFunctionsVisitor`
- [ ] Implement `CumulativeFunctionsVisitor`

**4. ExpressionSystem Interface**
- [ ] Extend `base.py` with window methods:
  - [ ] `rank()`
  - [ ] `dense_rank()`
  - [ ] `row_number()`
  - [ ] `percent_rank()`
  - [ ] `cume_dist()`
  - [ ] `ntile(buckets)`
  - [ ] `lag(offset, default)`
  - [ ] `lead(offset, default)`
  - [ ] `nth_value(n)`
  - [ ] `first_value()`
  - [ ] `last_value()`
  - [ ] `cumsum()`
  - [ ] `cummean()`
  - [ ] `cummin()`
  - [ ] `cummax()`
  - [ ] `over(group_by, order_by, frame)` - Apply window specification

**5. Backend Implementations**
- [ ] Implement all methods in `PolarsExpressionSystem`
- [ ] Implement all methods in `NarwhalsExpressionSystem`
- [ ] Implement all methods in `IbisExpressionSystem`
- [ ] Handle window frame translation for each backend

**6. ExpressionBuilder API**
- [ ] Add window function methods:
  - [ ] `.rank()`
  - [ ] `.dense_rank()`
  - [ ] `.row_number()`
  - [ ] `.percent_rank()`
  - [ ] `.cume_dist()`
  - [ ] `.ntile(n)`
  - [ ] `.lag(offset, default)`
  - [ ] `.lead(offset, default)`
  - [ ] `.nth_value(n)`
  - [ ] `.first_value()`
  - [ ] `.last_value()`
  - [ ] `.cumsum()`
  - [ ] `.cummean()`
  - [ ] `.cummin()`
  - [ ] `.cummax()`
- [ ] Add `.over()` method for window specification
- [ ] Add `ma.window()` helper for creating window specs

**7. Universal Visitor Integration**
- [ ] Add window mixins to `UniversalBooleanExpressionVisitor`
- [ ] Test visitor composition with window functions

**8. Testing**
- [ ] Create `tests/cross_backend/test_window_ranking.py`
- [ ] Create `tests/cross_backend/test_window_offset.py`
- [ ] Create `tests/cross_backend/test_window_cumulative.py`
- [ ] Test all ranking functions
- [ ] Test offset functions with various offsets and defaults
- [ ] Test cumulative functions
- [ ] Test window frame specifications (ROWS/RANGE)
- [ ] Test PARTITION BY and ORDER BY
- [ ] Test edge cases (empty windows, single row, NULL handling)

**9. Documentation**
- [ ] Window functions guide
- [ ] Window specification reference
- [ ] Frame specification reference
- [ ] Usage examples for each function
- [ ] Time series analysis guide
- [ ] Backend compatibility notes

### Success Criteria
- ✅ All 17 window operations work across Polars, Narwhals, Ibis-Polars
- ✅ Window specification system (PARTITION BY, ORDER BY) works
- ✅ Frame specifications (ROWS/RANGE BETWEEN) work
- ✅ Cumulative functions work as shortcuts for common windows
- ✅ NULL handling correct
- ✅ 100% test coverage
- ✅ Comprehensive documentation

### Dependencies
- None (can be implemented independently)

### Complexity Considerations

**Why High Complexity:**
1. **New infrastructure:** Requires window specification system
2. **Frame semantics:** ROWS vs RANGE have subtle differences
3. **Ordering requirements:** Many window functions require ORDER BY
4. **Backend differences:** Window syntax varies across backends
5. **Integration complexity:** Window functions can wrap both analytic and aggregation functions

**Architecture Decisions:**

1. **Window as wrapper:**
   ```python
   # Window functions wrap other expressions
   col("sales").sum().over(group_by="category", order_by="date")

   # Or use dedicated analytic functions
   ma.rank().over(group_by="category", order_by="sales")
   ```

2. **Cumulative as convenience:**
   ```python
   # Cumulative functions are shortcuts
   col("sales").cumsum()

   # Equivalent to:
   col("sales").sum().over(
       order_by="date",
       rows=(None, 0)  # Unbounded preceding to current row
   )
   ```

3. **Frame specification:**
   ```python
   # ROWS-based frame (physical rows)
   .over(rows=(-6, 0))  # Last 7 rows including current

   # RANGE-based frame (logical range)
   .over(range=("-7 days", "0 days"), order_by="date")
   ```

### Use Cases

**1. Ranking - Top N per Group:**
```python
# Top 3 products per category by sales
products.filter(
    ma.rank().over(
        group_by="category",
        order_by=col("sales").desc()
    ) <= 3
)
```

**2. Time Series - Moving Average:**
```python
# 7-day moving average
col("sales").mean().over(
    rows=(-6, 0),
    order_by="date"
)
```

**3. Sequential Comparison - Period over Period:**
```python
# Compare to previous month
ma.with_columns(
    df,
    prev_sales=col("sales").lag(1).over(order_by="month"),
    change=col("sales") - col("sales").lag(1).over(order_by="month")
)
```

**4. Cumulative - Running Total:**
```python
# Running total by customer
col("amount").cumsum().over(
    group_by="customer_id",
    order_by="transaction_date"
)

# Or simpler:
col("amount").cumsum()  # Uses implicit ordering
```

**5. Percentile - Quartiles:**
```python
# Assign quartile buckets
ma.ntile(4).over(order_by="income")
```

### Backend Compatibility

| Backend | Window Support | Notes |
|---------|----------------|-------|
| **Polars** | ✅ Excellent | Full window function support |
| **Narwhals** | ✅ Good | Depends on underlying backend |
| **Ibis-Polars** | ✅ Excellent | Full Ibis window API |
| **Ibis-DuckDB** | ✅ Excellent | Full SQL window support |
| **Ibis-SQLite** | ⚠️ Limited | Basic windows, limited frame specs |
| **Pandas** | ⚠️ Moderate | Via rolling/expanding/groupby |

### Risk Assessment

- **High Complexity:** Window specification system is non-trivial
- **Backend Variability:** Different backends have different capabilities
- **Testing Challenge:** Need comprehensive window frame tests
- **Documentation Critical:** Window functions have subtle semantics

---

## Phase 9: ML/Statistical Metrics

**Duration:** 4-7 weeks (9A: 1-2 weeks, 9B: 1-2 weeks, 9C: 2-3 weeks)
**Priority:** 🟡 HIGH (9A, 9B) / 🟢 MEDIUM (9C)
**Operations:** 10-12
**Complexity:** Medium-High

### Objectives
Enable machine learning model evaluation and credit risk analytics through dataframe-based metric calculations.

### Background

Machine learning metrics ARE dataframe operations when predictions and actuals are columns in a dataframe. This phase implements metrics that can be calculated using:
- **Aggregations only** (Phase 9A) - Can implement immediately
- **Window functions** (Phase 9B) - Requires Phase 8 completion
- **Discretization** (Phase 9C) - Optional, for advanced use cases

**Reference Implementation:** User's Django-based credit risk metrics system (2014-2016)
- **What to emulate:** Metric calculations and formulas
- **What to avoid:** Database coupling, dimension explosion, SQL string building

**Target:** ~460 lines of clean code (vs. 4,679 lines in legacy implementation)

### Sub-Phases

#### Phase 9A: Classification Metrics (No Window Functions)

**Duration:** 1-2 weeks
**Priority:** 🟡 HIGH
**Operations:** 4-5
**Complexity:** Low-Medium
**Dependencies:** None (aggregations only)

**Operations:**
- [x] `precision(actual, prediction)` - Proportion of true positives
- [x] `recall(actual, prediction)` - Proportion of actual positives found
- [x] `f1_score(actual, prediction)` - Harmonic mean of precision and recall
- [x] `accuracy(actual, prediction)` - Proportion of correct predictions
- [x] `confusion_matrix(actual, prediction)` - TP, FP, TN, FN counts

**Implementation:**
```python
# Given binary actual and prediction columns (0/1)
tp = (t.actual * t.prediction).sum()
fp = t.prediction.sum() - tp
fn = t.actual.sum() - tp
tn = t.count() - tp - fp - fn

precision = tp / t.prediction.sum()
recall = tp / t.actual.sum()
f1_score = 2 * tp / (t.actual.sum() + t.prediction.sum())
accuracy = (t.actual == t.prediction).mean()
```

**API Design:**
```python
# As expression methods
from mountainash_expressions import ma

metrics = ma.evaluate_classification(
    df,
    actual=col("actual"),
    prediction=col("pred")
)
# Returns: {"precision": 0.85, "recall": 0.78, "f1": 0.81, "accuracy": 0.82}

# Or individual metrics
precision = ma.precision(col("actual"), col("pred")).eval()(df)
```

#### Phase 9B: Ranking Metrics (Requires Window Functions)

**Duration:** 1-2 weeks
**Priority:** 🟡 HIGH
**Operations:** 2-3
**Complexity:** Medium
**Dependencies:** Phase 8 (Window Functions)

**Operations:**
- [x] `roc_auc(actual, prediction_proba)` - Area Under ROC Curve
- [x] `gini(actual, prediction_proba)` - Gini coefficient (2*AUC - 1)
- [x] `log_loss(actual, prediction_proba)` - Logarithmic loss

**Implementation:**
```python
# ROC-AUC requires ranking by prediction probability
# Then calculating cumulative sums over ranked data

# Pseudo-code using window functions
ranked = df.with_columns(
    rank=col("pred_proba").rank().over(order_by=col("pred_proba").desc())
)

# Cumulative sums of actual values (good/bad)
cusum_good = col("actual").cumsum().over(order_by=col("pred_proba").desc())
cusum_bad = (1 - col("actual")).cumsum().over(order_by=col("pred_proba").desc())

# Gini calculation from cumulative sums
# (See User-Metrics-Implementation-Analysis.md for full formula)
```

**API Design:**
```python
# Simplified API that handles window logic internally
roc_auc = ma.roc_auc(
    actual=col("actual"),
    prediction_proba=col("pred_proba")
).eval()(df)

gini = ma.gini(
    actual=col("actual"),
    prediction_proba=col("pred_proba")
).eval()(df)
```

#### Phase 9C: Credit Risk Metrics (Optional)

**Duration:** 2-3 weeks
**Priority:** 🟢 MEDIUM
**Operations:** 3-4
**Complexity:** Medium-High
**Dependencies:** Optional discretization/binning

**Operations:**
- [x] `information_value(actual, feature, bins)` - Feature selection metric (IV)
- [x] `weight_of_evidence(actual, feature, bins)` - WoE transformation
- [x] `population_stability_index(baseline, analysis, bins)` - Model drift (PSI)
- [x] `marginal_iv(actual, feature, bins, time)` - Change in IV over time (MIV)

**Formulas:**
```python
# Weight of Evidence (per bin)
WoE = ln(pct_good / pct_bad)

# Information Value (per feature)
IV = sum((pct_good - pct_bad) * WoE)

# Population Stability Index
PSI = sum((pct_analysis - pct_base) * ln(pct_analysis / pct_base))
```

**API Design:**
```python
# With auto-binning (stateless)
iv = ma.information_value(
    actual=col("target"),
    feature=col("income"),
    bins=10,  # Auto-create 10 quantile bins
    method="quantile"
).eval()(df)

# Or with explicit bin edges
iv = ma.information_value(
    actual=col("target"),
    feature=col("income"),
    bin_edges=[0, 30000, 50000, 75000, 100000, 999999]
).eval()(df)

# WoE transformation (returns new column)
df_woe = ma.with_columns(
    df,
    income_woe=ma.weight_of_evidence(
        actual=col("target"),
        feature=col("income"),
        bins=10
    )
)
```

**Discretization/Binning:**
- **Equal population mass** (quantiles) - Default
- **Equal width** (histogram) - Optional
- **Special value handling** - NaN, inf, etc.
- **Overflow bins** - Handle values outside range

**Implementation Note:**
Credit risk metrics require grouping continuous values into discrete bins, then calculating statistics per bin. Two approaches:

1. **Stateless (Recommended):** Auto-bin on-the-fly, no persistence
2. **Stateful (Legacy):** Pre-define bins, store in database (avoid this)

### Implementation Checklist

#### Phase 9A Checklist

**1. Create Metrics Module**
- [ ] Create `core/metrics/` directory
- [ ] Create `classification_metrics_nodes.py`
- [ ] Implement `PrecisionNode`, `RecallNode`, `F1ScoreNode`, `AccuracyNode`

**2. Visitor Mixin**
- [ ] Create `core/expression_visitors/metrics_mixins/`
- [ ] Implement `ClassificationMetricsVisitor`
- [ ] Add visitor methods for each metric

**3. ExpressionSystem Interface**
- [ ] Extend `base.py` with metric methods:
  - [ ] `precision(actual, prediction)`
  - [ ] `recall(actual, prediction)`
  - [ ] `f1_score(actual, prediction)`
  - [ ] `accuracy(actual, prediction)`

**4. Backend Implementations**
- [ ] Implement in `PolarsExpressionSystem`
- [ ] Implement in `NarwhalsExpressionSystem`
- [ ] Implement in `IbisExpressionSystem`

**5. API Layer**
- [ ] Add `ma.precision()` function
- [ ] Add `ma.recall()` function
- [ ] Add `ma.f1_score()` function
- [ ] Add `ma.accuracy()` function
- [ ] Add `ma.evaluate_classification()` helper (returns dict of all metrics)

**6. Testing**
- [ ] Create `tests/cross_backend/test_classification_metrics.py`
- [ ] Test with perfect predictions (all correct)
- [ ] Test with random predictions
- [ ] Test with imbalanced classes
- [ ] Test edge cases (all positive, all negative)
- [ ] Test NULL handling

**7. Documentation**
- [ ] Classification metrics guide
- [ ] Example use cases
- [ ] Comparison to sklearn.metrics

#### Phase 9B Checklist

**1. Extend Metrics Module**
- [ ] Create `ranking_metrics_nodes.py`
- [ ] Implement `RocAucNode`, `GiniNode`, `LogLossNode`

**2. Window Function Integration**
- [ ] Implement ranking using `.rank().over()`
- [ ] Implement cumulative sums using `.cumsum().over()`
- [ ] Handle ties in ranking

**3. ExpressionSystem Interface**
- [ ] Add methods:
  - [ ] `roc_auc(actual, prediction_proba)`
  - [ ] `gini(actual, prediction_proba)`
  - [ ] `log_loss(actual, prediction_proba)`

**4. Backend Implementations**
- [ ] Implement in all backends
- [ ] Optimize window function usage

**5. API Layer**
- [ ] Add `ma.roc_auc()` function
- [ ] Add `ma.gini()` function
- [ ] Add `ma.log_loss()` function

**6. Testing**
- [ ] Create `tests/cross_backend/test_ranking_metrics.py`
- [ ] Test with known AUC values
- [ ] Verify Gini = 2*AUC - 1
- [ ] Test edge cases (all same prediction, perfect separation)

**7. Documentation**
- [ ] Ranking metrics guide
- [ ] ROC curve explanation
- [ ] Gini coefficient interpretation

#### Phase 9C Checklist

**1. Discretization System**
- [ ] Create `core/discretization/` directory
- [ ] Implement `Discretizer` base class
- [ ] Implement `QuantileDiscretizer`
- [ ] Implement `HistogramDiscretizer`
- [ ] Handle special values (NaN, inf)

**2. Credit Risk Metrics**
- [ ] Create `credit_risk_metrics_nodes.py`
- [ ] Implement `InformationValueNode`
- [ ] Implement `WeightOfEvidenceNode`
- [ ] Implement `PopulationStabilityIndexNode`
- [ ] Implement `MarginalIVNode`

**3. ExpressionSystem Interface**
- [ ] Add methods:
  - [ ] `information_value(actual, feature, bins, method)`
  - [ ] `weight_of_evidence(actual, feature, bins, method)`
  - [ ] `psi(baseline, analysis, bins)`
  - [ ] `marginal_iv(actual, feature, bins, time_col)`

**4. Backend Implementations**
- [ ] Implement in all backends
- [ ] Handle binning efficiently

**5. API Layer**
- [ ] Add `ma.information_value()` function
- [ ] Add `ma.weight_of_evidence()` function
- [ ] Add `ma.psi()` function
- [ ] Add `ma.marginal_iv()` function

**6. Testing**
- [ ] Create `tests/cross_backend/test_credit_risk_metrics.py`
- [ ] Test IV calculation with known values
- [ ] Test WoE transformation
- [ ] Test PSI for drift detection
- [ ] Test different binning strategies

**7. Documentation**
- [ ] Credit risk metrics guide
- [ ] Binning strategies reference
- [ ] Model monitoring with PSI
- [ ] Feature selection with IV

### Success Criteria

#### Phase 9A
- ✅ All classification metrics work correctly
- ✅ Results match sklearn.metrics (within tolerance)
- ✅ Handle edge cases gracefully
- ✅ Work across all backends

#### Phase 9B
- ✅ ROC-AUC calculation correct
- ✅ Gini = 2*AUC - 1 verified
- ✅ Window function integration seamless
- ✅ Performance acceptable for large datasets

#### Phase 9C
- ✅ Binning strategies work correctly
- ✅ IV/WoE calculations match reference implementation
- ✅ PSI detects distribution drift
- ✅ Stateless evaluation (no database required)
- ✅ 10x code reduction vs. legacy implementation

### Dependencies

- **Phase 9A:** None (can start immediately)
- **Phase 9B:** Requires Phase 8 (Window Functions)
- **Phase 9C:** Optional, can be implemented independently

### Architecture Principles

#### DO (Lessons from Research)
1. **Stateless evaluation** - No database persistence required
2. **Expression compilation** - Not SQL string building
3. **Optional auto-binning** - Not required pre-configuration
4. **Work with dataframes** - Not Django ORM coupling

#### DON'T (Anti-patterns from Legacy)
1. **Database-first design** - Storing bins in database
2. **Dimension explosion** - 14 objects to track one metric
3. **SQL string building** - 1,041 lines generating CASE statements
4. **Required setup** - Pre-configuring bins before use

### Code Size Targets

| Component | Legacy (Lines) | Target (Lines) | Reduction |
|-----------|----------------|----------------|-----------|
| **Discretization** | 1,321 | 120 | 91% |
| **Metrics** | 1,321 | 200 | 85% |
| **Query Builders** | 1,537 | 140 | 91% |
| **TOTAL** | 4,679 | 460 | **90%** |

### Use Cases

#### 1. Model Evaluation (Phase 9A)
```python
from mountainash_expressions import ma, col

# Evaluate binary classifier
metrics = ma.evaluate_classification(
    df,
    actual=col("is_fraud"),
    prediction=col("pred_fraud")
)
print(f"Precision: {metrics['precision']:.2%}")
print(f"Recall: {metrics['recall']:.2%}")
print(f"F1 Score: {metrics['f1']:.2%}")
```

#### 2. Model Comparison (Phase 9B)
```python
# Compare two models using Gini
model1_gini = ma.gini(
    actual=col("actual"),
    prediction_proba=col("model1_proba")
).eval()(df)

model2_gini = ma.gini(
    actual=col("actual"),
    prediction_proba=col("model2_proba")
).eval()(df)

print(f"Model 1 Gini: {model1_gini:.3f}")
print(f"Model 2 Gini: {model2_gini:.3f}")
```

#### 3. Feature Selection (Phase 9C)
```python
# Calculate IV for feature selection
iv_age = ma.information_value(
    actual=col("default"),
    feature=col("age"),
    bins=10
).eval()(df)

iv_income = ma.information_value(
    actual=col("default"),
    feature=col("income"),
    bins=10
).eval()(df)

# IV > 0.3 = strong predictive power
print(f"Age IV: {iv_age:.3f}")
print(f"Income IV: {iv_income:.3f}")
```

#### 4. Model Drift Detection (Phase 9C)
```python
# Check for distribution drift
psi = ma.psi(
    baseline=col("score_baseline"),
    analysis=col("score_current"),
    bins=10
).eval()(df)

# PSI > 0.2 indicates significant drift
if psi > 0.2:
    print(f"WARNING: Significant drift detected (PSI={psi:.3f})")
```

### Backend Compatibility

| Backend | Phase 9A | Phase 9B | Phase 9C | Notes |
|---------|----------|----------|----------|-------|
| **Polars** | ✅ Excellent | ✅ Excellent | ✅ Excellent | Full support |
| **Narwhals** | ✅ Good | ✅ Good | ✅ Good | Depends on backend |
| **Ibis-Polars** | ✅ Excellent | ✅ Excellent | ✅ Excellent | Full support |
| **Ibis-DuckDB** | ✅ Excellent | ✅ Excellent | ✅ Good | Aggregations + windows |
| **Pandas** | ✅ Good | ⚠️ Moderate | ⚠️ Moderate | Window functions limited |

### Risk Assessment

**Phase 9A (Low Risk):**
- Simple aggregations
- Well-defined formulas
- sklearn.metrics as reference

**Phase 9B (Medium Risk):**
- Depends on Phase 8 completion
- Window function performance critical
- Tie handling in ranking

**Phase 9C (Medium-High Risk):**
- Discretization complexity
- Edge case handling (special values)
- Need to avoid legacy anti-patterns

### Reference Documentation

- **ML Research:** `/docs/ML-Statistical-Functions-Research.md`
- **User Implementation:** `/docs/User-Metrics-Implementation-Analysis.md`
- **Framework Analysis:** `/docs/Framework-Architecture-Analysis.md`
- **Ibis Blog:** https://ibis-project.org/posts/classification-metrics-on-the-backend/

---

## Summary Timeline

| Phase | Duration | Operations | Cumulative Coverage |
|-------|----------|------------|---------------------|
| **Current** | - | 65 | ~38% |
| **Phase 1** | 2-3 weeks | +12 | ~45% |
| **Phase 2** | 1-2 weeks | +5 | ~48% |
| **Phase 3** | 1-2 weeks | +10 | ~54% |
| **Phase 4** | 2-3 weeks | +12 | ~61% |
| **Phase 5** | 2-3 weeks | +14 | ~69% |
| **Phase 6** | 4-6 weeks | +18 | ~80% |
| **Phase 7** | 1-2 weeks | +12 | ~87% |
| **Phase 8** | 3-5 weeks | +17 | ~97% |
| **Phase 9A** | 1-2 weeks | +5 | ~100% |
| **Phase 9B** | 1-2 weeks | +3 | ~102% |
| **Phase 9C** | 2-3 weeks | +4 | ~105% (optional) |
| **TOTAL** | **21-34 weeks** | **+117** | **~105%** |

**Note:** Phase 9 adds ML/statistical metrics that go beyond base Ibis-Polars expression parity (100%+).

---

## Resource Requirements

### Development Time (Including Phase 9)
- **Minimum:** 21 weeks (optimistic, single developer)
- **Expected:** 27 weeks (realistic, single developer)
- **Maximum:** 34 weeks (conservative, single developer)

**Without Phase 9 (80% coverage):**
- **Minimum:** 17 weeks
- **Expected:** 22 weeks
- **Maximum:** 27 weeks

### Skills Required
- Python proficiency
- Understanding of DataFrame operations
- Cross-backend testing experience
- Math/statistics knowledge (Phase 1, 5)
- Array operations knowledge (Phase 6)
- Window functions/SQL analytic knowledge (Phase 8)
- ML metrics and model evaluation (Phase 9A, 9B)
- Credit risk analytics (Phase 9C, optional)

### Testing Infrastructure
- Cross-backend test fixtures (✅ already exists)
- Numerical tolerance utilities (needs to be added)
- Backend capability testing (needs to be added)

---

## Risk Management

### High Risk Items

**1. Array Operations (Phase 6)**
- **Risk:** Backend compatibility issues
- **Mitigation:**
  - Implement capability checking
  - Focus on Polars first
  - Clear documentation of limitations

**2. Numerical Precision (Phases 1, 5)**
- **Risk:** Floating-point precision differences
- **Mitigation:**
  - Establish tolerance thresholds
  - Document known differences
  - Test edge cases thoroughly

**3. Temporal Parsing (Phase 4)**
- **Risk:** Format string differences across backends
- **Mitigation:**
  - Document format string compatibility
  - Test common formats extensively
  - Provide format conversion guide

### Medium Risk Items

**1. Performance**
- **Risk:** Expression compilation overhead
- **Mitigation:**
  - Profile critical paths
  - Optimize hot paths
  - Maintain lazy evaluation

**2. Documentation**
- **Risk:** Incomplete or outdated docs
- **Mitigation:**
  - Document as you code
  - Include examples in docstrings
  - Maintain compatibility matrix

---

## Success Metrics

### Coverage Metrics
- **Target:** 80%+ of Ibis-Polars expression operations
- **Current:** ~40%
- **Increment per Phase:** 3-10% increase

### Quality Metrics
- **Test Coverage:** 100% for new operations
- **Cross-Backend Success:** 100% on Polars, Narwhals, Ibis-Polars
- **Documentation:** Every operation documented with examples

### Performance Metrics
- **Expression Build Time:** <1ms for simple expressions
- **Compilation Time:** <10ms for complex expressions
- **No Regression:** Existing operations maintain performance

---

## Next Steps

### Immediate (This Week)
1. Review and approve this roadmap
2. Set up project tracking (GitHub issues/projects)
3. Begin Phase 1 implementation

### Short-Term (Next 4 Weeks)
1. Complete Phase 1 (Essential Math)
2. Begin Phase 2 (Advanced Conditionals)

### Medium-Term (Next 3 Months)
1. Complete Phases 2-4
2. Reach ~65% coverage
3. Gather user feedback

### Long-Term (Next 6 Months)
1. Complete all phases
2. Achieve 80%+ coverage
3. Production-ready release

---

## Appendix: Quick Reference

### Phase Priorities

🔴 **CRITICAL** - Immediate business value, blocking work
🟡 **HIGH** - Significant value, should be done soon
🟠 **MEDIUM** - Nice to have, improves capabilities
🟢 **LOW** - Specialized use cases, can wait

### Coverage Calculation

```
Coverage % = (mountainash operations / Ibis-Polars operations) * 100
Current: 65 / 153 ≈ 42%
Target: 130 / 153 ≈ 85%
```

### Phase Dependencies

```
Phase 1 (Math Basic) → Phase 5 (Math Advanced)
Phase 6 (Arrays) → Phase 3 (StringSplit)
Phase 8 (Window Functions) → Phase 9B (Ranking Metrics)
Phase 9A (Classification Metrics) - Independent
Phase 9C (Credit Risk Metrics) - Independent (optional)
All other phases independent
```

---

**Document Status:** DRAFT - Pending Approval
**Owner:** mountainash-expressions maintainers
**Next Review:** After Phase 1 completion
**Last Updated:** 2025-01-09
