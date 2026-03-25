# Extended API Builder Coverage Test Suite Design

**Date:** 2026-03-25
**Status:** Approved
**Branch:** feature/substrait_alignment

## Problem

After the initial fluent composition test suite (10 files, 258 tests), several active API builders remain below 90% coverage. The biggest gaps are in string (47%) and datetime (51%) builders, with comparison (58%), arithmetic (74%), and ternary (85%) also below target.

### Current Coverage (active builders only)

| File | Coverage | Uncovered methods |
|------|----------|-------------------|
| `api_bldr_scalar_string.py` | 47% | 30 methods |
| `ext_ma_scalar_datetime.py` | 51% | 27 methods (+ 5 sugar methods tested elsewhere) |
| `api_bldr_scalar_logarithmic.py` | 55% | 4 methods |
| `api_bldr_scalar_comparison.py` | 58% | 15 methods |
| `api_bldr_scalar_datetime.py` | 62% | 3 methods |
| `api_bldr_scalar_rounding.py` | 71% | 2 methods |
| `api_bldr_scalar_arithmetic.py` | 74% | 27 methods |
| `ext_ma_scalar_ternary.py` | 85% | 6 methods |

**Target:** 90%+ on all active API builder files.

### Out of scope

- Stub files (ext_ma_scalar_string, ext_ma_scalar_comparison, ext_ma_scalar_aggregate, _api_bldr_scalar_aggregate) — dead code, replaced with empty stubs
- Logarithmic and rounding builders — small enough to fold into the comparison extended tests
- Protocol files — `...` method bodies are expected uncovered

## Design

### File Structure

5 new test files in `tests/cross_backend/`:

| File | Category | ~Tests | Target builders |
|------|----------|--------|-----------------|
| `test_compose_string_extended.py` | String methods | 17 | `api_bldr_scalar_string.py` (47% → 90%+) |
| `test_compose_datetime_extended.py` | Datetime methods | 13 | `ext_ma_scalar_datetime.py` (51% → 90%+), `api_bldr_scalar_datetime.py` (62% → 90%+) |
| `test_compose_comparison_extended.py` | Comparison + rounding + log | 12 | `api_bldr_scalar_comparison.py` (58% → 90%+), `api_bldr_scalar_rounding.py` (71% → 90%+), `api_bldr_scalar_logarithmic.py` (55% → 90%+) |
| `test_compose_arithmetic_extended.py` | Math + bitwise | 10 | `api_bldr_scalar_arithmetic.py` (74% → 90%+) |
| `test_compose_ternary_extended.py` | Ternary set + logic | 4 | `ext_ma_scalar_ternary.py` (85% → 90%+) |

~56 tests total. All parametrized across 6 backends with xfails for known limitations.

### Test Design Principles

Same as initial composition tests:
1. Inline test data via `backend_factory.create()`
2. Assert on executed results across all backends
3. xfail known backend limitations with clear messages
4. Each test exercises 1-3 methods, preferably in composition chains

### Test Categories Detail

#### 1. String Extended (`test_compose_string_extended.py`)

**Case conversion (2 tests):**
- `col("name").str.capitalize()` — verify first char uppercase
- `col("name").str.title()` then compare — title case conversion
- `col("name").str.swapcase()` — swap upper/lower
- `col("name").str.initcap()` — capitalize each word

**Trim variants (1 test):**
- `col("text").str.ltrim().str.rtrim()` — left/right trim chained

**Padding (2 tests):**
- `col("code").str.lpad(5, "0")` — left pad with zeros
- `col("code").str.rpad(10, ".")` — right pad
- `col("name").str.center(20, "-")` — center with fill char

**Extraction (2 tests):**
- `col("name").str.left(3)` then `col("name").str.right(3)` — extract from both ends
- `col("text").str.replace_slice(0, 3, "XXX")` — replace portion
- `col("text").str.slice(1, 3)` — extract substring

**Search (2 tests):**
- `col("text").str.strpos("x")` — find position of substring
- `col("text").str.count_substring("a")` — count occurrences

**Info (1 test):**
- `col("text").str.bit_length()` and `col("text").str.octet_length()` — byte-level info

**Manipulation (3 tests):**
- `col("a").str.concat(col("b"))` — concatenate two columns
- `col("a").str.concat_ws("-", col("b"), col("c"))` — concat with separator
- `col("text").str.repeat(3)` — repeat string
- `col("text").str.reverse()` — reverse string

**Regex (3 tests):**
- `col("text").str.regexp_match_substring(pattern)` — extract regex match
- `col("text").str.regexp_replace(pattern, replacement)` — regex replace
- `col("text").str.regex_match(pattern)` and `regex_contains` — convenience aliases
- `col("text").str.regexp_count_substring(pattern)` — count regex matches
- `col("text").str.regexp_strpos(pattern)` — find regex position

**Split (1 test):**
- `col("text").str.string_split(",")` — split by delimiter

#### 2. Datetime Extended (`test_compose_datetime_extended.py`)

**Sub-second extraction (1 test):**
- `col("ts").dt.millisecond()`, `.microsecond()`, `.nanosecond()` — extract sub-second components

**Calendar extraction (2 tests):**
- `col("ts").dt.quarter()`, `.day_of_year()` — calendar components
- `col("ts").dt.day_of_week()`, `.week_of_year()`, `.iso_year()` — week-based

**Special extraction (1 test):**
- `col("ts").dt.unix_timestamp()` — epoch seconds
- `col("ts").dt.timezone_offset()` — timezone info

**Boolean extraction (1 test):**
- `col("ts").dt.is_leap_year()` — leap year check
- `col("ts").dt.is_dst()` — daylight saving time

**Sub-day arithmetic (1 test):**
- `col("ts").dt.add_milliseconds(500)`, `.add_microseconds(1000)` — sub-second adds

**Calendar arithmetic (1 test):**
- `col("ts").dt.add_years(1)`, `.add_months(6)` — calendar intervals

**Diff operations (2 tests):**
- `col("a").dt.diff_years(col("b"))`, `.diff_months(col("b"))` — date diffs
- `col("a").dt.diff_days(col("b"))`, `.diff_seconds(col("b"))` — time diffs

**Rounding (1 test):**
- `col("ts").dt.round("hour")`, `.ceil("day")`, `.floor("day")` — temporal rounding

**Timezone + formatting (1 test):**
- `col("ts").dt.to_timezone("UTC")`, `.assume_timezone("UTC")`, `.strftime("%Y-%m-%d")` — timezone and format ops

**Offset (1 test):**
- `col("ts").dt.offset_by("1d2h")` — combined offset string

Known xfails: ibis-sqlite (all sub-day/interval ops), ibis-polars (calendar intervals, TimestampDelta).

#### 3. Comparison Extended (`test_compose_comparison_extended.py`)

**Between (1 test):**
- `col("score").between(60, 90)` with literal bounds (avoids the `closed` kwarg bug with column refs on Ibis)

**Truth tests (2 tests):**
- `col("flag").is_true()`, `.is_not_true()` — truth value checks
- `col("flag").is_false()`, `.is_not_false()` — false value checks

**Numeric tests (1 test):**
- `col("val").is_nan()`, `.is_finite()`, `.is_infinite()` — float classification

**Null/coalesce method form (1 test):**
- `col("a").nullif(0)` — nullif via comparison builder

**Min/max (2 tests):**
- `col("a").least(col("b"))`, `.greatest(col("b"))` — pairwise min/max
- `col("a").least_skip_null(col("b"))`, `.greatest_skip_null(col("b"))` — null-skipping variants

**Rounding (1 test):**
- `col("val").ceil()`, `.floor()` — rounding operations

**Logarithmic (2 tests):**
- `col("val").log()`, `.log10()`, `.log2()` — logarithms
- `col("val").ln()` — natural log (alias)

**Entrypoint coalesce method form (2 tests):**
- `coalesce(col("a"), col("b"), lit(0))` — already partially covered but method-form on comparison builder is not

#### 4. Arithmetic Extended (`test_compose_arithmetic_extended.py`)

**Math functions (2 tests):**
- `col("val").sqrt()`, `.abs()`, `.sign()` — basic math
- `col("val").exp()` — exponential

**Trig (2 tests):**
- `col("angle").sin()`, `.cos()`, `.tan()` — basic trig
- `col("val").asin()`, `.acos()`, `.atan()`, `.atan2(col("b"))` — inverse trig

**Hyperbolic (1 test):**
- `col("val").sinh()`, `.cosh()`, `.tanh()` — hyperbolic functions
- `col("val").asinh()`, `.acosh()`, `.atanh()` — inverse hyperbolic

**Angle conversion (1 test):**
- `col("deg").radians()`, `col("rad").degrees()` — angle conversion

**Factorial (1 test):**
- `col("n").factorial()` — factorial

**Bitwise (2 tests):**
- `col("a").bitwise_and(col("b"))`, `.bitwise_or(col("b"))`, `.bitwise_xor(col("b"))` — bitwise binary ops
- `col("a").bitwise_not()`, `.shift_left(2)`, `.shift_right(1)` — bitwise unary + shifts

#### 5. Ternary Extended (`test_compose_ternary_extended.py`)

**Ternary set (1 test):**
- `col("val").t_is_in([1, 2, 3])` — ternary set membership
- `col("val").t_is_not_in([4, 5])` — ternary set exclusion

**Ternary multi-arg logic (1 test):**
- `col("a").t_and(col("b"), col("c"))` — variadic t_and
- `col("a").t_or(col("b"), col("c"))` — variadic t_or

**Ternary xor (1 test):**
- `col("a").t_xor(col("b"))` — ternary exclusive or

**Ternary xor_parity (1 test):**
- `col("a").t_xor_parity(col("b"), col("c"))` — odd number of TRUEs

## Backend xfail expectations

| Backend | Expected xfails |
|---------|----------------|
| ibis-sqlite | Datetime sub-day ops, timezone, intervals, some string regex |
| ibis-polars | Calendar intervals (add_years/months), TimestampDelta, LIKE |
| ibis-duckdb | Possible trig/bitwise edge cases |
| pandas | Some datetime, conditional operations |

All xfails get clear messages explaining the backend limitation.
