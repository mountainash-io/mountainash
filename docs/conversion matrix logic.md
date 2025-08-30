
# Detailed Conversion Matrix Specification
"""
COMPREHENSIVE CONVERSION MATRIX SPECIFICATION
===========================================

This matrix defines semantic conversions between Boolean and Ternary logic operations.
The key insight is that conversions must preserve MEANING, not just syntax.

## Core Conversion Principles

### 1. Semantic Preservation
Operations maintain their intended mathematical meaning across logic types.
Example: Boolean AND preserves its FALSE-dominates semantics in Ternary AND.

### 2. Lossy vs Lossless Conversions
- **Boolean → Ternary**: Lossless (can always add UNKNOWN handling)
- **Ternary → Boolean**: Potentially lossy (UNKNOWN values must be interpreted)

### 3. Mathematical Differences
Some operations have different semantics between logic types:
- **XOR_PARITY**: TRUE if odd number of operands are TRUE (1,3,5...)
- **XOR_EXCLUSIVE**: TRUE if exactly one operand is TRUE
- **STRICT_AND**: UNKNOWN dominates over TRUE (used in BETWEEN operations)

## Detailed Conversion Matrix

### Column Operations (Value Comparisons)
Direct semantic mapping with appropriate UNKNOWN handling:

```
Boolean → Ternary:
├── EQ → EQ (with UNKNOWN value mapping)
├── NE → NE (with UNKNOWN value mapping)
├── GT, LT, GE, LE → Same (with UNKNOWN boundary handling)
├── IN → IN (with UNKNOWN list membership)
├── IS_NULL, IS_NOT_NULL → Same (null semantics identical)
└── BETWEEN → BETWEEN (with UNKNOWN boundary handling)

Ternary → Boolean:
├── EQ → EQ (UNKNOWN values become FALSE in boolean context)
├── NE → NE (UNKNOWN values become FALSE in boolean context)
├── GT, LT, GE, LE → Same (UNKNOWN comparisons become FALSE)
├── IN → IN (UNKNOWN membership becomes FALSE)
├── IS_NULL, IS_NOT_NULL → Same (null semantics preserved)
└── BETWEEN → BETWEEN (UNKNOWN boundaries become FALSE)
```

### Logical Operations (Complex Semantics)

```
Boolean → Ternary:
├── AND → AND
│   └── Semantics: FALSE dominates over TRUE and UNKNOWN
├── OR → OR
│   └── Semantics: TRUE dominates over FALSE and UNKNOWN
├── XOR_PARITY → XOR_PARITY
│   └── Semantics: TRUE if odd number of TRUE operands (with UNKNOWN handling)
└── NOT → NOT
    └── Semantics: FALSE↔TRUE, UNKNOWN→UNKNOWN

Ternary → Boolean:
├── AND → Convert operands + AND (UNKNOWN→FALSE)
├── OR → Convert operands + OR (UNKNOWN→FALSE)
├── XOR_EXCLUSIVE → Convert operands + XOR_EXCLUSIVE wrapped with IS_TRUE
├── XOR_PARITY → Convert operands + XOR_PARITY wrapped with IS_TRUE
├── STRICT_AND → Convert operands + AND (UNKNOWN dominance lost)
└── NOT → Convert operands + NOT wrapped with IS_TRUE
```

### Ternary-Specific State Testing Operations (Direct Visitor Delegation)
These operations return boolean results but are inherently ternary concepts that require delegation:

```
Ternary → Boolean (Direct Delegation):
├── IS_TRUE → Original node preserved → Boolean Visitor delegates to Ternary Visitor
├── IS_FALSE → Original node preserved → Boolean Visitor delegates to Ternary Visitor
├── IS_UNKNOWN → Original node preserved → Boolean Visitor delegates to Ternary Visitor
├── MAYBE_TRUE → Original node preserved → Boolean Visitor delegates to Ternary Visitor
├── MAYBE_FALSE → Original node preserved → Boolean Visitor delegates to Ternary Visitor
└── IS_KNOWN → Original node preserved → Boolean Visitor delegates to Ternary Visitor

Boolean → Ternary (N/A):
└── These operations don't exist in boolean logic
```

**Direct Delegation Pattern:**
```python
class BooleanExpressionVisitor:
    def visit_logical_expression(self, node):
        if node.logic_type == "ternary":
            converted_node = convert_to_boolean(node)

            # If it's a booleanizing operation, converted_node is the original node
            if self._is_booleanizing_operation(converted_node):
                # Create ternary visitor for same backend and delegate
                ternary_visitor = self._create_ternary_visitor_for_backend()
                return converted_node.accept(ternary_visitor)
            else:
                # Regular conversion for non-booleanizing operations
                return self._visit_boolean_logical_expression(converted_node)

        return self._visit_boolean_logical_expression(node)
```

### Constant Operations

```
Boolean → Ternary:
├── ALWAYS_TRUE → ALWAYS_TRUE
└── ALWAYS_FALSE → ALWAYS_FALSE

Ternary → Boolean:
├── ALWAYS_TRUE → ALWAYS_TRUE
├── ALWAYS_FALSE → ALWAYS_FALSE
└── ALWAYS_UNKNOWN → ALWAYS_FALSE (UNKNOWN becomes FALSE in boolean context)
```

## Special Case Handling

### 1. XOR Operations Mathematical Difference
```
For 3 TRUE operands (A=T, B=T, C=T):
├── XOR_PARITY(T,T,T) = T    # 3 is odd number of TRUE values
└── XOR_EXCLUSIVE(T,T,T) = F # Not exactly one TRUE value
```
These are fundamentally different mathematical operations!

### 2. STRICT_AND vs Regular AND
```
For operands (A=T, B=UNKNOWN):
├── AND(T,U) = U           # FALSE dominates, UNKNOWN otherwise
└── STRICT_AND(T,U) = U    # UNKNOWN dominates over TRUE
```
STRICT_AND is used in BETWEEN operations where UNKNOWN boundaries should make the result UNKNOWN.

### 3. Booleanizing Operations Conversion
```
Ternary IS_TRUE(some_ternary_expr) → Boolean context:
├── Convert operands recursively to boolean
├── Apply the IS_TRUE operation in boolean context
└── Result is already boolean (TRUE/FALSE)
```

### 4. Round-Trip Conversion Behavior
```
Boolean → Ternary → Boolean on clean data (no UNKNOWN):
└── Should preserve exact behavior

Boolean → Ternary → Boolean on data with UNKNOWN:
└── May lose information (UNKNOWN becomes FALSE in final boolean context)
```

## Integration with Visitor Pattern

### Automatic Conversion in Visitors
```python
class TernaryExpressionVisitor:
    def visit_column_expression(self, node):
        if node.logic_type == "boolean":
            node = convert_to_ternary(node)  # Automatic conversion
        return self._visit_ternary_column_expression(node)
```

### Simple Visitor Delegation Pattern Implementation
```python
class BooleanExpressionVisitor:
    def visit_logical_expression(self, node):
        if node.logic_type == "ternary":
            # Convert ternary to boolean context
            converted_node = convert_to_boolean(node)

            # Check if this is a booleanizing operation that should be delegated
            if self._is_booleanizing_operation(converted_node):
                # Delegate to ternary visitor for same backend
                ternary_visitor = self._create_ternary_visitor_for_backend()
                return converted_node.accept(ternary_visitor)
            else:
                # Regular conversion for non-booleanizing operations
                return self._visit_boolean_logical_expression(converted_node)

        return self._visit_boolean_logical_expression(node)

    def _is_booleanizing_operation(self, node):
        """Check if node is a booleanizing ternary operation."""
        booleanizing_ops = {
            "IS_TRUE", "IS_FALSE", "IS_UNKNOWN",
            "MAYBE_TRUE", "MAYBE_FALSE", "IS_KNOWN"
        }
        return hasattr(node, 'operator') and node.operator in booleanizing_ops

    def _create_ternary_visitor_for_backend(self):
        """Create ternary visitor for same backend."""
        backend_type = self.backend_type  # e.g., "polars", "pandas", etc.

        if backend_type == "polars":
            from ...visitors.ternary import PolarsTernaryExpressionVisitor
            return PolarsTernaryExpressionVisitor()
        elif backend_type == "pandas":
            from ...visitors.ternary import PandasTernaryExpressionVisitor
            return PandasTernaryExpressionVisitor()
        elif backend_type == "ibis":
            from ...visitors.ternary import IbisTernaryExpressionVisitor
            return IbisTernaryExpressionVisitor()
        elif backend_type == "pyarrow":
            from ...visitors.ternary import PyArrowTernaryExpressionVisitor
            return PyArrowTernaryExpressionVisitor()
        else:
            raise ValueError(f"No ternary visitor available for backend: {backend_type}")
```

### Seamless Cross-Logic Type Operations
```python
# Mixed logic types work seamlessly through automatic conversion and delegation
boolean_condition = BooleanColumnExpressionNode("active", "==", True)
ternary_condition = TernaryColumnExpressionNode("score", ">", 80)

# Ternary operations with boolean operands
combined = TernaryLogicalExpressionNode("AND", [boolean_condition, ternary_condition])
result = combined.eval_is_true()(dataframe)

# Boolean visitor encountering ternary booleanizing operations
ternary_state_check = TernaryLogicalExpressionNode("IS_TRUE", [ternary_condition])
boolean_visitor = BooleanExpressionVisitor()

# This works through simple delegation:
# 1. Boolean visitor recognizes IS_TRUE as booleanizing operation
# 2. Creates ternary visitor for same backend (e.g., Polars)
# 3. Delegates original node to ternary visitor
# 4. Gets back boolean result (since IS_TRUE returns boolean)
result_func = ternary_state_check.accept(boolean_visitor)
```

### Architecture Benefits

**1. Semantic Preservation**: Operations maintain their intended meaning across logic types

**2. Simple Delegation**: Booleanizing operations use original nodes with backend-matched visitor delegation

**3. Backend Consistency**: Same backend type maintained across delegation (Polars → Polars, Pandas → Pandas, etc.)

**4. No Extra Node Types**: No special delegation node classes needed - visitors handle delegation directly

**5. Performance Optimization**: Minimal conversion overhead, delegation only when necessary

**6. Type Safety**: Logic type mismatches are handled automatically without user intervention

## Testing Strategy

### 1. Semantic Correctness
Verify that conversions preserve the intended meaning of operations across logic types.

### 2. Mathematical Properties
Test truth tables for logical operations to ensure mathematical correctness.

### 3. Cross-Logic Integration
Validate that boolean and ternary expressions can be combined seamlessly.

### 4. Performance Impact
Ensure conversion overhead is minimal and doesn't impact expression evaluation performance.

This comprehensive conversion matrix enables true logic type orthogonality where any
expression can work with any visitor while preserving semantic correctness and
mathematical integrity.


def visit_logical_expression(self, node):

    visitor_delegate_required = should_delegate(node, self.logic_type):
    node_conversion_required = should_convert_node(node, self.logic_type):
    if node_conversion_required:
        node = convert_expression(node, self.logic_type)

    if visitor_delegate_required:
        visitor = ExpressionVisitorFactory.create_visitor(self.backend_type, node.logic_type)
        return node.accept(delegate_visitor)

    # Otherwise continue processing


      visitor_delegate_required = should_delegate_to_node_logic_type(node, self.logic_type)
      node_conversion_required = should_convert_node(node, self.logic_type)

      if node_conversion_required:
          node = convert_expression(node, self.logic_type)

      if visitor_delegate_required:
          delegate_visitor = ExpressionVisitorFactory.create_visitor(self.backend_type, node.logic_type)
          return node.accept(delegate_visitor)



  def visit_logical_expression(self, node):
      visitor_delegate_required = should_delegate_to_alternate_logic(node, self.logic_type)
      node_conversion_required = should_convert_node(node, self.logic_type)

      if node_conversion_required:
          node = convert_expression(node, self.logic_type)

      if visitor_delegate_required:
          delegate_visitor = create_delegate_visitor(self.table, "ternary", self)
          return node.accept(delegate_visitor)

      # Otherwise continue processing
      return self._process_logical_node(node)

"""
