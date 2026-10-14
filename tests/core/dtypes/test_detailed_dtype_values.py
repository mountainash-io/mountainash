from __future__ import annotations

import pytest

from mountainash.core.dtypes import (
    ArrayDtype,
    DecimalDtype,
    MountainashDtype,
    SchemaTypeStatus,
    StructDtype,
    TimestampDtype,
    dtype_family,
    dtype_is_complete,
)


def test_timestamp_unknown_parameters_differ_from_known_inapplicable_values():
    unknown = TimestampDtype()
    naive = TimestampDtype(precision=9, timezone_aware=False, timezone=None)
    aware_without_retained_zone = TimestampDtype(
        precision=9, timezone_aware=True, timezone=None
    )

    assert unknown.precision is SchemaTypeStatus.UNKNOWN
    assert unknown.timezone_aware is SchemaTypeStatus.UNKNOWN
    assert not dtype_is_complete(unknown)
    assert dtype_is_complete(naive)
    assert dtype_is_complete(aware_without_retained_zone)
    assert naive != aware_without_retained_zone


def test_descriptor_family_classification_does_not_erase_decimal():
    decimal = DecimalDtype(precision=18, scale=4)

    assert dtype_family(TimestampDtype(9, True, "UTC")) is MountainashDtype.TIMESTAMP
    assert dtype_family(ArrayDtype(MountainashDtype.I64, (2, 3))) is MountainashDtype.LIST
    assert dtype_family(StructDtype(())) is MountainashDtype.STRUCT
    assert dtype_family(decimal) is decimal


@pytest.mark.parametrize("family", [
    MountainashDtype.TIMESTAMP, MountainashDtype.TIME, MountainashDtype.DURATION,
    MountainashDtype.LIST, MountainashDtype.STRUCT,
])
def test_bare_parameterized_family_does_not_certify_completeness(family):
    assert not dtype_is_complete(family)


def test_unknown_nested_field_is_not_a_complete_empty_struct():
    assert dtype_is_complete(StructDtype(fields=()))
    assert not dtype_is_complete(StructDtype())
    assert not dtype_is_complete(StructDtype(fields=(("at", TimestampDtype()),)))


@pytest.mark.parametrize("constructor,kwargs", [
    (TimestampDtype, {"precision": 9, "timezone_aware": 1, "timezone": None}),
    (TimestampDtype, {"precision": 9, "timezone_aware": False, "timezone": "UTC"}),
    (ArrayDtype, {"dimensions": (-1,)}),
    (ArrayDtype, {"dimensions": [2, 3]}),
    (StructDtype, {"fields": [("n", MountainashDtype.I64)]}),
])
def test_descriptors_reject_contradictory_or_mutable_parameters(constructor, kwargs):
    from mountainash.core.dtypes.errors import UnknownDtypeError
    with pytest.raises(UnknownDtypeError):
        constructor(**kwargs)
