"""
Tests for mountainash.typespec.spec — TypeSpec, FieldSpec, FieldConstraints, SpecDiff.
"""
from __future__ import annotations

import pytest

from mountainash.core.dtypes import MountainashDtype
from mountainash.typespec.errors import (
    IncompatibleFieldPropertiesError,
    InvalidDescriptorStructure,
    InvalidKeyShapeError,
)
from mountainash.typespec.frictionless import (
    typespec_from_frictionless,
    typespec_to_frictionless,
)
from mountainash.typespec.spec import (
    FieldConstraints,
    FieldSpec,
    ForeignKey,
    ForeignKeyReference,
    LabeledValue,
    TypeSpec,
    compare_specs,
)
from mountainash.typespec.universal_types import UniversalType


class TestFieldSpec:
    # --- property/type compatibility (Section 8.7) ---

    @pytest.mark.parametrize(
        "kwargs,prop",
        [
            ({"type": UniversalType.STRING, "item_type": "integer"}, "item_type"),
            ({"type": UniversalType.STRING, "delimiter": ";"}, "delimiter"),
            ({"type": UniversalType.INTEGER, "item_type": "integer"}, "item_type"),
            (
                {"type": UniversalType.STRING,
                 "fields": {"a": FieldSpec(type=UniversalType.STRING)}},
                "dtype",
            ),
        ],
    )
    def test_incompatible_property_type_combinations_raise(self, kwargs, prop):
        with pytest.raises(IncompatibleFieldPropertiesError) as exc_info:
            FieldSpec(
                type=kwargs["type"],
                **{key: value for key, value in kwargs.items() if key != "type"},
            )
        assert exc_info.value.property_name == prop

    @pytest.mark.parametrize(
        "property_name,value",
        [("item_type", UniversalType.INTEGER), ("delimiter", "|")],
    )
    def test_array_rejects_lexical_properties(self, property_name, value):
        with pytest.raises(IncompatibleFieldPropertiesError):
            FieldSpec(type=UniversalType.ARRAY, **{property_name: value})

    def test_labeled_value_round_trip_on_categories_and_missing_values(self):
        f = FieldSpec(
            type=UniversalType.STRING,
            categories=[LabeledValue("a", "Active"), "raw"],
            missing_values=[LabeledValue("-", "Dash"), ""],
        )
        restored = typespec_from_frictionless(typespec_to_frictionless(TypeSpec(fields={"status": f})))
        rf = restored.fields["status"]
        assert list(rf.categories) == [LabeledValue("a", "Active"), "raw"]
        assert list(rf.missing_values) == [LabeledValue("-", "Dash"), ""]

    def test_read_side_property_type_incompatibility_raises(self):
        # A raw descriptor with a stray itemType on a string field now raises
        # on read (Section 8.11 read-side strictness change).
        with pytest.raises(InvalidDescriptorStructure) as exc:
            typespec_from_frictionless(
                {"fields": [{"name": "x", "type": "string", "itemType": "integer"}]}
            )
        assert exc.value.descriptor_path == "$.fields[0]"



# ============================================================================
# TestDirectKeyShapes
# ============================================================================

@pytest.mark.parametrize(
    "factory,label",
    [
        (lambda: TypeSpec(primary_key="id"), "primary_key"),
        (lambda: TypeSpec(unique_keys=[["ok"], "bad"]), "unique_keys[1]"),
        (
            lambda: ForeignKey(
                fields="id",
                reference=ForeignKeyReference(None, ["id"]),
            ),
            "foreign_key.fields",
        ),
        (
            lambda: ForeignKeyReference(None, "id"),
            "foreign_key.reference.fields",
        ),
    ],
)
def test_direct_key_shapes_require_list_str(factory, label) -> None:
    with pytest.raises(InvalidKeyShapeError) as exc_info:
        factory()
    assert exc_info.value.field_name == label


# ============================================================================
# TestTypeSpec
# ============================================================================

class TestTypeSpec:
    def test_from_simple_dict(self):
        spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        assert [(name, field.type) for name, field in spec.fields.items()] == [
            ("id", UniversalType.INTEGER), ("name", UniversalType.STRING),
        ]

    def test_get_field_by_name(self):
        spec = TypeSpec.from_simple_dict({"score": "number"})
        f = spec.get_field("score")
        assert f is not None
        assert f.type == UniversalType.NUMBER

    def test_get_field_missing_returns_none(self):
        spec = TypeSpec.from_simple_dict({"score": "number"})
        assert spec.get_field("nonexistent") is None



# ============================================================================
# TestSpecDiff
# ============================================================================

class TestSpecDiff:
    def _make_spec(self, columns: dict) -> TypeSpec:
        return TypeSpec.from_simple_dict(columns)

    def test_identical_specs_no_diff(self):
        source = self._make_spec({"id": "integer", "name": "string"})
        target = self._make_spec({"id": "integer", "name": "string"})
        diff = compare_specs(source, target)
        assert not diff.has_changes
        assert diff.added_fields == []
        assert diff.removed_fields == []
        assert diff.type_changes == {}

    def test_added_field_detected(self):
        source = self._make_spec({"id": "integer"})
        target = self._make_spec({"id": "integer", "name": "string"})
        diff = compare_specs(source, target)
        assert diff.has_changes
        assert "name" in diff.added_fields

    def test_removed_field_detected(self):
        source = self._make_spec({"id": "integer", "extra": "string"})
        target = self._make_spec({"id": "integer"})
        diff = compare_specs(source, target)
        assert diff.has_changes
        assert "extra" in diff.removed_fields

    def test_type_change_detected(self):
        source = self._make_spec({"id": "integer"})
        target = self._make_spec({"id": "string"})
        diff = compare_specs(source, target)
        assert diff.has_changes
        assert "id" in diff.type_changes
        old_type, new_type = diff.type_changes["id"]
        assert old_type == UniversalType.INTEGER
        assert new_type == UniversalType.STRING


# ============================================================================
# TestForeignKeyReference
# ============================================================================

class TestForeignKeyReference:
    def test_construction(self):
        ref = ForeignKeyReference(resource="customers", fields=["id"])
        assert ref.resource == "customers"
        assert ref.fields == ["id"]

    def test_self_referencing(self):
        ref = ForeignKeyReference(resource=None, fields=["manager_id"])
        assert ref.resource is None

    def test_empty_string_resource_is_rejected_on_direct_construction(self):
        with pytest.raises(ValueError, match="resource"):
            ForeignKeyReference(resource="", fields=["id"])

    def test_composite_key(self):
        ref = ForeignKeyReference(resource="orders", fields=["order_id", "line_id"])
        assert len(ref.fields) == 2


# ============================================================================
# TestForeignKey
# ============================================================================

class TestForeignKey:
    def test_construction(self):
        fk = ForeignKey(
            fields=["customer_id"],
            reference=ForeignKeyReference(resource="customers", fields=["id"]),
        )
        assert fk.fields == ["customer_id"]
        assert fk.reference.resource == "customers"
        assert fk.reference.fields == ["id"]

    def test_composite_foreign_key(self):
        fk = ForeignKey(
            fields=["order_id", "line_id"],
            reference=ForeignKeyReference(resource="order_lines", fields=["order_id", "line_id"]),
        )
        assert len(fk.fields) == 2
        assert len(fk.reference.fields) == 2



class TestTypeSpecToContract:
    def test_to_contract_produces_native_contract(self):
        # E6: TypeSpec.to_contract() lazily builds a native BaseDataContract
        # subclass (same lazy-import pattern as from_frictionless).
        from mountainash.datacontracts.contract import BaseDataContract

        spec = TypeSpec(
            fields={
                "id": FieldSpec(
                    type=UniversalType.INTEGER,
                    constraints=FieldConstraints(required=True, unique=True),
                ),
                "email": FieldSpec(type=UniversalType.STRING),
            },
            title="users",
            primary_key=["id"],
        )
        contract = spec.to_contract()
        assert issubclass(contract, BaseDataContract)
        assert contract.contract_name() == "users"
        ids = [c.id for c in contract.to_checks()]
        assert "id__not_null" in ids
        assert "id_unique" in ids



def test_parameterized_field_derives_semantic_type_without_losing_detail():
    from mountainash.core.dtypes import (
        ArrayDtype, DurationDtype, ListDtype, MountainashDtype,
        SchemaTypeStatus, StructDtype, TimeDtype, TimestampDtype,
    )

    cases = [
        (TimestampDtype(6, True, "UTC"), UniversalType.DATETIME),
        (TimeDtype(9), UniversalType.TIME),
        (DurationDtype("us", "fixed"), UniversalType.ANY),
        (ListDtype(MountainashDtype.I16), UniversalType.ARRAY),
        (ArrayDtype(MountainashDtype.I16, (2, 3)), UniversalType.ARRAY),
        (StructDtype((("at", TimestampDtype(6, True, "UTC")),)), UniversalType.OBJECT),
    ]
    for dtype, broad in cases:
        field = FieldSpec(dtype=dtype)
        assert field.type is broad
        assert field.dtype == dtype
    unknown = FieldSpec(type=UniversalType.INTEGER, dtype=SchemaTypeStatus.UNKNOWN)
    assert unknown.type is UniversalType.INTEGER
    assert unknown.dtype is SchemaTypeStatus.UNKNOWN


def test_archetype_variants_own_requirements_and_share_named_uses():
    from mountainash.core.dtypes import MountainashDtype

    allowed = [0, 2]
    constraints = FieldConstraints(minimum=0, maximum=100, enum=allowed)
    quantity = FieldSpec(dtype=MountainashDtype.I32, constraints=constraints)
    orders = TypeSpec(fields={"quantity": quantity})
    shipments = TypeSpec(fields={"shipped_quantity": quantity})
    bulk = quantity.variant(minimum=10)
    relaxed = quantity.variant(maximum=200)
    allowed.append(99)
    assert orders.get_field("quantity") is shipments.get_field("shipped_quantity")
    assert tuple(quantity.constraints.enum) == (0, 2)
    assert (quantity.constraints.minimum, quantity.constraints.maximum) == (0, 100)
    assert (bulk.constraints.minimum, bulk.constraints.maximum) == (10, 100)
    assert (relaxed.constraints.minimum, relaxed.constraints.maximum) == (0, 200)


def test_constraint_overlays_preserve_false_and_replace_whole_requirements():
    base = FieldConstraints(required=True, minimum=0, maximum=100)
    field = FieldSpec(type=UniversalType.INTEGER, constraints=base, required=False)
    replacement = field.variant(
        constraints=FieldConstraints(minimum=10), maximum=200,
    )
    assert base.required is True
    assert field.constraints.required is False
    assert field.constraints.maximum == 100
    assert (replacement.constraints.minimum, replacement.constraints.maximum) == (10, 200)


def test_composition_derives_dtype_and_variants_retain_children():
    from mountainash.core.dtypes import ArrayDtype, ListDtype, MountainashDtype, StructDtype

    quantity = FieldSpec(dtype=MountainashDtype.I32, minimum=0)
    children = {"quantity": quantity}
    record = FieldSpec(fields=children)
    children["extra"] = FieldSpec(dtype=MountainashDtype.STRING)
    collection = FieldSpec(element=record)
    fixed = FieldSpec(element=quantity, dimensions=(2, 3))
    assert record.dtype == StructDtype((("quantity", MountainashDtype.I32),))
    assert collection.dtype == ListDtype(record.dtype)
    assert fixed.dtype == ArrayDtype(MountainashDtype.I32, (2, 3))
    assert record.variant(description="Order").fields["quantity"] is quantity
    assert fixed.variant(description="Grid").dtype == fixed.dtype
    with pytest.raises(TypeError):
        record.fields["extra"] = quantity


def test_shared_metadata_is_owned_recursively_and_cannot_mutate_archetype():
    example = {"items": [{"quantity": 2}]}
    field = FieldSpec(type=UniversalType.OBJECT, example=example)
    example["items"][0]["quantity"] = 99
    assert field.example["items"][0]["quantity"] == 2
    with pytest.raises(TypeError):
        field.example["items"][0]["quantity"] = 10
    with pytest.raises(AttributeError):
        field.description = "changed"


def test_typespec_owns_named_mapping_without_copying_definitions():
    quantity = FieldSpec(type=UniversalType.INTEGER)
    fields = {"b": quantity, "a": quantity}
    schema = TypeSpec(fields=fields)
    fields.clear()
    assert schema.field_names == ["b", "a"]
    assert schema.get_field("b") is quantity
    schema.fields["c"] = quantity
    assert schema.field_names == ["b", "a", "c"]


@pytest.mark.parametrize("use_dtype", [False, True])
def test_native_override_exposure_cannot_mutate_shared_definition(use_dtype):
    import polars as pl
    from mountainash.core.dtypes import NativeDtype, StructDtype, TypeTarget

    native = pl.Struct([pl.Field("quantity", pl.Int32)])
    if use_dtype:
        definition = FieldSpec(dtype=StructDtype(
            native=NativeDtype(value=native, target=TypeTarget.POLARS),
        ))
        exposed = definition.dtype.native.value
    else:
        definition = FieldSpec(backend_type=native)
        exposed = definition.backend_type.value
    native.fields.append(pl.Field("caller_mutation", pl.String))
    exposed.fields.append(pl.Field("exposed_mutation", pl.String))
    retained = definition.dtype.native.value if use_dtype else definition.backend_type.value
    assert [field.name for field in retained.fields] == ["quantity"]


@pytest.mark.parametrize("element", [
    FieldSpec(type=UniversalType.INTEGER, minimum=0),
    FieldSpec(dtype=MountainashDtype.I32),
    FieldSpec(type=UniversalType.ANY, description="item"),
], ids=["broad", "precise", "any"])
def test_lexical_list_accepts_compatible_element(element):
    field = FieldSpec(type=UniversalType.LIST, item_type="integer", delimiter=";", element=element)
    assert field.element is element


@pytest.mark.parametrize("element_type", [UniversalType.DATE, UniversalType.STRING])
def test_lexical_list_rejects_incompatible_element(element_type):
    with pytest.raises(IncompatibleFieldPropertiesError):
        FieldSpec(type=UniversalType.LIST, item_type="integer", delimiter=";",
                  element=FieldSpec(type=element_type))
