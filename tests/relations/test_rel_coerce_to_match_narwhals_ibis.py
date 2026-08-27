"""`_coerce_to_match` non-Polars-target coercion (item 94).

`UnifiedRelationVisitor._coerce_to_match(target, value)` only implements a
conversion ladder for `target is Polars` (LazyFrame/DataFrame). For every
other target family -- Narwhals, Ibis -- it silently falls through to a
bare `return value`, passing the raw, unconverted value straight into the
eventual join/join_asof call, which then fails with a confusing native
error from deep inside that backend's own compiler.

Design: mountainash-central 2026-08-14-coerce-to-match-non-polars-target-
design.md (Revision 3, 3 Codex adversarial review rounds -- APPROVED).
"""
from __future__ import annotations

import ibis
import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from mountainash.relations.core.unified_visitor.relation_visitor import (
    UnifiedRelationVisitor,
)

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


def _nw_pandas(data: dict):
    return nw.from_native(pd.DataFrame(data), eager_only=True)


def _nw_polars(data: dict):
    return nw.from_native(pl.DataFrame(data), eager_only=True)


def _nw_pyarrow(data: dict):
    return nw.from_native(pa.table(data), eager_only=True)


IBIS_CONNECTORS = {
    "duckdb": lambda: ibis.duckdb.connect(),
    "polars": lambda: ibis.polars.connect(),
    "sqlite": lambda: ibis.sqlite.connect(":memory:"),
}


class TestIbisTargetDictAcceptance:
    """Item 94 acceptance test: confirmed live bug (design spec's
    'Empirical findings' section) -- an Ibis target + a raw dict right-hand
    value currently no-ops in `_coerce_to_match`, so the raw dict reaches
    Ibis's own join compiler and fails there with a confusing native
    error, never a clean, helpful `TypeError` from this codebase."""

    def test_join_coerces_dict_to_ibis_memtable_with_correct_data(self):
        con = ibis.duckdb.connect()
        left = con.create_table("t", {"id": [1, 2, 3], "a": ["x", "y", "z"]})
        right = {"id": [2, 3], "b": [10, 20]}

        result = (
            ma.relation(left)
            .join(right, on="id", how="inner")
            .sort("id")
            .to_polars()
        )
        assert result.to_dict(as_series=False) == {
            "id": [2, 3],
            "a": ["y", "z"],
            "b": [10, 20],
        }


class TestNarwhalsTargetEagerDialects:
    """Design spec testing plan #1-3: dict/list[dict]/Polars-LazyFrame right-
    hand values against all 3 eager Narwhals target dialects. Every "join
    succeeds" assertion checks correct data AND the result's exact dialect
    matches the target -- not merely "doesn't raise" (directly defends
    against Revision 1's finding-2 regression, where a `dict` always became
    pandas-backed regardless of the target's actual dialect)."""

    @pytest.mark.parametrize(
        "target_factory,target_dialect",
        [
            (lambda: _nw_pandas({"id": [1, 2, 3], "a": ["x", "y", "z"]}), "narwhals-pandas"),
            (lambda: _nw_polars({"id": [1, 2, 3], "a": ["x", "y", "z"]}), "narwhals-polars"),
            (lambda: _nw_pyarrow({"id": [1, 2, 3], "a": ["x", "y", "z"]}), "narwhals-pyarrow"),
        ],
    )
    @pytest.mark.parametrize(
        "value_factory",
        [
            lambda: {"id": [2, 3], "b": [10, 20]},
            lambda: [{"id": 2, "b": 10}, {"id": 3, "b": 20}],
            lambda: pl.DataFrame({"id": [2, 3], "b": [10, 20]}).lazy(),
        ],
        ids=["dict", "list_of_dict", "polars_lazyframe"],
    )
    def test_join_matches_target_dialect_exactly(
        self, target_factory, target_dialect, value_factory
    ):
        from mountainash.core.backend_detection import narwhals_dialect

        target = target_factory()
        value = value_factory()
        coerced = UnifiedRelationVisitor._coerce_to_match(target, value)
        assert narwhals_dialect(coerced) == target_dialect
        rel = ma.relation(target).join(value, on="id", how="inner")
        result, visitor = rel._compile_and_execute_with_visitor()
        assert visitor.backend.dialect == target_dialect
        # Assert the compiled RESULT (not just the coerced operand) is a
        # narwhals frame of the target's exact dialect, then verify the
        # complete joined record set (id, a, b -- not just id, b).
        assert narwhals_dialect(result) == target_dialect
        d = result.to_dict(as_series=False)
        rows = sorted(zip(d["id"], d["a"], d["b"]))
        assert rows == [(2, "y", 10), (3, "z", 20)]


class TestIbisTableToNarwhalsTarget:
    """Design spec testing plan #4: an Ibis Table right-hand value against a
    Narwhals target materializes via .to_pyarrow() (the same duck-type
    pattern the pre-existing Polars branch already uses) then wraps -- this
    replaces Revision 1's incorrect rejection of Ibis-Table-to-Narwhals."""

    @pytest.mark.parametrize(
        "target_factory,target_dialect",
        [
            (lambda: _nw_pandas({"id": [1, 2, 3], "a": ["x", "y", "z"]}), "narwhals-pandas"),
            (lambda: _nw_polars({"id": [1, 2, 3], "a": ["x", "y", "z"]}), "narwhals-polars"),
        ],
    )
    def test_ibis_table_materializes_to_target_dialect(self, target_factory, target_dialect):
        from mountainash.core.backend_detection import narwhals_dialect

        target = target_factory()
        con = ibis.duckdb.connect()
        value = con.create_table("t", {"id": [2, 3], "b": [10, 20]})
        coerced = UnifiedRelationVisitor._coerce_to_match(target, value)
        assert narwhals_dialect(coerced) == target_dialect
        rel = ma.relation(target).join(value, on="id", how="inner")
        result, visitor = rel._compile_and_execute_with_visitor()
        assert visitor.backend.dialect == target_dialect
        assert narwhals_dialect(result) == target_dialect
        d = result.to_dict(as_series=False)
        rows = sorted(zip(d["id"], d["a"], d["b"]))
        assert rows == [(2, "y", 10), (3, "z", 20)]


class TestLazyNarwhalsTargetRejectsEagerOperand:
    """Design spec testing plan #5: a lazy Narwhals target + an eager (or
    differently-shaped) value raises _coerce_same_family_dialect's own
    already-reviewed TypeError -- item 91's documented limitation, not a
    new regression introduced by this item's Narwhals branch."""

    @pytest.mark.parametrize(
        "value_factory",
        [
            lambda: {"id": [1]},
            lambda: [{"id": 1}],
            lambda: pl.DataFrame({"id": [1]}).lazy(),
        ],
        ids=["dict", "list_of_dict", "polars_lazyframe"],
    )
    def test_lazy_target_raises_lazy_typeerror(self, value_factory):
        target = _nw_pandas({"id": [1, 2]}).lazy()
        with pytest.raises(TypeError, match="lazy"):
            UnifiedRelationVisitor._coerce_to_match(target, value_factory())


class TestJoinAsofNarwhalsTargetDictValue:
    """Design spec testing plan #6: join_asof, Narwhals target, dict
    right-hand value, parameterized over pandas and Polars target dialects.
    PyArrow-backed narwhals is excluded -- narwhals itself raises its own
    pre-existing, unrelated NotImplementedError for join_asof on a PyArrow
    implementation (confirmed via probe), a genuine upstream limitation
    this item does not attempt to lift."""

    @pytest.mark.parametrize(
        "target_factory,expected_type",
        [(_nw_pandas, pd.DataFrame), (_nw_polars, pl.DataFrame)],
        ids=["pandas", "polars"],
    )
    def test_join_asof_coerces_dict_right_hand_side(self, target_factory, expected_type):
        left = target_factory({"id": [1, 3, 5], "a": ["x", "y", "z"]})
        right = {"id": [1, 2, 4], "b": [10, 20, 30]}
        rel = ma.relation(left).join_asof(right, on="id", strategy="backward")
        result = rel.collect()
        # Tie the collected result to the EXPECTED native type before
        # serializing: a narwhals-pandas .collect() yields a raw
        # pandas.DataFrame, a narwhals-polars .collect() a raw
        # polars.DataFrame. Assert the type explicitly (sniffing the
        # object could not catch an accidental cross-dialect result),
        # then serialize per that type.
        assert isinstance(result, expected_type)
        to_dict = (
            result.to_dict(orient="list")
            if expected_type is pd.DataFrame
            else result.to_dict(as_series=False)
        )
        assert to_dict == {"id": [1, 3, 5], "a": ["x", "y", "z"], "b": [10, 20, 30]}


class TestScalarListRejectedAgainstNarwhalsTarget:
    """Design spec testing plan #7: a scalar (non-dict) list/tuple right-
    hand value against a Narwhals target must NOT take the dict-sequence
    fast path (narrowed predicate) -- it falls through to the generic
    nw.from_native() fallback, which raises its own clean TypeError citing
    the original list type."""

    def test_scalar_list_falls_through_to_narwhals_native_rejection(self):
        target = _nw_pandas({"id": [1, 2]})
        with pytest.raises(TypeError, match="Cannot coerce list to Narwhals"):
            UnifiedRelationVisitor._coerce_to_match(target, [1, 2])


@pytest.fixture(params=["duckdb", "polars", "sqlite"])
def ibis_anchor(request):
    """An Ibis Table anchor, one per registered dialect. Built from a
    Polars DataFrame, not a raw dict -- the ibis-polars backend's
    create_table() rejects a raw dict directly (confirmed via probe:
    NotImplementedError: The `polars` backend currently does not support
    reading data of <class 'dict'>), while duckdb/sqlite accept either."""
    con = IBIS_CONNECTORS[request.param]()
    anchor_df = pl.DataFrame({"id": [1, 2, 3], "a": ["x", "y", "z"]})
    return con.create_table("anchor", anchor_df)


class TestIbisTargetAllValueShapes:
    """Design spec testing plan #8-14: 7 value shapes x 3 registered Ibis
    dialects (duckdb/polars/sqlite) = 21 tests. Every case asserts
    ibis.memtable() succeeds and produces the correct rows."""

    def _assert_correct(self, coerced):
        assert isinstance(coerced, ibis.expr.types.Table)
        df = coerced.to_pandas()
        rows = sorted(zip(df["id"].tolist(), df["b"].tolist()))
        assert rows == [(2, 10), (3, 20)]

    def test_pandas_dataframe(self, ibis_anchor):
        value = pd.DataFrame({"id": [2, 3], "b": [10, 20]})
        self._assert_correct(UnifiedRelationVisitor._coerce_to_match(ibis_anchor, value))

    def test_polars_dataframe_eager(self, ibis_anchor):
        value = pl.DataFrame({"id": [2, 3], "b": [10, 20]})
        self._assert_correct(UnifiedRelationVisitor._coerce_to_match(ibis_anchor, value))

    def test_polars_lazyframe(self, ibis_anchor):
        value = pl.DataFrame({"id": [2, 3], "b": [10, 20]}).lazy()
        self._assert_correct(UnifiedRelationVisitor._coerce_to_match(ibis_anchor, value))

    def test_pyarrow_table(self, ibis_anchor):
        value = pa.table({"id": [2, 3], "b": [10, 20]})
        self._assert_correct(UnifiedRelationVisitor._coerce_to_match(ibis_anchor, value))

    def test_dict(self, ibis_anchor):
        value = {"id": [2, 3], "b": [10, 20]}
        self._assert_correct(UnifiedRelationVisitor._coerce_to_match(ibis_anchor, value))

    def test_list_of_dict(self, ibis_anchor):
        value = [{"id": 2, "b": 10}, {"id": 3, "b": 20}]
        self._assert_correct(UnifiedRelationVisitor._coerce_to_match(ibis_anchor, value))

    def test_already_narwhals_wrapped_eager_and_lazy(self, ibis_anchor):
        """Directly defends against Revision 1's finding-3 regression:
        ibis.memtable() fails for a LAZY narwhals wrapper unless unwrapped
        via .to_native() first; an EAGER wrapper needs no unwrapping."""
        eager_pandas = _nw_pandas({"id": [2, 3], "b": [10, 20]})
        self._assert_correct(
            UnifiedRelationVisitor._coerce_to_match(ibis_anchor, eager_pandas)
        )
        lazy_pandas = _nw_pandas({"id": [2, 3], "b": [10, 20]}).lazy()
        self._assert_correct(
            UnifiedRelationVisitor._coerce_to_match(ibis_anchor, lazy_pandas)
        )
        lazy_polars = _nw_polars({"id": [2, 3], "b": [10, 20]}).lazy()
        self._assert_correct(
            UnifiedRelationVisitor._coerce_to_match(ibis_anchor, lazy_polars)
        )


class TestErrorWrappingPreservesOriginalTypeAndContext:
    """Design spec testing plan #15-17."""

    def test_narwhals_conversion_failure_wraps_original_source_type(self):
        """Task 5: a dict operand now builds the target-native Narwhals
        frame directly via ``nw.from_dict(..., backend=target_namespace)``
        (never a pandas intermediate). Force-fail that call via mock -- the
        wrapped TypeError must cite the ORIGINAL raw type (dict), proving
        source_type was captured before the attempt."""
        from unittest.mock import patch

        target = _nw_pandas({"id": [1, 2]})
        with patch("narwhals.from_dict", side_effect=RuntimeError("boom")):
            with pytest.raises(TypeError, match=r"Cannot coerce dict to Narwhals.*boom"):
                UnifiedRelationVisitor._coerce_to_match(target, {"id": [1]})

    def test_ibis_conversion_failure_wraps_custom_class_name(self):
        class NotConvertible:
            pass

        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        with pytest.raises(
            TypeError,
            match=r"Cannot coerce NotConvertible to Ibis.*DataFrame constructor not properly called",
        ):
            UnifiedRelationVisitor._coerce_to_match(target, NotConvertible())

    def test_final_branch_rejects_object_satisfying_only_permissive_detection(self):
        """A duck-typed object exposing `_compliant_frame` (narwhals' own
        permissive identify_backend()/read() detection signal) but failing
        the strict is_narwhals_dataframe/is_narwhals_lazyframe TypeGuards
        must raise a clean TypeError from the final branch -- a deliberate
        compatibility tightening vs. the prior accidental pass-through."""

        class Spoof:
            _compliant_frame = object()

        with pytest.raises(
            TypeError, match=r"Cannot coerce dict to unrecognized target type Spoof"
        ):
            UnifiedRelationVisitor._coerce_to_match(Spoof(), {"id": [1]})


class TestDegenerateInputCoverage:
    """Design spec testing plan #18 (expanded per Round 3's non-blocking
    note): empty/null-only/typed-empty inputs, and an unresolvable lazy
    source, against both a Narwhals and an Ibis target. Coercion's job is
    type conversion, not schema validation -- these assert either a
    legitimate degenerate result or a clean, appropriately-wrapped
    TypeError, never a silent no-op or data corruption."""

    def test_empty_dict_to_narwhals_succeeds_zero_columns(self):
        target = _nw_pandas({"id": [1, 2]})
        coerced = UnifiedRelationVisitor._coerce_to_match(target, {})
        assert coerced.to_native().shape == (0, 0)

    def test_empty_list_to_narwhals_succeeds_zero_columns(self):
        target = _nw_pandas({"id": [1, 2]})
        coerced = UnifiedRelationVisitor._coerce_to_match(target, [])
        assert coerced.to_native().shape == (0, 0)

    def test_empty_dict_to_ibis_succeeds_zero_columns(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        coerced = UnifiedRelationVisitor._coerce_to_match(target, {})
        assert coerced.schema() == ibis.schema({})

    def test_empty_list_to_ibis_succeeds_zero_columns(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        coerced = UnifiedRelationVisitor._coerce_to_match(target, [])
        # Zero-column table: assert the schema, do NOT execute (executing a
        # zero-column table raises a backend-level error -- out of scope).
        assert coerced.schema() == ibis.schema({})

    def test_null_only_polars_lazyframe_to_ibis_succeeds(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        value = pl.DataFrame({"id": [None, None]}, schema={"id": pl.Int64}).lazy()
        coerced = UnifiedRelationVisitor._coerce_to_match(target, value)
        assert coerced.count().to_pandas() == 2

    def test_typed_empty_polars_lazyframe_to_ibis_succeeds(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        value = pl.DataFrame({"id": []}, schema={"id": pl.Int64}).lazy()
        coerced = UnifiedRelationVisitor._coerce_to_match(target, value)
        assert coerced.count().to_pandas() == 0

    def test_null_only_dict_to_narwhals_succeeds(self):
        target = _nw_pandas({"id": [1, 2]})
        coerced = UnifiedRelationVisitor._coerce_to_match(target, {"id": [None, None]})
        assert coerced.to_native().to_dict(orient="list")["id"] == [None, None] or all(
            pd.isna(v) for v in coerced.to_native()["id"]
        )

    def test_null_only_dict_to_ibis_succeeds(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        coerced = UnifiedRelationVisitor._coerce_to_match(target, {"id": [None, None]})
        assert coerced.count().to_pandas() == 2

    def test_null_only_polars_lazyframe_to_narwhals_succeeds(self):
        target = _nw_pandas({"id": [1, 2]})
        value = pl.DataFrame({"id": [None, None]}, schema={"id": pl.Int64}).lazy()
        coerced = UnifiedRelationVisitor._coerce_to_match(target, value)
        assert coerced.to_native().shape == (2, 1)

    def test_typed_empty_polars_lazyframe_to_narwhals_succeeds(self):
        target = _nw_pandas({"id": [1, 2]})
        value = pl.DataFrame({"id": []}, schema={"id": pl.Int64}).lazy()
        coerced = UnifiedRelationVisitor._coerce_to_match(target, value)
        assert coerced.to_native().shape == (0, 1)

    def test_unresolvable_lazy_source_to_narwhals_raises_wrapped_typeerror(self):
        target = _nw_pandas({"id": [1, 2]})
        value = pl.scan_csv("/tmp/mountainash-item94-does-not-exist.csv")
        with pytest.raises(TypeError, match="Cannot coerce LazyFrame to Narwhals"):
            UnifiedRelationVisitor._coerce_to_match(target, value)

    def test_unresolvable_lazy_source_to_ibis_raises_wrapped_typeerror(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        value = pl.scan_csv("/tmp/mountainash-item94-does-not-exist.csv")
        with pytest.raises(TypeError, match="Cannot coerce LazyFrame to Ibis"):
            UnifiedRelationVisitor._coerce_to_match(target, value)
