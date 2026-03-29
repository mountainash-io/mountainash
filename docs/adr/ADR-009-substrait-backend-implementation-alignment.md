# ADR-009: Substrait Backend Implementation Alignment

## Status

**Proposed** (2025-12-31)

## Date

2025-12-31

## Context

Following ADR-008 (Substrait Extension Alignment), the package now has well-defined protocol interfaces that specify the contract between the expression API and backend implementations. However, analysis reveals significant gaps between what the protocols define and what the backends actually implement:

### Current State Analysis

| Protocol Category | Total Methods | Polars | Ibis | Narwhals |
|-------------------|---------------|--------|------|----------|
| **Foundation (4)** | 4 | Complete | Complete | Complete |
| scalar_comparison | 24 | 21/24 | 21/24 | 21/24 |
| scalar_boolean | 5 | 5/5 | 5/5 | 5/5 |
| scalar_arithmetic | 33 | 8/33 | 7/33 | 7/33 |
| scalar_string | 38 | ~38/38 | ~30/38 | ~30/38 |
| scalar_datetime | 18 | 5/18 | 5/18 | 5/18 |
| scalar_rounding | 3 | 3/3 | 3/3 | 3/3 |
| scalar_logarithmic | 5 | 3/5 | 3/5 | 3/5 |
| scalar_set | 1 | 1/1 | 1/1 | 1/1 |
| scalar_geometry | 18 | 0/18 | 0/18 | 0/18 |
| aggregate_generic | 2 | 0/2 | 0/2 | 0/2 |
| aggregate_boolean | 2 | 0/2 | 0/2 | 0/2 |
| aggregate_arithmetic | 12 | 0/12 | 0/12 | 0/12 |
| aggregate_string | 1 | 0/1 | 0/1 | 0/1 |
| window_arithmetic | 12 | 0/12 | 0/12 | 0/12 |
| **Total** | **177** | **~85** | **~75** | **~75** |

**Overall Coverage: ~45%**

### Identified Issues

1. **Missing Protocol Methods**
   - `is_distinct_from`, `is_not_distinct_from` missing from all backends
   - 26 arithmetic methods missing (trig, bitwise, math functions)
   - 13 datetime methods missing
   - All aggregate and window protocols unimplemented

2. **Signature Mismatches**
   - Protocol defines `coalesce(arg)` but implementations use `coalesce(*args)`
   - Same issue for `least`, `greatest`, `least_skip_null`, `greatest_skip_null`
   - Implementations are correct; protocols need updating

3. **Misplaced Methods**
   - `floor_divide` exists in Substrait implementations but is NOT a Substrait standard operation
   - Should be moved to MountainAsh extension namespace

4. **Missing Backend Files**
   - No aggregate implementation files exist
   - No window implementation files exist
   - No geometry implementation files exist

## Decision

**Complete the backend implementations to achieve full protocol alignment**, using the following strategy:

### 1. Fix Protocol Signatures First

Update protocols to match correct variadic signatures where implementations are correct:

```python
# Before (incorrect)
def coalesce(self, arg: SupportedExpressions) -> SupportedExpressions: ...

# After (correct)
def coalesce(self, *args: SupportedExpressions) -> SupportedExpressions: ...
```

### 2. NotImplementedError for Unsupported Operations

For operations that a backend cannot support natively, raise `NotImplementedError` with a clear message:

```python
def factorial(self, n: PolarsExpr, /, overflow: Any = None) -> PolarsExpr:
    """Factorial is not supported by Polars."""
    raise NotImplementedError(
        "factorial() is not supported by the Polars backend. "
        "Consider using a UDF or alternative approach."
    )
```

This approach:
- Makes the API complete (all protocol methods exist)
- Fails fast with clear error messages
- Allows type checkers to see the full interface
- Enables future implementations without API changes

### 3. Move Non-Substrait Operations to Extensions

`floor_divide` and any other non-Substrait operations must move to `extensions_mountainash/`:

```
# FROM (incorrect)
backends/expression_systems/polars/substrait/expsys_pl_scalar_arithmetic.py

# TO (correct)
backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_arithmetic.py
```

### 4. Create New Files for Missing Categories

| Category | New Files Required |
|----------|-------------------|
| Aggregate Generic | 3 (one per backend) |
| Aggregate Boolean | 3 |
| Aggregate Arithmetic | 3 |
| Aggregate String | 3 |
| Window Arithmetic | 3 |
| Scalar Geometry | 3 |
| **Total** | **18 new files** |

### 5. Implementation Priority

Based on practical value and complexity:

| Priority | Phase | Category | Methods |
|----------|-------|----------|---------|
| HIGH | 1 | Fix Protocol Signatures | 5 |
| HIGH | 2 | scalar_comparison completion | 2 |
| HIGH | 3 | scalar_arithmetic expansion | 26 |
| MEDIUM | 4 | scalar_logarithmic completion | 2 |
| MEDIUM | 5 | scalar_datetime expansion | 13 |
| MEDIUM | 6 | Aggregate protocols | 17 |
| LOW | 7 | Window protocol | 12 |
| LOW | 8 | Geometry protocol | 18 |

## Backend Support Matrix

### Expected Support After Implementation

| Operation Type | Polars | Ibis | Narwhals |
|----------------|--------|------|----------|
| Basic Comparison | Full | Full | Full |
| Null-aware Comparison | Full | Full | Full |
| Basic Arithmetic | Full | Full | Full |
| Trig/Math Functions | Full | Full | NotImplemented |
| Bitwise Operations | Partial | Partial | NotImplemented |
| Logarithmic | Full | Full | Partial |
| Datetime Extract | Full | Full | Partial |
| Datetime Arithmetic | Partial | Full | NotImplemented |
| Aggregates | Full | Full | Partial |
| Window Functions | Full | Full | Partial |
| Geometry | NotImplemented | NotImplemented | NotImplemented |

### Rationale for NotImplementedError Usage

**Narwhals** is a lightweight DataFrame abstraction layer. It intentionally provides a minimal API that works across Pandas, Polars, and other backends. Many advanced operations (trig functions, bitwise operations) are not part of its core API.

**Geometry operations** require specialized libraries (Shapely, GeoPandas) that are outside the scope of general DataFrame processing.

## Implementation Details

### File Changes Summary

**Files to Modify (16)**:
- 1 protocol file (signature fixes)
- 3 comparison files (add 2 methods each)
- 3 arithmetic files (add 26 methods each)
- 3 logarithmic files (add 2 methods each)
- 3 datetime files (add 13 methods each)
- 3 `__init__.py` files (add new imports)

**Files to Create (18)**:
- 12 aggregate files (4 protocols × 3 backends)
- 3 window files
- 3 geometry files

**Total New Methods**: ~270 across all backends

### Testing Strategy

1. **Unit Tests**: Each new method gets basic functionality tests
2. **Cross-Backend Tests**: Verify consistent behavior where applicable
3. **NotImplementedError Tests**: Verify appropriate errors are raised
4. **Protocol Compliance**: Automated checks that all protocol methods exist

## Consequences

### Positive

- **Complete API surface**: Users get clear errors for unsupported operations instead of AttributeError
- **Type safety**: Protocol inheritance provides full type checking
- **Documentation**: All methods documented even if NotImplemented
- **Future-proofing**: API is stable; implementations can be added later
- **Clear capabilities**: Support matrix documents what works where

### Negative

- **Implementation effort**: ~270 new methods to implement or stub
- **Maintenance**: More code to maintain across backends
- **Some operations raise errors**: Users may be surprised by NotImplementedError

### Mitigations

- **Phased implementation**: Start with high-priority/high-value operations
- **Clear documentation**: Backend support matrix in package docs
- **Error messages**: Include alternatives when raising NotImplementedError

## Alternatives Considered

### 1. Partial Protocols

Define separate "base" and "full" protocols, with backends implementing only what they support.

**Rejected because**: Makes type checking incomplete; users can't rely on interface consistency.

### 2. Polyfill Implementations

Implement missing operations using available primitives (e.g., compute sin() using Taylor series).

**Rejected because**: Performance would be poor; correctness hard to guarantee; maintenance burden high.

### 3. Runtime Feature Detection

Check backend capabilities at runtime and adjust API accordingly.

**Rejected because**: Dynamic APIs are hard to document and type-check; IDE autocomplete would be unreliable.

## References

- [ADR-008: Substrait Extension Alignment](./ADR-008-substrait-extension-alignment.md)
- [Substrait Specification](https://substrait.io/)
- [Substrait Function Extensions](https://substrait.io/extensions/)
- Implementation Plan: `/home/nathanielramm/.claude/plans/glistening-chasing-dahl.md`
