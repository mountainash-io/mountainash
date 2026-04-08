# `t_is_in` / `t_is_not_in` — Accept List-Typed Column Argument

**Date:** 2026-04-08
**Status:** Approved
**Issue:** mountainash-expressions#75
**Related principles:**
- `f.extension-model/arguments-vs-options.md` (ENFORCED)
- `e.cross-backend/known-divergences.md` (ADOPTED)
- `d.ternary-logic/three-valued-semantics.md` (ENFORCED)
- `d.ternary-logic/sentinel-values.md` (ADOPTED)

## Problem

`ma.t_col("ctx").t_is_in(ma.col("rule_list"))` — where `rule_list` is a list-typed column — raises `TypeError: not yet implemented: Nested object types` on Polars. The API builder wraps the single expression argument in a `LIST(...)` node as if the expression were a literal, producing a nested-list shape the backend visitors can't compile.

The downstream rules engine (`mountainash-utils-rules`) needs per-row set membership for its `SET_MEMBERSHIP` / `SET_EXCLUSION` strategies and today escapes to `ma.native(pl.col(rule_field).list.contains(pl.col(ctx_field)))` — the only Polars-specific code path in an otherwise backend-agnostic engine.

### Naming clarification

Earlier framing proposed `t_list_contains` on the scalar receiver, which conflates two mental models:

- `scalar.is_in(collection)` — receiver is the element
- `collection.contains(scalar)` — receiver is the collection

The downstream use case ("is this scalar in that row's allowed-list?") is `is_in` from the scalar's POV regardless of whether the collection is a literal or a list-typed column. Fixing `t_is_in` to accept both shapes gives one mental model and no new API surface.

## Design

### Polymorphic `t_is_in` / `t_is_not_in`

Dispatch at **visit time**, not build time. The API builder AST stays schema-free; each backend's `T_IS_IN` handler inspects the compiled second argument at visit time and branches on dtype.

The three-layer separation principle forbids leaking argument dtypes into the build layer — the AST doesn't know column types until a backend is bound. Backend-layer dispatch is ~5 lines of mechanical branching per backend and has no cross-layer leakage.

### Layer 1 — API builder (minimal change)

`src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_ternary.py`, `t_is_in` (~L191) and `t_is_not_in` (~L213).

Today:

```python
if isinstance(values, (list, tuple, set)):
    value_nodes = [LiteralNode(value=v) for v in values]
else:
    value_nodes = [self._to_substrait_node(values)]

node = ScalarFunctionNode(
    function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_IN,
    arguments=[self._node, ScalarFunctionNode(
        function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.LIST,
        arguments=value_nodes,
    )],
    options=options,
)
```

New:

```python
if isinstance(values, (list, tuple, set)):
    # Literal path — wrap in LIST node as today.
    collection_arg = ScalarFunctionNode(
        function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.LIST,
        arguments=[LiteralNode(value=v) for v in values],
    )
else:
    # Expression path — pass through raw. Backend decides at visit time
    # whether this is a scalar expression (today's behaviour) or a
    # list-typed column (new behaviour).
    collection_arg = self._to_substrait_node(values)

node = ScalarFunctionNode(
    function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_IN,
    arguments=[self._node, collection_arg],
    options=options,
)
```

The second argument shape is now one of:
- `ScalarFunctionNode(key=LIST, arguments=[LiteralNode, ...])` — literal path
- Any other compiled expression — expression path (scalar or list column)

The `LIST` wrapper stays as the unambiguous marker for the literal path; backends that see it know they're in the literal branch without any dtype introspection.

### Layer 2 — Backend visitors

Each backend's `T_IS_IN` handler already unwraps the `LIST` node. The change: when the second argument is **not** a `LIST` node, inspect the compiled expression's dtype and branch.

**Polars** (`expsys_pl_ext_ma_scalar_ternary.py`):

```python
def t_is_in(self, input, values, /, *, unknown_values=None):
    if _is_list_node(values):
        literals = _unwrap_list_literals(values)
        bool_result = input.is_in(literals)
    else:
        compiled = self._visit(values)
        if _is_list_dtype(compiled):
            bool_result = compiled.list.contains(input)
        else:
            bool_result = input.is_in(compiled)
    return _booleanize_to_ternary(input, bool_result, unknown_values)
```

`_is_list_dtype` uses Polars' `.dtype` on a sampled schema (the visitor already has the schema in hand via the relation plan). If dtype is `pl.List(_)` or `pl.Array(_)`, take the list branch.

**Ibis** (`expsys_ib_ext_ma_scalar_ternary.py`):

Same shape. Branch on `compiled.type().is_array()`. List branch calls `compiled.contains(input)`. Ibis handles nulls via its own tri-state; map to ternary via the existing helper.

**Narwhals** (`expsys_nw_ext_ma_scalar_ternary.py`):

Same shape. Branch via `compiled.dtype` introspection. Narwhals-polars: `compiled.list.contains(input)` works. Narwhals-pandas: narwhals' list namespace is thin; if the operation is unsupported for the active native backend, the existing `KNOWN_EXPR_LIMITATIONS` registry enriches the error at execution time. No special-casing in the visitor.

### Layer 3 — `KNOWN_EXPR_LIMITATIONS`

`src/mountainash/expressions/backends/expression_systems/narwhals/base.py`:

```python
_NW_LIST_CONTAINS_LIMITED = KnownLimitation(
    message=(
        "Narwhals does not support list-column membership on all native "
        "backends (narwhals-pandas in particular). Use polars or ibis, "
        "or pass a literal list as the argument."
    ),
    spec_ref="e.cross-backend/known-divergences.md",
    workaround="Use a literal list, the polars backend, or an ibis backend",
)

KNOWN_EXPR_LIMITATIONS: dict[tuple[Any, str], KnownLimitation] = {
    ...
    (FK_MA_TERN.T_IS_IN,     "values"): _NW_LIST_CONTAINS_LIMITED,
    (FK_MA_TERN.T_IS_NOT_IN, "values"): _NW_LIST_CONTAINS_LIMITED,
}
```

This keys on the `values` argument slot. When a narwhals-pandas execution fails because of the unsupported list op, the registry enriches the raw `AttributeError` / `NotImplementedError` with the spec-linked guidance.

### Null & sentinel semantics

| Input | Result |
|---|---|
| Scalar ∈ `unknown_values` sentinel | ternary UNKNOWN (0) |
| List-column row is null | ternary UNKNOWN (0) |
| Scalar matches an element in the list | `t_is_in` → TRUE (1); `t_is_not_in` → FALSE (-1) |
| Scalar matches no element in the list | `t_is_in` → FALSE (-1); `t_is_not_in` → TRUE (1) |
| Non-null list contains null elements | Nulls ignored — treated as "not a match" (Polars default) |
| Scalar is null but not in `unknown_values` | ternary UNKNOWN (0) — preserves today's scalar behaviour |

Null-row → UNKNOWN is new but consistent with the existing ternary principle: unknown input ⇒ unknown output.

## Tests

New cross-backend parametrised tests in `tests/cross_backend/test_ternary_is_in_list_column.py`:

1. **Literal list regression** — `t_is_in([1,2,3])` still works on every backend. Pin today's behaviour.
2. **List-column happy path** — `t_col("x").t_is_in(col("allowed_list"))` with mixed matches/misses, verified row-by-row across `polars`, `ibis-duckdb`, `ibis-sqlite`, `ibis-polars`, `narwhals-polars`.
3. **Null row in list column** — row where `allowed_list` is null → ternary UNKNOWN.
4. **Sentinel scalar** — `t_col("x", unknown={"<NA>"})` with `x == "<NA>"` → ternary UNKNOWN regardless of list contents.
5. **`t_is_not_in` mirror** for 2–4.
6. **Nulls inside the list** — `allowed_list = [1, None, 3]`, scalar `= 2` → FALSE; scalar `= None` → UNKNOWN.
7. **narwhals-pandas enriched error** — `xfail(strict=True)` on the list-column case; the test also invokes the expression directly and asserts the error message contains the `KNOWN_EXPR_LIMITATIONS` guidance.

Plus one smoke test in `tests/cross_backend/test_ternary_is_in_list_column.py::test_rules_engine_shape` mirroring the downstream rules-engine use case verbatim (context column `ctx` vs rule column `rule_list`).

## Non-goals

- No `.list` namespace on the non-ternary API. YAGNI until a broader list-ops batch is needed.
- No narwhals-pandas list-op implementation. Upstream narwhals concern.
- No new function keys (`T_IS_IN` / `T_IS_NOT_IN` keep their current identity).
- No change to the literal-list code path on any backend.
- No build-time dtype introspection. The AST stays schema-free per three-layer separation.
- Downstream `mountainash-utils-rules` cleanup happens in a follow-up PR in that repo.

## Downstream implication when this lands

`mountainash-utils-rules/src/mountainash_utils_rules/compiler.py` drops the `ma.native(pl.col(...).list.contains(...))` workarounds in `_compile_set_membership` and `_compile_set_exclusion`, replacing them with `ctx_col.t_is_in(ma.col(rule_field))` / `ctx_col.t_is_not_in(...)`. The `import polars as pl  # allow: SET_MEMBERSHIP workaround pending upstream` line disappears. Strict xfails in `tests/test_compiler.py::TestBackendAgnosticism::test_set_strategy_compiles_on_backend` and `tests/test_integration.py::TestMixedStrategyFraudDetection` on non-polars `LIST_CAPABLE_BACKENDS` flip XPASS and the markers are removed in the same downstream PR. The rules engine's `01.principles/mountainash-utils-rules/c.identity-and-representation/representation-fits-host-language.md` drops its "Future Considerations" exception.

## Risk

Low. The breaking-change surface is "callers who passed a single expression to `t_is_in` expecting it to be treated as a scalar-in-a-one-element-list" — semantically nonsensical and not exercised by any test in the current suite (which is how the nested-object bug went unnoticed). The change makes a previously-broken shape work; the scalar-expression-in-literal-list path is unchanged.
