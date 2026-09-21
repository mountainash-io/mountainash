"""Cross-backend behavior smoke coverage for Unit C structural operations."""
from __future__ import annotations

from datetime import date, datetime, time

import polars as pl
import pandas as pd
import pytest

import mountainash as ma
from mountainash.core.capabilities.identity import BackendIdentity
from mountainash.core.capabilities.policy import (
    _CapabilityTarget, _new_execution_context, _prepare_capability_context,
    _resolve_policy,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.backends.expression_systems.ibis import IbisExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals import NarwhalsExpressionSystem
from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_BOOLEAN as FK_BOOL,
    FKEY_MOUNTAINASH_SCALAR_CATEGORICAL as FK_CAT,
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT,
    FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL as FK_GEO,
)
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
    CaseFailureBehaviour,
)
from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.core.types import BackendCapabilityError
from tests.fixtures.backend_helpers import BackendDataFrameFactory, BackendResultHelper
from fixtures.backend_registry import ALL_BACKENDS

_SYSTEM_SPECS = {
    "polars": (PolarsExpressionSystem, CONST_BACKEND.POLARS, "polars"),
    "polars-lazy": (PolarsExpressionSystem, CONST_BACKEND.POLARS, "polars"),
    "pandas": (NarwhalsExpressionSystem, CONST_BACKEND.NARWHALS, "narwhals-pandas"),
    "narwhals-pandas": (NarwhalsExpressionSystem, CONST_BACKEND.NARWHALS, "narwhals-pandas"),
    "narwhals-polars": (NarwhalsExpressionSystem, CONST_BACKEND.NARWHALS, "narwhals-polars"),
    "narwhals-lazy": (NarwhalsExpressionSystem, CONST_BACKEND.NARWHALS, "narwhals-lazy"),
    "ibis-duckdb": (IbisExpressionSystem, CONST_BACKEND.IBIS, "ibis-duckdb"),
    "ibis-polars": (IbisExpressionSystem, CONST_BACKEND.IBIS, "ibis-polars"),
    "ibis-sqlite": (IbisExpressionSystem, CONST_BACKEND.IBIS, "ibis-sqlite"),
}


def _visitor_for(backend_name, *, input_data=None):
    system_cls, family, dialect = _SYSTEM_SPECS[backend_name]
    policy = _resolve_policy()
    if input_data is None:
        # A dialect-only compile fixture has no actual native engine owner.
        target = _CapabilityTarget(BackendIdentity(family, dialect), owner=object())
        context = _prepare_capability_context(policy, target, package_versions={})
    else:
        context = _new_execution_context(input_data, policy=policy)
    system = system_cls(dialect=dialect, execution_context=context)
    return UnifiedExpressionVisitor(
        system, input_data=input_data, execution_context=context,
    )


def _compile_for(backend_name: str, expr):
    return _visitor_for(backend_name).visit(expr._node)


def _compile(expr):
    return _compile_for("polars", expr)


def _extract(backend_name: str, data: dict, compiled, column: str):
    frame = BackendDataFrameFactory.create(data, backend_name)
    return BackendResultHelper.select_and_extract(frame, compiled, column, backend_name)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_list_parse_has_explicit_backend_contract(backend_name: str) -> None:
    expr = ma.col("values").str.parse_list(item_type="string", delimiter="|", field_name="values")
    visitor = lambda: _compile_for(backend_name, expr)
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError) as error:
            visitor()
        assert error.value.function_key is FK_LIST.PARSE
        return
    compiled = visitor()
    frame = BackendDataFrameFactory.create({"values": ["1|2", "3|4"]}, backend_name)
    if backend_name in {"pandas", "narwhals-pandas"}:
        with pytest.raises(TypeError):
            BackendResultHelper.select_and_extract(frame, compiled, "values", backend_name)
    else:
        assert BackendResultHelper.select_and_extract(
            frame, compiled, "values", backend_name,
        ) == [["1", "2"], ["3", "4"]]



def test_polars_list_parse_covers_custom_delimiter_and_complete_null_failure() -> None:
    expr = ma.col("values").str.parse_list(item_type="integer", delimiter="|", field_name="values")
    result = pl.DataFrame({"values": ["1|2", "3|4"]}).select(_compile(expr))
    assert result.to_series().to_list() == [[1, 2], [3, 4]]





@pytest.mark.parametrize("backend_name", ("polars", "ibis-duckdb"))
def test_boolean_invalid_item_invalidates_complete_list(backend_name: str) -> None:
    """Exercise the two implementations with atomic nullable list parsing."""
    expr = ma.col("values").str.parse_list(
        item_type="boolean",
        delimiter="|",
        field_name="values",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    frame = BackendDataFrameFactory.create(
        {"values": ["true|false", "true|tRuE", None]}, backend_name,
    )
    compiled = _visitor_for(backend_name, input_data=frame).visit(expr._node)
    assert BackendResultHelper.select_and_extract(
        frame, compiled, "values", backend_name,
    ) == [[True, False], None, None]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_boolean_valid_tokens_preserve_null(backend_name: str) -> None:
    if backend_name == "ibis-sqlite":
        throw_expr = ma.col("values").parse_boolean(
            true_values=("yes",), false_values=("no",), field_name="values",
        )
        with pytest.raises(BackendCapabilityError) as error:
            _compile_for(backend_name, throw_expr)
        assert error.value.function_key is FK_BOOL.PARSE_TOKENS

    expr = ma.col("values").parse_boolean(
        true_values=("yes",),
        false_values=("no",),
        field_name="values",
        failure_behavior=(
            CaseFailureBehaviour.NULL
            if backend_name == "ibis-sqlite"
            else CaseFailureBehaviour.THROW
        ),
    )
    frame = BackendDataFrameFactory.create({"values": ["yes", "no", None]}, backend_name)
    compiled = _visitor_for(backend_name, input_data=frame).visit(expr._node)
    values = BackendResultHelper.select_and_extract(
        frame, compiled, "values", backend_name,
    )
    assert values[:2] == [True, False]
    assert len(values) == 3 and pd.isna(values[2])

def test_ibis_boolean_list_parser_uses_closed_frictionless_tokens() -> None:
    expr = ma.col("values").str.parse_list(
        item_type="boolean", delimiter="|", field_name="values",
    )
    frame = BackendDataFrameFactory.create(
        {"values": ["true|True|TRUE|1|false|False|FALSE|0"]},
        "ibis-duckdb",
    )
    compiled = _visitor_for("ibis-duckdb", input_data=frame).visit(expr._node)
    assert BackendResultHelper.select_and_extract(
        frame, compiled, "values", "ibis-duckdb",
    ) == [[True, True, True, True, False, False, False, False]]


def test_ibis_boolean_list_parser_rejects_mixed_case_tokens() -> None:
    expr = ma.col("values").str.parse_list(
        item_type="boolean", delimiter="|", field_name="values",
    )
    frame = BackendDataFrameFactory.create({"values": ["tRuE|false"]}, "ibis-duckdb")
    compiled = _visitor_for("ibis-duckdb", input_data=frame).visit(expr._node)
    with pytest.raises(Exception):
        BackendResultHelper.select_and_extract(frame, compiled, "values", "ibis-duckdb")
def test_polars_recursive_array_struct_cast() -> None:
    field = FieldSpec(name="id", type=UniversalType.INTEGER)
    expr = ma.col("items").list.cast_items(item_object_fields=(field,), field_name="items")
    result = pl.DataFrame({"items": [[{"id": "1"}, {"id": "2"}]]}).select(_compile(expr))
    assert result.to_series().to_list() == [[{"id": 1}, {"id": 2}]]


def test_polars_nested_null_mode_cast_is_atomic() -> None:
    nested = FieldSpec(
        name="payload",
        type=UniversalType.OBJECT,
        object_fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
    )
    expr = ma.col("items").list.cast_items(
        item_object_fields=(nested,),
        failure_behavior=CaseFailureBehaviour.NULL,
        field_name="items",
    )
    frame = pl.DataFrame({"items": [[{"payload": {"id": "bad"}}]]})
    result = frame.select(_compile(expr))
    assert result.to_series().to_list() == [None]


def test_polars_struct_and_categorical_preserve_base_values() -> None:
    field = FieldSpec(name="id", type=UniversalType.INTEGER)
    struct = ma.col("payload").struct.cast(fields=(field,), field_name="payload")
    cat = ma.col("status").cat.cast(value_type="integer", categories=(1, 2), ordered=True, field_name="status")
    frame = pl.DataFrame({"payload": [{"id": "1"}], "status": ["2"]})
    out = frame.select([_compile(struct).alias("payload"), _compile(cat).alias("status")])
    assert out["payload"].to_list() == [{"id": 1}]
    assert out["status"].to_list() == [2]

@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars"])
def test_boolean_list_parser_uses_only_closed_frictionless_tokens(backend_name: str) -> None:
    expr = ma.col("values").str.parse_list(
        item_type="boolean", delimiter="|", field_name="values",
    )
    frame = BackendDataFrameFactory.create(
        {"values": ["true|True|TRUE|1|false|False|FALSE|0"]},
        backend_name,
    )
    compiled = _visitor_for(backend_name, input_data=frame).visit(expr._node)
    assert BackendResultHelper.select_and_extract(
        frame, compiled, "values", backend_name,
    ) == [[True, True, True, True, False, False, False, False]]


def test_narwhals_pandas_boolean_list_fails_at_materialization() -> None:
    expr = ma.col("values").str.parse_list(
        item_type="boolean", delimiter="|", field_name="values",
    )
    frame = BackendDataFrameFactory.create({"values": ["true|false"]}, "narwhals-pandas")
    compiled = _visitor_for("narwhals-pandas", input_data=frame).visit(expr._node)
    with pytest.raises(TypeError):
        BackendResultHelper.select_and_extract(frame, compiled, "values", "narwhals-pandas")


def test_null_list_item_type_refusal_is_public() -> None:
    expr = ma.col("values").str.parse_list(
        item_type="integer",
        delimiter="|",
        field_name="values",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    with pytest.raises(BackendCapabilityError) as error:
        _visitor_for("narwhals-polars").visit(expr._node)
    assert error.value.function_key is FK_LIST.PARSE


def test_conditioned_null_list_fact_does_not_block_supported_item_type() -> None:
    expr = ma.col("values").str.parse_list(
        item_type="string",
        delimiter="|",
        field_name="values",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    frame = BackendDataFrameFactory.create({"values": ["a|b"]}, "narwhals-polars")
    compiled = _visitor_for("narwhals-polars", input_data=frame).visit(expr._node)
    assert BackendResultHelper.select_and_extract(
        frame, compiled, "values", "narwhals-polars",
    ) == [["a", "b"]]


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars"])
def test_boolean_list_parser_rejects_mixed_case_tokens(backend_name: str) -> None:
    expr = ma.col("values").str.parse_list(
        item_type="boolean", delimiter="|", field_name="values",
    )
    frame = BackendDataFrameFactory.create({"values": ["tRuE|false"]}, backend_name)
    compiled = _visitor_for(backend_name, input_data=frame).visit(expr._node)
    with pytest.raises(Exception):
        BackendResultHelper.select_and_extract(frame, compiled, "values", backend_name)


 


_LIST_ITEM_TYPES = ("string", "integer", "boolean", "number", "datetime", "date", "time")
_LIST_INPUTS = {
    "string": ("a|b", "c|d"),
    "integer": ("1|2", "3|4"),
    "boolean": ("true|False", "TRUE|0"),
    "number": ("1.5|2.5", "3.5|4.5"),
    "datetime": ("2024-01-02T03:04:05Z|2024-01-03T03:04:05Z",) * 2,
    "date": ("2024-01-02|2024-01-03", "2024-01-04|2024-01-05"),
    "time": ("03:04:05|04:05:06", "05:06:07|06:07:08"),
}


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("item_type", _LIST_ITEM_TYPES)
def test_list_parse_matrix_covers_every_item_type(
    backend_name: str, item_type: str,
) -> None:
    expr = ma.col("values").str.parse_list(
        item_type=item_type, delimiter="|", field_name="values",
    )
    build = lambda: _compile_for(backend_name, expr)
    if (
        backend_name == "ibis-sqlite"
        or (backend_name == "ibis-polars" and item_type != "string")
        or (
            backend_name in {"pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy"}
            and item_type in {"datetime", "time"}
        )
    ):
        with pytest.raises(BackendCapabilityError) as error:
            build()
        assert error.value.function_key is FK_LIST.PARSE
        return
    if backend_name in {"pandas", "narwhals-pandas"}:
        compiled = build()
        with pytest.raises(TypeError):
            _extract(
                backend_name, {"values": list(_LIST_INPUTS[item_type])},
                compiled, "values",
            )
        return
    values = _extract(
        backend_name, {"values": list(_LIST_INPUTS[item_type])}, build(), "values",
    )
    assert len(values) == 2
    assert all(value is not None and len(value) == 2 for value in values)
    if item_type == "string":
        assert values == [["a", "b"], ["c", "d"]]
    elif item_type == "integer":
        assert values == [[1, 2], [3, 4]]
    elif item_type == "boolean":
        assert values == [[True, False], [True, False]]
    elif item_type == "number":
        assert values == [[1.5, 2.5], [3.5, 4.5]]

    elif item_type == "datetime":
        assert values == [
            [datetime(2024, 1, 2, 3, 4, 5), datetime(2024, 1, 3, 3, 4, 5)],
            [datetime(2024, 1, 2, 3, 4, 5), datetime(2024, 1, 3, 3, 4, 5)],
        ]
    elif item_type == "date":
        assert values == [
            [date(2024, 1, 2), date(2024, 1, 3)],
            [date(2024, 1, 4), date(2024, 1, 5)],
        ]
    elif item_type == "time":
        assert values == [
            [time(3, 4, 5), time(4, 5, 6)],
            [time(5, 6, 7), time(6, 7, 8)],
        ]
_LIST_INVALID_INPUTS = {
    "integer": ("1|bad", "3|4"),
    "boolean": ("true|tRuE", "false|0"),
    "number": ("1.5|bad", "3.5|4.5"),
    "datetime": ("2024-01-02T03:04:05Z|bad", "2024-01-03T03:04:05Z|2024-01-04T03:04:05Z"),
    "date": ("2024-01-02|bad", "2024-01-03|2024-01-04"),
    "time": ("03:04:05|bad", "04:05:06|05:06:07"),
}


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("item_type", tuple(_LIST_INVALID_INPUTS))
@pytest.mark.parametrize(
    "failure_behavior",
    (CaseFailureBehaviour.THROW, CaseFailureBehaviour.NULL),
)
def test_list_parse_invalid_item_is_complete_value_failure(
    backend_name: str, item_type: str, failure_behavior: CaseFailureBehaviour,
) -> None:
    expr = ma.col("values").str.parse_list(
        item_type=item_type, delimiter="|", field_name="values",
        failure_behavior=failure_behavior,
    )
    build = lambda: _compile_for(backend_name, expr)
    if (
        backend_name == "ibis-sqlite"
        or (backend_name == "ibis-polars" and item_type != "string")
        or (
            backend_name in {"pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy"}
            and (
                item_type in {"datetime", "time"}
                or failure_behavior is CaseFailureBehaviour.NULL
            )
        )
    ):
        with pytest.raises(BackendCapabilityError) as error:
            build()
        assert error.value.function_key is FK_LIST.PARSE
        return
    if backend_name in {"pandas", "narwhals-pandas"}:
        compiled = build()
        with pytest.raises(TypeError):
            _extract(
                backend_name,
                {"values": list(_LIST_INVALID_INPUTS[item_type])},
                compiled,
                "values",
            )
        return
    if failure_behavior is CaseFailureBehaviour.THROW:
        with pytest.raises(Exception):
            _extract(
                backend_name,
                {"values": list(_LIST_INVALID_INPUTS[item_type])},
                build(),
                "values",
            )
    else:
        values = _extract(
            backend_name,
            {"values": list(_LIST_INVALID_INPUTS[item_type])},
            build(),
            "values",
        )
        assert values[0] is None
        expected_valid_value = {
            "integer": [3, 4],
            "boolean": [False, False],
            "number": [3.5, 4.5],
            "datetime": [datetime(2024, 1, 3, 3, 4, 5), datetime(2024, 1, 4, 3, 4, 5)],
            "date": [date(2024, 1, 3), date(2024, 1, 4)],
            "time": [time(4, 5, 6), time(5, 6, 7)],
        }[item_type]
        assert values == [None, expected_valid_value]




def _recursive_item_fields() -> tuple[FieldSpec, ...]:
    return (
        FieldSpec(
            name="payload",
            type=UniversalType.OBJECT,
            object_fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
        ),
    )


def _recursive_struct_fields() -> tuple[FieldSpec, ...]:
    return (
        FieldSpec(
            name="nested",
            type=UniversalType.OBJECT,
            object_fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
        ),
    )


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "failure_behavior",
    (CaseFailureBehaviour.THROW, CaseFailureBehaviour.NULL),
)
def test_list_cast_items_recursive_matrix(
    backend_name: str, failure_behavior: CaseFailureBehaviour,
) -> None:
    expr = ma.col("items").list.cast_items(
        item_object_fields=_recursive_item_fields(),
        failure_behavior=failure_behavior,
        field_name="items",
    )
    build = lambda: _compile_for(backend_name, expr)
    if (
        backend_name == "ibis-sqlite"
        or (
            failure_behavior is CaseFailureBehaviour.NULL
            and backend_name not in {"polars", "polars-lazy"}
        )
    ):
        with pytest.raises(BackendCapabilityError) as error:
            build()
        assert error.value.function_key is FK_LIST.CAST_ITEMS
        return
    values = _extract(
        backend_name,
        {"items": [[{"payload": {"id": "1"}}, {"payload": {"id": "2"}}]]},
        build(),
        "items",
    )
    assert values == [[{"payload": {"id": 1}}, {"payload": {"id": 2}}]]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_list_cast_items_null_mode_invalidates_complete_recursive_value(
    backend_name: str,
) -> None:
    expr = ma.col("items").list.cast_items(
        item_object_fields=_recursive_item_fields(),
        failure_behavior=CaseFailureBehaviour.NULL,
        field_name="items",
    )
    build = lambda: _compile_for(backend_name, expr)
    if backend_name not in {"polars", "polars-lazy"}:
        with pytest.raises(BackendCapabilityError) as error:
            build()
        assert error.value.function_key is FK_LIST.CAST_ITEMS
        return
    values = _extract(
        backend_name,
        {"items": [[{"payload": {"id": "bad"}}], None]},
        build(),
        "items",
    )
    assert values == [None, None]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "failure_behavior",
    (CaseFailureBehaviour.THROW, CaseFailureBehaviour.NULL),
)
def test_struct_cast_recursive_matrix(
    backend_name: str, failure_behavior: CaseFailureBehaviour,
) -> None:
    expr = ma.col("payload").struct.cast(
        fields=_recursive_struct_fields(),
        failure_behavior=failure_behavior,
        field_name="payload",
    )
    build = lambda: _compile_for(backend_name, expr)
    if (
        (
            failure_behavior is CaseFailureBehaviour.NULL
            and backend_name not in {"polars", "polars-lazy"}
        )
        or backend_name in {"pandas", "narwhals-pandas", "ibis-sqlite"}
    ):
        with pytest.raises(BackendCapabilityError) as error:
            build()
        assert error.value.function_key is FK_STRUCT.CAST
        return
    values = _extract(
        backend_name,
        {"payload": [{"nested": {"id": "1"}}]},
        build(),
        "payload",
    )
    assert values == [{"nested": {"id": 1}}]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_struct_cast_null_mode_invalidates_recursive_value(backend_name: str) -> None:
    expr = ma.col("payload").struct.cast(
        fields=_recursive_struct_fields(),
        failure_behavior=CaseFailureBehaviour.NULL,
        field_name="payload",
    )
    build = lambda: _compile_for(backend_name, expr)
    if backend_name not in {"polars", "polars-lazy"}:
        with pytest.raises(BackendCapabilityError) as error:
            build()
        assert error.value.function_key is FK_STRUCT.CAST
        return
    values = _extract(
        backend_name,
        {"payload": [{"nested": {"id": "bad"}}, None]},
        build(),
        "payload",
    )
    assert values == [None, None]

@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("value_type", ("string", "integer"))
@pytest.mark.parametrize(
    "failure_behavior",
    (CaseFailureBehaviour.THROW, CaseFailureBehaviour.NULL),
)
def test_categorical_cast_preserves_supported_base_values(
    backend_name: str, value_type: str, failure_behavior: CaseFailureBehaviour,
) -> None:
    categories = ("new", "active") if value_type == "string" else (1, 2)
    source_value = "active" if value_type == "string" else "2"
    expr = ma.col("status").cat.cast(
        value_type=value_type,
        categories=categories,
        ordered=True,
        failure_behavior=failure_behavior,
        field_name="status",
    )
    build = lambda: _compile_for(backend_name, expr)
    if (
        (backend_name == "ibis-sqlite" and value_type == "integer")
        or (
            backend_name in {"pandas", "narwhals-pandas", "narwhals-polars", "narwhals-lazy"}
            and value_type == "integer"
            and failure_behavior is CaseFailureBehaviour.NULL
        )
    ):
        with pytest.raises(BackendCapabilityError) as error:
            build()
        assert error.value.function_key is FK_CAT.CAST
        return
    values = _extract(
        backend_name, {"status": [source_value]}, build(), "status",
    )
    assert values == ([source_value] if value_type == "string" else [2])


def test_polars_geopoint_default_preserves_valid_text_and_nulls() -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="default",
        source_representation="lexical",
        field_name="point",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    result = pl.DataFrame({"point": ["1.0, 2.0", "NaN, INF", "-INF, 3", None, "bad"]}).select(_compile(expr))
    assert result.to_series().to_list() == ["1.0, 2.0", "NaN, INF", "-INF, 3", None, None]


def test_polars_geopoint_throw_rejects_invalid_native_coordinates() -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="array",
        source_representation="native",
        field_name="point",
    )
    with pytest.raises(Exception):
        pl.DataFrame({"point": [[1.0], [float("inf"), 2.0]]}).select(_compile(expr))


def test_polars_geopoint_lexical_array_parses_json_numbers() -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="array",
        source_representation="lexical",
        field_name="point",
    )
    result = pl.DataFrame({"point": ["[1,-2.5e2]"]}).select(_compile(expr))
    assert result.to_series().to_list() == [[1.0, -250.0]]


def test_polars_geopoint_native_array_rejects_wrong_length_in_null_mode() -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="array",
        source_representation="native",
        field_name="point",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    result = pl.DataFrame({"point": [[1.0], [1.0, 2.0], None]}).select(_compile(expr))
    assert result.to_series().to_list() == [None, [1.0, 2.0], None]


def test_polars_geojson_parse_and_serialize() -> None:
    parse = ma.col("geometry").geo.parse_geojson(format="default", field_name="geometry")
    parsed = pl.DataFrame({"geometry": ['{"type":"Point","coordinates":[1,2]}']}).select(_compile(parse))
    assert parsed.to_series().to_list() == ['{"type":"Point","coordinates":[1,2]}']

    serialize = ma.col("geometry").geo.serialize_geojson(format="default", field_name="geometry")
    serialized = pl.DataFrame({"geometry": [{"type": "Point", "coordinates": [1.0, 2.0]}]}).select(_compile(serialize))
    assert serialized.to_series().to_list() == ['{"type":"Point","coordinates":[1.0,2.0]}']



def test_ibis_sqlite_geopoint_default_throw_has_public_refusal() -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="default",
        source_representation="lexical",
        field_name="point",
    )
    with pytest.raises(BackendCapabilityError) as error:
        _visitor_for("ibis-sqlite").visit(expr._node)
    assert error.value.function_key is FK_GEO.PARSE_GEOPOINT


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_geopoint_default_null_mode_all_backends(backend_name: str) -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="default",
        source_representation="lexical",
        field_name="point",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    compiled = _visitor_for(backend_name).visit(expr._node)
    frame = BackendDataFrameFactory.create({"point": ["1.0, 2.0", "bad", None]}, backend_name)
    values = BackendResultHelper.select_and_extract(frame, compiled, "point", backend_name)
    assert values[0] == "1.0, 2.0"
    assert all(pd.isna(value) for value in values[1:])

@pytest.mark.parametrize("backend_name", ("narwhals-polars", "ibis-sqlite"))
def test_lexical_array_geopoint_has_public_refusal(backend_name: str) -> None:
    lexical_array = ma.col("point").geo.parse_geopoint(
        format="array",
        source_representation="lexical",
        field_name="point",
    )
    with pytest.raises(BackendCapabilityError) as error:
        _compile_for(backend_name, lexical_array)
    assert error.value.function_key is FK_GEO.PARSE_GEOPOINT


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_geojson_is_polars_only(backend_name: str) -> None:
    expr = ma.col("geometry").geo.parse_geojson(
        format="default",
        field_name="geometry",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    visitor = lambda: _compile_for(backend_name, expr)
    if backend_name in {"polars", "polars-lazy"}:
        compiled = visitor()
        frame = BackendDataFrameFactory.create(
            {"geometry": ['{"type":"Point","coordinates":[1,2]}', "[1,2]"]},
            backend_name,
        )
        assert BackendResultHelper.select_and_extract(
            frame, compiled, "geometry", backend_name
        ) == ['{"type":"Point","coordinates":[1,2]}', None]
        return
    with pytest.raises(NotImplementedError):
        visitor()


@pytest.mark.parametrize("backend_name", ["narwhals-polars", "narwhals-pandas", "ibis-duckdb", "ibis-polars"])
def test_native_geopoint_array_throw_executes_supported_backends(backend_name: str) -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="array", source_representation="native", field_name="point"
    )
    compiled = _visitor_for(backend_name).visit(expr._node)
    frame = BackendDataFrameFactory.create({"point": [[1.0, 2.0], None]}, backend_name)
    values = BackendResultHelper.select_and_extract(frame, compiled, "point", backend_name)
    assert list(values[0]) == [1.0, 2.0]
    assert pd.isna(values[1]) or values[1] is None
def _geopoint_expression(
    format_name: str,
    source_representation: str,
    failure_behavior: CaseFailureBehaviour,
):
    return ma.col("point").geo.parse_geopoint(
        format=format_name,
        source_representation=source_representation,
        field_name="point",
        failure_behavior=failure_behavior,
    )




_GEOPOINT_CELLS = (
    ("default", "lexical"),
    ("array", "lexical"),
    ("array", "native"),
    ("object", "native"),
)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    ("format_name", "source_representation"),
    _GEOPOINT_CELLS,
)
@pytest.mark.parametrize("failure_behavior", CaseFailureBehaviour)
def test_geopoint_matrix_valid_values_and_top_level_null(
    backend_name: str,
    format_name: str,
    source_representation: str,
    failure_behavior: CaseFailureBehaviour,
) -> None:
    expr = _geopoint_expression(format_name, source_representation, failure_behavior)
    if (
        format_name == "default"
        and backend_name == "ibis-sqlite"
        and failure_behavior is CaseFailureBehaviour.THROW
    ):
        with pytest.raises(BackendCapabilityError) as error:
            _compile_for(backend_name, expr)
        assert error.value.function_key is FK_GEO.PARSE_GEOPOINT
        return
    if (format_name, source_representation) == ("array", "lexical"):
        if backend_name in {"polars", "polars-lazy"}:
            pass
        elif backend_name in {
            "pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy", "ibis-sqlite",
        }:
            with pytest.raises(BackendCapabilityError) as error:
                _compile_for(backend_name, expr)
            assert error.value.function_key is FK_GEO.PARSE_GEOPOINT
            return
        else:
            with pytest.raises(NotImplementedError):
                _compile_for(backend_name, expr)
            return
    elif (format_name, source_representation) == ("array", "native") and (
        backend_name == "ibis-sqlite"
        or (
            failure_behavior is CaseFailureBehaviour.NULL
            and backend_name not in {"polars", "polars-lazy", "ibis-duckdb"}
        )
    ):
        with pytest.raises(BackendCapabilityError) as error:
            _compile_for(backend_name, expr)
        assert error.value.function_key is FK_GEO.PARSE_GEOPOINT
        return
    elif (format_name, source_representation) == ("object", "native"):
        if backend_name in {"polars", "polars-lazy", "ibis-duckdb"} or (
            backend_name == "ibis-polars"
            and failure_behavior is CaseFailureBehaviour.THROW
        ):
            pass
        elif backend_name in {"pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy"}:
            with pytest.raises(NotImplementedError):
                _compile_for(backend_name, expr)
            return
        else:
            with pytest.raises(BackendCapabilityError) as error:
                _compile_for(backend_name, expr)
            assert error.value.function_key is FK_GEO.PARSE_GEOPOINT
            return

    valid = {
        ("default", "lexical"): ["1.0, 2.0", "NaN, inf"],
        ("array", "lexical"): ["[1,-2.5e2]"],
        ("array", "native"): [[1.0, 2.0]],
        ("object", "native"): [{"lon": 1.0, "lat": 2.0}],
    }[(format_name, source_representation)]
    values = _extract(backend_name, {"point": [*valid, None]}, _compile_for(backend_name, expr), "point")
    expected = (
        [[1.0, -250.0]]
        if (format_name, source_representation) == ("array", "lexical")
        else valid
    )
    actual = values[:-1]
    if actual and hasattr(actual[0], "tolist") and not isinstance(actual[0], dict):
        actual = [value.tolist() for value in actual]
    elif actual and isinstance(actual[0], tuple):
        actual = [list(value) for value in actual]
    assert actual == expected
    assert values[-1] is None or bool(pd.isna(values[-1]))


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    ("format_name", "source_representation"),
    _GEOPOINT_CELLS,
)
@pytest.mark.parametrize("failure_behavior", CaseFailureBehaviour)
def test_geopoint_matrix_invalid_length_null_nonfinite_and_throw_or_null(
    backend_name: str,
    format_name: str,
    source_representation: str,
    failure_behavior: CaseFailureBehaviour,
) -> None:
    expr = _geopoint_expression(format_name, source_representation, failure_behavior)
    if (
        format_name == "default"
        and backend_name == "ibis-sqlite"
        and failure_behavior is CaseFailureBehaviour.THROW
    ):
        with pytest.raises(BackendCapabilityError) as error:
            _compile_for(backend_name, expr)
        assert error.value.function_key is FK_GEO.PARSE_GEOPOINT
        return
    if (format_name, source_representation) == ("array", "lexical"):
        if backend_name in {"polars", "polars-lazy"}:
            pass
        elif backend_name in {
            "pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy", "ibis-sqlite",
        }:
            with pytest.raises(BackendCapabilityError) as error:
                _compile_for(backend_name, expr)
            assert error.value.function_key is FK_GEO.PARSE_GEOPOINT
            return
        else:
            with pytest.raises(NotImplementedError):
                _compile_for(backend_name, expr)
            return
    elif (format_name, source_representation) == ("array", "native") and (
        backend_name == "ibis-sqlite"
        or (
            failure_behavior is CaseFailureBehaviour.NULL
            and backend_name not in {"polars", "polars-lazy", "ibis-duckdb"}
        )
    ):
        with pytest.raises(BackendCapabilityError) as error:
            _compile_for(backend_name, expr)
        assert error.value.function_key is FK_GEO.PARSE_GEOPOINT
        return
    elif (format_name, source_representation) == ("object", "native"):
        if backend_name in {"polars", "polars-lazy", "ibis-duckdb"} or (
            backend_name == "ibis-polars"
            and failure_behavior is CaseFailureBehaviour.THROW
        ):
            pass
        elif backend_name in {"pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy"}:
            with pytest.raises(NotImplementedError):
                _compile_for(backend_name, expr)
            return
        else:
            with pytest.raises(BackendCapabilityError) as error:
                _compile_for(backend_name, expr)
            assert error.value.function_key is FK_GEO.PARSE_GEOPOINT
            return

    invalid_values = {
        ("default", "lexical"): ["bad", "1.0,  2.0", None],
        ("array", "lexical"): ["[1]", "[1, null]", None],
        ("array", "native"): [[1.0], [1.0, None], [float("inf"), 2.0], None],
        ("object", "native"): [
            {"lon": None, "lat": 2.0},
            {"lon": float("inf"), "lat": 2.0},
            None,
        ],
    }[(format_name, source_representation)]
    if failure_behavior is CaseFailureBehaviour.THROW:
        with pytest.raises(Exception):
            _extract(
                backend_name,
                {"point": invalid_values},
                _compile_for(backend_name, expr),
                "point",
            )
        return

    values = _extract(
        backend_name,
        {"point": invalid_values},
        _compile_for(backend_name, expr),
        "point",
    )
    assert all(value is None or bool(pd.isna(value)) for value in values)


_GEOJSON_DOCUMENTS = (
    ("object", '{"type":"Point","coordinates":[1,2]}', True),
    ("empty-object", "{}", True),
    (
        "leading-whitespace-object",
        ' \n\t{"type":"Point","coordinates":[1,2]} ',
        True,
    ),
    ("null-root", "null", False),
    ("string-root", '"not an object"', False),
    ("number-root", "42", False),
    ("boolean-root", "true", False),
    ("array-root", "[]", False),
    ("malformed-json", "{bad", False),
    ("non-canonical-json", '{"type":"Point","coordinates":[1,]}', False),
)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("format_name", ("default", "topojson"))
@pytest.mark.parametrize("failure_behavior", CaseFailureBehaviour)
@pytest.mark.parametrize(
    ("document_name", "document", "valid"),
    _GEOJSON_DOCUMENTS,
    ids=[document[0] for document in _GEOJSON_DOCUMENTS],
)
def test_geojson_parse_exceptional_documents_one_per_test(
    backend_name: str,
    format_name: str,
    failure_behavior: CaseFailureBehaviour,
    document_name: str,
    document: str | None,
    valid: bool,
) -> None:
    expr = ma.col("geometry").geo.parse_geojson(
        format=format_name,
        field_name="geometry",
        failure_behavior=failure_behavior,
    )
    visitor = lambda: _compile_for(backend_name, expr)
    if backend_name not in {"polars", "polars-lazy"}:
        with pytest.raises(NotImplementedError):
            visitor()
        return

    if valid:
        values = _extract(
            backend_name,
            {"geometry": [document]},
            visitor(),
            "geometry",
        )
        assert values == [document], document_name
    elif failure_behavior is CaseFailureBehaviour.THROW:
        with pytest.raises(Exception):
            _extract(
                backend_name,
                {"geometry": [document]},
                visitor(),
                "geometry",
            )
    else:
        values = _extract(
            backend_name,
            {"geometry": [document]},
            visitor(),
            "geometry",
        )
        assert values == [None], document_name


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("format_name", ("default", "topojson"))
@pytest.mark.parametrize("failure_behavior", CaseFailureBehaviour)
def test_geojson_serialization_matrix_and_topojson_refusals(
    backend_name: str,
    format_name: str,
    failure_behavior: CaseFailureBehaviour,
) -> None:
    expr = ma.col("geometry").geo.serialize_geojson(
        format=format_name,
        field_name="geometry",
        failure_behavior=failure_behavior,
    )
    visitor = lambda: _compile_for(backend_name, expr)
    if backend_name not in {"polars", "polars-lazy"}:
        with pytest.raises(NotImplementedError):
            visitor()
        return

    compiled = visitor()
    values = _extract(
        backend_name,
        {"geometry": [{"type": "Point", "coordinates": [1.0, 2.0]}, None]},
        compiled,
        "geometry",
    )
    assert values == ['{"type":"Point","coordinates":[1.0,2.0]}', None]
