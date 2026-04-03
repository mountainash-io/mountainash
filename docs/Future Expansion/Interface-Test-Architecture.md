# Interface Test Architecture & Protocol Alignment

**Date:** 2025-01-09
**Status:** Critical Architectural Enhancement
**Discovery:** Need interface tests to ensure complete alignment across all layers

---

## Executive Summary

**Problem:** Five architectural layers must stay perfectly aligned, but no automated verification:
1. Enums (define operations)
2. ExpressionNodes (AST structure)
3. Visitor Protocols (AST traversal interface)
4. Operations Protocols (backend interface)
5. Backend Implementations

**Solution:** Comprehensive interface test suite that verifies alignment at compile-time and run-time.

**Key Insight:** Need a **Node-Visitor Protocol** to ensure every ExpressionNode has a corresponding `visit_*()` method.

---

## The Five Layers That Must Align

### Layer 1: Enums (Single Source of Truth)

```python
# Node types
class CONST_EXPRESSION_NODE_TYPES(Enum):
    COMPARISON = "comparison"
    ARITHMETIC = "arithmetic"
    STRING = "string"
    # ... 10 more

# Operations for each type
class CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS(Enum):
    EQ = auto()
    NE = auto()
    GT = auto()
    LT = auto()
    GE = auto()
    LE = auto()
```

### Layer 2: ExpressionNodes (AST Structure)

```python
class ComparisonExpressionNode(ExpressionNode):
    def __init__(self, operator: CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS,
                 left: Any, right: Any):
        self.operator = operator
        self.left = left
        self.right = right
```

### Layer 3: Visitor Protocols (AST Traversal)

```python
class ComparisonVisitor(ComparisonOperations, Protocol):
    def visit_comparison_expression(self, node: ComparisonExpressionNode) -> Any:
        """Process comparison AST node."""
        ...

    # Inherited from ComparisonOperations:
    # def eq(self, left, right) -> Any: ...
    # def ne(self, left, right) -> Any: ...
```

### Layer 4: Operations Protocols (Backend Interface)

```python
class ComparisonOperations(Protocol):
    def eq(self, left: Any, right: Any) -> Any:
        """Equality comparison."""
        ...

    def ne(self, left: Any, right: Any) -> Any:
        """Inequality comparison."""
        ...

    # ... 4 more
```

### Layer 5: Backend Implementations

```python
class PolarsExpressionSystem(ComparisonOperations, ...):
    def eq(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left == right

    def ne(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left != right
```

---

## Required Alignment

### Alignment 1: Enum → ExpressionNode

**Rule:** Every `CONST_EXPRESSION_NODE_TYPES` enum value must have a corresponding ExpressionNode class.

```python
# Enum
CONST_EXPRESSION_NODE_TYPES.COMPARISON = "comparison"

# Must have corresponding class
class ComparisonExpressionNode(ExpressionNode):
    ...
```

**Currently:** 92% aligned (12/13 - ALIAS missing)

### Alignment 2: Enum → Operations

**Rule:** Every operator in `CONST_EXPRESSION_*_OPERATORS` must map to a protocol method.

```python
# Enum
CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.EQ = auto()

# Must have corresponding method
class ComparisonOperations(Protocol):
    def eq(self, left, right) -> Any:  # EQ → eq()
        ...
```

**Naming Convention:** `OPERATOR_NAME` → `operator_name()` (lowercase, underscores)

**Currently:** Only 23% aligned (18/78 operators abstracted)

### Alignment 3: ExpressionNode → visit_* Method

**Rule:** Every ExpressionNode class must have a corresponding `visit_*()` method in visitor protocol.

```python
# Node
class ComparisonExpressionNode(ExpressionNode):
    ...

# Must have visitor method
class ComparisonVisitor(Protocol):
    def visit_comparison_expression(self, node: ComparisonExpressionNode) -> Any:
        ...
```

**Naming Convention:** `*ExpressionNode` → `visit_*_expression()`

**Currently:** ~100% aligned (all implemented nodes have visitor methods)

### Alignment 4: Visitor Protocol → Operations Protocol

**Rule:** Every visitor protocol must extend corresponding operations protocol.

```python
# Visitor extends operations
class ComparisonVisitor(ComparisonOperations, Protocol):
    # Adds visit method
    def visit_comparison_expression(self, node) -> Any: ...

    # Inherits operations from ComparisonOperations
```

**Currently:** Needs implementation (part of refactoring)

### Alignment 5: Operations Protocol → Backend Implementation

**Rule:** Every backend must implement all operations protocols.

```python
class PolarsExpressionSystem(
    ComparisonOperations,
    ArithmeticOperations,
    StringOperations,
    # ... all 8 protocols
):
    # Must implement ALL methods from ALL protocols
```

**Currently:** Partial (only 23% of operations abstracted)

---

## Missing Protocol: Node-Visitor Alignment

### The Problem

Currently no protocol ensures every ExpressionNode type has a `visit_*()` method. The visitor mixins define `visit_*()` methods, but there's no type-safe enforcement.

### Proposed Solution: VisitorDispatch Protocol

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class VisitorDispatch(Protocol):
    """Protocol ensuring every node type has a visitor method."""

    # Core nodes
    def visit_source_expression(self, node: SourceExpressionNode) -> Any: ...
    def visit_literal_expression(self, node: LiteralExpressionNode) -> Any: ...
    def visit_cast_expression(self, node: CastExpressionNode) -> Any: ...
    def visit_native_expression(self, node: NativeExpressionNode) -> Any: ...
    def visit_alias_expression(self, node: AliasExpressionNode) -> Any: ...

    # Boolean logic nodes
    def visit_comparison_expression(self, node: ComparisonExpressionNode) -> Any: ...
    def visit_logical_expression(self, node: LogicalExpressionNode) -> Any: ...
    def visit_collection_expression(self, node: CollectionExpressionNode) -> Any: ...
    def visit_unary_expression(self, node: UnaryExpressionNode) -> Any: ...
    def visit_logical_constant_expression(self, node: LogicalConstantExpressionNode) -> Any: ...

    # Other operation nodes
    def visit_arithmetic_expression(self, node: ArithmeticExpressionNode) -> Any: ...
    def visit_string_expression(self, node: StringExpressionNode) -> Any: ...
    def visit_pattern_expression(self, node: PatternExpressionNode) -> Any: ...
    def visit_conditional_expression(self, node: ConditionalExpressionNode) -> Any: ...
    def visit_temporal_expression(self, node: TemporalExpressionNode) -> Any: ...
```

### Benefits

1. **Type Safety:** Compiler ensures all node types have visitor methods
2. **Complete Coverage:** Can't add new node without adding visitor method
3. **Single Source of Truth:** Protocol documents all visit_* methods
4. **IDE Support:** Autocomplete for all visitor methods

### Integration with Visitor Protocols

```python
# Each visitor protocol extends VisitorDispatch + Operations
class ComparisonVisitor(VisitorDispatch, ComparisonOperations, Protocol):
    # From VisitorDispatch
    def visit_comparison_expression(self, node: ComparisonExpressionNode) -> Any: ...

    # From ComparisonOperations
    def eq(self, left, right) -> Any: ...
    def ne(self, left, right) -> Any: ...
    # ... etc.

# UniversalBooleanVisitor implements all visitor protocols
class UniversalBooleanVisitor(
    ComparisonVisitor,
    ArithmeticVisitor,
    StringVisitor,
    # ... all 8 visitor protocols
):
    # Automatically inherits:
    # - All visit_*() methods from VisitorDispatch
    # - All operation methods from 8 operations protocols

    # Must implement all of them!
```

---

## Naming Conventions (PUBLIC vs _PRIVATE)

### PUBLIC: Protocol Methods

**All protocol methods are public** (no underscore prefix):

```python
# Operations Protocols (public)
class ComparisonOperations(Protocol):
    def eq(self, left, right) -> Any: ...       # PUBLIC
    def ne(self, left, right) -> Any: ...       # PUBLIC

# Visitor Protocols (public)
class ComparisonVisitor(Protocol):
    def visit_comparison_expression(self, node) -> Any: ...  # PUBLIC
```

**Why?** These are the **interface** - they define the contract that implementations must follow.

### _PRIVATE: Helper Methods

**All non-protocol methods are private** (underscore prefix):

```python
class UniversalBooleanVisitor(ComparisonVisitor):
    # PUBLIC (implements protocol)
    def eq(self, left, right) -> Any:
        left_expr = self._process_operand(left)   # Uses private helper
        right_expr = self._process_operand(right) # Uses private helper
        return self.backend.eq(left_expr, right_expr)

    # PRIVATE (helper method, not in protocol)
    def _process_operand(self, operand: Any) -> Any:
        """Helper to convert operand to backend expression."""
        if isinstance(operand, ExpressionNode):
            return operand.accept(self)
        return operand

    # PRIVATE (internal operation dictionary)
    @property
    def _boolean_comparison_ops(self) -> Dict[str, Callable]:
        return {
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.EQ: self.eq,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.NE: self.ne,
            # ...
        }
```

### Refactoring Required

**Current visitor methods with `_B_` prefix must be renamed:**

```python
# BEFORE (incorrect - protocol method with prefix)
def _B_eq(self, left, right) -> Any:
    ...

# AFTER (correct - public protocol method)
def eq(self, left, right) -> Any:
    ...
```

**Current helper methods without prefix must get prefix:**

```python
# BEFORE (incorrect - helper without prefix)
def process_operand(self, operand) -> Any:
    ...

# AFTER (correct - private helper)
def _process_operand(self, operand) -> Any:
    ...
```

---

## Interface Test Suite

### Test 1: Enum → Node Class Mapping

```python
def test_all_node_types_have_classes():
    """Verify every CONST_EXPRESSION_NODE_TYPES has a corresponding class."""
    for node_type in CONST_EXPRESSION_NODE_TYPES:
        class_name = f"{node_type.name.title()}ExpressionNode"
        assert hasattr(expression_nodes, class_name), \
            f"Missing ExpressionNode class for {node_type}"
```

### Test 2: Operator Enum → Protocol Method Mapping

```python
def test_all_operators_have_protocol_methods():
    """Verify every operator enum has corresponding protocol method."""

    # Comparison operators
    for op in CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS:
        method_name = op.name.lower()
        assert hasattr(ComparisonOperations, method_name), \
            f"Missing method ComparisonOperations.{method_name}() for operator {op}"

    # Arithmetic operators
    for op in CONST_EXPRESSION_ARITHMETIC_OPERATORS:
        method_name = _operator_to_method_name(op.name)  # ADD → add, FLOOR_DIVIDE → floor_divide
        assert hasattr(ArithmeticOperations, method_name), \
            f"Missing method ArithmeticOperations.{method_name}() for operator {op}"

    # ... repeat for all 11 operator categories
```

### Test 3: Node Class → visit_* Method

```python
def test_all_nodes_have_visitor_methods():
    """Verify every ExpressionNode class has visit_* method in VisitorDispatch."""

    node_classes = [
        ComparisonExpressionNode,
        ArithmeticExpressionNode,
        StringExpressionNode,
        # ... all node classes
    ]

    for node_class in node_classes:
        # Convert class name to visitor method name
        # ComparisonExpressionNode → visit_comparison_expression
        method_name = f"visit_{_class_to_method(node_class.__name__)}"

        assert hasattr(VisitorDispatch, method_name), \
            f"Missing visitor method VisitorDispatch.{method_name}() for {node_class.__name__}"
```

### Test 4: Visitor Protocol Extends Operations

```python
def test_visitor_protocols_extend_operations():
    """Verify each visitor protocol extends corresponding operations protocol."""

    protocol_pairs = [
        (ComparisonVisitor, ComparisonOperations),
        (ArithmeticVisitor, ArithmeticOperations),
        (StringVisitor, StringOperations),
        # ... all 8 pairs
    ]

    for visitor_protocol, operations_protocol in protocol_pairs:
        assert issubclass(visitor_protocol, operations_protocol), \
            f"{visitor_protocol.__name__} must extend {operations_protocol.__name__}"
```

### Test 5: Backend Implements All Operations

```python
def test_backends_implement_all_operations():
    """Verify each backend implements all required operations protocols."""

    backends = [
        PolarsExpressionSystem,
        NarwhalsExpressionSystem,
        IbisExpressionSystem,
    ]

    required_protocols = [
        ComparisonOperations,
        ArithmeticOperations,
        StringOperations,
        PatternOperations,
        ConditionalOperations,
        TemporalOperations,
        CommonOperations,
        BooleanLogicOperations,
    ]

    for backend in backends:
        for protocol in required_protocols:
            # Check protocol compliance
            assert isinstance(backend(), protocol), \
                f"{backend.__name__} must implement {protocol.__name__}"

            # Check all methods exist
            for method_name in dir(protocol):
                if not method_name.startswith('_'):  # Public methods only
                    assert hasattr(backend, method_name), \
                        f"{backend.__name__} missing method {method_name}() from {protocol.__name__}"
```

### Test 6: Visitor Implements All Protocols

```python
def test_visitor_implements_all_protocols():
    """Verify UniversalBooleanVisitor implements all visitor protocols."""

    required_protocols = [
        ComparisonVisitor,
        ArithmeticVisitor,
        StringVisitor,
        PatternVisitor,
        ConditionalVisitor,
        TemporalVisitor,
        CommonVisitor,
        BooleanLogicVisitor,
    ]

    visitor = UniversalBooleanVisitor(MockBackend())

    for protocol in required_protocols:
        assert isinstance(visitor, protocol), \
            f"UniversalBooleanVisitor must implement {protocol.__name__}"
```

### Test 7: No _B_ Prefix on Protocol Methods

```python
def test_no_underscore_b_prefix_on_protocol_methods():
    """Verify protocol methods don't have _B_ prefix (legacy artifact)."""

    all_protocols = [
        ComparisonOperations,
        ArithmeticOperations,
        # ... all protocols
    ]

    for protocol in all_protocols:
        for method_name in dir(protocol):
            if not method_name.startswith('__'):  # Skip dunder methods
                assert not method_name.startswith('_B_'), \
                    f"Protocol method {protocol.__name__}.{method_name} has legacy _B_ prefix"
```

### Test 8: Naming Convention Compliance

```python
def test_operator_enum_to_method_name_mapping():
    """Verify operator enum names map correctly to method names."""

    test_cases = [
        (CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.EQ, "eq"),
        (CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.NE, "ne"),
        (CONST_EXPRESSION_ARITHMETIC_OPERATORS.ADD, "add"),
        (CONST_EXPRESSION_ARITHMETIC_OPERATORS.FLOOR_DIVIDE, "floor_divide"),
        (CONST_EXPRESSION_STRING_OPERATORS.STARTS_WITH, "starts_with"),
        (CONST_EXPRESSION_TEMPORAL_OPERATORS.ADD_DAYS, "add_days"),
    ]

    for operator, expected_method in test_cases:
        actual_method = _operator_to_method_name(operator.name)
        assert actual_method == expected_method, \
            f"Operator {operator.name} should map to {expected_method}, got {actual_method}"
```

---

## Protocol Hierarchy (Complete)

### Level 1: Operations Protocols (8)

Base protocols defining backend operations:

1. **ComparisonOperations** - eq, ne, gt, lt, ge, le
2. **ArithmeticOperations** - add, subtract, multiply, divide, modulo, power, floor_divide
3. **StringOperations** - upper, lower, trim, substring, concat, length, replace, contains, starts_with, ends_with
4. **PatternOperations** - like, regex_match, regex_contains, regex_replace
5. **ConditionalOperations** - when, coalesce, fill_null
6. **TemporalOperations** - year, month, day, hour, minute, second, add_days, diff_days, etc.
7. **CommonOperations** - col, lit, cast, native, is_null, is_not_null
8. **BooleanLogicOperations** - and_, or_, not_, is_in, is_not_in

### Level 2: VisitorDispatch Protocol (1)

Ensures every ExpressionNode has a `visit_*()` method:

**VisitorDispatch** - visit_comparison_expression, visit_arithmetic_expression, etc. (13 methods)

### Level 3: Visitor Protocols (8)

Extend operations + VisitorDispatch:

1. **ComparisonVisitor** extends ComparisonOperations + VisitorDispatch
2. **ArithmeticVisitor** extends ArithmeticOperations + VisitorDispatch
3. **StringVisitor** extends StringOperations + VisitorDispatch
4. **PatternVisitor** extends PatternOperations + VisitorDispatch
5. **ConditionalVisitor** extends ConditionalOperations + VisitorDispatch
6. **TemporalVisitor** extends TemporalOperations + VisitorDispatch
7. **CommonVisitor** extends CommonOperations + VisitorDispatch
8. **BooleanLogicVisitor** extends BooleanLogicOperations + VisitorDispatch

**Total Protocols:** 17 (8 operations + 1 dispatch + 8 visitor)

---

## Implementation Roadmap

### Phase 1: Define Protocols (1 week)

1. Create 8 operations protocols
2. Create VisitorDispatch protocol
3. Create 8 visitor protocols extending operations + dispatch
4. Define all method signatures (align with enums)

### Phase 2: Implement Interface Tests (3-4 days)

1. Enum → Node class mapping tests
2. Operator → Protocol method mapping tests
3. Node → visit_* method mapping tests
4. Protocol extension tests
5. Backend compliance tests
6. Visitor compliance tests
7. Naming convention tests

### Phase 3: Refactor Visitor Methods (2-3 days)

1. Remove `_B_` prefix from all visitor operation methods
2. Add `_` prefix to all helper methods
3. Update operation dictionaries
4. Run interface tests to verify

### Phase 4: Add Missing Backend Methods (2-3 weeks)

1. Add 60 missing methods to ExpressionSystem protocols
2. Implement in all 3 backends (Polars, Narwhals, Ibis)
3. Update visitor implementations to use new backend methods
4. Run interface tests to verify

### Phase 5: CI/CD Integration (1 day)

1. Add interface tests to CI pipeline
2. Run on every commit
3. Block merges if alignment breaks

---

## Benefits

### Type Safety
- ✅ Compiler enforces protocol compliance
- ✅ Can't add enum operator without protocol method
- ✅ Can't add node without visitor method
- ✅ Can't implement backend without all operations

### Maintainability
- ✅ Single source of truth (enums define operations)
- ✅ Clear contracts (protocols define interfaces)
- ✅ Automated verification (tests ensure alignment)
- ✅ Easy to extend (follow the pattern, tests guide you)

### Documentation
- ✅ Protocols document all operations
- ✅ Tests document expected alignment
- ✅ Clear naming conventions
- ✅ Self-documenting architecture

### Quality
- ✅ Impossible to get out of sync
- ✅ Type errors at compile time, not runtime
- ✅ Complete coverage guaranteed
- ✅ Regression prevention

---

## Next Steps

1. **Review and approve** this interface test architecture
2. **Define protocols** (8 operations + 1 dispatch + 8 visitor = 17 total)
3. **Implement interface tests** (8 test suites)
4. **Run tests against current code** (will fail - 77% missing backend abstraction)
5. **Refactor to pass tests** (3-4 weeks)
6. **Add to CI/CD** (prevent future drift)

---

**Status:** Architecture designed, ready for implementation

**Impact:** Transforms architecture from "mostly aligned" to "guaranteed alignment"

**Effort:** 4-5 weeks total (can be phased)

**Risk:** Low (tests guide the refactoring, no external API changes)
