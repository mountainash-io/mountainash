# `regex_contains` / `regex_match` — Pattern as Option

**Date:** 2026-04-08
**Status:** Approved
**Related principles:**
- `f.extension-model/arguments-vs-options.md` (ENFORCED)
- `c.api-design/build-then-collect.md` — `compile()` escape hatch

## Problem

`Relation.filter(ma.col("phone").str.regex_match(r"\d{3}-\d{3}-\d{4}"))` raises `TypeError: unhashable type: 'Expr'` on the `narwhals-polars` and `pandas` backends — 26 tests across `tests/cross_backend/test_pattern.py`, `test_compose_string_extended.py`, and `string/test_regex_contains_refactor.py`.

### Root cause

In `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py:1089`, `regex_contains` stores the pattern as an **argument** (a visited expression node):

```python
pattern_node = self._to_substrait_node(pattern)
node = ScalarFunctionNode(
    function_key=FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS,
    arguments=[self._node, pattern_node],   # ← bug
    options={"case_sensitivity": ...},
)
```

This violates `f.extension-model/arguments-vs-options.md` (ENFORCED), which mandates that universally-literal parameters MUST be options.

### Why exactly two backends fail

The visitor compiles the literal pattern into a backend `Expr` (e.g. `pl.lit(r"\d{3}-\d{3}-\d{4}")`). What happens next depends on the backend:

- **Polars** — `pl.col(...).str.contains(pl.lit("..."))` accepts an `Expr` for the pattern. Passes.
- **Ibis** — extracts the literal during compilation. Passes.
- **narwhals over polars / narwhals over pandas** — narwhals' `series_str.contains` (`series_str.py:49`) calls `pandas.Series.str.contains(pat=pattern)`, which calls `re.compile(pattern)`. CPython's `re._compile` does `_cache[type(pattern), pattern, flags]` and chokes on `TypeError: unhashable type: 'Expr'`.

The bug has been latent on Polars+Ibis since the introduction of `regex_contains`; only narwhals' strict regex compilation surfaced it.

## Design

### Strict literal: `pattern: str` only

The API builder accepts `pattern: str` and nothing else. Non-string inputs (including `BaseExpressionAPI`, `LiteralNode`, `ma.lit("foo")`, `ma.col("regex_col")`) raise `TypeError` at build time with a message pointing at the documented escape hatch:

```python
def regex_contains(self, pattern: str, case_sensitive: bool = True) -> BaseExpressionAPI:
    """Check if string contains a match for a regex pattern.

    Args:
        pattern: Regex pattern. Must be a literal ``str``. Mountainash
            does not support dynamic regex patterns drawn from another
            column or computed at runtime — every supported backend
            requires the pattern as a literal at compile time.

            For dynamic patterns, use ``rel.compile()`` to drop into the
            native backend (Polars, Ibis, narwhals) and apply that
            backend's own dynamic-regex API directly.
        case_sensitive: Whether matching is case-sensitive (default True).
    """
    if not isinstance(pattern, str):
        raise TypeError(
            f"regex_contains pattern must be a literal str, "
            f"got {type(pattern).__name__}. For dynamic patterns, use "
            f"rel.compile() to drop into the native backend."
        )
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_STRING,
    )
    node = ScalarFunctionNode(
        function_key=FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS,
        arguments=[self._node],
        options={
            "pattern": pattern,
            "case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE",
        },
    )
    return self._build(node)
```

`regex_match` already delegates to `regex_contains` after anchoring; its only change is narrowing its own `pattern` parameter to `str` and reusing the same `TypeError` (raised inside the inner call).

### Six-layer wiring

| # | Layer | File | Change |
|---|---|---|---|
| 1 | API builder | `core/expression_api/api_builders/substrait/api_bldr_scalar_string.py` | `regex_contains` and `regex_match` take `pattern: str`; build-time `TypeError`; pattern stored as `options["pattern"]`; arguments shrink to `[self._node]`. |
| 2 | API builder protocol | `core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_string.py` | Update `regex_contains` and `regex_match` signatures: `pattern: str`. |
| 3 | Function mapping | `core/expression_system/function_mapping/definitions.py` (REGEX_CONTAINS row, line ~676) | Declare `pattern` as an option, not a positional argument. |
| 4 | ExpressionSystem protocol | `core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_string.py` | `regex_contains` signature: `pattern` becomes keyword-only `str`, not a `BackendExprT`. |
| 5a | Polars backend | `backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_string.py` | `def regex_contains(self, input, /, *, pattern: str, case_sensitivity=None)`. Body: `return input.str.contains(pattern, literal=False)` (case-insensitive prefix `(?i)` handled identically to today). |
| 5b | Narwhals backend | `backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_string.py` | Same signature change. Body: `return input.str.contains(pattern)` (narwhals' default is regex). This is the file that's actually broken today. |
| 5c | Ibis backend | `backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_string.py` | Same signature change. Body: `return input.re_search(pattern)`. |
| 6 | Limitations registry | wherever `KNOWN_EXPR_LIMITATIONS` is defined for the string namespace | Add an entry for `REGEX_CONTAINS.pattern`: literal-only on every backend. Surfaces the enriched error if a future caller tries to pass an expression. |

The visitor's options-vs-arguments dispatcher already passes options to backend methods as keyword arguments (per `arguments-vs-options.md`), so backends declaring `pattern` as a kwarg need no visitor changes.

### Tests

**Bar to clear:** the 26 currently-failing tests (`tests/cross_backend/test_pattern.py`, `test_compose_string_extended.py`, `string/test_regex_contains_refactor.py`) all pass on every backend after the fix, **without any edits to those test files**. That alone proves the fix end-to-end.

**New tests** in `tests/expressions/test_regex_pattern_validation.py`:

1. `test_regex_contains_rejects_expression_pattern` — `ma.col("name").str.regex_contains(ma.col("regex"))` raises `TypeError`, message contains "literal str" and "compile()".
2. `test_regex_contains_rejects_lit_wrapped_pattern` — `ma.col("name").str.regex_contains(ma.lit("foo"))` also raises `TypeError`. Pins the strict semantics — even literal-wrapped values are rejected.
3. `test_regex_match_rejects_expression_pattern` — same as #1 but on `regex_match`, to confirm the validation flows through the delegating method.

These are pure build-time tests; no DataFrame is needed.

### Scope / non-goals

- **Not** touching `contains()` (the literal-substring method at line 464). Same shape, but works on all backends today. YAGNI.
- **Not** unifying or refactoring the `KNOWN_EXPR_LIMITATIONS` machinery — just adding one row.
- **Not** changing the deprecated commented-out methods at lines 1016–1060. They're corpses; leave them.
- **Not** adding `regex_search` or other regex variants.
- **Not** supporting case-insensitive via a flag in the pattern itself — `case_sensitive=False` already works through the existing `case_sensitivity` option.

## Risk

Low. The breaking-change surface is "callers passing a non-`str` pattern to `regex_contains` or `regex_match`." The test suite contains zero such callers (Polars happened to work; the others didn't, so anyone who tried it on pandas/narwhals already had a broken test). External callers using `ma.lit("...")` as a pattern wrapper will need to drop the `ma.lit` — they get a clear `TypeError` at build time with the migration path in the message. No silent behavioral change.
