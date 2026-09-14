"""Registry, trace, guard, and error contracts for `mountainash.core.transit`."""
from __future__ import annotations

import pytest

from mountainash.core.errors import BackendConversionError
from mountainash.core.transit import (
    BOUNDARY_REGISTRY,
    BoundaryKey,
    TransitClass,
    capture_conversion_trace,
    transit_call,
)


def test_backend_conversion_error_preserves_typeerror_compatibility():
    from mountainash.core.errors import MountainashError

    error = BackendConversionError(
        "pandas transit is prohibited",
        boundary_key="IBIS_INTERNAL_EXECUTE",
        source_family="ibis",
        source_dialect="ibis-duckdb",
        destination_family="narwhals",
        destination_dialect="narwhals-pandas",
        source_type="ibis.expr.types.relations.Table",
        route="native_materialization",
        reason="internal execution transit",
    )
    assert isinstance(error, MountainashError)
    assert isinstance(error, TypeError)
    assert error.boundary_key == "IBIS_INTERNAL_EXECUTE"
    assert error.destination_dialect == "narwhals-pandas"


def test_every_boundary_key_has_exactly_one_specification():
    assert set(BOUNDARY_REGISTRY) == set(BoundaryKey)


def test_every_specification_has_a_non_empty_reason_and_a_since_date():
    for key, spec in BOUNDARY_REGISTRY.items():
        assert spec.reason.strip(), key
        assert spec.since is not None, key


def test_non_pandas_call_records_only_inside_capture_context():
    with capture_conversion_trace() as trace:
        result = transit_call(BoundaryKey.POLARS_LAZY_COLLECT, lambda: "native")
    assert result == "native"
    assert [record.boundary_key for record in trace.records] == [
        BoundaryKey.POLARS_LAZY_COLLECT
    ]


def test_call_outside_capture_context_records_nothing():
    result = transit_call(BoundaryKey.POLARS_LAZY_COLLECT, lambda: "native")
    assert result == "native"


def test_untraced_prohibited_pandas_result_raises():
    import pandas as pd

    with pytest.raises(BackendConversionError) as exc:
        transit_call(
            BoundaryKey.IBIS_INTERNAL_EXECUTE,
            lambda: pd.DataFrame({"x": [1]}),
        )
    assert exc.value.boundary_key is BoundaryKey.IBIS_INTERNAL_EXECUTE


def test_traced_prohibited_pandas_result_still_raises():
    import pandas as pd

    with capture_conversion_trace() as trace, pytest.raises(BackendConversionError):
        transit_call(
            BoundaryKey.IBIS_INTERNAL_EXECUTE,
            lambda: pd.DataFrame({"x": [1]}),
        )
    assert trace.records == []


def test_permitted_pandas_result_does_not_raise():
    import pandas as pd

    result = transit_call(
        BoundaryKey.NARWHALS_NATIVE_UNWRAP_PANDAS,
        lambda: pd.DataFrame({"x": [1]}),
    )
    assert isinstance(result, pd.DataFrame)


def test_narwhals_pandas_typed_boolean_projection_records_native_callback():
    import narwhals as nw
    import pandas as pd

    import mountainash as ma

    native = pd.DataFrame(
        {"x": pd.Series([0, 1, 2, None], dtype="Int64", index=[9, 2, 9, -1])}
    )
    frame = nw.from_native(native, eager_only=True)

    with capture_conversion_trace() as trace:
        expression = ma.col("x").boolean_value(source="binary_number").compile(frame)
        result = frame.select(expression.alias("result")).to_native()

    output = result["result"]
    assert result.index.equals(native.index)
    assert output.dtype == pd.BooleanDtype()
    assert [None if value is pd.NA else value for value in output.tolist()] == [
        False,
        True,
        None,
        None,
    ]
    assert any(
        record.boundary_key is BoundaryKey.EXPRESSION_NARWHALS_PANDAS_TYPED_CALLBACK
        for record in trace.records
    )
    assert any(
        record.boundary_key is BoundaryKey.EXPRESSION_NARWHALS_SCHEMA_UNWRAP
        for record in trace.records
    )


def test_narwhals_pandas_object_projection_records_native_callback():
    import narwhals as nw
    import pandas as pd

    import mountainash as ma

    native = pd.DataFrame(
        {"x": pd.Series([True, "yes", None], dtype=object, index=[4, -1, 4])}
    )
    frame = nw.from_native(native, eager_only=True)

    with capture_conversion_trace() as trace:
        expression = ma.col("x").value_kind().compile(frame)
        result = frame.select(expression.alias("result")).to_native()

    output = result["result"]
    assert result.index.equals(native.index)
    assert output.dtype == pd.StringDtype()
    assert output.tolist() == ["boolean", "text", "absent"]
    assert any(
        record.boundary_key is BoundaryKey.EXPRESSION_NARWHALS_OBJECT_NATIVE_CALLBACK
        for record in trace.records
    )


def test_ibis_constructor_adapter_records_pandas_coercion():
    import ibis
    import pandas as pd

    from mountainash.relations.core.materialization import coerce_to_ibis

    target = ibis.memtable({"id": [1]})
    with capture_conversion_trace() as trace:
        result = coerce_to_ibis(target, pd.DataFrame({"id": [2, 3]}))

    assert result.to_pyarrow()["id"].to_pylist() == [2, 3]
    assert any(
        record.boundary_key is BoundaryKey.IBIS_CONSTRUCTOR_ADAPTER
        for record in trace.records
    )


def test_boundary_registry_entries_use_frozensets_for_families_and_dialects():
    for key, spec in BOUNDARY_REGISTRY.items():
        assert isinstance(spec.source_families, frozenset), key
        assert isinstance(spec.source_dialects, frozenset), key
        assert isinstance(spec.destination_families, frozenset), key
        assert isinstance(spec.destination_dialects, frozenset), key


def test_internal_execution_transit_is_always_prohibited():
    spec = BOUNDARY_REGISTRY[BoundaryKey.IBIS_INTERNAL_EXECUTE]
    assert spec.transit_class is TransitClass.INTERNAL_EXECUTION_TRANSIT
