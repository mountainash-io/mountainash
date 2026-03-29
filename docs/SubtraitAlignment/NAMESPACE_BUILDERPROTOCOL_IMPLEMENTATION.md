# Namespace BuilderProtocol Implementation Plan

## Overview

This document outlines the plan to implement the remaining core namespaces in `api_namespaces/core/` with explicit BuilderProtocol inheritance. This creates a type-safe, IDE-friendly API layer that aligns with the Substrait-aligned protocols.

## Background

### Three-Layer Protocol Architecture

The expression system uses a three-layer protocol design:

1. **ExpressionProtocol** - Backend-specific primitive operations (implemented by backends)
2. **BuilderProtocol** - User-facing fluent API definitions (what namespaces implement)
3. **VisitorProtocol** - AST traversal for compilation (not in scope here)

### Current State

The BuilderProtocols were recently added to the substrait expression protocols:

```
src/mountainash_expressions/core/expression_protocols/substrait/
├── prtcl_scalar_comparison.py  → ScalarComparisonBuilderProtocol
├── prtcl_scalar_boolean.py     → ScalarBooleanBuilderProtocol
├── prtcl_scalar_arithmetic.py  → ScalarArithmeticBuilderProtocol
├── prtcl_scalar_string.py      → ScalarStringBuilderProtocol
├── prtcl_scalar_datetime.py    → ScalarDatetimeBuilderProtocol
├── prtcl_scalar_set.py         → ScalarSetBuilderProtocol
├── prtcl_scalar_rounding.py    → ScalarRoundingBuilderProtocol
├── prtcl_scalar_logarithmic.py → ScalarLogarithmicBuilderProtocol
├── prtcl_scalar_aggregate.py   → ScalarAggregateBuilderProtocol
├── prtcl_cast.py               → CastBuilderProtocol
└── prtcl_conditional.py        → ConditionalBuilderProtocol, WhenBuilderProtocol, ThenBuilderProtocol
```

### Gap Analysis

The namespace implementations need to:
1. Explicitly inherit from their corresponding BuilderProtocols
2. Complete stub implementations with full method coverage
3. Use Substrait-aligned function enums

## Architecture

### Namespace Inheritance Pattern

```python
from ..expression_protocols.substrait import ScalarStringBuilderProtocol
from .ns_base import BaseExpressionNamespace

class StringNamespace(BaseExpressionNamespace, ScalarStringBuilderProtocol):
    """String operations implementing ScalarStringBuilderProtocol."""

    def upper(self) -> BaseExpressionAPI:
        """Convert to uppercase. Substrait: upper"""
        node = ScalarFunctionNode(
            function=SUBSTRAIT_STRING.UPPER,
            arguments=[self._node],
        )
        return self._build(node)
```

### Benefits of Explicit Inheritance

1. **Type Safety**: IDE and mypy can verify method signatures match protocol
2. **Documentation**: Clear contract between API and protocols
3. **Discoverability**: IDE autocomplete shows all available methods
4. **Refactoring Safety**: Changes to protocols surface implementation gaps

### Namespace Categories

| Category | Accessor | Namespace Class | BuilderProtocol |
|----------|----------|-----------------|-----------------|
| **Flat** (direct access) | `expr.eq()` | BooleanNamespace | ScalarBooleanBuilderProtocol |
| **Flat** | `expr.add()` | ArithmeticNamespace | ScalarArithmeticBuilderProtocol |
| **Flat** | `expr.is_in()` | SetNamespace | ScalarSetBuilderProtocol |
| **Flat** | `expr.cast()` | CastNamespace | CastBuilderProtocol |
| **Explicit** | `expr.str.upper()` | StringNamespace | ScalarStringBuilderProtocol |
| **Explicit** | `expr.dt.year()` | DateTimeNamespace | ScalarDatetimeBuilderProtocol |

## Implementation Status

### Complete (need protocol inheritance added)

| File | Lines | Protocol to Add |
|------|-------|-----------------|
| `exns_scalar_boolean.py` | 379 | ScalarBooleanBuilderProtocol |
| `exns_scalar_arithmetic.py` | 300 | ScalarArithmeticBuilderProtocol |

### Stub (need full implementation)

| File | Lines | Protocol to Implement |
|------|-------|----------------------|
| `exns_scalar_comparison.py` | 28 | ScalarComparisonBuilderProtocol |
| `exns_scalar_string.py` | 28 | ScalarStringBuilderProtocol |
| `exns_scalar_datetime.py` | 28 | ScalarDatetimeBuilderProtocol |
| `exns_scalar_set.py` | 33 | ScalarSetBuilderProtocol |
| `exns_scalar_rounding.py` | 28 | ScalarRoundingBuilderProtocol |
| `exns_scalar_logarithmic.py` | 28 | ScalarLogarithmicBuilderProtocol |
| `exns_scalar_aggregate.py` | 28 | ScalarAggregateBuilderProtocol |
| `exns_cast.py` | 26 | CastBuilderProtocol |
| `exns_conditional.py` | 28 | ConditionalBuilderProtocol |

## Enum Requirements

### Missing Substrait Enums

The following enums need to be added to `expression_nodes/enums/substrait.py`:

```python
class SUBSTRAIT_ROUNDING(Enum):
    """Rounding functions from Substrait rounding extension."""
    CEIL = auto()
    FLOOR = auto()
    ROUND = auto()

class SUBSTRAIT_LOGARITHMIC(Enum):
    """Logarithmic functions from Substrait logarithmic extension."""
    LN = auto()
    LOG10 = auto()
    LOG2 = auto()
    LOGB = auto()

class SUBSTRAIT_SET(Enum):
    """Set functions from Substrait set extension."""
    INDEX_IN = auto()

class SUBSTRAIT_AGGREGATE(Enum):
    """Aggregate functions from Substrait aggregate_generic extension."""
    COUNT = auto()
    ANY_VALUE = auto()
```

### Ensure Complete String Enums

Verify `SUBSTRAIT_STRING` includes all operations from ScalarStringBuilderProtocol:
- Case: UPPER, LOWER, SWAPCASE, CAPITALIZE, TITLE, INITCAP
- Trim: LTRIM, RTRIM, TRIM
- Pad: LPAD, RPAD, CENTER
- Extract: SUBSTRING, LEFT, RIGHT, CHAR_LENGTH, BIT_LENGTH, OCTET_LENGTH
- Search: CONTAINS, STARTS_WITH, ENDS_WITH, STRPOS, COUNT_SUBSTRING
- Replace: REPLACE, REGEXP_REPLACE, REPLACE_SLICE
- Pattern: LIKE, REGEXP_MATCH_SUBSTRING
- Split/Join: CONCAT, CONCAT_WS, STRING_SPLIT, REGEXP_STRING_SPLIT
- Other: REPEAT, REVERSE

## Implementation Order

### Phase 1: Enums and Protocol Inheritance
1. Add missing enums to `substrait.py`
2. Update `exns_scalar_boolean.py` with protocol inheritance
3. Update `exns_scalar_arithmetic.py` with protocol inheritance

### Phase 2: Core Namespaces
4. Implement `exns_scalar_comparison.py` (22 methods)
5. Implement `exns_scalar_string.py` (~30 methods)
6. Implement `exns_scalar_datetime.py` (~35 methods)

### Phase 3: Specialized Namespaces
7. Implement `exns_scalar_set.py` (3 methods)
8. Implement `exns_scalar_rounding.py` (3 methods)
9. Implement `exns_scalar_logarithmic.py` (4 methods)
10. Implement `exns_scalar_aggregate.py` (2 methods)

### Phase 4: Foundation Namespaces
11. Implement `exns_cast.py` (1 method)
12. Implement `exns_conditional.py` (when/then/otherwise pattern)

### Phase 5: Integration
13. Update `api_namespaces/__init__.py` exports

## Reference Implementations

The deprecated namespace implementations provide reference patterns:

```
src/mountainash_expressions/core/expression_api/api_namespaces/deprecated/
├── boolean.py         → Comparison and logical patterns
├── scalar_string.py   → String operation patterns
├── datetime.py        → Datetime patterns
├── conditional.py     → When/then/otherwise pattern
└── cast.py           → Cast pattern
```

## Method Implementation Pattern

### Binary Operation
```python
def equal(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """Equal comparison. Substrait: equal"""
    other_node = self._to_substrait_node(other)
    node = ScalarFunctionNode(
        function=SUBSTRAIT_COMPARISON.EQ,
        arguments=[self._node, other_node],
    )
    return self._build(node)
```

### Unary Operation
```python
def upper(self) -> BaseExpressionAPI:
    """Convert to uppercase. Substrait: upper"""
    node = ScalarFunctionNode(
        function=SUBSTRAIT_STRING.UPPER,
        arguments=[self._node],
    )
    return self._build(node)
```

### Variadic Operation
```python
def and_(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """Logical AND. Substrait: and"""
    if not others:
        return self._build(self._node)

    operands = [self._node] + [self._to_substrait_node(o) for o in others]
    result = operands[0]
    for operand in operands[1:]:
        result = ScalarFunctionNode(
            function=SUBSTRAIT_BOOLEAN.AND,
            arguments=[result, operand],
        )
    return self._build(result)
```

### Collection Operation (is_in)
```python
def is_in(self, *values: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """Check membership. Substrait: index_in (>= 0)"""
    value_nodes = [
        LiteralNode(value=v) if not isinstance(v, ExpressionNode) else v
        for v in values
    ]
    node = SingularOrListNode(
        value=self._node,
        options=value_nodes,
    )
    return self._build(node)
```

## Estimated Effort

| Component | Estimated Lines |
|-----------|-----------------|
| Enum additions | ~50 |
| Protocol inheritance updates | ~20 |
| ScalarComparisonNamespace | ~250 |
| StringNamespace | ~400 |
| DateTimeNamespace | ~400 |
| ScalarSetNamespace | ~50 |
| ScalarRoundingNamespace | ~40 |
| ScalarLogarithmicNamespace | ~50 |
| ScalarAggregateNamespace | ~30 |
| CastNamespace | ~30 |
| ConditionalNamespace | ~100 |
| Export updates | ~30 |
| **Total** | **~2,500-3,500** |

## Success Criteria

1. All namespace classes explicitly inherit from their BuilderProtocols
2. All BuilderProtocol methods are implemented
3. Type checking passes (mypy)
4. Existing tests continue to pass
5. New methods are accessible via the expression API
