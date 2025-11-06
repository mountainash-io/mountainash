# Parameter Resolution Analysis

## Current Problem

There are **two different patterns** being used inconsistently:

### Pattern 1: `_B_is_true()` (✅ Correct for LogicalExpressionNode)
```python
def _B_is_true(self, expression_node: LogicalExpressionNode) -> Callable:
    return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(True)
```

**Flow:**
1. Receives a `LogicalExpressionNode` with operands
2. Returns a lambda that accepts a table/dataframe
3. Inside lambda: visits operand to get backend expression
4. Compares with literal True

### Pattern 2: `_B_eq()` (❌ BROKEN - doesn't visit nodes)
```python
def _B_eq(self, left: ExpressionNode, right: ExpressionNode) -> nw.Expr:
    return left == right  # WRONG! This tries to compare Python objects
```

**Problem**:
- Receives `ExpressionNode` objects (not backend expressions)
- Tries to compare them directly with `==`
- Python's `__eq__` on ExpressionNode just checks object identity
- Never visits nodes to get `nw.Expr`
- Returns wrong type (`nw.Expr` instead of `Callable`)

---

## The Correct Pattern

### Understanding the Two Signatures

There are actually **two different types** of operations:

#### Type A: Operations that receive ExpressionNodes (Comparison, Collection)
These receive **already-resolved parameters** as ExpressionNodes that need visiting:

```python
def _B_eq(self, left: ExpressionNode, right: ExpressionNode) -> ???
```

#### Type B: Operations that receive LogicalExpressionNode (Operators, Unary)
These receive **the entire expression node** with operands:

```python
def _B_and(self, expression_node: LogicalExpressionNode) -> ???
```

---

## Solution: Both Should Return Callables and Visit Nodes

### For Type A (Comparison Operations):

**Wrong** ❌:
```python
def _B_eq(self, left: ExpressionNode, right: ExpressionNode) -> nw.Expr:
    return left == right  # Doesn't work
```

**Correct** ✅:
```python
def _B_eq(self, left: ExpressionNode, right: ExpressionNode) -> Callable:
    """Compare two expression nodes for equality."""
    def evaluate(table):
        # Visit left node to get backend expression
        left_expr = left.accept(self)(table) if isinstance(left, ExpressionNode) else self._lit(left)
        # Visit right node to get backend expression
        right_expr = right.accept(self)(table) if isinstance(right, ExpressionNode) else self._lit(right)
        # Apply backend operation
        return left_expr == right_expr

    return evaluate
```

Or more concisely:
```python
def _B_eq(self, left: ExpressionNode, right: ExpressionNode) -> Callable:
    return lambda table: left.accept(self)(table) == right.accept(self)(table)
```

### For Type B (Logical Operations):

**Already Correct** ✅:
```python
def _B_is_true(self, expression_node: LogicalExpressionNode) -> Callable:
    if len(expression_node.operands) != 1:
        raise ValueError("IS_TRUE requires exactly one operand")

    return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(True)
```

---

## But Wait! There's a Subtlety...

Looking at the **mixin signatures**, comparison operations receive parameters that could be:
1. `ExpressionNode` objects (need visiting)
2. Raw values like strings, ints (need conversion to literals)

The `ExpressionParameter.resolve_to_expression_node()` currently returns:
```python
def resolve_to_expression_node(self) -> 'ExpressionNode':
    if isinstance(self.value, ExpressionNode):
        return self.value
    else:
        return self.value  # Returns raw value!
```

So the backend receives **mixed types**. We need to handle both:

```python
def _B_eq(self, left: Any, right: Any) -> Callable:
    """Handle both ExpressionNodes and raw values."""
    def evaluate(table):
        # Convert left to backend expression
        if isinstance(left, ExpressionNode):
            left_expr = left.accept(self)(table)
        else:
            left_expr = self._lit(left)  # Raw value → literal

        # Convert right to backend expression
        if isinstance(right, ExpressionNode):
            right_expr = right.accept(self)(table)
        else:
            right_expr = self._lit(right)  # Raw value → literal

        return left_expr == right_expr

    return evaluate
```

Or using a helper:

```python
def _to_backend_expr(self, value: Any, table: Any) -> nw.Expr:
    """Convert value to backend expression."""
    if isinstance(value, ExpressionNode):
        return value.accept(self)(table)
    else:
        return self._lit(value)

def _B_eq(self, left: Any, right: Any) -> Callable:
    return lambda table: self._to_backend_expr(left, table) == self._to_backend_expr(right, table)
```

---

## Call Flow Example

```python
# User code
expression = BooleanComparisonExpressionNode(
    operator=CONST.EQ,
    left=SourceExpressionNode(CONST.COL, "age"),
    right=LiteralExpressionNode(CONST.LIT, 25)
)

result = expression.eval()(df)
```

**What happens:**

```
1. expression.eval() returns a function
   └─> def eval_expr(backend): ...

2. User calls eval_expr(df)
   └─> Gets visitor for df
   └─> Calls visitor.visit_comparison_expression(expression)

3. Mixin resolves parameters:
   left_param = ExpressionParameter(SourceExpressionNode(...))
   right_param = ExpressionParameter(LiteralExpressionNode(...))

   left_resolved = left_param.resolve_to_expression_node()  # Returns SourceExpressionNode
   right_resolved = right_param.resolve_to_expression_node()  # Returns LiteralExpressionNode

4. Mixin calls:
   return self._B_eq(left_resolved, right_resolved)

5. Backend's _B_eq executes:
   ┌────────────────────────────────────────────────────┐
   │ return lambda table:                               │
   │     left.accept(self)(table) ==                    │
   │     right.accept(self)(table)                      │
   └────────────────────────────────────────────────────┘

   This returns a lambda (Callable)

6. BUT WAIT - who calls the lambda with the table?
```

---

## The Missing Piece!

Looking at the eval() signature more carefully:

```python
def eval(self) -> Callable:
    def eval_expr(backend: Any) -> Any:
        visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
        return visitor.visit_boolean_comparison_expression(self)
    return eval_expr
```

The `backend` parameter IS the table/dataframe!

So when visitor methods return a Callable, that callable should be called immediately with the backend:

**Option 1: Backend methods return Callable, mixin calls it**
```python
# In mixin:
def _process_comparison_expression(self, expression_node, left, right) -> Any:
    op_func = self.boolean_comparison_ops[expression_node.operator]
    result_fn = op_func(left, right)  # Returns Callable
    return result_fn  # Return callable to be called by eval()
```

But then eval() needs to call it:
```python
def eval_expr(backend: Any) -> Any:
    visitor = Factory.get_visitor_for_backend(backend, self.logic_type)
    result_fn = visitor.visit_comparison_expression(self)
    return result_fn(backend)  # Call with dataframe!
```

**Option 2: Backend methods return backend expressions directly**
The mixin needs to pass the table through:

```python
# In mixin:
def visit_comparison_expression(self, expression_node, table) -> Any:
    # Resolve and call with table
    return self._process_comparison_expression(expression_node, left, right, table)

def _process_comparison_expression(self, expr_node, left, right, table) -> Any:
    op_func = self.boolean_comparison_ops[expr_node.operator]
    return op_func(left, right, table)  # Pass table through
```

And backend:
```python
def _B_eq(self, left: ExpressionNode, right: ExpressionNode, table: Any) -> nw.Expr:
    left_expr = left.accept(self)(table)
    right_expr = right.accept(self)(table)
    return left_expr == right_expr  # Returns nw.Expr directly
```

---

## Recommended Pattern (Simpler)

**The cleanest pattern**: Backend methods receive table parameter and return backend expressions directly:

```python
class BooleanComparisonExpressionVisitor:
    def visit_comparison_expression(self, expression_node, table) -> Any:
        # Resolve parameters
        left = resolve(expression_node.left)
        right = resolve(expression_node.right)
        return self._process_comparison_expression(expression_node, left, right, table)

    def _process_comparison_expression(self, node, left, right, table) -> Any:
        op_func = self.boolean_comparison_ops[node.operator]
        return op_func(left, right, table)
```

```python
class NarwhalsBooleanExpressionVisitor:
    def _B_eq(self, left: Any, right: Any, table: Any) -> nw.Expr:
        """Compare two expressions for equality."""
        # Convert to backend expressions
        left_expr = left.accept(self)(table) if isinstance(left, ExpressionNode) else self._lit(left)
        right_expr = right.accept(self)(table) if isinstance(right, ExpressionNode) else self._lit(right)

        # Return backend expression
        return left_expr == right_expr
```

**Benefits:**
- No nested lambdas
- Table is explicit
- Returns concrete types (nw.Expr) not Callables
- Easier to debug and test

---

## Action Items

1. **Update mixin signatures** to pass table parameter through
2. **Update backend signatures** to receive table as third parameter
3. **Fix all comparison operations** to visit nodes properly
4. **Standardize return types**: Backend expressions (nw.Expr) not Callables




ADDENDUM:


● Short Answer: Return Expressions Directly (with table parameter)

  Your _B_is_true() pattern with lambdas is overly complicated. Here's why and what to do instead:

  The Problem with Current Approach

  You have two incompatible patterns:

  1. _B_is_true() - Returns Callable (lambda)
  2. _B_eq() - Returns nw.Expr directly (but broken)

  The Correct Pattern: Pass Table Through

  Backend methods should:
  - Receive table/dataframe as a parameter
  - Visit nodes to get backend expressions
  - Return backend expressions directly (not Callables)

  # ✅ CORRECT
  def _B_eq(self, left: Any, right: Any, table: Any) -> nw.Expr:
      """Compare equality - returns backend expression directly."""
      # Visit nodes or convert literals
      from ...core.expression_nodes import ExpressionNode

      left_expr = left.accept(self)(table) if isinstance(left, ExpressionNode) else self._lit(left)
      right_expr = right.accept(self)(table) if isinstance(right, ExpressionNode) else self._lit(right)

      return left_expr == right_expr  # Returns nw.Expr

  Why This is Better

  No nested lambdas:
  # ❌ Complex (your current _B_is_true pattern)
  def _B_is_true(self, expr_node) -> Callable:
      return lambda table: expr_node.operands[0].accept(self)(table) == nw.lit(True)

  # ✅ Simple (recommended)
  def _B_is_true(self, expr_node, table) -> nw.Expr:
      return expr_node.operands[0].accept(self)(table) == nw.lit(True)

  Call Flow:
  User: expression.eval()(df)
    └─> eval() returns function
        └─> User calls with df
            └─> visitor.visit_comparison_expression(self, df)  # Pass df!
                └─> _B_eq(left, right, df)  # Pass df!
                    └─> Returns nw.Expr directly

  What Needs to Change

  1. Update mixins to accept and pass table parameter
  2. Update backends to receive table and return expressions
  3. Fix eval() to pass backend/table to visitor

  Would you like me to implement these changes?

● Return a FUNCTION that returns an expression - your _B_is_true() pattern is CORRECT! ✅

  Let me trace through the complete call flow to show you why:

  The Complete Call Flow

  # User code
  expression = BooleanComparisonExpressionNode(
      operator=CONST.EQ,
      left=SourceExpressionNode(CONST.COL, "age"),
      right=25
  )

  result = expression.eval()(df)  # Note: TWO function calls!
           └─────┬─────┘  └┬┘
             returns      passes
             function     dataframe

  Step-by-Step Execution

  1. expression.eval() returns a function:
  def eval(self) -> Callable:
      def eval_expr(backend: Any) -> Any:
          visitor = Factory.get_visitor_for_backend(backend, self.logic_type)
          return visitor.visit_comparison_expression(self)  # Returns Callable!
      return eval_expr  # Returns function that user will call with df

  2. User calls that function with dataframe: eval_expr(df)

  3. Inside eval_expr:
  - Gets visitor for df
  - Calls visitor.visit_comparison_expression(self)
  - This must return a Callable (function)
  - Returns that Callable

  4. But wait - that would require THREE calls: expression.eval()(df)()?

  No! Because accept() returns a Callable that gets called immediately:

  # In _B_is_true:
  return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(True)
                       └────────────────────┬────────────────────┘  └─┬─┘
                                      returns Callable,           calls it
                                      calls it with table        with table

  The Correct Pattern (Your _B_is_true is RIGHT!)

  def _B_eq(self, left: Any, right: Any) -> Callable:
      """Returns a function that accepts a table and returns nw.Expr."""
      from ...core.expression_nodes import ExpressionNode

      def evaluate(table):
          # Visit nodes to get backend expressions
          left_expr = left.accept(self)(table) if isinstance(left, ExpressionNode) else self._lit(left)
          right_expr = right.accept(self)(table) if isinstance(right, ExpressionNode) else self._lit(right)
          return left_expr == right_expr  # Returns nw.Expr

      return evaluate  # Returns Callable

  Or more concisely (lambda style like your _B_is_true):

  def _B_eq(self, left: Any, right: Any) -> Callable:
      from ...core.expression_nodes import ExpressionNode
      return lambda table: (
          (left.accept(self)(table) if isinstance(left, ExpressionNode) else self._lit(left)) ==
          (right.accept(self)(table) if isinstance(right, ExpressionNode) else self._lit(right))
      )

  Why This Pattern?

  Lazy evaluation with dataframe binding:
  - The Callable captures the expression structure
  - When called with a dataframe, it traverses the tree
  - Each node visit returns a Callable that's immediately called with the dataframe
  - Primitives like _col("age") return actual backend expressions

  The magic:
  # When you call:
  operand.accept(self)(table)
           └──┬──┘  └──┬──┘
      returns Callable  calls it with table

  So Your _B_is_true IS the Correct Pattern!

  def _B_is_true(self, expression_node: LogicalExpressionNode) -> Callable:
      """✅ CORRECT - Returns function that takes table, returns nw.Expr"""
      return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(True)

  Just apply the same pattern to _B_eq and others:

  def _B_eq(self, left: Any, right: Any) -> Callable:
      """✅ CORRECT - Same pattern as _B_is_true"""
      return lambda table: self._resolve(left, table) == self._resolve(right, table)

  def _resolve(self, value: Any, table: Any) -> nw.Expr:
      """Helper to convert node or raw value to backend expression."""
      from ...core.expression_nodes import ExpressionNode
      if isinstance(value, ExpressionNode):
          return value.accept(self)(table)
      else:
          return self._lit(value)

  Answer: Return FUNCTIONS (Callables), not expressions directly! 🎯
