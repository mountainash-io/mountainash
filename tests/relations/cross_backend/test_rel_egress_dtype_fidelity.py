"""Egress must preserve column types, not widen them.

`Relation.to_polars()` converts a non-polars, non-pandas result (an ibis
`Table`) to polars.  Routing that through pandas silently widens temporal
types -- ibis `date` becomes `datetime64[s]`, which polars then reads as
`Datetime(time_unit="ms")` -- so a `date` column arrives as
`datetime.datetime` values at midnight.  Arrow preserves `date32[day]`, and
polars reads that as `Date`.

The values are equal either way; the TYPE is not, and `datetime.datetime(...)
!= datetime.date(...)`, so anything comparing against a `date` silently fails
on ibis while looking like a value bug.
"""
from __future__ import annotations

import datetime as _dt

import polars as pl
import pytest

import mountainash as ma

from fixtures.backend_registry import ALL_BACKENDS

_DATES = [_dt.date(2024, 3, 15), _dt.date(2024, 6, 20)]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_date_column_survives_egress_as_date(backend_name, backend_factory) -> None:
    """A `date` column stays `Date` through to_polars() on every backend."""
    df = backend_factory.create({"d": _DATES}, backend_name)
    out = ma.relation(df).select(ma.col("d")).to_polars()

    assert out.schema["d"] == pl.Date, (
        f"{backend_name}: date column egressed as {out.schema['d']!r}, not pl.Date"
    )
    assert out.to_dict(as_series=False)["d"] == _DATES
