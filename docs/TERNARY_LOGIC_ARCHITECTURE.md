# Ternary Logic System Architecture

## Summary

Integrate three-valued logic (TRUE/UNKNOWN/FALSE) into mountainash-expressions using the same-namespace approach with `t_` prefixed methods. This allows mixing boolean and ternary operations in the same expression chain.

## Design Decision

**Approach**: Same namespace with `t_` prefix for ternary operations, with **explicit scope boundaries**

### Two Distinct Scopes

| Scope | Values | Operations | Result Type |
|-------|--------|------------|-------------|
| **Boolean land** | `true`, `false` | `eq()`, `and_()`, `or_()` | Boolean |
| **Ternary land** | `-1`, `0`, `1` (FALSE, UNKNOWN, TRUE) | `t_eq()`, `t_and()`, `t_or()` | Integer |

**Key Principle**: `-1, 0, 1` only have ternary meaning **within ternary scope**. Crossing boundaries requires explicit conversion.

### Scope Transitions

```python
import mountainash_expressions as ma

# ═══════════════════════════════════════════════════════════════
# BOOLEAN LAND (standard expressions)
# ═══════════════════════════════════════════════════════════════
expr = ma.col("age").eq(30).and_(ma.col("active"))  # Returns boolean

# ═══════════════════════════════════════════════════════════════
# TERNARY LAND (NULL-aware expressions)
# ═══════════════════════════════════════════════════════════════
expr = ma.col("age").t_eq(30).t_and(ma.col("score").t_gt(50))  # Returns -1/0/1

# ═══════════════════════════════════════════════════════════════
# ENTERING TERNARY (boolean → ternary): use .to_ternary()
# ═══════════════════════════════════════════════════════════════
expr = (
    ma.col("active").eq(True)     # Boolean result
    .to_ternary()                 # ← EXPLICIT: Convert True→1, False→-1
    .t_and(ma.col("score").t_gt(50))  # Now in ternary land
)

# ═══════════════════════════════════════════════════════════════
# EXITING TERNARY (ternary → boolean): use booleanizers
# ═══════════════════════════════════════════════════════════════
expr = (
    ma.col("score").t_gt(50)      # Ternary result (-1/0/1)
    .is_true()                    # ← EXPLICIT: 1→True, else→False
    .and_(ma.col("active"))       # Now back in boolean land
)

# COMPLETE ROUND TRIP EXAMPLE
expr = (
    ma.col("active").eq(True)           # Boolean
    .to_ternary()                       # → Ternary (enter)
    .t_and(ma.col("score").t_ge(80))    # Ternary operation
    .t_or(ma.col("premium").t_eq(True)) # Still ternary
    .maybe_true()                       # → Boolean (exit)
    .and_(ma.col("verified"))           # Boolean operation
)
```

### Boundary Conversion Methods

**Entering ternary** (boolean → ternary):
```python
.to_ternary()       # True → 1, False → -1 (no UNKNOWN from boolean)
```

**Exiting ternary** (ternary → boolean) - the "booleanizers":
```python
.is_true()          # 1 → True, else → False
.is_false()         # -1 → True, else → False
.is_unknown()       # 0 → True, else → False
.is_known()         # 1 or -1 → True, 0 → False
.maybe_true()       # 1 or 0 → True, -1 → False
.maybe_false()      # -1 or 0 → True, 1 → False
```

### Error Handling at Boundaries

```python
# ERROR: Cannot use boolean ops on ternary result without conversion
ma.col("x").t_eq(5).and_(...)  # TypeError: ternary result requires booleanizer

# ERROR: Cannot use ternary ops on boolean result without conversion
ma.col("x").eq(5).t_and(...)   # TypeError: boolean result requires .to_ternary()
```

---

## Ternary Logic Semantics

### Values (from old implementation)
```python
class CONST_TERNARY_LOGIC_VALUES(IntEnum):
    TERNARY_FALSE = -1    # FALSE
    TERNARY_UNKNOWN = 0   # UNKNOWN/NULL
    TERNARY_TRUE = 1      # TRUE
```

### Truth Tables

**AND** (minimum of operands):
| A | B | A t_and B |
|---|---|-----------|
| T | T | T |
| T | U | U |
| T | F | F |
| U | U | U |
| U | F | F |
| F | F | F |

**OR** (maximum of operands):
| A | B | A t_or B |
|---|---|----------|
| T | T | T |
| T | U | T |
| T | F | T |
| U | U | U |
| U | F | U |
| F | F | F |

**NOT** (sign flip):
| A | t_not A |
|---|---------|
| T | F |
| U | U |
| F | T |

### Comparison with NULL
Any comparison involving UNKNOWN/NULL returns UNKNOWN:
- `5 t_eq NULL` → UNKNOWN (0)
- `NULL t_gt 3` → UNKNOWN (0)

---

## Architecture

### Layer 1: Ternary Expression Nodes

**New File**: `core/expression_nodes/ternary_expression_nodes.py`

```python
class TernaryExpressionNode(ExpressionNode):
    """Base class for ternary logic expression nodes."""
    operator: ENUM_TERNARY_OPERATORS = Field()
    logic_type: CONST_LOGIC_TYPES = Field(default=CONST_LOGIC_TYPES.TERNARY)

    def accept(self, visitor: TernaryExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self, dataframe: Any) -> SupportedExpressions:
        # Same pattern as boolean nodes
        ...

class TernaryComparisonExpressionNode(TernaryExpressionNode):
    """Comparison that returns ternary value (-1, 0, 1)."""
    left: Any = Field()
    right: Any = Field()

class TernaryIterableExpressionNode(TernaryExpressionNode):
    """N-ary ternary operations (AND, OR)."""
    operands: Iterable[Any] = Field()

class TernaryUnaryExpressionNode(TernaryExpressionNode):
    """Unary ternary operations (NOT, IS_TRUE, etc.)."""
    operand: Any = Field()

class TernaryConstantExpressionNode(TernaryExpressionNode):
    """Constants: ALWAYS_TRUE, ALWAYS_FALSE, ALWAYS_UNKNOWN."""
    pass
```

### Layer 2: Ternary Protocols

**New File**: `core/protocols/ternary_protocols.py`

```python
class TernaryVisitorProtocol(Protocol):
    """Visitor protocol for ternary logic operations."""

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES: ...

    def visit_expression_node(self, node: SupportedTernaryExpressionNodeTypes) -> SupportedExpressions: ...

    # Comparisons (return ternary integers)
    def t_eq(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions: ...
    def t_ne(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions: ...
    def t_gt(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions: ...
    def t_lt(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions: ...
    def t_ge(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions: ...
    def t_le(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions: ...
    def t_is_in(self, node: TernaryCollectionExpressionNode) -> SupportedExpressions: ...

    # Logical (ternary)
    def t_and(self, node: TernaryIterableExpressionNode) -> SupportedExpressions: ...
    def t_or(self, node: TernaryIterableExpressionNode) -> SupportedExpressions: ...
    def t_not(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions: ...
    def t_xor(self, node: TernaryIterableExpressionNode) -> SupportedExpressions: ...

    # Constants
    def always_true(self, node: TernaryConstantExpressionNode) -> SupportedExpressions: ...
    def always_false(self, node: TernaryConstantExpressionNode) -> SupportedExpressions: ...
    def always_unknown(self, node: TernaryConstantExpressionNode) -> SupportedExpressions: ...

    # Ternary → Boolean conversions
    def is_true(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions: ...
    def is_false(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions: ...
    def is_unknown(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions: ...
    def is_known(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions: ...
    def maybe_true(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions: ...
    def maybe_false(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions: ...


class TernaryExpressionProtocol(Protocol):
    """Backend protocol for ternary operations."""

    # Comparisons
    def t_eq(self, left: SupportedExpressions, right: SupportedExpressions) -> SupportedExpressions: ...
    def t_ne(self, left: SupportedExpressions, right: SupportedExpressions) -> SupportedExpressions: ...
    # ... etc

    # Logical
    def t_and(self, left: SupportedExpressions, right: SupportedExpressions) -> SupportedExpressions: ...
    def t_or(self, left: SupportedExpressions, right: SupportedExpressions) -> SupportedExpressions: ...
    def t_not(self, operand: SupportedExpressions) -> SupportedExpressions: ...

    # Conversions
    def is_true(self, operand: SupportedExpressions) -> SupportedExpressions: ...
    def is_unknown(self, operand: SupportedExpressions) -> SupportedExpressions: ...
    # ... etc


class TernaryBuilderProtocol(Protocol):
    """Builder protocol for ternary namespace methods."""

    def t_eq(self, other: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
    def t_ne(self, other: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
    def t_gt(self, other: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
    def t_lt(self, other: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
    def t_ge(self, other: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
    def t_le(self, other: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
    def t_and(self, *others: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
    def t_or(self, *others: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
    def t_not(self) -> BaseNamespace: ...
    def is_true(self) -> BaseNamespace: ...
    def is_false(self) -> BaseNamespace: ...
    def is_unknown(self) -> BaseNamespace: ...
    def is_known(self) -> BaseNamespace: ...
    def maybe_true(self) -> BaseNamespace: ...
    def maybe_false(self) -> BaseNamespace: ...
```

### Layer 3: Ternary Visitor

**New File**: `core/expression_visitors/ternary_visitor.py`

```python
class TernaryExpressionVisitor(ExpressionVisitor, TernaryVisitorProtocol):
    """
    Ternary logic visitor - handles TRUE(1), FALSE(-1), UNKNOWN(0).

    Implements three-valued logic where comparisons with NULL return UNKNOWN,
    and logical operations use min/max semantics.
    """

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.TERNARY

    @property
    def _ternary_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_TERNARY_OPERATORS.T_EQ: self.t_eq,
            ENUM_TERNARY_OPERATORS.T_NE: self.t_ne,
            ENUM_TERNARY_OPERATORS.T_GT: self.t_gt,
            ENUM_TERNARY_OPERATORS.T_LT: self.t_lt,
            ENUM_TERNARY_OPERATORS.T_GE: self.t_ge,
            ENUM_TERNARY_OPERATORS.T_LE: self.t_le,
            ENUM_TERNARY_OPERATORS.T_AND: self.t_and,
            ENUM_TERNARY_OPERATORS.T_OR: self.t_or,
            ENUM_TERNARY_OPERATORS.T_NOT: self.t_not,
            ENUM_TERNARY_OPERATORS.IS_TRUE: self.is_true,
            ENUM_TERNARY_OPERATORS.IS_FALSE: self.is_false,
            ENUM_TERNARY_OPERATORS.IS_UNKNOWN: self.is_unknown,
            # ... etc
        }

    def visit_expression_node(self, node: SupportedTernaryExpressionNodeTypes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._ternary_ops, node)
        return op_func(node)

    def t_eq(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions:
        left_expr = ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr = ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.t_eq(left_expr, right_expr)

    def t_and(self, node: TernaryIterableExpressionNode) -> SupportedExpressions:
        expr_list = [ExpressionParameter(op, expression_system=self.backend).to_native_expression()
                     for op in node.operands]
        # Ternary AND = minimum value
        return reduce(lambda x, y: self.backend.t_and(x, y), expr_list)

    def t_or(self, node: TernaryIterableExpressionNode) -> SupportedExpressions:
        expr_list = [ExpressionParameter(op, expression_system=self.backend).to_native_expression()
                     for op in node.operands]
        # Ternary OR = maximum value
        return reduce(lambda x, y: self.backend.t_or(x, y), expr_list)

    def is_true(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions:
        """Convert ternary to boolean: TRUE(1) → True, else → False."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.is_true(operand_expr)
```

### Layer 4: Backend Implementations

**New Files**:
- `backends/expression_systems/polars/ternary.py`
- `backends/expression_systems/ibis/ternary.py`
- `backends/expression_systems/narwhals/ternary.py`

```python
# backends/expression_systems/polars/ternary.py

class PolarsTernaryExpressionSystem(PolarsBaseExpressionSystem, TernaryExpressionProtocol):
    """Polars implementation of ternary logic operations."""

    def t_eq(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Ternary equality - returns -1/0/1."""
        return (
            pl.when(left.is_null() | right.is_null())
            .then(pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN))
            .otherwise(
                pl.when(left == right)
                .then(pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE))
                .otherwise(pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
            )
        )

    def t_and(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Ternary AND - minimum of operands."""
        return pl.min_horizontal(left, right)

    def t_or(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Ternary OR - maximum of operands."""
        return pl.max_horizontal(left, right)

    def t_not(self, operand: pl.Expr) -> pl.Expr:
        """Ternary NOT - sign flip (T↔F, U→U)."""
        return (
            pl.when(operand == pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE))
            .then(pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
            .when(operand == pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
            .then(pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE))
            .otherwise(pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN))
        )

    def is_true(self, operand: pl.Expr) -> pl.Expr:
        """Convert ternary to boolean: TRUE(1) → True."""
        return operand == pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)

    def is_unknown(self, operand: pl.Expr) -> pl.Expr:
        """Convert ternary to boolean: UNKNOWN(0) → True."""
        return operand == pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)

    def maybe_true(self, operand: pl.Expr) -> pl.Expr:
        """Convert ternary to boolean: TRUE or UNKNOWN → True."""
        return operand >= pl.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)
```

### Layer 5: Ternary Namespace

**New File**: `core/namespaces/ternary.py`

```python
class TernaryNamespace(BaseNamespace, TernaryBuilderProtocol):
    """
    Ternary logic operations namespace.

    All methods prefixed with t_ to distinguish from boolean operations.
    Returns integer expressions (-1=FALSE, 0=UNKNOWN, 1=TRUE).

    Operations:
    - Comparison: t_eq, t_ne, t_gt, t_lt, t_ge, t_le, t_is_in
    - Logical: t_and, t_or, t_not, t_xor
    - Constants: always_true, always_false, always_unknown
    - Conversions: is_true, is_false, is_unknown, is_known, maybe_true, maybe_false
    """

    def t_eq(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Ternary equal to - returns -1/0/1."""
        other_node = self._to_node_or_value(other)
        node = TernaryComparisonExpressionNode(
            ENUM_TERNARY_OPERATORS.T_EQ,
            self._node,
            other_node,
        )
        return self._build(node)

    def t_gt(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Ternary greater than - returns -1/0/1."""
        other_node = self._to_node_or_value(other)
        node = TernaryComparisonExpressionNode(
            ENUM_TERNARY_OPERATORS.T_GT,
            self._node,
            other_node,
        )
        return self._build(node)

    def t_and(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Ternary AND - minimum of operands."""
        operands = [self._node] + [self._to_node_or_value(o) for o in others]
        node = TernaryIterableExpressionNode(
            ENUM_TERNARY_OPERATORS.T_AND,
            operands=operands,
        )
        return self._build(node)

    def t_or(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Ternary OR - maximum of operands."""
        operands = [self._node] + [self._to_node_or_value(o) for o in others]
        node = TernaryIterableExpressionNode(
            ENUM_TERNARY_OPERATORS.T_OR,
            operands=operands,
        )
        return self._build(node)

    def t_not(self) -> BaseExpressionAPI:
        """Ternary NOT - sign flip."""
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.T_NOT,
            self._node,
        )
        return self._build(node)

    # Ternary → Boolean conversions
    def is_true(self) -> BaseExpressionAPI:
        """Convert ternary to boolean: TRUE(1) → True, else → False."""
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.IS_TRUE,
            self._node,
        )
        return self._build(node)

    def is_unknown(self) -> BaseExpressionAPI:
        """Convert ternary to boolean: UNKNOWN(0) → True, else → False."""
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.IS_UNKNOWN,
            self._node,
        )
        return self._build(node)

    def maybe_true(self) -> BaseExpressionAPI:
        """Convert ternary to boolean: TRUE or UNKNOWN → True."""
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.MAYBE_TRUE,
            self._node,
        )
        return self._build(node)

    # ... similar for is_false, is_known, maybe_false
```

### Layer 6: API Integration

**Modify**: `core/expression_api/boolean.py`

```python
class BooleanExpressionAPI(BaseExpressionAPI):
    """Expression API with boolean and ternary logic operations."""

    _FLAT_NAMESPACES: ClassVar[tuple[type[BaseNamespace], ...]] = (
        BooleanComparisonNamespace,
        BooleanLogicalNamespace,
        TernaryNamespace,           # ← ADD: Ternary operations
        ArithmeticNamespace,
        NullNamespace,
        TypeNamespace,
        HorizontalNamespace,
        NativeNamespace,
    )

    # ... rest unchanged
```

### Layer 7: Operator Enums

**Add to**: `core/constants.py`

```python
class ENUM_TERNARY_OPERATORS(Enum):
    """Ternary logic operators."""
    # Column reference (with sentinel config)
    T_COL = auto()

    # Comparisons
    T_EQ = auto()
    T_NE = auto()
    T_GT = auto()
    T_LT = auto()
    T_GE = auto()
    T_LE = auto()
    T_IS_IN = auto()
    T_IS_NOT_IN = auto()

    # Logical
    T_AND = auto()
    T_OR = auto()
    T_NOT = auto()
    T_XOR = auto()           # Exclusive: exactly one TRUE
    T_XOR_PARITY = auto()    # Parity: odd number of TRUEs

    # Constants
    ALWAYS_TRUE = auto()
    ALWAYS_FALSE = auto()
    ALWAYS_UNKNOWN = auto()

    # Conversions (ternary → boolean)
    IS_TRUE = auto()
    IS_FALSE = auto()
    IS_UNKNOWN = auto()
    IS_KNOWN = auto()
    MAYBE_TRUE = auto()
    MAYBE_FALSE = auto()
```

---

## Implementation Order

### Phase 1: Foundation (~50 lines)
1. Add `ENUM_TERNARY_OPERATORS` to `core/constants.py`
2. Verify `CONST_TERNARY_LOGIC_VALUES` exists (already present)

### Phase 2: Protocols (~200 lines)
3. Create `core/protocols/ternary_protocols.py`
   - `TernaryVisitorProtocol`
   - `TernaryExpressionProtocol`
   - `TernaryBuilderProtocol`
4. Export from `core/protocols/__init__.py`

### Phase 3: Expression Nodes (~200 lines)
5. Create `core/expression_nodes/ternary_expression_nodes.py`
   - `TernaryExpressionNode` (base)
   - `TernaryColumnExpressionNode` (with `unknown_values` field)
   - `TernaryComparisonExpressionNode`
   - `TernaryIterableExpressionNode`
   - `TernaryUnaryExpressionNode`
   - `TernaryConstantExpressionNode`
   - `TernaryCollectionExpressionNode`
6. Export from `core/expression_nodes/__init__.py`

### Phase 4: Visitor (~250 lines)
7. Create `core/expression_visitors/ternary_visitor.py`
   - Include `_check_unknown()` helper for sentinel detection
   - Handle sentinel config propagation
8. Register in `core/expression_visitors/visitor_factory.py`
9. Export from `core/expression_visitors/__init__.py`

### Phase 5: Backend Implementations (~450 lines total)
10. Create `backends/expression_systems/polars/ternary.py` (~150 lines)
    - Include `_check_unknown()` for sentinel value detection
11. Create `backends/expression_systems/ibis/ternary.py` (~150 lines)
12. Create `backends/expression_systems/narwhals/ternary.py` (~150 lines)
13. Update each backend's `__init__.py` to compose ternary protocol

### Phase 6: Namespace & Entry Points (~200 lines)
14. Create `core/namespaces/ternary.py`
    - All `t_*` methods
    - Conversion methods (`is_true`, `is_unknown`, etc.)
15. Add entry points to `core/namespaces/entrypoints.py`
    - `t_col(name, unknown=None)` - ternary-aware column
    - `always_true()`, `always_false()`, `always_unknown()`
    - `set_default_unknown_values()` (optional global config)
16. Add TernaryNamespace to `BooleanExpressionAPI._FLAT_NAMESPACES`
17. Export from `core/namespaces/__init__.py`
18. Export from `api/__init__.py`

### Phase 7: Tests (~500 lines)
19. Create `tests/cross_backend/test_ternary.py`
    - Test ternary comparisons with NULL
    - Test ternary comparisons with custom sentinels
    - Test ternary logical operations (AND, OR, NOT, XOR, XOR_PARITY)
    - Test ternary-to-boolean conversions (is_true, maybe_true, etc.)
    - Test ternary constants
    - Test mixed boolean/ternary chains
    - Test per-column sentinel configuration

---

## Files to Create

| File | Lines | Purpose |
|------|-------|---------|
| `core/protocols/ternary_protocols.py` | ~200 | Protocol definitions |
| `core/expression_nodes/ternary_expression_nodes.py` | ~200 | AST node classes (incl. sentinel config) |
| `core/expression_visitors/ternary_visitor.py` | ~250 | Visitor implementation |
| `core/namespaces/ternary.py` | ~200 | Namespace (API methods) |
| `backends/expression_systems/polars/ternary.py` | ~150 | Polars backend |
| `backends/expression_systems/ibis/ternary.py` | ~150 | Ibis backend |
| `backends/expression_systems/narwhals/ternary.py` | ~150 | Narwhals backend |
| `tests/cross_backend/test_ternary.py` | ~500 | Tests |
| **Total** | **~1,800** | |

## Files to Modify

| File | Changes |
|------|---------|
| `core/constants.py` | Add `ENUM_TERNARY_OPERATORS` (~30 lines) |
| `core/protocols/__init__.py` | Export ternary protocols |
| `core/expression_nodes/__init__.py` | Export ternary nodes |
| `core/expression_visitors/__init__.py` | Export ternary visitor |
| `core/expression_visitors/visitor_factory.py` | Register ternary visitor/nodes |
| `core/namespaces/__init__.py` | Export TernaryNamespace |
| `core/namespaces/entrypoints.py` | Add `t_col()`, `always_*()` entry points |
| `core/expression_api/boolean.py` | Add TernaryNamespace to _FLAT_NAMESPACES |
| `api/__init__.py` | Export new entry points |
| `backends/expression_systems/polars/__init__.py` | Compose ternary protocol |
| `backends/expression_systems/ibis/__init__.py` | Compose ternary protocol |
| `backends/expression_systems/narwhals/__init__.py` | Compose ternary protocol |

---

## Usage Examples

### Basic Ternary Operations
```python
import mountainash_expressions as ma

# Ternary comparison (NULL-aware, uses is_null() by default)
expr = ma.col("nullable_score").t_gt(50)  # Returns -1/0/1

# Ternary logical combination
expr = ma.col("a").t_gt(5).t_and(ma.col("b").t_lt(10))

# Convert to boolean for filtering
expr = ma.col("a").t_gt(5).is_true()        # Only TRUE → True
expr = ma.col("a").t_gt(5).maybe_true()     # TRUE or UNKNOWN → True
expr = ma.col("a").t_gt(5).is_unknown()     # Only UNKNOWN → True

# Filter with ternary (must convert to boolean)
df.filter(ma.col("score").t_ge(80).is_true().compile(df))
```

### Custom Sentinel Values (per-column UNKNOWN detection)
```python
# Legacy data with -99999 meaning "missing"
expr = ma.t_col("legacy_score", unknown={-99999}).t_gt(50)

# Multiple sentinel values
expr = ma.t_col("status", unknown={"NA", "<MISSING>", None}).t_eq("active")

# Different columns with different sentinels
expr = (
    ma.t_col("field_a", unknown={-99999, -1}).t_gt(0)
    .t_and(ma.t_col("field_b", unknown={"N/A", ""}).t_ne("invalid"))
)

# Optional: set global defaults
ma.set_default_unknown_values({None, -99999, "NA"})
```

### Mixed Boolean/Ternary
```python
# Start with boolean, switch to ternary where NULL-awareness needed
expr = (
    ma.col("active").eq(True)                    # Boolean comparison
    .t_and(ma.col("nullable_score").t_ge(50))   # Ternary AND
    .is_true()                                   # Convert back to boolean
)
```

### Ternary Constants (Entry Points)
```python
expr = ma.always_true()      # Returns 1 for all rows
expr = ma.always_unknown()   # Returns 0 for all rows
expr = ma.always_false()     # Returns -1 for all rows

# Usage in conditional
expr = ma.when(condition).then(value).otherwise(ma.always_unknown())
```

### XOR Variants
```python
# Exclusive XOR: exactly one TRUE
expr = ma.col("a").t_gt(0).t_xor(
    ma.col("b").t_gt(0),
    ma.col("c").t_gt(0)
)  # TRUE only if exactly one is TRUE

# Parity XOR: odd number of TRUEs
expr = ma.col("a").t_gt(0).t_xor_parity(
    ma.col("b").t_gt(0),
    ma.col("c").t_gt(0)
)  # TRUE if 1 or 3 are TRUE
```

### Complete Filtering Example
```python
import mountainash_expressions as ma
import polars as pl

df = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "Diana"],
    "score": [85, None, 70, -99999],  # -99999 means "not evaluated"
    "status": ["active", "NA", "active", "inactive"],
})

# Define expression with custom sentinels
expr = (
    ma.t_col("score", unknown={None, -99999}).t_ge(80)
    .t_and(ma.t_col("status", unknown={"NA"}).t_eq("active"))
    .maybe_true()  # Include TRUE and UNKNOWN results
)

# Compile and filter
result = df.filter(expr.compile(df))
# Returns: Alice (TRUE & TRUE), Charlie (FALSE & TRUE = FALSE excluded)
# Diana excluded (UNKNOWN & FALSE = FALSE)
```

---

## Key Design Decisions

### 1. Same Namespace vs Separate API
**Decision**: Same namespace with `t_` prefix

**Rationale**:
- Single import
- Mix logic types mid-chain
- IDE discoverability (autocomplete shows both)
- Explicit intent at each step

### 2. Return Type
**Decision**: Ternary operations return integer expressions (-1/0/1)

**Rationale**:
- Enables vectorized min/max for AND/OR
- Enables arithmetic on truth values
- Clear distinction from boolean

### 3. Conversion Methods
**Decision**: Six conversion methods on TernaryNamespace

| Method | Returns True when |
|--------|------------------|
| `is_true()` | value == 1 |
| `is_false()` | value == -1 |
| `is_unknown()` | value == 0 |
| `is_known()` | value != 0 (i.e., 1 or -1) |
| `maybe_true()` | value >= 0 (i.e., 1 or 0) |
| `maybe_false()` | value <= 0 (i.e., -1 or 0) |

### 4. NULL Handling - Configurable Sentinel Values
**Decision**: Flexible sentinel value configuration with sensible defaults

**Requirement**: Different fields may use different values to represent UNKNOWN:
- Field A might use `NULL`
- Field B might use `-99999`
- Field C might use `{"NA", "<MISSING>", None}`

**Design**: `t_col()` entry point with optional `unknown` parameter

```python
# Default: NULL is UNKNOWN
expr = ma.col("score").t_gt(50)  # Uses is_null() check

# Per-column sentinel configuration
expr = ma.t_col("legacy_score", unknown={-99999, -1}).t_gt(50)
expr = ma.t_col("status", unknown={"NA", "<MISSING>"}).t_eq("active")

# Multiple columns with different sentinels
expr = (
    ma.t_col("field_a", unknown={-99999}).t_gt(0)
    .t_and(ma.t_col("field_b", unknown={"N/A"}).t_eq("yes"))
)

# Global default (optional, for convenience)
ma.set_default_unknown_values({None, -99999, "NA"})  # Affects all subsequent t_col() calls
```

**Implementation**:
```python
# Entry point that captures sentinel config
def t_col(name: str, unknown: Optional[Set[Any]] = None) -> BaseExpressionAPI:
    """Create ternary-aware column reference with optional sentinel values."""
    node = TernaryColumnExpressionNode(
        operator=ENUM_TERNARY_OPERATORS.T_COL,
        column=name,
        unknown_values=unknown or _DEFAULT_UNKNOWN_VALUES,
    )
    return BooleanExpressionAPI(node)

# Node carries the sentinel configuration
class TernaryColumnExpressionNode(TernaryExpressionNode):
    column: str = Field()
    unknown_values: Set[Any] = Field(default_factory=lambda: {None})

# Backend checks both is_null AND sentinel values
def t_eq(self, left: pl.Expr, right: pl.Expr, left_unknown: Set[Any], right_unknown: Set[Any]) -> pl.Expr:
    left_is_unknown = self._check_unknown(left, left_unknown)
    right_is_unknown = self._check_unknown(right, right_unknown)
    return (
        pl.when(left_is_unknown | right_is_unknown)
        .then(pl.lit(0))  # UNKNOWN
        .otherwise(
            pl.when(left == right).then(pl.lit(1)).otherwise(pl.lit(-1))
        )
    )

def _check_unknown(self, expr: pl.Expr, unknown_values: Set[Any]) -> pl.Expr:
    """Check if expression value is in the UNKNOWN set."""
    if unknown_values == {None}:
        return expr.is_null()
    else:
        conditions = [expr.is_null()] if None in unknown_values else []
        for val in unknown_values:
            if val is not None:
                conditions.append(expr == pl.lit(val))
        return reduce(lambda x, y: x | y, conditions)
```

**Trade-off**: This adds complexity to the visitor since it needs to pass sentinel configs through. Alternative is to resolve sentinels at node creation time, but that loses the ability to inspect/serialize the config.

### 5. XOR Semantics
**Decision**: Both variants

| Method | Semantics |
|--------|-----------|
| `t_xor(*operands)` | Exclusive - exactly one TRUE |
| `t_xor_parity(*operands)` | Parity - odd number of TRUEs |

### 6. Ternary Constants as Entry Points
**Decision**: Top-level functions

```python
# Entry points (like col() and lit())
ma.always_true()      # Returns 1 for all rows
ma.always_false()     # Returns -1 for all rows
ma.always_unknown()   # Returns 0 for all rows

# Usage in expressions
expr = ma.when(condition).then(value).otherwise(ma.always_unknown())
```
