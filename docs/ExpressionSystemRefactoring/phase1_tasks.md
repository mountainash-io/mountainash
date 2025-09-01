# Phase 1: Architecture Proof-of-Concept - Detailed Task Breakdown

## Overview: Weeks 1-2 
**Goal**: Prove the orthogonal architecture with Narwhals prototype and validate LogicType-ExpressionNode binding

**Key Architecture Principles to Validate:**
1. **ExpressionNodes bind LogicType**: `BooleanComparisonGtNode` vs `TernaryComparisonGtNode`
2. **UniversalVisitor handles all logic types**: One visitor per backend, not per logic type
3. **ExpressionParameter centralizes type dispatch**: All `Any` parameter handling in one place
4. **Backend orthogonality**: Same visitor works with any backend

## Week 1: Core Architecture Design & Validation

### Day 1-2: ExpressionParameter System Implementation

#### Task 1.1: Implement ExpressionParameter Class
**Deliverable**: Core type dispatch system
**File**: `src/mountainash_expressions/core/expression_system/parameter.py`

```python
# Key validation: Can ExpressionParameter handle all parameter types?
class ExpressionParameter:
    """Centralized parameter type detection and conversion."""
    
    def __init__(self, value: Any, expression_system: ExpressionSystem, visitor: Optional[ExpressionVisitor] = None):
        self.value = value
        self.expression_system = expression_system
        self.visitor = visitor
        self._type = self._detect_type()
    
    def _detect_type(self) -> ParameterType:
        # Priority order: ExpressionNode > NativeExpression > ColumnReference > LiteralValue
        pass
    
    def to_native_expression(self) -> Any:
        # Convert any input to backend-specific expression
        pass
```

**Validation tests:**
- MountainAsh expression nodes → recursive visitor conversion
- Native backend expressions → pass-through
- String column names → backend.col()  
- Python literals → backend.lit()
- Mixed parameter types in single expression

#### Task 1.2: Logic-Bound Expression Nodes Implementation  
**Deliverable**: Expression nodes with explicit logic type binding
**File**: `src/mountainash_expressions/core/logic/nodes.py`

```python
# Key validation: Logic type changes semantic meaning
class BooleanComparisonGtNode(ExpressionNode):
    """Boolean GT: NULLs treated as False."""
    expression_type = "comparison_gt"
    logic_type = "boolean"
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_gt(self)

class TernaryComparisonGtNode(ExpressionNode):
    """Ternary GT: NULL-aware with propagation."""
    expression_type = "comparison_gt"
    logic_type = "ternary"
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_gt(self)
```

**Validation tests:**
- Same operation, different logic types → different visitor methods
- Semantic difference verification: boolean nulls→false, ternary nulls→propagate
- Method dispatch correctness

### Day 3: Expression System Protocol Design

#### Task 1.3: ExpressionSystem Protocol Implementation
**Deliverable**: Backend-agnostic expression system interface
**File**: `src/mountainash_expressions/core/expression_system/base.py`

```python
class ExpressionSystem(ABC):
    """Protocol for backend expression systems."""
    
    # Backend identification
    @abstractmethod
    def get_backend_name(self) -> str: pass
    @abstractmethod
    def is_native_expression(self, obj: Any) -> bool: pass
    
    # Basic expression creation
    @abstractmethod
    def col(self, name: str) -> Any: pass
    @abstractmethod
    def lit(self, value: Any) -> Any: pass
    
    # Boolean operations
    @abstractmethod
    def native_and(self, left: Any, right: Any) -> Any: pass
    @abstractmethod
    def native_or(self, left: Any, right: Any) -> Any: pass
    
    # Ternary operations (NULL-aware)
    def native_ternary_and(self, left: Any, right: Any) -> Any:
        # Default: use when/then/otherwise constructs
        raise NotImplementedError(f"{self.get_backend_name()} ternary logic not implemented")
```

**Validation criteria:**
- Protocol supports both boolean and ternary semantics
- Backend identification works correctly
- Native expression detection is accurate

### Day 4-5: Narwhals Backend Prototype

#### Task 1.4: NarwhalsExpressionSystem Implementation
**Deliverable**: First backend implementation with both logic types
**File**: `src/mountainash_expressions/backends/narwhals_system/expression_system.py`

```python
import narwhals as nw

class NarwhalsExpressionSystem(ExpressionSystem):
    """Narwhals backend supporting boolean and ternary logic."""
    
    def get_backend_name(self) -> str:
        return "narwhals"
    
    def is_native_expression(self, obj: Any) -> bool:
        return isinstance(obj, nw.Expr)
    
    def col(self, name: str) -> nw.Expr:
        return nw.col(name)
    
    def lit(self, value: Any) -> nw.Expr:
        return nw.lit(value)
    
    def native_and(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        return left & right
    
    def native_ternary_and(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """Ternary AND using when/then/otherwise."""
        return (
            nw.when(left.is_null() | right.is_null()).then(None)
            .when(left & right).then(True)
            .otherwise(False)
        )
```

**Validation tests:**
- Boolean operations work with pandas/polars/pyarrow via narwhals
- Ternary operations produce NULL-aware results
- Type detection correctly identifies nw.Expr objects

#### Task 1.5: Universal Visitor Implementation
**Deliverable**: Single visitor handling all logic types for any backend
**File**: `src/mountainash_expressions/core/visitor/universal_visitor.py`

```python
class UniversalExpressionVisitor(ExpressionVisitor):
    """Universal visitor: one per backend, handles all logic types."""
    
    def __init__(self, expression_system: ExpressionSystem):
        self.expression_system = expression_system
    
    # Boolean logic methods
    def visit_boolean_comparison_gt(self, node: BooleanComparisonGtNode) -> Any:
        """Boolean GT: NULLs become False."""
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        return self.expression_system.native_gt(left, right)
    
    # Ternary logic methods
    def visit_ternary_comparison_gt(self, node: TernaryComparisonGtNode) -> Any:
        """Ternary GT: NULL-aware with propagation."""
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        return self.expression_system.native_ternary_gt(left, right)
    
    def _process_operand(self, operand: Any) -> Any:
        """Centralized parameter dispatch via ExpressionParameter."""
        param = ExpressionParameter(operand, self.expression_system, self)
        return param.to_native_expression()
```

**Critical validation:**
- One visitor instance handles both boolean and ternary nodes
- Logic type routing works correctly through method dispatch
- ExpressionParameter integration successful

## Week 2: End-to-End Validation & Testing

### Day 1-2: Complete Pipeline Testing

#### Task 2.1: Expression Tree to Native Expression Compilation
**Deliverable**: End-to-end compilation pipeline validation

```python
# Test: Logic-specific expression compilation
def test_boolean_vs_ternary_compilation():
    # Same operation, different logic types
    boolean_expr = BooleanComparisonGtNode(ColumnNode("age"), 25)
    ternary_expr = TernaryComparisonGtNode(ColumnNode("age"), 25)
    
    narwhals_system = NarwhalsExpressionSystem()
    visitor = UniversalExpressionVisitor(narwhals_system)
    
    # Should produce different semantic results
    boolean_result = boolean_expr.accept(visitor)  # NULLs → False
    ternary_result = ternary_expr.accept(visitor)  # NULLs → NULL propagation
    
    # Validate semantic differences on test data with NULLs
    assert_boolean_semantics(boolean_result)
    assert_ternary_semantics(ternary_result)
```

#### Task 2.2: Mixed Parameter Type Handling
**Deliverable**: ExpressionParameter comprehensive validation

```python
def test_mixed_parameter_types():
    """Test ExpressionParameter handles all input types correctly."""
    expression = BooleanLogicalAndNode([
        BooleanComparisonGtNode(ColumnNode("age"), 25),           # MountainAsh nodes
        BooleanComparisonEqNode("status", "active"),             # String + literal
        native_narwhals_expression,                              # Pre-built nw.Expr
        BooleanComparisonInNode("tier", [1, 2, 3])              # List literal
    ])
    
    # Should compile successfully with mixed input types
    result = expression.accept(universal_visitor)
    assert isinstance(result, nw.Expr)
```

### Day 3: Performance Baseline

#### Task 2.3: Performance Comparison
**Deliverable**: Performance validation against current system

```python
@pytest.mark.benchmark
def test_current_vs_new_architecture_performance():
    """Compare current lambda-based system vs new architecture."""
    
    # Current system (lambda-based)
    current_time = benchmark_current_system()
    
    # New architecture (ExpressionParameter + UniversalVisitor)
    new_time = benchmark_new_architecture()
    
    # Validation: within 20% performance
    assert new_time / current_time < 1.2, f"Performance regression: {new_time/current_time:.2f}x slower"
```

#### Task 2.4: Multi-Backend Validation
**Deliverable**: Proof that same visitor works with multiple backends

```python
def test_backend_orthogonality():
    """Validate same visitor works with any backend."""
    expression = create_test_expression()
    
    # Different backends, same visitor pattern
    backends = [
        NarwhalsExpressionSystem(),
        # Note: Polars and Ibis will be added in Phase 3
    ]
    
    for backend in backends:
        visitor = UniversalExpressionVisitor(backend)
        result = expression.accept(visitor)
        
        # Should produce semantically equivalent results
        validate_semantic_equivalence(result, backend.get_backend_name())
```

### Day 4-5: Architecture Validation

#### Task 2.5: Orthogonality Testing
**Deliverable**: Proof of orthogonal architecture dimensions

```python
def test_parameter_binding_orthogonality():
    """Test orthogonal relationship between architecture dimensions."""
    
    # 1. ExpressionNodes: bind (expression_type, logic_type) - NOT orthogonal
    boolean_gt = BooleanComparisonGtNode(col("x"), 5)
    ternary_gt = TernaryComparisonGtNode(col("x"), 5)
    assert boolean_gt.logic_type != ternary_gt.logic_type  # Different semantics
    
    # 2. Visitor: parameterized by (backend_type) only - orthogonal to logic_type
    visitor = UniversalExpressionVisitor(narwhals_system)
    boolean_result = boolean_gt.accept(visitor)
    ternary_result = ternary_gt.accept(visitor)  # Same visitor, different logic
    
    # 3. ExpressionParameter: handles all parameter types uniformly
    param_tests = [
        ("column_name", str),
        (ColumnNode("test"), ExpressionNode),
        (nw.col("test"), nw.Expr),
        (42, int)
    ]
    
    for value, expected_type in param_tests:
        param = ExpressionParameter(value, narwhals_system, visitor)
        result = param.to_native_expression()
        assert isinstance(result, nw.Expr)  # All convert to native expressions
```

#### Task 2.6: Logic Type Semantic Validation
**Deliverable**: Proof that logic types produce semantically different results

```python
def test_boolean_vs_ternary_semantics():
    """Validate semantic differences between logic types."""
    # Create test data with NULLs
    test_data = create_test_dataframe_with_nulls()
    
    # Same comparison, different logic
    boolean_gt = BooleanComparisonGtNode(col("age"), 25)
    ternary_gt = TernaryComparisonGtNode(col("age"), 25)
    
    visitor = UniversalExpressionVisitor(NarwhalsExpressionSystem())
    
    # Boolean: NULL → False
    boolean_expr = boolean_gt.accept(visitor)
    boolean_results = test_data.filter(boolean_expr)
    assert_no_null_age_rows(boolean_results)  # NULLs excluded
    
    # Ternary: NULL → NULL propagation (user gets "OR IS_NULL for free")
    ternary_expr = ternary_gt.accept(visitor)  
    ternary_results = test_data.filter(ternary_expr)
    assert_includes_null_awareness(ternary_results)  # NULL-aware semantics
```

## Phase 1 Success Criteria

### Week 1 Success Criteria
- [ ] **ExpressionParameter successfully handles all parameter types**
  - MountainAsh nodes → recursive compilation
  - Native expressions → pass-through  
  - Column names → backend.col()
  - Literals → backend.lit()

- [ ] **Logic-bound expression nodes validate semantic binding**
  - BooleanComparisonGtNode vs TernaryComparisonGtNode dispatch to different visitor methods
  - Same expression_type, different logic_type produces different semantics

- [ ] **ExpressionSystem protocol supports both logic types**
  - Boolean operations (native_and, native_or, native_gt)
  - Ternary operations (native_ternary_and, native_ternary_gt) using when/then/otherwise

- [ ] **NarwhalsExpressionSystem validates multi-backend compatibility**
  - Works with pandas, polars, pyarrow via narwhals
  - Type detection correctly identifies native expressions

- [ ] **UniversalVisitor handles all logic types for any backend**
  - One visitor instance per backend (not per logic type)
  - Correct method dispatch based on node logic_type

### Week 2 Success Criteria
- [ ] **End-to-end compilation pipeline works**
  - Expression tree → visitor → native expression → execution
  - Mixed parameter types handled seamlessly
  - Performance within 20% of current system

- [ ] **Orthogonal architecture validated**
  - ExpressionNodes bind (expression_type, logic_type) together
  - Visitors are parameterized by backend_type only
  - ExpressionParameter handles all conversions uniformly

- [ ] **Boolean vs ternary semantic differences proven**
  - Boolean: NULLs become False (exclusion behavior)
  - Ternary: NULLs propagate (users get "OR IS_NULL for free")
  - Same operations produce different results with NULL data

- [ ] **Architecture scales to multiple backends**
  - Same visitor pattern will work for Polars and Ibis (Phase 3 validation)
  - Backend orthogonality demonstrated

## Deliverables Checklist

### Core Implementation
- [ ] `src/mountainash_expressions/core/expression_system/parameter.py` - ExpressionParameter class
- [ ] `src/mountainash_expressions/core/expression_system/base.py` - ExpressionSystem protocol  
- [ ] `src/mountainash_expressions/core/logic/nodes.py` - Logic-bound expression nodes
- [ ] `src/mountainash_expressions/core/visitor/universal_visitor.py` - UniversalExpressionVisitor
- [ ] `src/mountainash_expressions/backends/narwhals_system/expression_system.py` - Narwhals backend

### Validation Tests
- [ ] `tests/test_expression_parameter.py` - Parameter type dispatch validation
- [ ] `tests/test_logic_binding.py` - Logic type semantic differences
- [ ] `tests/test_universal_visitor.py` - Single visitor, multiple logic types
- [ ] `tests/test_narwhals_backend.py` - Backend implementation validation
- [ ] `tests/test_end_to_end_compilation.py` - Complete pipeline testing

### Performance & Architecture
- [ ] `benchmarks/phase1_performance.py` - Performance comparison baseline
- [ ] `tests/test_orthogonal_architecture.py` - Architecture dimension validation
- [ ] `docs/phase1_validation_results.md` - Architecture proof validation

## Phase 2 Readiness Checklist

### Architecture Validation Complete
- [ ] LogicType-ExpressionNode binding proven (not orthogonal)
- [ ] UniversalVisitor handles all logic types (backend orthogonal)  
- [ ] ExpressionParameter centralizes all type dispatch
- [ ] Performance acceptable (< 20% regression)

### Foundation Ready for Extension
- [ ] NarwhalsExpressionSystem serves as template for Polars/Ibis backends
- [ ] UniversalVisitor pattern validated for multi-backend use
- [ ] ExpressionParameter handles all expected input types
- [ ] Test infrastructure supports multi-backend validation

### Key Architecture Insights Validated
- [ ] **Explicit logic semantics**: Users can choose `BooleanGT(x,y)` vs `TernaryGT(x,y)`
- [ ] **Automatic NULL handling**: Ternary logic gives users "OR IS_NULL for free" 
- [ ] **Backend independence**: Same expression tree compiles to any backend
- [ ] **Clean separation**: ExpressionParameter eliminates scattered type checking

This Phase 1 foundation enables Phase 2 to implement all three backends (Narwhals, Polars, Ibis) and both logic types simultaneously, proving the orthogonal architecture scales across the full matrix.