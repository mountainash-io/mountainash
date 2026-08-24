from __future__ import annotations

import dataclasses

import pandas as pd
import polars as pl
import pytest

import mountainash as ma
from mountainash.conform.contract import resolve_contract
from mountainash.conform.diagnostics import OperationDiagnosticTrace
from mountainash.conform.errors import (
    ConformTransformError,
    IncompatibleSourceTypeError,
    UnresolvedSourceTypeError,
)
from mountainash.conform.expressions import _build_conform_exprs, resolve_conform_output
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.dtypes import MountainashDtype
from mountainash.core.limitations import enrich_materialization
from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)
from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
from mountainash.typespec.source_shape import SourceShape
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


def _spec(*fields: FieldSpec) -> TypeSpec:
    return TypeSpec(fields=list(fields), fields_match="open")


def _contract(action: str):
    return dataclasses.replace(resolve_contract("open"), data_type=action, from_preset=False)


def _compile(expr):
    return UnifiedExpressionVisitor(PolarsExpressionSystem("polars")).visit(expr._node)


def test_unknown_list_and_default_geopoint_use_lexical_operations() -> None:
    list_result = _build_conform_exprs(
        _spec(FieldSpec(name="items", type=UniversalType.LIST, item_type="integer")),
        available_columns=("items",),
        actual_shapes={"items": SourceShape(None)},
    )
    point_result = _build_conform_exprs(
        _spec(FieldSpec(name="point", type=UniversalType.GEOPOINT, format="default")),
        available_columns=("point",),
        actual_shapes={"point": SourceShape(None)},
    )
    assert list_result.exprs[0].node.arguments[0].function_key.name == "PARSE"
    assert point_result.exprs[0].node.arguments[0].function_key.name == "PARSE_GEOPOINT"


def test_unknown_native_shapes_remain_unresolved() -> None:
    with pytest.raises(UnresolvedSourceTypeError):
        _build_conform_exprs(
            _spec(FieldSpec(name="items", type=UniversalType.ARRAY)),
            available_columns=("items",),
            actual_shapes={"items": SourceShape(None)},
        )
    with pytest.raises(UnresolvedSourceTypeError):
        _build_conform_exprs(
            _spec(FieldSpec(name="point", type=UniversalType.GEOPOINT, format="array")),
            available_columns=("point",),
            actual_shapes={"point": SourceShape(None)},
        )


@pytest.mark.parametrize("action", ["evolve", "discard_value", "discard_row"])
def test_incompatible_concrete_source_uses_data_type_action(action: str) -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="items", type=UniversalType.LIST, item_type="integer")),
        available_columns=("items",),
        actual_shapes={"items": SourceShape(MountainashDtype.STRUCT)},
        contract=_contract(action),
    )
    assert len(result.exprs) == 1
    if action == "evolve":
        assert result.row_filters == []
    else:
        assert result.exprs[0].node.function_key.name == "ALIAS"
        if action == "discard_row":
            assert len(result.row_filters) == 1


def test_incompatible_concrete_source_still_raises_in_coerce() -> None:
    with pytest.raises(IncompatibleSourceTypeError):
        _build_conform_exprs(
            _spec(FieldSpec(name="items", type=UniversalType.LIST, item_type="integer")),
            available_columns=("items",),
            actual_shapes={"items": SourceShape(MountainashDtype.STRUCT)},
            contract=_contract("coerce"),
        )

def test_incompatible_relation_actions_are_materialized() -> None:
    frame = pl.DataFrame({"items": [{"id": 1}, None]})
    spec = _spec(FieldSpec(name="items", type=UniversalType.LIST, item_type="integer"))

    evolved = ma.relation(frame).conform(spec, contract={"data_type": "evolve"}).to_polars()
    assert evolved["items"].dtype == pl.Struct({"id": pl.Int64})

    discarded = ma.relation(frame).conform(
        spec, contract={"data_type": "discard_value"}
    ).to_polars()
    assert discarded["items"].dtype == pl.List(pl.Int64)
    assert discarded["items"].to_list() == [None, None]

    rows = ma.relation(frame).conform(
        spec, contract={"data_type": "discard_row"}
    ).to_polars()
    assert rows["items"].to_list() == [None]


def test_plain_native_container_shapes_are_wildcards() -> None:
    list_result = resolve_conform_output(
        _spec(FieldSpec(name="items", type=UniversalType.ARRAY)),
        available_columns=("items",),
        actual_shapes={"items": SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64))},
        contract=_contract("freeze"),
        raise_on_freeze=False,
    )
    object_result = resolve_conform_output(
        _spec(FieldSpec(name="record", type=UniversalType.OBJECT)),
        available_columns=("record",),
        actual_shapes={
            "record": SourceShape(
                MountainashDtype.STRUCT,
                struct_fields=(("id", SourceShape(MountainashDtype.I64)),),
            )
        },
        contract=_contract("freeze"),
        raise_on_freeze=False,
    )
    assert list_result.drift.type_mismatches == []
    assert object_result.drift.type_mismatches == []


@pytest.mark.parametrize("child", [MountainashDtype.I64, MountainashDtype.U32, MountainashDtype.FP32])
def test_geopoint_numeric_children_are_shape_compatible(child: MountainashDtype) -> None:
    result = resolve_conform_output(
        _spec(FieldSpec(name="point", type=UniversalType.GEOPOINT, format="array")),
        available_columns=("point",),
        actual_shapes={"point": SourceShape(MountainashDtype.LIST, SourceShape(child))},
        contract=_contract("freeze"),
        raise_on_freeze=False,
    )
    assert result.drift.type_mismatches == []


def test_integer_categories_resolve_declared_base_type() -> None:
    result = resolve_conform_output(
        _spec(FieldSpec(name="status", type=UniversalType.INTEGER, categories=[1, 2])),
        available_columns=("status",),
    )
    assert result.emitted[0].declared_type is MountainashDtype.I64


def test_polars_default_datetime_uses_exact_grammar_and_utc_naive() -> None:
    expr = ma.col("value").dt.parse_default(field_name="value")
    result = pl.DataFrame(
        {
            "value": [
                "2024-01-02T03:04:05Z",
                "2024-01-02T03:04:05.123+02:00",
            ]
        }
    ).select(_compile(expr))
    assert result["value"].to_list() == [
        __import__("datetime").datetime(2024, 1, 2, 3, 4, 5),
        __import__("datetime").datetime(2024, 1, 2, 1, 4, 5, 123000),
    ]
    spec = _spec(FieldSpec(name="value", type=UniversalType.DATETIME))
    public = ma.relation(
        pl.DataFrame({"value": ["2024-01-02T03:04:05+02:00"]})
    ).conform(spec).to_polars()
    assert public["value"].to_list() == [__import__("datetime").datetime(2024, 1, 2, 1, 4, 5)]
    for value in ("2024-01-02", "2024-01-02 03:04:05"):
        with pytest.raises(Exception):
            pl.DataFrame({"value": [value]}).select(_compile(expr))
        with pytest.raises(ConformTransformError):
            ma.relation(pl.DataFrame({"value": [value]})).conform(spec).to_polars()


def test_native_geojson_serializer_preserves_top_level_null() -> None:
    expr = ma.col("geometry").geo.serialize_geojson(format="default", field_name="geometry")
    result = pl.DataFrame({"geometry": [None, {"type": "Point", "coordinates": [1, 2]}]}).select(
        _compile(expr).alias("geometry")
    )
    assert result["geometry"].to_list() == [None, '{"type":"Point","coordinates":[1,2]}']


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, "0000"), (1, "0001"), (-1, "-0001"), (2024, "2024"), (None, None)],
)
def test_integer_year_normalizes_before_xsd_validation(value, expected) -> None:
    result = ma.relation(pl.DataFrame({"year": [value]})).conform(
        _spec(FieldSpec(name="year", type=UniversalType.YEAR)),
    ).to_polars()
    assert result["year"].to_list() == [expected]


def test_polars_xsd_coerce_keeps_throw_behavior() -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="duration", type=UniversalType.DURATION)),
        available_columns=("duration",),
    )
    node = result.exprs[0].node
    assert node.arguments[0].options.get("failure_behavior", "throw") == "throw"
    with pytest.raises(ConformTransformError):
        ma.relation(pl.DataFrame({"duration": ["invalid"]})).conform(
            _spec(FieldSpec(name="duration", type=UniversalType.DURATION)),
        ).to_polars()


def test_supported_throw_materialization_wraps_when_no_residue_fact() -> None:
    class Backend:
        backend_type = CONST_BACKEND.POLARS
        dialect = "polars"
        BACKEND_NAME = "polars"

    trace = OperationDiagnosticTrace()
    from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode

    trace.record(
        ScalarFunctionNode(
            function_key=FK_DT.PARSE_DEFAULT,
            arguments=[FieldReferenceNode(field="value")],
            options={"failure_behavior": "throw"},
            diagnostic_context={"field_name": "value", "logical_type": "datetime", "format": "default"},
        ),
        backend_family=CONST_BACKEND.POLARS.value,
        dialect="polars",
        conform_node_id="conform:0",
    )
    original = ValueError("invalid datetime")
    with pytest.raises(ConformTransformError) as raised:
        enrich_materialization(
            Backend(),
            lambda: (_ for _ in ()).throw(original),
            diagnostic_trace=trace,
        )
    assert raised.value.original_error is original
    assert raised.value.candidates[0].field_name == "value"


def test_pandas_unknown_lexical_fields_reach_operation_dispatch() -> None:
    list_spec = _spec(FieldSpec(name="items", type=UniversalType.LIST, item_type="integer"))
    with pytest.raises(Exception) as raised:
        ma.relation(pd.DataFrame({"items": ["1,2"]})).conform(list_spec).to_polars()
    assert not isinstance(raised.value, UnresolvedSourceTypeError)

    point_spec = _spec(FieldSpec(name="point", type=UniversalType.GEOPOINT, format="default"))
    result = ma.relation(pd.DataFrame({"point": ["1,2"]})).conform(point_spec).to_polars()
    assert result["point"].to_list() == ["1,2"]
