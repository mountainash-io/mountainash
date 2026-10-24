"""
Tests for mountainash.typespec.spec — TableSchema, FieldDefinition, FieldConstraints, SpecDiff.
"""
from __future__ import annotations

import pytest

from mountainash.core.dtypes import MountainashDtype as D, SchemaTypeStatus
from mountainash.typespec.errors import (
    IncompatibleFieldPropertiesError,
    InvalidDtypeDeclaration,
    InvalidKeyShapeError,
)
from mountainash.typespec.frictionless import (
    _field_to_frictionless_dict,
    table_schema_from_frictionless,
    table_schema_to_frictionless,
)
from mountainash.typespec.spec import (
    FieldConstraints,
    FieldDefinition,
    ForeignKey,
    ForeignKeyReference,
    LabeledValue,
    TableSchema,
    compare_specs,
)
from mountainash.typespec.universal_types import UniversalType


class TestSharedDeclarations:
    def test_variant_retains_unspecified_constraints(self):
        from mountainash.typespec.spec import FieldDefinition
        from mountainash.core.dtypes import MountainashDtype as D

        base = FieldDefinition(dtype=D.I64, minimum=0, maximum=100)
        variant = base.variant(minimum=10)
        replaced = base.variant(
            constraints=FieldConstraints(maximum=200), minimum=20,
        )
        assert (base.constraints.minimum, base.constraints.maximum) == (0, 100)
        assert (variant.constraints.minimum, variant.constraints.maximum) == (10, 100)
        assert (replaced.constraints.minimum, replaced.constraints.maximum) == (20, 200)

    def test_recursive_composition_preserves_shape_distinctions(self):
        from mountainash.typespec.spec import FieldDefinition
        from mountainash.core.dtypes import (
            ArrayDtype, ListDtype, MountainashDtype as D,
            SchemaTypeStatus, StructDtype,
        )

        quantity = FieldDefinition(dtype=D.I64, minimum=0)
        assert FieldDefinition(fields={"qty": quantity}).dtype == StructDtype(
            fields=(("qty", D.I64),),
        )
        assert FieldDefinition(fields={}).dtype == StructDtype(fields=())
        assert FieldDefinition(element=quantity).dtype == ListDtype(element=D.I64)
        assert FieldDefinition(
            element=quantity, dimensions=SchemaTypeStatus.UNKNOWN,
        ).dtype == ArrayDtype(element=D.I64, dimensions=SchemaTypeStatus.UNKNOWN)

    def test_declarations_own_nested_metadata_and_schema_mapping(self):
        from mountainash.typespec.spec import FieldDefinition, TableSchema
        from dataclasses import FrozenInstanceError

        enum = ["a", "b"]
        metadata = {"type": "string", "examples": ["a"]}
        definition = FieldDefinition(
            constraints=FieldConstraints(enum=enum, json_schema=metadata),
        )
        named = {"first": definition}
        schema = TableSchema(fields=named)
        enum.append("c")
        metadata["examples"].append("b")
        named["second"] = definition
        assert tuple(definition.constraints.enum) == ("a", "b")
        assert tuple(definition.constraints.json_schema["examples"]) == ("a",)
        assert list(schema.fields) == ["first"]
        with pytest.raises((FrozenInstanceError, AttributeError)):
            definition.title = "changed"

    def test_constraint_keywords_cover_complete_vocabulary_and_severity(self):
        definition = FieldDefinition(
            type=UniversalType.STRING, required=True, unique=True,
            eq="a", ne="b", notin=["c"], str_contains="x",
            str_startswith="y", str_endswith="z", min_length=1, max_length=5,
            pattern="^a", enum=["a", "d"], severity="warning",
        )
        c = definition.constraints
        assert (c.required, c.unique, c.eq, c.ne) == (True, True, "a", "b")
        assert tuple(c.notin) == ("c",)
        assert (c.str_contains, c.str_startswith, c.str_endswith) == ("x", "y", "z")
        assert (definition.min_length, definition.max_length, definition.pattern) == (1, 5, "^a")
        assert definition.severity == "warning"
        assert FieldDefinition().severity is None

    def test_variant_overlay_can_relax_and_unset_booleans_without_touching_original(self):
        base = FieldDefinition(dtype=D.I64, required=True, minimum=0, maximum=100)
        relaxed = base.variant(required=False, maximum=500)
        assert (relaxed.required, relaxed.minimum, relaxed.maximum) == (False, 0, 500)
        assert (base.required, base.maximum) == (True, 100)
        assert base.variant(rename_from="SRC").rename_from == "SRC"
        assert base.rename_from is None

    def test_variant_of_nested_shape_rederives_dtype(self):
        record = FieldDefinition(fields={"a": FieldDefinition(dtype=D.I64)})
        wider = record.variant(
            fields={"a": FieldDefinition(dtype=D.I64), "b": FieldDefinition(dtype=D.STRING)},
        )
        assert [name for name, _ in wider.dtype.fields] == ["a", "b"]
        assert len(record.dtype.fields) == 1

    def test_unknown_and_empty_structure_are_distinct(self):
        from mountainash.core.dtypes import StructDtype

        unknown = FieldDefinition(dtype=StructDtype())
        assert unknown.fields is None and unknown.dtype.fields is SchemaTypeStatus.UNKNOWN
        assert FieldDefinition(fields=SchemaTypeStatus.UNKNOWN).dtype == unknown.dtype
        assert FieldDefinition(fields={}).dtype != unknown.dtype

    def test_nested_declaration_contradicting_dtype_raises(self):
        with pytest.raises(InvalidDtypeDeclaration):
            FieldDefinition(dtype=D.I64, fields={"a": FieldDefinition(dtype=D.I64)})
        with pytest.raises(IncompatibleFieldPropertiesError):
            FieldDefinition(type=UniversalType.STRING, fields={})

    def test_schema_fields_assignment_is_copied_and_ordered(self):
        schema = TableSchema()
        named = {"b": FieldDefinition(), "a": FieldDefinition()}
        schema.fields = named
        named.pop("b")
        assert list(schema.fields) == ["b", "a"]
        with pytest.raises(InvalidDtypeDeclaration):
            TableSchema(fields=[FieldDefinition()])


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
        assert (c.eq, c.ne, c.notin) == (None, None, None)


# ============================================================================
# Model defaults / exports
# ============================================================================

def test_unit_b_model_defaults() -> None:
    assert FieldDefinition(type=UniversalType.ANY).type is UniversalType.ANY
    assert TableSchema().fields_match == "exact"
    assert TableSchema().missing_values == [""]


def test_labeled_values_and_v2_constraints_store_exact_shapes() -> None:
    labeled = LabeledValue(2, "Two")
    constraints = FieldConstraints(
        exclusive_minimum=0,
        exclusive_maximum=10,
        json_schema={"type": "integer"},
    )
    definition = FieldDefinition(
        type=UniversalType.INTEGER,
        categories=[labeled],
        missing_values=[LabeledValue("-", "Dash")],
        constraints=constraints,
    )
    assert definition.categories == (labeled,)
    assert constraints.json_schema == {"type": "integer"}


def test_labeled_value_and_model_classes_exported_from_typespec() -> None:
    # NB: `import mountainash.typespec as ts` is shadowed by the top-level
    # lazy `typespec` factory; the from-import form is the real export contract.
    import sys

    from mountainash.typespec import (  # noqa: F401
        FieldConstraints,
        FieldDefinition,
        ForeignKey,
        ForeignKeyReference,
        LabeledValue,
        MissingValue,
        TableSchema,
    )

    module = sys.modules["mountainash.typespec"]
    for name in (
        "LabeledValue",
        "MissingValue",
        "FieldConstraints",
        "ForeignKeyReference",
        "ForeignKey",
        "FieldDefinition",
        "TableSchema",
    ):
        assert hasattr(module, name), name
        assert name in module.__all__, name
    for retired in ("FieldSpec", "TypeSpec"):
        assert not hasattr(module, retired), retired


# ============================================================================
# TestFieldDefinition
# ============================================================================

class TestFieldDefinition:
    def test_default_type_is_any(self):
        assert FieldDefinition().type is UniversalType.ANY

    # --- serializer coverage ---

    def test_field_dict_minimal(self):
        d = _field_to_frictionless_dict(FieldDefinition(type=UniversalType.INTEGER), "id")
        assert d["name"] == "id"
        assert d["type"] == "integer"
        assert "x-mountainash" not in d
        assert "constraints" not in d

    def test_field_dict_with_constraints(self):
        constraints = FieldConstraints(required=True, min_length=2)
        definition = FieldDefinition(type=UniversalType.STRING, constraints=constraints)
        d = _field_to_frictionless_dict(definition, "username")
        assert d["name"] == "username"
        assert d["constraints"]["required"] is True
        assert d["constraints"]["minLength"] == 2

    def test_nested_fields_round_trip_in_declared_order(self):
        geo = FieldDefinition(fields={"lat": FieldDefinition(type=UniversalType.NUMBER)})
        addr = FieldDefinition(
            fields={
                "street": FieldDefinition(type=UniversalType.STRING),
                "geo": geo,
                "zip": FieldDefinition(type=UniversalType.STRING),
            },
        )
        restored = table_schema_from_frictionless(
            table_schema_to_frictionless(TableSchema(fields={"addr": addr}))
        ).fields["addr"]
        assert list(restored.fields) == ["street", "geo", "zip"]
        assert list(restored.fields["geo"].fields) == ["lat"]
        assert restored.fields["geo"].fields["lat"].type is UniversalType.NUMBER

    def test_element_round_trip(self):
        rows = FieldDefinition(
            element=FieldDefinition(
                fields={
                    "a": FieldDefinition(type=UniversalType.STRING),
                    "b": FieldDefinition(type=UniversalType.INTEGER),
                },
            ),
        )
        restored = table_schema_from_frictionless(
            table_schema_to_frictionless(TableSchema(fields={"rows": rows}))
        ).fields["rows"]
        assert list(restored.element.fields) == ["a", "b"]
        assert restored.element.fields["b"].type is UniversalType.INTEGER

    # --- property/type compatibility (Section 8.7) ---

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"type": UniversalType.STRING, "item_type": "integer"},
            {"type": UniversalType.STRING, "delimiter": ";"},
            {"type": UniversalType.INTEGER, "item_type": "integer"},
            {"type": UniversalType.LIST, "element": FieldDefinition(type=UniversalType.STRING)},
            {"type": UniversalType.STRING, "fields": {"a": FieldDefinition(type=UniversalType.STRING)}},
        ],
    )
    def test_incompatible_property_type_combinations_raise(self, kwargs):
        with pytest.raises(IncompatibleFieldPropertiesError):
            FieldDefinition(**kwargs)

    def test_item_type_and_delimiter_legal_on_list(self):
        f = FieldDefinition(type=UniversalType.LIST, item_type="integer", delimiter=";")
        assert f.item_type == "integer"
        assert f.delimiter == ";"

    @pytest.mark.parametrize(
        "property_name,value",
        [("item_type", UniversalType.INTEGER), ("delimiter", "|")],
    )
    def test_array_rejects_lexical_properties(self, property_name, value):
        with pytest.raises(IncompatibleFieldPropertiesError):
            FieldDefinition(type=UniversalType.ARRAY, **{property_name: value})

    def test_labeled_value_round_trip_on_categories_and_missing_values(self):
        definition = FieldDefinition(
            type=UniversalType.STRING,
            categories=[LabeledValue("a", "Active"), "raw"],
            missing_values=[LabeledValue("-", "Dash"), ""],
        )
        restored = table_schema_from_frictionless(
            table_schema_to_frictionless(TableSchema(fields={"status": definition}))
        ).fields["status"]
        assert restored.categories == (LabeledValue("a", "Active"), "raw")
        assert restored.missing_values == (LabeledValue("-", "Dash"), "")

    def test_read_side_property_type_incompatibility_raises(self):
        # A raw descriptor with a stray itemType on a string field raises on read.
        with pytest.raises(IncompatibleFieldPropertiesError):
            table_schema_from_frictionless(
                {"fields": [{"name": "x", "type": "string", "itemType": "integer"}]}
            )


# ============================================================================
# TestDirectKeyShapes
# ============================================================================

@pytest.mark.parametrize(
    "factory,label",
    [
        (lambda: TableSchema(primary_key="id"), "primary_key"),
        (lambda: TableSchema(unique_keys=[["ok"], "bad"]), "unique_keys[1]"),
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
# TestTableSchema
# ============================================================================

class TestTableSchema:
    def test_from_simple_dict(self):
        schema = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        assert list(schema.fields) == ["id", "name"]
        assert schema.fields["id"].type == UniversalType.INTEGER
        assert schema.fields["name"].type == UniversalType.STRING

    def test_field_names_property(self):
        schema = TableSchema.from_simple_dict({"a": "string", "b": "integer", "c": "number"})
        assert schema.field_names == ["a", "b", "c"]

    def test_get_field_by_name(self):
        schema = TableSchema.from_simple_dict({"score": "number"})
        f = schema.get_field("score")
        assert f is not None
        assert f.type == UniversalType.NUMBER

    def test_get_field_missing_returns_none(self):
        schema = TableSchema.from_simple_dict({"score": "number"})
        assert schema.get_field("nonexistent") is None

    def test_table_schema_to_frictionless_dict(self):
        schema = TableSchema.from_simple_dict({"id": "integer"}, title="My Spec")
        d = table_schema_to_frictionless(schema)
        assert len(d["fields"]) == 1
        assert d["fields"][0]["name"] == "id"
        assert d["title"] == "My Spec"

    def test_source_name_is_rename_from_or_local_mapping_name(self):
        schema = TableSchema(fields={
            "age": FieldDefinition(rename_from="AGE"),
            "name": FieldDefinition(),
        })
        sources = {
            name: d.rename_from if d.rename_from is not None else name
            for name, d in schema.fields.items()
        }
        assert sources == {"age": "AGE", "name": "name"}


# ============================================================================
# TestSpecDiff
# ============================================================================

class TestSpecDiff:
    def _make_spec(self, columns: dict) -> TableSchema:
        return TableSchema.from_simple_dict(columns)

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
# TestTableSchema ForeignKeys
# ============================================================================

class TestTableSchemaForeignKeys:
    def test_foreign_keys_default_is_none(self):
        spec = TableSchema()
        assert spec.foreign_keys is None

    def test_foreign_keys_with_value(self):
        fk = ForeignKey(
            fields=["customer_id"],
            reference=ForeignKeyReference(resource="customers", fields=["id"]),
        )
        spec = TableSchema(
            fields={"customer_id": FieldDefinition(type=UniversalType.INTEGER)},
            foreign_keys=[fk],
        )
        assert len(spec.foreign_keys) == 1
        assert spec.foreign_keys[0].fields == ["customer_id"]
        assert spec.foreign_keys[0].reference.resource == "customers"


class TestTableSchemaToContract:
    def test_to_contract_produces_native_contract(self):
        # E6: TableSchema.to_contract() lazily builds a native BaseDataContract
        # subclass (same lazy-import pattern as from_frictionless).
        from mountainash.datacontracts.contract import BaseDataContract

        spec = TableSchema(
            fields={
                "id": FieldDefinition(
                    type=UniversalType.INTEGER,
                    constraints=FieldConstraints(required=True, unique=True),
                ),
                "email": FieldDefinition(type=UniversalType.STRING),
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

    def test_to_contract_name_override(self):
        spec = TableSchema(fields={"a": FieldDefinition(type=UniversalType.INTEGER)})
        contract = spec.to_contract(name="Custom")
        assert contract.contract_name() == "Custom"


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
        field = FieldDefinition(dtype=dtype)
        assert field.type is broad
        assert field.dtype == dtype
    unknown = FieldDefinition(type=UniversalType.INTEGER, dtype=SchemaTypeStatus.UNKNOWN)
    assert unknown.type is UniversalType.INTEGER
    assert unknown.dtype is SchemaTypeStatus.UNKNOWN
