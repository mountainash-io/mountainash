"""
Tests for mountainash.typespec.spec — TypeSpec, FieldSpec, FieldConstraints, SpecDiff.
"""
from __future__ import annotations

import pytest

from mountainash.typespec.errors import (
    IncompatibleFieldPropertiesError,
    InvalidKeyShapeError,
)
from mountainash.typespec.frictionless import (
    _field_to_frictionless_dict,
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


# ============================================================================
# TestFieldConstraints
# ============================================================================

class TestFieldConstraints:
    def test_enum_weights_default_is_none(self):
        c = FieldConstraints()
        assert c.enum_weights is None

    def test_enum_weights_with_values(self):
        c = FieldConstraints(
            enum=["A", "B", "C"],
            enum_weights={"A": 0.5, "B": 0.3, "C": 0.2},
        )
        assert c.enum_weights == {"A": 0.5, "B": 0.3, "C": 0.2}

    def test_v2_constraint_fields_default_none(self):
        c = FieldConstraints()
        assert c.exclusive_minimum is None
        assert c.exclusive_maximum is None
        assert c.json_schema is None


# ============================================================================
# TestUnitBModelDefaults / exports
# ============================================================================

def test_unit_b_model_defaults() -> None:
    assert FieldSpec("value", type=UniversalType.ANY).type is UniversalType.ANY
    assert TypeSpec().fields_match == "exact"
    assert TypeSpec().missing_values == [""]


def test_labeled_values_and_v2_constraints_store_exact_shapes() -> None:
    labeled = LabeledValue(2, "Two")
    constraints = FieldConstraints(
        exclusive_minimum=0,
        exclusive_maximum=10,
        json_schema={"type": "integer"},
    )
    field = FieldSpec(
        "value",
        UniversalType.INTEGER,
        categories=[labeled],
        missing_values=[LabeledValue("-", "Dash")],
        constraints=constraints,
    )
    assert field.categories == [labeled]
    assert constraints.json_schema == {"type": "integer"}


def test_labeled_value_and_model_classes_exported_from_typespec() -> None:
    # NB: `import mountainash.typespec as ts` is shadowed by the top-level
    # lazy `typespec` factory; the from-import form is the real export contract.
    import sys

    from mountainash.typespec import (  # noqa: F401
        FieldConstraints,
        FieldSpec,
        ForeignKey,
        ForeignKeyReference,
        LabeledValue,
        MissingValue,
        TypeSpec,
    )

    module = sys.modules["mountainash.typespec"]
    for name in (
        "LabeledValue",
        "MissingValue",
        "FieldConstraints",
        "ForeignKeyReference",
        "ForeignKey",
        "FieldSpec",
        "TypeSpec",
    ):
        assert hasattr(module, name), name
        assert name in module.__all__, name


# ============================================================================
# TestFieldSpec
# ============================================================================

class TestFieldSpec:
    def test_source_name_defaults_to_name(self):
        f = FieldSpec(name="age", type=UniversalType.ANY)
        assert f.source_name == "age"

    def test_source_name_uses_rename_from(self):
        f = FieldSpec(name="age", type=UniversalType.ANY, rename_from="AGE")
        assert f.source_name == "AGE"

    def test_default_type_is_any(self):
        f = FieldSpec(name="col")
        assert f.type is UniversalType.ANY

    def test_null_fill_default_is_none(self):
        f = FieldSpec(name="col", type=UniversalType.ANY)
        assert f.null_fill is None

    # --- serializer coverage (rewritten from the deleted to_dict methods) ---

    def test_field_dict_minimal(self):
        f = FieldSpec(name="id", type=UniversalType.INTEGER)
        d = _field_to_frictionless_dict(f)
        assert d["name"] == "id"
        assert d["type"] == "integer"
        assert "x-mountainash" not in d
        assert "constraints" not in d

    def test_field_dict_with_constraints(self):
        constraints = FieldConstraints(required=True, min_length=2)
        f = FieldSpec(name="username", type=UniversalType.STRING, constraints=constraints)
        d = _field_to_frictionless_dict(f)
        assert d["name"] == "username"
        assert "constraints" in d
        assert d["constraints"]["required"] is True
        assert d["constraints"]["minLength"] == 2

    def test_field_spec_has_object_fields_default_none(self):
        f = FieldSpec(name="addr", type=UniversalType.OBJECT)
        assert f.object_fields is None

    def test_object_fields_omitted_from_dict_when_unset(self):
        f = FieldSpec(name="addr", type=UniversalType.OBJECT)
        d = _field_to_frictionless_dict(f)
        assert "x-mountainash" not in d

    def test_object_fields_exported_recursively_in_dict(self):
        inner = [
            FieldSpec(name="street", type=UniversalType.STRING),
            FieldSpec(name="zip", type=UniversalType.STRING),
        ]
        f = FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=inner)
        d = _field_to_frictionless_dict(f)
        assert d["x-mountainash"]["object_fields"] == [
            {"name": "street", "type": "string"},
            {"name": "zip", "type": "string"},
        ]

    def test_object_fields_two_levels_deep_in_dict(self):
        geo = [FieldSpec(name="lat", type=UniversalType.NUMBER)]
        inner = [
            FieldSpec(name="street", type=UniversalType.STRING),
            FieldSpec(name="geo", type=UniversalType.OBJECT, object_fields=geo),
        ]
        f = FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=inner)
        d = _field_to_frictionless_dict(f)
        nested = d["x-mountainash"]["object_fields"][1]
        assert nested["name"] == "geo"
        assert nested["x-mountainash"]["object_fields"] == [{"name": "lat", "type": "number"}]

    # --- property/type compatibility (Section 8.7) ---

    @pytest.mark.parametrize(
        "kwargs,prop",
        [
            ({"type": UniversalType.STRING, "item_type": "integer"}, "item_type"),
            ({"type": UniversalType.STRING, "delimiter": ";"}, "delimiter"),
            ({"type": UniversalType.INTEGER, "item_type": "integer"}, "item_type"),
            (
                {"type": UniversalType.LIST,
                 "item_object_fields": [FieldSpec(name="a", type=UniversalType.STRING)]},
                "item_object_fields",
            ),
            (
                {"type": UniversalType.STRING,
                 "object_fields": [FieldSpec(name="a", type=UniversalType.STRING)]},
                "object_fields",
            ),
        ],
    )
    def test_incompatible_property_type_combinations_raise(self, kwargs, prop):
        with pytest.raises(IncompatibleFieldPropertiesError) as exc_info:
            FieldSpec(
                name="f",
                type=kwargs["type"],
                **{key: value for key, value in kwargs.items() if key != "type"},
            )
        assert exc_info.value.property_name == prop

    def test_item_type_and_delimiter_legal_on_list(self):
        f = FieldSpec(name="tags", type=UniversalType.LIST, item_type="integer", delimiter=";")
        assert f.item_type == "integer"
        assert f.delimiter == ";"

    @pytest.mark.parametrize(
        "property_name,value",
        [("item_type", UniversalType.INTEGER), ("delimiter", "|")],
    )
    def test_array_rejects_lexical_properties(self, property_name, value):
        with pytest.raises(IncompatibleFieldPropertiesError):
            FieldSpec(name="values", type=UniversalType.ARRAY, **{property_name: value})

    def test_item_object_fields_legal_on_array(self):
        f = FieldSpec(
            name="rows",
            type=UniversalType.ARRAY,
            item_object_fields=[FieldSpec(name="a", type=UniversalType.STRING)],
        )
        assert f.item_object_fields[0].name == "a"

    def test_item_object_fields_round_trip(self):
        f = FieldSpec(
            name="rows",
            type=UniversalType.ARRAY,
            item_object_fields=[
                FieldSpec(name="a", type=UniversalType.STRING),
                FieldSpec(name="b", type=UniversalType.INTEGER),
            ],
        )
        d = _field_to_frictionless_dict(f)
        assert d["x-mountainash"]["item_object_fields"] == [
            {"name": "a", "type": "string"},
            {"name": "b", "type": "integer"},
        ]
        restored = typespec_from_frictionless(typespec_to_frictionless(TypeSpec(fields=[f])))
        assert restored.fields[0].item_object_fields[0].name == "a"
        assert restored.fields[0].item_object_fields[1].type is UniversalType.INTEGER

    def test_labeled_value_round_trip_on_categories_and_missing_values(self):
        f = FieldSpec(
            name="status",
            type=UniversalType.STRING,
            categories=[LabeledValue("a", "Active"), "raw"],
            missing_values=[LabeledValue("-", "Dash"), ""],
        )
        restored = typespec_from_frictionless(typespec_to_frictionless(TypeSpec(fields=[f])))
        rf = restored.fields[0]
        assert rf.categories == [LabeledValue("a", "Active"), "raw"]
        assert rf.missing_values == [LabeledValue("-", "Dash"), ""]

    def test_read_side_property_type_incompatibility_raises(self):
        # A raw descriptor with a stray itemType on a string field now raises
        # on read (Section 8.11 read-side strictness change).
        with pytest.raises(IncompatibleFieldPropertiesError):
            typespec_from_frictionless(
                {"fields": [{"name": "x", "type": "string", "itemType": "integer"}]}
            )



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
        assert len(spec.fields) == 2
        assert spec.fields[0].name == "id"
        assert spec.fields[0].type == UniversalType.INTEGER
        assert spec.fields[1].name == "name"
        assert spec.fields[1].type == UniversalType.STRING

    def test_field_names_property(self):
        spec = TypeSpec.from_simple_dict({"a": "string", "b": "integer", "c": "number"})
        assert spec.field_names == ["a", "b", "c"]

    def test_get_field_by_name(self):
        spec = TypeSpec.from_simple_dict({"score": "number"})
        f = spec.get_field("score")
        assert f is not None
        assert f.name == "score"
        assert f.type == UniversalType.NUMBER

    def test_get_field_missing_returns_none(self):
        spec = TypeSpec.from_simple_dict({"score": "number"})
        assert spec.get_field("nonexistent") is None

    def test_typespec_to_frictionless_dict(self):
        spec = TypeSpec.from_simple_dict({"id": "integer"}, title="My Spec")
        d = typespec_to_frictionless(spec)
        assert "fields" in d
        assert len(d["fields"]) == 1
        assert d["fields"][0]["name"] == "id"
        assert d["title"] == "My Spec"


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


# ============================================================================
# TestTypeSpec ForeignKeys
# ============================================================================

class TestTypeSpecForeignKeys:
    def test_foreign_keys_default_is_none(self):
        spec = TypeSpec()
        assert spec.foreign_keys is None

    def test_foreign_keys_with_value(self):
        fk = ForeignKey(
            fields=["customer_id"],
            reference=ForeignKeyReference(resource="customers", fields=["id"]),
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="customer_id", type=UniversalType.INTEGER)],
            foreign_keys=[fk],
        )
        assert len(spec.foreign_keys) == 1
        assert spec.foreign_keys[0].fields == ["customer_id"]
        assert spec.foreign_keys[0].reference.resource == "customers"


class TestTypeSpecToContract:
    def test_to_contract_produces_native_contract(self):
        # E6: TypeSpec.to_contract() lazily builds a native BaseDataContract
        # subclass (same lazy-import pattern as from_frictionless).
        from mountainash.datacontracts.contract import BaseDataContract

        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="id",
                    type=UniversalType.INTEGER,
                    constraints=FieldConstraints(required=True, unique=True),
                ),
                FieldSpec(name="email", type=UniversalType.STRING),
            ],
            title="users",
            primary_key=["id"],
        )
        contract = spec.to_contract()
        assert issubclass(contract, BaseDataContract)
        assert contract.contract_name() == "users"
        ids = [c.id for c in contract.to_checks()]
        assert "id__not_null" in ids
        assert "id__unique" in ids

    def test_to_contract_name_override(self):
        spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.INTEGER)])
        contract = spec.to_contract(name="Custom")
        assert contract.contract_name() == "Custom"
