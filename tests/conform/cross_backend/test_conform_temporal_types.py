"""Conform on DURATION / YEAR / YEARMONTH — blocked pre-unification by the
incomplete type bridge. Cross-backend per testing-philosophy."""

import polars as pl
import pytest

import mountainash as ma
from mountainash.conform.errors import IncompatibleSourceTypeError
from mountainash.typespec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS

# BACKENDS = ["polars", "pandas", "pyarrow"]


def _frame(backend, data):
    df = pl.DataFrame(data)
    if backend == "pandas":
        return df.to_pandas()
    if backend == "pyarrow":
        return df.to_arrow()
    return df


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_conform_duration_rejects_integer_source(backend):
    df = _frame(backend, {"d": [1_000_000, 2_000_000]})
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="d", type=UniversalType.DURATION)])
    with pytest.raises(IncompatibleSourceTypeError, match="requires duration source"):
        ma.relation(df).conform(spec).to_polars()

@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_conform_year(backend):
    df = _frame(backend, {"y": [2024, 2025]})
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="y", type=UniversalType.YEAR)])
    out = ma.relation(df).conform(spec).to_polars()
    # YEAR is a canonical semantic-string type — maps to the backend's string
    # dtype on every target (spec §11), like YEARMONTH below.
    assert out.schema["y"] == pl.String


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_conform_yearmonth_rejects_integer_source(backend):
    df = _frame(backend, {"ym": [202401, 202402]})
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="ym", type=UniversalType.YEARMONTH)])
    with pytest.raises(IncompatibleSourceTypeError, match="requires yearmonth source"):
        ma.relation(df).conform(spec).to_polars()


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_conform_any_skips_cast(backend):
    df = _frame(backend, {"a": [1, 2]})
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="a", type=UniversalType.ANY)])
    out = ma.relation(df).conform(spec).to_polars()
    assert out.schema["a"] == pl.Int64  # untouched


@pytest.mark.parametrize("backend", ["polars", "polars-lazy", "pandas", "pyarrow"])
@pytest.mark.parametrize("action", ["coerce", "evolve", "freeze"])
@pytest.mark.parametrize("kind", ["timestamp", "duration"])
@pytest.mark.parametrize("ticks", [[1, 999, 1001, -1, -1001, None], [], [None, None]])
def test_bare_temporal_conform_preserves_source_metadata(backend, action, kind, ticks):
    """Use typed frames, not Python datetimes which erase nanosecond residues."""
    native = pl.Datetime("ns", "UTC") if kind == "timestamp" else pl.Duration("ns")
    canonical = ma.MountainashDtype.TIMESTAMP if kind == "timestamp" else ma.MountainashDtype.DURATION
    source = pl.DataFrame({"value": pl.Series(ticks, dtype=pl.Int64).cast(native)})
    if backend == "polars-lazy":
        source = source.lazy()
    elif backend == "pandas":
        source = source.to_pandas()
    elif backend == "pyarrow":
        source = source.to_arrow()
    spec = TypeSpec(fields=[FieldSpec("value", dtype=canonical)], missing_values=[])
    from mountainash.core.dtypes import TypeTarget, registry

    query = ma.relation(source).conform(spec, contract={"data_type": action})
    assert registry.to_native_schema(query.schema["value"], TypeTarget.POLARS) == native
    result = query.to_polars()
    assert result.schema["value"] == native
    assert result["value"].cast(pl.Int64).to_list() == ticks


@pytest.mark.parametrize("backend", ["polars", "polars-lazy", "pandas", "pyarrow"])
@pytest.mark.parametrize("kind", ["timestamp", "duration"])
@pytest.mark.parametrize("action", ["coerce", "evolve"])
def test_temporal_null_fill_preserves_fractional_source(backend, kind, action):
    from datetime import datetime, timedelta, timezone
    from mountainash.core.dtypes import DurationDtype, TimestampDtype

    timestamp = kind == "timestamp"
    native = pl.Datetime("ns", "UTC") if timestamp else pl.Duration("ns")
    canonical = ma.MountainashDtype.TIMESTAMP if timestamp else ma.MountainashDtype.DURATION
    if action == "evolve":
        canonical = TimestampDtype(6, True, "UTC") if timestamp else DurationDtype("us", "fixed")
    fill = datetime(1970, 1, 1, tzinfo=timezone.utc) if timestamp else timedelta(0)
    source = pl.DataFrame({"value": pl.Series([1, -1001, None], dtype=pl.Int64).cast(native)})
    if backend == "polars-lazy":
        source = source.lazy()
    elif backend == "pandas":
        source = source.to_pandas()
    elif backend == "pyarrow":
        source = source.to_arrow()
    spec = TypeSpec(fields=[FieldSpec("value", dtype=canonical, null_fill=fill)], missing_values=[])
    result = ma.relation(source).conform(spec, contract={"data_type": action}).to_polars()
    assert result.schema["value"] == native
    assert result["value"].cast(pl.Int64).to_list() == [1, -1001, 0]


@pytest.mark.parametrize("backend", ["polars", "pyarrow"])
@pytest.mark.parametrize("container", ["list", "array", "struct"])
@pytest.mark.parametrize("kind", ["timestamp", "duration"])
def test_nested_bare_temporal_conform_preserves_null_shape_and_ticks(backend, container, kind):
    from mountainash.core.dtypes import ArrayDtype, ListDtype, StructDtype

    native = pl.Datetime("ns", "UTC") if kind == "timestamp" else pl.Duration("ns")
    canonical = ma.MountainashDtype.TIMESTAMP if kind == "timestamp" else ma.MountainashDtype.DURATION
    if container == "struct":
        source = pl.Series("value", [{"v": 1}, None, {"v": None}, {"v": -1001}]).cast(pl.Struct({"v": native}))
        target = StructDtype((("v", canonical),))
    else:
        values = [[1, None], None, [-1001, 1001]]
        if container == "list":
            values.append([])
        source = pl.Series("value", values).cast(pl.List(native))
        target = ListDtype(canonical)
        if container == "array":
            source = source.list.to_array(2)
            target = ArrayDtype(canonical, (2,))
    expected = source.to_frame()
    frame = expected if backend == "polars" else expected.to_arrow()
    spec = TypeSpec(fields=[FieldSpec("value", dtype=target)], missing_values=[])
    result = ma.relation(frame).conform(spec).to_polars()
    assert result.schema == expected.schema
    assert result.equals(expected)


@pytest.mark.parametrize("backend", ["polars", "pandas", "pyarrow"])
@pytest.mark.parametrize("target", ["string", "discard_value"])
def test_temporal_source_fill_respects_destination_and_discard(backend, target):
    from mountainash.core.dtypes import TimestampDtype

    source = pl.DataFrame({"value": pl.Series([None], dtype=pl.Datetime("ns"))})
    if backend == "pandas":
        source = source.to_pandas()
    elif backend == "pyarrow":
        source = source.to_arrow()
    field = (
        FieldSpec("value", type=UniversalType.STRING, null_fill="unknown")
        if target == "string" else
        FieldSpec("value", dtype=TimestampDtype(6, False, None), null_fill="bad")
    )
    query = ma.relation(source).conform(
        TypeSpec(fields=[field], missing_values=[]),
        contract={"data_type": "coerce" if target == "string" else "discard_value"},
    )
    if target == "discard_value" and backend != "polars":
        from mountainash.core.types import BackendCapabilityError

        with pytest.raises(BackendCapabilityError, match="null-on-failure"):
            query.to_polars()
        return
    if target == "string" and backend == "pyarrow":
        import pyarrow as pa

        # Native Arrow cannot coalesce timestamp and string, even before a cast.
        with pytest.raises(pa.ArrowNotImplementedError, match="coalesce.*no kernel"):
            query.to_polars()
        return
    result = query.to_polars()
    assert result.schema["value"] == (pl.String if target == "string" else pl.Datetime("us"))
    assert result["value"].to_list() == (["unknown"] if target == "string" else [None])
