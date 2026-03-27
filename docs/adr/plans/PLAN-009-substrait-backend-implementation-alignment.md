# PLAN-009: Substrait Protocol Backend Alignment Implementation Plan

## GitHub Tracking

- **Milestone**: [Substrait Backend Implementation Alignment](https://github.com/mountainash-io/mountainash-expressions/milestone/8) (Due: 2026-03-31)
- **ADR**: [ADR-009-substrait-backend-implementation-alignment.md](../ADR-009-substrait-backend-implementation-alignment.md)
- **Project**: [Mountain Ash - Data Framework](https://github.com/orgs/mountainash-io/projects/8)

### Phase Issues & Project Tasks

| Phase | Issue | Priority | Status | Methods |
|-------|-------|----------|--------|---------|
| 1. Fix Protocol Signatures | [#53](https://github.com/mountainash-io/mountainash-expressions/issues/53) | P0 | Backlog | 5 fixes |
| 2. Complete scalar_comparison | [#54](https://github.com/mountainash-io/mountainash-expressions/issues/54) | P0 | Backlog | +6 |
| 3. Expand scalar_arithmetic | [#55](https://github.com/mountainash-io/mountainash-expressions/issues/55) | P0 | Backlog | +78 |
| 4. Complete scalar_logarithmic | [#56](https://github.com/mountainash-io/mountainash-expressions/issues/56) | P1 | Backlog | +6 |
| 5. Expand scalar_datetime | [#57](https://github.com/mountainash-io/mountainash-expressions/issues/57) | P1 | Backlog | +39 |
| 6. Add Aggregate Protocols | [#58](https://github.com/mountainash-io/mountainash-expressions/issues/58) | P1 | Backlog | +51 |
| 7. Add Window Protocol | [#59](https://github.com/mountainash-io/mountainash-expressions/issues/59) | P2 | Backlog | +36 |
| 8. Add Geometry Protocol Stubs | [#60](https://github.com/mountainash-io/mountainash-expressions/issues/60) | P2 | Backlog | +54 |

---

## Overview

Align all three backends (Polars, Ibis, Narwhals) with the 18 Substrait expression system protocols.

- **Total Protocol Methods**: ~177 methods across 18 protocols
- **Current Coverage**: ~35%
- **Scope**: Complete implementation including aggregates and window functions
- **Fallback Strategy**: `NotImplementedError` for unsupported operations

---

## Current State Summary

| Category | Protocols | Methods | Polars | Ibis | Narwhals |
|----------|-----------|---------|--------|------|----------|
| Foundation | 4 | 4 | Complete | Complete | Complete |
| Scalar | 9 | 127 | ~40% | ~35% | ~35% |
| Aggregate | 4 | 17 | Missing | Missing | Missing |
| Window | 1 | 12 | Missing | Missing | Missing |

---

## Implementation Phases

### Phase 1: Fix Protocol Signatures
**Priority: P0 (Critical) | Effort: Small**

Fix variadic signatures in protocol (implementations are correct):

**File**: `src/mountainash_expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_scalar_comparison.py`

```python
# Change from:
def coalesce(self, arg: SupportedExpressions) -> SupportedExpressions:
# To:
def coalesce(self, *args: SupportedExpressions) -> SupportedExpressions:
```

Same fix for: `least`, `greatest`, `least_skip_null`, `greatest_skip_null`

---

### Phase 2: Complete scalar_comparison
**Priority: P0 (Critical) | Effort: Small | +6 methods**

Add missing `is_distinct_from` and `is_not_distinct_from` to all backends:

| File | Implementation |
|------|----------------|
| `backends/.../polars/substrait/expsys_pl_scalar_comparison.py` | `x.eq(y).fill_null(x.is_null() & y.is_null())` |
| `backends/.../ibis/substrait/expsys_ib_scalar_comparison.py` | `ibis.ifelse(x.isnull() & y.isnull(), True, x == y)` |
| `backends/.../narwhals/substrait/expsys_nw_scalar_comparison.py` | `nw.when(x.is_null() & y.is_null()).then(True).otherwise(x == y)` |

---

### Phase 3: Expand scalar_arithmetic
**Priority: P0 (Critical) | Effort: Large | +78 methods (26 per backend)**

Add 26 missing methods to each backend:

**Methods to add:**
- Math: `sqrt`, `exp`, `abs`, `sign`, `factorial`
- Trig: `sin`, `cos`, `tan`, `sinh`, `cosh`, `tanh`, `asin`, `acos`, `atan`, `asinh`, `acosh`, `atanh`, `atan2`
- Angular: `radians`, `degrees`
- Bitwise: `bitwise_not`, `bitwise_and`, `bitwise_or`, `bitwise_xor`, `shift_left`, `shift_right`, `shift_right_unsigned`

**Files to modify:**
- `backends/.../polars/substrait/expsys_pl_scalar_arithmetic.py`
- `backends/.../ibis/substrait/expsys_ib_scalar_arithmetic.py`
- `backends/.../narwhals/substrait/expsys_nw_scalar_arithmetic.py`

**Backend Support Matrix:**

| Method | Polars | Ibis | Narwhals |
|--------|--------|------|----------|
| `sqrt` | `x.sqrt()` | `x.sqrt()` | NotImplementedError |
| `exp` | `x.exp()` | `x.exp()` | NotImplementedError |
| `abs` | `x.abs()` | `x.abs()` | `x.abs()` |
| `sign` | `x.sign()` | `x.sign()` | NotImplementedError |
| `factorial` | NotImplementedError | NotImplementedError | NotImplementedError |
| `sin`/`cos`/`tan` | `x.sin()` etc | `x.sin()` etc | NotImplementedError |
| `asin`/`acos`/`atan` | `x.arcsin()` etc | `x.asin()` etc | NotImplementedError |
| Hyperbolic | `x.sinh()` etc | `x.sinh()` etc | NotImplementedError |
| `atan2` | `x.arctan2(y)` | `x.atan2(y)` | NotImplementedError |
| `radians`/`degrees` | `x.radians()` | `x.radians()` | NotImplementedError |
| Bitwise ops | `x & y` etc | `x & y` etc | NotImplementedError |
| Shift ops | NotImplementedError | NotImplementedError | NotImplementedError |

**Also:** Move `floor_divide` from these files to MountainAsh extension files.

---

### Phase 4: Complete scalar_logarithmic
**Priority: P1 (High) | Effort: Small | +6 methods**

Add `logb` and `log1p`:

| File | `logb` | `log1p` |
|------|--------|---------|
| `expsys_pl_scalar_logarithmic.py` | `x.log(base)` | `(x + 1).log()` |
| `expsys_ib_scalar_logarithmic.py` | `x.log(base)` | `(x + 1).log()` |
| `expsys_nw_scalar_logarithmic.py` | NotImplementedError | NotImplementedError |

---

### Phase 5: Expand scalar_datetime
**Priority: P1 (High) | Effort: Medium | +39 methods**

Add 13 missing methods per backend:

**Methods to add:**
- `extract_boolean` (is_leap_year, is_dst)
- `multiply` (interval * int)
- `add_intervals`
- Comparisons: `lt`, `lte`, `gt`, `gte`
- Timezone: `assume_timezone`, `local_timestamp`
- Parsing: `strptime_time`, `strptime_date`, `strptime_timestamp`
- Formatting: `strftime`
- Rounding: `round_temporal`, `round_calendar`

**Files:**
- `backends/.../polars/substrait/expsys_pl_scalar_datetime.py`
- `backends/.../ibis/substrait/expsys_ib_scalar_datetime.py`
- `backends/.../narwhals/substrait/expsys_nw_scalar_datetime.py`

---

### Phase 6: Add Aggregate Protocols
**Priority: P1 (High) | Effort: Medium | +51 methods | 12 new files**

Create new implementation files for all aggregate protocols:

**New files per backend (4 each = 12 total):**
```
backends/.../polars/substrait/expsys_pl_aggregate_generic.py
backends/.../polars/substrait/expsys_pl_aggregate_boolean.py
backends/.../polars/substrait/expsys_pl_aggregate_arithmetic.py
backends/.../polars/substrait/expsys_pl_aggregate_string.py
(same pattern for ibis/ and narwhals/)
```

**Methods by protocol:**

| Protocol | Methods |
|----------|---------|
| aggregate_generic | `count`, `any_value` |
| aggregate_boolean | `bool_and`, `bool_or` |
| aggregate_arithmetic | `sum`, `sum0`, `avg`, `min`, `max`, `product`, `std_dev`, `variance`, `corr`, `mode`, `median`, `quantile` |
| aggregate_string | `string_agg` |

**Update `__init__.py`** for each backend to include new classes in composition.

---

### Phase 7: Add Window Protocol
**Priority: P2 (Medium) | Effort: Medium | +36 methods | 3 new files**

Create window implementation files:

**New files:**
```
backends/.../polars/substrait/expsys_pl_window_arithmetic.py
backends/.../ibis/substrait/expsys_ib_window_arithmetic.py
backends/.../narwhals/substrait/expsys_nw_window_arithmetic.py
```

**Methods (12 per backend):**
```
row_number, rank, dense_rank, percent_rank, cume_dist,
ntile, first_value, last_value, nth_value, lead, lag
```

---

### Phase 8: Add Geometry Protocol
**Priority: P2 (Medium) | Effort: Small | +54 methods | 3 new files**

Create geometry stub files (all NotImplementedError):

**New files:**
```
backends/.../polars/substrait/expsys_pl_scalar_geometry.py
backends/.../ibis/substrait/expsys_ib_scalar_geometry.py
backends/.../narwhals/substrait/expsys_nw_scalar_geometry.py
```

**All 18 methods** raise `NotImplementedError("Geometry operations require specialized libraries")`.

---

## File Change Summary

### Files to Modify

| File | Changes |
|------|---------|
| `prtcl_expsys_scalar_comparison.py` | Fix 5 variadic signatures |
| `expsys_pl_scalar_comparison.py` | +2 methods |
| `expsys_ib_scalar_comparison.py` | +2 methods |
| `expsys_nw_scalar_comparison.py` | +2 methods |
| `expsys_pl_scalar_arithmetic.py` | +26 methods, remove floor_divide |
| `expsys_ib_scalar_arithmetic.py` | +26 methods, remove floor_divide |
| `expsys_nw_scalar_arithmetic.py` | +26 methods, remove floor_divide |
| `expsys_pl_scalar_logarithmic.py` | +2 methods |
| `expsys_ib_scalar_logarithmic.py` | +2 methods |
| `expsys_nw_scalar_logarithmic.py` | +2 methods |
| `expsys_pl_scalar_datetime.py` | +13 methods |
| `expsys_ib_scalar_datetime.py` | +13 methods |
| `expsys_nw_scalar_datetime.py` | +13 methods |
| `polars/__init__.py` | Add new class imports |
| `ibis/__init__.py` | Add new class imports |
| `narwhals/__init__.py` | Add new class imports |

### Files to Create (18 new)

| Category | Files |
|----------|-------|
| Aggregate Generic | `expsys_pl_aggregate_generic.py`, `expsys_ib_aggregate_generic.py`, `expsys_nw_aggregate_generic.py` |
| Aggregate Boolean | `expsys_pl_aggregate_boolean.py`, `expsys_ib_aggregate_boolean.py`, `expsys_nw_aggregate_boolean.py` |
| Aggregate Arithmetic | `expsys_pl_aggregate_arithmetic.py`, `expsys_ib_aggregate_arithmetic.py`, `expsys_nw_aggregate_arithmetic.py` |
| Aggregate String | `expsys_pl_aggregate_string.py`, `expsys_ib_aggregate_string.py`, `expsys_nw_aggregate_string.py` |
| Window Arithmetic | `expsys_pl_window_arithmetic.py`, `expsys_ib_window_arithmetic.py`, `expsys_nw_window_arithmetic.py` |
| Scalar Geometry | `expsys_pl_scalar_geometry.py`, `expsys_ib_scalar_geometry.py`, `expsys_nw_scalar_geometry.py` |

---

## Estimated Totals

| Metric | Count |
|--------|-------|
| Files to modify | 16 |
| Files to create | 18 |
| Total new methods | ~270 |
| NotImplementedError stubs | ~90 (primarily Narwhals + geometry) |

---

## Implementation Notes

1. **Pattern consistency**: Follow existing file structure and naming conventions
2. **Protocol inheritance**: Each implementation must inherit from corresponding protocol
3. **Type hints**: Use backend-specific types (PolarsExpr, IbisExpr, NarwhalsExpr)
4. **Docstrings**: Include Substrait URI reference in docstrings
5. **Tests**: Existing cross-backend tests should cover new implementations
