"""Descending window order is refused on native Dask frames routed as narwhals-dask."""

from __future__ import annotations

import dask.dataframe as dd
import pandas as pd
import narwhals as nw
import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError


_DESCENDING = ["a", "-b"]
_ORDER_DEPENDENT = [
    lambda c: c.cum_sum(),
    lambda c: c.cum_max(),
    lambda c: c.cum_min(),
    lambda c: c.cum_count(),
    lambda c: c.cum_prod(),
    lambda c: c.diff(),
    lambda c: c.forward_fill(),
    lambda c: c.backward_fill(),
    lambda c: c.lag(1),
    lambda c: c.lead(1),
    lambda c: c.first_value(),
    lambda c: c.last_value(),
    lambda c: c.nth_value(2),
]


@pytest.fixture
def dask_frame():
    source = dd.from_pandas(
        pd.DataFrame({"g": [1, 1, 1, 1], "a": [1, 1, 2, 2], "b": [2, 1, 2, 1], "v": [1, 2, 3, 4]}),
        npartitions=2,
    )
    return nw.from_native(source)


@pytest.mark.parametrize("build", _ORDER_DEPENDENT)
def test_dask_descending_order_refused_at_gate(dask_frame, build):
    expr = build(ma.col("v")).over("g", order_by=_DESCENDING)
    with pytest.raises(BackendCapabilityError, match="descending window order is unsupported"):
        ma.relation(dask_frame).select(expr.alias("r")).compile()
