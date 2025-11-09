# Unified Protocol Architecture

**Date:** 2025-01-09
**Status:** Refined Architecture - Simplified from Dual Protocol Approach
**Key Insight:** Remove artificial separation - use shared base protocols

---

## Executive Summary

**Original Proposal:** 16 protocols (8 visitor + 8 backend, paired)
**Refined Approach:** 16 protocols (8 base operations + 8 visitor extensions)
**Key Difference:** Backends and visitors implement THE SAME base protocols
**Artifact to Remove:** `_B_` prefix on visitor methods (legacy artifact)

---

## The Architectural Insight

### Current Problem: Artificial Duplication

```python
# Visitor Protocol (proposed in dual approach)
class ComparisonVisitorProtocol(Protocol):
    def _B_eq(self, left, right) -> Any: ...  # Different name
    def _B_ne(self, left, right) -> Any: ...

# Backend Protocol (proposed in dual approach)
class ComparisonBackendProtocol(Protocol):
    def eq(self, left, right) -> Any: ...     # Different name
    def ne(self, left, right) -> Any: ...
```

**Problem:** These are the SAME operations, just with different names due to legacy `_B_` prefix!

### Solution: Shared Base Protocols

```python
# One base protocol for operations (implemented by BOTH)
@runtime_checkable
class ComparisonOperations(Protocol):
    """Comparison operations - implemented by both visitors and backends."""

    def eq(self, left: Any, right: Any) -> Any:
        """Equality comparison."""
        ...

    def ne(self, left: Any, right: Any) -> Any:
        """Inequality comparison."""
        ...

    def gt(self, left: Any, right: Any) -> Any:
        """Greater-than comparison."""
        ...

    def lt(self, left: Any, right: Any) -> Any:
        """Less-than comparison."""
        ...

    def ge(self, left: Any, right: Any) -> Any:
        """Greater-than-or-equal comparison."""
        ...

    def le(self, left: Any, right: Any) -> Any:
        """Less-than-or-equal comparison."""
        ...


# Visitor protocol extends base + adds visit method
@runtime_checkable
class ComparisonVisitor(ComparisonOperations, Protocol):
    """Visitor for comparison expressions - extends operations with AST traversal."""

    def visit_comparison_expression(self, node: ComparisonExpressionNode) -> Any:
        """Process comparison expression AST node."""
        ...

    # Inherits: eq, ne, gt, lt, ge, le from ComparisonOperations
```

**Result:**
- Backend implements `ComparisonOperations` → has `eq()`, `ne()`, etc.
- Visitor implements `ComparisonVisitor` → has `eq()`, `ne()`, etc. PLUS `visit_comparison_expression()`
- **Same method names**, same protocol, no duplication!

---

## Complete Protocol Structure

### 8 Base Operations Protocols (Shared)

Both visitors AND backends implement these:

1. **ComparisonOperations**
   - Methods: `eq`, `ne`, `gt`, `lt`, `ge`, `le`

2. **ArithmeticOperations**
   - Methods: `add`, `sub`, `mul`, `div`, `mod`, `pow`

3. **StringOperations**
   - Methods: `contains`, `startswith`, `endswith`, `lower`, `upper`, `strip`, `len`, `slice`, `concat`

4. **PatternOperations**
   - Methods: `regex_match`, `glob_match`, `like`

5. **ConditionalOperations**
   - Methods: `if_else`, `when_then_otherwise`, `coalesce`

6. **TemporalOperations**
   - Methods: `year`, `month`, `day`, `hour`, `minute`, `second`, `date`, `time`, `timestamp`

7. **CommonOperations**
   - Methods: `col`, `lit`, `cast`, `native`, `is_null`, `is_not_null`

8. **BooleanLogicOperations**
   - Methods: `and_`, `or_`, `not_`, `is_in`, `is_not_in`

### 8 Visitor Protocols (Extend Base)

Visitors implement these (which include base operations):

1. **ComparisonVisitor** extends ComparisonOperations
   - Adds: `visit_comparison_expression()`

2. **ArithmeticVisitor** extends ArithmeticOperations
   - Adds: `visit_arithmetic_expression()`

3. **StringVisitor** extends StringOperations
   - Adds: `visit_string_expression()`

4. **PatternVisitor** extends PatternOperations
   - Adds: `visit_pattern_expression()`

5. **ConditionalVisitor** extends ConditionalOperations
   - Adds: `visit_conditional_expression()`, `visit_when_then_expression()`

6. **TemporalVisitor** extends TemporalOperations
   - Adds: `visit_temporal_expression()`

7. **CommonVisitor** extends CommonOperations
   - Adds: `visit_source_expression()`, `visit_literal_expression()`, `visit_cast_expression()`, `visit_native_expression()`

8. **BooleanLogicVisitor** extends BooleanLogicOperations
   - Adds: `visit_logical_expression()`, `visit_collection_expression()`, `visit_unary_expression()`

---

## Implementation Pattern

### Backend Implementation

```python
class PolarsExpressionSystem(
    ComparisonOperations,
    ArithmeticOperations,
    StringOperations,
    PatternOperations,
    ConditionalOperations,
    TemporalOperations,
    CommonOperations,
    BooleanLogicOperations,
):
    """Polars backend - implements base operations protocols."""

    def eq(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Actual implementation for Polars."""
        return left == right

    def ne(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left != right

    # ... etc. - all operations are ACTUAL implementations
```

### Visitor Implementation

```python
class UniversalBooleanVisitor(
    ComparisonVisitor,
    ArithmeticVisitor,
    StringVisitor,
    PatternVisitor,
    ConditionalVisitor,
    TemporalVisitor,
    CommonVisitor,
    BooleanLogicVisitor,
):
    """Universal visitor - implements visitor protocols (which extend operations)."""

    def __init__(self, backend: ComparisonOperations & ArithmeticOperations & ...):
        self.backend = backend

    # Implements operations by delegating to backend
    def eq(self, left: Any, right: Any) -> Any:
        """Visitor's delegating implementation."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.eq(left_expr, right_expr)

    # Implements AST traversal
    def visit_comparison_expression(self, node: ComparisonExpressionNode) -> Any:
        """Process AST node."""
        left_param = ExpressionParameter(node.left)
        right_param = ExpressionParameter(node.right)
        left_resolved = left_param.resolve_to_expression_node()
        right_resolved = right_param.resolve_to_expression_node()

        op_func = self.boolean_comparison_ops[node.operator]
        return op_func(left_resolved, right_resolved)  # Calls self.eq(), self.ne(), etc.
```

---

## Key Changes from Current Code

### 1. Remove `_B_` Prefix

**Current:**
```python
# Visitor mixin
@abstractmethod
def _B_eq(self, left, right) -> Any:
    pass

# UniversalBooleanVisitor
def _B_eq(self, left, right) -> Any:
    left_expr = self._process_operand(left)
    right_expr = self._process_operand(right)
    return self.backend.eq(left_expr, right_expr)
```

**Refactored:**
```python
# Visitor mixin (now using protocol)
# Protocol defines eq(), not _B_eq()

# UniversalBooleanVisitor
def eq(self, left, right) -> Any:
    """Implements ComparisonOperations protocol by delegating."""
    left_expr = self._process_operand(left)
    right_expr = self._process_operand(right)
    return self.backend.eq(left_expr, right_expr)
```

### 2. Align Method Names

**Before:**
- Visitor: `_B_eq()`, `_B_ne()`, `_B_gt()`
- Backend: `eq()`, `ne()`, `gt()`

**After:**
- Visitor: `eq()`, `ne()`, `gt()` (delegates to backend)
- Backend: `eq()`, `ne()`, `gt()` (actual implementation)
- **Same names, same protocol!**

### 3. Update Operation Dictionaries

**Current:**
```python
@property
def boolean_comparison_ops(self) -> Dict[str, Callable]:
    return {
        CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.EQ: self._B_eq,
        CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.NE: self._B_ne,
        # ...
    }
```

**Refactored:**
```python
@property
def boolean_comparison_ops(self) -> Dict[str, Callable]:
    return {
        CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.EQ: self.eq,  # No _B_ prefix
        CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.NE: self.ne,  # No _B_ prefix
        # ...
    }
```

---

## Directory Structure

```
src/mountainash_expressions/
├── core/
│   ├── protocols/                           # NEW: Shared protocols
│   │   ├── __init__.py
│   │   ├── operations/                      # Base operations protocols (8)
│   │   │   ├── __init__.py
│   │   │   ├── comparison.py               # ComparisonOperations
│   │   │   ├── arithmetic.py               # ArithmeticOperations
│   │   │   ├── string.py                   # StringOperations
│   │   │   ├── pattern.py                  # PatternOperations
│   │   │   ├── conditional.py              # ConditionalOperations
│   │   │   ├── temporal.py                 # TemporalOperations
│   │   │   ├── common.py                   # CommonOperations
│   │   │   └── boolean_logic.py            # BooleanLogicOperations
│   │   │
│   │   └── visitors/                       # Visitor protocols (8)
│   │       ├── __init__.py
│   │       ├── comparison_visitor.py       # ComparisonVisitor extends ComparisonOperations
│   │       ├── arithmetic_visitor.py       # ArithmeticVisitor extends ArithmeticOperations
│   │       ├── string_visitor.py           # StringVisitor extends StringOperations
│   │       ├── pattern_visitor.py          # PatternVisitor extends PatternOperations
│   │       ├── conditional_visitor.py      # ConditionalVisitor extends ConditionalOperations
│   │       ├── temporal_visitor.py         # TemporalVisitor extends TemporalOperations
│   │       ├── common_visitor.py           # CommonVisitor extends CommonOperations
│   │       └── boolean_logic_visitor.py    # BooleanLogicVisitor extends BooleanLogicOperations
│   │
│   ├── expression_visitors/
│   │   ├── universal_boolean_visitor.py    # Implements 8 visitor protocols
│   │   └── ...
│   │
│   └── expression_system/
│       └── base.py                          # May still exist for shared utilities
│
└── backends/
    ├── polars/
    │   └── expression_system/
    │       └── polars_expression_system.py  # Implements 8 operations protocols
    │
    ├── narwhals/
    │   └── expression_system/
    │       └── narwhals_expression_system.py # Implements 8 operations protocols
    │
    └── ibis/
        └── expression_system/
            └── ibis_expression_system.py    # Implements 8 operations protocols
```

---

## Conceptual Clarity

### Old Mental Model (Dual Protocols)

```
Visitor Protocols (8)  ←→  Backend Protocols (8)
      ↓                           ↓
  Visitors               Backends

"Two separate protocol hierarchies that need to stay aligned"
```

### New Mental Model (Shared Base)

```
      Operations Protocols (8)
           ↙          ↘
    Backends      Visitor Protocols (8)
                        ↓
                    Visitors

"One set of operations, implemented by both backends and visitors"
```

**Key Insight:** Backends implement operations directly, visitors implement operations by delegating to backend. Both follow the same protocol!

---

## Type Safety Benefits

### Compiler Enforces Alignment

```python
# Backend MUST implement all operations
class PolarsExpressionSystem(ComparisonOperations):
    # Missing eq()? → Type error!
    def ne(self, left, right): ...
    # ... etc.

# Visitor MUST implement all operations + visit methods
class UniversalBooleanVisitor(ComparisonVisitor):
    # Missing eq()? → Type error!
    # Missing visit_comparison_expression()? → Type error!
    def ne(self, left, right): ...
    # ... etc.

# Type checker ensures alignment automatically
def create_visitor(backend: ComparisonOperations) -> ComparisonVisitor:
    return UniversalBooleanVisitor(backend)  # Type safe!
```

### No Naming Drift

Since both implement the same base protocol:
- Can't rename backend method without updating visitor
- Can't rename visitor method without updating backend
- Compiler enforces consistency

---

## Migration Impact

### Low Risk Changes

1. **Protocol definitions** - NEW files, no existing code changes
2. **Backend signature changes** - Already correct (already use `eq`, `ne`, etc.)
3. **Visitor method renaming** - `_B_eq` → `eq` (search/replace, test)
4. **Operation dictionary updates** - Update references (search/replace, test)

### No External API Changes

- Public API unchanged (`col()`, `lit()`, `.eq()`, etc.)
- Expression compilation unchanged
- DataFrame operations unchanged
- Tests unchanged (except internal visitor tests)

---

## Benefits Summary

### Architectural

- ✅ **Simpler mental model** - One set of operations, not two
- ✅ **Clearer semantics** - Backend implements, visitor delegates
- ✅ **No artificial duplication** - Same protocol for same operations
- ✅ **Better protocol hierarchy** - Visitor extends operations (composition)

### Type Safety

- ✅ **Compiler-enforced alignment** - Type checker ensures consistency
- ✅ **No naming drift** - Same names in both implementations
- ✅ **Protocol compliance** - Both must implement all operations
- ✅ **Impossible to get out of sync** - Type errors if they diverge

### Maintainability

- ✅ **Single source of truth** - Operations protocol defines all operations
- ✅ **Easier to add operations** - Add to base protocol, implement in both
- ✅ **Clearer documentation** - Protocol = complete operation reference
- ✅ **Better IDE support** - Protocol hints for both visitors and backends

### Code Quality

- ✅ **Remove legacy artifact** - No more `_B_` prefix confusion
- ✅ **Consistent naming** - `eq()` everywhere
- ✅ **Clear separation** - Operations vs AST traversal
- ✅ **Protocol-based design** - Modern Python typing patterns

---

## Comparison: Dual vs Unified

| Aspect | Dual Protocols (Original) | Unified Protocols (Refined) |
|--------|---------------------------|----------------------------|
| **Total protocols** | 16 (8 visitor + 8 backend) | 16 (8 base + 8 visitor) |
| **Method names** | Different (`_B_eq` vs `eq`) | Same (`eq` everywhere) |
| **Duplication** | Operations defined twice | Operations defined once |
| **Alignment** | Enforced by pairing | Enforced by inheritance |
| **Mental model** | "Two hierarchies in lockstep" | "Shared base, visitors extend" |
| **Implementation** | Backend and visitor separate | Visitor delegates to backend |
| **Conceptual clarity** | Medium (why two protocols?) | High (one source of truth) |

---

## Recommendations

### Immediate

1. ✅ **Approve unified protocol architecture** (8 base + 8 visitor)
2. ✅ **Approve `_B_` prefix removal** (align method names)
3. ✅ **Create protocol definitions** before implementation

### Refactoring Phase Updates

**Phase 2: Define Protocols** (was 2-3 days, now 4-5 days)
- Define 8 base operations protocols
- Define 8 visitor protocols (extend base)
- Document protocol hierarchy
- Create type stubs

**Phase 3: Refactor Visitors** (NEW, 2-3 days)
- Remove `_B_` prefix from all visitor methods
- Update operation dictionaries
- Update tests
- Verify type checking passes

**Phase 4-7: Backend mixins** (unchanged)
- Backends already use correct names
- Update to explicitly implement protocols
- Extract mixins as planned

### Testing Strategy

- Update visitor tests for method name changes
- Add protocol compliance tests
- Verify type checking with mypy
- Cross-backend tests unchanged (external API same)

---

## Questions Answered

**Q: Why do we need DUAL protocols?**
**A:** We don't! We need ONE set of base operations protocols, which both visitors and backends implement. Visitors extend these with AST traversal methods.

**Q: Is the `_B_` prefix necessary?**
**A:** No, it's a legacy artifact. Remove it - both visitor and backend should use same method names (`eq`, `ne`, etc.).

**Q: Can we use one protocol in many locations?**
**A:** YES! That's the key insight. The base operations protocols are used by BOTH visitors and backends.

---

## Next Steps

1. **Review and approve** this unified protocol architecture
2. **Update refactoring roadmap** to include visitor method renaming
3. **Create protocol definitions** (8 base + 8 visitor)
4. **Begin Phase 2** with updated protocol approach

---

**Status:** Architectural refinement complete - simpler, clearer, more maintainable

**Impact:** Same type safety benefits, better conceptual model, removes legacy artifacts
