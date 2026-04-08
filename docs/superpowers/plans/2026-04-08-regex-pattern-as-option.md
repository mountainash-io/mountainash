# Regex Pattern as Option Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the `pattern` parameter of `regex_contains` and `regex_match` from a visited *argument* to a literal *option* per `arguments-vs-options.md` (ENFORCED), eliminating 26 cross-backend test failures on `narwhals-polars` and `pandas`.

**Architecture:** Six-layer wiring fix (api_builder + protocols + 3 backends + function mapping). The API builder gains build-time `TypeError` validation that `pattern` is a literal `str`. The pattern is stored on `ScalarFunctionNode.options["pattern"]`, never as an argument node, so the visitor never tries to compile it into a backend `Expr`. Backends read the pattern as a keyword-only `str` argument supplied by the visitor's options-as-kwargs dispatch.

**Tech Stack:** Python 3.10+, Polars, narwhals, Ibis, pytest, hatch.

**Spec:** `docs/superpowers/specs/2026-04-08-regex-pattern-as-option-design.md`

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `tests/expressions/test_regex_pattern_validation.py` | Build-time validation tests (no DataFrame needed) | Create |
| `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py` | API builder — `regex_contains` / `regex_match` methods | Modify (validation + node shape) |
| `src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_string.py` | API builder protocol | Modify (signature → `str`) |
| `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_string.py` | ExpressionSystem protocol | Modify (`pattern` → kw-only `str`) |
| `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_string.py` | Polars backend | Modify signature |
| `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_string.py` | Narwhals backend (the actually-broken one) | Modify signature |
| `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_string.py` | Ibis backend | Modify signature |
| `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py` | Function-mapping registry — `REGEX_CONTAINS` row | Modify (declare `pattern` as option) |
| `src/mountainash/expressions/backends/expression_systems/narwhals/base.py` | KNOWN_EXPR_LIMITATIONS registry | Modify (add `REGEX_CONTAINS.pattern` entry) |

---

## Task 1: Failing build-time validation tests (TDD red)

**Files:**
- Create: `tests/expressions/test_regex_pattern_validation.py`

- [ ] **Step 1: Create the test file**

```python
"""Build-time validation tests for regex_contains / regex_match.

Per arguments-vs-options.md (ENFORCED), the regex pattern is a
universally-literal parameter and MUST be passed as a literal `str`.
The API builder rejects non-string inputs at build time with a clear
TypeError pointing at the Relation.compile() escape hatch for
dynamic-pattern use cases.
"""
from __future__ import annotations

import pytest

import mountainash as ma


def test_regex_contains_rejects_expression_pattern():
    """Passing a column reference as the pattern raises TypeError."""
    with pytest.raises(TypeError) as excinfo:
        ma.col("name").str.regex_contains(ma.col("regex_col"))

    msg = str(excinfo.value)
    assert "literal str" in msg
    assert "compile()" in msg


def test_regex_contains_rejects_lit_wrapped_pattern():
    """Even ma.lit(\"foo\") wrapping a literal must be rejected.

    The strict semantics: pattern is `str` only, full stop. Wrapping
    a literal in an expression node loses the build-time type check
    and is therefore disallowed.
    """
    with pytest.raises(TypeError) as excinfo:
        ma.col("name").str.regex_contains(ma.lit("foo"))

    msg = str(excinfo.value)
    assert "literal str" in msg


def test_regex_match_rejects_expression_pattern():
    """regex_match delegates to regex_contains; the same TypeError flows through."""
    with pytest.raises(TypeError) as excinfo:
        ma.col("name").str.regex_match(ma.col("regex_col"))

    msg = str(excinfo.value)
    assert "literal str" in msg
```

- [ ] **Step 2: Run the tests and confirm they FAIL**

Run: `hatch run test:test-target-quick tests/expressions/test_regex_pattern_validation.py`

Expected: 3 FAIL. The current `regex_contains` accepts any input via `_to_substrait_node`, so passing `ma.col(...)` or `ma.lit(...)` does NOT raise — the test expectation `pytest.raises(TypeError)` fails. If any test instead PASSES, stop and report — that means validation already exists and the assumption is wrong.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/expressions/test_regex_pattern_validation.py
git commit -m "test(expressions): regex pattern build-time validation (red)"
```

---

## Task 2: Fix API builder + protocol — pattern as option

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py:1062-1095` (`regex_match`, `regex_contains`)
- Modify: `src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_string.py:429-433` (protocol signatures)

- [ ] **Step 1: Replace `regex_match` and `regex_contains` in the API builder**

In `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py`, find these two methods (currently at lines 1062 and 1074):

```python
    def regex_match(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Check if entire string matches regex pattern (anchored with ^ and $)."""
        if isinstance(pattern, str):
            anchored_pattern = f"^{pattern}$"
        else:
            anchored_pattern = pattern
        return self.regex_contains(anchored_pattern, case_sensitive=case_sensitive)

    def regex_contains(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Check if string contains a match for a regex pattern.

        Routes through the mountainash extension REGEX_CONTAINS function key.
        Substrait has no regexp_contains primitive — its CONTAINS is literal —
        so each backend implements regex_contains natively (polars str.contains
        with literal=False, ibis re_search, narwhals str.contains).
        """
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_STRING,
        )
        pattern_node = self._to_substrait_node(pattern)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS,
            arguments=[self._node, pattern_node],
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)
```

Replace them with:

```python
    def regex_match(
        self,
        pattern: str,
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Check if entire string matches regex pattern (anchored with ^ and $).

        Args:
            pattern: Regex pattern. Must be a literal ``str``. See
                :meth:`regex_contains` for the rationale and the escape
                hatch for dynamic patterns.
            case_sensitive: Whether matching is case-sensitive (default True).
        """
        if not isinstance(pattern, str):
            raise TypeError(
                f"regex_match pattern must be a literal str, "
                f"got {type(pattern).__name__}. For dynamic patterns, use "
                f"rel.compile() to drop into the native backend."
            )
        return self.regex_contains(f"^{pattern}$", case_sensitive=case_sensitive)

    def regex_contains(
        self,
        pattern: str,
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Check if string contains a match for a regex pattern.

        Routes through the mountainash extension REGEX_CONTAINS function key.
        Substrait has no regexp_contains primitive — its CONTAINS is literal —
        so each backend implements regex_contains natively (polars str.contains
        with literal=False, ibis re_search, narwhals str.contains).

        Args:
            pattern: Regex pattern. Must be a literal ``str``. Mountainash
                does not support dynamic regex patterns drawn from another
                column or computed at runtime — every supported backend
                requires the pattern as a literal at compile time.

                For dynamic patterns, use ``rel.compile()`` to drop into
                the native backend (Polars, Ibis, narwhals) and apply that
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

- [ ] **Step 2: Update the API builder protocol signatures**

In `src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_string.py`, find lines 429 and 433:

```python
    def regex_contains(self, pattern: Union[BaseExpressionAPI, ExpressionNode, Any], *, case_sensitive: bool = True) -> BaseExpressionAPI:
        ...

    def regex_match(self, pattern: Union[BaseExpressionAPI, ExpressionNode, Any], *, case_sensitive: bool = True) -> BaseExpressionAPI:
        ...
```

Replace with:

```python
    def regex_contains(self, pattern: str, *, case_sensitive: bool = True) -> BaseExpressionAPI:
        ...

    def regex_match(self, pattern: str, *, case_sensitive: bool = True) -> BaseExpressionAPI:
        ...
```

- [ ] **Step 3: Run the validation tests — must now PASS**

Run: `hatch run test:test-target-quick tests/expressions/test_regex_pattern_validation.py`

Expected: 3 PASS.

- [ ] **Step 4: Run the previously-failing cross-backend regex tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_pattern.py tests/cross_backend/test_compose_string_extended.py tests/cross_backend/string/test_regex_contains_refactor.py`

Expected outcome: most or all of the 26 previously-failing tests now pass. Note: under the new node shape, the visitor passes `pattern` as a kwarg drawn from `options`, and the existing backend signatures (`def regex_contains(self, input, /, pattern, case_sensitivity)`) accept it as a positional-or-keyword param — so the runtime path may already work end-to-end after only this task. If any tests still fail, **read the failure carefully** before proceeding to Task 3 — Task 3 is purely a type-cleanup task and should not change behavior. A failure here means something is wrong upstream (visitor dispatch, function-mapping declaration) and Task 3 won't fix it.

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_string.py
git commit -m "fix(expressions): regex pattern is a literal option, not an argument

Per arguments-vs-options.md, the regex pattern for regex_contains and
regex_match is a universally-literal parameter and MUST be an option.
Storing it as a visited argument caused TypeError: unhashable type:
'Expr' on narwhals over pandas/polars, where narwhals' str.contains
calls Python re.compile() on the visited Expr object directly.

The API builder now validates pattern is a literal str at build time
and raises TypeError pointing at the Relation.compile() escape hatch
for dynamic-pattern use cases."
```

---

## Task 3: Align ExpressionSystem protocol + backend signatures (type cleanup)

**Files:**
- Modify: `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_string.py:23-46`
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_string.py:22-34`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_string.py:22-33`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_string.py:18-29`

- [ ] **Step 1: Update the ExpressionSystem protocol**

In `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_string.py`, replace the `regex_contains` method (currently at line 23):

```python
    def regex_contains(
        self,
        input: ExpressionT,
        /,
        pattern: ExpressionT,
        case_sensitivity: Optional[str] = None,
    ) -> ExpressionT:
        """Check if string contains a match for a regex pattern.

        Mountainash extension — Substrait has no regexp_contains primitive.
        Backends should implement this natively (e.g. polars str.contains
        with literal=False, ibis re_search) so null propagation is correct
        and on-match returns boolean directly.

        Args:
            input: String expression.
            pattern: Regex pattern (string or expression).
            case_sensitivity: "CASE_SENSITIVE" or "CASE_INSENSITIVE".

        Returns:
            Boolean expression — True on match, False on no-match,
            null when input is null (backend-dependent for narwhals).
        """
        ...
```

with:

```python
    def regex_contains(
        self,
        input: ExpressionT,
        /,
        *,
        pattern: str,
        case_sensitivity: Optional[str] = None,
    ) -> ExpressionT:
        """Check if string contains a match for a regex pattern.

        Mountainash extension — Substrait has no regexp_contains primitive.
        Backends should implement this natively (e.g. polars str.contains
        with literal=False, ibis re_search) so null propagation is correct
        and on-match returns boolean directly.

        Args:
            input: String expression.
            pattern: Regex pattern as a literal ``str`` (kw-only, never an
                expression — see arguments-vs-options.md).
            case_sensitivity: "CASE_SENSITIVE" or "CASE_INSENSITIVE".

        Returns:
            Boolean expression — True on match, False on no-match,
            null when input is null (backend-dependent for narwhals).
        """
        ...
```

- [ ] **Step 2: Update the Polars backend**

In `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_string.py`, replace the `regex_contains` method:

```python
    def regex_contains(
        self,
        input: PolarsExpr,
        /,
        pattern: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Regex containment via Polars str.contains(literal=False).

        Polars str.contains propagates null on null input, returning a
        true boolean (no extract/null-mismatch hack needed).
        """
        return input.str.contains(pattern, literal=False)
```

with:

```python
    def regex_contains(
        self,
        input: PolarsExpr,
        /,
        *,
        pattern: str,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Regex containment via Polars str.contains(literal=False).

        Polars str.contains propagates null on null input, returning a
        true boolean (no extract/null-mismatch hack needed).
        """
        return input.str.contains(pattern, literal=False)
```

- [ ] **Step 3: Update the Narwhals backend**

In `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_string.py`, replace the `regex_contains` method:

```python
    def regex_contains(
        self,
        input: NarwhalsExpr,
        /,
        pattern: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Regex containment via Narwhals str.contains (regex by default).

        Note: narwhals/pandas may return False (not None) for null input.
        """
        return input.str.contains(pattern)
```

with:

```python
    def regex_contains(
        self,
        input: NarwhalsExpr,
        /,
        *,
        pattern: str,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Regex containment via Narwhals str.contains (regex by default).

        Note: narwhals/pandas may return False (not None) for null input.
        """
        return input.str.contains(pattern)
```

- [ ] **Step 4: Update the Ibis backend**

In `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_string.py`, replace the `regex_contains` method:

```python
    def regex_contains(
        self,
        input,
        /,
        pattern,
        case_sensitivity: Any = None,
    ):
        """Regex containment via Ibis re_search.

        re_search returns a true boolean and propagates null on null input.
        """
        return input.re_search(pattern)
```

with:

```python
    def regex_contains(
        self,
        input,
        /,
        *,
        pattern: str,
        case_sensitivity: Any = None,
    ):
        """Regex containment via Ibis re_search.

        re_search returns a true boolean and propagates null on null input.
        """
        return input.re_search(pattern)
```

- [ ] **Step 5: Run the regex test suite again — must still pass**

Run: `hatch run test:test-target-quick tests/cross_backend/test_pattern.py tests/cross_backend/test_compose_string_extended.py tests/cross_backend/string/test_regex_contains_refactor.py tests/expressions/test_regex_pattern_validation.py`

Expected: all green. This task is type-cleanup only — no behavior change. If anything regresses, the kw-only marker (`*,`) is incompatible with how the visitor passes options; investigate before proceeding.

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_string.py src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_string.py src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_string.py src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_string.py
git commit -m "refactor(expressions): regex_contains pattern is kw-only str on all backends

Type-cleanup follow-up to the API-builder fix. Aligns the
ExpressionSystem protocol and the three backend implementations
(Polars, narwhals, Ibis) with the new contract: pattern is a
literal str passed as a keyword option, not a backend Expr."
```

---

## Task 4: Function-mapping definitions + KNOWN_EXPR_LIMITATIONS

**Files:**
- Modify: `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py:675-680` (REGEX_CONTAINS row)
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/base.py:42` (KNOWN_EXPR_LIMITATIONS dict)

- [ ] **Step 1: Inspect the REGEX_CONTAINS function definition**

Read `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py` lines 668–681. The current row is:

```python
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS,
            substrait_uri=MountainashExtension.STRING,
            substrait_name="regex_contains",
            protocol_method=MountainAshScalarStringExpressionSystemProtocol.regex_contains,
        ),
```

Check the surrounding rows (e.g. STARTS_WITH, CONTAINS) for any field that declares "options" or "literal-only params". Look for keys like `option_names`, `literal_options`, `kwargs`, etc. on `ExpressionFunctionDef`.

If `ExpressionFunctionDef` has no field for declaring option names (i.e. all rows look identical to REGEX_CONTAINS, with just `function_key`/`uri`/`name`/`protocol_method`), then **no edit is needed for this file** — the visitor's options-as-kwargs dispatch reads `node.options` directly off the AST node, and the function-mapping registry only declares the protocol method. Skip to Step 2.

If there IS such a field, add the appropriate declaration so the visitor knows `pattern` is a literal option for `REGEX_CONTAINS`.

Document the finding in your commit message either way.

- [ ] **Step 2: Add the KNOWN_EXPR_LIMITATIONS entry to the narwhals base**

In `src/mountainash/expressions/backends/expression_systems/narwhals/base.py`, the `KNOWN_EXPR_LIMITATIONS` dict starts at line 42. Find the existing string entries (e.g. `(FK_STR.CONTAINS, "substring"): _NW_STRING_LITERAL_ONLY,`).

Just below `(FK_STR.LIKE, "match"): _NW_STRING_LITERAL_ONLY,`, add:

```python
        # Mountainash extension — regex_contains pattern is literal-only
        # on every backend (per arguments-vs-options.md). Defensive entry:
        # the API builder rejects non-str patterns at build time, so this
        # lookup should never actually fire — but if a future caller routes
        # around the builder this surfaces an enriched error instead of the
        # raw `TypeError: unhashable type: 'Expr'` from re.compile.
        (FK_MA_STR.REGEX_CONTAINS, "pattern"): _NW_STRING_LITERAL_ONLY,
```

You'll need to confirm the import alias `FK_MA_STR` exists in this file. Read the top of `narwhals/base.py` (lines 1–30):
- If there's an import like `from ...function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING as FK_MA_STR`, use that alias.
- If there's no import for the MA string enum, add one near the existing `FK_STR`/`FK_DT` imports:

  ```python
  from mountainash.expressions.core.expression_system.function_keys.enums import (
      FKEY_MOUNTAINASH_SCALAR_STRING as FK_MA_STR,
  )
  ```

- [ ] **Step 3: Run the regex test suite once more**

Run: `hatch run test:test-target-quick tests/cross_backend/test_pattern.py tests/cross_backend/test_compose_string_extended.py tests/cross_backend/string/test_regex_contains_refactor.py tests/expressions/test_regex_pattern_validation.py`

Expected: all green. No behavior change from this task — just registry hygiene.

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/narwhals/base.py
# Also add definitions.py if Step 1 required an edit
git commit -m "chore(expressions): document regex_contains pattern as literal-only

Add a defensive KNOWN_EXPR_LIMITATIONS entry for the narwhals backend
so future code paths that route around the API builder surface an
enriched error instead of TypeError: unhashable type: 'Expr'."
```

---

## Task 5: Final verification

**Files:** none

- [ ] **Step 1: Run the full test suite**

Run: `hatch run test:test-quick`

Expected: the 26 previously-failing tests are green. The full suite should be green or — at worst — the same set of pre-existing unrelated failures we already know about (none, in this branch's HEAD before this work). Compare against the baseline you have from earlier in the session: 4849 passed, 26 failed (the regex bug). After this plan: ≥4878 passed, 0 failed. New tests: 3 (validation file).

- [ ] **Step 2: Run pyright on the touched files**

Open the touched files in the editor and check the LSP diagnostics, or rely on `hatch run mypy:check` if it's quick. The kw-only `*,` marker on backend methods may produce new pyright complaints if the visitor's options-dispatch path isn't typed precisely — investigate any new errors before declaring done.

- [ ] **Step 3: Summarise the result**

If the suite is fully green, the implementation is complete. Report back with:
- Test counts before / after
- The 26 originally-failing tests now passing
- Any unexpected regressions
