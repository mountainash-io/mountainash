"""Cross-family operands of non-Polars anchors (item 94).

A join/union operand of another family must reach an Ibis or Narwhals anchor
as a value of the anchor's own family, never as a raw value handed to that
backend's join compiler. The scenarios run through public ``join``/``concat``;
degenerate shapes and error wrapping go through the shared
``TransportSession.transfer_native`` seam.

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
from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
from mountainash.relations.core.execution.transport import TransportSession

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
    "sqlite": lambda: ibis.sqlite.connect(":memory:"),
}


def _move(target, value):
    """Transfer *value* to the location of the native *target* (the unprepared-operand seam)."""
    transport = TransportSession(IdentityTokens())
    try:
        return transport.transfer_native(value, LocationResolver(transport.tokens)._read(target))
    finally:
        transport.close(release_owned=False)


class TestIbisTargetDictAcceptance:
    """Item 94 acceptance test: an Ibis anchor + a raw dict right-hand value
    joins with correct data, never a confusing native join-compiler error."""

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
    """dict/list[dict]/Polars-LazyFrame right-hand values against all 3 eager
    Narwhals anchor dialects. Every assertion checks correct data AND that
    the result's exact dialect matches the anchor."""

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
        rel = ma.relation(target).join(value, on="id", how="inner")
        result, visitor = rel._compile_and_execute_with_visitor()
        assert visitor.backend.dialect == target_dialect
        assert narwhals_dialect(result) == target_dialect
        d = result.to_dict(as_series=False)
        rows = sorted(zip(d["id"], d["a"], d["b"]))
        assert rows == [(2, "y", 10), (3, "z", 20)]

    @pytest.mark.parametrize(
        "value_factory",
        [
            lambda: {"id": [4], "a": ["w"]},
            lambda: [{"id": 4, "a": "w"}],
            lambda: pl.DataFrame({"id": [4], "a": ["w"]}).lazy(),
        ],
        ids=["dict", "list_of_dict", "polars_lazyframe"],
    )
    def test_concat_matches_target_dialect_exactly(self, value_factory):
        from mountainash.core.backend_detection import narwhals_dialect

        target = _nw_polars({"id": [1], "a": ["x"]})
        result = ma.concat([ma.relation(target), ma.relation(value_factory())]).collect()
        assert narwhals_dialect(nw.from_native(result)) == "narwhals-polars"
        assert sorted(result.to_dict(as_series=False)["id"]) == [1, 4]


class TestIbisTableToNarwhalsTarget:
    """An Ibis Table right-hand value against a Narwhals anchor executes at
    its own source and arrives in the anchor's dialect."""

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
        rel = ma.relation(target).join(value, on="id", how="inner")
        result, visitor = rel._compile_and_execute_with_visitor()
        assert visitor.backend.dialect == target_dialect
        assert narwhals_dialect(result) == target_dialect
        d = result.to_dict(as_series=False)
        rows = sorted(zip(d["id"], d["a"], d["b"]))
        assert rows == [(2, "y", 10), (3, "z", 20)]


class TestLazyNarwhalsTargetImportsEagerOperand:
    """A raw or Polars operand joined onto a lazy Narwhals frame is imported
    into the frame's implementation in lazy form and joined there."""

    @pytest.mark.parametrize(
        "value_factory",
        [
            lambda: {"id": [1]},
            lambda: [{"id": 1}],
            lambda: pl.DataFrame({"id": [1]}).lazy(),
        ],
        ids=["dict", "list_of_dict", "polars_lazyframe"],
    )
    def test_lazy_target_joins_imported_operand(self, value_factory):
        target = _nw_pandas({"id": [1, 2]}).lazy()
        out = ma.relation(target).join(value_factory(), on="id").to_polars()
        assert out.to_dict(as_series=False) == {"id": [1]}


class TestJoinAsofNarwhalsTargetDictValue:
    """join_asof, Narwhals anchor, dict right-hand value, over pandas and
    Polars anchor dialects (PyArrow-backed narwhals has no upstream join_asof)."""

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
        assert isinstance(result, expected_type)
        to_dict = (
            result.to_dict(orient="list")
            if expected_type is pd.DataFrame
            else result.to_dict(as_series=False)
        )
        assert to_dict == {"id": [1, 3, 5], "a": ["x", "y", "z"], "b": [10, 20, 30]}


class TestScalarListRejectedAgainstNarwhalsTarget:
    """A scalar (non-dict) list right-hand value is not row ingress and must
    not be treated as one."""

    def test_scalar_list_is_rejected(self):
        target = _nw_pandas({"id": [1, 2]})
        with pytest.raises(TypeError):
            ma.relation(target).join([1, 2], on="id").collect()


@pytest.fixture(params=["duckdb", "sqlite"])
def ibis_anchor(request):
    """An Ibis Table anchor, one per tested SQL dialect, built from a Polars frame."""
    con = IBIS_CONNECTORS[request.param]()
    anchor_df = pl.DataFrame({"id": [1, 2, 3], "a": ["x", "y", "z"]})
    return con.create_table("anchor", anchor_df)


class TestIbisTargetAllValueShapes:
    """7 value shapes x the registered Ibis dialects: each joins to the
    Ibis anchor with correct rows."""

    def _assert_correct(self, anchor, value):
        result = ma.relation(anchor).join(value, on="id", how="inner").sort("id").to_polars()
        assert result.to_dict(as_series=False) == {"id": [2, 3], "a": ["y", "z"], "b": [10, 20]}

    def test_pandas_dataframe(self, ibis_anchor):
        self._assert_correct(ibis_anchor, pd.DataFrame({"id": [2, 3], "b": [10, 20]}))

    def test_polars_dataframe_eager(self, ibis_anchor):
        self._assert_correct(ibis_anchor, pl.DataFrame({"id": [2, 3], "b": [10, 20]}))

    def test_polars_lazyframe(self, ibis_anchor):
        self._assert_correct(ibis_anchor, pl.DataFrame({"id": [2, 3], "b": [10, 20]}).lazy())

    def test_pyarrow_table(self, ibis_anchor):
        self._assert_correct(ibis_anchor, pa.table({"id": [2, 3], "b": [10, 20]}))

    def test_dict(self, ibis_anchor):
        self._assert_correct(ibis_anchor, {"id": [2, 3], "b": [10, 20]})

    def test_list_of_dict(self, ibis_anchor):
        self._assert_correct(ibis_anchor, [{"id": 2, "b": 10}, {"id": 3, "b": 20}])

    def test_already_narwhals_wrapped_eager_and_lazy(self, ibis_anchor):
        """ibis.memtable() fails for a LAZY narwhals wrapper unless it is
        exported first; an eager wrapper must work too."""
        self._assert_correct(ibis_anchor, _nw_pandas({"id": [2, 3], "b": [10, 20]}))
        self._assert_correct(ibis_anchor, _nw_pandas({"id": [2, 3], "b": [10, 20]}).lazy())
        self._assert_correct(ibis_anchor, _nw_polars({"id": [2, 3], "b": [10, 20]}).lazy())


class TestErrorWrappingPreservesOriginalTypeAndContext:
    """A destination that cannot store or build the value raises the typed
    transfer refusal carrying the source and destination context."""

    def test_narwhals_conversion_failure_wraps_original_cause(self):
        from unittest.mock import patch

        from mountainash.relations.core.errors import UnsupportedRelationTransportError

        target = _nw_polars({"id": [1, 2]})
        with patch("narwhals.from_arrow", side_effect=ValueError("boom")):
            with pytest.raises(UnsupportedRelationTransportError) as caught:
                _move(target, {"id": [1]})
        assert isinstance(caught.value.__cause__, ValueError)
        assert caught.value.destination_dialect == "narwhals-polars"

    def test_ibis_conversion_failure_wraps_original_cause(self):
        from unittest.mock import patch

        from mountainash.relations.core.errors import UnsupportedRelationTransportError

        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        with patch("ibis.memtable", side_effect=ValueError("not storable")):
            with pytest.raises(UnsupportedRelationTransportError) as caught:
                _move(target, {"id": [1]})
        assert caught.value.destination_dialect == "ibis-duckdb"

    def test_unrecognised_operand_is_rejected(self):
        class NotConvertible:
            pass

        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        with pytest.raises(Exception, match="Cannot identify backend"):
            _move(target, NotConvertible())


class TestDegenerateInputCoverage:
    """Empty/null-only/typed-empty inputs, and an unresolvable lazy source,
    against both a Narwhals and an Ibis destination: a legitimate degenerate
    result or a clean error, never a silent no-op or data corruption."""

    def test_empty_dict_to_narwhals_succeeds_zero_columns(self):
        coerced = _move(_nw_pandas({"id": [1, 2]}), {})
        assert coerced.to_native().shape == (0, 0)

    def test_empty_list_to_narwhals_succeeds_zero_columns(self):
        coerced = _move(_nw_pandas({"id": [1, 2]}), [])
        assert coerced.to_native().shape == (0, 0)

    def test_empty_dict_to_ibis_succeeds_zero_columns(self):
        con = ibis.duckdb.connect()
        coerced = _move(con.create_table("t", {"id": [1]}), {})
        assert coerced.schema() == ibis.schema({})

    def test_empty_list_to_ibis_succeeds_zero_columns(self):
        con = ibis.duckdb.connect()
        coerced = _move(con.create_table("t", {"id": [1]}), [])
        # Zero-column table: assert the schema, do NOT execute.
        assert coerced.schema() == ibis.schema({})

    def test_null_only_polars_lazyframe_to_ibis_succeeds(self):
        con = ibis.duckdb.connect()
        value = pl.DataFrame({"id": [None, None]}, schema={"id": pl.Int64}).lazy()
        assert _move(con.create_table("t", {"id": [1]}), value).count().to_pandas() == 2

    def test_typed_empty_polars_lazyframe_to_ibis_succeeds(self):
        con = ibis.duckdb.connect()
        value = pl.DataFrame({"id": []}, schema={"id": pl.Int64}).lazy()
        assert _move(con.create_table("t", {"id": [1]}), value).count().to_pandas() == 0

    def test_null_only_dict_to_narwhals_succeeds(self):
        coerced = _move(_nw_pandas({"id": [1, 2]}), {"id": [None, None]})
        assert all(pd.isna(v) for v in coerced.to_native()["id"])

    def test_null_only_dict_to_ibis_succeeds(self):
        con = ibis.duckdb.connect()
        coerced = _move(con.create_table("t", {"id": [1]}), {"id": [None, None]})
        assert coerced.count().to_pandas() == 2

    def test_null_only_polars_lazyframe_to_narwhals_succeeds(self):
        value = pl.DataFrame({"id": [None, None]}, schema={"id": pl.Int64}).lazy()
        assert _move(_nw_pandas({"id": [1, 2]}), value).to_native().shape == (2, 1)

    def test_typed_empty_polars_lazyframe_to_narwhals_succeeds(self):
        value = pl.DataFrame({"id": []}, schema={"id": pl.Int64}).lazy()
        assert _move(_nw_pandas({"id": [1, 2]}), value).to_native().shape == (0, 1)

    def test_unresolvable_lazy_source_to_narwhals_raises(self):
        value = pl.scan_csv("/tmp/mountainash-item94-does-not-exist.csv")
        with pytest.raises(Exception):
            _move(_nw_pandas({"id": [1, 2]}), value)

    def test_unresolvable_lazy_source_to_ibis_raises(self):
        con = ibis.duckdb.connect()
        value = pl.scan_csv("/tmp/mountainash-item94-does-not-exist.csv")
        with pytest.raises(Exception):
            _move(con.create_table("t", {"id": [1]}), value)
