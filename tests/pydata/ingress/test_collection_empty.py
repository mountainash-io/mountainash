"""Empty collections ingress as columnless frames, not a fabricated 'value' column."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.pydata.ingress.pydata_ingress import PydataIngress


@pytest.mark.parametrize("empty", [[], set(), frozenset()])
def test_empty_collection_is_columnless(empty):
    df = PydataIngress.convert(empty)
    assert isinstance(df, pl.DataFrame)
    assert df.shape == (0, 0)
    assert df.columns == []


def test_populated_collection_unchanged():
    df = PydataIngress.convert([1, 2, 3])
    assert df.shape == (3, 1)
    assert df.columns == ["value"]
