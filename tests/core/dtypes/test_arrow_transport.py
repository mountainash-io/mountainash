"""Native-to-Arrow transport: portable types, native owners and mixed containers.

The transport entrypoint returns an Arrow dtype, never a field: names,
nullability and metadata remain schema-adapter responsibilities, and a native
refinement is never re-expressed through a lossier portable type.
"""
from __future__ import annotations

import ibis.expr.datatypes as dt
import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

from mountainash.core.dtypes import (
    ArrayDtype,
    DecimalDtype,
    DtypeMappingError,
    DurationDtype,
    ListDtype,
    MountainashDtype as D,
    NativeDtype,
    SchemaTypeStatus,
    StructDtype,
    TimeDtype,
    TimestampDtype,
    TypeTarget,
    registry,
)


def native(value, target):
    return NativeDtype(value=value, target=target)


class TestAbsentAndPortableStates:
    def test_absent_transport_type_stays_absent(self):
        assert registry.to_arrow_transport(None) is None

    def test_unknown_transports_as_arrow_null(self):
        assert registry.to_arrow_transport(SchemaTypeStatus.UNKNOWN) == pa.null()

    @pytest.mark.parametrize("dtype,expected", [
        (D.I64, pa.int64()),
        (D.STRING, pa.string()),
        (D.BOOL, pa.bool_()),
        (DecimalDtype(12, 4), pa.decimal128(12, 4)),
        (TimestampDtype(6, True, "UTC"), pa.timestamp("us", tz="UTC")),
        (TimestampDtype(3, False, None), pa.timestamp("ms")),
        # Partial portable parameters take Arrow's construction defaults here.
        (TimestampDtype(), pa.timestamp("us")),
        (TimeDtype(6), pa.time64("us")),
        (DurationDtype("ms", "fixed"), pa.duration("ms")),
        (ListDtype(D.I16), pa.list_(pa.int16())),
        (ListDtype(), pa.list_(pa.null())),
        (ArrayDtype(D.I16, (2, 3)), pa.list_(pa.list_(pa.int16(), 3), 2)),
        (StructDtype((("a", D.I64), ("b", D.STRING))), pa.struct([("a", pa.int64()), ("b", pa.string())])),
        (StructDtype(), pa.struct([])),
    ])
    def test_portable_types_use_arrow_construction(self, dtype, expected):
        assert registry.to_arrow_transport(dtype) == expected

    def test_portable_parameters_arrow_cannot_hold_are_refused_not_rounded(self):
        with pytest.raises(DtypeMappingError):
            registry.to_arrow_transport(TimestampDtype(5, True, "UTC"))

    def test_unrepresentable_child_is_refused(self):
        with pytest.raises(DtypeMappingError):
            registry.to_arrow_transport(ListDtype(SchemaTypeStatus.UNCONSTRAINED))


class TestNativeOwners:
    @pytest.mark.parametrize("value,target,expected", [
        (pa.timestamp("ms", tz="UTC"), TypeTarget.PYARROW, pa.timestamp("ms", tz="UTC")),
        (pa.large_string(), TypeTarget.PYARROW, pa.large_string()),
        (pl.Datetime("ms", "UTC"), TypeTarget.POLARS, pa.timestamp("ms", tz="UTC")),
        (pl.Int16, TypeTarget.POLARS, pa.int16()),
        (pd.Int16Dtype(), TypeTarget.PANDAS, pa.int16()),
        (pd.DatetimeTZDtype(unit="ms", tz="UTC"), TypeTarget.PANDAS, pa.timestamp("ms", tz="UTC")),
        (pd.ArrowDtype(pa.list_(pa.int16())), TypeTarget.PANDAS, pa.list_(pa.int16())),
        (dt.Timestamp(scale=3, timezone="UTC"), TypeTarget.IBIS, pa.timestamp("ms", tz="UTC")),
        (dt.Array(dt.int16), TypeTarget.IBIS, pa.list_(pa.int16())),
        (nw.Datetime("ms", time_zone="UTC"), TypeTarget.NARWHALS, pa.timestamp("ms", tz="UTC")),
        (nw.Int16, TypeTarget.NARWHALS, pa.int16()),
    ])
    def test_native_type_is_converted_by_its_owner(self, value, target, expected):
        assert registry.to_arrow_transport(native(value, target)) == expected
        assert registry._adapter(target).to_arrow_transport(value) == expected

    def test_portable_dtype_with_native_refinement_uses_the_owner(self):
        refined = TimestampDtype(5, True, "Europe/London", native=native(pl.Datetime("ms"), TypeTarget.POLARS))
        assert registry.to_arrow_transport(refined) == pa.timestamp("ms")

    def test_native_refinement_is_not_flattened_to_a_portable_type(self):
        converted = registry.to_arrow_transport(native(pl.Categorical, TypeTarget.POLARS))
        assert pa.types.is_dictionary(converted)

    def test_arrow_field_qualifiers_are_not_stripped_on_the_dtype_path(self):
        qualified = native(pa.field("", pa.int64(), nullable=False), TypeTarget.PYARROW)
        with pytest.raises(DtypeMappingError, match="qualifiers"):
            registry.to_arrow_transport(qualified)

    def test_ibis_physical_sql_refinement_is_refused(self):
        with pytest.raises(DtypeMappingError, match="Physical SQL"):
            registry.to_arrow_transport(native("NUMERIC", TypeTarget.IBIS))

    def test_python_hints_have_no_arrow_transport(self):
        with pytest.raises(DtypeMappingError):
            registry.to_arrow_transport(native(int, TypeTarget.PYTHON))
        with pytest.raises(DtypeMappingError):
            registry.to_arrow_transport(ListDtype(native(int, TypeTarget.PYTHON)))


class TestContainersWithNativeChildren:
    def test_each_native_child_is_dispatched_to_its_own_owner(self):
        dtype = StructDtype((
            ("polars_at", native(pl.Datetime("ms", "UTC"), TypeTarget.POLARS)),
            ("pandas_ids", ListDtype(native(pd.Int16Dtype(), TypeTarget.PANDAS))),
            ("ibis_pair", ArrayDtype(native(dt.int8, TypeTarget.IBIS), (2,))),
            ("narwhals_ts", native(nw.Datetime("us"), TypeTarget.NARWHALS)),
            ("arrow_text", native(pa.large_string(), TypeTarget.PYARROW)),
            ("plain", D.STRING),
            ("missing", SchemaTypeStatus.UNKNOWN),
        ))
        assert registry.to_arrow_transport(dtype) == pa.struct([
            ("polars_at", pa.timestamp("ms", tz="UTC")),
            ("pandas_ids", pa.list_(pa.int16())),
            ("ibis_pair", pa.list_(pa.int8(), 2)),
            ("narwhals_ts", pa.timestamp("us")),
            ("arrow_text", pa.large_string()),
            ("plain", pa.string()),
            ("missing", pa.null()),
        ])

    def test_native_children_survive_nested_portable_wrappers(self):
        child = native(pl.Datetime("ns", "UTC"), TypeTarget.POLARS)
        dtype = ListDtype(StructDtype((("events", ListDtype(child)),)))
        assert registry.to_arrow_transport(dtype) == pa.list_(
            pa.struct([("events", pa.list_(pa.timestamp("ns", tz="UTC")))])
        )

    def test_native_container_keeps_children_inside_the_native_type(self):
        """A native container is owned whole; its children are not re-selected."""
        value = pl.List(pl.Struct({"at": pl.Datetime("ms", "UTC")}))
        converted = registry.to_arrow_transport(native(value, TypeTarget.POLARS))
        assert pa.types.is_list(converted) or pa.types.is_large_list(converted)
        assert converted.value_type == pa.struct([("at", pa.timestamp("ms", tz="UTC"))])


class TestTransportDispositionPerTarget:
    """Every target is either a transport owner or an explicit, typed refusal.

    Closed by default: a new TypeTarget fails here until its disposition is stated, so
    a target cannot be silently missing from transport.
    """

    OWNERS = {
        TypeTarget.POLARS: (pl.Int16, pa.int16()),
        TypeTarget.PANDAS: (pd.Int16Dtype(), pa.int16()),
        TypeTarget.PYARROW: (pa.int16(), pa.int16()),
        TypeTarget.IBIS: (dt.int16, pa.int16()),
        TypeTarget.NARWHALS: (nw.Int16, pa.int16()),
    }
    REFUSED = {TypeTarget.PYTHON: int}  # Python hints are carriers, not storage types.

    def test_every_target_states_its_disposition(self):
        assert set(self.OWNERS) | set(self.REFUSED) == set(TypeTarget)
        assert not set(self.OWNERS) & set(self.REFUSED)

    @pytest.mark.parametrize("target", sorted(OWNERS, key=lambda t: t.value), ids=lambda t: t.value)
    def test_owner_converts_its_own_dtypes_through_the_registry(self, target):
        value, expected = self.OWNERS[target]
        assert registry.to_arrow_transport(native(value, target)) == expected

    @pytest.mark.parametrize("target", sorted(REFUSED, key=lambda t: t.value), ids=lambda t: t.value)
    def test_refusal_is_a_typed_mapping_error(self, target):
        with pytest.raises(DtypeMappingError):
            registry.to_arrow_transport(native(self.REFUSED[target], target))
