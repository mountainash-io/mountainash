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


    @pytest.mark.parametrize(
        "target",
        [
            TypeTarget.POLARS,
            TypeTarget.PYARROW,
            TypeTarget.PANDAS,
            TypeTarget.IBIS,
            TypeTarget.NARWHALS,
        ],
    )
    @pytest.mark.parametrize("precision,scale", [(1, 0), (20, 3), (38, 38)])
    def test_decimal_native_round_trip_retains_parameters(
        self, target, precision, scale
    ):
        from mountainash.core.dtypes.canonical import DecimalDtype

        dtype = DecimalDtype(precision=precision, scale=scale)

        native = registry.to_native_schema(dtype, target)
        assert registry.from_native(native, target=target) == dtype
        cast_native = registry.to_native_cast(dtype, target)
        assert registry.from_native(cast_native, target=target) == dtype

    def test_bare_decimal_cannot_lower_to_native_schema(self):
        with pytest.raises(DtypeMappingError):
            registry.to_native_schema(D.DECIMAL, TypeTarget.POLARS)
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


# Semantic-string kinds, including lexical numeric declarations, are
# physically indistinguishable from STRING on each target.
# Native strings carry no proof of any such semantic declaration.
# Bare DECIMAL is separately excluded because parameters are required.
_SEMANTIC_STRING_DTYPES: frozenset[D] = frozenset({
    D.JSON, D.XSD_DURATION, D.XSD_YEAR, D.XSD_YEARMONTH,
    D.LEXICAL_INTEGER, D.LEXICAL_DECIMAL,
})
_INCOMPLETE_DTYPES: frozenset[D] = frozenset({D.DECIMAL})


class TestRoundTrip:
    @pytest.mark.parametrize("target", [TypeTarget.POLARS, TypeTarget.NARWHALS])
    @pytest.mark.parametrize(
        "dtype",
        [
            d for d in D
            if d not in _SEMANTIC_STRING_DTYPES | _INCOMPLETE_DTYPES
        ],
    )
    def test_canon_to_native_to_canon(self, dtype, target):
        native = registry.to_native_schema(dtype, target)
        back = registry.from_native(native, target=target)
        assert back is dtype

    @pytest.mark.parametrize("target", [TypeTarget.POLARS, TypeTarget.NARWHALS])
    @pytest.mark.parametrize(
        "dtype", sorted(_SEMANTIC_STRING_DTYPES, key=lambda d: d.value)
    )
    def test_semantic_string_types_collapse_to_string_on_round_trip(
        self, dtype, target
    ):
        native = registry.to_native_schema(dtype, target)
        back = registry.from_native(native, target=target)
        assert back is D.STRING

    def test_special_type_buckets_cover_canonical_vocabulary(self):
        assert _SEMANTIC_STRING_DTYPES | _INCOMPLETE_DTYPES <= set(D)

class TestParseTypeString:
    def test_delegates(self):
        assert registry.parse_type_string("Int32", TypeTarget.POLARS) is pl.Int32
        assert registry.parse_type_string("garbage", TypeTarget.POLARS) is None
