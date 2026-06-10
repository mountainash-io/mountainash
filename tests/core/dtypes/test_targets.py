# tests/core/dtypes/test_targets.py
"""TypeTarget enum and native-module auto-detection."""
import polars as pl
import pytest

from mountainash.core.dtypes.targets import TypeTarget, detect_target


class TestTypeTarget:
    def test_members(self):
        assert {t.value for t in TypeTarget} == {
            "polars", "pandas", "pyarrow", "ibis", "narwhals", "python",
        }


class TestDetectTarget:
    def test_polars_dtype_instance(self):
        assert detect_target(pl.Datetime("us")) is TypeTarget.POLARS

    def test_polars_dtype_class(self):
        assert detect_target(pl.Int64) is TypeTarget.POLARS

    def test_pyarrow(self):
        pa = pytest.importorskip("pyarrow")
        assert detect_target(pa.int64()) is TypeTarget.PYARROW

    def test_numpy_dtype_maps_to_pandas(self):
        np = pytest.importorskip("numpy")
        assert detect_target(np.dtype("int64")) is TypeTarget.PANDAS

    def test_narwhals(self):
        nw = pytest.importorskip("narwhals")
        assert detect_target(nw.Int64) is TypeTarget.NARWHALS

    def test_unknown_returns_none(self):
        assert detect_target("i64") is None
        assert detect_target(42) is None
        assert detect_target(int) is None
