# tests/fixtures/test_backend_helpers.py
"""Self-tests for BackendDataFrameFactory (backend_helpers.py)."""
from __future__ import annotations
import datetime as dt

import pytest

from .backend_helpers import BackendDataFrameFactory, BackendResultHelper
from .backend_registry import ALL_BACKENDS


# Same shape as test_backend_registry.py's NULL_TEMPORAL_DATA -- mixed
# null/non-null date AND datetime columns. Regression for item 112 / IB-DT-19:
# BackendDataFrameFactory.create/create_pair duplicate the same ibis-sqlite
# construction pattern as the REGISTRY-driven factory and were independently
# confirmed to crash the same way before the fix.
NULL_TEMPORAL_DATA = {
    "id": [1, 2, 3],
    "when_date": [None, dt.date(2024, 1, 1), dt.date(2024, 1, 2)],
    "when_ts": [
        None,
        dt.datetime(2024, 1, 1, 12, 0, 0),
        dt.datetime(2024, 1, 2, 8, 30, 0),
    ],
}

NULL_TEMPORAL_DATA_RIGHT = {
    "id": [1, 2, 3],
    "other_date": [dt.date(2024, 2, 1), None, dt.date(2024, 2, 2)],
}


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_create_survives_null_date_and_null_datetime(backend_name):
    """BackendDataFrameFactory.create must not crash on a null date/datetime
    mixed with non-null rows, for every backend (named explicitly in item 112
    required work #1, alongside _build_ibis_sqlite)."""
    df = BackendDataFrameFactory.create(NULL_TEMPORAL_DATA, backend_name)
    assert BackendResultHelper.get_count(df, backend_name) == 3


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_create_pair_survives_null_date_and_null_datetime(backend_name):
    """BackendDataFrameFactory.create_pair must not crash when either side of
    the pair has a null date/datetime column, for every backend."""
    left, right = BackendDataFrameFactory.create_pair(
        NULL_TEMPORAL_DATA, NULL_TEMPORAL_DATA_RIGHT, backend_name
    )
    assert BackendResultHelper.get_count(left, backend_name) == 3
    assert BackendResultHelper.get_count(right, backend_name) == 3
