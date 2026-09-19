"""Cross-backend behavior for ``assume_timezone``.

Polars attaches the requested zone without changing the wall clock. Ibis and
Narwhals cannot implement timezone attachment and reject the operation at its
intrinsic function boundary.
"""
from __future__ import annotations

from datetime import datetime

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
)

_TS = datetime(2026, 7, 21, 13, 37, 45)

TIMESTAMP_BACKENDS = (
    "polars",
    "polars-lazy",
    "narwhals-polars",
    "narwhals-pandas",
    "narwhals-lazy",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite",
)



@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TIMESTAMP_BACKENDS)
@pytest.mark.parametrize("tz", ["UTC", "Australia/Sydney"])
def test_assume_timezone(backend_factory, collect_expr, backend_name, tz):
    df = backend_factory.create({"ts": [_TS, None]}, backend_name)
    expr = ma.col("ts").dt.assume_timezone(tz)
    if backend_name.startswith("polars"):
        got = collect_expr(df, expr, alias="r")
        assert got[0].replace(tzinfo=None) == _TS
        assert str(got[0].tzinfo) == tz
        assert got[1] is None
        return
    with pytest.raises(BackendCapabilityError) as raised:
        collect_expr(df, expr, alias="r")
    assert raised.value.function_key is FKEY_SUBSTRAIT_SCALAR_DATETIME.ASSUME_TIMEZONE
    assert raised.value.backend == (
        "ibis" if backend_name.startswith("ibis") else "narwhals"
    )
    assert raised.value.limitation is None
