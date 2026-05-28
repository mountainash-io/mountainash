# Adding Operations

This is the contributor-facing how-to for adding a new scalar/aggregate/window expression or a new relational operation. The architecture principle behind it is `g.development-practices/adding-operations.md` in the principles directory; this guide turns that into a concrete walk-through.

There are two kinds of operations:

1. **Expression operations** — column-level functions (e.g. `col.str.lower()`, `col.cum_sum()`). They live in the `expressions/` package.
2. **Relational operations** — DataFrame-level operations (e.g. `relation.unnest()`, `relation.sample()`). They live in the `relations/` package.

The shape is the same: enum → protocol → API builder → all backends → registration → tests. The files differ.

## Decide: Substrait or Mountainash extension?

| If your op… | Put it in | Prefix |
|-------------|-----------|--------|
| Maps 1:1 to a Substrait scalar/aggregate/window function or a Substrait logical relation | `…/substrait/` | `FKEY_SUBSTRAIT_*`, `prtcl_…_substrait.py`, `reln_…` (no prefix) |
| Is mountainash-specific, ternary-logic-related, or has no Substrait analogue | `…/extensions_mountainash/` | `FKEY_MOUNTAINASH_*`, `prtcl_…_ext_ma_*.py`, `reln_ext_ma_*` |

See principle `f.extension-model/substrait-vs-mountainash.md`. The two trees never mix.

## Expression operations (six steps)

### 1. Add the function key

Add an enum value to the appropriate group in:

`src/mountainash/expressions/core/expression_system/function_keys/enums.py`

```python
class KEY_SCALAR_STRING(Enum):
    LOWER = auto()
    UPPER = auto()
    MY_NEW_OP = auto()    # ← new
```

Substrait-aligned keys go in the `KEY_SCALAR_*`, `KEY_AGGREGATE_*`, `KEY_WINDOW_*` enums. Mountainash extensions go in `MOUNTAINASH_*` enums.

### 2. Add the protocol method

In `src/mountainash/expressions/core/expression_protocols/<file>.py`:

```python
class ScalarStringExpressionProtocol(Protocol[ExpressionT]):
    def lower(self, arg: ExpressionT, /) -> ExpressionT: ...
    def my_new_op(self, arg: ExpressionT, /, *, opt: int) -> ExpressionT: ...   # ← new
```

Follow `arguments-vs-options.md`: positional `/`-only params are visited arguments; `*, kwarg`-only params are raw literal options.

### 3. Add the API builder method

In `src/mountainash/expressions/core/expression_api/<file>.py`:

```python
class StringExpressionAPI(...):
    def my_new_op(self, *, opt: int) -> Expression:
        return Expression(
            ScalarFunctionNode(
                function_key=KEY_SCALAR_STRING.MY_NEW_OP,
                arguments=[self._node],
                options={"opt": opt},
            )
        )
```

This is the user-facing call site. Short aliases live here, never in the protocol.

### 4. Implement in every backend

Three backends: Polars, Narwhals, Ibis.

`src/mountainash/expressions/backends/polars/string/expsys_pl_string.py`:

```python
class PolarsStringExpressionSystem(ScalarStringExpressionProtocol[pl.Expr]):
    def my_new_op(self, arg: pl.Expr, /, *, opt: int) -> pl.Expr:
        return arg.str.some_polars_thing(opt)
```

Repeat for `narwhals/` and `ibis/`. If a backend genuinely cannot support it, raise a clear `NotImplementedError` and record the divergence (see step 6).

### 5. Wire the function key into the registry

`src/mountainash/expressions/core/expression_system/function_keys/<file>.py` maps the enum to the protocol method name:

```python
FUNCTION_KEY_TO_METHOD = {
    KEY_SCALAR_STRING.LOWER: "lower",
    KEY_SCALAR_STRING.MY_NEW_OP: "my_new_op",   # ← new
}
```

The unified visitor uses this map to dispatch.

### 6. Tests

Cross-backend parametrized tests under `tests/expressions/`:

```python
@pytest.mark.parametrize("backend", ["polars", "narwhals", "ibis"])
def test_my_new_op(backend):
    df = _fixture_for(backend)
    out = df.with_columns(ma.col("s").str.my_new_op(opt=2).compile(df).alias("r"))
    assert _values(out, "r") == ["expected", ...]
```

If one backend is intentionally broken, `xfail` it per-backend with a reason — **never** blanket-skip:

```python
@pytest.mark.xfail(
    backend == "narwhals",
    reason="Narwhals does not support X; tracked in known-divergences.md",
    strict=True,
)
```

Then add the entry to `docs/known-divergences.md`.

## Relational operations

The shape mirrors expressions but the file layout is different.

### 1. Add the operation enum

For an extension op, add to `ExtensionRelOperation` in `src/mountainash/core/constants.py`:

```python
class ExtensionRelOperation(Enum):
    DROP_NULLS = auto()
    UNNEST = auto()
    MY_NEW_REL_OP = auto()    # ← new
```

For a new Substrait-aligned relation node, add a new `reln_*.py` under `relations/core/relation_nodes/substrait/` and an entry to `JoinType` / `SetType` / etc. as appropriate.

### 2. Add the API method

`src/mountainash/relations/core/relation_api/relation.py`:

```python
def my_new_rel_op(self, *columns: str, opt: int) -> Relation:
    return Relation(
        ExtensionRelNode(
            input=self._node,
            operation=ExtensionRelOperation.MY_NEW_REL_OP,
            options={"columns": list(columns), "opt": opt},
        )
    )
```

### 3. Add the API protocol method

`src/mountainash/relations/core/relation_protocols/prtcl_relation_api.py`:

```python
class RelationAPIProtocol(Protocol):
    def my_new_rel_op(self, *columns: str, opt: int) -> Self: ...
```

### 4. Add the backend-protocol method

`src/mountainash/relations/core/relation_protocols/relation_systems/extensions_mountainash/prtcl_relsys_ext_ma_util.py`:

```python
def my_new_rel_op(self, relation: Any, /, *, columns: list[str], opt: int) -> Any: ...
```

### 5. Implement in every backend

`src/mountainash/relations/backends/relation_systems/{polars,narwhals,ibis}/extensions_mountainash/relsys_*_ext_ma_util.py`:

```python
def my_new_rel_op(self, relation: pl.LazyFrame, /, *, columns: list[str], opt: int) -> pl.LazyFrame:
    return relation.with_columns(...)
```

### 6. Tests

`tests/relations/cross_backend/extensions_mountainash/test_my_new_rel_op.py` — cross-backend parametrized with terminal result verification (compare against an expected Polars LazyFrame collected to native dicts). Use `xfail` per-backend, never blanket skip.

## Checklist

- [ ] Enum value added
- [ ] Protocol method added
- [ ] API builder method added
- [ ] Polars backend implemented
- [ ] Narwhals backend implemented (or `NotImplementedError` + xfail + divergences entry)
- [ ] Ibis backend implemented (or `NotImplementedError` + xfail + divergences entry)
- [ ] Function key registered (expressions only)
- [ ] Cross-backend test added
- [ ] `docs/known-divergences.md` updated if any backend diverges
- [ ] If touching public API surface: brainstorm spec saved under `mountainash-central` (see CLAUDE.md)

## Verification

After implementing, run the wiring-verification suite — it will fail if you've added an enum but forgotten the protocol method, or a protocol method but no backend implementation:

```bash
hatch run test:test-target tests/wiring_verification/
```

See principle `g.development-practices/closed-by-default-verification.md`.
