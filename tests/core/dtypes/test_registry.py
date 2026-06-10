# tests/core/dtypes/test_registry.py
import polars as pl
import pytest

from mountainash.core.dtypes.canonical import MountainashDtype as D
from mountainash.core.dtypes.errors import DtypeMappingError, UnknownDtypeError
from mountainash.core.dtypes.registry import registry
from mountainash.core.dtypes.targets import TypeTarget


class TestToNative:
    def test_schema_polars(self):
        assert registry.to_native_schema(D.I64, TypeTarget.POLARS) is pl.Int64

    def test_schema_list_succeeds(self):
        assert registry.to_native_schema(D.LIST, TypeTarget.POLARS) is pl.List

    def test_cast_list_raises_with_supported_set(self):
        with pytest.raises(DtypeMappingError, match="list"):
            registry.to_native_cast(D.LIST, TypeTarget.POLARS)

    def test_cast_scalar_succeeds(self):
        assert registry.to_native_cast(D.I64, TypeTarget.IBIS) == "int64"


class TestFromNative:
    def test_explicit_target(self):
        assert registry.from_native(pl.Int32(), target=TypeTarget.POLARS) is D.I32

    def test_auto_detect(self):
        assert registry.from_native(pl.Int32()) is D.I32

    def test_auto_detect_failure_raises(self):
        with pytest.raises(UnknownDtypeError, match="target"):
            registry.from_native("int32")  # strings can't auto-detect

    def test_string_with_explicit_target(self):
        assert registry.from_native("int32", target=TypeTarget.PANDAS) is D.I32


class TestRoundTrip:
    @pytest.mark.parametrize("target", [TypeTarget.POLARS, TypeTarget.NARWHALS])
    @pytest.mark.parametrize("dtype", [d for d in D])
    def test_canon_to_native_to_canon(self, dtype, target):
        native = registry.to_native_schema(dtype, target)
        back = registry.from_native(native, target=target)
        # Width-preserving identity (STRING-collapsing types like
        # Categorical only appear in from_native, not to_native)
        assert back is dtype


class TestParseTypeString:
    def test_delegates(self):
        assert registry.parse_type_string("Int32", TypeTarget.POLARS) is pl.Int32
        assert registry.parse_type_string("garbage", TypeTarget.POLARS) is None
