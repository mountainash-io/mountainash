# tests/core/dtypes/test_registry.py
import polars as pl
import pytest

from mountainash.core.dtypes.canonical import MountainashDtype as D
from mountainash.core.dtypes import ListDtype, TimestampDtype, dtype_family
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

    def test_explicit_target_preserves_native_parameters(self):
        assert registry.from_native(
            pl.Datetime("ms", "UTC"), target=TypeTarget.POLARS
        ) == TimestampDtype(
            precision=3, timezone_aware=True, timezone="UTC"
        )
        assert registry.from_native(
            pl.List(pl.Int64), target=TypeTarget.POLARS
        ) == ListDtype(element=D.I64)


# Semantic-string canonical types (item 113 Unit B, Task 2) are physically
# indistinguishable from STRING on every target — a native string cannot
# prove JSON/XSD-duration/XSD-year/XSD-yearmonth semantics, so from_native
# collapses them all to STRING by design. They are structurally excluded
# from the round-trip identity check below (which is completeness-checked
# via set(D) so a future canonical addition is still forced to declare
# itself into one bucket or the other).
_SEMANTIC_STRING_DTYPES: frozenset[D] = frozenset({
    D.JSON, D.XSD_DURATION, D.XSD_YEAR, D.XSD_YEARMONTH,
})


class TestRoundTrip:
    @pytest.mark.parametrize("target", [TypeTarget.POLARS, TypeTarget.NARWHALS])
    @pytest.mark.parametrize(
        "dtype", [d for d in D if d not in _SEMANTIC_STRING_DTYPES]
    )
    def test_canon_to_native_to_canon(self, dtype, target):
        native = registry.to_native_schema(dtype, target)
        back = registry.from_native(native, target=target)
        assert dtype_family(back) is dtype

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



class TestParseTypeString:
    def test_delegates(self):
        assert registry.parse_type_string("Int32", TypeTarget.POLARS) is pl.Int32
        assert registry.parse_type_string("garbage", TypeTarget.POLARS) is None


@pytest.mark.parametrize("target", [
    TypeTarget.POLARS, TypeTarget.PYARROW, TypeTarget.PANDAS,
    TypeTarget.NARWHALS, TypeTarget.IBIS,
])
def test_portable_timestamp_constructs_exact_native_type(target):
    """A portable descriptor must not be rejected or lose its unit/zone."""
    import ibis.expr.datatypes as dt
    import narwhals as nw
    import pandas as pd
    import pyarrow as pa

    expected = {
        TypeTarget.POLARS: pl.Datetime("us", "UTC"),
        TypeTarget.PYARROW: pa.timestamp("us", tz="UTC"),
        TypeTarget.PANDAS: pd.DatetimeTZDtype(unit="us", tz="UTC"),
        TypeTarget.NARWHALS: nw.Datetime("us", time_zone="UTC"),
        TypeTarget.IBIS: dt.Timestamp(scale=6, timezone="UTC"),
    }[target]
    descriptor = TimestampDtype(6, True, "UTC")
    assert registry.to_native_schema(descriptor, target) == expected
    assert registry.to_native_cast(descriptor, target) == expected


@pytest.mark.parametrize("target", [
    TypeTarget.POLARS, TypeTarget.PYARROW, TypeTarget.PANDAS,
    TypeTarget.NARWHALS, TypeTarget.IBIS,
])
def test_portable_nested_schema_preserves_order_and_child_parameters(target):
    import ibis.expr.datatypes as dt
    import narwhals as nw
    import pandas as pd
    import pyarrow as pa
    from mountainash.core.dtypes import StructDtype

    descriptor = ListDtype(StructDtype((
        ("at", TimestampDtype(6, True, "UTC")), ("id", D.I16),
    )))
    arrow = pa.list_(pa.struct([
        pa.field("at", pa.timestamp("us", tz="UTC")), pa.field("id", pa.int16()),
    ]))
    expected = {
        TypeTarget.POLARS: pl.List(pl.Struct({"at": pl.Datetime("us", "UTC"), "id": pl.Int16})),
        TypeTarget.PYARROW: arrow,
        TypeTarget.PANDAS: pd.ArrowDtype(arrow),
        TypeTarget.NARWHALS: nw.List(nw.Struct([
            nw.Field("at", nw.Datetime("us", time_zone="UTC")), nw.Field("id", nw.Int16),
        ])),
        TypeTarget.IBIS: dt.Array(dt.Struct({
            "at": dt.Timestamp(scale=6, timezone="UTC"), "id": dt.int16,
        })),
    }[target]
    assert registry.to_native_schema(descriptor, target) == expected


@pytest.mark.parametrize("target", [
    TypeTarget.POLARS, TypeTarget.PYARROW, TypeTarget.PANDAS,
    TypeTarget.NARWHALS, TypeTarget.IBIS,
])
@pytest.mark.parametrize("precision", [0, 3, 6, 9])
def test_timestamp_precision_is_not_silently_changed(target, precision):
    import ibis.expr.datatypes as dt
    import narwhals as nw
    import pandas as pd
    import pyarrow as pa

    dtype = TimestampDtype(precision, True, None)
    if precision == 0 and target in {TypeTarget.POLARS, TypeTarget.NARWHALS}:
        with pytest.raises(DtypeMappingError):
            registry.to_native_schema(dtype, target)
        return
    unit = {0: "s", 3: "ms", 6: "us", 9: "ns"}[precision]
    expected = {
        TypeTarget.PYARROW: lambda: pa.timestamp(unit, tz="UTC"),
        TypeTarget.PANDAS: lambda: pd.DatetimeTZDtype(unit=unit, tz="UTC"),
        TypeTarget.POLARS: lambda: pl.Datetime(unit, "UTC"),
        TypeTarget.NARWHALS: lambda: nw.Datetime(unit, time_zone="UTC"),
        TypeTarget.IBIS: lambda: dt.Timestamp(scale=precision, timezone="UTC"),
    }[target]()
    assert registry.to_native_schema(dtype, target) == expected
    assert dtype.timezone is None


@pytest.mark.parametrize("target", [
    TypeTarget.POLARS, TypeTarget.PYARROW, TypeTarget.PANDAS,
    TypeTarget.NARWHALS, TypeTarget.IBIS,
])
def test_fixed_array_keeps_every_dimension(target):
    import ibis.expr.datatypes as dt
    import narwhals as nw
    import pandas as pd
    import pyarrow as pa
    from mountainash.core.dtypes import ArrayDtype

    expected = {
        TypeTarget.POLARS: lambda: pl.Array(pl.Int16, (2, 3)),
        TypeTarget.PYARROW: lambda: pa.list_(pa.list_(pa.int16(), 3), 2),
        TypeTarget.PANDAS: lambda: pd.ArrowDtype(pa.list_(pa.list_(pa.int16(), 3), 2)),
        TypeTarget.NARWHALS: lambda: nw.Array(nw.Int16, (2, 3)),
        TypeTarget.IBIS: lambda: dt.Array(dt.Array(dt.int16, length=3), length=2),
    }[target]()
    actual = registry.to_native_schema(ArrayDtype(D.I16, (2, 3)), target)
    assert actual == expected


def test_ibis_fractional_precision_and_calendar_duration_are_native():
    import ibis.expr.datatypes as dt
    from mountainash.core.dtypes import DurationDtype, SchemaTypeStatus

    assert registry.to_native_schema(
        TimestampDtype(5, False, None), TypeTarget.IBIS,
    ) == dt.Timestamp(scale=5)
    assert registry.to_native_schema(
        DurationDtype("M", "calendar"), TypeTarget.IBIS,
    ) == dt.Interval("M")
    assert registry.to_native_schema(
        DurationDtype(SchemaTypeStatus.UNKNOWN, "calendar"), TypeTarget.IBIS,
    ) == dt.Interval("M")


@pytest.mark.parametrize("target", [TypeTarget.POLARS, TypeTarget.PYARROW])
def test_time_precision_retains_native_unit(target):
    import pyarrow as pa
    from mountainash.core.dtypes import TimeDtype

    expected = pl.Time if target is TypeTarget.POLARS else pa.time64("ns")
    assert registry.to_native_schema(TimeDtype(9), target) == expected


def test_python_carriers_do_not_claim_unrepresentable_metadata():
    import datetime
    from mountainash.core.dtypes import ArrayDtype, StructDtype

    assert registry.to_native_schema(TimestampDtype(), TypeTarget.PYTHON) is datetime.datetime
    assert registry.to_native_schema(ListDtype(D.I64), TypeTarget.PYTHON) == list[int]
    for dtype in (TimestampDtype(6, True, "UTC"), ArrayDtype(D.I64, (2,)),
                  StructDtype((("x", D.I64),))):
        with pytest.raises(DtypeMappingError):
            registry.to_native_schema(dtype, TypeTarget.PYTHON)


@pytest.mark.parametrize("target", [TypeTarget.POLARS, TypeTarget.PYARROW])
def test_nested_native_refinement_overrides_portable_parameters(target):
    import pyarrow as pa
    from mountainash.core.dtypes import NativeDtype

    native = pl.Datetime("ms") if target is TypeTarget.POLARS else pa.timestamp("ms")
    expected = pl.List(native) if target is TypeTarget.POLARS else pa.list_(native)
    dtype = ListDtype(TimestampDtype(
        5, True, "Europe/London", native=NativeDtype(value=native, target=target),
    ))
    assert registry.to_native_schema(dtype, target) == expected
