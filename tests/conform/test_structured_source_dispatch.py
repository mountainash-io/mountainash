"""Structured source-schema dispatch tests."""
from __future__ import annotations

from types import MappingProxyType

import pytest

from mountainash.conform.contract import ConformContract
from mountainash.conform.errors import IncompatibleSourceTypeError, SchemaDriftError
from mountainash.conform.expressions import _build_conform_exprs, resolve_conform_output
from mountainash.conform.structured_transport import StructuredCarrier, StructuredRoot
from mountainash.core.dtypes import MountainashDtype
from mountainash.typespec.source_shape import SourceShape
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


@pytest.mark.parametrize(
    ("declared_type", "source_type", "carrier"),
    [
        (UniversalType.ARRAY, MountainashDtype.LIST, StructuredCarrier.NATIVE),
        (UniversalType.ARRAY, MountainashDtype.STRING, StructuredCarrier.JSON_TEXT),
        (UniversalType.ARRAY, MountainashDtype.JSON, StructuredCarrier.JSON_TEXT),
        (UniversalType.ARRAY, None, StructuredCarrier.OPAQUE),
        (UniversalType.OBJECT, MountainashDtype.STRUCT, StructuredCarrier.NATIVE),
        (UniversalType.OBJECT, MountainashDtype.STRING, StructuredCarrier.JSON_TEXT),
        (UniversalType.OBJECT, MountainashDtype.JSON, StructuredCarrier.JSON_TEXT),
        (UniversalType.OBJECT, None, StructuredCarrier.OPAQUE),
    ],
)
def test_structured_source_schema_selects_a_carrier_without_decoding(
    monkeypatch,
    declared_type,
    source_type,
    carrier,
):
    """Schema evidence selects a carrier without inspecting any source value."""
    import mountainash.conform.structured_transport as transport

    def decode_must_not_run(*args, **kwargs):
        raise AssertionError("source dispatch decoded a data value")

    monkeypatch.setattr(transport, "decode_structured_value", decode_must_not_run)
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="payload", type=declared_type)],
    )

    result = _build_conform_exprs(
        spec,
        actual_shapes={"payload": SourceShape(source_type)},
        node_identity=("conform-node", None, None),
    )

    plan = result.structured_field_plans["payload"]
    assert plan.root is (
        StructuredRoot.ARRAY if declared_type is UniversalType.ARRAY else StructuredRoot.OBJECT
    )
    assert plan.carrier is carrier
    assert plan.origin_node_id == "conform-node"
    assert isinstance(result.structured_field_plans, MappingProxyType)


@pytest.mark.parametrize("declared_type", [UniversalType.ARRAY, UniversalType.OBJECT])
def test_known_incompatible_structured_source_is_rejected(declared_type):
    """A known scalar cannot be silently treated as portable structured text."""
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="payload", type=declared_type)],
    )

    with pytest.raises(IncompatibleSourceTypeError):
        _build_conform_exprs(
            spec,
            actual_shapes={"payload": SourceShape(MountainashDtype.I64)},
        )


@pytest.mark.parametrize("action", ["coerce", "discard_value", "discard_row"])
def test_applied_transport_actions_require_logical_egress_for_non_native_carriers(action):
    """Portable transformed carriers cannot leave through native terminal APIs."""
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
    )

    result = _build_conform_exprs(
        spec,
        actual_shapes={"payload": SourceShape(MountainashDtype.STRING)},
        contract=ConformContract(data_type=action, from_preset=False),
    )

    assert result.structured_field_plans["payload"].requires_logical_terminal is True


@pytest.mark.parametrize("action", ["coerce", "discard_value", "discard_row", "evolve", "freeze"])
def test_structural_only_structured_actions_do_not_require_logical_egress(action):
    """Assessment-only conformance preserves the native physical representation."""
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
    )

    result = _build_conform_exprs(
        spec,
        actual_shapes={"payload": SourceShape(MountainashDtype.STRING)},
        contract=ConformContract(data_type=action, from_preset=False),
        apply_value_transforms=False,
    )

    assert result.structured_field_plans["payload"].requires_logical_terminal is False


def test_native_structured_carrier_does_not_require_logical_egress():
    """Native list/struct values keep their zero-JSON-round-trip terminal path."""
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
    )

    result = _build_conform_exprs(
        spec,
        actual_shapes={"payload": SourceShape(MountainashDtype.LIST)},
    )

    assert result.structured_field_plans["payload"].requires_logical_terminal is False


@pytest.mark.parametrize("source_type", [MountainashDtype.STRING, MountainashDtype.JSON, None])
def test_applied_freeze_rejects_every_non_native_structured_representation(source_type):
    """Freeze rejects portable and opaque representation drift before lowering expressions."""
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
    )

    with pytest.raises(SchemaDriftError):
        _build_conform_exprs(
            spec,
            actual_shapes={"payload": SourceShape(source_type)},
            node_identity=("conform-node", None, None),
            contract=ConformContract(data_type="freeze", from_preset=False),
        )


def test_structural_only_freeze_reports_unapplied_structured_drift():
    """Assessment-only freeze records the portable representation mismatch without raising."""
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
    )

    output = resolve_conform_output(
        spec,
        actual_shapes={"payload": SourceShape(MountainashDtype.STRING)},
        contract=ConformContract(data_type="freeze", from_preset=False),
        apply_value_transforms=False,
    )

    assert output.drift is not None
    assert output.drift.type_mismatches[0].applied is False
