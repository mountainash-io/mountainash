# Substrait Function Type Alignment Plan

**Date:** 2025-12-30
**Status:** Planning

## Summary

The `generate_from_substrait.py` script has a fundamental flaw: it doesn't properly distinguish between scalar_functions, aggregate_functions, and window_functions. This leads to incorrect protocol generation and misaligned test expectations.

---

## Priority 1: Fix Generator Script

Before fixing protocol alignment, we must fix the generator that creates the protocols.

### Current Generator Issues

**File:** `scripts/generate_from_substrait.py`

**Problem 1: Scalar/Aggregate Conflation (Lines 207-228)**
```python
# Current: Parses scalar_functions correctly
for func_data in data.get("scalar_functions", []):
    ...
    functions.append(SubstraitFunction(..., category=category))  # e.g., "arithmetic"

# Current: Parses aggregate_functions with hack suffix
for func_data in data.get("aggregate_functions", []):
    ...
    functions.append(SubstraitFunction(..., category=f"{category}_agg"))  # e.g., "arithmetic_agg"
```

**Problem 2: Window Functions Missing**
```python
# MISSING: No parsing of window_functions at all!
# for func_data in data.get("window_functions", []):
#     ...
```

**Problem 3: Protocol Generation Skips Aggregates (Line 512)**
```python
if "_agg" in category:  # Skip aggregates for now
    continue
```

### Required Generator Changes

**1. Add FunctionType enum to track scalar/aggregate/window:**
```python
class FunctionType(Enum):
    SCALAR = "scalar"
    AGGREGATE = "aggregate"
    WINDOW = "window"
```

**2. Update SubstraitFunction dataclass:**
```python
@dataclass
class SubstraitFunction:
    name: str
    description: str
    category: str           # Domain: arithmetic, boolean, comparison, etc.
    function_type: FunctionType  # NEW: scalar, aggregate, or window
    extension_uri: str
    impls: list[SubstraitImpl]
```

**3. Update parse_yaml to extract all three function types:**
```python
def parse_yaml(content: str, category: str, extension_uri: str) -> list[SubstraitFunction]:
    data = yaml.safe_load(content)
    functions = []

    # Scalar functions
    for func_data in data.get("scalar_functions", []):
        functions.append(SubstraitFunction(
            ...,
            category=category,
            function_type=FunctionType.SCALAR,
        ))

    # Aggregate functions
    for func_data in data.get("aggregate_functions", []):
        functions.append(SubstraitFunction(
            ...,
            category=category,
            function_type=FunctionType.AGGREGATE,
        ))

    # Window functions
    for func_data in data.get("window_functions", []):
        functions.append(SubstraitFunction(
            ...,
            category=category,
            function_type=FunctionType.WINDOW,
        ))

    return functions
```

**4. Update code generation to group by function_type:**
- Generate separate enums: `SUBSTRAIT_ARITHMETIC_SCALAR`, `SUBSTRAIT_ARITHMETIC_AGGREGATE`, `SUBSTRAIT_ARITHMETIC_WINDOW`
- Generate separate protocols: `ScalarArithmeticProtocol`, `AggregateArithmeticProtocol`, `WindowArithmeticProtocol`
- Generate separate FunctionDefs grouped by type

**5. Update report to show function type breakdown:**
```markdown
## functions_arithmetic.yaml
- Scalar (21): add, subtract, multiply, ...
- Aggregate (12): sum, avg, min, max, ...
- Window (11): row_number, rank, ...
```

### Files to Modify

1. **Primary:** `scripts/generate_from_substrait.py`
   - Add FunctionType enum
   - Update SubstraitFunction dataclass
   - Update parse_yaml() to handle all 3 types
   - Update generate_enum() to include function_type in name
   - Update generate_protocol_class() to generate type-specific protocols
   - Remove the `if "_agg" in category: continue` hack
   - Update generate_report() to show type breakdown

2. **Regenerate:** Run updated script to regenerate all artifacts
   - `generated/enums.py`
   - `generated/protocols_generated.py`
   - `generated/definitions_generated.py`
   - `generated/SUBSTRAIT_FUNCTIONS.md`

---

## YAML Function Type Distribution (from cache)

| YAML File | scalar_functions | aggregate_functions | window_functions |
|-----------|-----------------|--------------------|--------------------|
| `functions_arithmetic.yaml` | ✅ line 4 | ✅ line 1046 | ✅ line 1716 (ONLY file with window!) |
| `functions_arithmetic_decimal.yaml` | ✅ line 4 | ✅ line 187 | ❌ |
| `functions_boolean.yaml` | ✅ line 4 | ✅ line 117 (bool_and, bool_or) | ❌ |
| `functions_comparison.yaml` | ✅ line 4 | ❌ | ❌ |
| `functions_datetime.yaml` | ✅ line 4 | ✅ line 1001 | ❌ |
| `functions_string.yaml` | ✅ line 4 | ✅ line 1563 (string_agg) | ❌ |
| `functions_geometry.yaml` | ✅ line 10 | ❌ | ❌ |
| `functions_logarithmic.yaml` | ✅ line 4 | ❌ | ❌ |
| `functions_rounding.yaml` | ✅ line 4 | ❌ | ❌ |
| `functions_rounding_decimal.yaml` | ✅ line 4 | ❌ | ❌ |
| `functions_set.yaml` | ✅ line 4 | ❌ | ❌ |
| `functions_aggregate_generic.yaml` | ❌ | ✅ line 4 | ❌ |
| `functions_aggregate_approx.yaml` | ❌ | ✅ line 4 | ❌ |
| `functions_aggregate_decimal_output.yaml` | ❌ | ✅ line 4 | ❌ |

**Key insight:** Window functions ONLY exist in `functions_arithmetic.yaml` (row_number, rank, dense_rank, etc.)

---

## Priority 2: Protocol Alignment (After Generator Fix)

### CRITICAL: Substrait Function Type Hierarchy

Substrait YAMLs distinguish THREE function types within each domain:

```
functions_arithmetic.yaml
├── scalar_functions (21)    → add, subtract, multiply, divide, power, modulus, negate, abs, sign, sqrt, exp, factorial, trig, bitwise
├── aggregate_functions (14) → sum, sum0, min, max, avg, std_dev, variance, mode, median, quantile, product, correlation
└── window_functions (11)    → row_number, rank, dense_rank, percent_rank, cume_dist, ntile, first_value, last_value, nth_value, lead, lag
```

**Current Issue:** The codebase has `scalar_aggregate` which conflates scalar and aggregate functions. This is incorrect terminology.

### Substrait Standard Functions by Category

| YAML File | Scalar Functions | Aggregate Functions | Window Functions |
|-----------|-----------------|---------------------|------------------|
| `functions_arithmetic.yaml` | add, subtract, multiply, divide, power, modulus, negate, abs, sign, sqrt, exp, factorial, sin, cos, tan, etc. (21+) | sum, sum0, min, max, avg, std_dev, variance, mode, median, quantile, product, corr (12) | row_number, rank, dense_rank, percent_rank, cume_dist, ntile, first_value, last_value, nth_value, lead, lag (11) |
| `functions_comparison.yaml` | equal, not_equal, lt, gt, lte, gte, between, is_null, is_not_null, is_nan, is_finite, is_infinite, is_true, is_false, nullif, coalesce, least, greatest | - | - |
| `functions_boolean.yaml` | and, or, not, xor, and_not (5) | **bool_and, bool_or** (2) | - |
| `functions_string.yaml` | concat, like, substring, replace, starts_with, ends_with, contains, lower, upper, trim, char_length, strpos, reverse, repeat | string_agg | - |
| `functions_datetime.yaml` | extract, add, subtract, strftime, strptime, lt, gt, lte, gte | min, max | - |
| `functions_rounding.yaml` | ceil, floor, round | - | - |
| `functions_logarithmic.yaml` | ln, log10, log2, logb, log1p | - | - |
| `functions_set.yaml` | index_in | - | - |
| `functions_aggregate_generic.yaml` | - | count, count_all, any_value | - |
| `functions_aggregate_approx.yaml` | - | approx_count_distinct | - |

### Summary: ALL Substrait Aggregate Functions

From all YAML files combined:
- **Arithmetic aggregates (12):** sum, sum0, avg, min, max, product, std_dev, variance, corr, mode, median, quantile
- **Boolean aggregates (2):** bool_and, bool_or
- **String aggregates (1):** string_agg
- **Datetime aggregates (2):** min, max (on temporal types)
- **Generic aggregates (3):** count, count_all, any_value
- **Approximate aggregates (1):** approx_count_distinct

**TOTAL: ~21 Substrait-standard aggregate functions**

---

## MountainAsh Extensions (Move to Extension Protocols)

NOT in Substrait specification:

| Category | Functions | Rationale |
|----------|-----------|-----------|
| **Arithmetic (Scalar)** | `floor_divide` | Substrait only has modulus, not floor division |
| **Boolean (Scalar)** | `xor_parity` | Substrait has xor (2-arg), not parity |
| **Datetime (Scalar)** | `add_days`, `add_hours`, `diff_days`, `diff_hours`, individual extractors (`year()`, `month()`, `day()`, etc.), `day_of_week`, `day_of_year`, `is_leap_year`, `truncate` | Substrait uses `extract(COMPONENT)` and `add(interval)` patterns |
| **Set (Scalar)** | `is_in`, `is_not_in` | Substrait's `index_in` returns position (i64), not boolean |
| **Aggregate** | `first`, `last`, `n_unique` | NOT in Substrait. NOTE: `median`, `std_dev`, `variance` ARE Substrait (in arithmetic aggregates) |
| **Null** | `fill_null` | Substrait uses `coalesce` |
| **Name** | `alias`, `prefix`, `suffix` | Not expression operations in Substrait |
| **Ternary** | All `t_*` operations | MountainAsh-specific three-valued logic |

### KEY INSIGHT: What IS in Substrait Aggregates

These aggregate functions ARE Substrait-standard (from `functions_arithmetic.yaml`):
- `sum`, `sum0`, `min`, `max`, `avg` (basic)
- `std_dev`, `variance`, `mode`, `median`, `quantile`, `product`, `corr` (statistical)

These aggregate functions are NOT in Substrait:
- `first`, `last` (window functions in Substrait: `first_value`, `last_value`)
- `n_unique` (Substrait has `approx_count_distinct`)
- `count_distinct` (not defined, only `count` and `approx_count_distinct`)

---

## User Decisions

1. **Datetime Approach:** ✅ **Option A: Strict Substrait Compliance**
   - Substrait protocol: Only `extract(component)`, `add(interval)`, `strftime`, `strptime`
   - MountainAsh extension: All convenience methods (`year()`, `month()`, `add_days()`, `diff_hours()`, etc.)

2. **Set Operations:** ✅ **Match Substrait Interface**
   - Substrait protocol: `index_in` returning position (i64)
   - MountainAsh extension: `is_in`, `is_not_in` (boolean semantics) as wrappers

3. **Scope:** ✅ **Full Refactor**
   - Execute all phases to achieve clean Substrait/MountainAsh separation

4. **Aggregate Naming:** ✅ **Rename scalar_aggregate → aggregate**
   - Substrait distinguishes scalar/aggregate/window - align with this

---

## Execution Plan

### Phase 1: Fix Generator Script
1. Add FunctionType enum (SCALAR, AGGREGATE, WINDOW)
2. Update SubstraitFunction dataclass with function_type field
3. Update parse_yaml() to parse all three function type sections
4. Update code generation to group by function_type
5. Remove the `if "_agg" in category` hack
6. Regenerate all artifacts

### Phase 2: Fix Signature Mismatches (Quick Wins)

**Files to modify:**
- `prtcl_expsys_scalar_boolean.py`
  - Change `and_(a)` → `and_(*args)`
  - Change `or_(a)` → `or_(*args)`
- `prtcl_expsys_scalar_comparison.py`
  - Change `coalesce(arg)` → `coalesce(*args)`
  - Change `greatest(arg)` → `greatest(*args)`
  - Change `greatest_skip_null(arg)` → `greatest_skip_null(*args)`
  - Change `least(arg)` → `least(*args)`
  - Change `least_skip_null(arg)` → `least_skip_null(*args)`

### Phase 3: Move Misplaced Methods

**3.1 floor_divide (Arithmetic)**
- Remove from Substrait implementations (if present)
- Ensure only in MountainAsh extension protocol/implementations

**3.2 xor_parity (Boolean)**
- Remove from Substrait implementations (if present)
- Ensure only in MountainAsh extension protocol/implementations

**3.3 is_in/is_not_in → index_in (Set)**
- Add `index_in` to Substrait protocol (returns i64 position)
- Move `is_in`/`is_not_in` to MountainAsh extension (boolean wrappers)
- Update backend implementations

### Phase 4: Datetime Refactor

**4.1 Substrait Protocol** - Keep only:
- `extract(component: DatetimeComponent, value)` → returns extracted part
- `add(value, interval)` → adds interval to datetime
- `subtract(value, interval)` → subtracts interval
- `strftime(value, format)` → format to string
- `strptime(value, format)` → parse from string

**4.2 MountainAsh Extension** - Move all convenience methods:
- Individual extractors: `year()`, `month()`, `day()`, `hour()`, `minute()`, `second()`, `microsecond()`, `millisecond()`, `quarter()`, `week()`
- Day variants: `day_of_week()`, `day_of_year()`
- Add methods: `add_days()`, `add_hours()`, `add_minutes()`, `add_seconds()`, `add_months()`, `add_years()`
- Diff methods: `diff_days()`, `diff_hours()`, `diff_minutes()`, `diff_seconds()`, `diff_months()`, `diff_years()`
- Other: `truncate()`, `floor()`, `ceil()`, `is_leap_year()`, `assume_timezone()`

**4.3 Create DatetimeComponent Enum:**
```python
class DatetimeComponent(Enum):
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"
    MICROSECOND = "microsecond"
    MILLISECOND = "millisecond"
    QUARTER = "quarter"
    WEEK = "week"
    DAY_OF_WEEK = "day_of_week"
    DAY_OF_YEAR = "day_of_year"
```

### Phase 5: Aggregate Functions

**IMPORTANT:** The current `scalar_aggregate` naming is misleading. RENAME to `aggregate_*`.

**5.1 Substrait Aggregate Protocol** - These ARE Substrait standard (~21 total):

From `functions_aggregate_generic.yaml`:
- `count()`, `count_all()`, `any_value()`

From `functions_arithmetic.yaml` (aggregate_functions section):
- `sum()`, `sum0()` (sum with zero default)
- `min()`, `max()`
- `avg()` (not `mean`)
- `std_dev()`, `variance()`
- `median()`, `mode()`, `quantile()`
- `product()`, `corr()`

From `functions_boolean.yaml` (aggregate_functions section):
- `bool_and()` - Returns false if any input is false
- `bool_or()` - Returns true if any input is true

From `functions_string.yaml`:
- `string_agg()` - Concatenate strings with separator

From `functions_aggregate_approx.yaml`:
- `approx_count_distinct()`

**5.2 MountainAsh Aggregate Extension** - NOT in Substrait:
- `first()`, `last()` (Substrait has these as WINDOW functions: `first_value`, `last_value`)
- `n_unique()` (exact count distinct - Substrait only has approximate)
- `mean()` (alias for `avg` if desired)

**5.3 Window Functions** (Future consideration):
Substrait defines these as window_functions, not aggregate_functions:
- `row_number()`, `rank()`, `dense_rank()`
- `percent_rank()`, `cume_dist()`, `ntile()`
- `first_value()`, `last_value()`, `nth_value()`
- `lead()`, `lag()`

### Phase 6: Update Backend Implementations

For each of Polars, Ibis, Narwhals:
1. Move methods between substrait/ and extensions_mountainash/ directories
2. Ensure protocol compliance
3. Update __init__.py exports

### Phase 7: Update APIBuilder Layer

Mirror changes from ExpressionSystem layer to APIBuilder protocols and implementations.

---

## Critical Files List

### Generator Script
```
scripts/generate_from_substrait.py
scripts/.substrait_cache/*.yaml
```

### Protocols to Modify
```
src/mountainash_expressions/core/expression_protocols/expression_systems/substrait/
├── prtcl_expsys_scalar_aggregate.py     # RENAME → prtcl_expsys_aggregate.py + add Substrait aggregates
├── prtcl_expsys_scalar_arithmetic.py    # Verify no floor_divide
├── prtcl_expsys_scalar_boolean.py       # Fix and_/or_ signatures, remove xor_parity
├── prtcl_expsys_scalar_comparison.py    # Fix variadic signatures
├── prtcl_expsys_scalar_datetime.py      # Reduce to extract/add/subtract/strftime/strptime
├── prtcl_expsys_scalar_set.py           # Add index_in, remove is_in/is_not_in

src/mountainash_expressions/core/expression_protocols/expression_systems/extensions_mountainash/
├── prtcl_expsys_ext_ma_aggregate.py         # NEW: first, last, n_unique, mean (alias)
├── prtcl_expsys_ext_ma_scalar_arithmetic.py # Verify floor_divide present
├── prtcl_expsys_ext_ma_scalar_boolean.py    # Verify xor_parity present
├── prtcl_expsys_ext_ma_scalar_datetime.py   # Add all convenience methods
├── prtcl_expsys_ext_ma_scalar_set.py        # NEW: is_in, is_not_in
```

### Renames Required (scalar_aggregate → aggregate)
Files to rename across all layers:
- Protocols: `prtcl_expsys_scalar_aggregate.py` → `prtcl_expsys_aggregate.py`
- Backends (x3): `expsys_{pl,ib,nw}_scalar_aggregate.py` → `expsys_{pl,ib,nw}_aggregate.py`
- API Builders: `api_bldr_scalar_aggregate.py` → `api_bldr_aggregate.py`
- Classes: `SubstraitScalarAggregate*` → `SubstraitAggregate*`

### Backend Implementations (× 3 backends)
```
src/mountainash_expressions/backends/expression_systems/{polars,ibis,narwhals}/
├── substrait/
│   ├── expsys_{pl,ib,nw}_scalar_aggregate.py
│   ├── expsys_{pl,ib,nw}_scalar_boolean.py
│   ├── expsys_{pl,ib,nw}_scalar_comparison.py
│   ├── expsys_{pl,ib,nw}_scalar_datetime.py
│   └── expsys_{pl,ib,nw}_scalar_set.py
└── extensions_mountainash/
    ├── expsys_{pl,ib,nw}_ext_ma_scalar_aggregate.py  # NEW
    ├── expsys_{pl,ib,nw}_ext_ma_scalar_datetime.py
    └── expsys_{pl,ib,nw}_ext_ma_scalar_set.py        # NEW
```

### APIBuilder Layer (Mirror structure)
```
src/mountainash_expressions/core/expression_api/api_builders/substrait/
src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/
src/mountainash_expressions/core/expression_protocols/api_builders/substrait/
src/mountainash_expressions/core/expression_protocols/api_builders/extensions_mountainash/
```

---

## References

- Substrait Specification: https://substrait.io
- Extension YAMLs: https://github.com/substrait-io/substrait/tree/main/extensions
- ADR-008: Substrait Extension Alignment
