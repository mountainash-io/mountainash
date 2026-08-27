"""Union (concat) cross-family raw-value coercion (item 96)."""
from __future__ import annotations

import pandas as pd
import polars as pl

import mountainash as ma

import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


class TestUnionCrossFamilyCoercionAcceptance:
    def test_concat_polars_anchor_coerces_pandas_operand(self):
        left = pl.DataFrame({"k": [1, 2]})
        right = pd.DataFrame({"k": [3, 4]})
        result = ma.concat([ma.relation(left), ma.relation(right)]).to_polars()
        assert result.to_dict(as_series=False) == {"k": [1, 2, 3, 4]}

import ibis
import narwhals as nw
import pyarrow as pa
import pytest

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.backend_detection import narwhals_dialect


def _nw_pandas(data: dict):
    return nw.from_native(pd.DataFrame(data), eager_only=True)


def _nw_polars(data: dict):
    return nw.from_native(pl.DataFrame(data), eager_only=True)


def _nw_pyarrow(data: dict):
    return nw.from_native(pa.table(data), eager_only=True)


def _nw_lazy_polars(data: dict):
    return nw.from_native(pl.DataFrame(data).lazy())


class TestPolarsAnchorCrossFamily:
    @pytest.mark.parametrize(
        "operand_factory",
        [
            lambda: pd.DataFrame({"k": [3, 4]}),
            lambda: pa.table({"k": [3, 4]}),
            lambda: ibis.memtable({"k": [3, 4]}),
            lambda: _nw_pandas({"k": [3, 4]}),
            lambda: _nw_polars({"k": [3, 4]}),
            lambda: _nw_pyarrow({"k": [3, 4]}),
        ],
        ids=["pandas", "pyarrow", "ibis", "nw-pandas", "nw-polars", "nw-pyarrow"],
    )
    @pytest.mark.parametrize("distinct", [False, True])
    def test_concat_coerces_operand_to_polars(self, operand_factory, distinct):
        left = pl.DataFrame({"k": [1, 2]})
        rel = ma.concat([ma.relation(left), ma.relation(operand_factory())], distinct=distinct)
        _, visitor = rel._compile_and_execute_with_visitor()
        assert visitor.backend.backend_type is CONST_BACKEND.POLARS
        got = rel.to_polars().to_dict(as_series=False)["k"]
        if distinct:
            assert sorted(got) == [1, 2, 3, 4]
        else:
            assert got == [1, 2, 3, 4]


class TestIbisAnchorCrossFamily:
    @pytest.mark.parametrize(
        "operand_factory",
        [
            lambda: pd.DataFrame({"k": [3, 4]}),
            lambda: pl.DataFrame({"k": [3, 4]}),
            lambda: pa.table({"k": [3, 4]}),
            lambda: _nw_pandas({"k": [3, 4]}),
            lambda: _nw_polars({"k": [3, 4]}),
            lambda: _nw_pyarrow({"k": [3, 4]}),
            lambda: _nw_lazy_polars({"k": [3, 4]}),
        ],
        ids=["pandas", "polars", "pyarrow", "nw-pandas", "nw-polars", "nw-pyarrow",
             "nw-lazy-polars"],
    )
    @pytest.mark.parametrize("distinct", [False, True])
    def test_concat_coerces_operand_to_ibis(self, operand_factory, distinct):
        con = ibis.duckdb.connect()
        left = con.create_table("t", {"k": [1, 2]})
        rel = ma.concat([ma.relation(left), ma.relation(operand_factory())], distinct=distinct)
        _, visitor = rel._compile_and_execute_with_visitor()
        assert visitor.backend.backend_type is CONST_BACKEND.IBIS
        got = rel.to_polars().to_dict(as_series=False)["k"]
        if distinct:
            assert sorted(got) == [1, 2, 3, 4]
        else:
            assert got == [1, 2, 3, 4]


class TestNarwhalsAnchorCrossFamily:
    @pytest.mark.parametrize(
        "anchor_factory,anchor_dialect",
        [
            (lambda: _nw_pandas({"k": [1, 2]}), "narwhals-pandas"),
            (lambda: _nw_polars({"k": [1, 2]}), "narwhals-polars"),
            (lambda: _nw_pyarrow({"k": [1, 2]}), "narwhals-pyarrow"),
        ],
    )
    @pytest.mark.parametrize("distinct", [False, True])
    def test_concat_coerces_ibis_operand_to_anchor_dialect(
        self, anchor_factory, anchor_dialect, distinct
    ):
        anchor = anchor_factory()
        rel = ma.concat([ma.relation(anchor), ma.relation(ibis.memtable({"k": [3, 4]}))],
                        distinct=distinct)
        result, visitor = rel._compile_and_execute_with_visitor()
        assert visitor.backend.dialect == anchor_dialect
        assert narwhals_dialect(result) == anchor_dialect
        got = result.to_dict(as_series=False)["k"]
        if distinct:
            assert sorted(got) == [1, 2, 3, 4]
        else:
            assert got == [1, 2, 3, 4]


class TestSameFamilyRegression:
    def test_narwhals_pandas_polars_unchanged(self):
        rel = ma.concat([ma.relation(_nw_pandas({"k": [1, 2]})),
                         ma.relation(_nw_polars({"k": [3, 4]}))])
        assert rel.to_polars().to_dict(as_series=False) == {"k": [1, 2, 3, 4]}

    def test_narwhals_pandas_raw_pandas_unchanged(self):
        rel = ma.concat([ma.relation(_nw_pandas({"k": [1, 2]})),
                         ma.relation(pd.DataFrame({"k": [3, 4]}))])
        assert rel.to_polars().to_dict(as_series=False) == {"k": [1, 2, 3, 4]}


class TestThreeWayMix:
    def test_concat_mixes_three_families(self):
        rel = ma.concat([
            ma.relation(pl.DataFrame({"k": [1]})),
            ma.relation(pd.DataFrame({"k": [2]})),
            ma.relation(pa.table({"k": [3]})),
        ])
        _, visitor = rel._compile_and_execute_with_visitor()
        assert visitor.backend.backend_type is CONST_BACKEND.POLARS
        assert sorted(rel.to_polars().to_dict(as_series=False)["k"]) == [1, 2, 3]


class TestUnionDistinctDedup:
    def test_distinct_dedupes_across_families(self):
        rel = ma.concat([ma.relation(pl.DataFrame({"k": [1, 2]})),
                         ma.relation(pd.DataFrame({"k": [2, 3]}))], distinct=True)
        assert sorted(rel.to_polars().to_dict(as_series=False)["k"]) == [1, 2, 3]


class TestBoundaries:
    def test_derived_foreign_operand_is_not_rescued(self):
        with pytest.raises(TypeError):
            ma.concat([ma.relation(pl.DataFrame({"k": [1]})),
                       ma.relation(pd.DataFrame({"k": [2, 3]})).filter(ma.col("k") > 0),
                       ]).to_polars()

    def test_lazy_narwhals_anchor_boundary_raises_clean_typeerror(self):
        lazy_anchor = _nw_lazy_polars({"k": [1]})
        with pytest.raises(TypeError):
            ma.concat([ma.relation(lazy_anchor),
                       ma.relation(ibis.memtable({"k": [2]}))]).to_polars()

    def test_lazy_narwhals_operand_polars_anchor_coerces_via_collect(self):
        """Task 5: the Polars-target adapter now handles a lazy Narwhals
        operand by collecting it (NARWHALS_LAZY_COLLECT) then converting via
        its declared to_polars() route -- no longer an accidental gap."""
        lazy_operand = _nw_lazy_polars({"k": [3, 4]})
        result = ma.concat([ma.relation(pl.DataFrame({"k": [1, 2]})),
                             ma.relation(lazy_operand)]).to_polars()
        assert sorted(result.to_dict(as_series=False)["k"]) == [1, 2, 3, 4]
