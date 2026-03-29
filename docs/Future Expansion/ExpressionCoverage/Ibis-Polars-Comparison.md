# Ibis-Polars vs mountainash-expressions: Comprehensive Operation Comparison

**Date:** 2025-01-09
**Ibis Version:** Local fork at `/home/nathanielramm/git/ibis`
**mountainash-expressions Version:** Current main branch
**Analysis Source:** `/home/nathanielramm/git/ibis/ibis/backends/polars/compiler.py`

## Executive Summary

This document provides a comprehensive comparison between Ibis-Polars backend expression operations and mountainash-expressions capabilities, identifying gaps, overlaps, and opportunities for enhancement.

### Quick Stats

- **Ibis-Polars Operations Cataloged:** ~170+ distinct expression operations
- **mountainash-expressions Operations:** ~65+ operations across 7 categories
- **Estimated Coverage:** ~38-42% of Ibis-Polars expression capabilities
- **Total Gap:** 103 operations
- **Critical Gaps:** Math functions (26), Array operations (18), Window functions (17)

### Coverage Summary

| Status | Coverage | Categories |
|--------|----------|------------|
| ✅ **Excellent (100%+)** | 100%+ | Boolean/Logical, Basic String, Pattern/Regex |
| ✅ **Good (75-99%)** | 75-99% | Arithmetic, Comparison, Null Handling, Temporal Arithmetic |
| ⚠️ **Moderate (40-74%)** | 40-74% | Temporal Extraction, Collection/Set, Type Ops |
| ❌ **Poor (<40%)** | <40% | Conditional, Advanced String |
| ❌ **Missing (0%)** | 0% | **Math, Arrays, Bitwise, Temporal Construction/Parsing** |

---

## Table of Contents

1. [Operation Category Analysis](#operation-category-analysis)
2. [Critical Gaps](#critical-gaps)
3. [mountainash-expressions Unique Features](#mountainash-expressions-unique-features)
4. [Implementation Roadmap](#implementation-roadmap)
5. [Backend Compatibility Considerations](#backend-compatibility-considerations)
6. [Detailed Operation Tables](#detailed-operation-tables)

---

## Operation Category Analysis

### 1. Comparison Operations ✅ **75% Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.Equals` | ✅ | ✅ | `boolean_mixins/comparison/_B_eq` |
| `ops.NotEquals` | ✅ | ✅ | `boolean_mixins/comparison/_B_ne` |
| `ops.Greater` | ✅ | ✅ | `boolean_mixins/comparison/_B_gt` |
| `ops.GreaterEqual` | ✅ | ✅ | `boolean_mixins/comparison/_B_ge` |
| `ops.Less` | ✅ | ✅ | `boolean_mixins/comparison/_B_lt` |
| `ops.LessEqual` | ✅ | ✅ | `boolean_mixins/comparison/_B_le` |
| `ops.Between` | ✅ | ❌ | **GAP: Range check** |
| `ops.IdenticalTo` | ✅ | ❌ | **GAP: Null-safe equality** |

**Assessment:** Strong foundation, minor gaps that would be nice to have.

---

### 2. Arithmetic Operations ✅ **87.5% Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.Add` | ✅ | ✅ | `arithmetic_mixins/_add` |
| `ops.Subtract` | ✅ | ✅ | `arithmetic_mixins/_subtract` |
| `ops.Multiply` | ✅ | ✅ | `arithmetic_mixins/_multiply` |
| `ops.Divide` | ✅ | ✅ | `arithmetic_mixins/_divide` |
| `ops.Modulus` | ✅ | ✅ | `arithmetic_mixins/_modulo` |
| `ops.Power` | ✅ | ✅ | `arithmetic_mixins/_power` |
| `ops.FloorDivide` | ✅ | ✅ | `arithmetic_mixins/_floor_divide` |
| `ops.Negate` | ✅ | ❌ | **GAP: Unary negation** |

**Assessment:** Excellent coverage of binary operators, missing unary negation.

---

### 3. Boolean/Logical Operations ✅ **100%+ Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.And` | ✅ | ✅ | `boolean_mixins/operators/_B_and` |
| `ops.Or` | ✅ | ✅ | `boolean_mixins/operators/_B_or` |
| `ops.Not` | ✅ | ✅ | `boolean_mixins/unary/_B_negate` |
| `ops.Xor` | ✅ | ✅ | `boolean_mixins/operators/_B_xor_exclusive` |
| XOR Parity | ❌ | ✅ | **UNIQUE:** `_B_xor_parity` |

**Assessment:** Full coverage plus unique extensions. Excellent.

---

### 4. Null Handling Operations ✅ **80% Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.IsNull` | ✅ | ✅ | `boolean_mixins/unary/_B_is_null` |
| `ops.NotNull` | ✅ | ✅ | `boolean_mixins/unary/_B_not_null` |
| `ops.Coalesce` | ✅ | ✅ | `conditional_mixins/_conditional_coalesce` |
| `ops.FillNull` | ✅ | ✅ | `conditional_mixins/_conditional_fill_null` |
| `ops.NullIf` | ✅ | ❌ | **GAP: Returns null if condition met** |

**Assessment:** Strong coverage, missing one operation.

---

### 5. Conditional Operations ⚠️ **20% Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.IfElse` | ✅ | ✅ | `conditional_mixins/_conditional_when` |
| `ops.SimpleCase` | ✅ | ❌ | **GAP: CASE value WHEN x THEN y...** |
| `ops.SearchedCase` | ✅ | ❌ | **GAP: CASE WHEN x THEN y...** |
| `ops.Least` | ✅ | ❌ | **GAP: Minimum of N values** |
| `ops.Greatest` | ✅ | ❌ | **GAP: Maximum of N values** |

**Assessment:** Basic if-else covered, missing advanced multi-branch logic.

**Priority:** HIGH - These are common SQL patterns with high value.

---

### 6. String Operations - Basic ✅ **100% Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.Uppercase` | ✅ | ✅ | `string_mixins/_str_upper` |
| `ops.Lowercase` | ✅ | ✅ | `string_mixins/_str_lower` |
| `ops.Strip` | ✅ | ✅ | `string_mixins/_str_trim` |
| `ops.LStrip` | ✅ | ✅ | `string_mixins/_str_ltrim` |
| `ops.RStrip` | ✅ | ✅ | `string_mixins/_str_rtrim` |
| `ops.StringLength` | ✅ | ✅ | `string_mixins/_str_length` |
| `ops.Substring` | ✅ | ✅ | `string_mixins/_str_substring` |
| `ops.StringConcat` | ✅ | ✅ | `string_mixins/_str_concat` |
| `ops.StringReplace` | ✅ | ✅ | `string_mixins/_str_replace` |
| `ops.StringContains` | ✅ | ✅ | `string_mixins/_str_contains` |
| `ops.StartsWith` | ✅ | ✅ | `string_mixins/_str_starts_with` |
| `ops.EndsWith` | ✅ | ✅ | `string_mixins/_str_ends_with` |

**Assessment:** Excellent - all basic string operations covered.

---

### 7. String Operations - Advanced ❌ **0% Coverage**

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.Capitalize` | ✅ | ❌ | Medium |
| `ops.Reverse` | ✅ | ❌ | Low |
| `ops.StringSplit` | ✅ | ❌ | **High** |
| `ops.StringJoin` | ✅ | ❌ | Medium |
| `ops.ArrayStringJoin` | ✅ | ❌ | Medium |
| `ops.LPad` | ✅ | ❌ | Low |
| `ops.RPad` | ✅ | ❌ | Low |
| `ops.StrRight` | ✅ | ❌ | Low |
| `ops.Repeat` | ✅ | ❌ | Low |
| `ops.StringFind` | ✅ | ❌ | **High** |

**Assessment:** Missing convenience operations. StringSplit and StringFind are most valuable.

**Priority:** MEDIUM - Would enhance text processing capabilities.

---

### 8. Pattern/Regex Operations ✅ **100% Coverage (with unique features)**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.RegexSearch` | ✅ | ✅ | `pattern_mixins/_pattern_regex_contains` |
| `ops.RegexReplace` | ✅ | ✅ | `pattern_mixins/_pattern_regex_replace` |
| `ops.RegexExtract` | ✅ | ❌ | **GAP: Extract matched group** |
| `ops.RegexSplit` | ✅ | ❌ | **GAP: Split by regex** |
| SQL LIKE | ❌ | ✅ | **UNIQUE:** `_pattern_like` |
| Regex Full Match | ❌ | ✅ | **UNIQUE:** `_pattern_regex_match` |

**Assessment:** Core regex covered, plus SQL LIKE which Ibis lacks. Missing extract/split.

**Priority:** MEDIUM - RegexExtract is useful for parsing.

---

### 9. Temporal/DateTime Operations - Extraction ⚠️ **60% Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.ExtractYear` | ✅ | ✅ | `temporal_mixins/_temporal_year` |
| `ops.ExtractMonth` | ✅ | ✅ | `temporal_mixins/_temporal_month` |
| `ops.ExtractDay` | ✅ | ✅ | `temporal_mixins/_temporal_day` |
| `ops.ExtractHour` | ✅ | ✅ | `temporal_mixins/_temporal_hour` |
| `ops.ExtractMinute` | ✅ | ✅ | `temporal_mixins/_temporal_minute` |
| `ops.ExtractSecond` | ✅ | ✅ | `temporal_mixins/_temporal_second` |
| `ops.ExtractQuarter` | ✅ | ✅ | `temporal_mixins/_temporal_quarter` |
| `ops.ExtractWeekOfYear` | ✅ | ✅ | `temporal_mixins/_temporal_week` |
| `ops.DayOfWeekIndex` | ✅ | ✅ | `temporal_mixins/_temporal_weekday` |
| `ops.DayOfWeekName` | ✅ | ❌ | **GAP: Weekday name string** |
| `ops.ExtractIsoYear` | ✅ | ❌ | **GAP: ISO 8601 year** |
| `ops.ExtractDayOfYear` | ✅ | ❌ | **GAP: Day of year (1-366)** |
| `ops.ExtractMicrosecond` | ✅ | ❌ | **GAP: Microsecond component** |
| `ops.ExtractMillisecond` | ✅ | ❌ | **GAP: Millisecond component** |
| `ops.ExtractEpochSeconds` | ✅ | ❌ | **GAP: Unix timestamp** |

**Assessment:** Core extraction well covered, missing some specialized extractions.

**Priority:** LOW-MEDIUM - Most common operations covered.

---

### 10. Temporal/DateTime Operations - Arithmetic ✅ **86% Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.DateAdd` | ✅ | ✅ | `temporal_mixins/operations` (all units) |
| `ops.TimestampAdd` | ✅ | ✅ | `temporal_mixins/operations` (all units) |
| `ops.DateSub` | ✅ | ✅ | Via negative interval |
| `ops.TimestampSub` | ✅ | ✅ | Via negative interval |
| `ops.DateDiff` | ✅ | ❌ | **GAP: Generic diff** |
| `ops.TimestampDiff` | ✅ | ✅ | `temporal_mixins/_temporal_diff_*` |
| `ops.DateDelta` | ✅ | ✅ | `temporal_mixins/_temporal_diff_*` |

**Assessment:** Excellent coverage of temporal arithmetic with all interval units.

**Unique Feature:** mountainash supports flexible `offset_by` with string format.

---

### 11. Temporal/DateTime Operations - Manipulation ⚠️ **50% Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.DateTruncate` | ✅ | ✅ | `temporal_mixins/_temporal_truncate` |
| `ops.TimestampTruncate` | ✅ | ✅ | `temporal_mixins/_temporal_truncate` |
| `ops.TimestampBucket` | ✅ | ❌ | **GAP: Bucket dates into intervals** |
| `ops.Date` | ✅ | ❌ | **GAP: Cast to date** |
| `ops.Time` | ✅ | ❌ | **GAP: Extract time portion** |
| Offset By | ❌ | ✅ | **UNIQUE:** `_temporal_offset_by` |

**Assessment:** Core truncation covered, missing some utilities.

**Priority:** MEDIUM - TimestampBucket useful for time-series bucketing.

---

### 12. Temporal/DateTime Operations - Construction ❌ **0% Coverage**

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.DateFromYMD` | ✅ | ❌ | **High** |
| `ops.TimestampFromYMDHMS` | ✅ | ❌ | **High** |
| `ops.TimestampFromUNIX` | ✅ | ❌ | **High** |
| `ops.TimeFromHMS` | ✅ | ❌ | Medium |
| `ops.IntervalFromInteger` | ✅ | ❌ | Medium |

**Assessment:** Complete gap in date/time construction from components.

**Priority:** HIGH - Common ETL pattern (construct dates from parts).

---

### 13. Temporal/DateTime Operations - Parsing ❌ **0% Coverage**

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.StringToDate` | ✅ | ❌ | **High** |
| `ops.StringToTimestamp` | ✅ | ❌ | **High** |
| `ops.StringToTime` | ✅ | ❌ | Medium |
| `ops.Strftime` | ✅ | ❌ | **High** |

**Assessment:** Complete gap in string parsing and formatting.

**Priority:** HIGH - Essential for ETL workflows.

---

### 14. Temporal/DateTime Operations - Constants ❌ **0% Coverage**

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.TimestampNow` | ✅ | ❌ | Medium |
| `ops.DateNow` | ✅ | ❌ | Medium |

**Assessment:** Missing current timestamp/date functions.

**Priority:** MEDIUM - Useful for relative date filtering.

---

### 15. Math Operations ❌ **0% Coverage - CRITICAL GAP**

#### Trigonometric Functions

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.Sin` | ✅ | ❌ | **Critical** |
| `ops.Cos` | ✅ | ❌ | **Critical** |
| `ops.Tan` | ✅ | ❌ | **Critical** |
| `ops.Asin` | ✅ | ❌ | High |
| `ops.Acos` | ✅ | ❌ | High |
| `ops.Atan` | ✅ | ❌ | High |
| `ops.Atan2` | ✅ | ❌ | High |
| `ops.Cot` | ✅ | ❌ | Low |

#### Logarithmic & Exponential

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.Ln` | ✅ | ❌ | **Critical** |
| `ops.Log` | ✅ | ❌ | **Critical** |
| `ops.Log2` | ✅ | ❌ | High |
| `ops.Log10` | ✅ | ❌ | High |
| `ops.Exp` | ✅ | ❌ | **Critical** |

#### Rounding & Basic Math

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.Abs` | ✅ | ❌ | **Critical** |
| `ops.Sign` | ✅ | ❌ | **Critical** |
| `ops.Sqrt` | ✅ | ❌ | **Critical** |
| `ops.Round` | ✅ | ❌ | **Critical** |
| `ops.Ceil` | ✅ | ❌ | **Critical** |
| `ops.Floor` | ✅ | ❌ | **Critical** |
| `ops.Clip` | ✅ | ❌ | Medium |

#### Special Functions

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.IsNan` | ✅ | ❌ | High |
| `ops.IsInf` | ✅ | ❌ | High |
| `ops.Radians` | ✅ | ❌ | Medium |
| `ops.Degrees` | ✅ | ❌ | Medium |
| `ops.Pi` | ✅ | ❌ | Medium |
| `ops.E` | ✅ | ❌ | Medium |

**Assessment:** Complete absence of math operations is a critical gap.

**Priority:** **CRITICAL** - Math operations are fundamental for data analysis.

**Impact:** Without these, mountainash-expressions cannot be used for scientific/analytical workloads.

---

### 16. Array Operations ❌ **0% Coverage - CRITICAL GAP**

#### Array Construction & Basics

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.Array` | ✅ | ❌ | High |
| `ops.ArrayConcat` | ✅ | ❌ | High |
| `ops.ArrayLength` | ✅ | ❌ | **Critical** |
| `ops.ArrayIndex` | ✅ | ❌ | **Critical** |
| `ops.ArraySlice` | ✅ | ❌ | High |
| `ops.ArraySort` | ✅ | ❌ | Medium |

#### Array Set Operations

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.ArrayUnion` | ✅ | ❌ | High |
| `ops.ArrayIntersect` | ✅ | ❌ | High |
| `ops.ArrayDistinct` | ✅ | ❌ | High |
| `ops.ArrayRemove` | ✅ | ❌ | Medium |
| `ops.ArrayContains` | ✅ | ❌ | **Critical** |

#### Array Aggregations

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.ArraySum` | ✅ | ❌ | High |
| `ops.ArrayMean` | ✅ | ❌ | High |
| `ops.ArrayMin` | ✅ | ❌ | High |
| `ops.ArrayMax` | ✅ | ❌ | High |
| `ops.ArrayAny` | ✅ | ❌ | Medium |
| `ops.ArrayAll` | ✅ | ❌ | Medium |

#### Other Array Operations

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.ArrayFlatten` | ✅ | ❌ | Medium |

**Assessment:** Complete absence of array operations.

**Priority:** **CRITICAL** - Arrays/lists are fundamental data structures.

**Complexity:** High - Requires backend capability checking (not all backends support arrays equally).

---

### 17. Collection/Set Operations ⚠️ **67% Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.InValues` | ✅ | ✅ | `boolean_mixins/collection/_B_in` |
| `ops.InSubquery` | ✅ | ❌ | **GAP: IN with subquery** |
| NOT IN | ❌ | ✅ | `boolean_mixins/collection/_B_not_in` |

**Assessment:** Core membership operations covered.

**Priority:** LOW - InSubquery is advanced feature.

---

### 18. Type Operations ⚠️ **50% Coverage**

| Operation | Ibis-Polars | mountainash | Implementation |
|-----------|-------------|-------------|----------------|
| `ops.Cast` | ✅ | ✅ | `common_mixins/_cast` |
| `ops.TryCast` | ✅ | ❌ | **GAP: Safe cast with null on failure** |

**Assessment:** Basic casting covered, missing safe variant.

**Priority:** MEDIUM - TryCast prevents errors in production.

---

### 19. Bitwise Operations ❌ **0% Coverage**

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.BitwiseAnd` | ✅ | ❌ | Low |
| `ops.BitwiseOr` | ✅ | ❌ | Low |
| `ops.BitwiseXor` | ✅ | ❌ | Low |
| `ops.BitwiseNot` | ✅ | ❌ | Low |
| `ops.BitwiseLeftShift` | ✅ | ❌ | Low |
| `ops.BitwiseRightShift` | ✅ | ❌ | Low |

**Assessment:** Complete gap, but niche use cases.

**Priority:** LOW - Rarely used outside specialized domains.

---

### 20. Window/Analytic Functions ❌ **0% Coverage - CRITICAL GAP**

**IMPORTANT:** Window functions are a distinct category that operate over a "window" of rows defined by partitioning and ordering. They are neither simple expressions nor table aggregations.

#### Pure Analytic Functions (Ranking)

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.MinRank` | ✅ | ❌ | **Critical** |
| `ops.DenseRank` | ✅ | ❌ | **Critical** |
| `ops.RowNumber` | ✅ | ❌ | **Critical** |
| `ops.PercentRank` | ✅ | ❌ | High |
| `ops.CumeDist` | ✅ | ❌ | High |
| `ops.NTile` | ✅ | ❌ | High |

#### Offset/Position Functions

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `ops.Lag` | ✅ | ❌ | **Critical** |
| `ops.Lead` | ✅ | ❌ | **Critical** |
| `ops.NthValue` | ✅ | ❌ | High |
| `ops.FirstValue` | ✅ | ❌ | High |
| `ops.LastValue` | ✅ | ❌ | High |

#### Cumulative Functions

| Operation | Ibis-Polars | mountainash | Priority |
|-----------|-------------|-------------|----------|
| `cumsum()` | ✅ | ❌ | **Critical** |
| `cummean()` | ✅ | ❌ | High |
| `cummin()` | ✅ | ❌ | High |
| `cummax()` | ✅ | ❌ | High |
| `cumany()` | ✅ | ❌ | Medium |
| `cumall()` | ✅ | ❌ | Medium |

#### Window Specification

| Feature | Ibis-Polars | mountainash | Priority |
|---------|-------------|-------------|----------|
| `.over(group_by, order_by)` | ✅ | ❌ | **Critical** |
| `ROWS BETWEEN` frames | ✅ | ❌ | **Critical** |
| `RANGE BETWEEN` frames | ✅ | ❌ | High |

**Assessment:** Complete absence of window function support.

**Priority:** **CRITICAL** - Window functions are essential for:
- Ranking and top-N queries
- Time series analysis (moving averages, running totals)
- Sequential comparisons (lag/lead)
- Percentile calculations
- Cumulative aggregations

**Complexity:** High - Requires:
- Window specification system (PARTITION BY, ORDER BY)
- Frame specification (ROWS/RANGE BETWEEN)
- Integration with both analytic and aggregation functions

**Use Cases:**
```python
# Ranking - Top 3 per category
rank().over(group_by="category", order_by=sales.desc()) <= 3

# Time series - 7-day moving average
mean().over(rows=(-6, 0), order_by=date)

# Sequential - Compare to previous period
current - lag(1).over(order_by=month)

# Cumulative - Running total
cumsum()
```

**Total Window Operations:** 17

---

## Critical Gaps

### Priority 1: Math Operations (26 operations)

**Impact:** CRITICAL - Fundamental for any analytical/scientific work

**Quick Wins (10 operations, 2-3 weeks):**
- `Abs`, `Sign`, `Sqrt` - Basic operations
- `Round`, `Floor`, `Ceil` - Rounding
- `Ln`, `Log`, `Log10`, `Exp` - Logarithms
- `IsNan`, `IsInf` - NaN/Inf checks

**Advanced (16 operations, 2-3 weeks):**
- Trigonometry: `Sin`, `Cos`, `Tan`, `Asin`, `Acos`, `Atan`, `Atan2`, `Cot`
- Other: `Log2`, `Radians`, `Degrees`, `Clip`
- Constants: `Pi`, `E`

**Implementation Strategy:**
```python
# Add new mixin: math_mixins/
class MathOperatorsExpressionVisitor:
    @property
    def math_ops(self) -> Dict[str, Callable]:
        return {
            CONST_MATH_OPERATORS.ABS: self._math_abs,
            CONST_MATH_OPERATORS.SQRT: self._math_sqrt,
            # ...
        }

    def _math_abs(self, node):
        arg = self._process_operand(node.operand)
        return self.backend.abs(arg)
```

---

### Priority 2: Array Operations (18 operations)

**Impact:** HIGH - Essential for data science workflows

**Challenges:**
- Backend support varies significantly
- Polars: Excellent array support
- Pandas: Limited array support
- Ibis backends: Varies by SQL engine

**Critical Operations (5 operations, 2-3 weeks):**
- `ArrayLength` - Get array size
- `ArrayIndex` - Access element by index
- `ArrayContains` - Check membership
- `ArraySlice` - Extract sub-array
- `Array` - Construct array from values

**High Value Operations (7 operations, 2-3 weeks):**
- `ArrayConcat` - Concatenate arrays
- `ArrayUnion` - Set union
- `ArrayIntersect` - Set intersection
- `ArrayDistinct` - Remove duplicates
- `ArraySum`, `ArrayMean`, `ArrayMin`, `ArrayMax` - Aggregations

**Implementation Strategy:**
```python
# Add new mixin: array_mixins/
class ArrayOperatorsExpressionVisitor:
    # Requires backend capability checking
    def _check_array_support(self):
        if not self.backend.supports_arrays:
            raise NotImplementedError(
                f"Backend {self.backend} does not support array operations"
            )
```

---

### Priority 3: Advanced Conditionals (5 operations)

**Impact:** HIGH - Common SQL patterns

**Operations (1-2 weeks):**
- `SimpleCase` - CASE value WHEN ... THEN ... ELSE
- `SearchedCase` - CASE WHEN condition THEN ... ELSE
- `Least` - Minimum of N values
- `Greatest` - Maximum of N values
- `NullIf` - Return NULL if condition met

**Implementation Strategy:**
```python
# Extend conditional_mixins/
def _conditional_case(self, node):
    """Handle multi-branch CASE expressions"""
    # Reverse iteration to build nested when/then/otherwise
    result = self._process_operand(node.default)
    for case, value in reversed(zip(node.cases, node.values)):
        cond = self._process_operand(case)
        val = self._process_operand(value)
        result = self.backend.when(cond).then(val).otherwise(result)
    return result
```

---

### Priority 4: Temporal Construction & Parsing (12 operations)

**Impact:** MEDIUM-HIGH - Essential for ETL workflows

**Construction (5 operations, 1-2 weeks):**
- `DateFromYMD` - Build date from year, month, day
- `TimestampFromYMDHMS` - Build timestamp from components
- `TimestampFromUNIX` - Convert Unix timestamp
- `TimeFromHMS` - Build time from components
- `IntervalFromInteger` - Create interval

**Parsing (4 operations, 1-2 weeks):**
- `StringToDate` - Parse date string
- `StringToTimestamp` - Parse timestamp string
- `StringToTime` - Parse time string
- `Strftime` - Format datetime as string

**Constants (2 operations, <1 week):**
- `TimestampNow` - Current timestamp
- `DateNow` - Current date

---

### Priority 5: Advanced String Operations (11 operations)

**Impact:** MEDIUM - Enhances text processing

**High Value (3 operations, 1 week):**
- `StringSplit` - Split into array
- `StringFind` - Find position of substring
- `RegexExtract` - Extract matched group

**Medium Value (5 operations, 1 week):**
- `Capitalize` - Capitalize first letter
- `StringJoin` - Join array to string
- `Repeat` - Repeat string N times
- `LPad`, `RPad` - Padding

**Low Value (3 operations):**
- `Reverse` - Reverse string
- `StrRight` - Right N characters
- `ArrayStringJoin` - Join array with separator

---

## mountainash-expressions Unique Features

Features that mountainash-expressions has that Ibis-Polars does NOT have:

### 1. Ternary Logic System (UNIQUE)

Complete three-valued logic implementation:

```python
# Ternary logic checks (not in Ibis)
expr.is_unknown()    # TRUE/FALSE/UNKNOWN → checks for UNKNOWN
expr.is_known()      # TRUE/FALSE/UNKNOWN → checks for TRUE or FALSE
expr.maybe_true()    # TRUE/FALSE/UNKNOWN → checks for TRUE or UNKNOWN
expr.maybe_false()   # TRUE/FALSE/UNKNOWN → checks for FALSE or UNKNOWN

# Ternary constants
ALWAYS_TRUE
ALWAYS_FALSE
ALWAYS_UNKNOWN
```

**Value:** Provides NULL-safe three-valued logic for complex conditions.

---

### 2. XOR Parity Operation (UNIQUE)

```python
# Boolean parity XOR (different from exclusive XOR)
expr1.xor_parity(expr2, expr3, ...)
```

**Value:** Different semantics than standard XOR - useful for specific logic patterns.

---

### 3. SQL LIKE Pattern Matching (UNIQUE)

```python
# SQL-style LIKE with wildcards
col("name").like("John%")    # Starts with "John"
col("email").like("%@%.com") # Email pattern
```

Ibis-Polars doesn't have native LIKE support.

**Value:** Familiar SQL pattern matching syntax.

---

### 4. Regex Full Match (UNIQUE)

```python
# Full string match (not just contains)
col("code").regex_match(r"^[A-Z]{3}-\d{4}$")
```

Ibis has `RegexSearch` (contains) but not full match.

**Value:** Stricter pattern validation.

---

### 5. Natural Language Temporal Helpers (UNIQUE)

```python
# Natural language time expressions
within_last(col("timestamp"), "10 minutes")
older_than(col("created"), "7 days")
time_ago("2 hours")
between_last(col("updated"), "1 hour", "3 hours")

# Flexible offset_by format
col("date").offset_by("2d")      # 2 days
col("date").offset_by("3mo")     # 3 months
col("date").offset_by("-1y")     # 1 year ago
col("date").offset_by("1h30m")   # 1.5 hours
```

Ibis requires more verbose interval construction.

**Value:** User-friendly temporal operations inspired by journalctl/find commands.

---

### 6. Unified Temporal Interface (UNIQUE)

Single, consistent API for all temporal operations across backends:

```python
# All temporal units supported consistently
col("date").add_years(1)
col("date").add_months(3)
col("date").add_weeks(2)
col("date").add_days(7)
col("date").add_hours(24)
col("date").add_minutes(30)
col("date").add_seconds(60)

# Corresponding diff operations
col("end").diff_years(col("start"))
col("end").diff_months(col("start"))
# ... etc
```

**Value:** Eliminates backend-specific temporal quirks.

---

## Implementation Roadmap

### Phase 1: Essential Math (2-3 weeks) - **PRIORITY 1**

**Objective:** Enable basic analytical/scientific workloads

**Operations (10-12):**
- Basic: `Abs`, `Sign`, `Sqrt`
- Rounding: `Round`, `Floor`, `Ceil`
- Logarithms: `Ln`, `Log`, `Log10`, `Log2`, `Exp`
- Checks: `IsNan`, `IsInf`

**Deliverables:**
- New mixin: `math_mixins/basic_math_visitor.py`
- Constants: `CONST_MATH_OPERATORS`
- Node types: `MathUnaryExpressionNode`, `MathBinaryExpressionNode`
- Tests: Cross-backend math operation tests
- Documentation: Math operations reference

**Success Criteria:**
- All basic math operations work across Polars, Narwhals, Ibis backends
- Consistent behavior (same results as native backend)
- 100% test coverage

---

### Phase 2: Advanced Conditionals (1-2 weeks) - **PRIORITY 2**

**Objective:** Support complex business logic patterns

**Operations (5):**
- `SimpleCase` - CASE value WHEN matching
- `SearchedCase` - CASE WHEN conditions
- `Least` - Minimum of N values
- `Greatest` - Maximum of N values
- `NullIf` - Conditional null

**Deliverables:**
- Extend `conditional_mixins/`
- Node types: `CaseExpressionNode`, `LeastGreatestExpressionNode`
- Tests: Multi-branch logic tests
- Documentation: Case expressions guide

**Success Criteria:**
- Multi-branch CASE WHEN works correctly
- Least/Greatest handle variable argument counts
- All operations NULL-safe

---

### Phase 3: String Enhancements (1-2 weeks) - **PRIORITY 3**

**Objective:** Fill obvious string operation gaps

**Operations (8-10):**
- High value: `StringSplit`, `StringFind`, `RegexExtract`
- Medium value: `Capitalize`, `Repeat`, `LPad`, `RPad`
- Low value: `Reverse`, `StrRight`, `StringJoin`

**Deliverables:**
- Extend `string_mixins/`
- Extend `pattern_mixins/` for `RegexExtract`
- Tests: String operation tests
- Documentation: String operations reference

**Success Criteria:**
- All string operations work across backends
- StringSplit returns arrays (requires array support)
- RegexExtract handles capture groups

---

### Phase 4: Temporal Construction & Parsing (2-3 weeks) - **PRIORITY 4**

**Objective:** Enable date/time construction and parsing for ETL

**Operations (12):**
- Construction: `DateFromYMD`, `TimestampFromYMDHMS`, `TimestampFromUNIX`, `TimeFromHMS`, `IntervalFromInteger`
- Parsing: `StringToDate`, `StringToTimestamp`, `StringToTime`, `Strftime`
- Constants: `TimestampNow`, `DateNow`
- Other: `TimestampBucket`

**Deliverables:**
- Extend `temporal_mixins/construction/`
- New: `temporal_mixins/parsing/`
- Node types: `TemporalConstructionNode`, `TemporalParsingNode`
- Tests: Construction and parsing tests
- Documentation: Temporal construction guide

**Success Criteria:**
- Can construct dates/timestamps from components
- Can parse common date formats
- Format strings work across backends
- now() functions return current time

---

### Phase 5: Advanced Math (2-3 weeks) - **PRIORITY 5**

**Objective:** Complete math operation coverage

**Operations (14):**
- Trigonometry: `Sin`, `Cos`, `Tan`, `Asin`, `Acos`, `Atan`, `Atan2`, `Cot`
- Other: `Radians`, `Degrees`, `Clip`
- Constants: `Pi`, `E`

**Deliverables:**
- Extend `math_mixins/`
- Add: `math_mixins/trigonometry_visitor.py`
- Constants: Math constants (`Pi`, `E`)
- Tests: Trigonometry tests
- Documentation: Advanced math reference

**Success Criteria:**
- All trigonometric functions work
- Angle conversion (radians/degrees) correct
- Constants available as expressions

---

### Phase 6: Array Operations (4-6 weeks) - **PRIORITY 6**

**Objective:** Enable array/list operations

**Complexity:** HIGH - Requires backend capability checking

**Operations (18):**
- **Critical (5):** `ArrayLength`, `ArrayIndex`, `ArrayContains`, `ArraySlice`, `Array`
- **High Value (7):** `ArrayConcat`, `ArrayUnion`, `ArrayIntersect`, `ArrayDistinct`, `ArraySum`, `ArrayMean`, `ArrayMin`, `ArrayMax`
- **Medium Value (6):** `ArraySort`, `ArrayRemove`, `ArrayFlatten`, `ArrayAny`, `ArrayAll`

**Deliverables:**
- New mixin: `array_mixins/`
- Backend capability checking system
- Node types: `ArrayExpressionNode`, `ArrayIndexNode`, etc.
- Tests: Array operation tests (Polars-focused initially)
- Documentation: Array operations guide with backend compatibility matrix

**Success Criteria:**
- All array operations work on Polars backend
- Graceful degradation for backends without array support
- Clear error messages when arrays not supported
- Documentation of backend compatibility

**Backend Considerations:**
- Polars: Excellent array support (full implementation)
- Narwhals: Good support (depends on underlying backend)
- Ibis-Polars: Good support
- Ibis-DuckDB: Good support
- Ibis-SQLite: Limited/no support
- Pandas: Limited array support (may need workarounds)

---

### Phase 7: Specialized Operations (1-2 weeks) - **PRIORITY 7**

**Objective:** Fill remaining gaps

**Operations (10-12):**
- Bitwise: `BitwiseAnd`, `BitwiseOr`, `BitwiseXor`, `BitwiseNot`, `LeftShift`, `RightShift`
- Type: `TryCast`
- Comparison: `Between`, `IdenticalTo`
- Other: `Negate` (unary), remaining temporal extractions

**Deliverables:**
- New mixin: `bitwise_mixins/`
- Extend existing mixins
- Tests: Specialized operation tests
- Documentation: Complete operation reference

**Success Criteria:**
- All operations work correctly
- Complete Ibis-Polars feature parity
- Comprehensive documentation

---

## Backend Compatibility Considerations

### Array Operations - Backend Support Matrix

| Backend | Array Support | Limitations |
|---------|---------------|-------------|
| **Polars** | ✅ Excellent | Full support for all array operations |
| **Narwhals** | ✅ Good | Depends on underlying backend |
| **Ibis-Polars** | ✅ Good | Full support via Polars |
| **Ibis-DuckDB** | ✅ Good | Good array/list support |
| **Ibis-SQLite** | ❌ Poor | Very limited array support |
| **Pandas** | ⚠️ Limited | Arrays as object dtype, limited operations |

**Strategy:**
1. Implement arrays with Polars as reference
2. Add backend capability checking
3. Provide clear error messages for unsupported backends
4. Document compatibility matrix

---

### Math Operations - Precision Considerations

**Backend Differences:**
- **Polars:** Uses Rust implementations (high precision)
- **SQLite:** Limited math functions, some missing
- **DuckDB:** Full math support
- **Pandas:** NumPy-based (high precision)

**Strategy:**
- Test for numerical precision across backends
- Document any known precision differences
- Use appropriate tolerances in tests

---

### Temporal Operations - Calendar Intervals

**Backend Differences:**
- **Polars:** Native calendar interval support (months, years)
- **Other backends:** May need workarounds for calendar intervals

**Current Solution:**
- mountainash-expressions already handles this via `offset_by` with string format
- Ibis local fork includes calendar interval fix for Polars

---

## Implementation Guidelines

### 1. Architecture Patterns

**Follow Existing Patterns:**
```python
# 1. Define operation constants
class CONST_MATH_OPERATORS(StrEnum):
    ABS = "abs"
    SQRT = "sqrt"
    ROUND = "round"
    # ...

# 2. Create node types
class MathUnaryExpressionNode(ExpressionNode):
    operator: CONST_MATH_OPERATORS
    operand: ExpressionNode

# 3. Implement visitor mixin
class MathOperatorsExpressionVisitor:
    def visit_math_unary_expression(self, node):
        arg = self._process_operand(node.operand)
        method = self.math_ops[node.operator]
        return method(arg)

# 4. Add to ExpressionSystem interface
class ExpressionSystem(ABC):
    @abstractmethod
    def abs(self, arg): ...

    @abstractmethod
    def sqrt(self, arg): ...

# 5. Implement in each backend
class PolarsExpressionSystem(ExpressionSystem):
    def abs(self, arg: pl.Expr) -> pl.Expr:
        return arg.abs()
```

---

### 2. Testing Strategy

**Cross-Backend Parametrized Tests:**
```python
@pytest.mark.parametrize("backend_df", [
    pytest.param("polars_df", id="polars"),
    pytest.param("narwhals_df", id="narwhals"),
    pytest.param("ibis_polars_df", id="ibis-polars"),
    # ...
])
def test_abs_operation(backend_df, request):
    df = request.getfixturevalue(backend_df)
    expr = ma.col("value").abs()
    result = ma.filter(df, expr.gt(10))
    # assertions...
```

**Numerical Tolerance:**
```python
# For floating-point math operations
assert abs(result - expected) < 1e-10
```

**Backend Capability Tests:**
```python
def test_array_operations_not_supported_on_sqlite():
    with pytest.raises(NotImplementedError, match="does not support array"):
        ma.col("arr").array_length()
```

---

### 3. Documentation Requirements

**For Each New Operation:**
1. API reference with signature
2. Description and use cases
3. Example code
4. Backend compatibility notes
5. Related operations

**Example:**
```markdown
## abs()

Returns the absolute value of a numeric expression.

### Signature
```python
col(name).abs() -> ExpressionBuilder
```

### Description
Computes the absolute value (magnitude) of each element, removing the sign.

### Examples
```python
import mountainash_expressions as ma

# Basic usage
expr = ma.col("temperature").abs()

# Filter by absolute value
result = ma.filter(df, ma.col("change").abs().gt(10))

# Combine with other operations
expr = ma.col("value").abs().sqrt()
```

### Backend Compatibility
| Backend | Support | Notes |
|---------|---------|-------|
| Polars | ✅ | Full support |
| Narwhals | ✅ | Full support |
| Ibis-Polars | ✅ | Full support |
| Ibis-DuckDB | ✅ | Full support |
| Ibis-SQLite | ✅ | Full support |

### See Also
- `sign()` - Returns the sign of a number
- `sqrt()` - Square root
```

---

### 4. Performance Considerations

**Lazy Evaluation:**
- All backends use lazy evaluation
- Expression building should be fast
- Actual computation happens during execution

**Avoid Expensive Operations:**
- Don't materialize intermediate results
- Let backend optimizer handle query planning

**Backend-Specific Optimizations:**
- Some backends have optimized implementations
- Document performance characteristics

---

## Detailed Operation Tables

### Complete Ibis-Polars Operation List

Total operations cataloged from `/home/nathanielramm/git/ibis/ibis/backends/polars/compiler.py`:

#### Category: Comparison (8 operations)
1. `ops.Equals` - Equality
2. `ops.NotEquals` - Inequality
3. `ops.Greater` - Greater than
4. `ops.GreaterEqual` - Greater or equal
5. `ops.Less` - Less than
6. `ops.LessEqual` - Less or equal
7. `ops.Between` - Range check
8. `ops.IdenticalTo` - Null-safe equality

#### Category: Arithmetic (8 operations)
1. `ops.Add` - Addition
2. `ops.Subtract` - Subtraction
3. `ops.Multiply` - Multiplication
4. `ops.Divide` - Division
5. `ops.FloorDivide` - Integer division
6. `ops.Modulus` - Modulo
7. `ops.Power` - Exponentiation
8. `ops.Negate` - Unary negation

#### Category: Boolean/Logical (4 operations)
1. `ops.And` - Logical AND
2. `ops.Or` - Logical OR
3. `ops.Not` - Logical NOT
4. `ops.Xor` - Logical XOR

#### Category: Math (26 operations)
1. `ops.Abs` - Absolute value
2. `ops.Sign` - Sign of number
3. `ops.Sqrt` - Square root
4. `ops.Round` - Round to N decimals
5. `ops.Ceil` - Round up
6. `ops.Floor` - Round down
7. `ops.Clip` - Clip values to range
8. `ops.Ln` - Natural logarithm
9. `ops.Log` - Logarithm with base
10. `ops.Log2` - Base-2 logarithm
11. `ops.Log10` - Base-10 logarithm
12. `ops.Exp` - Exponential (e^x)
13. `ops.Sin` - Sine
14. `ops.Cos` - Cosine
15. `ops.Tan` - Tangent
16. `ops.Asin` - Arcsine
17. `ops.Acos` - Arccosine
18. `ops.Atan` - Arctangent
19. `ops.Atan2` - Two-argument arctangent
20. `ops.Cot` - Cotangent
21. `ops.Radians` - Degrees to radians
22. `ops.Degrees` - Radians to degrees
23. `ops.IsNan` - Check for NaN
24. `ops.IsInf` - Check for infinity
25. `ops.Pi` - Pi constant
26. `ops.E` - Euler's number constant

#### Category: String Basic (12 operations)
1. `ops.Uppercase` - Convert to uppercase
2. `ops.Lowercase` - Convert to lowercase
3. `ops.Strip` - Remove whitespace from both ends
4. `ops.LStrip` - Remove leading whitespace
5. `ops.RStrip` - Remove trailing whitespace
6. `ops.StringLength` - Get string length
7. `ops.Substring` - Extract substring
8. `ops.StringConcat` - Concatenate strings
9. `ops.StringReplace` - Replace substring
10. `ops.StringContains` - Check if contains substring
11. `ops.StartsWith` - Check if starts with prefix
12. `ops.EndsWith` - Check if ends with suffix

#### Category: String Advanced (11 operations)
1. `ops.Capitalize` - Capitalize first letter
2. `ops.Reverse` - Reverse string
3. `ops.StringSplit` - Split into array
4. `ops.StringJoin` - Join array to string
5. `ops.ArrayStringJoin` - Join array with separator
6. `ops.LPad` - Left pad
7. `ops.RPad` - Right pad
8. `ops.StrRight` - Right N characters
9. `ops.Repeat` - Repeat string N times
10. `ops.StringFind` - Find substring position

#### Category: Pattern/Regex (4 operations)
1. `ops.RegexSearch` - Regex contains
2. `ops.RegexExtract` - Extract matched group
3. `ops.RegexReplace` - Replace by regex
4. `ops.RegexSplit` - Split by regex

#### Category: Temporal Extraction (15 operations)
1. `ops.ExtractYear` - Extract year
2. `ops.ExtractMonth` - Extract month
3. `ops.ExtractDay` - Extract day
4. `ops.ExtractHour` - Extract hour
5. `ops.ExtractMinute` - Extract minute
6. `ops.ExtractSecond` - Extract second
7. `ops.ExtractQuarter` - Extract quarter
8. `ops.ExtractWeekOfYear` - Extract week of year
9. `ops.ExtractIsoYear` - Extract ISO year
10. `ops.ExtractDayOfYear` - Extract day of year
11. `ops.ExtractMicrosecond` - Extract microseconds
12. `ops.ExtractMillisecond` - Extract milliseconds
13. `ops.ExtractEpochSeconds` - Unix timestamp
14. `ops.DayOfWeekIndex` - Weekday index (0-6)
15. `ops.DayOfWeekName` - Weekday name string

#### Category: Temporal Arithmetic (7 operations)
1. `ops.DateAdd` - Add interval to date
2. `ops.TimestampAdd` - Add interval to timestamp
3. `ops.DateSub` - Subtract interval from date
4. `ops.TimestampSub` - Subtract interval from timestamp
5. `ops.DateDiff` - Difference between dates
6. `ops.TimestampDiff` - Difference between timestamps
7. `ops.DateDelta` - Interval between dates

#### Category: Temporal Manipulation (6 operations)
1. `ops.DateTruncate` - Truncate date to unit
2. `ops.TimestampTruncate` - Truncate timestamp to unit
3. `ops.TimestampBucket` - Bucket timestamp into intervals
4. `ops.Date` - Cast to date
5. `ops.Time` - Extract time portion

#### Category: Temporal Construction (5 operations)
1. `ops.DateFromYMD` - Construct date from parts
2. `ops.TimestampFromYMDHMS` - Construct timestamp from parts
3. `ops.TimestampFromUNIX` - Convert from Unix timestamp
4. `ops.TimeFromHMS` - Construct time from parts
5. `ops.IntervalFromInteger` - Create interval

#### Category: Temporal Parsing (4 operations)
1. `ops.StringToDate` - Parse date string
2. `ops.StringToTimestamp` - Parse timestamp string
3. `ops.StringToTime` - Parse time string
4. `ops.Strftime` - Format datetime as string

#### Category: Temporal Constants (2 operations)
1. `ops.TimestampNow` - Current timestamp
2. `ops.DateNow` - Current date

#### Category: Null Handling (5 operations)
1. `ops.IsNull` - Check if null
2. `ops.NotNull` - Check if not null
3. `ops.Coalesce` - First non-null value
4. `ops.FillNull` - Replace nulls
5. `ops.NullIf` - Return null if condition

#### Category: Conditional (5 operations)
1. `ops.IfElse` - If-then-else
2. `ops.SimpleCase` - CASE value WHEN
3. `ops.SearchedCase` - CASE WHEN
4. `ops.Least` - Minimum of N values
5. `ops.Greatest` - Maximum of N values

#### Category: Collection/Set (3 operations)
1. `ops.InValues` - IN with literal values
2. `ops.InSubquery` - IN with subquery

#### Category: Type Operations (2 operations)
1. `ops.Cast` - Type cast
2. `ops.TryCast` - Safe type cast

#### Category: Bitwise (6 operations)
1. `ops.BitwiseAnd` - Bitwise AND
2. `ops.BitwiseOr` - Bitwise OR
3. `ops.BitwiseXor` - Bitwise XOR
4. `ops.BitwiseNot` - Bitwise NOT
5. `ops.BitwiseLeftShift` - Left shift
6. `ops.BitwiseRightShift` - Right shift

#### Category: Array (18 operations)
1. `ops.Array` - Construct array
2. `ops.ArrayConcat` - Concatenate arrays
3. `ops.ArrayLength` - Get array length
4. `ops.ArrayIndex` - Access by index
5. `ops.ArraySlice` - Extract sub-array
6. `ops.ArraySort` - Sort array
7. `ops.ArrayContains` - Check membership
8. `ops.ArrayRemove` - Remove element
9. `ops.ArrayUnion` - Set union
10. `ops.ArrayIntersect` - Set intersection
11. `ops.ArrayDistinct` - Remove duplicates
12. `ops.ArrayFlatten` - Flatten nested arrays
13. `ops.ArraySum` - Sum of array
14. `ops.ArrayMean` - Mean of array
15. `ops.ArrayMin` - Minimum of array
16. `ops.ArrayMax` - Maximum of array
17. `ops.ArrayAny` - Any element true
18. `ops.ArrayAll` - All elements true

---

### Total Operations by Priority

| Priority | Operations | Effort (weeks) | Categories |
|----------|-----------|----------------|------------|
| **CRITICAL** | 43 | 8-11 | Math operations (26), Window functions (17) |
| **HIGH** | 30 | 8-12 | Arrays (18), Conditionals (5), Temporal Const/Parse (7) |
| **MEDIUM** | 20 | 4-6 | String advanced (11), Temporal extractions (5), Type ops (1), Misc (3) |
| **LOW** | 12 | 2-3 | Bitwise (6), Misc (6) |
| **TOTAL** | **105** | **22-32** | All categories |

---

## Conclusion

mountainash-expressions has built a **solid foundation** with excellent coverage of:
- Core logical operations (100%+)
- Basic arithmetic (87.5%)
- String operations (100% basic)
- Pattern matching (100%+)
- Temporal arithmetic (86%)

However, to reach feature parity with Ibis-Polars, **105 operations** need to be added, with **Math operations** (26) and **Window functions** (17) being the most critical gaps.

### Key Strengths
1. Clean, extensible architecture (mixin-based)
2. Unique ternary logic system
3. Natural language temporal helpers
4. Strong cross-backend testing infrastructure

### Key Gaps
1. **Math operations** - Complete absence, critical for analytics
2. **Window functions** - Complete absence, essential for ranking/time series
3. **Array operations** - Complete absence, important for data science
4. **Advanced conditionals** - Missing CASE WHEN patterns
5. **Temporal construction** - Can't build dates from parts

### Recommended Next Steps

1. **Immediate:** Implement Phase 1 (Essential Math) - 2-3 weeks
2. **Short-term:** Implement Phase 2 (Advanced Conditionals) - 1-2 weeks
3. **Medium-term:** Phases 3-5 (Strings, Temporal, Advanced Math) - 6-9 weeks
4. **Long-term:** Phases 6-8 (Arrays, Specialized Ops, Window Functions) - 8-13 weeks

**Total estimated effort to 80%+ coverage:** 17-27 weeks of focused development.

---

**Document Version:** 1.0
**Last Updated:** 2025-01-09
**Next Review:** After Phase 1 completion
