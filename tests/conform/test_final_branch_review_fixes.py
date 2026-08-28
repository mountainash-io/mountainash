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
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
    CaseFailureBehaviour,
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
    conformed = ma.relation(pd.DataFrame({"items": ["not-json"]})).conform(
        _spec(FieldSpec(name="items", type=UniversalType.ARRAY))
    )
    with pytest.raises(
        ConformTransformError,
        match=r"invalid array value in field 'items' at row ordinal 0",
    ):
        conformed.to_polars()
    with pytest.raises(UnresolvedSourceTypeError):
        _build_conform_exprs(
            _spec(FieldSpec(name="point", type=UniversalType.GEOPOINT, format="array")),
            available_columns=("point",),
            actual_shapes={"point": SourceShape(None)},
        )


def test_unknown_any_source_passes_through_without_synthetic_drift() -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="value", type=UniversalType.ANY)),
        available_columns=("value",),
        actual_shapes={"value": SourceShape(None)},
    )
    assert result.exprs[0].node.function_key.name == "ALIAS"
    assert result.drift is not None
    assert result.drift.type_mismatches == []


def test_any_string_source_normalizes_missing_sentinels() -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="value", type=UniversalType.ANY)),
        available_columns=("value",),
        actual_shapes={"value": SourceShape(MountainashDtype.STRING)},
    )
    output = pl.DataFrame({"value": ["", "kept"]}).select(_compile(result.exprs[0]))
    assert output["value"].to_list() == [None, "kept"]


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


@pytest.mark.parametrize(
    ("format_name", "actual_shape"),
    [
        ("array", SourceShape(MountainashDtype.LIST, SourceShape(None))),
        (
            "object",
            SourceShape(
                MountainashDtype.STRUCT,
                struct_fields=(
                    ("lon", SourceShape(None)),
                    ("lat", SourceShape(MountainashDtype.I64)),
                ),
            ),
        ),
    ],
    ids=["array-child", "object-child"],
)
def test_unknown_geopoint_numeric_child_reports_shape_drift(
    format_name: str, actual_shape: SourceShape
) -> None:
    result = resolve_conform_output(
        _spec(FieldSpec(name="point", type=UniversalType.GEOPOINT, format=format_name)),
        available_columns=("point",),
        actual_shapes={"point": actual_shape},
        contract=_contract("freeze"),
        raise_on_freeze=False,
    )
    assert len(result.drift.type_mismatches) == 1
    assert result.drift.type_mismatches[0].reason == "shape"


@pytest.mark.parametrize("failure_behavior", CaseFailureBehaviour)
@pytest.mark.parametrize(
    "document",
    [
        '{"type":"Point","coordinates":[NaN,0]}',
        '{"type":"Point","coordinates":[Infinity,0]}',
        '{"type":"Point","coordinates":[-Infinity,0]}',
    ],
    ids=["nan", "infinity", "negative-infinity"],
)
def test_polars_geojson_rejects_nonfinite_json_constants(
    failure_behavior: CaseFailureBehaviour, document: str
) -> None:
    expr = ma.col("geometry").geo.parse_geojson(
        format="default",
        field_name="geometry",
        failure_behavior=failure_behavior,
    )
    compiled = _compile(expr).alias("geometry")
    if failure_behavior is CaseFailureBehaviour.THROW:
        with pytest.raises(Exception):
            pl.DataFrame({"geometry": [document]}).select(compiled)
    else:
        result = pl.DataFrame({"geometry": [document]}).select(compiled)
        assert result["geometry"].to_list() == [None]


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
    [(0, "0000"), (1, "0001"), (-1, "-0001"), (2024, "2024")],
)
def test_integer_year_normalizes_before_xsd_validation(value, expected) -> None:
    result = ma.relation(pl.DataFrame({"year": [value]})).conform(
        _spec(FieldSpec(name="year", type=UniversalType.YEAR)),
    ).to_polars()
    assert result["year"].to_list() == [expected]

def test_integer_year_preserves_null_with_known_integer_schema() -> None:
    result = ma.relation(pl.DataFrame({"year": [2024, None]})).conform(
        _spec(FieldSpec(name="year", type=UniversalType.YEAR)),
    ).to_polars()
    assert result["year"].to_list() == ["2024", None]


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


@pytest.mark.parametrize(
    ("field_type", "shape"),
    [
        (UniversalType.LIST, SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64))),
        (UniversalType.INTEGER, SourceShape(MountainashDtype.LIST)),
        (UniversalType.INTEGER, SourceShape(MountainashDtype.STRUCT)),
        (UniversalType.INTEGER, SourceShape(MountainashDtype.TIMESTAMP)),
    ],
    ids=["lexical-list-native-list", "integer-list", "integer-struct", "integer-timestamp"],
)
def test_source_representation_dispatch_rejects_incompatible_shapes(
    field_type: UniversalType, shape: SourceShape
) -> None:
    with pytest.raises(IncompatibleSourceTypeError):
        _build_conform_exprs(
            _spec(FieldSpec(name="value", type=field_type)),
            available_columns=("value",),
            actual_shapes={"value": shape},
        )


@pytest.mark.parametrize(
    "field",
    [
        FieldSpec(name="items", type=UniversalType.ARRAY),
        FieldSpec(name="record", type=UniversalType.OBJECT),
        FieldSpec(name="point", type=UniversalType.GEOPOINT, format="array"),
    ],
)
def test_evolve_unknown_native_source_bypasses_shape_resolution(field: FieldSpec) -> None:
    result = _build_conform_exprs(
        _spec(field),
        available_columns=(field.name,),
        actual_shapes={field.name: SourceShape(None)},
        contract=_contract("evolve"),
    )
    assert len(result.exprs) == 1
    mismatch = result.drift.type_mismatches[0]
    assert mismatch.action == "evolve"
    assert mismatch.applied is False


@pytest.mark.parametrize("action", ["evolve", "freeze"])
def test_non_transforming_data_type_actions_are_not_marked_applied(action: str) -> None:
    result = resolve_conform_output(
        _spec(FieldSpec(name="value", type=UniversalType.INTEGER)),
        available_columns=("value",),
        actual_shapes={"value": SourceShape(MountainashDtype.STRING)},
        contract=_contract(action),
        raise_on_freeze=False,
    )
    assert result.drift.type_mismatches[0].applied is False


def test_canonical_json_source_revalidates_through_geojson_parser() -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="geometry", type=UniversalType.GEOJSON)),
        available_columns=("geometry",),
        actual_shapes={"geometry": SourceShape(MountainashDtype.JSON)},
    )
    assert result.exprs[0].node.arguments[0].function_key.name == "PARSE_GEOJSON"


def test_geopoint_object_shape_comparison_ignores_child_order() -> None:
    result = resolve_conform_output(
        _spec(FieldSpec(name="point", type=UniversalType.GEOPOINT, format="object")),
        available_columns=("point",),
        actual_shapes={
            "point": SourceShape(
                MountainashDtype.STRUCT,
                struct_fields=(
                    ("lat", SourceShape(MountainashDtype.FP64)),
                    ("lon", SourceShape(MountainashDtype.FP64)),
                ),
            )
        },
        contract=_contract("freeze"),
        raise_on_freeze=False,
    )
    assert result.drift.type_mismatches == []

@pytest.mark.parametrize(
    ("field", "shape"),
    [
        (
            FieldSpec(name="items", type=UniversalType.ARRAY),
            SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64)),
        ),
        (
            FieldSpec(name="record", type=UniversalType.OBJECT),
            SourceShape(
                MountainashDtype.STRUCT,
                struct_fields=(("id", SourceShape(MountainashDtype.I64)),),
            ),
        ),
    ],
    ids=["plain-array", "plain-object"],
)
def test_plain_native_container_without_child_schema_preserves_source(
    field: FieldSpec, shape: SourceShape
) -> None:
    result = _build_conform_exprs(
        _spec(field),
        available_columns=(field.name,),
        actual_shapes={field.name: shape},
    )
    assert result.exprs[0].node.function_key.name == "ALIAS"


@pytest.mark.parametrize(
    "shape",
    [
        SourceShape(MountainashDtype.LIST),
        SourceShape(MountainashDtype.STRUCT),
        SourceShape(MountainashDtype.JSON),
    ],
    ids=["list", "struct", "json"],
)
def test_any_accepts_every_physical_container_representation(shape: SourceShape) -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="value", type=UniversalType.ANY)),
        available_columns=("value",),
        actual_shapes={"value": shape},
    )
    assert result.exprs[0].node.function_key.name == "ALIAS"


@pytest.mark.parametrize(
    "source",
    [MountainashDtype.DATE, MountainashDtype.TIME, MountainashDtype.TIMESTAMP],
    ids=["date", "time", "timestamp"],
)
def test_native_temporal_sources_can_cast_to_string(source: MountainashDtype) -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="value", type=UniversalType.STRING)),
        available_columns=("value",),
        actual_shapes={"value": SourceShape(source)},
    )
    assert result.exprs[0].node.function_key.name == "ALIAS"

def test_native_duration_source_uses_configured_action() -> None:
    with pytest.raises(IncompatibleSourceTypeError):
        _build_conform_exprs(
            _spec(FieldSpec(name="value", type=UniversalType.DURATION)),
            available_columns=("value",),
            actual_shapes={"value": SourceShape(MountainashDtype.DURATION)},
        )
    evolved = _build_conform_exprs(
        _spec(FieldSpec(name="value", type=UniversalType.DURATION)),
        available_columns=("value",),
        actual_shapes={"value": SourceShape(MountainashDtype.DURATION)},
        contract=_contract("evolve"),
    )
    assert evolved.exprs[0].node.function_key.name == "ALIAS"


def test_year_accepts_integer_source_but_rejects_float() -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="year", type=UniversalType.YEAR)),
        available_columns=("year",),
        actual_shapes={"year": SourceShape(MountainashDtype.I32)},
    )
    assert result.exprs[0].node.function_key.name == "ALIAS"
    with pytest.raises(IncompatibleSourceTypeError):
        _build_conform_exprs(
            _spec(FieldSpec(name="year", type=UniversalType.YEAR)),
            available_columns=("year",),
            actual_shapes={"year": SourceShape(MountainashDtype.FP64)},
        )


@pytest.mark.parametrize(
    "field_type",
    [
        UniversalType.DATE,
        UniversalType.TIME,
        UniversalType.DATETIME,
        UniversalType.DURATION,
        UniversalType.YEARMONTH,
    ],
)
def test_numeric_sources_cannot_feed_temporal_fields(field_type: UniversalType) -> None:
    with pytest.raises(IncompatibleSourceTypeError):
        _build_conform_exprs(
            _spec(FieldSpec(name="value", type=field_type)),
            available_columns=("value",),
            actual_shapes={"value": SourceShape(MountainashDtype.FP64)},
        )


@pytest.mark.parametrize(
    ("field_type", "format_name"),
    [
        (UniversalType.DATE, "%Y/%m/%d"),
        (UniversalType.TIME, "%H:%M:%S"),
        (UniversalType.DATETIME, "%Y/%m/%d %H:%M:%S"),
        (UniversalType.DATE, "any"),
        (UniversalType.TIME, "any"),
        (UniversalType.DATETIME, "any"),
        (UniversalType.YEAR, None),
    ],
    ids=["date-custom", "time-custom", "datetime-custom", "date-any", "time-any", "datetime-any", "year"],
)
def test_unknown_custom_temporal_and_year_sources_require_shape_evidence(
    field_type: UniversalType, format_name: str | None
) -> None:
    field = FieldSpec(name="value", type=field_type, format=format_name)
    with pytest.raises(UnresolvedSourceTypeError):
        _build_conform_exprs(
            _spec(field),
            available_columns=("value",),
            actual_shapes={"value": SourceShape(None)},
        )
    evolved = _build_conform_exprs(
        _spec(field),
        available_columns=("value",),
        actual_shapes={"value": SourceShape(None)},
        contract=_contract("evolve"),
    )
    assert evolved.exprs[0].node.function_key.name == "ALIAS"


@pytest.mark.parametrize(
    "field_type",
    [UniversalType.DATE, UniversalType.TIME, UniversalType.DATETIME],
)
def test_unknown_default_temporal_sources_keep_lexical_dispatch(field_type: UniversalType) -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="value", type=field_type)),
        available_columns=("value",),
        actual_shapes={"value": SourceShape(None)},
    )
    assert result.exprs[0].node.function_key.name == "ALIAS"


@pytest.mark.parametrize("field_type", [UniversalType.DURATION, UniversalType.YEARMONTH])
def test_unknown_lexical_duration_and_yearmonth_keep_dispatch(field_type: UniversalType) -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="value", type=field_type)),
        available_columns=("value",),
        actual_shapes={"value": SourceShape(None)},
    )
    assert result.exprs[0].node.function_key.name == "ALIAS"

@pytest.mark.parametrize(
    "field",
    [
        FieldSpec(name="items", type=UniversalType.ARRAY),
        FieldSpec(name="record", type=UniversalType.OBJECT),
        FieldSpec(name="value", type=UniversalType.DATE, format="%Y/%m/%d"),
        FieldSpec(name="value", type=UniversalType.YEAR),
    ],
    ids=["array", "object", "custom-date", "year"],
)
def test_absent_source_shape_evidence_is_unresolved(
    field: FieldSpec, monkeypatch: pytest.MonkeyPatch
) -> None:
    if field.type in {UniversalType.ARRAY, UniversalType.OBJECT}:
        source_shape_module = __import__(
            "mountainash.typespec.source_shape",
            fromlist=["extract_source_shapes"],
        )
        monkeypatch.setattr(source_shape_module, "extract_source_shapes", lambda _: {})
        conformed = ma.relation(
            pl.DataFrame({field.name: ["not-json"]})
        ).conform(_spec(field))
        expected_root = field.type.value
        with pytest.raises(
            ConformTransformError,
            match=rf"invalid {expected_root} value in field '{field.name}' at row ordinal 0",
        ):
            conformed.to_polars()
    else:
        with pytest.raises(UnresolvedSourceTypeError):
            _build_conform_exprs(
                _spec(field),
                available_columns=(field.name,),
                actual_shapes={},
            )
    evolved = _build_conform_exprs(
        _spec(field),
        available_columns=(field.name,),
        actual_shapes={},
        contract=_contract("evolve"),
    )
    assert evolved.exprs[0].node.function_key.name == "ALIAS"


def test_absent_any_source_shape_evidence_passes_through() -> None:
    result = _build_conform_exprs(
        _spec(FieldSpec(name="value", type=UniversalType.ANY)),
        available_columns=("value",),
        actual_shapes={},
    )
    assert result.exprs[0].node.function_key.name == "ALIAS"
    assert result.drift is not None
    assert result.drift.type_mismatches == []

def test_missing_dotted_source_shape_evidence_is_unresolved() -> None:
    field = FieldSpec(
        name="value",
        type=UniversalType.ARRAY,
        rename_from="payload.value",
    )
    with pytest.raises(UnresolvedSourceTypeError):
        _build_conform_exprs(
            _spec(field),
            available_columns=("payload",),
            actual_shapes={"payload": SourceShape(MountainashDtype.STRUCT)},
        )
