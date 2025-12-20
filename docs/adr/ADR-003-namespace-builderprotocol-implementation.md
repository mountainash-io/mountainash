# ADR-003: Namespace BuilderProtocol Implementation

**Status**: PROPOSED
**Date**: 2025-12-20
**Deciders**: @nathanielramm
**Supersedes**: None
**Related**: ADR-002 (Substrait BuilderProtocol Migration)

## Context

ADR-002 established BuilderProtocols in `expression_protocols/substrait/` for all Substrait-aligned operations. These protocols define the user-facing fluent API contract. However, the namespace implementations in `api_namespaces/core/` do not yet:

1. Explicitly inherit from their corresponding BuilderProtocols
2. Have complete method implementations (most are stubs)
3. Use Substrait-aligned function enums consistently

### Current State

| Namespace File | Status | Lines | BuilderProtocol |
|---------------|--------|-------|-----------------|
| `exns_scalar_boolean.py` | Complete | 379 | ScalarBooleanBuilderProtocol |
| `exns_scalar_arithmetic.py` | Complete | 300 | ScalarArithmeticBuilderProtocol |
| `exns_scalar_comparison.py` | **Stub** | 28 | ScalarComparisonBuilderProtocol |
| `exns_scalar_string.py` | **Stub** | 28 | ScalarStringBuilderProtocol |
| `exns_scalar_datetime.py` | **Stub** | 28 | ScalarDatetimeBuilderProtocol |
| `exns_scalar_set.py` | **Stub** | 33 | ScalarSetBuilderProtocol |
| `exns_scalar_rounding.py` | **Stub** | 28 | ScalarRoundingBuilderProtocol |
| `exns_scalar_logarithmic.py` | **Stub** | 28 | ScalarLogarithmicBuilderProtocol |
| `exns_scalar_aggregate.py` | **Stub** | 28 | ScalarAggregateBuilderProtocol |
| `exns_cast.py` | **Stub** | 26 | CastBuilderProtocol |
| `exns_conditional.py` | **Stub** | 28 | ConditionalBuilderProtocol |

### Gap Analysis

1. **9 stub namespaces** need full implementation (~200-400 lines each)
2. **2 complete namespaces** need protocol inheritance added
3. **Missing enums** in `substrait.py`: ROUNDING, LOGARITHMIC, SET, AGGREGATE
4. **Reference implementations** exist in `api_namespaces/deprecated/`

## Decision

### 1. Explicit Protocol Inheritance

All namespace classes will explicitly inherit from their BuilderProtocols:

```python
from ..expression_protocols.substrait import ScalarStringBuilderProtocol
from .ns_base import BaseExpressionNamespace

class StringNamespace(BaseExpressionNamespace, ScalarStringBuilderProtocol):
    """String operations implementing ScalarStringBuilderProtocol."""
```

### 2. Implementation Pattern

All namespace methods will follow this pattern:

```python
def upper(self) -> BaseExpressionAPI:
    """Convert to uppercase. Substrait: upper"""
    node = ScalarFunctionNode(
        function=SUBSTRAIT_STRING.UPPER,
        arguments=[self._node],
    )
    return self._build(node)
```

Key characteristics:
- Use `ScalarFunctionNode` with Substrait function enums
- Use `self._to_substrait_node(other)` for input coercion
- Use `self._build(node)` for fluent chaining
- Document Substrait function name in docstring

### 3. Enum Additions

Add missing enums to `expression_nodes/enums/substrait.py`:

```python
class SUBSTRAIT_ROUNDING(Enum):
    CEIL = auto()
    FLOOR = auto()
    ROUND = auto()

class SUBSTRAIT_LOGARITHMIC(Enum):
    LN = auto()
    LOG10 = auto()
    LOG2 = auto()
    LOGB = auto()

class SUBSTRAIT_SET(Enum):
    INDEX_IN = auto()

class SUBSTRAIT_AGGREGATE(Enum):
    COUNT = auto()
    ANY_VALUE = auto()
```

### 4. Namespace Categories

| Category | Accessor | Namespace Class | Example Usage |
|----------|----------|-----------------|---------------|
| **Flat** | Direct | ScalarBooleanNamespace | `expr.eq()` |
| **Flat** | Direct | ScalarArithmeticNamespace | `expr.add()` |
| **Flat** | Direct | ScalarComparisonNamespace | `expr.between()` |
| **Flat** | Direct | ScalarSetNamespace | `expr.is_in()` |
| **Flat** | Direct | CastNamespace | `expr.cast()` |
| **Explicit** | `.str` | StringNamespace | `expr.str.upper()` |
| **Explicit** | `.dt` | DateTimeNamespace | `expr.dt.year()` |

### 5. Implementation Phases

**Phase 1: Enums and Protocol Inheritance**
1. Add missing enums to `substrait.py`
2. Update `exns_scalar_boolean.py` with protocol inheritance
3. Update `exns_scalar_arithmetic.py` with protocol inheritance

**Phase 2: Core Namespaces**
4. Implement `exns_scalar_comparison.py` (22 methods)
5. Implement `exns_scalar_string.py` (~30 methods)
6. Implement `exns_scalar_datetime.py` (~35 methods)

**Phase 3: Specialized Namespaces**
7. Implement `exns_scalar_set.py` (3 methods)
8. Implement `exns_scalar_rounding.py` (3 methods)
9. Implement `exns_scalar_logarithmic.py` (4 methods)
10. Implement `exns_scalar_aggregate.py` (2 methods)

**Phase 4: Foundation Namespaces**
11. Implement `exns_cast.py` (1 method)
12. Implement `exns_conditional.py` (when/then/otherwise pattern)

**Phase 5: Integration**
13. Update `api_namespaces/__init__.py` exports

## Consequences

### Positive

- **Type Safety**: IDE and mypy verify method signatures match protocols
- **Documentation**: Clear contract between API and protocols
- **Discoverability**: IDE autocomplete shows all available methods
- **Refactoring Safety**: Protocol changes surface implementation gaps
- **Substrait Alignment**: Consistent function naming with Substrait spec
- **Maintainability**: Reference implementations available in deprecated/

### Negative

- **Implementation Effort**: ~2,500-3,500 lines of new code
- **Temporary Duplication**: Reference implementations exist until migration complete
- **Learning Curve**: New pattern for contributors

### Neutral

- **No API Changes**: Public interface remains the same
- **Backward Compatible**: Existing code continues to work
- **Gradual Migration**: Namespaces can be implemented incrementally

## Alternatives Considered

1. **Generate namespaces automatically from protocols**
   - Rejected: Lose semantic meaning and custom logic

2. **Keep namespaces without protocol inheritance**
   - Rejected: Lose type safety and IDE support

3. **Merge deprecated implementations directly**
   - Rejected: Want clean implementation following new patterns

4. **Implement all at once**
   - Rejected: Phased approach allows testing and iteration

## References

- [ADR-002: Substrait BuilderProtocol Migration](./ADR-002-substrait-builder-protocols.md)
- [NAMESPACE_BUILDERPROTOCOL_IMPLEMENTATION.md](../SubtraitAlignment/NAMESPACE_BUILDERPROTOCOL_IMPLEMENTATION.md)
- [Substrait Function Extensions](https://substrait.io/extensions/)

## Tasks

### Phase 1: Enums and Protocol Inheritance
- [ ] Add SUBSTRAIT_ROUNDING enum to substrait.py
- [ ] Add SUBSTRAIT_LOGARITHMIC enum to substrait.py
- [ ] Add SUBSTRAIT_SET enum to substrait.py
- [ ] Add SUBSTRAIT_AGGREGATE enum to substrait.py
- [ ] Update exns_scalar_boolean.py with ScalarBooleanBuilderProtocol inheritance
- [ ] Update exns_scalar_arithmetic.py with ScalarArithmeticBuilderProtocol inheritance

### Phase 2: Core Namespaces
- [ ] Implement exns_scalar_comparison.py with ScalarComparisonBuilderProtocol
- [ ] Implement exns_scalar_string.py with ScalarStringBuilderProtocol
- [ ] Implement exns_scalar_datetime.py with ScalarDatetimeBuilderProtocol

### Phase 3: Specialized Namespaces
- [ ] Implement exns_scalar_set.py with ScalarSetBuilderProtocol
- [ ] Implement exns_scalar_rounding.py with ScalarRoundingBuilderProtocol
- [ ] Implement exns_scalar_logarithmic.py with ScalarLogarithmicBuilderProtocol
- [ ] Implement exns_scalar_aggregate.py with ScalarAggregateBuilderProtocol

### Phase 4: Foundation Namespaces
- [ ] Implement exns_cast.py with CastBuilderProtocol
- [ ] Implement exns_conditional.py with ConditionalBuilderProtocol

### Phase 5: Integration
- [ ] Update api_namespaces/__init__.py exports
- [ ] Verify type checking passes (mypy)
- [ ] Ensure existing tests pass

## Completion Criteria

- [ ] ADR updated to ACCEPTED
- [ ] All 11 namespace files implement their BuilderProtocols
- [ ] All BuilderProtocol methods are implemented
- [ ] Missing enums added to substrait.py
- [ ] Type checking passes
- [ ] Existing tests continue to pass
- [ ] New methods accessible via expression API
