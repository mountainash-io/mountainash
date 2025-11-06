# Visitor Architecture Analysis

## Pattern: Composition-Based Visitor with Mixin Dispatch

### Core Design Philosophy

The architecture achieves **separation of dispatch logic from execution logic** through a three-layer mixin composition pattern.

---

## Architecture Layers

### Layer 1: Common Operations (Cross-Logic)
**Location**: `core/expression_visitors/common_mixins/`

These mixins handle operations that work the same regardless of logic type (Boolean/Ternary):

```python
├── SourceExpressionVisitor       # COL, IS_NULL, IS_NOT_NULL
├── LiteralExpressionVisitor      # LIT
├── CastExpressionVisitor         # CAST
└── NativeBackendExpressionVisitor # NATIVE (backend passthrough)
```

**Responsibility**: Backend primitive operations

---

### Layer 2: Logic-Specific Operations
**Location**: `core/expression_visitors/boolean_mixins/` (and future `ternary_mixins/`)

These mixins handle operations specific to Boolean logic:

```python
├── BooleanComparisonExpressionVisitor   # EQ, NE, GT, LT, GE, LE
├── BooleanOperatorsExpressionVisitor    # AND, OR, NOT, XOR_EXCLUSIVE, XOR_PARITY
├── BooleanCollectionExpressionVisitor   # IN, NOT_IN
├── BooleanUnaryExpressionVisitor        # IS_TRUE, IS_FALSE
└── BooleanConstantExpressionVisitor     # ALWAYS_TRUE, ALWAYS_FALSE
```

**Responsibility**: Logic-specific dispatch and abstract operations

---

### Layer 3: Backend Implementations
**Location**: `backends/<backend_name>/`

Concrete implementations for specific DataFrame libraries:

```python
NarwhalsBooleanExpressionVisitor
├── NarwhalsBackendBaseVisitor           # Implements _col, _lit, _cast, _is_null, etc.
├── BooleanCollectionExpressionVisitor   # Provides dispatch, requires _B_in, _B_not_in
├── BooleanComparisonExpressionVisitor   # Provides dispatch, requires _B_eq, _B_ne, ...
├── BooleanConstantExpressionVisitor     # Provides dispatch, requires _B_always_true, ...
├── BooleanOperatorsExpressionVisitor    # Provides dispatch, requires _B_and, _B_or, ...
└── BooleanUnaryExpressionVisitor        # Provides dispatch, requires _B_is_true, ...
```

**Responsibility**: Backend-specific primitive implementations

---

## Mixin Anatomy (Consistent 4-Part Structure)

Every mixin follows this pattern:

```python
class BooleanComparisonExpressionVisitor(ExpressionVisitor):
    
    # ========================================
    # PART 1: Operation Map
    # ========================================
    @property
    def boolean_comparison_ops(self) -> Dict[str, Callable]:
        """Maps operator enums to implementation methods."""
        return {
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.EQ: self._B_eq,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.NE: self._B_ne,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.GT: self._B_gt,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.LT: self._B_lt,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.GE: self._B_ge,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.LE: self._B_le,
        }
    
    # ========================================
    # PART 2: Public Visitor Method (Front Door)
    # ========================================
    def visit_comparison_expression(self, expression_node: ComparisonExpressionNode) -> Any:
        """
        Called by expression nodes.
        Handles parameter resolution and validation.
        """
        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")
        
        # Resolve parameters to expression nodes
        left_parameter = ExpressionParameter(expression_node.left)
        right_parameter = ExpressionParameter(expression_node.right)
        
        left_resolved = left_parameter.resolve_to_expression_node()
        right_resolved = right_parameter.resolve_to_expression_node()
        
        return self._process_comparison_expression(expression_node, left_resolved, right_resolved)
    
    # ========================================
    # PART 3: Private Processing Method (Dispatcher)
    # ========================================
    def _process_comparison_expression(
        self, 
        expression_node: ComparisonExpressionNode, 
        left: ExpressionNode, 
        right: ExpressionNode
    ) -> Any:
        """
        Routes to the appropriate backend implementation.
        Uses the operation map for dispatch.
        """
        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")
        
        op_func = self.boolean_comparison_ops[expression_node.operator]
        return op_func(left, right)
    
    # ========================================
    # PART 4: Abstract Backend Operations (Contract)
    # ========================================
    @abstractmethod
    def _B_eq(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        """Backend must implement equals comparison."""
        pass
    
    @abstractmethod
    def _B_ne(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        """Backend must implement not-equals comparison."""
        pass
    
    # ... remaining abstract methods
```

---

## Naming Conventions

### Method Prefixes

| Prefix | Purpose | Example | Who Calls |
|--------|---------|---------|-----------|
| `visit_*` | Public entry point | `visit_comparison_expression()` | Expression nodes |
| `_process_*` | Private dispatcher | `_process_comparison_expression()` | visit_* methods |
| `_B_*` | Boolean backend op | `_B_eq()`, `_B_and()` | _process_* methods |
| `_T_*` | Ternary backend op | `_T_eq()`, `_T_and()` | _process_* methods |
| `_col`, `_lit`, etc. | Backend primitives | `_col()`, `_lit()`, `_cast()` | All layers |

### Property Suffixes

| Suffix | Purpose | Example |
|--------|---------|---------|
| `*_ops` | Operation map | `boolean_comparison_ops`, `source_ops` |

---

## Constants Refactoring

Operations are now organized by **category** rather than lumped together:

### Old Structure (Monolithic)
```python
CONST_EXPRESSION_LOGIC_OPERATORS
    COL, LIT, CAST                  # Mixed concerns
    EQ, NE, GT, LT, GE, LE         # Mixed concerns
    IN, NOT_IN                      # Mixed concerns
    IS_NULL, IS_NOT_NULL            # Mixed concerns
    AND, OR, NOT, XOR               # Mixed concerns
    ALWAYS_TRUE, ALWAYS_FALSE       # Mixed concerns
```

### New Structure (Granular)
```python
CONST_EXPRESSION_SOURCE_OPERATORS         # COL, IS_NULL, IS_NOT_NULL
CONST_EXPRESSION_LITERAL_OPERATORS        # LIT
CONST_EXPRESSION_CAST_OPERATORS           # CAST
CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS  # EQ, NE, GT, LT, GE, LE
CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS  # IN, NOT_IN
CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS      # IS_TRUE, IS_FALSE, IS_UNKNOWN, ...
CONST_EXPRESSION_LOGICAL_CONSTANT_OPERATORS   # ALWAYS_TRUE, ALWAYS_FALSE, ALWAYS_UNKNOWN
CONST_EXPRESSION_LOGICAL_OPERATORS            # AND, OR, NOT, XOR_EXCLUSIVE, XOR_PARITY
```

**Benefits**:
- Clear categorization
- Each mixin uses its own constant enum
- Easier to extend (add new categories without polluting others)
- Better IDE autocomplete

---

## Composition Example: Narwhals Boolean Visitor

```python
class NarwhalsBooleanExpressionVisitor(
    NarwhalsBackendBaseVisitor,           # Layer 3: Backend primitives
    BooleanCollectionExpressionVisitor,   # Layer 2: IN, NOT_IN dispatch
    BooleanComparisonExpressionVisitor,   # Layer 2: EQ, NE, GT, LT, GE, LE dispatch
    BooleanConstantExpressionVisitor,     # Layer 2: ALWAYS_TRUE, ALWAYS_FALSE dispatch
    BooleanOperatorsExpressionVisitor,    # Layer 2: AND, OR, NOT, XOR dispatch
    BooleanUnaryExpressionVisitor         # Layer 2: IS_TRUE, IS_FALSE dispatch
):
    """
    Concrete visitor for Narwhals backend with Boolean logic.
    
    Inherits:
    - All dispatch logic from mixins (visit_*, _process_*, operation maps)
    - Backend primitives from NarwhalsBackendBaseVisitor (_col, _lit, _cast, etc.)
    
    Must implement:
    - All abstract _B_* methods from boolean mixins
    """
    
    # Boolean Comparison Operations (from BooleanComparisonExpressionVisitor)
    def _B_eq(self, left, right) -> nw.Expr:
        return left == right
    
    def _B_ne(self, left, right) -> nw.Expr:
        return left != right
    
    # ... 4 more comparison ops
    
    # Boolean Logical Operations (from BooleanOperatorsExpressionVisitor)
    def _B_and(self, operands) -> nw.Expr:
        return reduce(lambda x, y: x & y, operands)
    
    def _B_or(self, operands) -> nw.Expr:
        return reduce(lambda x, y: x | y, operands)
    
    # ... 3 more logical ops
    
    # Boolean Collection Operations (from BooleanCollectionExpressionVisitor)
    def _B_in(self, element, container) -> nw.Expr:
        return element.is_in(list(container))
    
    # ... 1 more collection op
    
    # Boolean Unary Operations (from BooleanUnaryExpressionVisitor)
    def _B_is_true(self, expr) -> nw.Expr:
        return expr == nw.lit(True)
    
    # ... 1 more unary op
    
    # Boolean Constant Operations (from BooleanConstantExpressionVisitor)
    def _B_always_true(self) -> nw.Expr:
        return nw.lit(True)
    
    # ... 1 more constant op
```

**Total Implementation Burden**: ~15-20 small methods (one per operation)

**Total Inherited Behavior**: ~100+ lines of dispatch logic (from mixins)

---

## Benefits of This Architecture

### 1. **Single Responsibility Principle**
Each mixin handles exactly ONE category of operations:
- Comparison mixin ONLY handles EQ, NE, GT, LT, GE, LE
- Operators mixin ONLY handles AND, OR, NOT, XOR
- Collection mixin ONLY handles IN, NOT_IN

### 2. **DRY (Don't Repeat Yourself)**
Dispatch logic is written **once** in the mixin, reused by **all backends**:
- Parameter resolution: once per operation category
- Operator validation: once per operation category
- Dispatch routing: once per operation category

### 3. **Open/Closed Principle**
- Open for extension: Add new backends by implementing abstract methods
- Closed for modification: Mixins don't change when adding backends

### 4. **Inversion of Control**
- Expression nodes call `visitor.visit_comparison_expression(self)`
- Mixins route to abstract `_B_eq()`, `_B_ne()`, etc.
- Backend provides concrete implementations
- **Dependency flow**: Nodes → Mixins → Backend (all depend on abstractions)

### 5. **Type Safety**
Abstract methods enforce implementation contracts:
```python
@abstractmethod
def _B_eq(self, left: ExpressionNode, right: ExpressionNode) -> Any:
    pass  # Backend MUST implement this
```

### 6. **Testability**
Each layer can be tested independently:
- Test mixins with mock backends
- Test backends with mock expression nodes
- Test integration with real components

### 7. **Logic Independence**
Boolean and Ternary logic can coexist without interference:
- `BooleanComparisonExpressionVisitor` has `_B_eq()`
- `TernaryComparisonExpressionVisitor` would have `_T_eq()`
- Same backend can support both by inheriting from both mixins

### 8. **Minimal Backend Implementation**
Backend developers only write **primitive operations**:
- No dispatch logic
- No parameter resolution
- No operation maps
- Just: "here's how to do EQ in Narwhals"

---

## Usage Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Expression Node (BooleanComparisonExpressionNode)       │
│    expression_node.eval()(dataframe)                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Visitor Factory                                          │
│    factory.get_visitor_for_backend(dataframe, BOOLEAN)      │
│    → Returns: NarwhalsBooleanExpressionVisitor              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Mixin (BooleanComparisonExpressionVisitor)              │
│    visitor.visit_comparison_expression(expression_node)     │
│    ├─ Resolve parameters                                    │
│    └─ Call _process_comparison_expression()                 │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Mixin Dispatcher (_process_comparison_expression)       │
│    op_func = boolean_comparison_ops[expression_node.operator]│
│    return op_func(left, right)                              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Backend Implementation (NarwhalsBooleanExpressionVisitor)│
│    _B_eq(left, right) → left == right                       │
│    Returns: nw.Expr                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Extension Examples

### Adding a New Backend (e.g., Pandas)

```python
class PandasBooleanExpressionVisitor(
    PandasBackendBaseVisitor,             # New: _col(), _lit() for pandas
    BooleanCollectionExpressionVisitor,   # Reuse: dispatch logic
    BooleanComparisonExpressionVisitor,   # Reuse: dispatch logic
    BooleanConstantExpressionVisitor,     # Reuse: dispatch logic
    BooleanOperatorsExpressionVisitor,    # Reuse: dispatch logic
    BooleanUnaryExpressionVisitor         # Reuse: dispatch logic
):
    # Only implement pandas-specific primitives
    def _B_eq(self, left, right) -> pd.Series:
        return left == right  # pandas comparison
    
    # ... ~15 more methods
```

### Adding a New Operation Category

```python
# 1. Add new constant enum
class CONST_EXPRESSION_STRING_OPERATORS(Enum):
    CONTAINS = auto()
    STARTS_WITH = auto()
    ENDS_WITH = auto()

# 2. Create mixin
class BooleanStringExpressionVisitor(ExpressionVisitor):
    @property
    def boolean_string_ops(self):
        return {
            CONST_EXPRESSION_STRING_OPERATORS.CONTAINS: self._B_contains,
            # ...
        }
    
    def visit_string_expression(self, node):
        # ... dispatch logic
    
    @abstractmethod
    def _B_contains(self, string, pattern): pass

# 3. Add to backend visitor composition
class NarwhalsBooleanExpressionVisitor(
    NarwhalsBackendBaseVisitor,
    BooleanStringExpressionVisitor,  # NEW
    # ... other mixins
):
    def _B_contains(self, string, pattern):
        return string.str.contains(pattern)
```

---

## Comparison: Old vs New Architecture

| Aspect | Old (Monolithic) | New (Mixin-Based) |
|--------|------------------|-------------------|
| **Dispatch Logic** | Duplicated per backend | Written once in mixins |
| **Backend Implementation** | ~200 lines per backend | ~50 lines per backend |
| **Adding Operations** | Modify all backends | Add mixin, backends inherit |
| **Testing** | Integration tests only | Unit test each layer |
| **Coupling** | High (backends know dispatch) | Low (backends know primitives) |
| **Code Duplication** | High | Minimal |
| **Logic Separation** | Mixed | Clear (Boolean/Ternary) |
| **Extension** | Modify existing code | Add new mixins/backends |

---

## Summary

This architecture achieves:

✅ **Separation of Concerns**: Dispatch vs Execution  
✅ **Code Reuse**: Dispatch logic written once  
✅ **Type Safety**: Abstract methods enforce contracts  
✅ **Extensibility**: Add backends or operations easily  
✅ **Testability**: Each layer independently testable  
✅ **Maintainability**: Changes localized to specific mixins  
✅ **Clarity**: Clear responsibility for each component  

**The Pattern**: 
- Mixins provide the "what operations exist" and "how to route"
- Backends provide the "how to execute for this DataFrame library"
- Expression nodes provide the "what to evaluate"

**Result**: A scalable, maintainable visitor architecture that supports multiple backends and multiple logic systems with minimal code duplication.

