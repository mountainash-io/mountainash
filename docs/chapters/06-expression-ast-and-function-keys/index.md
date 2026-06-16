---
title: Expression AST and Function Keys
description: The Pydantic-based expression AST including ExpressionNode base, function key enums, and all concrete node types from ScalarFunctionNode to WindowFunctionNode.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 6: Expression AST and Function Keys

## Summary

The Pydantic-based expression AST: ExpressionNode base, function key enums, ScalarFunctionNode, FieldReferenceNode, LiteralNode, CastNode, IfThenNode, SingularOrListNode, WindowFunctionNode, WindowSpec, WindowBound, and OverNode.

---

## Introduction

When you call `ma.col("price").multiply(ma.col("qty"))`, mountainash does not compute anything. Instead, it constructs an abstract syntax tree (AST) of expression nodes. This AST is the internal representation that the compilation system walks to produce backend-native code. Understanding the AST node types gives you insight into what the library can represent and how it maps user-facing operations to compiler-facing structures.

This chapter dissects each node type in the expression AST, starting with the base class and progressing through field references, literals, scalar functions, conditionals, and window functions.

<!-- concept:55 -->
## ExpressionNode Base

`ExpressionNode` is the abstract base class for all expression AST nodes. It inherits from Pydantic's `BaseModel` and is configured as frozen (immutable). Every concrete node type inherits from `ExpressionNode` and implements the `accept` method for visitor dispatch.

```python
class ExpressionNode(BaseModel, ABC):
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )

    function_key: Optional[Enum] = None

    @abstractmethod
    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch compilation."""
        ...
```

The `function_key` field is optional because not all node types use it. `ScalarFunctionNode` uses function keys to identify which operation it represents (ADD, UPPER, EQ, etc.). Other node types like `FieldReferenceNode` and `LiteralNode` have their own identification mechanisms.

Key properties of `ExpressionNode` include:

- **Immutability**: Once created, nodes cannot be modified (enforced by `frozen=True`)
- **Validation**: Pydantic validates all field types at construction time
- **Serialization**: Nodes can be converted to and from dictionaries via `model_dump()`/`model_validate()`
- **Visitor pattern**: Every node implements `accept()` for double-dispatch compilation

<!-- concept:66 -->
## Function Key Enums

Function key enums are the identifiers that tell the compiler which specific operation a `ScalarFunctionNode` represents. Rather than using string identifiers (which are error-prone), mountainash uses Python `Enum` values from the operation enum classes defined in the constants module.

The function key system is organized into two prefixes. Substrait-standard functions use keys from the official Substrait function catalog (comparison, arithmetic, boolean, string, datetime). Mountainash extension functions use keys prefixed with the mountainash namespace for operations not covered by Substrait.

```python
from mountainash.core.constants import (
    CONST_EXPRESSION_ARITHMETIC_OPERATORS,
    CONST_EXPRESSION_STRING_OPERATORS,
)

# A node representing addition
node.function_key = CONST_EXPRESSION_ARITHMETIC_OPERATORS.ADD

# A node representing string uppercase
node.function_key = CONST_EXPRESSION_STRING_OPERATORS.UPPER
```

#### Diagram: Function Key Taxonomy
<iframe src="../../sims/function-key-taxonomy/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Function Key Taxonomy</summary>
Type: diagram
**sim-id:** function-key-taxonomy<br/>
**Library:** vis-network<br/>
**Status:** Specified

A hierarchical tree diagram showing the function key organization. Root node "Function Keys" branches into "Substrait Standard" and "Mountainash Extensions". Substrait branches into Comparison (6 keys), Arithmetic (7 keys), Boolean (5 keys), String (12 keys), Pattern (4 keys), Temporal (24 keys), Conditional (3 keys). Extensions branch into Name, Null, Native, Aggregate, List, Struct, Ternary. Each leaf node shows the enum class name. Clicking a category expands to show all enum members. Colors: LimeGreen for EXAST taxonomy. Learning objective: Categorize function keys by their Substrait alignment and locate extension operations (Bloom: Understand).
</details>

The two-prefix system enables mountainash to maintain alignment with the Substrait standard for interoperability while extending beyond it for practical features. The `ExpressionFunctionRegistry` (covered in Chapter 7) maps each function key to its Substrait URI and backend method name.

<!-- concept:57 -->
## FieldReferenceNode

A `FieldReferenceNode` represents a column reference in the expression AST. It corresponds to the `col()` entry point function and stores the column name that will be resolved at compile time.

```python
class FieldReferenceNode(ExpressionNode):
    """Reference to a named field (column) in the input data."""
    column_name: str

    def accept(self, visitor):
        return visitor.visit_field_reference(self)
```

The node is intentionally simple. It holds a single string (the column name) and delegates all compilation logic to the visitor. When the Polars backend's visitor encounters this node, it produces `pl.col(node.column_name)`. The Ibis backend produces an Ibis column reference. The Narwhals backend produces `nw.col(node.column_name)`.

Field reference nodes appear at the leaves of expression trees. They are the terminal points where the AST connects to actual data columns. Every expression tree must eventually reach one or more `FieldReferenceNode` instances (or `LiteralNode` instances) at its leaves.

<!-- concept:58 -->
## LiteralNode

A `LiteralNode` represents a constant value embedded in the expression AST. It corresponds to the `lit()` entry point function and stores the Python value along with optional type information.

```python
class LiteralNode(ExpressionNode):
    """A literal (constant) value in an expression."""
    value: Any
    dtype: Optional[str] = None

    def accept(self, visitor):
        return visitor.visit_literal(self)
```

Literal nodes support all Python scalar types: strings, integers, floats, booleans, None, dates, and datetimes. The optional `dtype` field allows explicit type specification when the Python type is ambiguous (for example, distinguishing between i32 and i64 for an integer value).

<!-- concept:56 -->
## ScalarFunctionNode

`ScalarFunctionNode` is the workhorse of the expression AST. It represents any operation that takes one or more expression arguments and produces a scalar result per row. This includes arithmetic, comparison, boolean, string, datetime, and most other operations.

```python
class ScalarFunctionNode(ExpressionNode):
    """A scalar function call with arguments and optional options."""
    function_key: Enum
    arguments: list[ExpressionNode]
    options: dict[str, Any] = {}

    def accept(self, visitor):
        return visitor.visit_scalar_function(self)
```

The `function_key` identifies which operation this node represents (from the function key enums). The `arguments` list contains child expression nodes that serve as inputs to the function. The `options` dictionary carries additional parameters that are not expressions (like a format string or a flag).

For example, `ma.col("price").add(ma.col("tax"))` produces a `ScalarFunctionNode` with `function_key=ADD` and `arguments=[FieldReferenceNode("price"), FieldReferenceNode("tax")]`.

| Field | Type | Purpose |
|-------|------|---------|
| `function_key` | Enum | Identifies the operation (ADD, UPPER, EQ, etc.) |
| `arguments` | list[ExpressionNode] | Child expressions serving as inputs |
| `options` | dict[str, Any] | Non-expression parameters (format, flags) |

<!-- concept:59 -->
## CastNode

A `CastNode` represents a type conversion operation. It wraps an input expression and specifies a target data type. Unlike `ScalarFunctionNode`, cast has dedicated handling because type conversions are structurally different from function calls in the Substrait specification.

```python
class CastNode(ExpressionNode):
    """Type cast expression."""
    input: ExpressionNode
    target_type: str  # Canonical MountainashDtype string

    def accept(self, visitor):
        return visitor.visit_cast(self)
```

The `target_type` is stored as a canonical `MountainashDtype` string (e.g., "i64", "fp32", "string"). The `resolve_dtype()` function normalizes the user's input before the node is constructed, so the AST always contains canonical type identifiers regardless of what alias the user originally provided.

<!-- concept:60 -->
## IfThenNode

An `IfThenNode` represents a conditional expression (if-then-else logic). It corresponds to the `when().then().otherwise()` API and stores paired lists of conditions and results, plus an optional else value.

```python
class IfThenNode(ExpressionNode):
    """Conditional if-then-else expression (Substrait IfThen)."""
    ifs: list[ExpressionNode]    # Condition expressions
    thens: list[ExpressionNode]  # Result expressions (same length as ifs)
    else_value: Optional[ExpressionNode] = None

    def accept(self, visitor):
        return visitor.visit_if_then(self)
```

The `ifs` and `thens` lists are parallel: `ifs[0]` is paired with `thens[0]`, `ifs[1]` with `thens[1]`, and so on. Conditions are evaluated in order, and the result from the first matching condition is returned. If no condition matches and `else_value` is set, it provides the default. If no condition matches and `else_value` is None, the result is null.

This structure aligns with SQL's CASE WHEN syntax and Substrait's IfThen expression type. The backend compiler translates it to the appropriate native construct.

<!-- concept:61 -->
## SingularOrListNode

A `SingularOrListNode` represents a membership test operation (IN or NOT IN). It checks whether a value appears in a list of candidates, corresponding to SQL's `value IN (a, b, c)` syntax.

```python
class SingularOrListNode(ExpressionNode):
    """Membership test: value IN (candidates...)."""
    value: ExpressionNode
    options: list[ExpressionNode]

    def accept(self, visitor):
        return visitor.visit_singular_or_list(self)
```

The `value` field holds the expression being tested, and `options` holds the list of candidate expressions. Both the value and candidates can be any expression type, though candidates are typically literal values.

```python
import mountainash as ma

# Check if status is one of several values
active = ma.col("status").is_in(["active", "pending", "trial"])
```

<!-- concept:62 -->
## WindowFunctionNode

A `WindowFunctionNode` represents a window function application. It combines an aggregation or ranking function with a window specification that defines partitioning and ordering.

```python
class WindowFunctionNode(ExpressionNode):
    """Window function with specification."""
    function: ExpressionNode      # The aggregation/ranking expression
    window_spec: WindowSpec       # Partition, order, and frame definition

    def accept(self, visitor):
        return visitor.visit_window_function(self)
```

Window function nodes are created when the `.over()` method is called on an aggregation expression. The `function` field holds the underlying aggregation (e.g., a sum or rank), and the `window_spec` defines how rows are grouped and ordered for the computation.

<!-- concept:63 -->
## WindowSpec

`WindowSpec` is a Pydantic model that defines the window over which a window function operates. It specifies three components: the partition columns (grouping), the ordering columns (sort within each partition), and optional frame bounds.

```python
class WindowSpec(BaseModel):
    """Window specification for partitioning, ordering, and framing."""
    partition_by: list[str] = []
    order_by: list[SortField] = []
    lower_bound: Optional[WindowBound] = None
    upper_bound: Optional[WindowBound] = None
```

The partition determines which rows are grouped together for the computation. The order determines the sequence within each partition. The frame bounds, when specified, restrict the computation to a subset of rows relative to the current row.

#### Diagram: Window Function Anatomy
<iframe src="../../sims/window-function-anatomy/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Window Function Anatomy</summary>
Type: microsim
**sim-id:** window-function-anatomy<br/>
**Library:** p5.js<br/>
**Status:** Specified

An interactive visualization of a window function operating on tabular data. A 10-row table is displayed with partition groups highlighted in alternating colors. A slider moves the "current row" indicator, and for each position, the window frame (set of rows included in the computation) is highlighted. Dropdown selects between SUM, RANK, and LAG functions. Controls allow changing partition columns and frame bounds. The computed value for the current row updates in real time. Colors: MediumPurple highlight for the active window frame. Learning objective: Predict the output of window functions given different partition, order, and frame specifications (Bloom: Apply).
</details>

<!-- concept:64 -->
## WindowBound

A `WindowBound` defines one edge of a window frame. It specifies whether the bound is relative to the current row (preceding or following by N rows) or absolute (unbounded, or the current row itself).

```python
class WindowBoundType(str, Enum):
    CURRENT_ROW = "current_row"
    PRECEDING = "preceding"
    FOLLOWING = "following"
    UNBOUNDED_PRECEDING = "unbounded_preceding"
    UNBOUNDED_FOLLOWING = "unbounded_following"
```

Common frame configurations include:

- **Unbounded preceding to current row**: Running aggregate (default for ordered windows)
- **N preceding to N following**: Sliding window of fixed size
- **Unbounded preceding to unbounded following**: Full partition aggregate
- **Current row to unbounded following**: Reverse running aggregate

The bound type and offset work together. `PRECEDING` with offset 3 means "three rows before the current row." `UNBOUNDED_PRECEDING` means "the first row in the partition." `CURRENT_ROW` means exactly the current row position.

<!-- concept:65 -->
## OverNode

The `OverNode` is a mountainash extension node that represents the `.over()` method call in the expression API. It serves as a bridge between the user-facing window function syntax and the underlying `WindowFunctionNode` representation.

When you write `ma.col("salary").sum().over(partition_by="dept")`, the `.over()` method constructs an `OverNode` that packages the aggregation expression with the window specification. During compilation, the OverNode may be rewritten into a `WindowFunctionNode` or compiled directly depending on the backend.

The OverNode captures the user's intent in a form that is close to the API surface, while `WindowFunctionNode` captures it in a form aligned with the Substrait specification. This separation allows the API to evolve independently of the compilation target.

## Key Takeaways

- `ExpressionNode` is the immutable, Pydantic-backed base class for all AST nodes, providing validation, serialization, and visitor dispatch.
- Function key enums use two prefixes (Substrait standard and Mountainash extensions) to identify operations, enabling both interoperability and practical extension.
- `ScalarFunctionNode` handles the majority of operations (arithmetic, comparison, string, datetime) through its function_key + arguments structure.
- `FieldReferenceNode` and `LiteralNode` serve as leaf nodes, connecting the AST to actual data columns and constant values respectively.
- `CastNode` handles type conversions as a distinct node type, using canonical MountainashDtype strings for the target type.
- `IfThenNode` represents conditional logic with parallel condition/result lists, aligning with SQL CASE WHEN and Substrait IfThen.
- `WindowFunctionNode` combines an aggregation with a `WindowSpec` (partition, order, frame) for row-level computations over partitioned data.
- The AST is purely structural; no computation occurs in any node. All execution is deferred to the visitor-based compilation system.
