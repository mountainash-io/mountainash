# Expression Argument Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove inconsistent `_extract_literal_value` calls from string backends, let expressions pass through to native APIs, and catch + enrich errors from known backend limitations via a registry.

**Architecture:** Three shared core types (`KnownLimitation`, `BackendCapabilityError`, `_call_with_expr_support` base method) plus per-backend limitation registries. Polars and Ibis methods pass expressions through directly. Narwhals methods use `_extract_literal_if_possible` to unwrap literals (since Narwhals rejects even `nw.lit("hello")`) while letting column references pass through to be caught by the error enrichment layer.

**Tech Stack:** Python, pytest, Polars, Ibis, Narwhals

**Spec:** `docs/superpowers/specs/2026-04-06-expression-argument-consistency-design.md`

---

### Task 1: Add `KnownLimitation` and `BackendCapabilityError` to Shared Core

**Files:**
- Modify: `src/mountainash/core/types.py:253` (append after last line)
- Test: `tests/unit/test_known_limitation.py` (create)

- [ ] **Step 1: Write tests for `KnownLimitation` and `BackendCapabilityError`**

Create `tests/unit/test_known_limitation.py`:

```python
"""Unit tests for KnownLimitation and BackendCapabilityError."""

import pytest
from mountainash.core.types import KnownLimitation, BackendCapabilityError


class TestKnownLimitation:
    def test_frozen_dataclass(self):
        lim = KnownLimitation(
            message="test limitation",
            native_errors=(TypeError,),
        )
        assert lim.message == "test limitation"
        assert lim.native_errors == (TypeError,)
        assert lim.upstream_issue is None
        assert lim.workaround is None

    def test_with_all_fields(self):
        lim = KnownLimitation(
            message="test",
            native_errors=(TypeError, ValueError),
            upstream_issue="https://github.com/pola-rs/polars/issues/123",
            workaround="Use a literal value",
        )
        assert lim.upstream_issue == "https://github.com/pola-rs/polars/issues/123"
        assert lim.workaround == "Use a literal value"

    def test_immutable(self):
        lim = KnownLimitation(message="test", native_errors=(TypeError,))
        with pytest.raises(AttributeError):
            lim.message = "changed"


class TestBackendCapabilityError:
    def test_basic_error(self):
        err = BackendCapabilityError(
            "cannot do this",
            backend="polars",
            function_key="CONTAINS",
        )
        assert "[polars]" in str(err)
        assert "cannot do this" in str(err)
        assert err.backend == "polars"
        assert err.function_key == "CONTAINS"
        assert err.limitation is None

    def test_error_with_limitation(self):
        lim = KnownLimitation(
            message="test",
            native_errors=(TypeError,),
            workaround="Use a literal",
            upstream_issue="https://github.com/example/issue/1",
        )
        err = BackendCapabilityError(
            "cannot do this",
            backend="narwhals",
            function_key="STARTS_WITH",
            limitation=lim,
        )
        msg = str(err)
        assert "Workaround: Use a literal" in msg
        assert "Upstream: https://github.com/example/issue/1" in msg

    def test_error_without_workaround(self):
        lim = KnownLimitation(
            message="test",
            native_errors=(TypeError,),
        )
        err = BackendCapabilityError(
            "cannot do this",
            backend="polars",
            function_key="REPLACE",
            limitation=lim,
        )
        msg = str(err)
        assert "Workaround" not in msg
        assert "Upstream" not in msg

    def test_is_exception(self):
        err = BackendCapabilityError(
            "test", backend="polars", function_key="CONTAINS"
        )
        assert isinstance(err, Exception)
        with pytest.raises(BackendCapabilityError):
            raise err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target-quick tests/unit/test_known_limitation.py -v`
Expected: FAIL — `ImportError: cannot import name 'KnownLimitation' from 'mountainash.core.types'`

- [ ] **Step 3: Implement `KnownLimitation` and `BackendCapabilityError`**

Append to `src/mountainash/core/types.py` after line 253:

```python
# ============================================================================
# Backend Capability — Known Limitations
# ============================================================================

from dataclasses import dataclass


@dataclass(frozen=True)
class KnownLimitation:
    """Documents a known backend limitation for expression-typed arguments.

    Consulted only when the backend raises a native error — never gates
    execution. When the upstream library adds support, the error stops
    being raised and this entry becomes dormant.
    """

    message: str
    native_errors: tuple[type[Exception], ...]
    upstream_issue: str | None = None
    workaround: str | None = None


class BackendCapabilityError(Exception):
    """Raised when a backend cannot handle an expression-typed argument.

    Wraps native backend errors with curated context from the known
    limitation registry.
    """

    def __init__(
        self,
        message: str,
        *,
        backend: str,
        function_key: str,
        limitation: KnownLimitation | None = None,
    ) -> None:
        parts = [f"[{backend}] {message}"]
        if limitation:
            if limitation.workaround:
                parts.append(f"Workaround: {limitation.workaround}")
            if limitation.upstream_issue:
                parts.append(f"Upstream: {limitation.upstream_issue}")
        super().__init__("\n".join(parts))
        self.backend = backend
        self.function_key = function_key
        self.limitation = limitation
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `hatch run test:test-target-quick tests/unit/test_known_limitation.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_known_limitation.py src/mountainash/core/types.py
git commit -m "feat: add KnownLimitation and BackendCapabilityError to shared core"
```

---

### Task 2: Add `_call_with_expr_support` and `_extract_literal_if_possible` to Base Classes

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/base.py:40` (append methods)
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/base.py:67` (append methods + registry)
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/base.py:122` (append methods + empty registry)
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/base.py:78` (append methods + registry)
- Test: `tests/unit/test_call_with_expr_support.py` (create)

- [ ] **Step 1: Write tests for `_call_with_expr_support`**

Create `tests/unit/test_call_with_expr_support.py`:

```python
"""Unit tests for _call_with_expr_support error enrichment."""

import pytest
from mountainash.core.types import KnownLimitation, BackendCapabilityError
from mountainash.expressions.backends.expression_systems.polars.base import (
    PolarsBaseExpressionSystem,
)
from mountainash.expressions.backends.expression_systems.ibis.base import (
    IbisBaseExpressionSystem,
)
from mountainash.expressions.backends.expression_systems.narwhals.base import (
    NarwhalsBaseExpressionSystem,
)


class TestCallWithExprSupport:
    """Test that _call_with_expr_support enriches known errors."""

    def test_polars_success_passes_through(self):
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_STRING as FK,
        )
        sys = PolarsBaseExpressionSystem()
        result = sys._call_with_expr_support(
            lambda: "ok",
            function_key=FK.CONTAINS,
            substring="hello",
        )
        assert result == "ok"

    def test_polars_unknown_error_propagates(self):
        sys = PolarsBaseExpressionSystem()

        def raise_runtime():
            raise RuntimeError("unrelated")

        with pytest.raises(RuntimeError, match="unrelated"):
            sys._call_with_expr_support(
                raise_runtime,
                function_key="CONTAINS",
                substring="hello",
            )

    def test_narwhals_known_limitation_enriches_error(self):
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_STRING as FK,
        )
        sys = NarwhalsBaseExpressionSystem()

        def raise_type_error():
            raise TypeError("expected a string")

        # Narwhals has STARTS_WITH/substring in its registry
        with pytest.raises(BackendCapabilityError, match="narwhals"):
            sys._call_with_expr_support(
                raise_type_error,
                function_key=FK.STARTS_WITH,
                substring="not_a_literal",
            )

    def test_ibis_no_limitations(self):
        sys = IbisBaseExpressionSystem()

        def raise_type_error():
            raise TypeError("some error")

        # Ibis has empty registry — TypeError should propagate as-is
        with pytest.raises(TypeError, match="some error"):
            sys._call_with_expr_support(
                raise_type_error,
                function_key="STARTS_WITH",
                substring="hello",
            )


class TestExtractLiteralIfPossible:
    """Test literal extraction for backends that need raw values."""

    def test_polars_raw_value_passes_through(self):
        sys = PolarsBaseExpressionSystem()
        assert sys._extract_literal_if_possible("hello") == "hello"
        assert sys._extract_literal_if_possible(42) == 42
        assert sys._extract_literal_if_possible(None) is None

    def test_polars_literal_expr_extracts(self):
        import polars as pl
        sys = PolarsBaseExpressionSystem()
        result = sys._extract_literal_if_possible(pl.lit("hello"))
        assert result == "hello"

    def test_polars_column_ref_passes_through(self):
        import polars as pl
        sys = PolarsBaseExpressionSystem()
        col_expr = pl.col("name")
        result = sys._extract_literal_if_possible(col_expr)
        # Column ref cannot be extracted — returns unchanged
        assert isinstance(result, pl.Expr)

    def test_narwhals_raw_value_passes_through(self):
        sys = NarwhalsBaseExpressionSystem()
        assert sys._extract_literal_if_possible("hello") == "hello"
        assert sys._extract_literal_if_possible(42) == 42

    def test_narwhals_literal_expr_extracts(self):
        import narwhals as nw
        sys = NarwhalsBaseExpressionSystem()
        result = sys._extract_literal_if_possible(nw.lit("hello"))
        assert result == "hello"

    def test_narwhals_column_ref_passes_through(self):
        import narwhals as nw
        sys = NarwhalsBaseExpressionSystem()
        col_expr = nw.col("name")
        result = sys._extract_literal_if_possible(col_expr)
        assert isinstance(result, nw.Expr)

    def test_ibis_always_passes_through(self):
        import ibis
        sys = IbisBaseExpressionSystem()
        lit_expr = ibis.literal("hello")
        result = sys._extract_literal_if_possible(lit_expr)
        # Ibis never needs extraction — expressions always pass through
        assert result is lit_expr
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target-quick tests/unit/test_call_with_expr_support.py -v`
Expected: FAIL — `AttributeError: 'PolarsBaseExpressionSystem' object has no attribute '_call_with_expr_support'`

- [ ] **Step 3: Add base method and `KNOWN_EXPR_LIMITATIONS` class var to `BaseExpressionSystem`**

In `src/mountainash/expressions/backends/expression_systems/base.py`, add after line 39:

```python
    # Class-level registry for known expression argument limitations.
    # Each backend subclass populates this with its own limitations.
    KNOWN_EXPR_LIMITATIONS: dict[tuple[str, str], "KnownLimitation"] = {}

    # Backend name for error messages. Subclasses should override.
    BACKEND_NAME: str = "unknown"

    def _extract_literal_if_possible(self, expr: Any) -> Any:
        """Extract the raw Python value from a literal expression, if possible.

        Some native APIs (e.g., Narwhals/Pandas str methods) require raw Python
        values, not expression objects, even for literal values. This method
        unwraps literal expressions back to raw values. Column references and
        complex expressions pass through unchanged.

        Subclasses override with backend-specific literal detection.

        Returns:
            Raw Python value if the expression is a simple literal, otherwise
            the expression unchanged.
        """
        # Default: return unchanged. Subclasses override.
        return expr

    def _call_with_expr_support(
        self,
        fn: Any,
        *,
        function_key: str,
        **named_args: Any,
    ) -> Any:
        """Call a native backend function, enriching errors for known limitations.

        Args:
            fn: Zero-arg callable that invokes the native backend operation.
            function_key: The FKEY_* enum value for registry lookup.
            **named_args: Parameter names mapped to their values, used to
                identify which parameter caused the error in registry lookup.
        """
        try:
            return fn()
        except Exception as exc:
            for param_name in named_args:
                key = (function_key, param_name)
                limitation = self.KNOWN_EXPR_LIMITATIONS.get(key)
                if limitation and isinstance(exc, limitation.native_errors):
                    from mountainash.core.types import BackendCapabilityError
                    raise BackendCapabilityError(
                        limitation.message,
                        backend=self.BACKEND_NAME,
                        function_key=function_key,
                        limitation=limitation,
                    ) from exc
            raise
```

Also add the import at the top of `base.py`:

```python
if TYPE_CHECKING:
    from mountainash.core.types import KnownLimitation
```

- [ ] **Step 4: Implement Polars `_extract_literal_if_possible` and `BACKEND_NAME`**

In `src/mountainash/expressions/backends/expression_systems/polars/base.py`, add after line 67:

```python
    BACKEND_NAME: str = "polars"

    def _extract_literal_if_possible(self, expr: Any) -> Any:
        """Extract literal value from a Polars expression.

        Polars accepts expressions natively for most string methods, so this
        is mainly used for consistency. Returns raw Python values as-is and
        attempts to evaluate Polars literal expressions.
        """
        if isinstance(expr, (str, int, float, bool, type(None))):
            return expr

        if isinstance(expr, pl.Expr):
            try:
                result = pl.select(expr).item()
                return result
            except Exception:
                pass

        return expr
```

- [ ] **Step 5: Implement Ibis `_extract_literal_if_possible` and `BACKEND_NAME`**

In `src/mountainash/expressions/backends/expression_systems/ibis/base.py`, add after line 68 (after `_extract_literal_value`):

```python
    BACKEND_NAME: str = "ibis"

    def _extract_literal_if_possible(self, expr: Any) -> Any:
        """Ibis accepts expressions everywhere — no extraction needed."""
        return expr
```

- [ ] **Step 6: Implement Narwhals `_extract_literal_if_possible`, `BACKEND_NAME`, and registry**

In `src/mountainash/expressions/backends/expression_systems/narwhals/base.py`, add after line 78:

```python
    BACKEND_NAME: str = "narwhals"

    def _extract_literal_if_possible(self, expr: Any) -> Any:
        """Extract literal value from a Narwhals expression.

        Narwhals/Pandas string methods require raw Python values — they reject
        even nw.lit("hello"). This unwraps literal expressions back to raw
        values while letting column references pass through unchanged.
        """
        if isinstance(expr, (str, int, float, bool, type(None))):
            return expr

        if isinstance(expr, nw.Expr):
            expr_repr = repr(expr)
            if "lit(" in expr_repr.lower() or "literal" in expr_repr.lower():
                try:
                    import pandas as pd
                    tiny_df = nw.from_native(pd.DataFrame({"_": [0]}))
                    result = tiny_df.select(expr.alias("_val"))["_val"].to_list()[0]
                    return result
                except Exception:
                    pass

        return expr
```

Also populate the Narwhals limitation registry. Add to `narwhals/base.py` after the class definition's `_extract_literal_if_possible` method, as a class variable block at the top of the class (after `BACKEND_NAME`). First add the imports at the top of the file:

```python
from mountainash.core.types import KnownLimitation
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
```

Then add the class variable:

```python
    _NW_STRING_LITERAL_ONLY = KnownLimitation(
        message="Narwhals string methods require literal values, not column references",
        native_errors=(TypeError,),
        workaround="Use a literal string value instead of a column reference",
    )

    KNOWN_EXPR_LIMITATIONS: dict[tuple[str, str], KnownLimitation] = {
        (FK_STR.STARTS_WITH, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.ENDS_WITH, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.CONTAINS, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.REPLACE, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.REPLACE, "replacement"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.LIKE, "match"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.REGEXP_REPLACE, "pattern"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.REGEXP_REPLACE, "replacement"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.SUBSTRING, "start"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.SUBSTRING, "length"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.LEFT, "count"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.RIGHT, "count"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.TRIM, "characters"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.LTRIM, "characters"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.RTRIM, "characters"): _NW_STRING_LITERAL_ONLY,
    }
```

- [ ] **Step 7: Add Polars limitation registry**

Add imports at top of `src/mountainash/expressions/backends/expression_systems/polars/base.py`:

```python
from mountainash.core.types import KnownLimitation
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
```

Add class variable to `PolarsBaseExpressionSystem`:

```python
    KNOWN_EXPR_LIMITATIONS: dict[tuple[str, str], KnownLimitation] = {
        (FK_STR.REPLACE, "pattern"): KnownLimitation(
            message="Polars does not support dynamic column patterns in str.replace",
            native_errors=(Exception,),  # pl.exceptions.ComputeError
            workaround="Use a literal string pattern; replacement can be a column reference",
        ),
        (FK_STR.LPAD, "length"): KnownLimitation(
            message="Polars str.pad_start requires a literal integer length",
            native_errors=(TypeError,),
            workaround="Use a literal integer for the padding length",
        ),
        (FK_STR.RPAD, "length"): KnownLimitation(
            message="Polars str.pad_end requires a literal integer length",
            native_errors=(TypeError,),
            workaround="Use a literal integer for the padding length",
        ),
    }
```

Note: Use `Exception` for Polars `ComputeError` since the exact exception class path (`pl.exceptions.ComputeError`) may vary. Refine to the exact type during implementation if import is straightforward.

- [ ] **Step 8: Run tests to verify they pass**

Run: `hatch run test:test-target-quick tests/unit/test_call_with_expr_support.py -v`
Expected: All tests PASS

- [ ] **Step 9: Run existing test suite to ensure no regressions**

Run: `hatch run test:test-target-quick tests/ -x --timeout=120`
Expected: All existing tests PASS (no changes to backend methods yet)

- [ ] **Step 10: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/base.py \
  src/mountainash/expressions/backends/expression_systems/polars/base.py \
  src/mountainash/expressions/backends/expression_systems/ibis/base.py \
  src/mountainash/expressions/backends/expression_systems/narwhals/base.py \
  tests/unit/test_call_with_expr_support.py
git commit -m "feat: add _call_with_expr_support and per-backend limitation registries"
```

---

### Task 3: Migrate Polars String Backend — Search Operations

The search operations (contains, strpos, count_substring) are the highest-impact inconsistency. `starts_with` and `ends_with` already pass through correctly.

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py:380-482`
- Test: `tests/cross_backend/test_expression_argument_types.py` (create — first test cases)

- [ ] **Step 1: Write expression argument type tests for search operations**

Create `tests/cross_backend/test_expression_argument_types.py`:

```python
"""Cross-backend tests for expression argument types in string operations.

Tests that string operations handle four argument types consistently:
- RAW_SCALAR: raw Python value ("world")
- EXPRESSION_LITERAL: ma.lit("world")
- COLUMN_REFERENCE: ma.col("pattern")
- COMPLEX_EXPRESSION: ma.col("pattern").str.lower()

Where backends cannot support column references, tests are xfail(strict=True)
so they break when the backend adds support.
"""

import pytest
import mountainash as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


# =============================================================================
# Search Operations — contains
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestContainsArgTypes:
    """Test contains() with different argument types."""

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_contains_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "world cup"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("world")
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_contains_expr_literal(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "world cup"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains(ma.lit("world"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
    ])
    def test_contains_column_reference(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "world cup"], "pattern": ["world", "baz", "cup"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains(ma.col("pattern"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
    ])
    def test_contains_complex_expression(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "world cup"], "pattern": ["WORLD", "BAZ", "CUP"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains(ma.col("pattern").str.lower())
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"


# =============================================================================
# Search Operations — starts_with
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestStartsWithArgTypes:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_starts_with_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "help me"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.starts_with("hel")
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_starts_with_expr_literal(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "help me"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.starts_with(ma.lit("hel"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
    ])
    def test_starts_with_column_reference(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "help me"], "prefix": ["hel", "baz", "hel"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.starts_with(ma.col("prefix"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"


# =============================================================================
# Search Operations — ends_with
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestEndsWithArgTypes:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_ends_with_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "my world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.ends_with("world")
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
    ])
    def test_ends_with_column_reference(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "my world"], "suffix": ["world", "baz", "world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.ends_with(ma.col("suffix"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"


# =============================================================================
# Search Operations — strpos
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestStrposArgTypes:

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals strpos not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals strpos not implemented")),
    ])
    def test_strpos_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.strpos("lo")
        actual = collect_expr(df, expr)
        assert actual[0] > 0, f"[{backend_name}] 'hello' should contain 'lo'"
        assert actual[1] == 0, f"[{backend_name}] 'world' should not contain 'lo'"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals strpos not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals strpos not implemented")),
    ])
    def test_strpos_column_reference(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello", "world"], "sub": ["lo", "xyz"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.strpos(ma.col("sub"))
        actual = collect_expr(df, expr)
        assert actual[0] > 0, f"[{backend_name}] 'hello' should contain 'lo'"
        assert actual[1] == 0, f"[{backend_name}] 'world' should not contain 'xyz'"


# =============================================================================
# Search Operations — count_substring
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestCountSubstringArgTypes:

    @pytest.mark.parametrize("backend_name", [
        "polars",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals count_substring not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals count_substring not implemented")),
        pytest.param("ibis-polars", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
        pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
        pytest.param("ibis-sqlite", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
    ])
    def test_count_substring_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["abcabc", "xyz"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.count_substring("abc")
        actual = collect_expr(df, expr)
        assert actual == [2, 0], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals count_substring not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals count_substring not implemented")),
        pytest.param("ibis-polars", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
        pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
        pytest.param("ibis-sqlite", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
    ])
    def test_count_substring_column_reference(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["abcabc", "xyz"], "sub": ["abc", "xyz"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.count_substring(ma.col("sub"))
        actual = collect_expr(df, expr)
        assert actual == [2, 1], f"[{backend_name}] got {actual}"
```

- [ ] **Step 2: Run tests to check current state (some will fail due to `_extract_literal_value`)**

Run: `hatch run test:test-target-quick tests/cross_backend/test_expression_argument_types.py -v`
Expected: Raw scalar and expr literal tests pass on Polars; column reference tests may fail on Polars for `contains`/`strpos`/`count_substring` due to `_extract_literal_value`.

- [ ] **Step 3: Migrate Polars `contains` — remove `_extract_literal_value`, wrap with `_call_with_expr_support`**

In `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py`, replace the `contains` method (lines 380-402):

```python
    def contains(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Whether the input string contains the substring.

        Args:
            input: String expression.
            substring: Substring to search for (expression or literal).
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        return self._call_with_expr_support(
            lambda: input.str.contains(substring, literal=True),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            substring=substring,
        )
```

Note: The old code had regex detection logic (`is_regex = any(c in str(pattern) for c in regex_chars)`). This is removed because the `literal=True` flag is the correct default for `contains` — regex matching should go through `regex_contains` / `regexp_match_substring` instead. The regex detection was a workaround for the literal extraction.

Add the function key import at the top of the file if not already present:

```python
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
)
```

- [ ] **Step 4: Migrate Polars `strpos` — remove `_extract_literal_value`**

Replace the `strpos` method (around lines 442-462):

```python
    def strpos(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Return 1-indexed position of substring in input, 0 if not found.

        Args:
            input: String expression.
            substring: Substring to search for (expression or literal).
            case_sensitivity: Case sensitivity option.

        Returns:
            Integer expression (1-indexed, 0 = not found).
        """
        return self._call_with_expr_support(
            lambda: input.str.find(substring).fill_null(-1) + 1,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS,
            substring=substring,
        )
```

- [ ] **Step 5: Migrate Polars `count_substring` — remove `_extract_literal_value`**

Replace the `count_substring` method (around lines 464-482):

```python
    def count_substring(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Count occurrences of substring in input.

        Args:
            input: String expression.
            substring: Substring to count (expression or literal).
            case_sensitivity: Case sensitivity option.

        Returns:
            Integer expression.
        """
        return self._call_with_expr_support(
            lambda: input.str.count_matches(substring, literal=True),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING,
            substring=substring,
        )
```

- [ ] **Step 6: Run argument type tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_expression_argument_types.py -v`
Expected: Polars contains/strpos/count_substring column reference tests now PASS. xfails for narwhals/pandas still xfail.

- [ ] **Step 7: Run full existing string test suite for regressions**

Run: `hatch run test:test-target-quick tests/cross_backend/test_string.py tests/cross_backend/test_string_aspirational.py tests/cross_backend/test_string_strip_prefix_suffix.py -v`
Expected: All existing tests PASS (they use literal arguments — unchanged behaviour)

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py \
  tests/cross_backend/test_expression_argument_types.py
git commit -m "feat: migrate Polars search string ops to pass-through expressions"
```

---

### Task 4: Migrate Ibis String Backend — Search Operations

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py:353-462`

- [ ] **Step 1: Read current Ibis search methods to identify `_extract_literal_value` calls**

Read `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py` lines 353-462.

- [ ] **Step 2: Migrate Ibis `contains` — remove `_extract_literal_value`, wrap with `_call_with_expr_support`**

The current Ibis `contains` (line 370) calls `_extract_literal_value` and has special regex detection. Replace with:

```python
    def contains(
        self,
        input: IbisExpr,
        /,
        substring: IbisExpr,
        case_sensitivity: Any = None,
    ) -> IbisExpr:
        """Whether the input string contains the substring."""
        return self._call_with_expr_support(
            lambda: input.contains(substring),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            substring=substring,
        )
```

Add the function key import at the top if not present:

```python
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
)
```

- [ ] **Step 3: Migrate Ibis `starts_with` — remove `_extract_literal_value`**

Replace (around line 381-399):

```python
    def starts_with(
        self,
        input: IbisExpr,
        substring: IbisExpr,
        /,
        case_sensitivity: Any = None,
    ) -> IbisExpr:
        """Whether input string starts with the substring."""
        return self._call_with_expr_support(
            lambda: input.startswith(substring),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
            substring=substring,
        )
```

- [ ] **Step 4: Migrate Ibis `ends_with` — remove `_extract_literal_value`**

Replace (around line 401-419):

```python
    def ends_with(
        self,
        input: IbisExpr,
        /,
        substring: IbisExpr,
        case_sensitivity: Any = None,
    ) -> IbisExpr:
        """Whether input string ends with the substring."""
        return self._call_with_expr_support(
            lambda: input.endswith(substring),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
            substring=substring,
        )
```

- [ ] **Step 5: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_expression_argument_types.py tests/cross_backend/test_string.py -v`
Expected: All Ibis search tests PASS (both literal and column ref)

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py
git commit -m "feat: migrate Ibis search string ops to pass-through expressions"
```

---

### Task 5: Migrate Narwhals String Backend — Search Operations

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py:378-488`

- [ ] **Step 1: Read current Narwhals search methods**

Read `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py` lines 378-442.

- [ ] **Step 2: Migrate Narwhals `contains` — use `_extract_literal_if_possible` + `_call_with_expr_support`**

Replace (around lines 378-398):

```python
    def contains(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Whether the input string contains the substring."""
        pattern = self._extract_literal_if_possible(substring)
        return self._call_with_expr_support(
            lambda: input.str.contains(pattern),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            substring=substring,
        )
```

Add the function key import at the top if not present:

```python
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
)
```

- [ ] **Step 3: Migrate Narwhals `starts_with` — use `_extract_literal_if_possible` + `_call_with_expr_support`**

Replace (around lines 400-420):

```python
    def starts_with(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Whether input string starts with the substring."""
        prefix = self._extract_literal_if_possible(substring)
        return self._call_with_expr_support(
            lambda: input.str.starts_with(prefix),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
            substring=substring,
        )
```

- [ ] **Step 4: Migrate Narwhals `ends_with` — use `_extract_literal_if_possible` + `_call_with_expr_support`**

Replace (around lines 422-442):

```python
    def ends_with(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Whether input string ends with the substring."""
        suffix = self._extract_literal_if_possible(substring)
        return self._call_with_expr_support(
            lambda: input.str.ends_with(suffix),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
            substring=substring,
        )
```

- [ ] **Step 5: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_expression_argument_types.py tests/cross_backend/test_string.py -v`
Expected: Narwhals literal tests PASS, column ref tests XFAIL (strict) with `BackendCapabilityError`

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py
git commit -m "feat: migrate Narwhals search string ops to pass-through with error enrichment"
```

---

### Task 6: Migrate Remaining Polars String Operations

Migrate all other Polars string methods that call `_extract_literal_value`. Read each method, remove the extraction, wrap with `_call_with_expr_support`.

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py`

- [ ] **Step 1: Identify all remaining `_extract_literal_value` calls in Polars string file**

Run: `grep -n "_extract_literal_value" src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py`

This should show calls in: `trim` (182), `ltrim` (202), `rtrim` (222), `lpad` (242-243), `rpad` (263-264), `center` (286-287), `substring` (319-320), `left` (333), `right` (343), `like` (643), `repeat` (603), `replace_slice` (365-367), `regexp_replace` (792-793).

- [ ] **Step 2: Migrate trim/ltrim/rtrim**

For each, replace `_extract_literal_value` with direct pass-through and `_call_with_expr_support`:

```python
    def trim(self, input: PolarsExpr, /, characters: PolarsExpr = None, ...) -> PolarsExpr:
        if characters is None:
            return input.str.strip_chars()
        return self._call_with_expr_support(
            lambda: input.str.strip_chars(characters),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TRIM,
            characters=characters,
        )
```

Apply the same pattern to `ltrim` (using `strip_chars_start`) and `rtrim` (using `strip_chars_end`).

- [ ] **Step 3: Migrate lpad/rpad**

These have known Polars limitations (length must be literal int). Use `_extract_literal_if_possible` for the length since Polars `pad_start`/`pad_end` requires `int`, and wrap with `_call_with_expr_support`:

```python
    def lpad(self, input: PolarsExpr, /, length: PolarsExpr, characters: PolarsExpr = None, ...) -> PolarsExpr:
        length_val = self._extract_literal_if_possible(length)
        fill_char = self._extract_literal_if_possible(characters) if characters is not None else " "
        return self._call_with_expr_support(
            lambda: input.str.pad_start(length_val, fill_char=str(fill_char)),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,
            length=length,
        )
```

Same pattern for `rpad` using `pad_end`.

- [ ] **Step 4: Migrate substring/left/right**

Polars `str.slice` accepts Expr offsets. Remove extraction, pass through:

```python
    def substring(self, input: PolarsExpr, /, start: PolarsExpr, length: PolarsExpr = None, ...) -> PolarsExpr:
        if length is None:
            return self._call_with_expr_support(
                lambda: input.str.slice(start),
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
                start=start,
            )
        return self._call_with_expr_support(
            lambda: input.str.slice(start, length),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
            start=start, length=length,
        )
```

For `left` (using `str.head`) and `right` (using `str.tail`), pass through directly.

- [ ] **Step 5: Migrate like, repeat, replace_slice, regexp_replace**

For `like` — extraction is needed because it converts SQL LIKE syntax to regex. Keep `_extract_literal_if_possible` for that conversion, but wrap with `_call_with_expr_support`.

For `repeat` — Polars does have `str.repeat_by` which can accept expressions. Check if the current UDF approach can be replaced. If Polars supports it natively, remove UDF and pass through.

For `replace_slice` — uses UDF. Keep `_extract_literal_if_possible` since UDF needs raw values. Wrap with `_call_with_expr_support`.

For `regexp_replace` — remove extraction, pass through. Polars `str.replace` with `literal=False` handles regex.

- [ ] **Step 6: Run full test suite**

Run: `hatch run test:test-target-quick tests/cross_backend/test_string.py tests/cross_backend/test_string_aspirational.py tests/cross_backend/test_string_strip_prefix_suffix.py tests/cross_backend/test_expression_argument_types.py -v`
Expected: All tests PASS or XFAIL as expected

- [ ] **Step 7: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py
git commit -m "feat: migrate all remaining Polars string ops to pass-through expressions"
```

---

### Task 7: Migrate Remaining Ibis String Operations

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py`

- [ ] **Step 1: Identify all remaining `_extract_literal_value` calls**

Run: `grep -n "_extract_literal_value" src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py`

- [ ] **Step 2: Migrate each method**

For each method with `_extract_literal_value`, remove the extraction and wrap the native call with `_call_with_expr_support`. Ibis supports expressions everywhere, so no `_extract_literal_if_possible` needed.

Methods to migrate (from audit): `lpad` (223-224), `rpad` (244-245), `substring` (297-298), `left` (311), `right` (321), `replace` (574-575), `repeat` (601), `like` (636), `regexp_match_substring` (666), `regexp_replace` (788-789).

Pattern for each:
```python
    def method_name(self, input, /, param, ...):
        return self._call_with_expr_support(
            lambda: input.ibis_method(param),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.METHOD_KEY,
            param=param,
        )
```

- [ ] **Step 3: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_string.py tests/cross_backend/test_string_aspirational.py tests/cross_backend/test_expression_argument_types.py -v`
Expected: All Ibis tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py
git commit -m "feat: migrate all remaining Ibis string ops to pass-through expressions"
```

---

### Task 8: Migrate Remaining Narwhals String Operations

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py`

- [ ] **Step 1: Identify all remaining `_extract_literal_value` calls**

Run: `grep -n "_extract_literal_value" src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py`

- [ ] **Step 2: Migrate each method**

For each method with `_extract_literal_value`, replace with `_extract_literal_if_possible` + `_call_with_expr_support`. All methods follow the same pattern:

```python
    def method_name(self, input, /, param, ...):
        param_val = self._extract_literal_if_possible(param)
        return self._call_with_expr_support(
            lambda: input.str.narwhals_method(param_val),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.METHOD_KEY,
            param=param,
        )
```

Methods to migrate (from audit): `trim` (181), `substring` (317-318), `left` (336), `right` (346), `replace` (597-598), `like` (659), `regexp_replace` (824-825).

- [ ] **Step 3: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_string.py tests/cross_backend/test_expression_argument_types.py -v`
Expected: All Narwhals literal tests PASS, column ref tests XFAIL (strict) with `BackendCapabilityError`

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py
git commit -m "feat: migrate all remaining Narwhals string ops to pass-through with error enrichment"
```

---

### Task 9: Add Expression Argument Type Tests for Replace, Substring, Padding

Extend `tests/cross_backend/test_expression_argument_types.py` with tests for the remaining operation categories.

**Files:**
- Modify: `tests/cross_backend/test_expression_argument_types.py`

- [ ] **Step 1: Add replace tests**

```python
# =============================================================================
# Replace Operations
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestReplaceArgTypes:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_replace_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.replace("world", "earth")
        actual = collect_expr(df, expr)
        assert actual == ["hello earth", "foo bar"], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("polars", marks=pytest.mark.xfail(
            strict=True, reason="polars dynamic pattern not supported")),
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
    ])
    def test_replace_column_reference_pattern(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar"], "old": ["world", "bar"], "new": ["earth", "baz"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.replace(ma.col("old"), ma.col("new"))
        actual = collect_expr(df, expr)
        assert actual == ["hello earth", "foo baz"], f"[{backend_name}] got {actual}"
```

- [ ] **Step 2: Add substring tests**

```python
# =============================================================================
# Substring Operations
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestSubstringArgTypes:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_substring_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.substring(0, 5)
        actual = collect_expr(df, expr)
        assert actual == ["hello", "foo b"], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
    ])
    def test_substring_column_reference_start(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar"], "start": [6, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.substring(ma.col("start"), 3)
        actual = collect_expr(df, expr)
        assert actual == ["wor", "bar"], f"[{backend_name}] got {actual}"
```

- [ ] **Step 3: Add padding tests**

```python
# =============================================================================
# Padding Operations
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestPaddingArgTypes:

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals lpad not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals lpad not implemented")),
    ])
    def test_lpad_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hi", "hey"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.lpad(5, " ")
        actual = collect_expr(df, expr)
        assert actual == ["   hi", "  hey"], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("polars", marks=pytest.mark.xfail(
            strict=True, reason="polars pad requires literal length")),
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals lpad not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals lpad not implemented")),
    ])
    def test_lpad_column_reference_length(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hi", "hey"], "len": [5, 6]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.lpad(ma.col("len"), " ")
        actual = collect_expr(df, expr)
        assert actual == ["   hi", "   hey"], f"[{backend_name}] got {actual}"
```

- [ ] **Step 4: Run all tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_expression_argument_types.py -v`
Expected: All tests PASS or strict XFAIL as documented

- [ ] **Step 5: Commit**

```bash
git add tests/cross_backend/test_expression_argument_types.py
git commit -m "test: add expression argument type tests for replace, substring, padding"
```

---

### Task 10: Deprecate `_extract_literal_value` and Update Principle

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/base.py:39`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/base.py:39`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/base.py:39`
- Modify: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/e.cross-backend/arguments-vs-options.md`

- [ ] **Step 1: Add deprecation notice to `_extract_literal_value` on all three backends**

In each backend's `base.py`, update the docstring of `_extract_literal_value`:

```python
    def _extract_literal_value(self, expr: Any) -> Any:
        """Extract the literal value from a backend literal expression.

        .. deprecated::
            Use _extract_literal_if_possible() + _call_with_expr_support() instead.
            See docs/superpowers/specs/2026-04-06-expression-argument-consistency-design.md
            This method will be removed once all callers (datetime, rounding, etc.) are migrated.
        """
```

- [ ] **Step 2: Update arguments-vs-options principle**

In `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/e.cross-backend/arguments-vs-options.md`:

Update the "When _extract_literal_value() Is Appropriate" section to reference the new pattern:

```markdown
## When Backends Need Raw Values

Some backend APIs (e.g., Narwhals `str.slice`) only accept Python scalars, not expression objects. Use `_extract_literal_if_possible()` to unwrap literals, combined with `_call_with_expr_support()` for error enrichment when column references are passed:

1. **`_extract_literal_if_possible(expr)`** — unwraps `nw.lit("hello")` → `"hello"`, returns column refs unchanged
2. **`_call_with_expr_support(fn, function_key=..., param=expr)`** — calls `fn()`, catches native errors, enriches with context from `KNOWN_EXPR_LIMITATIONS` registry

See `KnownLimitation` and `BackendCapabilityError` in `mountainash.core.types`.
```

Update the "Future Considerations" section to remove the audit bullet (completed).

- [ ] **Step 3: Run full test suite to confirm no regressions**

Run: `hatch run test:test-quick`
Expected: All tests PASS or strict XFAIL

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/base.py \
  src/mountainash/expressions/backends/expression_systems/ibis/base.py \
  src/mountainash/expressions/backends/expression_systems/narwhals/base.py
git commit -m "docs: deprecate _extract_literal_value, update arguments-vs-options principle"
```

Note: The principle file is in the mountainash-central repo — commit separately there if it's a separate working tree.
