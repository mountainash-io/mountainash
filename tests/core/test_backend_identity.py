"""Runtime dialect detection (spec Section 1 — verified feasible 2026-07-05)."""
import pandas as pd
import polars as pl
import pytest

from mountainash.core.backend_detection import identify_backend_identity
from mountainash.core.capabilities import KNOWN_DIALECTS, BackendIdentity
from mountainash.core.constants import CONST_BACKEND


class TestPolarsIdentity:
    def test_eager(self):
        ident = identify_backend_identity(pl.DataFrame({"a": [1]}))
        assert ident == BackendIdentity(CONST_BACKEND.POLARS, "polars")

    def test_lazy(self):
        ident = identify_backend_identity(pl.DataFrame({"a": [1]}).lazy())
        assert ident == BackendIdentity(CONST_BACKEND.POLARS, "polars")


class TestNarwhalsIdentity:
    def test_polars_eager(self):
        import narwhals as nw
        ident = identify_backend_identity(nw.from_native(pl.DataFrame({"a": [1]})))
        assert ident == BackendIdentity(CONST_BACKEND.NARWHALS, "narwhals-polars")

    def test_polars_lazy_maps_to_narwhals_lazy(self):
        import narwhals as nw
        ident = identify_backend_identity(nw.from_native(pl.DataFrame({"a": [1]}).lazy()))
        assert ident == BackendIdentity(CONST_BACKEND.NARWHALS, "narwhals-lazy")

    def test_pandas(self):
        import narwhals as nw
        ident = identify_backend_identity(
            nw.from_native(pd.DataFrame({"a": [1]}), eager_only=True)
        )
        assert ident == BackendIdentity(CONST_BACKEND.NARWHALS, "narwhals-pandas")

    def test_native_pandas_fallback(self):
        ident = identify_backend_identity(pd.DataFrame({"a": [1]}))
        assert ident.family is CONST_BACKEND.NARWHALS
        assert ident.dialect == "narwhals-pandas"


class TestIbisIdentity:
    def test_bound_table_and_derived_expr(self):
        ibis = pytest.importorskip("ibis")
        con = ibis.duckdb.connect()
        t = con.create_table("t", pd.DataFrame({"a": [1]}))
        assert identify_backend_identity(t) == BackendIdentity(
            CONST_BACKEND.IBIS, "ibis-duckdb"
        )
        assert identify_backend_identity(t.mutate(b=t.a + 1)).dialect == "ibis-duckdb"

    def test_unbound_and_memtable_degrade_to_family(self):
        ibis = pytest.importorskip("ibis")
        assert identify_backend_identity(
            ibis.table({"a": "int64"}, name="u")
        ) == BackendIdentity(CONST_BACKEND.IBIS, None)
        assert identify_backend_identity(ibis.memtable({"a": [1]})).dialect is None


def test_known_dialects_vocabulary():
    assert "narwhals-polars" in KNOWN_DIALECTS[CONST_BACKEND.NARWHALS]
    assert "ibis-sqlite" in KNOWN_DIALECTS[CONST_BACKEND.IBIS]
    assert KNOWN_DIALECTS[CONST_BACKEND.POLARS] == frozenset({"polars"})


def test_known_dialects_is_exhaustive_over_backend_enum():
    # _validate_fact indexes KNOWN_DIALECTS[family] directly, so every
    # CONST_BACKEND member (incl. PYARROW) must have an entry or facts under
    # that family would KeyError at registration.
    assert set(KNOWN_DIALECTS) == set(CONST_BACKEND)
