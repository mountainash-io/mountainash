# Expressions

mountainash expressions are backend-agnostic column-level computations. You write them once; they compile to native Polars, Ibis, or Narwhals expressions at the call site.

## The model

An expression is a tree built up by method calls and operator overloading. The leaves are column references (`ma.col("name")`), literals (`ma.lit(42)`), or native expressions (`ma.native(pl.col("x"))`). The interior nodes are function applications: arithmetic, comparisons, string ops, datetime ops, conditionals, aggregations, window functions.

The tree is data. You can inspect it, walk it, serialise it. It does not execute until you ask it to.

```python
import mountainash as ma

expr = (ma.col("price") * ma.col("qty")).alias("revenue")
```

At this point nothing has happened. `expr` is a Python object holding a small tree:

```
AliasNode("revenue")
└─ ScalarFunctionNode(MULTIPLY)
   ├─ FieldReferenceNode("price")
   └─ FieldReferenceNode("qty")
```

To get a result, you compile against a frame:

```python
df = pl.DataFrame({"price": [10.0, 20.0], "qty": [3, 4]})
df.with_columns(expr.compile(df))
```

`compile()` detects the backend (Polars here) and produces a native `pl.Expr`. You hand that to Polars and it does the work.

## What's in the API

The surface mirrors Polars conventions. If you can write something in Polars, you can usually write it in mountainash by replacing `pl.col(...)` with `ma.col(...)`.

| Category | Examples |
|----------|----------|
| Columns / literals | `ma.col("x")`, `ma.lit(42)`, `ma.lit("hello")`, `ma.duration(days=7)`, `ma.native(pl.col("x"))` |
| Arithmetic | `+ - * / // %`, `ma.col("x").pow(2)`, `.sqrt()`, `.abs()`, `.log()`, `.exp()` |
| Comparisons | `.eq() .ne() .gt() .ge() .lt() .le()`, operator overloads `==`, `!=`, `>`, etc. |
| Boolean | `.and_() .or_() .not_() .xor()`, `ma.all_horizontal(...)`, `ma.any_horizontal(...)` |
| Conditional | `ma.when(cond).then(a).otherwise(b)` |
| Coalesce / extremes | `ma.coalesce(...)`, `ma.greatest(...)`, `ma.least(...)` |
| String namespace | `ma.col("name").str.lower().strip().slice(0, 5)` |
| Datetime namespace | `ma.col("t").dt.year()`, `.weekday()`, `.truncate("1d")` |
| List namespace | `ma.col("tags").list.contains("x")`, `.list.unique()`, `.list.sum()` |
| Struct namespace | `ma.col("addr").struct.field("city")` |
| Aggregates | `.sum() .mean() .min() .max() .median() .quantile() .std() .var() .n_unique()` |
| Window functions | `.over("group").rank()`, `.over("group").sum()`, `lag/lead/cum_*` |
| Name namespace | `.name.prefix("p_")`, `.name.suffix("_v2")`, `.name.to_lowercase()` |
| Ternary logic | `ma.t_col(...)`, `ma.always_true()`, `ma.always_unknown()` — see [ternary logic](ternary-logic.md) |

The full surface re-exports at the top level: `from mountainash import col, lit, when, coalesce, greatest, ...`.

## How dispatch works

Every operation has a **function key** — a typed enum value like `KEY_SCALAR_STRING.LOWER` or `KEY_AGGREGATE_NUMERIC.SUM`. When you call `expr.compile(df)`, the visitor walks the tree and looks up each function key against the registry. The registry maps the key to a method name; the backend system implements that method.

The keys are aligned with Substrait function categories where possible. Operations that have no Substrait equivalent (e.g. mountainash's ternary logic) live in a separate `MOUNTAINASH_*` enum namespace and a separate set of implementation files. The two never mix.

This means:

- Every backend implements the same surface — verified by introspection tests, not vibes.
- Adding a new operation is a fixed six-step process: add the enum, add the protocol method, add the API builder, implement in every backend, register the function key, write cross-backend tests. See [Adding operations](../../guides/adding-operations.md).
- The AST is small and stable: 7 expression node types, and "operations" are values carried by `ScalarFunctionNode`, `AggregateFunctionNode`, and `WindowFunctionNode`.

## Operator overloading

Standard Python operators map onto named methods:

```python
ma.col("a") + ma.col("b")              # → .add()
ma.col("a") > 5                        # → .gt()
ma.col("a") & ma.col("b")              # → .and_()
~ma.col("a")                           # → .not_()
```

Reversed operators are supported: `5 + ma.col("a")` works.

## Inspecting an expression

Expression trees are Pydantic models. You can serialise them, diff them, transform them programmatically:

```python
expr = ma.col("x").gt(5).and_(ma.col("y").lt(10))
print(expr._node)
# ScalarFunctionNode(function_key=KEY_SCALAR_BOOLEAN.AND, arguments=[...])
```

This is the foundation for later work — see the [vision](../vision.md) page on stored, versioned query plans.

## What you can't (yet) do

- **Direct Substrait emit/consume.** The AST is Substrait-aligned but the wire format isn't there yet. Roadmap item.
- **Custom user-defined functions across backends.** UDFs are inherently backend-specific. You can drop into native expressions (`ma.native(pl.col(...).map_batches(...))`) when you need to, but it pins that branch to that backend.
- **Every operation on every backend.** See [cross-backend execution](cross-backend.md#known-divergences).

## Related

- [Relations](relations.md) — DataFrame-level operations that compose with expressions
- [Cross-backend execution](cross-backend.md) — how dispatch works in practice
- [Ternary logic](ternary-logic.md) — three-valued boolean reasoning
- [Adding operations](../../guides/adding-operations.md) — contributor guide
