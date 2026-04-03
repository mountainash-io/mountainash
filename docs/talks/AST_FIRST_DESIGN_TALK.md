# Conference Talk: AST-First Expression Design

## Talk Title Options

1. **"AST-First Expression Design: Why Treating Expressions as Data Changes Everything"**
2. **"Don't Execute It, Describe It: The Case for Expression ASTs"**
3. **"Expressions as Data: Serialization, Inspection, and Composition for Free"**
4. **"The Interpreter Pattern Had It Right: AST-First Design in Python"**
5. **"What If col('age') > 30 Didn't Do Anything?"**

---

## Talk Abstract (300 words)

> When you write `df.filter(pl.col("age") > 30)`, something happens immediately. Polars builds an expression. The filter executes. You get results.
>
> But what if it didn't? What if `col("age") > 30` just... described what you wanted? A data structure. A recipe. A plan—not an action.
>
> This talk introduces **AST-first expression design**: a pattern where expressions are represented as inspectable, serializable, composable data structures *before* they become backend-specific code.
>
> You'll learn:
> - **Why eager expression building is limiting** - You can't serialize a Polars expression. You can't inspect what it will do. You can't send it across a wire.
> - **The AST-first alternative** - Build a syntax tree first. Compile to backend-specific code later.
> - **What this unlocks**:
>   - **Serialization**: Save expressions to JSON, store in databases, send over APIs
>   - **Inspection**: Debug by examining the tree before execution
>   - **Composition**: Programmatically build and combine expressions
>   - **Transformation**: Optimize, normalize, or rewrite before compilation
>   - **Backend independence**: Same AST compiles to Polars, Ibis, Pandas, SQL
>   - **Telemetry**: Log what expressions are being used without executing them
>
> We'll walk through a real implementation using Pydantic for node validation, the Visitor pattern for compilation, and protocol-driven backends for extensibility.
>
> Whether you're building a query builder, a rule engine, a BI tool, or just want to understand how expression libraries work under the hood, this talk will change how you think about "code as data."
>
> Because sometimes, the best thing an expression can do is nothing—until you tell it to.

---

## Talk Outline (35-40 minutes)

### Act 1: The Problem with Eager Expressions (8 minutes)

#### Opening: What Does This Return? (2 min)

```python
import polars as pl

expr = pl.col("age") > 30

print(type(expr))
# <class 'polars.expr.expr.Expr'>

print(expr)
# col("age") > 30
```

Looks harmless. But try this:

```python
import json
json.dumps(expr)
# TypeError: Object of type Expr is not JSON serializable

import pickle
pickle.dumps(expr)
# Works, but it's opaque bytes. Can you see what's inside?
```

**The expression exists. But you can't see it. Can't save it. Can't send it.**

#### The Eager Execution Model (3 min)

Most expression libraries use **eager building**:

```python
# Polars
expr = pl.col("age").gt(30).and_(pl.col("score").ge(80))
# → Immediately creates a Polars Expr object

# Pandas
mask = (df["age"] > 30) & (df["score"] >= 80)
# → Immediately creates a boolean Series

# SQLAlchemy
stmt = select(users).where(users.c.age > 30)
# → Immediately creates an AST (SQLAlchemy gets this right!)
```

**The moment you write the expression, the library takes over.**

You get back their object. Their representation. Their format.

#### What You Can't Do (3 min)

**1. Serialize to JSON:**
```python
# Save a business rule to a database?
rule = pl.col("risk_score") > 0.8
db.save("high_risk_rule", rule)  # ← Can't serialize!
```

**2. Send over an API:**
```python
# Central rule server distributes filter logic?
response = requests.get("/rules/high_risk")
rule = response.json()  # ← Can't deserialize!
```

**3. Inspect the structure:**
```python
# What columns does this expression reference?
expr = complex_business_logic()
print(expr.get_columns())  # ← No introspection API!
```

**4. Transform before execution:**
```python
# Add audit logging to every comparison?
expr = add_logging(original_expr)  # ← Can't traverse/modify!
```

**5. Test without data:**
```python
# Verify the expression structure without a DataFrame?
assert expr.has_condition_on("age")  # ← Can't examine!
```

---

### Act 2: The AST-First Alternative (10 minutes)

#### What Is AST-First? (3 min)

**AST = Abstract Syntax Tree.** A data structure representing code.

```python
# Instead of this:
pl.col("age") > 30  # → Opaque Polars object

# Build this:
{
    "type": "comparison",
    "operator": "gt",
    "left": {"type": "column", "name": "age"},
    "right": {"type": "literal", "value": 30}
}
```

**The expression is data.** You can:
- Read it
- Write it
- Transform it
- Store it
- Send it
- And only later... execute it

#### The Two-Phase Model (3 min)

**Phase 1: Build the AST (no backend needed)**
```python
from mountainash_expressions import col, lit

# This doesn't touch Polars, Pandas, or anything else
expr = col("age").gt(30).and_(col("score").ge(80))

# It's just a tree
print(expr.to_dict())
# {
#   "type": "boolean_and",
#   "operands": [
#     {"type": "gt", "left": {"type": "col", "name": "age"}, "right": {"type": "lit", "value": 30}},
#     {"type": "ge", "left": {"type": "col", "name": "score"}, "right": {"type": "lit", "value": 80}}
#   ]
# }
```

**Phase 2: Compile to backend (when needed)**
```python
# NOW we care about the backend
polars_expr = expr.compile(polars_df)  # → pl.Expr
ibis_expr = expr.compile(ibis_table)    # → ir.Expr
pandas_mask = expr.compile(pandas_df)   # → pd.Series[bool]
```

**Separation of concerns:**
- Phase 1: What do you want?
- Phase 2: How do we do it on this backend?

#### The Pydantic Implementation (4 min)

Using Pydantic for node definitions gives us validation + serialization for free:

```python
from pydantic import BaseModel, Field
from typing import Any, Union, Literal
from enum import Enum

class NodeType(str, Enum):
    COLUMN = "column"
    LITERAL = "literal"
    COMPARISON = "comparison"
    LOGICAL = "logical"

class ExpressionNode(BaseModel):
    """Base class for all AST nodes."""

    class Config:
        extra = "forbid"  # Catch typos

    def accept(self, visitor: "ExpressionVisitor"):
        """Visitor pattern for compilation."""
        raise NotImplementedError

class ColumnNode(ExpressionNode):
    """Reference to a DataFrame column."""
    type: Literal[NodeType.COLUMN] = NodeType.COLUMN
    name: str

class LiteralNode(ExpressionNode):
    """A constant value."""
    type: Literal[NodeType.LITERAL] = NodeType.LITERAL
    value: Any

class ComparisonNode(ExpressionNode):
    """Binary comparison (gt, lt, eq, etc.)."""
    type: Literal[NodeType.COMPARISON] = NodeType.COMPARISON
    operator: Literal["eq", "ne", "gt", "ge", "lt", "le"]
    left: Union[ColumnNode, LiteralNode, "ComparisonNode", "LogicalNode"]
    right: Union[ColumnNode, LiteralNode, "ComparisonNode", "LogicalNode"]
```

**What Pydantic gives us:**
```python
# Validation
node = ComparisonNode(operator="gt", left=..., right=...)
node = ComparisonNode(operator="invalid", ...)  # ValidationError!

# Serialization
json_str = node.model_dump_json()
node_back = ComparisonNode.model_validate_json(json_str)

# Type safety
reveal_type(node.left)  # Union[ColumnNode, LiteralNode, ...]
```

---

### Act 3: What This Unlocks (12 minutes)

#### 1. Serialization (3 min)

**Save expressions to a database:**
```python
# Business rules as data
rule = col("risk_score").gt(0.8).and_(col("amount").gt(10000))

# Store in database
db.execute("""
    INSERT INTO rules (name, expression, created_at)
    VALUES (?, ?, ?)
""", ("high_risk_transaction", rule.to_json(), datetime.now()))

# Load later
row = db.fetchone("SELECT expression FROM rules WHERE name = ?", ("high_risk_transaction",))
rule = Expression.from_json(row["expression"])

# Apply to new data
flagged = df.filter(rule.compile(df))
```

**Send over HTTP:**
```python
# Server
@app.get("/rules/{rule_name}")
def get_rule(rule_name: str):
    rule = load_rule(rule_name)
    return {"expression": rule.to_dict()}

# Client
response = requests.get(f"{server}/rules/high_risk")
rule = Expression.from_dict(response.json()["expression"])
result = df.filter(rule.compile(df))
```

**Version control expressions:**
```yaml
# rules/fraud_detection.yaml
name: high_risk_transaction
version: 2.3.1
expression:
  type: logical_and
  operands:
    - type: comparison
      operator: gt
      left: {type: column, name: risk_score}
      right: {type: literal, value: 0.8}
    - type: comparison
      operator: gt
      left: {type: column, name: amount}
      right: {type: literal, value: 10000}
```

Now your business rules are in Git. With history. With code review. With diffs.

#### 2. Inspection (2 min)

**Find all columns referenced:**
```python
def get_columns(node: ExpressionNode) -> set[str]:
    """Recursively find all column references."""
    if isinstance(node, ColumnNode):
        return {node.name}
    elif isinstance(node, LiteralNode):
        return set()
    elif isinstance(node, ComparisonNode):
        return get_columns(node.left) | get_columns(node.right)
    elif isinstance(node, LogicalNode):
        return set().union(*(get_columns(op) for op in node.operands))

# Usage
expr = col("age").gt(30).and_(col("score").ge(80))
print(get_columns(expr._node))
# {"age", "score"}
```

**Validate before execution:**
```python
def validate_columns(expr: Expression, df: DataFrame) -> list[str]:
    """Check if all referenced columns exist."""
    referenced = get_columns(expr._node)
    available = set(df.columns)
    missing = referenced - available
    if missing:
        raise ValueError(f"Columns not found: {missing}")

# Fail fast with clear error
validate_columns(expr, df)  # Before compilation
```

#### 3. Composition (2 min)

**Programmatic expression building:**
```python
def build_range_filter(column: str, min_val: float, max_val: float) -> Expression:
    """Factory function for range filters."""
    return col(column).ge(min_val).and_(col(column).le(max_val))

# Build from config
config = {"column": "price", "min": 100, "max": 500}
expr = build_range_filter(**config)
```

**Combine existing expressions:**
```python
# Base rules
is_adult = col("age").ge(18)
is_premium = col("tier").eq("premium")
has_consent = col("consent").eq(True)

# Combine for different contexts
marketing_eligible = is_adult.and_(has_consent)
premium_offer = is_adult.and_(is_premium).and_(has_consent)

# Rules are reusable, composable, inspectable
```

**Build from user input:**
```python
# Query builder UI sends JSON
user_filter = {
    "and": [
        {"column": "age", "op": "gt", "value": 25},
        {"column": "country", "op": "eq", "value": "US"}
    ]
}

# Parse and compile safely
expr = Expression.from_user_input(user_filter)  # Validates!
result = df.filter(expr.compile(df))
```

#### 4. Transformation (2 min)

**Optimize expressions:**
```python
def simplify(node: ExpressionNode) -> ExpressionNode:
    """Simplify constant expressions."""
    if isinstance(node, ComparisonNode):
        if isinstance(node.left, LiteralNode) and isinstance(node.right, LiteralNode):
            # Both sides are constants - evaluate now
            result = evaluate(node.operator, node.left.value, node.right.value)
            return LiteralNode(value=result)
    return node

# col("x") > 5 AND True → col("x") > 5
# 10 > 5 → True
```

**Add instrumentation:**
```python
def add_telemetry(node: ExpressionNode, context: dict) -> ExpressionNode:
    """Wrap expression with telemetry hooks."""
    return TelemetryNode(
        inner=node,
        context=context,
        on_compile=lambda: log_expression_compiled(node, context),
        on_execute=lambda: log_expression_executed(node, context)
    )
```

**Normalize for comparison:**
```python
def normalize(node: ExpressionNode) -> ExpressionNode:
    """Canonical form for expression equality."""
    if isinstance(node, LogicalNode) and node.operator == "and":
        # Sort operands for consistent comparison
        sorted_ops = sorted(node.operands, key=lambda n: n.fingerprint())
        return LogicalNode(operator="and", operands=sorted_ops)
    return node

# Now you can compare expressions for equality
expr1 = col("a").gt(1).and_(col("b").lt(2))
expr2 = col("b").lt(2).and_(col("a").gt(1))
assert normalize(expr1) == normalize(expr2)  # Same expression!
```

#### 5. Backend Independence (2 min)

**Same AST, multiple backends:**
```python
# Define once
expr = col("age").gt(30).and_(col("active").eq(True))

# Compile to anything
polars_result = df_polars.filter(expr.compile(df_polars))
ibis_result = table_ibis.filter(expr.compile(table_ibis)).execute()
pandas_result = df_pandas[expr.compile(df_pandas)]

# Same logic, same results, different execution engines
```

**Compile to SQL:**
```python
def to_sql(node: ExpressionNode) -> str:
    """Compile AST to SQL WHERE clause."""
    if isinstance(node, ColumnNode):
        return f'"{node.name}"'
    elif isinstance(node, LiteralNode):
        return repr(node.value)
    elif isinstance(node, ComparisonNode):
        op_map = {"gt": ">", "ge": ">=", "lt": "<", "le": "<=", "eq": "=", "ne": "!="}
        return f"({to_sql(node.left)} {op_map[node.operator]} {to_sql(node.right)})"
    elif isinstance(node, LogicalNode):
        op = " AND " if node.operator == "and" else " OR "
        return f"({op.join(to_sql(n) for n in node.operands)})"

expr = col("age").gt(30).and_(col("active").eq(True))
print(to_sql(expr._node))
# (("age" > 30) AND ("active" = True))
```

#### 6. Testing (1 min)

**Test expression structure without data:**
```python
def test_high_risk_rule_structure():
    """Verify rule references expected columns."""
    rule = get_high_risk_rule()

    columns = get_columns(rule._node)
    assert "risk_score" in columns
    assert "amount" in columns

    # No DataFrame needed!

def test_expression_round_trip():
    """Verify serialization preserves structure."""
    original = col("x").gt(5).and_(col("y").lt(10))

    json_str = original.to_json()
    restored = Expression.from_json(json_str)

    assert original.fingerprint() == restored.fingerprint()
```

---

### Act 4: The Implementation Pattern (8 minutes)

#### The Visitor Pattern (3 min)

How do you compile AST → backend expression?

**The Visitor pattern:**

```python
from abc import ABC, abstractmethod

class ExpressionVisitor(ABC):
    """Abstract visitor for compiling expressions."""

    @abstractmethod
    def visit_column(self, node: ColumnNode): ...

    @abstractmethod
    def visit_literal(self, node: LiteralNode): ...

    @abstractmethod
    def visit_comparison(self, node: ComparisonNode): ...

    @abstractmethod
    def visit_logical(self, node: LogicalNode): ...

class PolarsVisitor(ExpressionVisitor):
    """Compile AST to Polars expressions."""

    def visit_column(self, node: ColumnNode):
        return pl.col(node.name)

    def visit_literal(self, node: LiteralNode):
        return pl.lit(node.value)

    def visit_comparison(self, node: ComparisonNode):
        left = node.left.accept(self)
        right = node.right.accept(self)

        ops = {
            "gt": lambda l, r: l > r,
            "ge": lambda l, r: l >= r,
            "lt": lambda l, r: l < r,
            "le": lambda l, r: l <= r,
            "eq": lambda l, r: l == r,
            "ne": lambda l, r: l != r,
        }
        return ops[node.operator](left, right)

    def visit_logical(self, node: LogicalNode):
        compiled = [op.accept(self) for op in node.operands]
        if node.operator == "and":
            return reduce(lambda a, b: a & b, compiled)
        else:
            return reduce(lambda a, b: a | b, compiled)
```

**Each node knows how to accept visitors:**
```python
class ComparisonNode(ExpressionNode):
    # ...

    def accept(self, visitor: ExpressionVisitor):
        return visitor.visit_comparison(self)
```

**Adding a new backend = adding a new visitor.** No changes to nodes.

#### The Protocol Pattern (3 min)

How do you ensure backends are complete?

**Define protocols for what backends must implement:**

```python
from typing import Protocol

class BooleanExpressionProtocol(Protocol):
    """What a backend must provide for boolean operations."""

    def eq(self, left, right): ...
    def ne(self, left, right): ...
    def gt(self, left, right): ...
    def lt(self, left, right): ...
    def ge(self, left, right): ...
    def le(self, left, right): ...
    def and_(self, left, right): ...
    def or_(self, left, right): ...
    def not_(self, operand): ...

class PolarsBackend(BooleanExpressionProtocol):
    """Polars implementation of boolean operations."""

    def eq(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left == right

    def gt(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        return left > right

    # ... etc
```

**The visitor delegates to the backend:**
```python
class BooleanVisitor:
    def __init__(self, backend: BooleanExpressionProtocol):
        self.backend = backend

    def visit_comparison(self, node: ComparisonNode):
        left = self.compile(node.left)
        right = self.compile(node.right)

        ops = {
            "gt": self.backend.gt,
            "eq": self.backend.eq,
            # ...
        }
        return ops[node.operator](left, right)
```

**Adding operations = protocol + implementations. Type-checked!**

#### The Fluent Builder (2 min)

How do you make this nice to use?

**Wrap the AST in a builder class:**

```python
class Expression:
    """Fluent API for building expression ASTs."""

    def __init__(self, node: ExpressionNode):
        self._node = node

    def gt(self, other) -> "Expression":
        other_node = self._to_node(other)
        return Expression(ComparisonNode(
            operator="gt",
            left=self._node,
            right=other_node
        ))

    def and_(self, other: "Expression") -> "Expression":
        return Expression(LogicalNode(
            operator="and",
            operands=[self._node, other._node]
        ))

    def compile(self, df) -> Any:
        backend = detect_backend(df)
        visitor = get_visitor(backend)
        return self._node.accept(visitor)

    def to_json(self) -> str:
        return self._node.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "Expression":
        node = parse_node(json_str)
        return cls(node)

def col(name: str) -> Expression:
    return Expression(ColumnNode(name=name))

def lit(value: Any) -> Expression:
    return Expression(LiteralNode(value=value))
```

**User writes:**
```python
expr = col("age").gt(30).and_(col("active").eq(True))
```

**Under the hood:**
```
col("age")               → Expression(ColumnNode(name="age"))
    .gt(30)              → Expression(ComparisonNode(op="gt", left=..., right=LiteralNode(30)))
    .and_(col("active")...) → Expression(LogicalNode(op="and", operands=[...]))
```

**Clean API, powerful internals.**

---

### Closing (4 minutes)

#### The Design Philosophy

**Eager execution:** "Do what I say immediately"
- Fast for simple cases
- Limited composability
- Opaque results

**AST-first:** "Describe what you want, execute when ready"
- Inspectable
- Serializable
- Transformable
- Backend-agnostic
- Testable

**The tradeoff:** Slight overhead in building the tree. But you gain superpowers.

#### When to Use AST-First

**Use AST-first when:**
- Expressions need to be serialized (rules engines, configs)
- Multiple backends are possible (DataFrame abstraction)
- Expressions come from untrusted input (query builders)
- You need to transform/optimize before execution
- Testing expression structure matters
- Telemetry on expression usage is needed

**Maybe skip AST-first when:**
- Single backend, simple expressions
- Performance is critical and overhead matters
- Expression never leaves the process

#### The Takeaways

1. **Code is data** - The old Lisp wisdom applies to expression libraries too
2. **Defer execution** - Build the description, compile later
3. **Separation of concerns** - AST definition vs compilation vs execution
4. **Visitor pattern** - New backends without changing nodes
5. **Protocol pattern** - Type-safe backend contracts
6. **Pydantic** - Validation + serialization for free

#### Resources

- mountainash-expressions: [GitHub link]
- Pydantic documentation: [Link]
- "Design Patterns" (Gang of Four) - Visitor pattern chapter
- "Structure and Interpretation of Computer Programs" - Code as data

---

## Supplementary Materials

### Architecture Diagram

```
User Code                    AST Layer                 Backend Layer
─────────────────────────────────────────────────────────────────────

col("age").gt(30)     →     ComparisonNode
                            ├─ left: ColumnNode
                            │        name: "age"
                            └─ right: LiteralNode
                                     value: 30

                                     │
                                     │ .compile(df)
                                     ▼

                            ┌─────────────────┐
                            │ Backend         │
                            │ Detection       │
                            └────────┬────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
               PolarsVisitor    IbisVisitor    PandasVisitor
                    │                │                │
                    ▼                ▼                ▼
               pl.Expr          ir.Expr         pd.Series
```

### The Full Node Hierarchy

```python
ExpressionNode (base)
├── ColumnNode           # col("name")
├── LiteralNode          # lit(42)
├── ComparisonNode       # gt, lt, eq, ne, ge, le
├── LogicalNode          # and, or
├── UnaryNode            # not, is_null
├── ArithmeticNode       # add, sub, mul, div
├── StringNode           # contains, startswith, upper
├── TemporalNode         # year, month, day, truncate
└── ConditionalNode      # when/then/otherwise
```

### Serialization Format Options

**JSON (human-readable, widely supported):**
```json
{
  "type": "comparison",
  "operator": "gt",
  "left": {"type": "column", "name": "age"},
  "right": {"type": "literal", "value": 30}
}
```

**YAML (more readable for complex expressions):**
```yaml
type: comparison
operator: gt
left:
  type: column
  name: age
right:
  type: literal
  value: 30
```

**MessagePack (compact binary, fast):**
```python
import msgpack
packed = msgpack.packb(node.model_dump())
unpacked = msgpack.unpackb(packed)
```

### Expression Fingerprinting

```python
import hashlib
import json

def fingerprint(node: ExpressionNode) -> str:
    """Deterministic hash for expression identity."""
    # Normalize first (sort operands, etc.)
    normalized = normalize(node)

    # Serialize deterministically
    json_str = normalized.model_dump_json(sort_keys=True)

    # Hash
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]

# Same expression = same fingerprint
expr1 = col("a").gt(1).and_(col("b").lt(2))
expr2 = col("b").lt(2).and_(col("a").gt(1))

print(fingerprint(normalize(expr1._node)))
print(fingerprint(normalize(expr2._node)))
# Both: "a3f7c2e8b1d4..."
```

### Real-World Use Cases

**1. Rules Engine:**
```python
# Store rules in database
rules = [
    Rule(name="high_risk", expr=col("risk").gt(0.8)),
    Rule(name="premium", expr=col("tier").eq("premium")),
]

for rule in rules:
    db.save(rule.name, rule.expr.to_json())

# Load and apply
rule = Rule.load("high_risk")
flagged = df.filter(rule.expr.compile(df))
```

**2. Query Builder UI:**
```python
# Frontend sends filter config
user_request = {
    "filters": [
        {"field": "age", "op": ">", "value": 25},
        {"field": "country", "op": "in", "value": ["US", "CA"]}
    ],
    "combine": "and"
}

# Backend parses safely
expr = parse_user_filter(user_request)  # Validates input!
result = df.filter(expr.compile(df))
```

**3. A/B Test Expression Variants:**
```python
# Define variants
variants = {
    "control": col("score").gt(50),
    "treatment_a": col("score").gt(45),
    "treatment_b": col("score").gt(55),
}

# Log which variant is used
variant = get_user_variant(user_id)
expr = variants[variant]

# Telemetry knows exactly what expression ran
log_expression_used(user_id, variant, expr.fingerprint())
result = df.filter(expr.compile(df))
```

**4. Expression Diff:**
```python
# Compare two versions of a business rule
old_rule = load_rule("fraud_v1")
new_rule = load_rule("fraud_v2")

diff = compare_expressions(old_rule, new_rule)
print(diff)
# Changes:
# - threshold: risk_score > 0.7 → risk_score > 0.8
# + added: amount > 10000
# ~ modified: country IN ['US'] → country IN ['US', 'CA']
```

---

## Conference Submission Notes

### Target Conferences

- **PyCon US/EU** - General Python audience, architecture patterns
- **PyData** - Data practitioners building tools
- **EuroPython** - Broad technical audience
- **PyCon AU** - Technical depth appreciated
- **Python Web Conf** - API/rules engine angle

### Talk Format

- **Preferred:** 35-40 minutes (full architecture)
- **Condensed:** 25 minutes (skip visitor/protocol details)
- **Lightning:** 5 minutes (problem + "expressions as data" solution)

### Why This Talk?

1. **Novel pattern** - Not widely discussed in Python community
2. **Practical applications** - Rules engines, query builders, DSLs
3. **Live coding potential** - Build an AST, serialize it, compile it
4. **Transferable knowledge** - Pattern applies beyond DataFrames
5. **Architecture depth** - Visitor, Protocol, Builder patterns

### Speaker Bio Elements

- Building cross-backend DataFrame tooling
- Interest in language design and DSLs
- Experience with expression serialization in production

---

## Lightning Talk Version (5 min)

### Slide 1: The Problem
```python
expr = pl.col("age") > 30
json.dumps(expr)  # TypeError!
```

You can't serialize a Polars expression.

### Slide 2: The Solution
```python
# Don't execute. Describe.
expr = col("age").gt(30)  # → AST node

# Now you can:
expr.to_json()       # Serialize
expr.fingerprint()   # Hash
expr.compile(df)     # Execute later
```

### Slide 3: What's an AST?
```json
{
  "type": "comparison",
  "operator": "gt",
  "left": {"type": "column", "name": "age"},
  "right": {"type": "literal", "value": 30}
}
```

It's just data. You can read it, write it, transform it.

### Slide 4: What This Unlocks
- Serialization (save rules to database)
- Inspection (find all referenced columns)
- Transformation (optimize before compile)
- Backend independence (Polars, Ibis, Pandas)

### Slide 5: The Pattern
```
User API → AST (data) → Visitor → Backend Expression
```

Build the tree. Compile when ready. Execute when needed.

"Sometimes the best thing an expression can do is nothing—until you tell it to."
