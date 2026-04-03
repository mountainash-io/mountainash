# PLAN-010: API Builder Protocol Alignment Implementation Plan

## GitHub Tracking

- **Milestone**: [API Builder Protocol Alignment](https://github.com/mountainash-io/mountainash-expressions/milestone/9) (Due: 2026-06-30)
- **ADR**: [ADR-010-api-builder-protocol-alignment.md](../ADR-010-api-builder-protocol-alignment.md)
- **Project**: [Mountain Ash - Data Framework](https://github.com/orgs/mountainash-io/projects/8)

### Phase Issues & Project Tasks

| Phase | Issue | Priority | Status | Methods |
|-------|-------|----------|--------|---------|
| 1. Fix Protocol Signatures | [#61](https://github.com/mountainash-io/mountainash-expressions/issues/61) | P0 | Backlog | 5 fixes |
| 2. Complete scalar_comparison | [#62](https://github.com/mountainash-io/mountainash-expressions/issues/62) | P0 | Backlog | +2 |
| 3. Expand scalar_arithmetic | [#63](https://github.com/mountainash-io/mountainash-expressions/issues/63) | P0 | Backlog | +26 |
| 4. Complete scalar_logarithmic | [#64](https://github.com/mountainash-io/mountainash-expressions/issues/64) | P1 | Backlog | +1 |
| 5. Expand scalar_datetime | [#65](https://github.com/mountainash-io/mountainash-expressions/issues/65) | P1 | Backlog | +15 |
| 6. Expand scalar_string | [#66](https://github.com/mountainash-io/mountainash-expressions/issues/66) | P1 | Backlog | +4 |
| 7. Create Aggregate Protocols | [#67](https://github.com/mountainash-io/mountainash-expressions/issues/67) | P1 | Backlog | +17 |
| 8. Create Window Protocol | [#68](https://github.com/mountainash-io/mountainash-expressions/issues/68) | P2 | Backlog | +12 |
| 9. Create Geometry Protocol | [#69](https://github.com/mountainash-io/mountainash-expressions/issues/69) | P2 | Backlog | +18 |

---

## Overview

Align API builder protocols with expression system protocols to ensure the public API exposes all Substrait operations.

- **Dependency**: PLAN-009 (Substrait Backend Implementation Alignment)
- **Scope**: Update/create API builder protocols to match expression system protocols
- **Pattern**: API builders create AST nodes; expression systems execute them
- **Total Gap**: ~93 missing methods + 6 new protocol files

---

## Current State Analysis

| Category | API Builder | Expression System | Gap |
|----------|-------------|-------------------|-----|
| scalar_comparison | 16 methods | 24 methods | -2 |
| scalar_boolean | 5 methods | 5 methods | 0 |
| scalar_arithmetic | 7 methods | 33 methods | -26 |
| scalar_string | 29 methods | 38 methods | -4 |
| scalar_datetime | 3 methods | 18 methods | -15 |
| scalar_rounding | 3 methods | 3 methods | 0 |
| scalar_logarithmic | 4 methods | 5 methods | -1 |
| scalar_set | 1 method | 1 method | 0 |
| aggregate_generic | 2 methods | 2 methods | 0 |
| aggregate_boolean | **MISSING** | 2 methods | -2 |
| aggregate_arithmetic | **MISSING** | 12 methods | -12 |
| aggregate_string | **MISSING** | 1 method | -1 |
| window_arithmetic | **MISSING** | 12 methods | -12 |
| scalar_geometry | **MISSING** | 18 methods | -18 |

---

## Implementation Phases

### Phase 1: Fix Protocol Signature Mismatches
**Priority: P0 | Effort: Small | Depends on: PLAN-009 #53**

Fix variadic signatures in API builder protocols:

**File**: `prtcl_api_bldr_scalar_comparison.py`
```python
# Change from:
def coalesce(self, arg: ...) -> ...:
# To:
def coalesce(self, *args: ...) -> ...:
```

**Methods to fix:** `coalesce`, `least`, `greatest`, `least_skip_null`, `greatest_skip_null`

---

### Phase 2: Complete scalar_comparison Protocol
**Priority: P0 | Effort: Small | +2 methods | Depends on: PLAN-009 #54**

**File**: `prtcl_api_bldr_scalar_comparison.py`

| Method | Signature | Return Type |
|--------|-----------|-------------|
| `is_distinct_from` | `(other)` | `BooleanExpressionAPI` |
| `is_not_distinct_from` | `(other)` | `BooleanExpressionAPI` |

---

### Phase 3: Expand scalar_arithmetic Protocol
**Priority: P0 | Effort: Large | +26 methods | Depends on: PLAN-009 #55**

**File**: `prtcl_api_bldr_scalar_arithmetic.py`

**Math Functions (5):** `sqrt`, `exp`, `abs`, `sign`, `factorial`

**Trigonometric (15):**
- Basic: `sin`, `cos`, `tan`
- Hyperbolic: `sinh`, `cosh`, `tanh`
- Inverse: `asin`, `acos`, `atan`
- Inverse hyperbolic: `asinh`, `acosh`, `atanh`
- Two-arg: `atan2`, `radians`, `degrees`

**Bitwise (6):** `bitwise_not`, `bitwise_and`, `bitwise_or`, `bitwise_xor`, `shift_left`, `shift_right`

---

### Phase 4: Complete scalar_logarithmic Protocol
**Priority: P1 | Effort: Small | +1 method | Depends on: PLAN-009 #56**

**File**: `prtcl_api_bldr_scalar_logarithmic.py`

| Method | Description |
|--------|-------------|
| `log1p` | Natural log of (1 + x) |

---

### Phase 5: Expand scalar_datetime Protocol
**Priority: P1 | Effort: Medium | +15 methods | Depends on: PLAN-009 #57**

**File**: `prtcl_api_bldr_scalar_datetime.py`

**Extraction (2):** `extract`, `extract_boolean`
**Arithmetic (4):** `dt_add`, `dt_subtract`, `dt_multiply`, `add_intervals`
**Comparison (4):** `dt_lt`, `dt_lte`, `dt_gt`, `dt_gte`
**Parsing (3):** `strptime_time`, `strptime_date`, `strptime_timestamp`
**Rounding (2):** `round_temporal`, `round_calendar`

---

### Phase 6: Expand scalar_string Protocol
**Priority: P1 | Effort: Small | +4 methods**

**File**: `prtcl_api_bldr_scalar_string.py`

| Method | Description |
|--------|-------------|
| `regexp_match_substring_all` | All regex matches |
| `regexp_strpos` | Position of regex match |
| `regexp_count_substring` | Count regex matches |

---

### Phase 7: Create Aggregate Protocols
**Priority: P1 | Effort: Medium | +17 methods | 4 new files | Depends on: PLAN-009 #58**

**New Files:**
- `prtcl_api_bldr_aggregate_generic.py` (2 methods: `count`, `any_value`)
- `prtcl_api_bldr_aggregate_boolean.py` (2 methods: `bool_and`, `bool_or`)
- `prtcl_api_bldr_aggregate_arithmetic.py` (12 methods: `sum`, `sum0`, `avg`, `min`, `max`, `product`, `std_dev`, `variance`, `corr`, `mode`, `median`, `quantile`)
- `prtcl_api_bldr_aggregate_string.py` (1 method: `string_agg`)

---

### Phase 8: Create Window Protocol
**Priority: P2 | Effort: Medium | +12 methods | 1 new file | Depends on: PLAN-009 #59**

**New File**: `prtcl_api_bldr_window_arithmetic.py`

**Ranking (5):** `row_number`, `rank`, `dense_rank`, `percent_rank`, `cume_dist`
**Distribution (1):** `ntile`
**Value (6):** `first_value`, `last_value`, `nth_value`, `lead`, `lag`

---

### Phase 9: Create Geometry Protocol (Stubs)
**Priority: P2 | Effort: Small | +18 methods | 1 new file | Depends on: PLAN-009 #60**

**New File**: `prtcl_api_bldr_scalar_geometry.py`

All 18 geometry methods as protocol stubs (implementations will raise NotImplementedError).

---

## File Change Summary

### Files to Modify (6)

| File | Changes |
|------|---------|
| `prtcl_api_bldr_scalar_comparison.py` | Fix 5 signatures, +2 methods |
| `prtcl_api_bldr_scalar_arithmetic.py` | +26 methods |
| `prtcl_api_bldr_scalar_logarithmic.py` | +1 method |
| `prtcl_api_bldr_scalar_datetime.py` | +15 methods |
| `prtcl_api_bldr_scalar_string.py` | +4 methods |
| `substrait/__init__.py` | Add new protocol imports |

### Files to Create (6)

| File | Methods |
|------|---------|
| `prtcl_api_bldr_aggregate_generic.py` | 2 |
| `prtcl_api_bldr_aggregate_boolean.py` | 2 |
| `prtcl_api_bldr_aggregate_arithmetic.py` | 12 |
| `prtcl_api_bldr_aggregate_string.py` | 1 |
| `prtcl_api_bldr_window_arithmetic.py` | 12 |
| `prtcl_api_bldr_scalar_geometry.py` | 18 |

---

## Dependencies

This plan depends on PLAN-009 (Backend Implementation):

| This Phase | Depends on PLAN-009 |
|------------|---------------------|
| Phase 1 | #53 (Fix Protocol Signatures) |
| Phase 2 | #54 (scalar_comparison) |
| Phase 3 | #55 (scalar_arithmetic) |
| Phase 4 | #56 (scalar_logarithmic) |
| Phase 5 | #57 (scalar_datetime) |
| Phase 7 | #58 (Aggregate Protocols) |
| Phase 8 | #59 (Window Protocol) |
| Phase 9 | #60 (Geometry Protocol) |

**Recommended execution order:**
1. Complete PLAN-009 phases first (backend implementations)
2. Then update API builder protocols to expose new functionality

---

## Estimated Totals

| Metric | Count |
|--------|-------|
| Files to modify | 6 |
| Files to create | 6 |
| Total new methods | ~93 |
| Protocol stubs | 18 (geometry) |

---

## Implementation Notes

1. **API Builder vs Expression System**: API builders create AST nodes (ScalarFunctionNode with function_key), expression systems execute those nodes on specific backends.

2. **User-facing API**: The `BooleanExpressionAPI` class composes these protocol methods via namespaces. New methods need corresponding namespace exposure.

3. **Namespace updates**: After protocol updates, also update:
   - `api_builders/substrait/api_bldr_*.py` (implementations)
   - `expression_api/api_base.py` or namespace files (user exposure)
