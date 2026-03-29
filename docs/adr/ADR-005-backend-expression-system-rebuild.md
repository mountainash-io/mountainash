# ADR-005: Backend Expression System Rebuild

**Status**: PROPOSED
**Date**: 2025-12-21
**Deciders**: @nathanielramm

## Context

The mountainash-expressions package has backend expression systems that implement ExpressionProtocol interfaces. Currently:

1. **Deprecated Implementations** exist at `backends/deprecated_expression_systems/`
   - Three backends: Polars (~1,423 lines), Narwhals (~991 lines), Ibis (~984 lines)
   - Use legacy categorical organization (12 category files per backend)
   - Partially aligned with new Substrait-aligned protocols

2. **New Protocol Architecture** defined at `expression_protocols/substrait/`
   - 13 protocol categories with 102+ methods
   - Substrait-aligned naming and signatures
   - Two-layer design: ExpressionProtocol (backend primitives) + BuilderProtocol (user-facing)

3. **Empty Target Directory** at `backends/expression_systems/`
   - Scaffolded but not implemented
   - Ready for new protocol-aligned implementations

### Protocol Categories to Implement

| Protocol | Methods | Description |
|----------|---------|-------------|
| FieldReferenceExpressionProtocol | 1 | Column references |
| LiteralExpressionProtocol | 1 | Constant values |
| CastExpressionProtocol | 1 | Type conversions |
| ConditionalExpressionProtocol | 1 | If-then-else logic |
| ScalarComparisonExpressionProtocol | 23 | Equality, ordering, null checks |
| ScalarBooleanExpressionProtocol | 5 | Logical operations |
| ScalarArithmeticExpressionProtocol | 7 | Math operations |
| ScalarStringExpressionProtocol | 50+ | String manipulation |
| ScalarDatetimeExpressionProtocol | 2 | Datetime extraction |
| ScalarRoundingExpressionProtocol | 3 | Rounding operations |
| ScalarLogarithmicExpressionProtocol | 4 | Logarithm operations |
| ScalarSetExpressionProtocol | 1 | Set membership |
| ScalarAggregateExpressionProtocol | 3 | Aggregation operations |

## Decision

Rebuild backend expression systems from scratch using ExpressionProtocol classes as the source of truth.

### Approach: Protocol-First Implementation

1. **Do not migrate** deprecated implementations
2. **Use protocols** as the authoritative specification for method signatures
3. **Reference deprecated code** only for implementation patterns and edge cases
4. **One file per protocol** for clean organization
5. **Start with Polars** as the reference implementation

### Implementation Structure

```
backends/expression_systems/
├── __init__.py                    # Export all backends
├── base.py                        # Shared base classes
├── polars/
│   ├── __init__.py               # PolarsExpressionSystem composition
│   ├── base.py                   # PolarsBaseExpressionSystem
│   ├── field_reference.py        # FieldReferenceExpressionProtocol
│   ├── literal.py                # LiteralExpressionProtocol
│   ├── cast.py                   # CastExpressionProtocol
│   ├── conditional.py            # ConditionalExpressionProtocol
│   ├── scalar_comparison.py      # ScalarComparisonExpressionProtocol
│   ├── scalar_boolean.py         # ScalarBooleanExpressionProtocol
│   ├── scalar_arithmetic.py      # ScalarArithmeticExpressionProtocol
│   ├── scalar_string.py          # ScalarStringExpressionProtocol
│   ├── scalar_datetime.py        # ScalarDatetimeExpressionProtocol
│   ├── scalar_rounding.py        # ScalarRoundingExpressionProtocol
│   ├── scalar_logarithmic.py     # ScalarLogarithmicExpressionProtocol
│   ├── scalar_set.py             # ScalarSetExpressionProtocol
│   └── scalar_aggregate.py       # ScalarAggregateExpressionProtocol
├── narwhals/                      # (same structure)
└── ibis/                          # (same structure)
```

### Composition Pattern

```python
@register_expression_system(CONST_VISITOR_BACKENDS.POLARS)
class PolarsExpressionSystem(
    PolarsFieldReferenceSystem,
    PolarsLiteralSystem,
    PolarsCastSystem,
    PolarsConditionalSystem,
    PolarsScalarComparisonSystem,
    PolarsScalarBooleanSystem,
    PolarsScalarArithmeticSystem,
    PolarsScalarStringSystem,
    PolarsScalarDatetimeSystem,
    PolarsScalarRoundingSystem,
    PolarsScalarLogarithmicSystem,
    PolarsScalarSetSystem,
    PolarsScalarAggregateSystem,
):
    """Complete Polars backend implementation."""
    pass
```

## Consequences

### Positive

- Clean protocol alignment from the start
- Each file implements exactly one protocol - easy to test and maintain
- Substrait-compatible method signatures enable future serialization
- Reference implementation (Polars) can be cloned for other backends
- Deprecated code remains available during transition

### Negative

- Full reimplementation required (~4,100 lines across 3 backends)
- Cannot reuse deprecated code directly
- Potential for missed edge cases not in protocol definitions

### Neutral

- Same number of files per backend (14 vs 12 in deprecated)
- Same composition pattern (multiple inheritance)
- Existing tests remain valid for validation

## Alternatives Considered

1. **Migrate & refactor deprecated code**
   - Rejected: Would carry forward misaligned method signatures
   - Would require significant refactoring anyway

2. **Implement only Polars, deprecate others**
   - Rejected: Narwhals and Ibis are important for cross-backend support
   - Users depend on all three backends

3. **Protocol-first rebuild (selected)**
   - Selected: Cleanest alignment with new architecture
   - Protocols are source of truth for all implementations

## References

- [ADR-004: Function Mapping Registry Alignment](./ADR-004-function-mapping-registry-alignment.md)
- [Substrait Extensions](https://substrait.io/extensions/)
- [Expression Type Reference](../../src/mountainash_expressions/core/expression_system/function_mapping/EXPRESSION_TYPE_REFERENCE.md)

## Tasks

GitHub Issues created in [mountainash-io/mountainash-expressions](https://github.com/mountainash-io/mountainash-expressions):

- [ ] Issue #30: Create ADR-005 and scaffold backend structure
- [ ] Issue #31: Implement Polars foundation protocols
- [ ] Issue #32: Implement Polars comparison & boolean protocols
- [ ] Issue #33: Implement Polars arithmetic & rounding protocols
- [ ] Issue #34: Implement Polars string operations
- [ ] Issue #35: Implement Polars datetime operations
- [ ] Issue #36: Implement Polars set & aggregate protocols
- [ ] Issue #37: Implement Narwhals backend
- [ ] Issue #38: Implement Ibis backend

**Milestone**: [Substrait Alignment Phase 4 - Backend Expression Systems](https://github.com/mountainash-io/mountainash-expressions/milestone/5)

## Completion Criteria

- [ ] ADR-005 created
- [ ] Backend structure scaffolded
- [ ] Polars backend fully implemented (102+ methods)
- [ ] Narwhals backend fully implemented
- [ ] Ibis backend fully implemented
- [ ] All existing cross-backend tests pass
- [ ] ADR status updated to ACCEPTED
