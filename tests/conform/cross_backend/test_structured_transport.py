"""Regression coverage for portable structured logical transport."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

import pytest

from fixtures.backend_registry import ALL_BACKENDS

from mountainash.conform.structured_transport import (
    INVALID_STRUCTURED_VALUE,
    StructuredRoot,
    decode_structured_value,
)


def test_opaque_nested_transport_retains_native_parameterized_leaves():
    instant = datetime(2026, 1, 1, 0, 0, 0, 123456, tzinfo=timezone.utc)
    value = {
        "at": instant,
        "events": [{"amount": Decimal("12.3400"), "elapsed": timedelta(seconds=2)}, None],
        "clock": time(12, 30, 15, 500000),
    }

    decoded = decode_structured_value(value, expected_root=StructuredRoot.OBJECT)

    assert decoded == value
    assert decoded["events"][1] is None


def test_opaque_nested_transport_keeps_invalid_leaf_rejection():
    decoded = decode_structured_value(
        {"at": object()}, expected_root=StructuredRoot.OBJECT
    )

    assert decoded is INVALID_STRUCTURED_VALUE


@pytest.mark.parametrize("value", [None, [], [None]])
def test_nested_transport_distinguishes_null_and_empty_array_values(value):
    decoded = decode_structured_value(value, expected_root=StructuredRoot.ARRAY)

    assert decoded == value


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    ("format_", "encoded"),
    [("%Y%m%d", "20260101"), ("%Y%m%d%z", "20260101+0000")],
)
def test_nested_custom_format_and_child_fill_survive_composition(
    backend_name, backend_factory, format_, encoded,
):
    import mountainash as ma
    import polars as pl
    from mountainash.core.dtypes import TimestampDtype, MountainashDtype as D
    from mountainash.typespec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    declaration = FieldSpec(
        fields={
            "count": FieldSpec(type=UniversalType.INTEGER, dtype=D.I16),
            "backup": FieldSpec(
                type=UniversalType.INTEGER, dtype=D.I16, null_fill=12
            ),
            "at": FieldSpec(
                type=UniversalType.DATETIME,
                dtype=TimestampDtype(6, True, "UTC"),
                format=format_,
                null_fill=encoded,
            ),
        },
    )
    source = backend_factory.create(
        {"record": ['{"count":"13","backup":null,"at":null}', '{"count":"14"}', None]},
        backend_name,
    )
    result = ma.relation(source).conform(
        TypeSpec(fields={"record": declaration}, missing_values=[]),
    ).to_polars()
    assert result.schema["record"] == pl.Struct({
        "count": pl.Int16, "backup": pl.Int16, "at": pl.Datetime("us", "UTC"),
    })
    instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert result["record"].to_list() == [
        {"count": 13, "backup": 12, "at": instant},
        {"count": 14, "backup": 12, "at": instant},
        None,
    ]

def test_invalid_nested_custom_temporal_value_remains_a_value_error():
    import mountainash as ma
    import polars as pl
    from mountainash.core.dtypes import TimestampDtype
    from mountainash.typespec import FieldSpec, TypeSpec
    from mountainash.conform.errors import ConformTransformError

    declaration = FieldSpec(
        fields={
            "at": FieldSpec(
                dtype=TimestampDtype(6, False), format="%Y%m%d"
            ),
        },
    )
    source = pl.DataFrame({"record": ['{"at":"not-a-date"}']})

    with pytest.raises(ConformTransformError, match="invalid object value"):
        ma.relation(source).conform(
            TypeSpec(fields={"record": declaration}, missing_values=[]),
        ).to_polars()

@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_nested_missing_sentinel_is_filled_before_temporal_conversion(
    backend_name, backend_factory,
):
    import mountainash as ma
    from mountainash.core.dtypes import TimestampDtype
    from mountainash.typespec import FieldSpec, TypeSpec

    declaration = FieldSpec(
        fields={
            "at": FieldSpec(
                dtype=TimestampDtype(6, False),
                format="%Y-%m-%d %H:%M:%S",
                missing_values=["MISSING"],
                null_fill="2026-01-01 00:00:00",
            ),
        },
    )
    source = backend_factory.create(
        {"record": ['{"at":"MISSING"}']}, backend_name,
    )

    result = ma.relation(source).conform(
        TypeSpec(fields={"record": declaration}, missing_values=[]),
    ).to_polars()

    assert result["record"].to_list() == [{"at": datetime(2026, 1, 1)}]


@pytest.mark.parametrize(
    ("encoded", "expected_ns"),
    [
        ("2026/01/01 00:00:00.123456789", 1767225600123456789),
        ("2026/01/01 00:00:00,123456789", 1767225600123456789),
        ("2026/01/01 00:00.123456789", 1767225607407407340),
    ],
)
@pytest.mark.xfail(
    reason="parse_temporal_any returns Python datetime with microsecond precision",
    strict=False,
)
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_nested_any_timestamp_preserves_nanoseconds(
    backend_name, backend_factory, encoded, expected_ns,
):
    import mountainash as ma
    import polars as pl
    from mountainash.core.dtypes import TimestampDtype
    from mountainash.typespec import FieldSpec, TypeSpec

    declaration = FieldSpec(
        fields={
            "at": FieldSpec(dtype=TimestampDtype(9, False), format="any"),
        },
    )
    source = backend_factory.create(
        {"record": [f'{{"at":"{encoded}"}}']}, backend_name,
    )

    result = ma.relation(source).conform(
        TypeSpec(fields={"record": declaration}, missing_values=[]),
    ).to_polars()

    assert result.schema["record"].fields[0].dtype == pl.Datetime("ns")
    assert result.select(
        pl.col("record").struct.field("at").dt.epoch("ns")
    ).to_series().to_list() == [expected_ns]
