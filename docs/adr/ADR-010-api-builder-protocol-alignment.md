# ADR-010: API Builder Protocol Alignment

## Status

**Proposed** (2025-12-31)

## Date

2025-12-31

## Context

Following ADR-009 (Substrait Backend Implementation Alignment), the expression system protocols are being expanded to include all Substrait standard operations. The API builder protocols - which define the user-facing expression API - must be updated to expose these new operations.

### Architecture Overview

The mountainash-expressions package has a three-layer architecture:

```
User Code → API Builder Protocols → AST Nodes → Expression System Protocols → Backend
           (creates nodes)                       (executes nodes)
```

**API Builder Protocols** define methods that users call (e.g., `col("x").sin()`). These methods create AST nodes (ScalarFunctionNode with function_key enums).

**Expression System Protocols** define methods that backends implement to execute those AST nodes on specific DataFrame libraries.

### Current Gap Analysis

| Category | API Builder | Expression System | Gap |
|----------|-------------|-------------------|-----|
| scalar_comparison | 16 methods | 24 methods | -8 |
| scalar_boolean | 5 methods | 5 methods | 0 |
| scalar_arithmetic | 7 methods | 33 methods | -26 |
| scalar_string | 29 methods | 38 methods | -9 |
| scalar_datetime | 3 methods | 18 methods | -15 |
| scalar_rounding | 3 methods | 3 methods | 0 |
| scalar_logarithmic | 4 methods | 5 methods | -1 |
| scalar_set | 1 method | 1 method | 0 |
| aggregate_generic | EXISTS | 2 methods | 0 |
| aggregate_boolean | **MISSING** | 2 methods | -2 |
| aggregate_arithmetic | **MISSING** | 12 methods | -12 |
| aggregate_string | **MISSING** | 1 method | -1 |
| window_arithmetic | **MISSING** | 12 methods | -12 |
| scalar_geometry | **MISSING** | 18 methods | -18 |

**Total Gap: ~93 missing methods + 6 missing protocol files**

## Decision

**Update API builder protocols to mirror expression system protocols**, ensuring:

1. Every expression system method has a corresponding API builder method
2. Users can access all Substrait operations through the expression API
3. Protocol signatures are consistent between layers

### Implementation Strategy

#### 1. Expand Existing Protocols

Update existing `prtcl_api_bldr_*.py` files to include missing methods:

```python
# Example: Adding sin() to scalar_arithmetic
class SubstraitScalarArithmeticAPIBuilderProtocol(Protocol):
    def sin(self) -> "BaseExpressionAPI":
        """Get the sine of a value in radians.

        Substrait: sin
        """
        ...
```

#### 2. Create New Protocol Files

Create new protocol files for missing categories:
- `prtcl_api_bldr_aggregate_boolean.py`
- `prtcl_api_bldr_aggregate_arithmetic.py`
- `prtcl_api_bldr_aggregate_string.py`
- `prtcl_api_bldr_window_arithmetic.py`
- `prtcl_api_bldr_scalar_geometry.py`

#### 3. Fix Signature Mismatches

Update variadic function signatures to match expression system protocols:

```python
# Before (incorrect)
def coalesce(self, arg: ...) -> ...:

# After (correct)
def coalesce(self, *args: ...) -> ...:
```

### Method Naming Conventions

API builder methods should:
- Use the same names as expression system methods where possible
- Add prefixes for clarity where needed (e.g., `dt_add` for datetime addition to avoid collision with arithmetic `add`)
- Return `BaseExpressionAPI` or `BooleanExpressionAPI` as appropriate

### Return Type Guidelines

| Operation Type | Return Type |
|----------------|-------------|
| Comparison (eq, lt, etc.) | `BooleanExpressionAPI` |
| Boolean logic (and, or) | `BooleanExpressionAPI` |
| Null checks (is_null) | `BooleanExpressionAPI` |
| Arithmetic (add, sin) | `BaseExpressionAPI` |
| String operations | `BaseExpressionAPI` |
| Aggregations | `BaseExpressionAPI` |
| Window functions | `BaseExpressionAPI` |

## Implementation Phases

| Phase | Category | Methods | Priority |
|-------|----------|---------|----------|
| 1 | Fix signatures | 5 fixes | P0 |
| 2 | scalar_comparison | +2 | P0 |
| 3 | scalar_arithmetic | +26 | P0 |
| 4 | scalar_logarithmic | +1 | P1 |
| 5 | scalar_datetime | +15 | P1 |
| 6 | scalar_string | +4 | P1 |
| 7 | Aggregate protocols | +17 | P1 |
| 8 | Window protocol | +12 | P2 |
| 9 | Geometry protocol | +18 | P2 |

## Dependencies

This ADR depends on [ADR-009: Substrait Backend Implementation Alignment](./ADR-009-substrait-backend-implementation-alignment.md).

**Execution order:**
1. Implement backend expression system methods (ADR-009)
2. Update API builder protocols to expose those methods (this ADR)
3. Update API builder implementations (`api_bldr_*.py`)
4. Update user-facing namespaces if needed

## Consequences

### Positive

- **Complete API surface**: Users can access all Substrait operations
- **Consistent architecture**: Protocol layers mirror each other
- **Type safety**: Full protocol coverage enables better IDE support
- **Future-proof**: New operations follow established patterns

### Negative

- **Implementation effort**: ~93 new protocol methods
- **Documentation**: More methods to document
- **Learning curve**: Larger API surface for users

### Mitigations

- Organize methods into clear namespaces (`.str`, `.dt`, `.math`, etc.)
- Provide comprehensive docstrings with examples
- Maintain backward compatibility with existing API

## Files Changed

### Modified (6)
- `prtcl_api_bldr_scalar_comparison.py`
- `prtcl_api_bldr_scalar_arithmetic.py`
- `prtcl_api_bldr_scalar_logarithmic.py`
- `prtcl_api_bldr_scalar_datetime.py`
- `prtcl_api_bldr_scalar_string.py`
- `substrait/__init__.py`

### Created (6)
- `prtcl_api_bldr_aggregate_generic.py` (if not exists)
- `prtcl_api_bldr_aggregate_boolean.py`
- `prtcl_api_bldr_aggregate_arithmetic.py`
- `prtcl_api_bldr_aggregate_string.py`
- `prtcl_api_bldr_window_arithmetic.py`
- `prtcl_api_bldr_scalar_geometry.py`

## References

- [ADR-009: Substrait Backend Implementation Alignment](./ADR-009-substrait-backend-implementation-alignment.md)
- [ADR-008: Substrait Extension Alignment](./ADR-008-substrait-extension-alignment.md)
- [Substrait Specification](https://substrait.io/)
- Implementation Plan: `docs/adr/plans/PLAN-010-api-builder-protocol-alignment.md`
