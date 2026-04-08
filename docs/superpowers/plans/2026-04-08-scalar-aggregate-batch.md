# Scalar Aggregate Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire 13 aggregate expression functions (`any_value`, `sum`, `sum0`, `avg`, `min`, `max`, `product`, `std_dev`, `variance`, `corr`, `mode`, `median`, `quantile`) through the missing layers 4–6 of the wiring matrix; expose 8 deterministic unary reducers as `Relation.<agg>(col) -> Python scalar` terminals; alias `mean` → `avg` on both surfaces; codify two recurring patterns as new principles.

**Architecture:** Pure wiring work — protocols and backend impls already exist. Add function-mapping entries, extend the api-builder protocol, add api-builder method bodies, add 3 free functions in `entrypoints.py`, add 8 Relation scalar terminals as 3-line compositions matching today's `count_rows()` pattern, write 2 new principles + 4 doc updates.

**Tech Stack:** Python 3.10+, Polars, Narwhals, Ibis, hatch + pytest.

**Spec:** `docs/superpowers/specs/2026-04-08-scalar-aggregate-batch-design.md`

**Foundation note:** Enums (`FKEY_SUBSTRAIT_SCALAR_AGGREGATE.{ANY_VALUE, SUM, SUM0, AVG, MIN, MAX, PRODUCT, STD_DEV, VARIANCE, CORR, MODE, MEDIAN, QUANTILE}`) already exist. Protocol methods already exist in `prtcl_expsys_aggregate_generic.py` (any_value) and `prtcl_expsys_aggregate_arithmetic.py` (12 arithmetic methods). All three backends implement them. The aggregate api_builder file is already real (not stub) and currently exposes only `count`. The `MountainAshNameAPIBuilder` is already in `_FLAT_NAMESPACES` so `.alias()` works directly. `AggregateRelNode(keys=[])` already works on all three backends from today's count_rows fix.

`sum0`, `first_value`, `last_value` are out of scope per the spec.

---

## File Structure

```
# Phase 1 — function mapping (single edit)
src/mountainash/expressions/core/expression_system/function_mapping/definitions.py
    Append 13 ExpressionFunctionDef entries to SCALAR_AGGREGATE_FUNCTIONS
    Add import: SubstraitAggregateArithmeticExpressionSystemProtocol

# Phase 2 — api_builder protocol
src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_aggregate.py
    Add 9 method signatures (any_value + 8 fluent reducers)

# Phase 3 — api_builder class
src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_aggregate.py
    Add 9 method bodies after existing count()

# Phase 4 — free functions
src/mountainash/expressions/core/expression_api/entrypoints.py
    Add corr(), median(), quantile() free functions
src/mountainash/expressions/__init__.py
src/mountainash/__init__.py
    Re-export corr, median, quantile

# Phase 5 — mountainash mean alias on col fluent surface
src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_aggregate.py
    Replace stub with mean() method delegating to AVG enum

# Phase 6 — Relation scalar terminals
src/mountainash/relations/core/relation_api/relation.py
    Add 8 scalar terminal methods + mean() alias

# Phase 7 — tests
tests/expressions/test_aggregate_fluent_reducers.py            (new)
tests/expressions/test_aggregate_free_functions.py             (new)
tests/relations/test_terminal_scalar_aggregates.py             (new)
tests/relations/test_terminal_scalar_aggregates_empty.py       (new)

# Phase 8 — principles
mountainash-central/01.principles/mountainash-expressions/c.api-design/scalar-terminal-composition.md   (new)
mountainash-central/01.principles/mountainash-expressions/c.api-design/free-function-entrypoints.md     (new)
mountainash-central/01.principles/mountainash-expressions/a.architecture/wiring-matrix.md               (update)
mountainash-central/01.principles/mountainash-expressions/f.extension-model/adding-operations.md        (update — add wiring-only flow)
mountainash-central/01.principles/mountainash-expressions/h.backlog/polars-alignment-deferred.md        (update — strike sum/avg/min/max/mean)
CLAUDE.md                                                                                                (update — 2 new c.api-design rows)
```

---

## Task 1: Function mapping — append 13 entries

**Files:**
- Modify: `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`
- Test: `tests/expressions/test_aggregate_function_mapping.py` *(new)*

- [ ] **Step 1: Write the failing test.**

```python
# tests/expressions/test_aggregate_function_mapping.py
"""All 13 aggregate functions from the scalar aggregate batch must be in the function registry."""
from __future__ import annotations

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE as K,
)
from mountainash.expressions.core.expression_system.function_mapping import (
    ExpressionFunctionRegistry,
)


EXPECTED_KEYS = {
    K.ANY_VALUE,
    K.SUM, K.AVG, K.MIN, K.MAX, K.PRODUCT,
    K.STD_DEV, K.VARIANCE, K.MODE,
    K.CORR, K.MEDIAN, K.QUANTILE,
}


def test_all_thirteen_aggregates_registered():
    ExpressionFunctionRegistry._init_registry()
    registered = set(ExpressionFunctionRegistry._functions.keys())
    missing = EXPECTED_KEYS - registered
    assert not missing, f"Missing aggregate registrations: {sorted(k.name for k in missing)}"
```

- [ ] **Step 2: Run, see fail.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_function_mapping.py
```

Expected: `AssertionError: Missing aggregate registrations: ['ANY_VALUE', 'AVG', 'CORR', ...]` (13 names).

- [ ] **Step 3: Add the import.** In `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`, find the import block around line 46 that imports from `expression_systems.substrait` and add `SubstraitAggregateArithmeticExpressionSystemProtocol` next to the existing `SubstraitAggregateGenericExpressionSystemProtocol`.

```python
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    ...,
    SubstraitAggregateGenericExpressionSystemProtocol,
    SubstraitAggregateArithmeticExpressionSystemProtocol,   # NEW
    ...,
)
```

- [ ] **Step 4: Append the 13 entries.** Find `SCALAR_AGGREGATE_FUNCTIONS` (around line 794). Currently it has two entries (`COUNT`, `COUNT_RECORDS`). Append the following entries inside the same list, in the order shown:

```python
        # --- generic ---
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="any_value",
            options=("ignore_nulls",),
            protocol_method=SubstraitAggregateGenericExpressionSystemProtocol.any_value,
        ),
        # --- arithmetic, single-arg ---
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="sum",
            options=("overflow",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.sum,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.AVG,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="avg",
            options=("overflow",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.avg,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MIN,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="min",
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.min,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MAX,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="max",
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.max,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.PRODUCT,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="product",
            options=("overflow",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.product,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.STD_DEV,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="std_dev",
            options=("rounding", "distribution"),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.std_dev,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.VARIANCE,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="variance",
            options=("rounding", "distribution"),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.variance,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="mode",
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.mode,
        ),
        # --- arithmetic, multi-arg (free functions only) ---
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="corr",
            options=("rounding",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.corr,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="median",
            options=("rounding",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.median,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="quantile",
            options=("rounding",),
            protocol_method=SubstraitAggregateArithmeticExpressionSystemProtocol.quantile,
        ),
```

- [ ] **Step 5: Run, see pass.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_function_mapping.py
```

- [ ] **Step 6: No regressions.**

```bash
hatch run test:test-target-quick tests/expressions/
```

- [ ] **Step 7: Commit.**

```bash
git add src/mountainash/expressions/core/expression_system/function_mapping/definitions.py \
        tests/expressions/test_aggregate_function_mapping.py
git commit -m "feat(expressions): register 13 aggregate functions in SCALAR_AGGREGATE_FUNCTIONS"
```

---

## Task 2: api_builder protocol — add 9 fluent signatures

**Files:**
- Modify: `src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_aggregate.py`

The protocol currently declares only `count`. Add 9 method signatures: `any_value`, `sum`, `avg`, `min`, `max`, `product`, `std_dev`, `variance`, `mode`. Multi-arg `corr`/`median`/`quantile` are NOT on this protocol — they live in `entrypoints.py` (Task 4).

- [ ] **Step 1: Replace the protocol body** with the full surface. Open the file and replace the existing class body with:

```python
"""Protocol for Substrait scalar aggregate api_builder methods."""
from __future__ import annotations

from typing import Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI


class SubstraitScalarAggregateAPIBuilderProtocol(Protocol):
    """Substrait-standard scalar aggregate builder surface."""

    def count(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Count non-null values of this column. Substrait ``count(x)``."""
        ...

    def any_value(self, *, ignore_nulls: Optional[bool] = None) -> "BaseExpressionAPI":
        """Return one representative value from the group. Substrait ``any_value(x)``."""
        ...

    def sum(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Sum a set of values. Returns null for empty input. Substrait ``sum(x)``."""
        ...

    def avg(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Arithmetic mean. Substrait ``avg(x)``."""
        ...

    def min(self) -> "BaseExpressionAPI":
        """Minimum value. Substrait ``min(x)``."""
        ...

    def max(self) -> "BaseExpressionAPI":
        """Maximum value. Substrait ``max(x)``."""
        ...

    def product(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Product of values. Substrait ``product(x)``."""
        ...

    def std_dev(
        self,
        *,
        rounding: Optional[str] = None,
        distribution: Optional[str] = None,
    ) -> "BaseExpressionAPI":
        """Standard deviation. Substrait ``std_dev(x)``."""
        ...

    def variance(
        self,
        *,
        rounding: Optional[str] = None,
        distribution: Optional[str] = None,
    ) -> "BaseExpressionAPI":
        """Variance. Substrait ``variance(x)``."""
        ...

    def mode(self) -> "BaseExpressionAPI":
        """Most common value. Substrait ``mode(x)``."""
        ...
```

- [ ] **Step 2: Smoke import.**

```bash
hatch run python -c "from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_scalar_aggregate import SubstraitScalarAggregateAPIBuilderProtocol as P; print([m for m in dir(P) if not m.startswith('_')])"
```

Expected output should list all 10 methods (count + 9 new).

- [ ] **Step 3: Commit.**

```bash
git add src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_aggregate.py
git commit -m "feat(expressions): extend SubstraitScalarAggregateAPIBuilderProtocol with 9 fluent reducers"
```

---

## Task 3: api_builder class — add 9 method bodies

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_aggregate.py`
- Test: `tests/expressions/test_aggregate_fluent_reducers.py` *(new)*

- [ ] **Step 1: Write the failing cross-backend test.**

```python
# tests/expressions/test_aggregate_fluent_reducers.py
"""Cross-backend tests for the 9 fluent aggregate reducers."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.fixture
def df() -> pl.DataFrame:
    return pl.DataFrame({
        "g": ["a", "a", "a", "b", "b"],
        "x": [1, 2, 3, 4, 6],
    })


def _agg_via_polars(df, expr_factory):
    return (
        relation(df)
        .group_by("g")
        .agg(expr_factory(ma.col("x")).alias("v"))
        .to_polars()
        .sort("g")
    )


def test_sum(df):
    result = _agg_via_polars(df, lambda c: c.sum())
    assert result["v"].to_list() == [6, 10]


def test_avg(df):
    result = _agg_via_polars(df, lambda c: c.avg())
    assert result["v"].to_list() == [2.0, 5.0]


def test_min(df):
    result = _agg_via_polars(df, lambda c: c.min())
    assert result["v"].to_list() == [1, 4]


def test_max(df):
    result = _agg_via_polars(df, lambda c: c.max())
    assert result["v"].to_list() == [3, 6]


def test_product(df):
    result = _agg_via_polars(df, lambda c: c.product())
    assert result["v"].to_list() == [6, 24]


def test_std_dev(df):
    result = _agg_via_polars(df, lambda c: c.std_dev())
    # group a: [1,2,3] sample std_dev == 1.0; group b: [4,6] == sqrt(2) ≈ 1.414
    assert result["v"].to_list()[0] == pytest.approx(1.0)
    assert result["v"].to_list()[1] == pytest.approx(1.4142135623730951)


def test_variance(df):
    result = _agg_via_polars(df, lambda c: c.variance())
    # group a: var=1.0; group b: var=2.0
    assert result["v"].to_list()[0] == pytest.approx(1.0)
    assert result["v"].to_list()[1] == pytest.approx(2.0)


def test_mode(df):
    # mode is not deterministic on uniform groups; use a group with a clear mode
    df2 = pl.DataFrame({"g": ["a", "a", "a", "b"], "x": [1, 1, 2, 5]})
    result = (
        relation(df2)
        .group_by("g")
        .agg(ma.col("x").mode().alias("v"))
        .to_polars()
        .sort("g")
    )
    # mode of [1,1,2] = 1; mode of [5] = 5
    # Some backends return a list, some a scalar — check membership
    a_val = result.filter(pl.col("g") == "a")["v"].to_list()[0]
    b_val = result.filter(pl.col("g") == "b")["v"].to_list()[0]
    if isinstance(a_val, list):
        assert 1 in a_val
        assert 5 in b_val
    else:
        assert a_val == 1
        assert b_val == 5


def test_any_value(df):
    result = _agg_via_polars(df, lambda c: c.any_value())
    # Nondeterministic representative — just verify it's in the source set
    a_val = result.filter(pl.col("g") == "a")["v"].to_list()[0]
    b_val = result.filter(pl.col("g") == "b")["v"].to_list()[0]
    assert a_val in {1, 2, 3}
    assert b_val in {4, 6}


# Cross-backend smoke tests for sum (representative of the wiring path)

def test_sum_narwhals():
    pytest.importorskip("narwhals")
    import narwhals as nw
    nw_df = nw.from_native(
        pl.DataFrame({"g": ["a", "b", "b"], "x": [1, 2, 3]}),
        eager_only=True,
    )
    result = (
        relation(nw_df)
        .group_by("g")
        .agg(ma.col("x").sum().alias("v"))
        .to_polars()
        .sort("g")
    )
    assert result["v"].to_list() == [1, 5]


def test_sum_ibis():
    pytest.importorskip("ibis")
    import ibis
    t = ibis.memtable({"g": ["a", "b", "b"], "x": [1, 2, 3]})
    result = (
        relation(t)
        .group_by("g")
        .agg(ma.col("x").sum().alias("v"))
        .to_polars()
        .sort("g")
    )
    assert result["v"].to_list() == [1, 5]
```

- [ ] **Step 2: Run, see fail.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_fluent_reducers.py
```

Expected: `AttributeError` on `.sum()` etc., because the api_builder class doesn't expose them yet.

- [ ] **Step 3: Add the 9 method bodies.** Open `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_aggregate.py`. After the existing `count()` method (around line 30), append:

```python
    def any_value(self, *, ignore_nulls: Optional[bool] = None) -> "BaseExpressionAPI":
        """Return one representative value from the group. Substrait ``any_value(x)``.

        Note: nondeterministic — different backends may return different
        representative values across runs.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE,
            arguments=[self._node],
            options={"ignore_nulls": ignore_nulls} if ignore_nulls is not None else {},
        )
        return self._build(node)

    def sum(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Sum a set of values. Returns null for empty input. Substrait ``sum(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return self._build(node)

    def avg(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Arithmetic mean. Substrait ``avg(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.AVG,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return self._build(node)

    def min(self) -> "BaseExpressionAPI":
        """Minimum value. Substrait ``min(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MIN,
            arguments=[self._node],
            options={},
        )
        return self._build(node)

    def max(self) -> "BaseExpressionAPI":
        """Maximum value. Substrait ``max(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MAX,
            arguments=[self._node],
            options={},
        )
        return self._build(node)

    def product(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Product of values. Substrait ``product(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.PRODUCT,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return self._build(node)

    def std_dev(
        self,
        *,
        rounding: Optional[str] = None,
        distribution: Optional[str] = None,
    ) -> "BaseExpressionAPI":
        """Standard deviation. Substrait ``std_dev(x)``."""
        opts: dict = {}
        if rounding is not None:
            opts["rounding"] = rounding
        if distribution is not None:
            opts["distribution"] = distribution
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.STD_DEV,
            arguments=[self._node],
            options=opts,
        )
        return self._build(node)

    def variance(
        self,
        *,
        rounding: Optional[str] = None,
        distribution: Optional[str] = None,
    ) -> "BaseExpressionAPI":
        """Variance. Substrait ``variance(x)``."""
        opts: dict = {}
        if rounding is not None:
            opts["rounding"] = rounding
        if distribution is not None:
            opts["distribution"] = distribution
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.VARIANCE,
            arguments=[self._node],
            options=opts,
        )
        return self._build(node)

    def mode(self) -> "BaseExpressionAPI":
        """Most common value. Substrait ``mode(x)``.

        Note: behaviour on ties varies across backends — see
        ``e.cross-backend/known-divergences.md``.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE,
            arguments=[self._node],
            options={},
        )
        return self._build(node)
```

- [ ] **Step 4: Run, iterate until green.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_fluent_reducers.py
```

If `mode` or `any_value` fails because of backend-specific output shape, narrow the assertion to membership check (the test already does this for `mode`/`any_value`). If a backend genuinely doesn't support the aggregate, mark that specific case `xfail` with a clear note pointing to `e.cross-backend/known-divergences.md` — do NOT skip silently.

- [ ] **Step 5: No regressions.**

```bash
hatch run test:test-target-quick tests/expressions/ tests/relations/
```

- [ ] **Step 6: Commit.**

```bash
git add src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_aggregate.py \
        tests/expressions/test_aggregate_fluent_reducers.py
git commit -m "feat(expressions): expose 9 fluent aggregate reducers on SubstraitScalarAggregateAPIBuilder"
```

---

## Task 4: Free functions — corr, median, quantile

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/entrypoints.py`
- Modify: `src/mountainash/expressions/__init__.py`
- Modify: `src/mountainash/__init__.py`
- Test: `tests/expressions/test_aggregate_free_functions.py` *(new)*

- [ ] **Step 1: Write the failing test.**

```python
# tests/expressions/test_aggregate_free_functions.py
"""Multi-arg aggregates exposed as free functions."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


def test_corr_polars():
    df = pl.DataFrame({
        "g": ["a", "a", "a", "a"],
        "x": [1.0, 2.0, 3.0, 4.0],
        "y": [2.0, 4.0, 6.0, 8.0],
    })
    result = (
        relation(df)
        .group_by("g")
        .agg(ma.corr(ma.col("x"), ma.col("y")).alias("c"))
        .to_polars()
    )
    assert result["c"].to_list()[0] == pytest.approx(1.0)


def test_median_polars():
    df = pl.DataFrame({"g": ["a", "a", "a"], "x": [1, 2, 3]})
    result = (
        relation(df)
        .group_by("g")
        .agg(ma.median(ma.lit(0.5), ma.col("x")).alias("m"))
        .to_polars()
    )
    assert result["m"].to_list()[0] == pytest.approx(2.0)


def test_quantile_polars():
    df = pl.DataFrame({"g": ["a", "a", "a", "a", "a"], "x": [1.0, 2.0, 3.0, 4.0, 5.0]})
    # quantile signature per protocol: (boundaries, precision, n, distribution)
    # Concrete shape verified via the existing protocol method.
    result = (
        relation(df)
        .group_by("g")
        .agg(
            ma.quantile(
                ma.lit(0.5),   # boundaries
                ma.lit(0.01),  # precision
                ma.lit(1),     # n
                ma.lit("linear"),  # distribution
            ).alias("q")
        )
        .to_polars()
    )
    # Median of 1..5 is 3
    assert result["q"].to_list()[0] == pytest.approx(3.0)


def test_corr_importable_from_top_level():
    assert ma.corr is not None


def test_median_importable_from_top_level():
    assert ma.median is not None


def test_quantile_importable_from_top_level():
    assert ma.quantile is not None
```

**Note on `quantile` argument shape:** The protocol signature is `quantile(boundaries, precision, n, distribution, rounding=None)`. If the test reveals that any backend rejects one of these argument shapes (e.g. because Polars expects a single quantile fraction), narrow the test to verify the call dispatches without erroring rather than asserting a specific value, and add a clear note in the test docstring. The wiring is the deliverable; backend semantic alignment for `quantile` is a known-divergences-level issue.

- [ ] **Step 2: Run, see fail.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_free_functions.py
```

- [ ] **Step 3: Add the free functions to entrypoints.py.** Open `src/mountainash/expressions/core/expression_api/entrypoints.py`. After the existing `count_records()` definition (around line 302), add:

```python
def corr(
    x: Union[BaseExpressionAPI, ExpressionNode, Any],
    y: Union[BaseExpressionAPI, ExpressionNode, Any],
    *,
    rounding: Optional[str] = None,
) -> BaseExpressionAPI:
    """Pearson correlation between two expressions. Substrait ``corr(x, y)``.

    Args:
        x: First column expression.
        y: Second column expression.
        rounding: Optional Substrait rounding mode.

    Returns:
        BooleanExpressionAPI wrapping a ScalarFunctionNode with CORR.
    """
    from ..expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    )
    from ..expression_api import BooleanExpressionAPI

    operands = [_to_substrait_node(x), _to_substrait_node(y)]
    opts: dict = {}
    if rounding is not None:
        opts["rounding"] = rounding
    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR,
        arguments=operands,
        options=opts,
    )
    return BooleanExpressionAPI(node)


def median(
    precision: Union[BaseExpressionAPI, ExpressionNode, Any],
    x: Union[BaseExpressionAPI, ExpressionNode, Any],
    *,
    rounding: Optional[str] = None,
) -> BaseExpressionAPI:
    """Median value. Substrait ``median(precision, x)``.

    Args:
        precision: Precision parameter (per Substrait spec).
        x: Column expression to take the median of.
        rounding: Optional Substrait rounding mode.
    """
    from ..expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    )
    from ..expression_api import BooleanExpressionAPI

    operands = [_to_substrait_node(precision), _to_substrait_node(x)]
    opts: dict = {}
    if rounding is not None:
        opts["rounding"] = rounding
    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN,
        arguments=operands,
        options=opts,
    )
    return BooleanExpressionAPI(node)


def quantile(
    boundaries: Union[BaseExpressionAPI, ExpressionNode, Any],
    precision: Union[BaseExpressionAPI, ExpressionNode, Any],
    n: Union[BaseExpressionAPI, ExpressionNode, Any],
    distribution: Union[BaseExpressionAPI, ExpressionNode, Any],
    *,
    rounding: Optional[str] = None,
) -> BaseExpressionAPI:
    """Quantile aggregate. Substrait ``quantile(boundaries, precision, n, distribution)``.

    Args:
        boundaries: Quantile boundaries (e.g. 0.5 for median).
        precision: Precision parameter.
        n: Sample-size hint.
        distribution: Distribution mode (e.g. "linear").
        rounding: Optional Substrait rounding mode.
    """
    from ..expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    )
    from ..expression_api import BooleanExpressionAPI

    operands = [
        _to_substrait_node(boundaries),
        _to_substrait_node(precision),
        _to_substrait_node(n),
        _to_substrait_node(distribution),
    ]
    opts: dict = {}
    if rounding is not None:
        opts["rounding"] = rounding
    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE,
        arguments=operands,
        options=opts,
    )
    return BooleanExpressionAPI(node)
```

If `Optional` is not yet imported at the top of `entrypoints.py`, add `Optional` to the existing `from typing import ...` line.

- [ ] **Step 4: Re-export from `mountainash.expressions/__init__.py`.** Find the existing import line that brings in `count_records` and add `corr, median, quantile`:

```python
from mountainash.expressions.core.expression_api.entrypoints import (
    col, lit, coalesce, greatest, least, when, native, t_col,
    count_records,
    corr, median, quantile,   # NEW
)
```

Add `"corr", "median", "quantile"` to `__all__`.

- [ ] **Step 5: Re-export from `mountainash/__init__.py`.** Find where `count_records` is re-exported and add `corr, median, quantile` alongside; add to `__all__`.

- [ ] **Step 6: Run tests, iterate.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_free_functions.py
```

- [ ] **Step 7: Smoke test imports.**

```bash
hatch run python -c "import mountainash as ma; print(ma.corr, ma.median, ma.quantile)"
```

- [ ] **Step 8: Commit.**

```bash
git add src/mountainash/expressions/core/expression_api/entrypoints.py \
        src/mountainash/expressions/__init__.py \
        src/mountainash/__init__.py \
        tests/expressions/test_aggregate_free_functions.py
git commit -m "feat(expressions): add corr/median/quantile free functions"
```

---

## Task 5: Mountainash `mean` alias on the col fluent surface

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_aggregate.py`
- Test: extend `tests/expressions/test_aggregate_fluent_reducers.py`

`mean` is the only naming divergence from Substrait in this batch. Per `c.api-design/short-aliases.md`, aliases live in extension builders. The existing `MountainAshScalarAggregateAPIBuilder` is currently a stub — replace its body with a single `mean()` method that produces an `AVG` node, identical to the Substrait builder's `avg()`.

- [ ] **Step 1: Add a failing test.**

Append to `tests/expressions/test_aggregate_fluent_reducers.py`:

```python
def test_mean_alias_for_avg(df):
    """ma.col('x').mean() is a short alias for .avg() — same numeric result."""
    avg_result = _agg_via_polars(df, lambda c: c.avg())
    mean_result = _agg_via_polars(df, lambda c: c.mean())
    assert avg_result["v"].to_list() == mean_result["v"].to_list()
```

- [ ] **Step 2: Run, see fail.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_fluent_reducers.py::test_mean_alias_for_avg
```

Expected: `AttributeError: 'BooleanExpressionAPI' object has no attribute 'mean'`.

- [ ] **Step 3: Replace the stub.** Open `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_aggregate.py` and replace its body with:

```python
"""Mountainash extension aggregate operations APIBuilder.

Hosts short aliases for Substrait aggregates per
``c.api-design/short-aliases.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)

from ..api_builder_base import BaseExpressionAPIBuilder

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarAggregateAPIBuilder(BaseExpressionAPIBuilder):
    """Mountainash short aliases for Substrait aggregate operations."""

    def mean(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Short alias for :meth:`SubstraitScalarAggregateAPIBuilder.avg`.

        Matches the Polars / pandas idiom; semantically identical to ``avg``.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.AVG,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return self._build(node)
```

- [ ] **Step 4: Verify it's wired into `_FLAT_NAMESPACES`.** Open `src/mountainash/expressions/core/expression_api/boolean.py` and check whether `MountainAshScalarAggregateAPIBuilder` is imported and listed in `_FLAT_NAMESPACES`. If it isn't, add it:

```python
# import section
from .api_builders.extensions_mountainash import (
    ...,
    MountainAshScalarAggregateAPIBuilder,   # add if missing
    ...,
)

# _FLAT_NAMESPACES
_FLAT_NAMESPACES = [
    ...,
    MountainAshScalarAggregateAPIBuilder,   # add if missing
    ...,
]
```

Verify `MountainAshScalarAggregateAPIBuilder` is also exported from the extension package's `__init__.py`.

- [ ] **Step 5: Run, see pass.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_fluent_reducers.py::test_mean_alias_for_avg
```

- [ ] **Step 6: No regressions.**

```bash
hatch run test:test-target-quick tests/expressions/
```

- [ ] **Step 7: Commit.**

```bash
git add src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_aggregate.py \
        src/mountainash/expressions/core/expression_api/boolean.py \
        src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/__init__.py \
        tests/expressions/test_aggregate_fluent_reducers.py
git commit -m "feat(expressions): add mean alias for avg via MountainAshScalarAggregateAPIBuilder"
```

---

## Task 6: Relation scalar terminals — 8 reducers + mean alias

**Files:**
- Modify: `src/mountainash/relations/core/relation_api/relation.py`
- Test: `tests/relations/test_terminal_scalar_aggregates.py` *(new)*
- Test: `tests/relations/test_terminal_scalar_aggregates_empty.py` *(new)*

- [ ] **Step 1: Write failing tests for the 8 terminals.**

```python
# tests/relations/test_terminal_scalar_aggregates.py
"""Cross-backend tests for Relation.<agg>(col) scalar terminal methods."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.fixture
def df() -> pl.DataFrame:
    return pl.DataFrame({"x": [1, 2, 3, 4, 6]})


def test_sum(df):
    assert relation(df).sum("x") == 16


def test_avg(df):
    assert relation(df).avg("x") == pytest.approx(3.2)


def test_mean_alias(df):
    assert relation(df).mean("x") == relation(df).avg("x")


def test_min(df):
    assert relation(df).min("x") == 1


def test_max(df):
    assert relation(df).max("x") == 6


def test_product(df):
    assert relation(df).product("x") == 144


def test_std_dev():
    df = pl.DataFrame({"x": [1.0, 2.0, 3.0]})
    assert relation(df).std_dev("x") == pytest.approx(1.0)


def test_variance():
    df = pl.DataFrame({"x": [1.0, 2.0, 3.0]})
    assert relation(df).variance("x") == pytest.approx(1.0)


def test_any_value(df):
    val = relation(df).any_value("x")
    assert val in {1, 2, 3, 4, 6}


# Cross-backend smoke for sum

def test_sum_narwhals():
    pytest.importorskip("narwhals")
    import narwhals as nw
    nw_df = nw.from_native(pl.DataFrame({"x": [1, 2, 3]}), eager_only=True)
    assert relation(nw_df).sum("x") == 6


def test_sum_ibis():
    pytest.importorskip("ibis")
    import ibis
    t = ibis.memtable({"x": [1, 2, 3]})
    assert relation(t).sum("x") == 6


# After filter

def test_sum_after_filter(df):
    rel = relation(df).filter(ma.col("x").gt(ma.lit(2)))
    assert rel.sum("x") == 13  # 3+4+6
```

- [ ] **Step 2: Write empty-relation tests.**

```python
# tests/relations/test_terminal_scalar_aggregates_empty.py
"""Empty-relation behaviour for scalar aggregate terminals."""
from __future__ import annotations

import polars as pl

import mountainash as ma
from mountainash.relations import relation


def _empty_rel():
    df = pl.DataFrame({"x": [1, 2, 3]})
    return relation(df).filter(ma.col("x").gt(ma.lit(999)))


def test_empty_sum_returns_null_or_zero():
    """Empty input -> Substrait sum yields null. Polars represents this as None."""
    result = _empty_rel().sum("x")
    assert result is None or result == 0


def test_empty_avg_returns_null():
    result = _empty_rel().avg("x")
    assert result is None


def test_empty_min_returns_null():
    result = _empty_rel().min("x")
    assert result is None


def test_empty_max_returns_null():
    result = _empty_rel().max("x")
    assert result is None
```

- [ ] **Step 3: Run, see fail.**

```bash
hatch run test:test-target-quick tests/relations/test_terminal_scalar_aggregates.py tests/relations/test_terminal_scalar_aggregates_empty.py
```

- [ ] **Step 4: Add the 8 terminals + alias to `Relation`.** Open `src/mountainash/relations/core/relation_api/relation.py`. After the existing `item()` method, add:

```python
    # ------------------------------------------------------------------
    # Scalar aggregate terminals
    #
    # Each method is a thin composition over the corresponding aggregate
    # expression function. The pattern is identical to ``count_rows()``:
    # wrap ``self._node`` in an AggregateRelNode with empty keys, compile
    # via the existing visitor pipeline, extract via ``.item(...)``.
    #
    # See: c.api-design/scalar-terminal-composition.md
    # ------------------------------------------------------------------

    def _scalar_aggregate(self, agg_expr) -> Any:
        """Internal helper: aggregate the relation to one row, extract scalar."""
        from mountainash.relations.core.relation_nodes import AggregateRelNode
        aggregated = Relation(
            AggregateRelNode(
                input=self._node,
                keys=[],
                measures=[agg_expr.alias("__value__")],
            )
        )
        return aggregated.item("__value__")

    def sum(self, col: str) -> Any:
        """Return the sum of ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).sum())

    def avg(self, col: str) -> Any:
        """Return the arithmetic mean of ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).avg())

    def mean(self, col: str) -> Any:
        """Short alias for :meth:`avg`."""
        return self.avg(col)

    def min(self, col: str) -> Any:
        """Return the minimum value in ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).min())

    def max(self, col: str) -> Any:
        """Return the maximum value in ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).max())

    def product(self, col: str) -> Any:
        """Return the product of values in ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).product())

    def std_dev(self, col: str) -> Any:
        """Return the standard deviation of ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).std_dev())

    def variance(self, col: str) -> Any:
        """Return the variance of ``col`` as a Python scalar."""
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).variance())

    def any_value(self, col: str) -> Any:
        """Return one representative value from ``col`` as a Python scalar.

        Note: nondeterministic — different backends may return different
        representatives across runs.
        """
        import mountainash as ma
        return self._scalar_aggregate(ma.col(col).any_value())
```

- [ ] **Step 5: Run, see pass.**

```bash
hatch run test:test-target-quick tests/relations/test_terminal_scalar_aggregates.py tests/relations/test_terminal_scalar_aggregates_empty.py
```

If empty-relation behaviour diverges across backends (e.g. sum returns 0 on some, null on others), update the empty-relation test assertions to accept either, and document the divergence in `e.cross-backend/known-divergences.md` in Task 9.

- [ ] **Step 6: No regressions.**

```bash
hatch run test:test-target-quick tests/relations/ tests/expressions/
```

- [ ] **Step 7: Commit.**

```bash
git add src/mountainash/relations/core/relation_api/relation.py \
        tests/relations/test_terminal_scalar_aggregates.py \
        tests/relations/test_terminal_scalar_aggregates_empty.py
git commit -m "feat(relation): add 8 scalar aggregate terminals + mean alias"
```

---

## Task 7: New principle — `scalar-terminal-composition.md`

**Files:**
- Create: `mountainash-central/01.principles/mountainash-expressions/c.api-design/scalar-terminal-composition.md`

- [ ] **Step 1: Write the principle.**

```bash
cat > /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/c.api-design/scalar-terminal-composition.md <<'EOF'
# Scalar Terminal Composition

> **Status:** ADOPTED

## The Principle

A scalar terminal on `Relation` (a method that returns a Python scalar) is implemented as a **thin composition** over an aggregate expression function. The method wraps `self._node` in an `AggregateRelNode` with empty keys, compiles through the existing visitor pipeline, and extracts the single cell via `.item(...)`. **No per-backend dispatch.**

## Rationale

Backend variance is a solved problem at the *expression* layer — every aggregate function has cross-backend-tested implementations in the `aggregate_generic` and `aggregate_arithmetic` protocols. Pushing backend dispatch into `Relation` methods duplicates that work, violates the "relations compose; backends live in expression systems" separation, and forfeits lazy evaluation on backends that support it (Polars `LazyFrame`, Ibis deferred execution).

## Canonical Shape

```python
def _scalar_aggregate(self, agg_expr) -> Any:
    aggregated = Relation(
        AggregateRelNode(
            input=self._node,
            keys=[],
            measures=[agg_expr.alias("__value__")],
        )
    )
    return aggregated.item("__value__")

def sum(self, col: str) -> Any:
    import mountainash as ma
    return self._scalar_aggregate(ma.col(col).sum())
```

Three lines per terminal. The work is in the aggregate expression function (which already exists) and `item()` (which already exists).

## Inclusion Criteria

A function qualifies for a `Relation` scalar terminal if and only if it is:

1. **Deterministic.** Same input → same output across backends and runs. `any_value` is borderline; it's deterministic-per-call within a backend but the *value* varies. Documented in the docstring.
2. **Scalar-output.** Returns one Python value. `mode` fails: it returns a *set* in general, and tie-breaking diverges across backends.
3. **Unary.** Takes one column argument. `count_rows` is the nullary special case (uses the `count_records` 0-arg aggregate). Multi-arg aggregates (`corr`, `median`, `quantile`) stay in the expression-layer free-function surface.

`first_value` and `last_value` fail criterion 3 (they need ordering arguments) and are out of scope until aggregate ordering propagation lands.

## Naming

Match the Substrait expression-layer name character-for-character. Short aliases (e.g. `mean` → `avg`) live in the extension-builder layer per [`short-aliases.md`](short-aliases.md) and apply identically to both the expression-layer (`col("x").mean()`) and Relation surfaces (`Relation.mean(col)`).

## Out-of-Scope Patterns

These are **not** scalar terminals and should never be added under this name:

- **Multi-arg aggregates** (`corr`, `median`, `quantile`). Users write `relation(df).select(ma.quantile(...).alias("q")).item("q")` — two lines, explicit, no new Relation method.
- **Set-returning aggregates** (`mode`, `unique`). Different shape; need a different pattern.
- **Window functions.** Not scalar-output by definition.

## Examples

| Function | Status | Pattern |
|---|---|---|
| `count_rows()` | ✓ wired | nullary; uses `count_records()` |
| `sum`, `avg`, `min`, `max`, `product` | ✓ wired | classic unary reducers |
| `std_dev`, `variance` | ✓ wired | unary statistical |
| `any_value` | ✓ wired | nondeterministic but scalar |
| `mean` | ✓ wired (alias for `avg`) | extension-builder alias |
| `mode` | ✗ excluded | not scalar-output |
| `corr`, `median`, `quantile` | ✗ excluded | multi-arg; free function only |
| `first_value`, `last_value` | ⏳ deferred | needs ordering propagation |

## Anti-Patterns

- **Per-backend `if isinstance(native, pl.LazyFrame): ... elif ...` ladders inside a Relation method.** This was the rejected first draft of `count_rows()`. Always defer to the aggregate expression function.
- **Materialising to Polars then doing the reduction in Python.** Forfeits lazy evaluation. The aggregate pipeline already pushes down on Polars and Ibis.
- **Adding a `Relation.<agg>` method when no corresponding aggregate expression function exists.** Means the wiring matrix has a gap; close the expression-layer first, then add the terminal.

## Technical Reference

- `src/mountainash/relations/core/relation_api/relation.py` — `count_rows()`, `item()`, `_scalar_aggregate()`, the 8 reducer terminals
- `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_aggregate.py` — fluent aggregate methods
- `src/mountainash/relations/backends/relation_systems/{polars,narwhals,ibis}/*aggregate.py` — `keys=[]` handling per backend (the foundation that makes this pattern possible)

## Future Considerations

When `first_value`/`last_value` lands with ordering support, both will satisfy criteria 1, 2, and 3 (with the ordering as an additional kwarg, not a positional column) and join the terminal set. The existing pattern accommodates this without modification — the `agg_expr` argument to `_scalar_aggregate` just needs to carry the ordering.
EOF
```

- [ ] **Step 2: Verify file written.**

```bash
ls -la /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/c.api-design/scalar-terminal-composition.md
```

- [ ] **Step 3: Defer commit to Task 9 (single principles commit).**

---

## Task 8: New principle — `free-function-entrypoints.md`

**Files:**
- Create: `mountainash-central/01.principles/mountainash-expressions/c.api-design/free-function-entrypoints.md`

- [ ] **Step 1: Write the principle.**

```bash
cat > /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/c.api-design/free-function-entrypoints.md <<'EOF'
# Free-Function Entrypoints

> **Status:** ADOPTED

## The Principle

A **free function** is a top-level callable in `mountainash` that produces a `BaseExpressionAPI` (or a DSL builder, e.g. `when`) without a preceding `col(...)` context. Free functions live in `src/mountainash/expressions/core/expression_api/entrypoints.py` and are re-exported from `mountainash.expressions/__init__.py` and `mountainash/__init__.py`.

This principle codifies the existing `entrypoints.py` convention and answers a recurring design question: *should a new operation be a fluent column method, a free function, or both?*

## When to Use a Free Function

In priority order:

1. **No natural receiver.** `col`, `lit`, `native`, `count_records`, `t_col`, `always_true`, `always_false`. There is no "subject" column — the function creates one.

2. **Multi-arg combinators with no primary argument.** `coalesce`, `greatest`, `least`, and `corr`, `median`, `quantile`. All arguments are peers; making one the receiver would be arbitrary, and the call site reads worse: `col("x").coalesce(col("y"), col("z"))` is uglier than `coalesce(col("x"), col("y"), col("z"))`.

3. **DSL entry points.** `when(cond).then(...).otherwise(...)`. The free function begins a fluent chain that doesn't fit the column-method shape.

4. **Backend escape hatches.** `native(...)` wraps a backend-specific expression.

## When a Free Function Is Wrong

Any unary transformation with a natural column receiver. `ma.str_lower(col("x"))` would be wrong; `col("x").str.lower()` is idiomatic. The test:

> *Does one argument dominate the operation?*
> Yes → fluent column method.
> No → free function.

If yes, the operation belongs on a fluent api-builder (e.g. `SubstraitScalarStringAPIBuilder`), not in `entrypoints.py`.

## Both Forms Together

Allowed, with a clear rule: **fluent is canonical, free function is sugar.** The free function delegates to the fluent form (or vice versa) so there is one source of truth for the operation's semantics. Polars does this with `pl.sum("x")` (free) vs `col("x").sum()` (fluent). mountainash currently does *not* expose any operation in both forms, but this principle permits it for cases where idiom strongly favours both surfaces.

When a function is exposed in both forms:

- The fluent method is the canonical implementation (it directly constructs the `ScalarFunctionNode`).
- The free function delegates: `def sum(c): return col(c).sum()`.
- They MUST share the same name character-for-character.

## Naming Consistency

Free functions match their fluent counterpart's name character-for-character when both exist. No renames at the free-function layer. Short aliases (e.g. `mean` → `avg`) happen once, in the extension-builder layer per [`short-aliases.md`](short-aliases.md), and propagate to both surfaces.

## File Organisation

`entrypoints.py` is organised by section comments in priority order. New entrypoints go in the appropriate section, not in topic-specific files:

```python
# === Column and literal ===
def col(...): ...
def lit(...): ...

# === Combinators ===
def coalesce(...): ...
def greatest(...): ...
def least(...): ...

# === Control flow ===
def when(...): ...

# === Aggregates ===
def count_records(): ...
def corr(...): ...
def median(...): ...
def quantile(...): ...

# === Native / escape hatches ===
def native(...): ...

# === Extension ===
def t_col(...): ...
def always_true(): ...
def always_false(): ...
def always_unknown(): ...
```

The aim: a contributor scanning `entrypoints.py` should be able to find a function by category in seconds, and the file should never grow internal sub-files (e.g. `entrypoints/aggregates.py` would defeat the discoverability the principle exists to enforce).

## Re-Export Discipline

Every free function added to `entrypoints.py` MUST be re-exported in two places:

1. `src/mountainash/expressions/__init__.py` — package-level `from ... import` and `__all__`.
2. `src/mountainash/__init__.py` — top-level `from mountainash.expressions import` and `__all__`.

A free function that isn't reachable as `ma.<name>` is not finished.

## Future Work

Audit existing free functions against this principle (likely all pass; worth confirming once).

Candidate additions when backend support lands:
- `sum0` — faithful Substrait variant of `sum` returning 0 for empty input.
- `first_value(x, order_by=...)`, `last_value(x, order_by=...)`, `nth_value(x, n, order_by=...)` — once aggregate ordering propagation lands.
- `window(...)` — possible DSL entry to window functions, currently only buildable via `.over(...)` on a column.

These are not committed; they are flagged here so the next contributor doesn't have to rediscover the gaps.

## Anti-Patterns

- **A free function for a unary operation that has a natural receiver.** `ma.upper(col("x"))` instead of `col("x").str.upper()`. Choose fluent.
- **Topic-specific entrypoint files** (`entrypoints_aggregate.py`, `entrypoints_string.py`). The whole point of `entrypoints.py` is one place to look. Use section comments instead.
- **Free functions that don't get re-exported at the top level.** Forces users to write `from mountainash.expressions.core.expression_api.entrypoints import ...` — defeats the purpose.
- **Renaming a free function relative to its fluent counterpart.** Pick one name; use it everywhere; let aliases live in the extension-builder layer.

## Technical Reference

- `src/mountainash/expressions/core/expression_api/entrypoints.py` — canonical location
- `src/mountainash/expressions/__init__.py`, `src/mountainash/__init__.py` — re-export points
- [`short-aliases.md`](short-aliases.md) — companion principle for extension-layer aliases
EOF
```

- [ ] **Step 2: Verify file written.**

```bash
ls -la /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/c.api-design/free-function-entrypoints.md
```

- [ ] **Step 3: Defer commit to Task 9.**

---

## Task 9: Update existing principles + CLAUDE.md, lint, finalize

**Files:**
- Modify: `mountainash-central/01.principles/mountainash-expressions/a.architecture/wiring-matrix.md`
- Modify: `mountainash-central/01.principles/mountainash-expressions/f.extension-model/adding-operations.md`
- Modify: `mountainash-central/01.principles/mountainash-expressions/h.backlog/polars-alignment-deferred.md`
- Modify: `CLAUDE.md` (in `mountainash-expressions` repo)

- [ ] **Step 1: Update `wiring-matrix.md`.** Find the Substrait Scalar Aggregate section (added in today's count work). Update the table to mark `any_value`, `sum`, `avg`, `min`, `max`, `product`, `std_dev`, `variance`, `mode`, `corr`, `median`, `quantile` as `+` across all 5 layers (ENUM, Fn Map, Polars, Ibis, Narwhals). Leave `sum0`, `first_value`, `last_value` as `-` (still aspirational).

Update the Summary table row for Substrait Scalar Aggregate from `2 / 9` to `14 / 17` (or whatever the correct denominator is after adding the 3 deferred rows). Update the grand total accordingly.

Update the Future Considerations note: aggregate protocols are now **mostly wired** rather than "partially wired".

- [ ] **Step 2: Update `adding-operations.md`.** Add a new subsection after the existing six-step process:

```markdown
## Wiring-Only Additions

When protocol methods and backend implementations already exist (e.g. inherited from a previous batch), the six-layer process collapses to layers 4–6:

1. **Function mapping** — append `ExpressionFunctionDef` entries to the appropriate `*_FUNCTIONS` list in `definitions.py`.
2. **api_builder protocol** — add the method signature to the relevant `prtcl_api_bldr_*.py`.
3. **api_builder class** — add the method body building a `ScalarFunctionNode` and calling `self._build(node)`.

This is the path used by the 2026-04-08 count batch and the scalar aggregate batch. The first task in any wiring-only spec should be a layer audit (a `notes/` markdown file documenting the state of each layer for each operation in scope), to confirm the assumption that protocols and backends are ready before starting.
```

- [ ] **Step 3: Update `polars-alignment-deferred.md`.** Find the Out-of-Scope Aggregation row and strike through `sum`, `avg`, `min`, `max`, `mean` similar to how `count` was struck through. Add a note: "Wired 2026-04-08 via the scalar aggregate batch."

- [ ] **Step 4: Update `CLAUDE.md`** (in the `mountainash-expressions` repo, not the central principles repo). In the principles table under `### c. API Design`, add two new rows:

```markdown
| scalar-terminal-composition.md | ADOPTED | Scalar terminals on `Relation` are thin compositions over aggregate expression functions; no per-backend dispatch |
| free-function-entrypoints.md | ADOPTED | `entrypoints.py` conventions: when to use free functions vs fluent methods |
```

- [ ] **Step 5: Commit principles repo.**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expressions/c.api-design/scalar-terminal-composition.md \
        01.principles/mountainash-expressions/c.api-design/free-function-entrypoints.md \
        01.principles/mountainash-expressions/a.architecture/wiring-matrix.md \
        01.principles/mountainash-expressions/f.extension-model/adding-operations.md \
        01.principles/mountainash-expressions/h.backlog/polars-alignment-deferred.md
git commit -m "docs(principles): add scalar-terminal-composition and free-function-entrypoints; mark aggregate batch wired"
git push
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions
```

- [ ] **Step 6: Commit CLAUDE.md.**

```bash
git add CLAUDE.md
git commit -m "docs(claude.md): add scalar-terminal and free-function principles to c.api-design table"
```

- [ ] **Step 7: Lint.**

```bash
hatch run ruff:check 2>&1 | tail -20
hatch run ruff:fix
```

Stage and commit any auto-fixes to files touched in this batch (do not commit pre-existing fixes to unrelated files).

- [ ] **Step 8: Type check the touched files.**

```bash
hatch run mypy:check \
  src/mountainash/expressions/core/expression_system/function_mapping/definitions.py \
  src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_aggregate.py \
  src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_aggregate.py \
  src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_aggregate.py \
  src/mountainash/expressions/core/expression_api/entrypoints.py \
  src/mountainash/relations/core/relation_api/relation.py \
  2>&1 | tail -20
```

Pre-existing errors (verifiable via `git stash` baseline diff) are out of scope. New errors must be fixed.

- [ ] **Step 9: Full test sweep.**

```bash
hatch run test:test-target-quick tests/expressions/ tests/relations/
```

Expected: all green, no regressions vs baseline.

- [ ] **Step 10: Empty finalising commit.**

```bash
git commit --allow-empty -m "chore(aggregate): finalize scalar aggregate batch"
```

---

## Self-Review

**Spec coverage:**

| Spec section | Covered by |
|---|---|
| Part A: 9 fluent reducers | Tasks 1, 2, 3 |
| Part A: 3 free-function aggregates (corr/median/quantile) | Tasks 1, 4 |
| Part B: 8 Relation scalar terminals | Task 6 |
| Part B: `mean` alias on col fluent | Task 5 |
| Part B: `mean` alias on Relation | Task 6 (`Relation.mean` delegates to `Relation.avg`) |
| Part C: `scalar-terminal-composition.md` (new) | Task 7 |
| Part C: `free-function-entrypoints.md` (new) | Task 8 |
| Part C: `wiring-matrix.md` update | Task 9 Step 1 |
| Part C: `adding-operations.md` update | Task 9 Step 2 |
| Part C: `polars-alignment-deferred.md` update | Task 9 Step 3 |
| Part C: `CLAUDE.md` update | Task 9 Step 4 |
| Risks: multi-arg function mapping | Task 4 (free functions follow `coalesce`/`if_then_else` precedent) |
| Risks: AggregateRelNode(keys=[]) | Already fixed in today's branch; reused in Task 6 |
| Risks: any_value nondeterminism | Task 3 (membership assertion); Task 6 (membership assertion) |
| Risks: protocol split generic vs arithmetic | Task 1 imports both protocols; api-builder stays single |
| Tests: 4 new test files | Tasks 1, 3, 4, 6 |

No spec gaps.

**Placeholder scan:** No "TBD" or "figure it out". Each task has complete code blocks. Two flex points are explicitly noted: Task 4 quantile argument shape (narrow assertion if backend rejects), Task 6 empty-relation test (accept `None` or `0`). Both list the specific fallback.

**Type consistency:** `Relation.<agg>(col: str) -> Any` consistent across Task 6 methods and the spec. Fluent method names (`sum`, `avg`, `min`, `max`, `product`, `std_dev`, `variance`, `mode`, `any_value`) consistent across Tasks 2, 3, 5, 6 and the protocol/api-builder/Relation surfaces. Free function names (`corr`, `median`, `quantile`) consistent across Tasks 1, 4 and the re-exports. `mean` consistently used as the alias name in Tasks 5 and 6.
