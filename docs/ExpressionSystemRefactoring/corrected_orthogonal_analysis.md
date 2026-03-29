# Corrected Orthogonal Architecture Analysis

## Critical Correction: ExpressionNodes ARE Bound to LogicType

**Previous Error**: Stated that ExpressionNodes are orthogonal to LogicType
**Correct Understanding**: ExpressionNodes must explicitly specify their LogicType as it fundamentally changes their semantic behavior

## Corrected Orthogonal Relationships

### Core Dimensions with Corrected Relationships

1. **LogicType**: `boolean`, `ternary`, `fuzzy`
2. **ExpressionType**: `logical_and`, `logical_or`, `comparison_gt`, `comparison_eq`, etc.
3. **BackendType**: `narwhals`, `polars`, `ibis`
4. **Visitors**: Parameterized by `(logic_type, backend_type)`
5. **Visitor Methods**: Parameterized by `(expression_type, logic_type)` - handle specific operation with specific logic

## Corrected Component Relationships

### ExpressionNodes: (ExpressionType, LogicType) → **NOT Orthogonal**

The fundamental insight: **Logic type changes the semantic meaning of operations**

```python
# Boolean Logic - Nulls implicitly become False
class BooleanGtNode(ExpressionNode):
    logic_type = "boolean"
    expression_type = "comparison_gt"
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_gt(self)
    
    # Semantic meaning: x > y, treating NULL as False

class BooleanAndNode(ExpressionNode):
    logic_type = "boolean" 
    expression_type = "logical_and"
    
    def accept(self, visitor):
        return visitor.visit_boolean_logical_and(self)
    
    # Semantic meaning: x AND y, treating NULL as False

# Ternary Logic - Nulls propagate as UNKNOWN, user gets NULL handling automatically
class TernaryGtNode(ExpressionNode):
    logic_type = "ternary"
    expression_type = "comparison_gt"
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_gt(self)
    
    # Semantic meaning: x > y OR IS_NULL, NULL-aware comparison

class TernaryAndNode(ExpressionNode):
    logic_type = "ternary"
    expression_type = "logical_and"
    
    def accept(self, visitor):
        return visitor.visit_ternary_logical_and(self)
    
    # Semantic meaning: Kleene logic AND with NULL propagation
```

### Visitor Methods: (ExpressionType, LogicType) → **NOT Orthogonal**

Visitor methods must handle the specific combination of operation type AND logic type:

```python
class UniversalExpressionVisitor(ABC):
    """
    Visitor with methods for each (expression_type, logic_type) combination.
    
    Each method handles a specific operation with specific logic semantics.
    """
    
    def __init__(self, expression_system: ExpressionSystem):
        self.expression_system = expression_system
    
    # Boolean Logic Methods
    @abstractmethod
    def visit_boolean_logical_and(self, node: BooleanAndNode) -> Any:
        """Handle boolean AND: NULL treated as False."""
        pass
    
    @abstractmethod  
    def visit_boolean_comparison_gt(self, node: BooleanGtNode) -> Any:
        """Handle boolean GT: NULL treated as False."""
        pass
    
    # Ternary Logic Methods  
    @abstractmethod
    def visit_ternary_logical_and(self, node: TernaryAndNode) -> Any:
        """Handle ternary AND: NULL-aware Kleene logic."""
        pass
    
    @abstractmethod
    def visit_ternary_comparison_gt(self, node: TernaryGtNode) -> Any:
        """Handle ternary GT: NULL-aware comparison with propagation."""
        pass
    
    # Base nodes (these could be logic-agnostic)
    @abstractmethod
    def visit_column(self, node: ColumnNode) -> Any:
        pass
    
    @abstractmethod 
    def visit_literal(self, node: LiteralNode) -> Any:
        pass
```

## Corrected Architecture Components

### 1. Logic-Specific Expression Nodes

```python
# core/logic/boolean_nodes.py
class BooleanExpressionNode(ExpressionNode):
    """Base class for boolean logic expressions."""
    logic_type = "boolean"

class BooleanAndNode(BooleanExpressionNode):
    expression_type = "logical_and"
    
    def __init__(self, operands: List[Any]):
        self.operands = operands
    
    def accept(self, visitor):
        return visitor.visit_boolean_logical_and(self)

class BooleanGtNode(BooleanExpressionNode):
    expression_type = "comparison_gt"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_boolean_comparison_gt(self)

# core/logic/ternary_nodes.py  
class TernaryExpressionNode(ExpressionNode):
    """Base class for ternary logic expressions."""
    logic_type = "ternary"

class TernaryAndNode(TernaryExpressionNode):
    expression_type = "logical_and"
    
    def __init__(self, operands: List[Any]):
        self.operands = operands
    
    def accept(self, visitor):
        return visitor.visit_ternary_logical_and(self)

class TernaryGtNode(TernaryExpressionNode):
    expression_type = "comparison_gt"
    
    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_ternary_comparison_gt(self)
```

### 2. Backend-Agnostic Universal Visitor

Instead of separate BooleanVisitor and TernaryVisitor, we have one visitor that handles all logic types but is parameterized by backend:

```python
# core/visitor/universal_visitor.py
class UniversalExpressionVisitor(ExpressionVisitor):
    """
    Universal visitor that handles all logic types for a specific backend.
    
    The logic type is determined by the expression node type,
    not by the visitor class.
    """
    
    def __init__(self, expression_system: ExpressionSystem):
        self.expression_system = expression_system
    
    # Boolean Logic Implementation
    def visit_boolean_logical_and(self, node: BooleanAndNode) -> Any:
        """Boolean AND: NULL becomes False."""
        operands = self._process_operands(node.operands)
        
        # Chain boolean AND operations
        result = operands[0]
        for operand in operands[1:]:
            result = self.expression_system.native_and(result, operand)
        
        return result
    
    def visit_boolean_comparison_gt(self, node: BooleanGtNode) -> Any:
        """Boolean GT: NULL becomes False."""
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        
        # Standard comparison - NULLs will be handled as False by backend
        return self.expression_system.native_gt(left, right)
    
    # Ternary Logic Implementation
    def visit_ternary_logical_and(self, node: TernaryAndNode) -> Any:
        """Ternary AND: NULL-aware Kleene logic."""
        operands = self._process_operands(node.operands)
        
        # Chain ternary AND operations
        result = operands[0]
        for operand in operands[1:]:
            result = self.expression_system.native_ternary_and(result, operand)
        
        return result
    
    def visit_ternary_comparison_gt(self, node: TernaryGtNode) -> Any:
        """Ternary GT: NULL-aware comparison."""
        left = self._process_operand(node.left)
        right = self._process_operand(node.right)
        
        # Ternary comparison with NULL propagation
        return self.expression_system.native_ternary_gt(left, right)
```

### 3. Expression System Extensions for Ternary Comparisons

```python
# core/expression_system/base.py
class ExpressionSystem(ABC):
    # ... existing methods ...
    
    # Ternary comparison operations
    @abstractmethod
    def native_ternary_gt(self, left: Any, right: Any) -> Any:
        """Ternary greater-than with NULL propagation."""
        pass
    
    @abstractmethod
    def native_ternary_lt(self, left: Any, right: Any) -> Any:
        """Ternary less-than with NULL propagation."""
        pass
    
    @abstractmethod
    def native_ternary_eq(self, left: Any, right: Any) -> Any:
        """Ternary equality with NULL propagation."""
        pass
```

### 4. Backend Implementation Example

```python
# backends/narwhals_system/expression_system.py
class NarwhalsExpressionSystem(ExpressionSystem):
    # ... existing methods ...
    
    def native_ternary_gt(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """
        Ternary GT: Returns TRUE, FALSE, or NULL.
        
        User gets NULL-aware comparison automatically:
        - If either operand is NULL → result is NULL
        - Otherwise → standard comparison
        """
        return (
            nw.when(left.is_null() | right.is_null()).then(None)
            .when(left > right).then(True)
            .otherwise(False)
        )
    
    def native_ternary_eq(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """
        Ternary EQ: NULL-aware equality.
        
        - NULL == NULL → NULL (not TRUE like in SQL)
        - NULL == value → NULL  
        - value == value → TRUE/FALSE
        """
        return (
            nw.when(left.is_null() | right.is_null()).then(None)
            .when(left == right).then(True)
            .otherwise(False)
        )
```

## Corrected Usage Patterns

### Creating Logic-Specific Expressions

```python
# Boolean Logic: NULLs treated as False throughout
boolean_expr = BooleanAndNode([
    BooleanGtNode(ColumnNode("age"), 25),      # age > 25, NULL age → False
    BooleanEqNode(ColumnNode("status"), "active"),  # status == "active", NULL status → False
])

# Ternary Logic: User automatically gets NULL-aware semantics
ternary_expr = TernaryAndNode([
    TernaryGtNode(ColumnNode("age"), 25),      # age > 25 OR age IS NULL → NULL
    TernaryEqNode(ColumnNode("status"), "active"),  # status == "active" OR status IS NULL → NULL  
])
```

### Compilation with Backend Choice

```python
# Same backend, different logic semantics
narwhals_system = NarwhalsExpressionSystem()
universal_visitor = UniversalExpressionVisitor(narwhals_system)

# Boolean compilation
boolean_result = boolean_expr.accept(universal_visitor)
# Calls: visit_boolean_logical_and() → visit_boolean_comparison_gt() → visit_boolean_comparison_eq()

# Ternary compilation  
ternary_result = ternary_expr.accept(universal_visitor)
# Calls: visit_ternary_logical_and() → visit_ternary_comparison_gt() → visit_ternary_comparison_eq()
```

## Corrected Component Matrix

| Component | Required Parameters | Orthogonal To |
|-----------|-------------------|---------------|
| **ExpressionNode** | `expression_type`, `logic_type` | `backend_type` only |
| **Visitor** | `backend_type` | `logic_type`, `expression_type` |  
| **Visitor Method** | `expression_type`, `logic_type` (from node) | `backend_type` |
| **ExpressionSystem** | `backend_type` | `logic_type`, `expression_type` |

## Key Architectural Benefits

### 1. **Explicit Logic Semantics**
Users explicitly choose logic type when creating expressions:
```python
# Clear intent: I want boolean logic (NULLs = False)
BooleanGtNode(col("age"), 25)

# Clear intent: I want ternary logic (NULLs propagate) 
TernaryGtNode(col("age"), 25)
```

### 2. **Automatic NULL Handling**
In ternary logic, users get NULL-aware semantics automatically without explicit IS_NULL checks:
```python
# Boolean: Explicit NULL handling required
BooleanOrNode([
    BooleanGtNode(col("age"), 25),
    BooleanIsNullNode(col("age"))  # Manual NULL handling
])

# Ternary: Automatic NULL handling  
TernaryGtNode(col("age"), 25)  # Automatically handles NULLs appropriately
```

### 3. **Backend Independence with Logic Awareness**
The same expression tree works with any backend while preserving logic semantics:
```python
# Same ternary expression, different backends
ternary_expr = TernaryAndNode([...])

narwhals_result = ternary_expr.accept(UniversalVisitor(NarwhalsExpressionSystem()))
polars_result = ternary_expr.accept(UniversalVisitor(PolarsExpressionSystem()))
ibis_result = ternary_expr.accept(UniversalVisitor(IbisExpressionSystem()))

# All preserve ternary logic semantics in their native format
```

This corrected architecture properly captures the fundamental insight that **logic type is intrinsic to expression semantics**, not just a backend choice.