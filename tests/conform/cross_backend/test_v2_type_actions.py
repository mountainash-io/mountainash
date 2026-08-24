"""Task 7 evaluator and action-policy contracts."""
from __future__ import annotations

import pytest

from mountainash.conform.errors import (
    ExactFieldsMismatchError,
    IncompatibleSourceTypeError,
    UnresolvedSourceTypeError,
)
from mountainash.conform.expressions import resolve_conform_output
from mountainash.core.dtypes import MountainashDtype
from mountainash.typespec.source_shape import SourceShape
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


def _spec(*fields: FieldSpec, fields_match: str = "exact") -> TypeSpec:
    return TypeSpec(fields=list(fields), fields_match=fields_match)


@pytest.mark.parametrize(
    "actual,reason",
    [(('a',), "count"), (('a', 'c'), "name"), (('b', 'a'), "order")],
)
def test_exact_reports_stable_reason(actual: tuple[str, ...], reason: str) -> None:
    spec = _spec(FieldSpec(name="a"), FieldSpec(name="b"))
    with pytest.raises(ExactFieldsMismatchError) as exc_info:
        resolve_conform_output(spec, available_columns=actual)
    assert exc_info.value.reason == reason


def test_exact_rejects_dotted_sources_before_count() -> None:
    spec = _spec(FieldSpec(name="a", rename_from="payload.a"))
    with pytest.raises(ExactFieldsMismatchError) as exc_info:
        resolve_conform_output(spec, available_columns=("payload",))
    assert exc_info.value.reason == "nested_source"


def test_structural_only_assesses_drift_without_actions() -> None:
    spec = _spec(FieldSpec(name="a", type=UniversalType.INTEGER), fields_match="open")
    result = resolve_conform_output(
        spec,
        available_columns=("a",),
        actual_dtypes={"a": MountainashDtype.STRING},
        apply_value_transforms=False,
    )
    assert result.drift is not None
    assert result.drift.type_mismatches[0].applied is False
    assert result.drift.type_mismatches[0].action is None


def test_unknown_actual_shape_is_unknown_drift_evidence() -> None:
    spec = _spec(FieldSpec(name="a", type=UniversalType.INTEGER), fields_match="open")
    result = resolve_conform_output(
        spec,
        available_columns=("a",),
        actual_shapes={"a": SourceShape(None)},
    )
    assert result.drift is not None
    mismatch = result.drift.type_mismatches[0]
    assert mismatch.reason == "unknown"
    assert mismatch.source_detail is None


def test_equal_canonical_dtype_with_different_shape_reports_shape_drift() -> None:
    spec = _spec(FieldSpec(name="a", type=UniversalType.LIST), fields_match="open")
    result = resolve_conform_output(
        spec,
        available_columns=("a",),
        actual_shapes={"a": SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64))},
    )
    assert result.drift is not None
    mismatch = result.drift.type_mismatches[0]
    assert mismatch.reason == "shape"


def test_nested_struct_shape_detail_reports_child_types() -> None:
    spec = _spec(
        FieldSpec(
            name="record",
            type=UniversalType.OBJECT,
            object_fields=[FieldSpec(name="child", type=UniversalType.STRING)],
        ),
        fields_match="open",
    )
    result = resolve_conform_output(
        spec,
        available_columns=("record",),
        actual_shapes={
            "record": SourceShape(
                MountainashDtype.STRUCT,
                struct_fields=(("child", SourceShape(MountainashDtype.I64)),),
            )
        },
    )
    mismatch = result.drift.type_mismatches[0]
    assert mismatch.reason == "shape"
    assert "child:" in mismatch.source_detail
    assert "child:" in mismatch.requirement

def test_shape_drift_uses_configured_action() -> None:
    import dataclasses
    from mountainash.conform.contract import resolve_contract

    spec = _spec(FieldSpec(name="a", type=UniversalType.LIST), fields_match="open")
    contract = dataclasses.replace(
        resolve_contract("open"), data_type="discard_value", from_preset=False,
    )
    result = resolve_conform_output(
        spec,
        available_columns=("a",),
        actual_shapes={"a": SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64))},
        contract=contract,
    )
    assert result.drift is not None
    assert result.drift.type_mismatches[0].action == "discard_value"


def test_unresolved_and_incompatible_source_errors_are_public() -> None:
    assert issubclass(UnresolvedSourceTypeError, Exception)
    assert issubclass(IncompatibleSourceTypeError, Exception)


def test_structural_only_builder_keeps_projection_without_type_operation() -> None:
    from mountainash.conform.expressions import _build_conform_exprs
    spec = _spec(FieldSpec(name="a", type=UniversalType.INTEGER), fields_match="open")
    result = _build_conform_exprs(
        spec,
        available_columns=("a",),
        actual_shapes={"a": SourceShape(MountainashDtype.STRING)},
        apply_value_transforms=False,
    )
    assert len(result.exprs) == 1
    assert result.row_filters == []
    assert result.residue_checks == []


def test_unknown_and_incompatible_shapes_fail_before_operation_lowering() -> None:
    from mountainash.conform.expressions import _build_conform_exprs
    unknown = _spec(FieldSpec(name="items", type=UniversalType.LIST), fields_match="open")
    with pytest.raises(UnresolvedSourceTypeError):
        _build_conform_exprs(
            unknown,
            available_columns=("items",),
            actual_shapes={"items": SourceShape(None)},
        )
    incompatible = _spec(FieldSpec(name="items", type=UniversalType.LIST), fields_match="open")
    with pytest.raises(IncompatibleSourceTypeError):
        _build_conform_exprs(
            incompatible,
            available_columns=("items",),
            actual_shapes={"items": SourceShape(MountainashDtype.STRUCT)},
        )


def test_structural_only_relation_skips_cast() -> None:
    import polars as pl
    from mountainash import relation

    spec = _spec(FieldSpec(name="value", type=UniversalType.INTEGER), fields_match="open")
    result = relation(pl.DataFrame({"value": ["7"]})).conform(
        spec, apply_value_transforms=False
    ).to_polars()
    assert result["value"].to_list() == ["7"]


def test_discard_row_keeps_null_and_invalid_fill_rows() -> None:
    import polars as pl
    from mountainash import relation

    spec = _spec(
        FieldSpec(name="value", type=UniversalType.INTEGER, null_fill="bad"),
        fields_match="open",
    )
    result = relation(pl.DataFrame({"value": [None, "bad", "3", "4"]})).conform(
        spec, contract={"data_type": "discard_row"}
    ).to_polars()
    assert result["value"].to_list() == [None, 3, 4]


def test_native_scalar_list_uses_scalar_item_type_option() -> None:
    import mountainash as ma
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_LIST,
    )
    expr = ma.col("items").list.cast_items(item_type="integer", field_name="items")
    node = expr._node
    assert node.function_key is FKEY_MOUNTAINASH_SCALAR_LIST.CAST_ITEMS
    assert node.options["item_type"] == "integer"
    assert node.options["item_object_fields"] == ()


def test_boolean_coerce_parser_node_keeps_throw_failure_behavior() -> None:
    from mountainash.conform.expressions import _build_conform_exprs
    from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
    spec = _spec(FieldSpec(name="flag", type=UniversalType.BOOLEAN), fields_match="open")
    result = _build_conform_exprs(spec, available_columns=("flag",))
    nodes = []

    def walk(node):
        if isinstance(node, ScalarFunctionNode):
            nodes.append(node)
            for arg in node.arguments:
                walk(arg)

    walk(result.exprs[0].node)
    assert nodes

def test_native_scalar_list_null_action_is_atomic() -> None:
    import polars as pl
    from mountainash import relation
    spec = _spec(
        FieldSpec(name="items", type=UniversalType.LIST, item_type="integer"),
        fields_match="open",
    )
    result = relation(pl.DataFrame({"items": [["1", "bad"], ["2", "3"]]})).conform(
        spec, contract={"data_type": "discard_value"}
    ).to_polars()
    assert result["items"].to_list() == [None, [2, 3]]


def test_native_scalar_list_null_action_preserves_original_null_children() -> None:
    import polars as pl
    from mountainash import relation
    spec = _spec(
        FieldSpec(name="items", type=UniversalType.LIST, item_type="integer"),
        fields_match="open",
    )
    result = relation(pl.DataFrame({"items": [[None, "2"], ["bad", None]]})).conform(
        spec, contract={"data_type": "discard_value"}
    ).to_polars()
    assert result["items"].to_list() == [[None, 2], None]



