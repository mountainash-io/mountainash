# ADR-001: SingularOrList Node Implementation

**Status**: PROPOSED
**Issues**: [#1](https://github.com/mountainash-io/mountainash-expressions/issues/1), [#2](https://github.com/mountainash-io/mountainash-expressions/issues/2), [#3](https://github.com/mountainash-io/mountainash-expressions/issues/3), [#4](https://github.com/mountainash-io/mountainash-expressions/issues/4)
**Milestone**: [Phase 1: Foundation](https://github.com/mountainash-io/mountainash-expressions/milestone/1)
**Date**: 2025-12-20
**Deciders**: @nathanielramm
**Milestone**: 1 (Foundation)

## Context

The mountainash-expressions package declares `SingularOrListNode` in its `__init__.py` exports, but the implementation file `exn_singular_or_list.py` does not exist. This causes:

1. Import errors when attempting to use SingularOrListNode
2. Incomplete Substrait expression type coverage
3. No support for IN operator / membership tests

Substrait defines `SingularOrList` as one of 6 core expression types for membership testing.

## Decision

Create `SingularOrListNode` as a proper expression node class that:

1. Follows the existing node pattern (dataclass with `accept()` method)
2. Maps directly to Substrait's `SingularOrList` expression type
3. Supports the IN operator semantics
4. Integrates with UnifiedExpressionVisitor

### Implementation

```python
# exn_singular_or_list.py
from dataclasses import dataclass
from typing import List, Any, TYPE_CHECKING

from .exn_base import ExpressionNode

if TYPE_CHECKING:
    from ..unified_visitor.visitor import ExpressionVisitor

@dataclass
class SingularOrListNode(ExpressionNode):
    """
    Substrait SingularOrList expression.

    Tests if a value is contained within a list of options.
    Equivalent to SQL: value IN (option1, option2, ...)
    """
    value: ExpressionNode
    options: List[ExpressionNode]

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_singular_or_list(self)

    def to_substrait(self):
        raise NotImplementedError("Phase 7: Substrait serialization")

    @classmethod
    def from_substrait(cls, expr):
        raise NotImplementedError("Phase 7: Substrait serialization")
```

### Visitor Integration

```python
# In UnifiedExpressionVisitor
def visit_singular_or_list(self, node: SingularOrListNode) -> Any:
    value = self.visit(node.value)
    options = [self.visit(opt) for opt in node.options]
    return self.backend.is_in(value, options)
```

## Consequences

### Positive
- Completes the 6 Substrait expression types
- Enables IN operator support across all backends
- Removes import errors

### Negative
- Requires backend implementations (is_in for each backend)
- Increases test surface area

### Neutral
- Aligns with existing node pattern - no architectural changes

## References

- Substrait Spec: [SingularOrList](https://substrait.io/expressions/specialized_record_expressions/)
- Deprecated Reference: `_deprecated/202511/expression_nodes/BooleanCollectionExpressionNode`

## Tasks

- [ ] Create `exn_singular_or_list.py`
- [ ] Add `visit_singular_or_list()` to UnifiedExpressionVisitor
- [ ] Implement `is_in()` in Polars backend
- [ ] Implement `is_in()` in Narwhals backend
- [ ] Implement `is_in()` in Ibis backend
- [ ] Add tests for SingularOrListNode
- [ ] Update `__init__.py` to export properly

## Completion Criteria

- [ ] ADR updated to ACCEPTED
- [ ] All tasks complete
- [ ] Tests passing
