# Polars Power Operator: Existing Issues & History

## Summary

The power operator overflow bug we discovered **has existing related issues** in Polars, but our specific case (Int8 overflow to 0) doesn't appear to be explicitly reported yet.

---

## Related Open Issues

### Issue #21596: "Pow operator takes the type of a literal base over the type of the column exponent"

**Status**: ⚠️ **OPEN** (as of latest check)
**Link**: https://github.com/pola-rs/polars/issues/21596
**Date**: Recent (Polars 0.46.0)

**Description**:
Reports that when a literal is the base and a column is the exponent in `pow()`, the result type comes from the literal instead of the column, unlike all other operators.

```python
(lit(1f64).pow(col("x"))).alias("1pow")  # Returns f64, not f32
```

**Relationship to our bug**:
- Same root cause: `pow_dtype()` doesn't handle type promotion correctly
- Focused on float type inconsistency
- **Our case is worse**: Int8 overflow to 0, not just wrong type

---

## Closed Issues (Previously Fixed)

### Issue #3764: "pow() operation does not support having a literal on the left"

**Status**: ✅ **CLOSED** (Fixed in PR #3768, June 2022)
**Link**: https://github.com/pola-rs/polars/issues/3764

**Description**:
Original issue where `10 ** pl.col("a")` didn't work at all.

**Fix**: Added basic support for literal base with expression exponent.

**Note**: While this made the operation work, it didn't address the overflow issue.

---

## The Misguided "Fix" (Commit 30edab06f)

**Commit**: `30edab06f` (December 2023)
**Link**: https://github.com/pola-rs/polars/commit/30edab06f
**Title**: "feat(rust, python): preserve base dtype when raising to uint power"
**PR**: https://github.com/pola-rs/polars/pull/10446
**Author**: Marco Edward Gorelli

### What it did:

```rust
pub(super) fn pow_dtype(&self) -> PolarsResult<Field> {
    match (self.fields[0].data_type(), self.fields[1].data_type()) {
        // If exponent is unsigned int, preserve base dtype
        (base_dtype, DataType::UInt8 | DataType::UInt16 | DataType::UInt32 | DataType::UInt64) => {
            Ok(Field::new(self.fields[0].name(), base_dtype.clone()))  // ← CAUSES OVERFLOW!
        },
        (DataType::Float32, _) => Ok(Field::new(self.fields[0].name(), DataType::Float32)),
        (_, _) => Ok(Field::new(self.fields[0].name(), DataType::Float64)),
    }
}
```

### The Problem:

**Intent**: Preserve precision when raising integers to unsigned powers
**Reality**: Causes overflow when narrow base types can't hold result

```python
# After this commit:
Int8(2) ** UInt32(10)  # → Int8: 0  ❌ (Overflow!)
# Before this commit:
Int8(2) ** UInt32(10)  # → Float64: 1024.0  ✅ (Worked, but wrong type)
```

**This commit INTRODUCED the overflow bug we found!**

---

## Current State (in our cloned repo)

Looking at the current `pow_dtype()` (lines 711-720):

```rust
pub(super) fn pow_dtype(&self) -> PolarsResult<Field> {
    let dtype1 = self.fields[0].dtype();  // base
    let dtype2 = self.fields[1].dtype();  // exponent
    let out_dtype = if dtype1.is_integer() {
        if dtype2.is_float() { dtype2 } else { dtype1 }  // ← Still preserves base!
    } else {
        dtype1
    };
    Ok(Field::new(self.fields[0].name().clone(), out_dtype.clone()))
}
```

This is a simplified version that still has the same problem: preserves base dtype for integer-integer operations.

---

## Why Other Operators Work (Comparison)

**Multiplication, Addition, etc.** (from `type_coercion/binary.rs`):

```rust
// Line 242:
let st = unpack!(get_supertype(&type_left, &type_right));  // ← Auto-widens!
```

These operators call `get_supertype()` which:
- Detects `Int8 * Int8` could overflow
- Returns `Int64` automatically
- Prevents overflow

**Power operator** doesn't call `get_supertype()`, so it doesn't benefit from this auto-widening.

---

## Evidence Our Specific Bug Isn't Reported

Searched for:
- ✅ "polars pow Int8 overflow"
- ✅ "polars power operator returns 0"
- ✅ Issues in #1941, #8595, #21318 (related but different)

**Result**: No existing issue specifically describes:
- Int8 power operation returning 0
- Comparison with multiplication's auto-widening behavior
- The inconsistency we documented

---

## Related Overflow Issues (Different problems)

### Issue #1941: "Integer overflow issues"
- **Focus**: Aggregation overflow (sum, etc.)
- **Example**: Summing 100k Int8(1) → -96
- **Not about**: Power operator

### Issue #8595: "Protection against integer overflows"
- **Scope**: General overflow warning system
- **Status**: Discussion about overflow detection
- **Not specific to**: Power operator

### Issue #21318: "rolling_sum with small integer types does not cast to Int64"
- **Focus**: Rolling window aggregations
- **Similar pattern**: Doesn't upcast like other operations
- **Not about**: Power operator

---

## Our Contribution

### What's New in Our Report:

1. **Specific reproduction**: `Int8(2) ** col(10)` → 0
2. **Comparison with multiplication**: Shows power is the ONLY operator that doesn't upcast
3. **Comprehensive testing**: All operators tested, power is the outlier
4. **Root cause identified**: Exact location in source code
5. **Proposed fix**: Use `get_supertype()` like other operators

### Why It's Important:

- **Silent data corruption**: Returns 0, not an error
- **Inconsistent with design**: All other arithmetic ops upcast
- **Type promotion exists**: Just not used for power
- **Simple fix**: One function call to `get_supertype()`

---

## Recommendation

### For Polars Bug Report:

1. **Reference Issue #21596** as related (type handling in pow)
2. **Note Commit 30edab06f** (https://github.com/pola-rs/polars/commit/30edab06f) introduced the regression
3. **Emphasize difference**: Our issue is overflow, #21596 is type choice
4. **Provide comprehensive evidence**: Our test scripts show it's unique to power
5. **Suggest fix**: Use `get_supertype()` for integer-integer power

### Key Message:

> "The December 2023 commit (#10446) that tried to preserve base dtype in power operations introduced silent integer overflow. Unlike all other arithmetic operators which call `get_supertype()` to auto-widen types, power operations preserve narrow types, causing `Int8(2) ** col(10)` to return 0 instead of 1024."

---

## Files to Reference in Bug Report

From our investigation:
- `POLARS_BUG_LOCATION.md` - Exact source location
- `POLARS_TECHNICAL_ANALYSIS.md` - Comprehensive analysis
- `investigate_polars_upcasting.py` - Proof power is the only operator that doesn't upcast
- `test_polars_overflow_behavior.py` - Shows multiplication works, power doesn't
- `polars_bug_minimal_repro.py` - Simple reproduction

---

## Timeline

1. **June 2022**: Issue #3764 - Basic literal pow support added
2. **December 2023**: [Commit 30edab06f](https://github.com/pola-rs/polars/commit/30edab06f) - "Preserve base dtype" feature added (introduced bug)
3. **Recent**: Issue #21596 - Type inconsistency reported (still open)
4. **November 2025**: Our discovery - Int8 overflow to 0, comprehensive analysis

---

## Next Steps

File new issue with:
- **Title**: "Power operator causes integer overflow (returns 0) with narrow types, unlike other arithmetic operators"
- **Reference**: Issues #21596, #3764, commit [30edab06f](https://github.com/pola-rs/polars/commit/30edab06f)
- **Evidence**: Our comprehensive test suite
- **Fix**: Revert to using `get_supertype()` like other operators
