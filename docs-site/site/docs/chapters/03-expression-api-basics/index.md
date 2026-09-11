---
title: Expression API Basics
description: Introduction to the fluent expression API including col() and lit() factory functions, expression building, the BaseExpressionAPI protocol, operator overloading, and null handling.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 3: Expression API Basics

## Summary

Introduction to the fluent expression API: the col() and lit() factory functions, expression building patterns, BaseExpressionAPI protocol, BooleanExpressionAPI, fluent expression chaining, operator overloading, and null handling.

---

## Introduction

The expression API is the primary interface for describing column-level computations in mountainash. Rather than manipulating data directly, you build abstract expression objects that describe what transformation should happen. These expressions compile to backend-native operations at execution time, providing a single API that works identically across Polars, pandas (via Narwhals), and SQL databases (via Ibis).

This chapter introduces the two entry point functions (`col` and `lit`), explains how expressions compose into chains, and covers the protocol classes that define the expression interface. We conclude with operator overloading and null-handling semantics.

<!-- concept:25 -->
## col Function

The `col` function creates a column reference expression. It represents "the value of this column in each row" without actually accessing any data. The name you pass to `col` must match a column name in the DataFrame that the expression will eventually be compiled against.

```python
import mountainash as ma

# Create a column reference -- no data access yet
age_expr = ma.col("age")
name_expr = ma.col("first_name")
```

Under the hood, `col("age")` constructs a `FieldReferenceNode` in the expression AST. This node stores the column name and provides all the methods defined by `BaseExpressionAPI`, enabling you to chain operations onto it.

The `col` function accepts a single string argument representing the column name. When the expression is eventually compiled for a specific backend, the column reference resolves to the appropriate accessor. For Polars, this becomes `pl.col("age")`; for Ibis, it becomes a table column reference; for Narwhals, it becomes `nw.col("age")`.

- Column names are case-sensitive
- Names must match exactly what exists in the DataFrame schema
- No validation occurs at construction time (errors appear at compile time)
- Multiple `col()` calls can reference the same column

<!-- concept:26 -->
## lit Function

The `lit` function creates a literal value expression. It wraps a Python scalar value into the expression system so that constants can participate in expression chains alongside column references.

```python
import mountainash as ma

# Wrap scalar values as expressions
threshold = ma.lit(100)
label = ma.lit("unknown")
flag = ma.lit(True)
```

Literal expressions are essential whenever you need a constant in a computation. Without `lit`, you cannot use plain Python values in expression arithmetic because the system needs everything to be an expression node to build the AST properly.

The following code demonstrates why `lit` is necessary for mixed computations.

```python
# This works: expression + expression
normalized = ma.col("score") / ma.lit(100)

# Operator overloading also handles plain values on the right:
normalized = ma.col("score") / 100  # Automatically wraps 100 as lit(100)

# But left-side scalars need explicit lit():
offset = ma.lit(1000) - ma.col("deduction")
```

| Input Type | Example | AST Node Created |
|-----------|---------|-----------------|
| `str` | `ma.lit("hello")` | `LiteralNode(value="hello")` |
| `int` | `ma.lit(42)` | `LiteralNode(value=42)` |
| `float` | `ma.lit(3.14)` | `LiteralNode(value=3.14)` |
| `bool` | `ma.lit(True)` | `LiteralNode(value=True)` |
| `None` | `ma.lit(None)` | `LiteralNode(value=None)` |

<!-- concept:27 -->
## Expression Building

Expression building is the process of composing simple expressions (`col`, `lit`) into complex operations through method calls. Each method call produces a new expression node that wraps the previous expression as its input, forming a tree of operations.

The fundamental pattern is: start with an entry point (`col` or `lit`), then chain operations that progressively build up the desired computation. No computation occurs during building. The result is a tree of AST nodes that records what should happen, not a computed value.

```python
import mountainash as ma

# Simple: column reference
expr1 = ma.col("price")

# Compound: arithmetic on a column
expr2 = ma.col("price").multiply(ma.col("quantity"))

# Complex: multiple operations chained
expr3 = (
    ma.col("price")
    .multiply(ma.col("quantity"))
    .add(ma.col("tax"))
    .alias("total_cost")
)
```

#### Diagram: Expression Building Tree
<iframe src="../../sims/expression-building-tree/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Expression Building Tree</summary>
Type: diagram
**sim-id:** expression-building-tree<br/>
**Library:** vis-network<br/>
**Status:** Specified

An interactive tree diagram showing how expression method calls build an AST. Root node at top shows a ScalarFunctionNode (ADD). Its children are another ScalarFunctionNode (MULTIPLY) and a FieldReferenceNode ("tax"). The MULTIPLY node's children are two FieldReferenceNode instances ("price" and "quantity"). Nodes are color-coded by type: DarkGreen for ScalarFunctionNode, LimeGreen for FieldReferenceNode, Gold for LiteralNode. Clicking any node shows its properties (function_key, arguments). Hovering shows the Python code that created it. Learning objective: Construct expression ASTs by understanding how each method call creates a new node wrapping the previous (Bloom: Apply).
</details>

Each building operation is immutable. The original expression remains unchanged, and a new expression object wraps it. This allows you to reuse partial expressions in multiple contexts.

<!-- concept:28 -->
## BaseExpressionAPI

`BaseExpressionAPI` is the protocol class that defines all methods available on any expression object. It establishes the contract that every expression (whether created by `col`, `lit`, `when`, or any other entry point) must support.

The protocol is organized into method categories. Comparison methods produce boolean expressions. Arithmetic methods produce numeric expressions. String and datetime methods access specialized namespaces. Aggregation methods produce scalar results from grouped data.

```python
class BaseExpressionAPI(Protocol):
    """Every expression object supports these methods."""

    # Comparison
    def eq(self, other) -> BooleanExpressionAPI: ...
    def ne(self, other) -> BooleanExpressionAPI: ...
    def gt(self, other) -> BooleanExpressionAPI: ...
    def lt(self, other) -> BooleanExpressionAPI: ...
    def ge(self, other) -> BooleanExpressionAPI: ...
    def le(self, other) -> BooleanExpressionAPI: ...

    # Arithmetic
    def add(self, other) -> BaseExpressionAPI: ...
    def subtract(self, other) -> BaseExpressionAPI: ...
    def multiply(self, other) -> BaseExpressionAPI: ...
    def divide(self, other) -> BaseExpressionAPI: ...

    # Naming
    def alias(self, name: str) -> BaseExpressionAPI: ...

    # Type casting
    def cast(self, dtype) -> BaseExpressionAPI: ...
```

The protocol uses structural subtyping, meaning any object with these methods satisfies the contract without inheriting from `BaseExpressionAPI`. This decouples the API definition from its implementation.

<!-- concept:29 -->
## BooleanExpressionAPI

`BooleanExpressionAPI` extends `BaseExpressionAPI` with methods specific to boolean (true/false) expressions. When a comparison operation produces a boolean result, the returned object supports logical combination methods that regular numeric expressions do not provide.

```python
import mountainash as ma

# Comparisons return BooleanExpressionAPI objects
is_adult = ma.col("age").ge(18)       # Boolean expression
is_active = ma.col("status").eq("active")  # Boolean expression

# Boolean expressions support logical operators
eligible = is_adult.and_(is_active)
excluded = is_adult.not_()
either = is_adult.or_(is_active)
```

The boolean API provides these logical methods:

- `and_(*others)` -- logical AND with one or more expressions
- `or_(*others)` -- logical OR with one or more expressions
- `not_()` -- logical negation
- `xor(other)` -- exclusive OR

The trailing underscore on `and_` and `or_` avoids collision with Python's reserved keywords. The `not_()` method takes no arguments because it operates on the expression it is called on.

<!-- concept:30 -->
## Fluent Expression Chain

A fluent expression chain is a sequence of method calls where each call returns an expression object that supports further method calls. This enables writing complex transformations as a single, readable pipeline.

The fluent pattern works because every method on `BaseExpressionAPI` returns either a `BaseExpressionAPI` or a `BooleanExpressionAPI` object. These return types support all the same methods (plus boolean-specific ones), so chaining continues indefinitely.

```python
import mountainash as ma

# A fluent chain computing a derived metric
engagement_score = (
    ma.col("clicks")
    .add(ma.col("shares").multiply(ma.lit(2)))
    .divide(ma.col("impressions"))
    .multiply(ma.lit(100))
    .alias("engagement_pct")
)
```

The chain reads left-to-right and top-to-bottom as a sequence of transformations. Each line adds one operation to the AST tree. The final `.alias()` assigns a name to the output column when this expression is used in a `select` or `with_columns` operation.

- Every intermediate result is a valid expression (no "dangling" states)
- Chains can branch by saving intermediate references
- The order of operations follows method call order (innermost first in the AST)
- Parentheses group multi-line chains for readability

<!-- concept:31 -->
## Operator Overloading

Mountainash expressions support Python's standard arithmetic and comparison operators through operator overloading. This means you can write natural mathematical syntax instead of explicit method calls for common operations.

The following operators are overloaded on expression objects.

```python
import mountainash as ma

# Arithmetic operators
total = ma.col("price") * ma.col("qty")     # multiply
net = ma.col("revenue") - ma.col("cost")    # subtract
ratio = ma.col("part") / ma.col("whole")    # divide
pct = ma.col("score") % ma.lit(100)         # modulo

# Comparison operators
adults = ma.col("age") > 18                  # gt
exact = ma.col("status") == "active"         # eq
differs = ma.col("a") != ma.col("b")        # ne

# Boolean operators
combined = (ma.col("age") > 18) & (ma.col("score") >= 80)  # and_
either = (ma.col("a") > 0) | (ma.col("b") > 0)            # or_
negated = ~(ma.col("active"))                               # not_
```

| Python Operator | Expression Method | Returns |
|----------------|-------------------|---------|
| `+` | `add` | BaseExpressionAPI |
| `-` | `subtract` | BaseExpressionAPI |
| `*` | `multiply` | BaseExpressionAPI |
| `/` | `divide` | BaseExpressionAPI |
| `%` | `modulo` | BaseExpressionAPI |
| `**` | `power` | BaseExpressionAPI |
| `//` | `floor_divide` | BaseExpressionAPI |
| `==` | `eq` | BooleanExpressionAPI |
| `!=` | `ne` | BooleanExpressionAPI |
| `>` | `gt` | BooleanExpressionAPI |
| `<` | `lt` | BooleanExpressionAPI |
| `>=` | `ge` | BooleanExpressionAPI |
| `<=` | `le` | BooleanExpressionAPI |
| `&` | `and_` | BooleanExpressionAPI |
| `\|` | `or_` | BooleanExpressionAPI |
| `~` | `not_` | BooleanExpressionAPI |

!!! note "Operator Precedence"
    Python's operator precedence applies. Bitwise operators (`&`, `|`, `~`) bind tighter than comparison operators, so boolean combinations require parentheses around each comparison: `(col("a") > 1) & (col("b") < 10)`.

<!-- concept:51 -->
## Null Handling

Null handling in mountainash provides methods for detecting, replacing, and propagating null values in expressions. Nulls represent missing or unknown data and require special treatment because standard comparisons with null produce null rather than true or false.

The core null-handling methods available on all expressions include:

```python
import mountainash as ma

# Detect nulls
has_missing = ma.col("email").is_null()
has_value = ma.col("email").is_not_null()

# Replace nulls
filled = ma.col("score").fill_null(0)
coalesced = ma.coalesce(ma.col("preferred_name"), ma.col("legal_name"))
```

The `is_null()` and `is_not_null()` methods return boolean expressions that can be used as filter predicates. The `fill_null(value)` method returns an expression that substitutes the given value wherever a null appears. The module-level `coalesce()` function takes multiple expressions and returns the first non-null value for each row.

Null propagation follows SQL semantics by default. Any arithmetic or comparison involving null produces null. This means `ma.col("x") + ma.lit(1)` produces null for rows where `x` is null, rather than raising an error.

- `is_null()` -- Returns true where the value is null
- `is_not_null()` -- Returns true where the value is not null
- `fill_null(value)` -- Replaces nulls with the given value
- `coalesce(expr1, expr2, ...)` -- First non-null from left to right
- Arithmetic with null propagates null (does not raise)
- Comparison with null returns null (not false)

## Key Takeaways

- `col("name")` creates a column reference expression that compiles to the appropriate backend accessor (pl.col, nw.col, or ibis column reference).
- `lit(value)` wraps a Python scalar into the expression system, enabling constants to participate in expression trees alongside column references.
- Expression building creates immutable AST nodes; each method call produces a new node wrapping the previous, forming a tree of operations.
- `BaseExpressionAPI` defines the full method set available on any expression through a structural protocol, enabling extensibility without inheritance.
- `BooleanExpressionAPI` adds logical combination methods (and_, or_, not_) that are only available on expressions known to produce boolean results.
- Fluent chains compose arbitrarily complex expressions by chaining methods, with each intermediate result being a valid, reusable expression.
- Operator overloading maps Python's standard operators to expression methods, enabling natural mathematical syntax for common operations.
- Null handling follows SQL semantics: nulls propagate through operations, and explicit methods (is_null, fill_null, coalesce) provide detection and replacement.
