# Backend Architecture Deep Dive

How mountainash gets identical results out of three very different libraries — Polars (native Rust expressions over `LazyFrame`), Narwhals (a thin cross-library abstraction over pandas/PyArrow), and Ibis (SQL-backed table expressions) — from a single backend-agnostic AST.

Audience: maintainers, backend implementers, and anyone debugging a cross-backend divergence.

## The three layers

Every expression and every relation flows through the same three layers:

```
┌──────────────────────────────────────────────────────────────────┐
│  1. Public API           ma.col("x").str.lower()                 │
│     (api_builders)       ma.relation(df).filter(...).sort(...)   │
└──────────────────────┬───────────────────────────────────────────┘
                       │ builds nodes
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  2. AST                  ScalarFunctionNode(KEY_SCALAR_STRING    │
│     (nodes)              .LOWER, args=[FieldRef("x")])           │
│                          FilterRelNode(input=…, predicate=…)     │
└──────────────────────┬───────────────────────────────────────────┘
                       │ at terminal op (.compile / .collect)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  3. Backend                                                      │
│     - Backend detection (from the DataFrame's type)              │
│     - Unified visitor walks the tree                             │
│     - For each node, looks up the function key → protocol method │
│     - Dispatches to the concrete backend system's method         │
└──────────────────────────────────────────────────────────────────┘
```

Principle: `a.architecture/three-layer-separation.md`. Each layer has a single responsibility:

- **API builders** know how the user types things.
- **Nodes** know the structure of the operation.
- **Backends** know how to make a specific library do it.

## The AST is minimal by design

There are only **7 expression node types** and **10 relational node types**. Everything else is parameterised through `ScalarFunctionNode` (or `AggregateFunctionNode`, `WindowFunctionNode`) using a `function_key` enum, plus `ExtensionRelNode` with an `operation` enum for non-Substrait relational ops.

This is principle `a.architecture/minimal-ast.md`. You don't add a node type per operation — you add an enum value and a protocol method. See [adding-operations.md](adding-operations.md).

## Protocol contracts

A backend is an implementation of a set of `Protocol` classes. The protocol is the contract — it says "if you implement these methods with these signatures, you are a valid backend." There is no abstract base class, no inheritance — just structural typing.

Files: `src/mountainash/expressions/core/expression_protocols/` and `src/mountainash/relations/core/relation_protocols/`.

Example: `ScalarStringExpressionProtocol[ExpressionT]` — generic over the backend's native expression type.

```python
class ScalarStringExpressionProtocol(Protocol[ExpressionT]):
    def lower(self, arg: ExpressionT, /) -> ExpressionT: ...
    def upper(self, arg: ExpressionT, /) -> ExpressionT: ...
    def length(self, arg: ExpressionT, /) -> ExpressionT: ...
    # …
```

Three things to notice:

1. **Generic over `ExpressionT`.** Polars binds it to `pl.Expr`, Ibis to `ir.Value`, Narwhals to `nw.Expr`. The protocol stays library-agnostic.
2. **Positional `/`-only** args are visited expressions; **keyword-only `*`** args are raw literal options. See principle `e.cross-backend/arguments-vs-options.md`.
3. **No default implementations.** Every backend must implement every method or fail wiring verification.

Principle: `c.api-design/protocol-as-contract.md`.

## Three backends side by side

| Concern | Polars | Narwhals | Ibis |
|---------|--------|----------|------|
| Native frame | `pl.LazyFrame` | `nw.DataFrame` (wraps pandas/PyArrow) | `ir.Table` |
| Native expression | `pl.Expr` | `nw.Expr` | `ir.Value` |
| Execution model | Lazy until `.collect()` | Wraps eager frames; lazy when underlying is lazy | Builds SQL; executes against engine (DuckDB/SQLite/…) |
| Strengths | Speed; expression coverage closest to mountainash's surface | Reach into pandas/PyArrow ecosystems | SQL portability; persistent stores |
| Where it pulls ahead | Reference backend; most ops native | Pandas-shaped data without conversion | Push compute to a real database |
| Where it diverges | Some parameter-width restrictions (literals only on certain args) | Frame-level ops missing (e.g. `unnest`); cumulative-in-`over()` quirks | Type inference gaps; Polars-backend interval limitations |

Tracked divergences live in `docs/known-divergences.md` (94 entries as of last regeneration). See [known-divergences.md](known-divergences.md) for the index doc.

## Backend detection

When you call `ma.relation(df)`, the backend is detected from `df`:

```python
detect_dataframe_backend_type(df) -> CONST_BACKEND
```

Registered via a decorator in `core/factories.py`. The resulting `CONST_BACKEND` enum value routes the visitor to the matching `RelationSystem` and `ExpressionSystem` composition.

For cross-type joins (`relation(polars_df).join(pandas_df, on=…)`), one side is coerced — see principle `e.cross-backend/cross-type-joins.md`. Use `execute_on=` to force a target backend.

Principle: `e.cross-backend/backend-detection.md`.

## The unified visitor

A single visitor class dispatches **every** node type via a function registry. Source: `src/mountainash/expressions/core/unified_visitor/` and `src/mountainash/relations/core/unified_visitor/`.

The dispatch sequence for a scalar function:

1. Visitor sees a `ScalarFunctionNode`.
2. Visitor recursively visits each argument, getting back native expressions.
3. Visitor looks up `node.function_key` in the function-key-to-method map.
4. Visitor finds the protocol method name (e.g. `KEY_SCALAR_STRING.LOWER` → `"lower"`).
5. Visitor calls `expression_system.lower(visited_arg)`.
6. The backend method returns a native expression. Visitor returns it.

```
ScalarFunctionNode(KEY_SCALAR_STRING.LOWER, args=[FieldRef("name")])
                            │
              visitor.visit(node)
                            │
   ┌────────────────────────┴────────────────────────┐
   │ visit args first                                │
   │   FieldRef("name") → pl.col("name")             │
   │ look up KEY_SCALAR_STRING.LOWER → "lower"       │
   │ call expression_system.lower(pl.col("name"))    │
   │ → pl.col("name").str.to_lowercase()             │
   └─────────────────────────────────────────────────┘
```

Principle: `a.architecture/unified-visitor.md`.

### Relation visitor

The relation visitor is the same pattern but for `RelationNode` types. It composes with the expression visitor for embedded expressions (filters, projections, aggregations).

Two extension points (see [extension-points.md](extension-points.md)):

- **`RelationVisitRegistry`** — register a handler for a custom `RelationNode` subclass.
- **`OptimisationRegistry`** — register an AST rewrite that runs before the visitor.

## Function key system

Every operation has an ENUM key, prefixed by category:

| Category | Enum prefix | Example |
|----------|-------------|---------|
| Substrait scalar | `KEY_SCALAR_*` | `KEY_SCALAR_STRING.LOWER` |
| Substrait aggregate | `KEY_AGGREGATE_*` | `KEY_AGGREGATE_NUMERIC.SUM` |
| Substrait window | `KEY_WINDOW_*` | `KEY_WINDOW_RANKING.RANK` |
| Mountainash extension | `MOUNTAINASH_*` | `MOUNTAINASH_TERNARY.AND` |

The enum-to-method map lives in `expressions/core/expression_system/function_keys/`. Each map covers one category.

Principle: `b.type-system/function-key-enums.md`.

## Backend composition

A backend is a class composed via multiple inheritance from all the protocol implementations:

```python
class PolarsExpressionSystem(
    ScalarComparisonPolarsExpressionSystem,
    ScalarBooleanPolarsExpressionSystem,
    ScalarStringPolarsExpressionSystem,
    ScalarDatetimePolarsExpressionSystem,
    AggregateNumericPolarsExpressionSystem,
    WindowRankingPolarsExpressionSystem,
    MountainashTernaryPolarsExpressionSystem,
    # … one mixin per protocol …
):
    pass
```

Each mixin implements one protocol. The structural typing means the visitor can call any method without knowing which mixin provides it — as long as the composition covers every protocol the visitor might dispatch to.

Principle: `f.extension-model/backend-composition.md`.

## Walk-through: `ma.col("x").str.lower()` on Polars vs Ibis

User code:

```python
expr = ma.col("name").str.lower()
```

After build:

```python
ScalarFunctionNode(
    function_key=KEY_SCALAR_STRING.LOWER,
    arguments=[FieldReferenceNode(field="name")],
    options={},
)
```

On Polars (`df.with_columns(expr.compile(df))`):

```
visitor.visit(ScalarFunctionNode(...))
  └─ visit FieldReferenceNode("name") → pl.col("name")
  └─ lookup KEY_SCALAR_STRING.LOWER → "lower"
  └─ PolarsExpressionSystem.lower(pl.col("name"))
     → pl.col("name").str.to_lowercase()
```

On Ibis (`expr.compile(ibis_table)`):

```
visitor.visit(ScalarFunctionNode(...))
  └─ visit FieldReferenceNode("name") → t.name (Ibis Column)
  └─ lookup KEY_SCALAR_STRING.LOWER → "lower"
  └─ IbisExpressionSystem.lower(t.name)
     → t.name.lower()
```

Same AST, same dispatch, different native call.

## Why this matters for correctness

The "same expression must produce the same logical result on all backends" guarantee is principle `e.cross-backend/consistency-guarantees.md`. Mechanically:

- Tests are cross-backend parametrized (`@pytest.mark.parametrize("backend", ["polars", "narwhals", "ibis"])`).
- Known intentional divergences are tracked in `docs/known-divergences.md` and enforced via strict `xfail`.
- Wiring verification (`tests/wiring_verification/`) ensures every enum key has a protocol method and every protocol method has an implementation in every backend.

If you find an unexpected divergence, see the divergence-catalog index ([known-divergences.md](known-divergences.md)).

## File-organisation cheat sheet

| You want to … | Look in |
|---------------|---------|
| Add a scalar function | `expressions/core/expression_api/`, `expression_protocols/`, `expression_system/function_keys/`, `backends/{polars,narwhals,ibis}/scalar/` |
| Add an aggregate | Same dirs, `aggregate/` subfolders |
| Add a window function | Same dirs, `window/` subfolders |
| Add a relation operation (Substrait) | `relations/core/relation_nodes/substrait/`, `relation_protocols/relation_systems/substrait/`, `relations/backends/relation_systems/{polars,narwhals,ibis}/substrait/` |
| Add a relation operation (Mountainash) | Same paths with `extensions_mountainash/` |
| Register a custom node type from outside the package | `RelationVisitRegistry` — see [extension-points.md](extension-points.md) |

## Principles you should read before changing anything here

The principles directory (`mountainash-central/01.principles/mountainash/`) is the source of truth. The relevant ones for backend work:

- `a.architecture/three-layer-separation.md` — the layer split
- `a.architecture/minimal-ast.md` — why we have 7 node types
- `a.architecture/unified-visitor.md` — dispatch
- `b.type-system/function-key-enums.md` — enum-based dispatch
- `c.api-design/protocol-as-contract.md` — protocols define backends
- `c.api-design/expression-type-generics.md` — `ExpressionT` generics
- `e.cross-backend/backend-detection.md` — how routing happens
- `e.cross-backend/consistency-guarantees.md` — the correctness contract
- `e.cross-backend/arguments-vs-options.md` — `/` vs `*` semantics
- `e.cross-backend/known-divergences.md` — when divergences are OK
- `f.extension-model/backend-composition.md` — how backends are composed
- `f.extension-model/substrait-vs-mountainash.md` — physical separation
