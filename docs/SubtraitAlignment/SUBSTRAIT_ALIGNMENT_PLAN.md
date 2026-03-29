# Substrait Alignment Refactoring: Complete Scope

## Executive Summary

**Objective:** Refactor the node/visitor/protocol architecture to align with Substrait's expression model, enabling native Substrait serialization/deserialization while preserving the public API.

**Impact:**
- ~5,300 lines in `core/` (nodes, protocols, visitors) - **major refactoring**
- ~4,400 lines in `backends/` - **minimal changes** (methods stay, dispatch changes)
- ~2,800 lines in `namespaces/` - **no changes** (builds nodes, same interface)
- Public API - **unchanged**
- Tests - **should pass with minimal updates**

---

## Background: Why Substrait?

### Current State

The current architecture uses arbitrary categorical groupings for expression nodes:
- `BooleanComparisonExpressionNode`, `StringExpressionNode`, `TemporalExpressionNode`, etc.
- Each category has its own operator enum (`ENUM_BOOLEAN_OPERATORS`, `ENUM_STRING_OPERATORS`, etc.)
- Separate visitors for each category dispatch based on node type + operator enum

**The insight:** The node types are arbitrary organizational buckets. What actually matters is the **operation → function mapping**. The current system uses `NodeType + OperatorEnum` as a function identifier; Substrait uses `FunctionURI`.

### Target State

Align with [Substrait](https://substrait.io/), the cross-language serialization format for relational algebra:
- Replace categorical nodes with Substrait-aligned primitives (`ScalarFunctionNode`, `IfThenNode`, etc.)
- Replace operator enums with a unified function registry
- Enable native Substrait serialization/deserialization
- Maintain all existing functionality

### Benefits

1. **Interoperability**: Native import/export with Substrait consumers (DuckDB, Arrow, Velox, DataFusion)
2. **Simpler architecture**: Fewer node types, single visitor, unified function dispatch
3. **Standards compliance**: Operations identified by industry-standard URIs
4. **Extensibility**: Adding operations requires only a registry entry + backend method

---

## Current Architecture Inventory

### Expression Nodes (15 files, ~1,241 lines)

| File | Node Classes | Purpose |
|------|-------------|---------|
| `base_expression_node.py` | `ExpressionNode` | Abstract base |
| `core_expression_nodes.py` | `ColumnExpressionNode`, `LiteralExpressionNode` | Core primitives |
| `boolean_expression_nodes.py` | 8 classes | Comparison, logical, collection |
| `arithmetic_expression_nodes.py` | 2 classes | Binary/iterable arithmetic |
| `string_expression_nodes.py` | 9+ classes | String operations |
| `temporal_expression_nodes.py` | 6 classes | Date/time operations |
| `null_expression_nodes.py` | 4 classes | Null handling |
| `horizontal_expression_nodes.py` | 1 class | Coalesce/greatest/least |
| `name_expression_nodes.py` | 4 classes | Alias/prefix/suffix |
| `type_expression_nodes.py` | 1 class | Cast |
| `native_expression_nodes.py` | 1 class | Passthrough |
| `conditional_expression_nodes.py` | 1 class | When/then/otherwise |
| `ternary_expression_nodes.py` | 7 classes | Ternary logic |

**Total: ~40+ node classes**

### Operator Enums (11 enums, ~150 members)

| Enum | Members |
|------|---------|
| `ENUM_CORE_OPERATORS` | COL, LIT |
| `ENUM_BOOLEAN_OPERATORS` | EQ, NE, GT, LT, GE, LE, IS_CLOSE, BETWEEN, IS_IN, IS_NOT_IN, AND, OR, XOR, XOR_PARITY, NOT, IS_TRUE, IS_FALSE, ALWAYS_TRUE, ALWAYS_FALSE |
| `ENUM_ARITHMETIC_OPERATORS` | ADD, SUBTRACT, MULTIPLY, DIVIDE, MODULO, POWER, FLOOR_DIVIDE |
| `ENUM_STRING_OPERATORS` | STR_UPPER, STR_LOWER, STR_TRIM, STR_LTRIM, STR_RTRIM, STR_SUBSTRING, STR_LENGTH, STR_REPLACE, STR_CONTAINS, STR_STARTS_WITH, STR_ENDS_WITH, STR_CONCAT, PAT_LIKE, PAT_REGEX_MATCH, PAT_REGEX_CONTAINS, PAT_REGEX_REPLACE |
| `ENUM_TEMPORAL_OPERATORS` | 26 operators (extract, diff, add, truncate, etc.) |
| `ENUM_NULL_OPERATORS` | IS_NULL, IS_NOT_NULL, FILL_NULL |
| `ENUM_HORIZONTAL_OPERATORS` | COALESCE, GREATEST, LEAST |
| `ENUM_NAME_OPERATORS` | ALIAS, PREFIX, SUFFIX |
| `ENUM_TYPE_OPERATORS` | CAST |
| `ENUM_NATIVE_OPERATORS` | NATIVE |
| `ENUM_TERNARY_OPERATORS` | T_EQ, T_NE, T_GT, T_LT, T_GE, T_LE, T_IS_IN, T_IS_NOT_IN, T_AND, T_OR, T_NOT, T_XOR, T_XOR_PARITY, IS_TRUE, IS_FALSE, IS_UNKNOWN, IS_KNOWN, MAYBE_TRUE, MAYBE_FALSE, TO_TERNARY, ALWAYS_TRUE, ALWAYS_FALSE, ALWAYS_UNKNOWN |

### Visitors (16 files, ~1,862 lines)

| Visitor | Handles |
|---------|---------|
| `CoreExpressionVisitor` | col, lit |
| `BooleanExpressionVisitor` | Comparisons, logical ops |
| `ArithmeticExpressionVisitor` | Math operations |
| `StringExpressionVisitor` | String operations |
| `TemporalExpressionVisitor` | Date/time operations |
| `NullExpressionVisitor` | Null handling |
| `HorizontalExpressionVisitor` | Coalesce, greatest, least |
| `NameExpressionVisitor` | Alias, prefix, suffix |
| `TypeExpressionVisitor` | Cast |
| `NativeExpressionVisitor` | Passthrough |
| `ConditionalExpressionVisitor` | When/then/otherwise |
| `TernaryExpressionVisitor` | Ternary logic |

### Backend ExpressionSystems (3 backends, ~4,400 lines)

Each backend has ~12 mixin classes implementing protocol methods. **These stay largely unchanged.**

---

## Target Architecture

### Substrait-Aligned Node Types (6 core types)

```python
# core/substrait_nodes/base.py

class SubstraitNode(BaseModel, ABC):
    """Base for all Substrait-aligned expression nodes."""

    def to_substrait(self) -> substrait.Expression: ...

    @classmethod
    def from_substrait(cls, expr: substrait.Expression) -> SubstraitNode: ...


class LiteralNode(SubstraitNode):
    """Constant value."""
    value: Any
    dtype: Optional[str] = None  # Substrait type hint


class FieldReferenceNode(SubstraitNode):
    """Column reference."""
    field: str  # Column name


class ScalarFunctionNode(SubstraitNode):
    """Universal function call - ALL operations use this."""
    function: str  # Function identifier (maps to registry)
    arguments: list[SubstraitNode]
    options: dict[str, Any] = {}  # Function-specific options


class IfThenNode(SubstraitNode):
    """Conditional expression."""
    conditions: list[tuple[SubstraitNode, SubstraitNode]]  # [(cond, result), ...]
    else_clause: SubstraitNode


class CastNode(SubstraitNode):
    """Type conversion."""
    input: SubstraitNode
    target_type: str
    failure_behavior: Literal["throw", "null"] = "throw"


class SingularOrListNode(SubstraitNode):
    """Membership test (IN operator)."""
    value: SubstraitNode
    options: list[SubstraitNode]
```

### Unified Function Registry

```python
# core/functions/registry.py

from dataclasses import dataclass
from enum import Enum

class SubstraitExtension(str, Enum):
    """Standard Substrait extension URIs."""
    COMPARISON = "https://github.com/substrait-io/substrait/extensions/functions_comparison.yaml"
    BOOLEAN = "https://github.com/substrait-io/substrait/extensions/functions_boolean.yaml"
    ARITHMETIC = "https://github.com/substrait-io/substrait/extensions/functions_arithmetic.yaml"
    STRING = "https://github.com/substrait-io/substrait/extensions/functions_string.yaml"
    DATETIME = "https://github.com/substrait-io/substrait/extensions/functions_datetime.yaml"
    # Mountainash extensions
    MOUNTAINASH = "https://mountainash.io/extensions/functions.yaml"


@dataclass(frozen=True)
class FunctionDef:
    """Function definition with Substrait mapping."""
    name: str                    # Internal name (used in code)
    substrait_uri: str           # Substrait extension URI
    substrait_name: str          # Substrait function name
    backend_method: str          # Method name on ExpressionSystem
    category: str                # For organization: "comparison", "boolean", etc.
    is_extension: bool = False   # True for mountainash-specific functions


class FunctionRegistry:
    """Central registry mapping function names to definitions."""

    _functions: dict[str, FunctionDef] = {}

    @classmethod
    def register(cls, func: FunctionDef) -> None:
        cls._functions[func.name] = func

    @classmethod
    def get(cls, name: str) -> FunctionDef:
        return cls._functions[name]

    @classmethod
    def get_substrait_uri(cls, name: str) -> str:
        return cls._functions[name].substrait_uri

    @classmethod
    def get_backend_method(cls, name: str) -> str:
        return cls._functions[name].backend_method
```

### Function Definitions

```python
# core/functions/definitions.py

FUNCTIONS = [
    # Comparison (Substrait standard)
    FunctionDef("eq", SubstraitExtension.COMPARISON, "equal", "eq", "comparison"),
    FunctionDef("ne", SubstraitExtension.COMPARISON, "not_equal", "ne", "comparison"),
    FunctionDef("gt", SubstraitExtension.COMPARISON, "gt", "gt", "comparison"),
    FunctionDef("lt", SubstraitExtension.COMPARISON, "lt", "lt", "comparison"),
    FunctionDef("ge", SubstraitExtension.COMPARISON, "gte", "ge", "comparison"),
    FunctionDef("le", SubstraitExtension.COMPARISON, "lte", "le", "comparison"),
    FunctionDef("is_null", SubstraitExtension.COMPARISON, "is_null", "is_null", "comparison"),
    FunctionDef("is_not_null", SubstraitExtension.COMPARISON, "is_not_null", "is_not_null", "comparison"),
    FunctionDef("coalesce", SubstraitExtension.COMPARISON, "coalesce", "coalesce", "comparison"),
    FunctionDef("greatest", SubstraitExtension.COMPARISON, "greatest", "greatest", "comparison"),
    FunctionDef("least", SubstraitExtension.COMPARISON, "least", "least", "comparison"),
    FunctionDef("between", SubstraitExtension.COMPARISON, "between", "between", "comparison"),

    # Boolean (Substrait standard)
    FunctionDef("and", SubstraitExtension.BOOLEAN, "and", "and_", "boolean"),
    FunctionDef("or", SubstraitExtension.BOOLEAN, "or", "or_", "boolean"),
    FunctionDef("not", SubstraitExtension.BOOLEAN, "not", "not_", "boolean"),
    FunctionDef("xor", SubstraitExtension.BOOLEAN, "xor", "xor_", "boolean"),

    # Arithmetic (Substrait standard)
    FunctionDef("add", SubstraitExtension.ARITHMETIC, "add", "add", "arithmetic"),
    FunctionDef("subtract", SubstraitExtension.ARITHMETIC, "subtract", "subtract", "arithmetic"),
    FunctionDef("multiply", SubstraitExtension.ARITHMETIC, "multiply", "multiply", "arithmetic"),
    FunctionDef("divide", SubstraitExtension.ARITHMETIC, "divide", "divide", "arithmetic"),
    FunctionDef("modulo", SubstraitExtension.ARITHMETIC, "modulus", "modulo", "arithmetic"),
    FunctionDef("power", SubstraitExtension.ARITHMETIC, "power", "power", "arithmetic"),
    FunctionDef("abs", SubstraitExtension.ARITHMETIC, "abs", "abs", "arithmetic"),
    FunctionDef("negate", SubstraitExtension.ARITHMETIC, "negate", "negate", "arithmetic"),

    # String (Substrait standard)
    FunctionDef("upper", SubstraitExtension.STRING, "upper", "str_upper", "string"),
    FunctionDef("lower", SubstraitExtension.STRING, "lower", "str_lower", "string"),
    FunctionDef("concat", SubstraitExtension.STRING, "concat", "str_concat", "string"),
    FunctionDef("substring", SubstraitExtension.STRING, "substring", "str_substring", "string"),
    FunctionDef("trim", SubstraitExtension.STRING, "trim", "str_trim", "string"),
    FunctionDef("ltrim", SubstraitExtension.STRING, "ltrim", "str_ltrim", "string"),
    FunctionDef("rtrim", SubstraitExtension.STRING, "rtrim", "str_rtrim", "string"),
    FunctionDef("char_length", SubstraitExtension.STRING, "char_length", "str_length", "string"),
    FunctionDef("replace", SubstraitExtension.STRING, "replace", "str_replace", "string"),
    FunctionDef("contains", SubstraitExtension.STRING, "contains", "str_contains", "string"),
    FunctionDef("starts_with", SubstraitExtension.STRING, "starts_with", "str_starts_with", "string"),
    FunctionDef("ends_with", SubstraitExtension.STRING, "ends_with", "str_ends_with", "string"),
    FunctionDef("like", SubstraitExtension.STRING, "like", "pat_like", "string"),
    FunctionDef("regexp_match", SubstraitExtension.STRING, "regexp_match_substring", "pat_regex_match", "string"),
    FunctionDef("regexp_replace", SubstraitExtension.STRING, "regexp_replace", "pat_regex_replace", "string"),

    # Temporal (Substrait standard)
    FunctionDef("extract_year", SubstraitExtension.DATETIME, "extract", "dt_year", "temporal"),
    FunctionDef("extract_month", SubstraitExtension.DATETIME, "extract", "dt_month", "temporal"),
    FunctionDef("extract_day", SubstraitExtension.DATETIME, "extract", "dt_day", "temporal"),
    FunctionDef("extract_hour", SubstraitExtension.DATETIME, "extract", "dt_hour", "temporal"),
    FunctionDef("extract_minute", SubstraitExtension.DATETIME, "extract", "dt_minute", "temporal"),
    FunctionDef("extract_second", SubstraitExtension.DATETIME, "extract", "dt_second", "temporal"),
    FunctionDef("extract_weekday", SubstraitExtension.DATETIME, "extract", "dt_weekday", "temporal"),
    FunctionDef("extract_week", SubstraitExtension.DATETIME, "extract", "dt_week", "temporal"),
    FunctionDef("extract_quarter", SubstraitExtension.DATETIME, "extract", "dt_quarter", "temporal"),
    FunctionDef("add_interval", SubstraitExtension.DATETIME, "add", "dt_add", "temporal"),

    # Name operations (mapped to Substrait via custom extension)
    FunctionDef("alias", SubstraitExtension.MOUNTAINASH, "alias", "alias", "name", is_extension=True),
    FunctionDef("prefix", SubstraitExtension.MOUNTAINASH, "prefix", "prefix", "name", is_extension=True),
    FunctionDef("suffix", SubstraitExtension.MOUNTAINASH, "suffix", "suffix", "name", is_extension=True),

    # Mountainash extensions (non-standard)
    FunctionDef("is_close", SubstraitExtension.MOUNTAINASH, "is_close", "is_close", "comparison", is_extension=True),
    FunctionDef("xor_parity", SubstraitExtension.MOUNTAINASH, "xor_parity", "xor_parity", "boolean", is_extension=True),
    FunctionDef("floor_divide", SubstraitExtension.MOUNTAINASH, "floor_divide", "floor_divide", "arithmetic", is_extension=True),

    # Ternary logic (Mountainash extension - convenience that lowers to standard ops)
    # These are handled at the namespace layer and lower to IfThenNode + standard comparisons
]

for func in FUNCTIONS:
    FunctionRegistry.register(func)
```

### Unified Visitor

```python
# core/unified_visitor/visitor.py

class UnifiedExpressionVisitor:
    """Single visitor that handles all Substrait-aligned nodes."""

    def __init__(self, expression_system: ExpressionSystem):
        self.backend = expression_system

    def visit(self, node: SubstraitNode) -> SupportedExpressions:
        """Dispatch to appropriate handler based on node type."""
        if isinstance(node, LiteralNode):
            return self.visit_literal(node)
        elif isinstance(node, FieldReferenceNode):
            return self.visit_field_reference(node)
        elif isinstance(node, ScalarFunctionNode):
            return self.visit_scalar_function(node)
        elif isinstance(node, IfThenNode):
            return self.visit_if_then(node)
        elif isinstance(node, CastNode):
            return self.visit_cast(node)
        elif isinstance(node, SingularOrListNode):
            return self.visit_singular_or_list(node)
        else:
            raise ValueError(f"Unknown node type: {type(node)}")

    def visit_literal(self, node: LiteralNode) -> SupportedExpressions:
        return self.backend.lit(node.value)

    def visit_field_reference(self, node: FieldReferenceNode) -> SupportedExpressions:
        return self.backend.col(node.field)

    def visit_scalar_function(self, node: ScalarFunctionNode) -> SupportedExpressions:
        """Universal function dispatch via registry."""
        # Resolve arguments recursively
        args = [self.visit(arg) for arg in node.arguments]

        # Look up backend method from registry
        func_def = FunctionRegistry.get(node.function)
        method = getattr(self.backend, func_def.backend_method)

        # Call with appropriate signature
        return method(*args, **node.options)

    def visit_if_then(self, node: IfThenNode) -> SupportedExpressions:
        """Handle conditional expressions."""
        # Build when/then/otherwise chain
        builder = None
        for condition, result in node.conditions:
            cond_expr = self.visit(condition)
            result_expr = self.visit(result)
            if builder is None:
                builder = self.backend.when(cond_expr).then(result_expr)
            else:
                builder = builder.when(cond_expr).then(result_expr)

        else_expr = self.visit(node.else_clause)
        return builder.otherwise(else_expr)

    def visit_cast(self, node: CastNode) -> SupportedExpressions:
        input_expr = self.visit(node.input)
        return self.backend.cast(input_expr, node.target_type)

    def visit_singular_or_list(self, node: SingularOrListNode) -> SupportedExpressions:
        value_expr = self.visit(node.value)
        options = [self.visit(opt) if isinstance(opt, SubstraitNode) else opt
                   for opt in node.options]
        return self.backend.is_in(value_expr, options)
```

### Ternary Logic: Lowering Example

Ternary logic operations are convenience syntax that lower to standard Substrait primitives:

```python
# In namespace layer: t_gt() lowers to IfThenNode

def t_gt(self, other) -> BaseExpressionAPI:
    """Ternary greater-than: returns -1/0/1."""
    left = self._node
    right = self._to_substrait_node(other)

    # when(left.is_null() | right.is_null()).then(0)
    # .otherwise(when(left > right).then(1).otherwise(-1))

    null_check = ScalarFunctionNode(
        function="or",
        arguments=[
            ScalarFunctionNode("is_null", [left]),
            ScalarFunctionNode("is_null", [right]),
        ]
    )

    comparison = ScalarFunctionNode("gt", [left, right])

    node = IfThenNode(
        conditions=[
            (null_check, LiteralNode(value=0)),
            (comparison, LiteralNode(value=1)),
        ],
        else_clause=LiteralNode(value=-1)
    )

    return self._build(node)
```

This means ternary logic is **syntactic sugar** that compiles to standard operations - no custom Substrait extensions needed for the core functionality.

---

## Migration Plan

### Overview: Direct Replacement

This is a **direct replacement** strategy - old nodes are replaced entirely, not adapted. No temporary adapter layer, no dual-path compilation. Clean swap.

```
BEFORE                              AFTER
───────────────────────────────────────────────────────────────
BooleanComparisonExpressionNode  →  ScalarFunctionNode("eq", [...])
BooleanIterableExpressionNode    →  ScalarFunctionNode("and", [...])
ArithmeticExpressionNode         →  ScalarFunctionNode("add", [...])
StringExpressionNode             →  ScalarFunctionNode("upper", [...])
TemporalExtractExpressionNode    →  ScalarFunctionNode("extract_year", [...])
TernaryComparisonExpressionNode  →  IfThenNode([...])  # lowered
ColumnExpressionNode             →  FieldReferenceNode(field="col")
LiteralExpressionNode            →  LiteralNode(value=42)

40+ node classes                 →  6 node classes
11 operator enums                →  1 function registry
12 visitors                      →  1 unified visitor
```

---

### Phase 1: Create New Node & Visitor Infrastructure

**Create new modules (old modules remain untouched):**

```
core/
├── expression_nodes/           # EXISTING - untouched for now
├── substrait_nodes/            # NEW
│   ├── __init__.py
│   ├── base.py                 # SubstraitNode base class
│   ├── literal.py              # LiteralNode
│   ├── field_reference.py      # FieldReferenceNode
│   ├── scalar_function.py      # ScalarFunctionNode
│   ├── if_then.py              # IfThenNode
│   ├── cast.py                 # CastNode
│   └── singular_or_list.py     # SingularOrListNode
│
├── functions/                  # NEW
│   ├── __init__.py
│   ├── registry.py             # FunctionRegistry
│   └── definitions.py          # All FunctionDef registrations
│
├── expression_visitors/        # EXISTING - untouched for now
└── unified_visitor/            # NEW
    ├── __init__.py
    └── visitor.py              # UnifiedExpressionVisitor
```

**Deliverables:**
- 6 new Substrait-aligned node classes (Pydantic models)
- Function registry with all ~80 operations mapped
- Unified visitor that compiles Substrait nodes to backend expressions
- Unit tests for new infrastructure

**Estimated: ~800 new lines**

---

### Phase 2: Update Namespaces to Build New Nodes

Update all namespace methods to build Substrait nodes directly:

```python
# OLD: Creates categorical node + operator enum
def eq(self, other):
    other_node = self._to_node_or_value(other)
    return BooleanComparisonExpressionNode(
        operator=ENUM_BOOLEAN_OPERATORS.EQ,
        left=self._node,
        right=other_node
    )

# NEW: Creates universal function node
def eq(self, other):
    other_node = self._to_node(other)
    node = ScalarFunctionNode(
        function="eq",
        arguments=[self._node, other_node]
    )
    return self._build(node)
```

**Files to update:**
- `core/namespaces/boolean.py` - comparison & logical ops
- `core/namespaces/arithmetic.py` - math ops
- `core/namespaces/string.py` - string ops
- `core/namespaces/datetime.py` - temporal ops
- `core/namespaces/null.py` - null handling
- `core/namespaces/horizontal.py` - coalesce, greatest, least
- `core/namespaces/type.py` - cast
- `core/namespaces/name.py` - alias, prefix, suffix
- `core/namespaces/native.py` - passthrough
- `core/namespaces/conditional.py` - when/then/otherwise
- `core/namespaces/ternary.py` - ternary logic (lowers to IfThenNode)
- `core/namespaces/entrypoints.py` - col(), lit(), coalesce(), etc.

**Ternary lowering example:**
```python
def t_gt(self, other) -> BaseExpressionAPI:
    """Ternary greater-than: returns -1/0/1."""
    left = self._node
    right = self._to_node(other)

    # when(left.is_null() | right.is_null()).then(0)
    # .otherwise(when(left > right).then(1).otherwise(-1))
    null_check = ScalarFunctionNode(
        function="or",
        arguments=[
            ScalarFunctionNode("is_null", [left]),
            ScalarFunctionNode("is_null", [right]),
        ]
    )
    comparison = ScalarFunctionNode("gt", [left, right])

    node = IfThenNode(
        conditions=[
            (null_check, LiteralNode(value=0)),
            (comparison, LiteralNode(value=1)),
        ],
        else_clause=LiteralNode(value=-1)
    )
    return self._build(node)
```

**Deliverables:**
- All namespace methods build Substrait nodes
- `BaseExpressionAPI._node` is now a `SubstraitNode`
- Tests may fail at this point (compile() still uses old visitors)

**Estimated: ~2,800 lines modified**

---

### Phase 3: Update Compilation to Use Unified Visitor

Update `BooleanExpressionAPI.compile()` to use the new unified visitor:

```python
class BooleanExpressionAPI:
    _node: SubstraitNode  # Now always a Substrait node

    def compile(
        self,
        df,
        *,
        booleanizer: str | Callable | None = "is_true",
    ) -> SupportedExpressions:
        """Compile expression to backend-native form."""
        from ..unified_visitor import UnifiedExpressionVisitor

        # Identify backend and get expression system
        backend = ExpressionVisitorFactory._identify_backend(df)
        system = ExpressionVisitorFactory._expression_systems_registry[backend]()

        # Compile with unified visitor
        visitor = UnifiedExpressionVisitor(system)
        result = visitor.visit(self._node)

        # Apply booleanizer if needed (for ternary expressions)
        if booleanizer is not None:
            result = self._apply_booleanizer(result, booleanizer, system)

        return result
```

**Deliverables:**
- `compile()` uses unified visitor exclusively
- All tests should pass at this point
- Old visitors are now unused

**Estimated: ~100 lines modified**

**Gate:** Full test suite must pass before proceeding.

---

### Phase 4: Delete Legacy Code

Remove all legacy nodes, visitors, and enums:

**Delete:**
```
core/expression_nodes/              # All 15 files (~1,241 lines)
├── arithmetic_expression_nodes.py
├── boolean_expression_nodes.py
├── conditional_expression_nodes.py
├── core_expression_nodes.py
├── horizontal_expression_nodes.py
├── name_expression_nodes.py
├── native_expression_nodes.py
├── null_expression_nodes.py
├── string_expression_nodes.py
├── temporal_expression_nodes.py
├── type_expression_nodes.py
├── ternary_expression_nodes.py
├── base_expression_node.py
├── types.py
└── __init__.py

core/expression_visitors/           # 12 visitor files (~1,400 lines)
├── arithmetic_visitor.py
├── boolean_visitor.py
├── conditional_visitor.py
├── core_visitor.py
├── horizontal_visitor.py
├── name_visitor.py
├── native_visitor.py
├── null_visitor.py
├── string_visitor.py
├── temporal_visitor.py
├── type_visitor.py
├── ternary_visitor.py
└── expression_visitor.py

core/protocols/                     # All enum definitions (~800 lines)
├── arithmetic_protocols.py         # ENUM_ARITHMETIC_OPERATORS
├── boolean_protocols.py            # ENUM_BOOLEAN_OPERATORS
├── core_protocols.py               # ENUM_CORE_OPERATORS
├── horizontal_protocols.py         # ENUM_HORIZONTAL_OPERATORS
├── name_protocols.py               # ENUM_NAME_OPERATORS
├── native_protocols.py             # ENUM_NATIVE_OPERATORS
├── null_protocols.py               # ENUM_NULL_OPERATORS
├── string_protocols.py             # ENUM_STRING_OPERATORS
├── temporal_protocols.py           # ENUM_TEMPORAL_OPERATORS
├── type_protocols.py               # ENUM_TYPE_OPERATORS
├── ternary_protocols.py            # ENUM_TERNARY_OPERATORS
├── conditional_protocols.py
└── __init__.py
```

**Rename/Move:**
```
core/substrait_nodes/  →  core/expression_nodes/   # Take over the name
core/unified_visitor/  →  core/expression_visitor/ # Singular
```

**Update imports throughout codebase.**

**Deliverables:**
- ~3,400 lines deleted
- Clean directory structure
- All tests still pass

---

### Phase 5: Add Substrait Serialization

Add serialization methods:

```python
class BooleanExpressionAPI:
    def to_substrait(self, schema: Optional[Schema] = None) -> bytes:
        """Serialize to Substrait protobuf."""
        # Build ExtendedExpression with schema info
        ext_expr = ExtendedExpression(
            referred_expr=[ExpressionReference(expression=self._node.to_substrait())],
            base_schema=schema.to_substrait() if schema else None,
        )
        return ext_expr.SerializeToString()

    @classmethod
    def from_substrait(cls, data: bytes) -> "BooleanExpressionAPI":
        """Deserialize from Substrait protobuf."""
        ext_expr = ExtendedExpression()
        ext_expr.ParseFromString(data)

        # Convert first referred expression
        proto_expr = ext_expr.referred_expr[0].expression
        node = SubstraitNode.from_substrait(proto_expr)
        return cls(node)

    def to_json(self) -> str:
        """Serialize to JSON (Substrait text format)."""
        return self._node.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "BooleanExpressionAPI":
        """Deserialize from JSON."""
        node = SubstraitNode.model_validate_json(data)
        return cls(node)
```

**Deliverables:**
- `to_substrait()` / `from_substrait()` for protobuf serialization
- `to_json()` / `from_json()` for human-readable format
- Round-trip tests for both formats

**Estimated: ~300 lines**

---

## Effort Estimate

| Phase | Description | New Lines | Modified Lines | Deleted Lines | Risk |
|-------|-------------|-----------|----------------|---------------|------|
| 1 | New node & visitor infrastructure | ~800 | 0 | 0 | Low |
| 2 | Update namespaces | 0 | ~2,800 | 0 | Medium |
| 3 | Update compilation | 0 | ~100 | 0 | Low |
| 4 | Delete legacy code | 0 | ~200 (imports) | ~3,400 | Low |
| 5 | Substrait serialization | ~300 | ~50 | 0 | Low |

**Total: ~1,100 new lines, ~3,400 lines deleted, ~3,150 lines modified**

**Net result: ~2,300 fewer lines, dramatically simpler architecture**

---

## Files Changed Summary

### New Files (12 files, ~800 lines)

```
core/substrait_nodes/           # Later renamed to core/expression_nodes/
├── __init__.py
├── base.py                     # SubstraitNode base class
├── literal.py                  # LiteralNode
├── field_reference.py          # FieldReferenceNode
├── scalar_function.py          # ScalarFunctionNode
├── if_then.py                  # IfThenNode
├── cast.py                     # CastNode
└── singular_or_list.py         # SingularOrListNode

core/functions/
├── __init__.py
├── registry.py                 # FunctionRegistry class
└── definitions.py              # All FunctionDef registrations

core/unified_visitor/           # Later renamed to core/expression_visitor/
├── __init__.py
└── visitor.py                  # UnifiedExpressionVisitor
```

### Modified Files (~15 files, ~3,000 lines modified)

- `core/namespaces/*.py` (12 files) - build Substrait nodes instead of categorical nodes
- `core/expression_api/base.py` - compile() uses unified visitor
- `core/expression_api/boolean.py` - add serialization methods
- `__init__.py` files - update imports

### Deleted Files (~40 files, ~3,400 lines removed)

```
core/expression_nodes/          # 15 files - replaced by substrait_nodes
├── arithmetic_expression_nodes.py
├── boolean_expression_nodes.py
├── conditional_expression_nodes.py
├── core_expression_nodes.py
├── horizontal_expression_nodes.py
├── name_expression_nodes.py
├── native_expression_nodes.py
├── null_expression_nodes.py
├── string_expression_nodes.py
├── temporal_expression_nodes.py
├── type_expression_nodes.py
├── ternary_expression_nodes.py
├── base_expression_node.py
├── types.py
└── __init__.py

core/expression_visitors/       # 13 files - replaced by unified_visitor
├── arithmetic_visitor.py
├── boolean_visitor.py
├── conditional_visitor.py
├── core_visitor.py
├── horizontal_visitor.py
├── name_visitor.py
├── native_visitor.py
├── null_visitor.py
├── string_visitor.py
├── temporal_visitor.py
├── type_visitor.py
├── ternary_visitor.py
└── expression_visitor.py

core/protocols/                 # 13 files - enums no longer needed
├── arithmetic_protocols.py
├── boolean_protocols.py
├── conditional_protocols.py
├── core_protocols.py
├── horizontal_protocols.py
├── name_protocols.py
├── native_protocols.py
├── null_protocols.py
├── string_protocols.py
├── temporal_protocols.py
├── type_protocols.py
├── ternary_protocols.py
└── __init__.py
```

### Unchanged Files

- `backends/expression_systems/**/*.py` - all backend methods stay, just called via registry
- `core/namespaces/base.py` - base class unchanged
- `core/expression_api/descriptor.py` - namespace descriptors unchanged
- Public API - completely unchanged

---

## Risk Mitigation

### Technical Risks

1. **Phase 3 is the key gate**: All tests must pass after updating compile() before deleting legacy code
   - Mitigation: Run full test suite, ensure 100% pass rate before Phase 4

2. **Backend method signatures**: Some backend methods may have unexpected signatures
   - Mitigation: Function registry includes backend_method name; verify each mapping

3. **Ternary lowering complexity**: Complex ternary expressions may not lower cleanly
   - Mitigation: Comprehensive tests for ternary → IfThenNode conversion

4. **Namespace method changes**: Updating ~80 namespace methods is error-prone
   - Mitigation: Systematic file-by-file approach; run tests after each file

### Process Risks

1. **Large refactoring scope**: ~3,000 lines modified
   - Mitigation: Phased approach - infrastructure first, then namespaces, then cleanup

2. **Test coverage**: Tests may rely on internal implementation details
   - Mitigation: Focus on public API behavior; internal structure can change

3. **Rollback**: Need ability to revert if issues found
   - Mitigation: Work on feature branch; don't delete legacy until tests pass

---

## Success Criteria

### Functional

1. ✅ All existing tests pass
2. ✅ `expr.to_substrait()` produces valid Substrait protobuf
3. ✅ `BooleanExpressionAPI.from_substrait()` round-trips correctly
4. ✅ Expressions can be consumed by DuckDB's `from_substrait()`

### Architectural

1. ✅ Single unified visitor (vs 12 category visitors)
2. ✅ 6 node types (vs 40+ node classes)
3. ✅ Function registry as single source of truth for operations
4. ✅ Codebase is ~1,000-2,000 lines smaller

### Developer Experience

1. ✅ Adding new operations requires only:
   - One `FunctionDef` in registry
   - One method on ExpressionSystem (if not already exists)
   - One namespace method (if user-facing)
2. ✅ Clear mapping from internal names to Substrait standard names
3. ✅ Easy to identify which operations are standard vs extensions

---

## Appendix: Substrait Alignment Matrix

### Comparison Functions

| mountainash | Substrait URI | Substrait Name | Status |
|-------------|---------------|----------------|--------|
| `eq` | functions_comparison.yaml | `equal` | ✅ Standard |
| `ne` | functions_comparison.yaml | `not_equal` | ✅ Standard |
| `gt` | functions_comparison.yaml | `gt` | ✅ Standard |
| `lt` | functions_comparison.yaml | `lt` | ✅ Standard |
| `ge` | functions_comparison.yaml | `gte` | ✅ Standard |
| `le` | functions_comparison.yaml | `lte` | ✅ Standard |
| `is_null` | functions_comparison.yaml | `is_null` | ✅ Standard |
| `is_not_null` | functions_comparison.yaml | `is_not_null` | ✅ Standard |
| `coalesce` | functions_comparison.yaml | `coalesce` | ✅ Standard |
| `greatest` | functions_comparison.yaml | `greatest` | ✅ Standard |
| `least` | functions_comparison.yaml | `least` | ✅ Standard |
| `between` | functions_comparison.yaml | `between` | ✅ Standard |
| `is_close` | mountainash/functions.yaml | `is_close` | ⚡ Extension |

### Boolean Functions

| mountainash | Substrait URI | Substrait Name | Status |
|-------------|---------------|----------------|--------|
| `and_` | functions_boolean.yaml | `and` | ✅ Standard |
| `or_` | functions_boolean.yaml | `or` | ✅ Standard |
| `not_` | functions_boolean.yaml | `not` | ✅ Standard |
| `xor_` | functions_boolean.yaml | `xor` | ✅ Standard |
| `xor_parity` | mountainash/functions.yaml | `xor_parity` | ⚡ Extension |

### Arithmetic Functions

| mountainash | Substrait URI | Substrait Name | Status |
|-------------|---------------|----------------|--------|
| `add` | functions_arithmetic.yaml | `add` | ✅ Standard |
| `subtract` | functions_arithmetic.yaml | `subtract` | ✅ Standard |
| `multiply` | functions_arithmetic.yaml | `multiply` | ✅ Standard |
| `divide` | functions_arithmetic.yaml | `divide` | ✅ Standard |
| `modulo` | functions_arithmetic.yaml | `modulus` | ✅ Standard |
| `power` | functions_arithmetic.yaml | `power` | ✅ Standard |
| `floor_divide` | mountainash/functions.yaml | `floor_divide` | ⚡ Extension |

### String Functions

| mountainash | Substrait URI | Substrait Name | Status |
|-------------|---------------|----------------|--------|
| `str_upper` | functions_string.yaml | `upper` | ✅ Standard |
| `str_lower` | functions_string.yaml | `lower` | ✅ Standard |
| `str_concat` | functions_string.yaml | `concat` | ✅ Standard |
| `str_substring` | functions_string.yaml | `substring` | ✅ Standard |
| `str_trim` | functions_string.yaml | `trim` | ✅ Standard |
| `str_ltrim` | functions_string.yaml | `ltrim` | ✅ Standard |
| `str_rtrim` | functions_string.yaml | `rtrim` | ✅ Standard |
| `str_length` | functions_string.yaml | `char_length` | ✅ Standard |
| `str_replace` | functions_string.yaml | `replace` | ✅ Standard |
| `str_contains` | functions_string.yaml | `contains` | ✅ Standard |
| `str_starts_with` | functions_string.yaml | `starts_with` | ✅ Standard |
| `str_ends_with` | functions_string.yaml | `ends_with` | ✅ Standard |
| `pat_like` | functions_string.yaml | `like` | ✅ Standard |
| `pat_regex_match` | functions_string.yaml | `regexp_match_substring` | ✅ Standard |
| `pat_regex_replace` | functions_string.yaml | `regexp_replace` | ✅ Standard |

### Temporal Functions

| mountainash | Substrait URI | Substrait Name | Status |
|-------------|---------------|----------------|--------|
| `dt_year` | functions_datetime.yaml | `extract(YEAR)` | ✅ Standard |
| `dt_month` | functions_datetime.yaml | `extract(MONTH)` | ✅ Standard |
| `dt_day` | functions_datetime.yaml | `extract(DAY)` | ✅ Standard |
| `dt_hour` | functions_datetime.yaml | `extract(HOUR)` | ✅ Standard |
| `dt_minute` | functions_datetime.yaml | `extract(MINUTE)` | ✅ Standard |
| `dt_second` | functions_datetime.yaml | `extract(SECOND)` | ✅ Standard |
| `dt_add_*` | functions_datetime.yaml | `add` | ✅ Standard |
| `dt_diff_*` | functions_datetime.yaml | `subtract` | ✅ Standard |
| `dt_truncate` | functions_datetime.yaml | `round_temporal` | ✅ Standard |

### Ternary Logic (Lowered)

| mountainash | Lowers To | Status |
|-------------|-----------|--------|
| `t_eq` | `IfThen(is_null → 0, eq → 1, else → -1)` | ✅ Lowered |
| `t_ne` | `IfThen(is_null → 0, ne → 1, else → -1)` | ✅ Lowered |
| `t_gt` | `IfThen(is_null → 0, gt → 1, else → -1)` | ✅ Lowered |
| `t_and` | `least(a, b)` (min semantics) | ✅ Lowered |
| `t_or` | `greatest(a, b)` (max semantics) | ✅ Lowered |
| `t_not` | `negate(x)` (sign flip) | ✅ Lowered |
| `is_true` | `eq(x, 1)` | ✅ Lowered |
| `maybe_true` | `ge(x, 0)` | ✅ Lowered |

---

## References

- [Substrait Home](https://substrait.io/)
- [Substrait Extended Expression](https://substrait.io/expressions/extended_expression/)
- [Substrait Extensions](https://substrait.io/extensions/)
- [Substrait Python](https://github.com/substrait-io/substrait-python)
- [ibis-substrait](https://github.com/ibis-project/ibis-substrait)
- [Substrait functions_comparison.yaml](https://github.com/substrait-io/substrait/blob/main/extensions/functions_comparison.yaml)
- [Substrait functions_boolean.yaml](https://github.com/substrait-io/substrait/blob/main/extensions/functions_boolean.yaml)
- [Substrait functions_arithmetic.yaml](https://github.com/substrait-io/substrait/blob/main/extensions/functions_arithmetic.yaml)
- [Substrait functions_string.yaml](https://github.com/substrait-io/substrait/blob/main/extensions/functions_string.yaml)
- [Substrait functions_datetime.yaml](https://github.com/substrait-io/substrait/blob/main/extensions/functions_datetime.yaml)
