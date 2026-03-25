# Polars API Alignment Audit

> **For agentic workers:** This is a reference/roadmap document, not an implementation plan. Use this to inform future spec/plan cycles for individual feature batches.

**Goal:** Comprehensive comparison of the mountainash-expressions public API against the Polars Expression API (v1.36.1), identifying naming gaps, missing features, and a prioritized roadmap for alignment.

**Approach:** Substrait-first with Polars aliases. Our Substrait-aligned names remain canonical; Polars-compatible aliases are added where they differ. Feature gaps are catalogued but not implemented in this spec — each batch gets its own spec/plan cycle.

**Scope:** Cross-backend essentials only. Operations that only make sense in a single-backend context (rolling, EWM, cumulative, sampling, ranking) are marked out-of-scope.

---

## Status Legend

| Status | Meaning |
|--------|---------|
| `aligned` | Method exists with matching or compatible name |
| `name-differs` | Method exists but name differs from Polars convention |
| `aspirational` | Builder method exists but enum/backend alignment needed |
| `missing` | We don't have this operation at all |
| `out-of-scope` | Polars-specific, not cross-backend essential |
| `we-only` | We have it, Polars doesn't |

---

## 1. Flat Namespace — Comparison

| Polars Method | Our Method | Status | Naming Gap | Signature Gap |
|---|---|---|---|---|
| `eq(other)` | `equal(other)` / `eq` alias | aligned | `eq` alias exists | -- |
| `eq_missing(other)` | -- | missing | -- | None==None returns True |
| `ne(other)` | `not_equal(other)` / `ne` alias | aligned | `ne` alias exists | -- |
| `ne_missing(other)` | -- | missing | -- | |
| `gt(other)` | `gt(other)` | aligned | -- | -- |
| `lt(other)` | `lt(other)` | aligned | -- | -- |
| `ge(other)` | `gte(other)` / `ge` alias | aligned | `ge` alias exists | -- |
| `le(other)` | `lte(other)` / `le` alias | aligned | `le` alias exists | -- |
| `is_between(low, high, closed)` | `between(low, high, closed)` | name-differs | Missing `is_` prefix | Known bug: `closed` kwarg passed to backends that reject it |
| `is_close(other, abs_tol, rel_tol)` | -- | aspirational | -- | Enum `IS_CLOSE` exists; API builder method and function mapping needed |
| `is_in(other)` | `is_in(*values)` | aligned | -- | Ours is variadic; Polars takes a single collection |
| `is_unique()` | -- | out-of-scope | -- | Aggregation-like |
| `is_null()` | `is_null()` | aligned | -- | -- |
| `is_not_null()` | `is_not_null()` | aligned | -- | -- |
| `is_nan()` | `is_nan()` | aligned | -- | -- |
| `is_not_nan()` | -- | missing | -- | See Section 5 (Null & NaN) |
| `is_finite()` | `is_finite()` | aligned | -- | -- |
| `is_infinite()` | `is_infinite()` | aligned | -- | -- |
| **Type Casting** | | | | |
| `cast(dtype, *, strict)` | `cast(dtype, failure_behavior)` | aligned | -- | Polars has `strict` bool; ours has `CastFailureBehaviour` enum |
| **Aliasing** | | | | |
| `alias(name)` | `.name.alias(name)` | aligned | Different location | Polars: flat on Expr. Ours: in `.name` namespace |

**We have but Polars doesn't (Mountainash extras):**
- `is_true()`, `is_not_true()`, `is_false()`, `is_not_false()` — Substrait truth-value checks
- `nullif(other)` — Substrait null_if
- `coalesce(*others)` — Also available as entrypoint `ma.coalesce()`
- `greatest()`, `least()`, `greatest_skip_null()`, `least_skip_null()` — Polars has these as top-level functions, not methods
- Full ternary comparison suite (`t_eq`, `t_gt`, etc.)

**Known bugs:**
- `between()`: `closed` kwarg passed to backends that reject it
- `least()` / `least_skip_null()`: builder references `LTEAST` / `LTEAST_SKIP_NULL` which don't exist as enum values — runtime `AttributeError` (broken, not just misnamed)

---

## 2. Flat Namespace — Boolean / Logical

| Polars Method | Our Method | Status | Naming Gap | Signature Gap |
|---|---|---|---|---|
| `and_(*others)` | `and_(*others)` | aligned | -- | -- |
| `or_(*others)` | `or_(*others)` | aligned | -- | -- |
| `not_()` | `not_()` | aligned | -- | -- |
| `xor(other)` | `xor(other)` / `xor_` alias | aligned | -- | -- |
| `any(*, ignore_nulls)` | -- | out-of-scope | -- | Aggregation |
| `all(*, ignore_nulls)` | -- | out-of-scope | -- | Aggregation |

**We have but Polars doesn't:**
- `and_not(other)` — Substrait-specific
- `xor_parity(*others)` — Mountainash extension (odd number of TRUEs)
- `always_true()`, `always_false()` — Constant constructors
- Full ternary logic suite (`t_and`, `t_or`, `t_not`, `t_xor`, booleanizers)

---

## 3. Flat Namespace — Arithmetic

| Polars Method | Our Method | Status | Naming Gap | Signature Gap |
|---|---|---|---|---|
| `add(other)` | `add(other)` | aligned | -- | -- |
| `sub(other)` | `subtract(other)` | name-differs | Polars: `sub` | Add `sub` alias |
| `mul(other)` | `multiply(other)` | name-differs | Polars: `mul` | Add `mul` alias |
| `truediv(other)` | `divide(other)` | name-differs | Polars: `truediv` | Add `truediv` alias |
| `floordiv(other)` | `floor_divide(other)` | name-differs | Polars: `floordiv` | Add `floordiv` alias |
| `mod(other)` | `modulus(other)` / `modulo` alias | name-differs | Polars: `mod` | Add `mod` alias |
| `pow(exponent)` | `power(other)` | name-differs | Polars: `pow` | Add `pow` alias |
| `neg()` | -- | aspirational | -- | Enum `NEGATE` exists, builder/backends commented out. `__neg__` calls `self.negate()` which is commented out — runtime bug. Uncomment and wire. |
| `abs()` | `abs()` | aspirational | -- | Enum missing, needs backend alignment |
| `sign()` | `sign()` | aspirational | -- | Enum missing, needs backend alignment |
| `sqrt()` | `sqrt()` | aspirational | -- | Enum missing, needs backend alignment |
| `exp()` | `exp()` | aspirational | -- | Enum missing, needs backend alignment |
| `clip(lower, upper)` | -- | missing | -- | Cross-backend feasible |
| `dot(other)` | -- | out-of-scope | -- | Aggregation-like |
| `product()` | -- | out-of-scope | -- | Aggregation |

### Trig / Hyperbolic (aspirational)

16 Polars trig/hyperbolic methods (`sin`, `cos`, `tan`, `cot`, `arcsin`, `arccos`, `arctan`, `arctan2`, `sinh`, `cosh`, `tanh`, `arcsinh`, `arccosh`, `arctanh`, `degrees`, `radians`) have corresponding aspirational builder methods in our API (except `cot` which we lack). Naming difference: Polars uses `arcsin`/`arccos`/`arctan`; we use `asin`/`acos`/`atan` (Substrait naming). All need enum + function mapping + backend alignment.

**We have but Polars doesn't:**
- `rsubtract()`, `rdivide()`, `rmodulus()`, `rpower()`, `rfloor_divide()` — Reverse operators for Python `__rsub__` etc.

---

## 4. Flat Namespace — Rounding & Logarithmic

| Polars Method | Our Method | Status | Naming Gap | Signature Gap |
|---|---|---|---|---|
| `round(decimals, mode)` | `round(decimals)` | aligned | -- | Polars has `mode` param (rounding strategy) |
| `ceil()` | `ceil()` | aligned | -- | -- |
| `floor()` | `floor()` | aligned | -- | -- |
| `round_sig_figs(digits)` | -- | missing | -- | Niche, low priority |
| `log(base)` | `log(base)` | aligned | -- | -- |
| `log10()` | `log10()` | aligned | -- | -- |
| `log1p()` | -- | missing | -- | Cross-backend feasible |
| -- | `log2()` | we-only | -- | We have dedicated log2; Polars uses `log(2)` |
| -- | `ln()` | we-only | -- | Maps to `log` with base=e |

---

## 5. Flat Namespace — Null & NaN Handling

| Polars Method | Our Method | Status | Naming Gap | Signature Gap |
|---|---|---|---|---|
| `fill_null(value, strategy, limit)` | `fill_null(replacement)` | aligned | -- | Polars has `strategy` and `limit` params |
| `drop_nulls()` | -- | missing | -- | Cross-backend feasible |
| `forward_fill(limit)` | -- | missing | -- | Cross-backend feasible |
| `backward_fill(limit)` | -- | missing | -- | Cross-backend feasible |
| `has_nulls()` | -- | out-of-scope | -- | Aggregation |
| `null_count()` | -- | out-of-scope | -- | Aggregation |
| `fill_nan(value)` | -- | missing | -- | Cross-backend feasible |
| `is_not_nan()` | -- | missing | -- | Trivial: `not_(is_nan())` |
| `drop_nans()` | -- | missing | -- | Cross-backend feasible |

**We have but Polars doesn't:**
- `null_if(other)` — Substrait operation (return null if value equals sentinel)

---

## 6. `.str` Namespace — String Operations

| Polars Method | Our Method | Status | Naming Gap | Signature Gap |
|---|---|---|---|---|
| `to_uppercase()` | `upper()` | name-differs | Substrait naming | Add `to_uppercase` alias |
| `to_lowercase()` | `lower()` | name-differs | Substrait naming | Add `to_lowercase` alias |
| `to_titlecase()` | `title()` | name-differs | Substrait naming | `title` aspirational (enum missing) |
| `strip_chars(chars)` | `trim(characters)` | name-differs | Substrait naming | Add `strip_chars` alias |
| `strip_chars_start(chars)` | `ltrim(characters)` | name-differs | Substrait naming | Add `strip_chars_start` alias |
| `strip_chars_end(chars)` | `rtrim(characters)` | name-differs | Substrait naming | Add `strip_chars_end` alias |
| `strip_prefix(prefix)` | -- | missing | -- | Cross-backend feasible |
| `strip_suffix(suffix)` | -- | missing | -- | Cross-backend feasible |
| `pad_start(length, fill_char)` | `lpad(length, characters)` | name-differs | Substrait naming | `lpad` aspirational (enum missing) |
| `pad_end(length, fill_char)` | `rpad(length, characters)` | name-differs | Substrait naming | `rpad` aspirational (enum missing) |
| `zfill(length)` | -- | missing | -- | Convenience over `pad_start` |
| `contains(pattern, literal)` | `contains(substring, case_sensitive)` | aligned | -- | Different semantics: Polars defaults to regex, ours to literal. Polars has `literal` flag; ours has `case_sensitive` |
| `contains_any(patterns)` | -- | out-of-scope | -- | Polars-specific Aho-Corasick |
| `starts_with(prefix)` | `starts_with(prefix, case_sensitive)` | aligned | -- | We have extra `case_sensitive` param |
| `ends_with(suffix)` | `ends_with(suffix, case_sensitive)` | aligned | -- | We have extra `case_sensitive` param |
| `find(pattern)` | `strpos(substring, case_sensitive)` | name-differs | Substrait: `strpos` | `strpos` aspirational. Add `find` alias when implemented |
| `find_many(patterns)` | -- | out-of-scope | -- | Polars-specific Aho-Corasick |
| `replace(pattern, value, literal, n)` | `replace(old, new, case_sensitive)` | aligned | -- | Polars has `n` (max replacements) and `literal` flag; ours has `case_sensitive` |
| `replace_all(pattern, value, literal)` | -- | missing | -- | Polars separates replace/replace_all; ours replaces all by default |
| `replace_many(patterns)` | -- | out-of-scope | -- | Polars-specific Aho-Corasick |
| `slice(offset, length)` | `slice(offset, length)` / `substring(start, length)` | aligned | -- | -- |
| `head(n)` | `left(count)` | name-differs | Substrait: `left` | `left` aspirational. Add `head` alias when implemented |
| `tail(n)` | `right(count)` | name-differs | Substrait: `right` | `right` aspirational. Add `tail` alias when implemented |
| `len_chars()` | `char_length()` / `length` / `len` | name-differs | Substrait naming | Add `len_chars` alias |
| `len_bytes()` | `octet_length()` | name-differs | Substrait naming | `octet_length` aspirational. Add `len_bytes` alias when implemented |
| `concat(delimiter)` | `concat(*others)` | aligned | -- | Different semantics: Polars vertical; ours horizontal |
| `join(delimiter)` | -- | out-of-scope | -- | Polars vertical join |
| `split(by)` | `string_split(separator)` | name-differs | Substrait naming | `string_split` aspirational. Add `split` alias when implemented |
| `split_exact(by, n)` | -- | missing | -- | Low priority |
| `splitn(by, n)` | -- | missing | -- | Low priority |
| `reverse()` | `reverse()` | aspirational | -- | Enum missing, needs backend alignment |
| `explode()` | -- | out-of-scope | -- | Structural operation |
| `count_matches(pattern)` | `count_substring(substring, case_sensitive)` | name-differs | Substrait naming | `count_substring` aspirational. Add `count_matches` alias when implemented |
| `extract(pattern, group_index)` | `regexp_match_substring(pattern, ...)` | name-differs | Substrait naming | Ours has richer params |
| `extract_all(pattern)` | `regexp_match_substring_all(...)` | name-differs | Substrait naming | Aspirational |
| `extract_groups(pattern)` | -- | missing | -- | Low priority |
| `extract_many(patterns)` | -- | out-of-scope | -- | Polars-specific |
| `escape_regex()` | -- | missing | -- | Utility, low priority |
| `normalize(form)` | -- | missing | -- | Unicode, low priority |
| `encode(encoding)` | -- | out-of-scope | -- | Binary encoding |
| `decode(encoding)` | -- | out-of-scope | -- | Binary encoding |
| `strptime(dtype, format)` | -- | missing | -- | Parsing; cross-backend feasible |
| `to_date(format)` | -- | missing | -- | Convenience over strptime |
| `to_datetime(format)` | -- | missing | -- | Convenience over strptime |
| `to_time(format)` | -- | missing | -- | Convenience over strptime |
| `to_decimal(scale)` | -- | out-of-scope | -- | Type-specific |
| `to_integer(base)` | -- | missing | -- | Cross-backend feasible |
| `json_decode(dtype)` | -- | out-of-scope | -- | Polars-specific |
| `json_path_match(path)` | -- | out-of-scope | -- | Polars-specific |

**We have but Polars doesn't:**
- `like(pattern, case_sensitive)` — SQL LIKE pattern matching (Substrait)
- `regex_contains(pattern)` — Convenience alias
- `regex_match(pattern)` — Anchored full-string regex match
- `regex_replace(pattern, replacement)` — Convenience alias for `regexp_replace`
- `regexp_replace(pattern, replacement, ...)` — Richer params than Polars
- `center(length, character)` — Substrait center-pad
- `bit_length()` — Substrait bit-level length
- `concat_ws(separator, *others)` — Concat with separator
- `replace_slice(start, length, replacement)` — Positional replacement

---

## 7. `.dt` Namespace — Datetime Operations

| Polars Method | Our Method | Status | Naming Gap | Signature Gap |
|---|---|---|---|---|
| **Extraction** | | | | |
| `year()` | `year()` | aligned | -- | -- |
| `iso_year()` | `iso_year()` | aligned | -- | -- |
| `month()` | `month()` | aligned | -- | -- |
| `day()` | `day()` | aligned | -- | -- |
| `hour()` | `hour()` | aligned | -- | -- |
| `minute()` | `minute()` | aligned | -- | -- |
| `second(*, fractional)` | `second()` | aligned | -- | Polars has `fractional` param |
| `millisecond()` | `millisecond()` | aligned | -- | -- |
| `microsecond()` | `microsecond()` | aligned | -- | -- |
| `nanosecond()` | `nanosecond()` | aligned | -- | -- |
| `quarter()` | `quarter()` | aligned | -- | -- |
| `week()` | `week_of_year()` | name-differs | Polars: `week` | Add `week` alias |
| `weekday()` | `day_of_week()` | name-differs | Polars: `weekday` | Add `weekday` alias |
| `ordinal_day()` | `day_of_year()` | name-differs | Polars: `ordinal_day` | Add `ordinal_day` alias |
| `century()` | -- | missing | -- | Low priority |
| `millennium()` | -- | missing | -- | Low priority |
| **Component Access** | | | | |
| `date()` | -- | missing | -- | Extract date part; cross-backend feasible |
| `time()` | -- | missing | -- | Extract time part; cross-backend feasible |
| **Rounding / Truncation** | | | | |
| `round(every)` | `round(unit)` | aligned | -- | Polars uses duration string |
| `truncate(every)` | `truncate(unit)` | aligned | -- | Same |
| -- | `ceil(unit)` | we-only | -- | Ceil rounding |
| -- | `floor(unit)` | we-only | -- | Floor rounding |
| **Offsets** | | | | |
| `offset_by(by)` | `offset_by(offset)` | aligned | -- | -- |
| `add_business_days(n, week_mask, holidays)` | -- | missing | -- | Rich Polars feature |
| `month_start()` | -- | missing | -- | Cross-backend feasible |
| `month_end()` | -- | missing | -- | Cross-backend feasible |
| **Duration** | | | | |
| `total_days(*, fractional)` | -- | missing | -- | Polars operates on Duration dtype |
| `total_hours(*, fractional)` | -- | missing | -- | We use `diff_*()` instead |
| `total_minutes` thru `total_nanoseconds` | -- | missing | -- | Different design philosophy |
| **Timezone** | | | | |
| `convert_time_zone(tz)` | `to_timezone(tz)` | name-differs | Polars: `convert_time_zone` | Add alias |
| `replace_time_zone(tz, ambiguous, non_existent)` | `assume_timezone(tz)` | name-differs | Polars: `replace_time_zone` | Polars has richer error params |
| `base_utc_offset()` | -- | missing | -- | Low priority |
| `dst_offset()` | -- | missing | -- | Low priority |
| **Formatting** | | | | |
| `strftime(format)` | `strftime(format)` | aligned | -- | -- |
| `to_string(format)` | -- | missing | -- | Convenience over strftime |
| **Epoch** | | | | |
| `epoch(time_unit)` | `unix_timestamp()` | name-differs | Polars: `epoch` | Polars has `time_unit` param |
| `timestamp(time_unit)` | -- | missing | -- | Similar to epoch |
| **Calendar** | | | | |
| `days_in_month()` | -- | missing | -- | Cross-backend feasible |
| `is_leap_year()` | `is_leap_year()` | aligned | -- | -- |
| `is_business_day(week_mask, holidays)` | -- | missing | -- | Rich Polars feature |
| **Time Unit** | | | | |
| `cast_time_unit(tu)` | -- | out-of-scope | -- | Polars-specific |
| `with_time_unit(tu)` | -- | out-of-scope | -- | Polars-specific |
| **Combine** | | | | |
| `combine(time, time_unit)` | -- | missing | -- | Cross-backend feasible |
| `replace(*, year, month, ...)` | -- | missing | -- | Cross-backend feasible |

**We have but Polars doesn't:**
- `add_years/months/days/hours/minutes/seconds/milliseconds/microseconds()` — Explicit duration arithmetic
- `diff_years/months/days/hours/minutes/seconds()` — Column-to-column difference
- `timezone_offset()` — Direct offset extraction
- `is_dst(timezone)` — DST check
- `within_last()`, `older_than()`, `newer_than()`, `within_next()`, `between_last()` — Natural language temporal filters

**Design philosophy difference:** Polars uses a Duration dtype with `total_*()` extraction. We use explicit `add_*()` and `diff_*()` methods. Both are valid; ours is designed for cross-backend portability where not all backends have a Duration type.

---

## 8. `.name` Namespace

| Polars Method | Our Method | Status | Naming Gap | Signature Gap |
|---|---|---|---|---|
| `keep()` | -- | missing | -- | Identity naming |
| `prefix(prefix)` | `prefix(prefix)` | aligned | -- | -- |
| `suffix(suffix)` | `suffix(suffix)` | aligned | -- | -- |
| `map(function)` | -- | missing | -- | UDF-based; hard to serialize cross-backend |
| `replace(pattern, value)` | -- | missing | -- | Cross-backend feasible |
| `to_lowercase()` | `name_to_lower()` | name-differs | Polars: `to_lowercase` | Add alias |
| `to_uppercase()` | `name_to_upper()` | name-differs | Polars: `to_uppercase` | Add alias |
| `prefix_fields(prefix)` | -- | out-of-scope | -- | Struct-specific |
| `suffix_fields(suffix)` | -- | out-of-scope | -- | Struct-specific |
| `map_fields(function)` | -- | out-of-scope | -- | Struct-specific |

**We have but Polars doesn't (in .name namespace):**
- `alias(name)` — Polars has `alias()` on Expr directly, not in `.name`

---

## Summary Statistics

### By Status

| Status | Count | Note |
|--------|-------|------|
| aligned | ~60 | Approximate — will be validated during implementation |
| name-differs | ~28 | |
| aspirational | ~27 | Builder exists, enum/backend needed |
| missing | ~45 | |
| out-of-scope | ~30 | |
| we-only | ~35 | Mountainash extras Polars doesn't have |

*Counts are approximate and will be validated during implementation planning.*

### Naming Aliases Needed (quick wins — no backend work)

These are one-line class-level alias additions on existing working methods. **Important:** All Polars-compatible aliases must be defined in the **Mountainash extension** API builders, not in the Substrait builders — these aliases are not part of the Substrait standard.

**Arithmetic** (in `api_bldr_ext_ma_scalar_arithmetic.py`):
- `sub = subtract`
- `mul = multiply`
- `truediv = divide`
- `floordiv = floor_divide`
- `mod = modulus`
- `pow = power`

**String** (in `api_bldr_ext_ma_scalar_string.py`):
- `to_uppercase = upper`
- `to_lowercase = lower`
- `strip_chars = trim`
- `strip_chars_start = ltrim`
- `strip_chars_end = rtrim`
- `len_chars = char_length`

**Datetime** (in `api_bldr_ext_ma_scalar_datetime.py`):
- `week = week_of_year`
- `weekday = day_of_week`
- `ordinal_day = day_of_year`
- `convert_time_zone = to_timezone`
- `replace_time_zone = assume_timezone`
- `epoch = unix_timestamp`

**Name** (in `api_bldr_ext_ma_name.py`):
- `to_lowercase = name_to_lower`
- `to_uppercase = name_to_upper`

**Comparison** (in `api_bldr_ext_ma_scalar_comparison.py`):
- `is_between = between` — consider adding for Polars parity

---

## Prioritized Feature Roadmap

Features grouped by implementation batch, ordered by cross-backend feasibility and user value. Each batch requires its own spec/plan cycle following the full pipeline: **enum value → function mapping → backend implementations (Polars, Ibis, Narwhals) → API builder method → tests**.

### Batch 1: Arithmetic Essentials (highest value, cross-backend feasible)

| Operation | Polars | Backends | Notes |
|-----------|--------|----------|-------|
| `abs()` | `abs()` | All have native abs | Enum commented out — uncomment and wire |
| `sqrt()` | `sqrt()` | All have native sqrt | Enum commented out |
| `sign()` | `sign()` | Polars/Ibis native; Narwhals via numpy | Enum commented out |
| `exp()` | `exp()` | All have native exp | Enum commented out |
| `neg()` | `neg()` | All have native negate | Enum exists, builder/backends commented out. `__neg__` is broken — uncomment and wire |
| `clip(lower, upper)` | `clip(lower, upper)` | Cross-backend feasible via `when().then()` | New method |

### Batch 2: Null & NaN Handling

| Operation | Polars | Backends | Notes |
|-----------|--------|----------|-------|
| `is_not_nan()` | `is_not_nan()` | Trivial: `not_(is_nan())` | New enum + implementation OR convenience wrapper |
| `fill_nan(value)` | `fill_nan(value)` | Cross-backend feasible | New method |
| `drop_nulls()` | `drop_nulls()` | All backends support | New method |
| `forward_fill(limit)` | `forward_fill(limit)` | Polars/Ibis native; Narwhals likely | New method |
| `backward_fill(limit)` | `backward_fill(limit)` | Polars/Ibis native; Narwhals likely | New method |

### Batch 3: Aspirational Arithmetic (trig, bitwise)

Depends on Batch 1 establishing the enum/backend alignment pattern.

| Operation | Count | Notes |
|-----------|-------|-------|
| Trig functions | 10 (`sin`, `cos`, `tan`, `cot`, `asin`, `acos`, `atan`, `atan2`, `degrees`, `radians`) | Builder methods exist (except `cot`); need enums + backends |
| Hyperbolic functions | 6 (`sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`) | Same |
| Bitwise operations | 6 (`bitwise_and`, `bitwise_or`, `bitwise_xor`, `bitwise_not`, `shift_left`, `shift_right`) | Builder methods exist; need enums + backends |

### Batch 4: Aspirational String Operations

| Operation | Count | Notes |
|-----------|-------|-------|
| Case transforms | 3 (`swapcase`, `capitalize`, `initcap`/`title`) | Need enums |
| Padding | 3 (`lpad`, `rpad`, `center`) | Need enums |
| Substring ops | 4 (`left`, `right`, `strpos`, `count_substring`) | Need enums |
| Split/Join | 2 (`string_split`, `regexp_string_split`) | Need enums |
| Other | 5 (`repeat`, `reverse`, `concat`, `concat_ws`, `replace_slice`) | Need enums |
| Length variants | 2 (`bit_length`, `octet_length`) | Need enums |

### Batch 5: New String Features

| Operation | Polars | Notes |
|-----------|--------|-------|
| `strip_prefix(prefix)` | `strip_prefix(prefix)` | New method, cross-backend feasible |
| `strip_suffix(suffix)` | `strip_suffix(suffix)` | New method, cross-backend feasible |
| `to_integer(base)` | `to_integer(base)` | New method |
| `strptime(dtype, format)` | `strptime(dtype, format)` | String parsing to datetime |

### Batch 6: Datetime Enrichment

| Operation | Polars | Notes |
|-----------|--------|-------|
| `date()` | `date()` | Extract date component |
| `time()` | `time()` | Extract time component |
| `month_start()` | `month_start()` | Roll to first of month |
| `month_end()` | `month_end()` | Roll to last of month |
| `days_in_month()` | `days_in_month()` | Calendar helper |
| `combine(time)` | `combine(time, time_unit)` | Date + Time → Datetime |
| `replace(*, year, month, ...)` | `replace(...)` | Component replacement |

### Batch 7: Missing Comparison Features

| Operation | Polars | Notes |
|-----------|--------|-------|
| `eq_missing(other)` | `eq_missing(other)` | None==None returns True |
| `ne_missing(other)` | `ne_missing(other)` | Inverse |
| `is_close(other, abs_tol, rel_tol)` | `is_close(...)` | Enum exists; API builder method and function mapping needed |

### Bug Fixes (can be done anytime)

| Bug | Location | Fix |
|-----|----------|-----|
| `LTEAST` / `LTEAST_SKIP_NULL` typo | `api_bldr_scalar_comparison.py` | Change to `LEAST` / `LEAST_SKIP_NULL`. Currently broken — `AttributeError` at runtime |
| `between()` passes `closed` kwarg | `api_bldr_scalar_comparison.py` | Store in `options` dict, handle in backends |
| `is_false`/`is_true` shadowing | `_FLAT_NAMESPACES` ordering | Comparison builder's `is_false`/`is_true` shadowed by ternary builder priority |

---

## Out-of-Scope Polars Features

The following Polars capabilities were deliberately excluded from comparison as they are single-backend or structural operations not aligned with cross-backend expression evaluation:

| Category | Examples | Reason |
|----------|----------|--------|
| **Window functions** | `over(*partition_by)` | Polars-specific partition semantics |
| **Rolling / EWM** | `rolling_mean`, `ewm_mean`, etc. (26+ methods) | Stateful windowed computation |
| **Cumulative** | `cum_sum`, `cum_min`, `cum_max`, `cum_prod`, `cum_count` | Ordered accumulation |
| **Sorting / Indexing** | `sort`, `sort_by`, `arg_sort`, `gather`, `get`, `head`, `tail`, `slice` | Structural operations |
| **Aggregation** | `sum`, `mean`, `median`, `min`, `max`, `std`, `var`, `count`, `len`, `n_unique` | Aggregate reductions |
| **Unique / Duplicates** | `unique`, `is_duplicated`, `is_first_distinct` | Set-like operations |
| **Top-K** | `top_k`, `bottom_k` | Selection operations |
| **Binning** | `cut`, `qcut` | Discretization |
| **Statistics** | `entropy`, `skew`, `kurtosis` | Statistical measures |
| **UDFs** | `map_elements`, `map_batches`, `pipe` | User-defined functions; not serializable |
| **Interpolation** | `interpolate`, `interpolate_by` | Gap-filling |
| **Value replacement** | `replace`, `replace_strict` | Polars-specific replace semantics |
| **Structural** | `explode`, `implode`, `flatten`, `reshape`, `rechunk` | DataFrame structure operations |
| **Serialization** | `deserialize`, `from_json` | Polars-specific persistence |
| **Searching** | `arg_max`, `arg_min`, `search_sorted` | Index-returning operations |
| **Misc** | `shift`, `diff`, `sample`, `shuffle`, `hash`, `rank`, `rle` | Various Polars-specific operations |

These categories may be revisited in future if cross-backend support becomes feasible (e.g., window functions are a natural next frontier after the current roadmap).

---

## Design Philosophy Differences

### Duration Handling
- **Polars:** Duration is a first-class dtype. Subtract two datetimes → Duration. Then `total_days()`, `total_hours()` etc.
- **Us:** Explicit `diff_days(other)`, `diff_hours(other)` methods that return numeric values. This is more portable across backends that lack a Duration type.
- **Recommendation:** Keep our design. Add `total_*()` convenience aliases on Duration-like results only if/when we introduce Duration support.

### Null-Safe Comparison
- **Polars:** `eq_missing()` / `ne_missing()` where None==None is True.
- **Us:** Not implemented. Our ternary system (`t_eq`) handles null-awareness differently (returns UNKNOWN for null operands).
- **Recommendation:** Add `eq_missing`/`ne_missing` as they solve a different problem than ternary (structural equality vs. data validation).

### String Contains Semantics
- **Polars:** `contains(pattern, literal=False)` — defaults to regex.
- **Us:** `contains(substring, case_sensitive=True)` — defaults to literal match.
- **Recommendation:** Keep our literal-first default (safer). Document the difference. Consider adding a `literal` param for explicit control.

### Naming Convention
- **Polars:** Short names (`sub`, `mul`, `truediv`, `len_chars`, `strip_chars`).
- **Us:** Substrait-aligned names (`subtract`, `multiply`, `divide`, `char_length`, `trim`).
- **Recommendation:** Add Polars aliases as documented above. Both naming styles work.
