# Architecture Mismatch Analysis

## The Documented Architecture (ExpressionSystemRefactoring)

### Key Pattern: Direct Backend Expression Return

```python
# From refined_architecture.md (line 1007-1011)
def visit_boolean_comparison_eq(self, node):
    """Boolean equality: NULLs treated as False."""
    left = self._process_operand(node.left)
    right = self._process_operand(node.right)
    return self.expression_system.native_eq(left, right)  # ← Returns nw.Expr DIRECTLY
```

**Return Type**: `nw.Expr` (backend expression) - NOT `Callable`

### Documented Compilation Flow

```
User Code:
  node = TernaryComparisonEqNode(col("age"), 25)
  
Backend Selection:
  system = NarwhalsExpressionSystem()
  visitor = UniversalVisitor(system)
  
Compilation:
  backend_expr = node.accept(visitor)  # ← Returns nw.Expr directly
  
Execution:
  result = df.filter(backend_expr)  # ← Apply expression to dataframe
```

**THREE SEPARATE PHASES**:
1. Tree construction (no backend)
2. Compilation to backend expression (returns nw.Expr)
3. Execution on dataframe (user calls df.filter())

---

## Current Implementation (What You Built)

### Pattern: Nested Callables

```python
# Current narwhals_boolean_visitor.py
def _B_is_true(self, expression_node: LogicalExpressionNode) -> Callable:
    return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(True)
                                                                  ^^^^^^
                                                    Expects Callable!
```

**Return Type**: `Callable` - NOT backend expression

### Current Call Flow

```
User Code:
  expression = BooleanComparisonExpressionNode(...)
  
Compilation + Execution Combined:
  result = expression.eval()(df)
           └───┬───┘  └┬┘
        returns fn   calls fn with df
               │
               └─> Gets visitor
                   Calls visitor.visit_comparison(self)
                   Returns Callable
                   User calls that Callable with df
```

**PROBLEM**: Compilation and execution are CONFLATED in Callables

---

## Key Differences

| Aspect | Documented Architecture | Current Implementation |
|--------|------------------------|----------------------|
| **Visitor Return Type** | Backend expression (nw.Expr) | Callable (function) |
| **accept() Return** | Backend expression | Callable |
| **Compilation Result** | nw.Expr ready to use | Function waiting for df |
| **User API** | `expr = node.accept(visitor)` | `expr = node.eval()` |
| **Execution** | `df.filter(expr)` | `node.eval()(df)` |
| **Phases** | Separate: compile then execute | Combined: compile+execute |

---

## The Core Problem: Lazy vs Eager Compilation

### Documented (Eager Compilation):

```python
# Phase 1: Build tree
node = TernaryComparisonEqNode(ColumnNode("age"), 25)

# Phase 2: Compile to backend (EAGER - happens now)
system = NarwhalsExpressionSystem()
visitor = UniversalVisitor(system)
narwhals_expr = node.accept(visitor)  # Returns nw.Expr NOW
type(narwhals_expr)  # → nw.Expr

# Phase 3: Execute on dataframe
result = df.filter(narwhals_expr)
```

**Benefits**:
- Expression compiled once, used many times
- Can inspect backend expression before execution
- Clear separation of concerns

### Current (Lazy Compilation via Callables):

```python
# Phase 1: Build tree
node = BooleanComparisonExpressionNode(...)

# Phase 2+3: Compile AND execute combined
result = node.eval()(df)
             └┬┘   └┬┘
        returns    compiles NOW
        function   and executes

# Can't inspect compiled expression
# Can't reuse compiled expression across dataframes
```

**Problems**:
- Compilation happens every time eval() is called
- Can't reuse compiled expression
- Can't inspect what backend expression looks like
- Conflates compilation and execution

---

## Why Your _B_is_true Has Callables

Looking at current implementation:

```python
def _B_is_true(self, expression_node: LogicalExpressionNode) -> Callable:
    return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(True)
                                                                  ^^^^^^
                                        Why does accept() need to be called with table?
```

**Because**: The current pattern has `accept()` return Callable instead of backend expression!

This creates recursive problems:
- `accept(self)` returns Callable
- Must call that Callable with table: `accept(self)(table)`
- So parent also returns Callable
- Callables all the way up!

---

## The Fix: Match Documented Architecture

### Change 1: Visitor Methods Return Backend Expressions

```python
# WRONG (current):
def _B_eq(self, left: Any, right: Any) -> Callable:
    return lambda table: (
        left.accept(self)(table) == right.accept(self)(table)
    )

# CORRECT (documented):
def _B_eq(self, left: Any, right: Any) -> nw.Expr:
    """Returns backend expression directly."""
    # Process operands through ExpressionParameter
    left_expr = self._process_operand(left)   # Returns nw.Expr
    right_expr = self._process_operand(right)  # Returns nw.Expr
    
    # Return backend expression
    return left_expr == right_expr  # Returns nw.Expr
```

### Change 2: accept() Returns Backend Expression

```python
# Expression node:
def accept(self, visitor):
    return visitor.visit_boolean_comparison_eq(self)  # Returns nw.Expr directly
```

### Change 3: User API Changes

```python
# OLD API (current):
result = expression.eval()(df)

# NEW API (documented):
# Compile
visitor = UniversalVisitor(NarwhalsExpressionSystem())
backend_expr = expression.accept(visitor)  # Returns nw.Expr

# Execute
result = df.filter(backend_expr)
```

---

## Where Did the Table Come From?

In documented architecture, **ExpressionParameter handles table-less compilation**:

```python
def _process_operand(self, operand: Any) -> Any:
    """Convert operand to backend expression WITHOUT needing table."""
    from ..expression_system.parameter import ExpressionParameter
    param = ExpressionParameter(operand, self.expression_system, self)
    return param.to_native_expression()
```

Key method:

```python
def to_native_expression(self) -> Any:
    """Convert to backend expression."""
    if self._type == ParameterType.EXPRESSION_NODE:
        return self.value.accept(self.visitor)  # Recursive visit, no table!
        
    elif self._type == ParameterType.COLUMN_REFERENCE:
        return self.expression_system.col(self.value)  # Just creates col reference
        
    elif self._type == ParameterType.LITERAL_VALUE:
        return self.expression_system.lit(self.value)  # Just creates literal
```

**No table needed!** Backend expressions are symbolic:
- `nw.col("age")` - symbolic reference to age column
- `nw.lit(25)` - literal value 25
- `nw.col("age") > nw.lit(25)` - symbolic comparison

These are **unevaluated expressions** that get evaluated when applied to dataframe:
```python
expr = nw.col("age") > nw.lit(25)  # Symbolic
result = df.filter(expr)           # Evaluated on df
```

---

## Summary: Architecture Mismatch

| Component | Documented | Current | Match? |
|-----------|------------|---------|--------|
| Visitor return type | Backend expr | Callable | ❌ NO |
| accept() return type | Backend expr | Callable | ❌ NO |
| Compilation phase | Separate | Combined | ❌ NO |
| Execution phase | Separate | Combined | ❌ NO |
| Reusable expressions | ✅ Yes | ❌ No | ❌ NO |
| Table parameter | Not needed | Required | ❌ NO |
| ExpressionParameter | Central dispatch | Not used | ❌ NO |

**Conclusion**: Current implementation does NOT match documented architecture.

The documented architecture is:
- Cleaner (no nested lambdas)
- More efficient (compile once, execute many times)
- More inspectable (can see backend expression)
- More flexible (can pass expression around)

**Recommendation**: Refactor to match documented architecture by removing Callables and returning backend expressions directly.

