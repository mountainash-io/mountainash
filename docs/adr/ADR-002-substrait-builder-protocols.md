# ADR-002: Substrait BuilderProtocol Migration

**Status**: PROPOSED
**Date**: 2025-12-20
**Deciders**: @nathanielramm

## Context

The mountainash-expressions package uses a three-layer protocol architecture:

1. **VisitorProtocol** - AST node traversal (being replaced by unified visitor)
2. **ExpressionProtocol** - Backend primitive operations
3. **BuilderProtocol** - User-facing fluent API

During the Substrait alignment refactoring, ExpressionProtocols were auto-generated from Substrait YAML specifications and placed in `expression_protocols/substrait/`. However, the corresponding BuilderProtocols were not created, leaving the protocol layer incomplete.

### Current State

| Directory | ExpressionProtocol | BuilderProtocol |
|-----------|-------------------|-----------------|
| `deprecated/` | 11 protocols | 11 protocols |
| `substrait/` | 13 protocols | **0 protocols** |
| `extensions/` | 9 protocols | 0 protocols |

The namespaces currently rely on deprecated BuilderProtocols for type contracts.

## Decision

Create BuilderProtocols for all Substrait ExpressionProtocols in the same files:

### Protocols to Create (13 total)

1. **ScalarComparisonBuilderProtocol** - Comparison operations (24 methods)
2. **ScalarBooleanBuilderProtocol** - Boolean logic (5 methods)
3. **ScalarArithmeticBuilderProtocol** - Arithmetic operations (7 methods)
4. **ScalarStringBuilderProtocol** - String operations (30+ methods)
5. **ScalarDatetimeBuilderProtocol** - Temporal operations (2+ methods)
6. **LiteralBuilderProtocol** - Literal creation
7. **FieldReferenceBuilderProtocol** - Column references
8. **CastBuilderProtocol** - Type casting
9. **ConditionalBuilderProtocol** - When/then/otherwise
10. **ScalarSetBuilderProtocol** - Set membership
11. **ScalarRoundingBuilderProtocol** - Rounding functions
12. **ScalarLogarithmicBuilderProtocol** - Logarithmic functions
13. **ScalarAggregateBuilderProtocol** - Aggregate functions

### Naming Convention

Use Substrait-aligned naming:
- `ScalarComparisonBuilderProtocol` (not `ComparisonBuilderProtocol`)
- `ScalarStringBuilderProtocol` (not `StringBuilderProtocol`)

### File Placement

Add BuilderProtocol to the same file as ExpressionProtocol:
- `prtcl_scalar_comparison.py` contains both `ScalarComparisonExpressionProtocol` and `ScalarComparisonBuilderProtocol`

### Implementation Pattern

```python
class ScalarComparisonBuilderProtocol(Protocol):
    """Builder protocol for comparison operations."""

    def equal(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Equal comparison (==).

        Substrait: equal
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...
```

Key characteristics:
- Return type: `BaseNamespace` (for fluent chaining)
- Input type: `Union[BaseNamespace, ExpressionNode, Any]` (flexible)
- Variadic ops use `*args`
- Docstrings include Substrait function name and URI

## Consequences

### Positive

- Completes the three-layer protocol architecture for Substrait alignment
- Provides type contracts for namespace implementations
- Enables IDE autocompletion and static type checking
- Maintains consistency with deprecated protocol pattern
- Documents Substrait function mappings in docstrings

### Negative

- 13 new protocol classes to maintain
- Some methods may not yet have namespace implementations
- Potential for drift between ExpressionProtocol and BuilderProtocol

### Neutral

- Does not change public API
- Does not require immediate namespace updates
- Extensions directory deferred to Phase 2

## Alternatives Considered

1. **Skip BuilderProtocols entirely**: Rely only on ExpressionProtocols
   - Rejected: Loses type contracts for namespace layer

2. **Generate BuilderProtocols automatically**: Script to derive from ExpressionProtocol
   - Considered but deferred: Would require signature transformation logic

3. **Merge with deprecated protocols**: Add Substrait methods to existing files
   - Rejected: Want clean separation between deprecated and new architecture

## References

- [Substrait Extensions](https://substrait.io/extensions/)
- [SUBSTRAIT_ALIGNMENT_PLAN.md](../SubtraitAlignment/SUBSTRAIT_ALIGNMENT_PLAN.md)
- [deprecated/boolean_protocols.py](../../src/mountainash_expressions/core/expression_protocols/deprecated/boolean_protocols.py)

## Tasks

- [ ] Add ScalarComparisonBuilderProtocol to prtcl_scalar_comparison.py
- [ ] Add ScalarBooleanBuilderProtocol to prtcl_scalar_boolean.py
- [ ] Add ScalarArithmeticBuilderProtocol to prtcl_scalar_arithmetic.py
- [ ] Add ScalarStringBuilderProtocol to prtcl_scalar_string.py
- [ ] Add ScalarDatetimeBuilderProtocol to prtcl_scalar_datetime.py
- [ ] Add LiteralBuilderProtocol to prtcl_literal.py
- [ ] Add FieldReferenceBuilderProtocol to prtcl_field_reference.py
- [ ] Add CastBuilderProtocol to prtcl_cast.py
- [ ] Add ConditionalBuilderProtocol to prtcl_conditional.py
- [ ] Add ScalarSetBuilderProtocol to prtcl_scalar_set.py
- [ ] Add ScalarRoundingBuilderProtocol to prtcl_scalar_rounding.py
- [ ] Add ScalarLogarithmicBuilderProtocol to prtcl_scalar_logarithmic.py
- [ ] Add ScalarAggregateBuilderProtocol to prtcl_scalar_aggregate.py
- [ ] Update substrait/__init__.py with exports
- [ ] Verify imports work correctly

## Completion Criteria

- [ ] ADR updated to ACCEPTED
- [ ] All 13 BuilderProtocols implemented
- [ ] Tests pass
- [ ] Documentation updated
