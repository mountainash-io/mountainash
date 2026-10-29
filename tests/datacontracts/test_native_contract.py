"""Native BaseDataContract: declaration collection, TableSchema round trip, validate."""
import polars as pl
import pytest

from typing import ClassVar

from mountainash.datacontracts.compiler import contract_from_table_schema
from mountainash.datacontracts.contract import BaseDataContract
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.errors import IdentityInvalidError


class UserContract(BaseDataContract):
    id: int = FieldDefinition(type=UniversalType.INTEGER, required=True, unique=True)
    email: str = FieldDefinition(type=UniversalType.STRING, required=True, pattern=r".+@.+")
    age: int = FieldDefinition(type=UniversalType.INTEGER, minimum=0)
    note: str = FieldDefinition(type=UniversalType.STRING)

    class Config:
        name = "users"
        natural_key = ["id"]


class TestDeclarationCollection:
    def test_every_member_collected_in_declaration_order(self):
        assert list(UserContract._contract_fields) == ["id", "email", "age", "note"]

    def test_declaration_syntax_preserved(self):
        assert isinstance(UserContract._contract_fields["age"], FieldDefinition)
        assert UserContract._contract_fields["age"].minimum == 0

    def test_annotation_without_a_definition_is_not_a_contract_member(self):
        # Members are explicit shared definitions; an annotation never declares one.
        with pytest.raises(TypeError, match="FieldDefinition"):

            class AnnotationOnly(BaseDataContract):
                note: str

    def test_class_variable_annotation_is_not_a_member(self):
        class WithClassVar(BaseDataContract):
            kind: ClassVar[str] = "demo"
            qty: int = FieldDefinition(type=UniversalType.INTEGER)

        assert list(WithClassVar.to_table_schema().fields) == ["qty"]

    def test_attached_definition_owns_type_even_with_annotation(self):
        class Mismatched(BaseDataContract):
            value: int = FieldDefinition(type=UniversalType.STRING)

        assert Mismatched.to_table_schema().fields["value"].type == UniversalType.STRING

    def test_one_definition_attached_under_different_names(self):
        quantity = FieldDefinition(type=UniversalType.INTEGER, required=True, minimum=0)

        class Lines(BaseDataContract):
            ordered: int = quantity
            shipped: int = quantity

        fields = Lines.to_table_schema().fields
        assert fields["ordered"] is fields["shipped"] or fields["ordered"] == fields["shipped"]
        ids = [c.id for c in Lines.to_checks()]
        assert {"ordered_range", "shipped_range", "ordered__not_null", "shipped__not_null"} <= set(ids)

    def test_inheritance_keeps_base_order_and_subclass_replaces_in_place(self):
        class Base(BaseDataContract):
            a: int = FieldDefinition(type=UniversalType.INTEGER)
            b: int = FieldDefinition(type=UniversalType.INTEGER)

        class Child(Base):
            c: int = FieldDefinition(type=UniversalType.INTEGER)
            a: int = FieldDefinition(type=UniversalType.INTEGER, minimum=5)

        assert list(Child.to_table_schema().fields) == ["a", "b", "c"]
        assert Child.to_table_schema().fields["a"].minimum == 5
        assert Base.to_table_schema().fields["a"].minimum is None

    def test_unannotated_definition_member_is_collected(self):
        class Bare(BaseDataContract):
            qty = FieldDefinition(type=UniversalType.INTEGER, minimum=1)

        assert list(Bare.to_table_schema().fields) == ["qty"]

    def test_subclass_of_schema_generated_contract_replaces_definition_in_place(self):
        schema = TableSchema(
            fields={
                "a": FieldDefinition(type=UniversalType.INTEGER),
                "b": FieldDefinition(type=UniversalType.INTEGER),
            },
            fields_match="open",
        )
        Generated = contract_from_table_schema(schema)

        class Stricter(Generated):
            a: int = FieldDefinition(type=UniversalType.INTEGER, minimum=5)
            c: int = FieldDefinition(type=UniversalType.INTEGER)

        derived = Stricter.to_table_schema()
        assert list(derived.fields) == ["a", "b", "c"]
        assert derived.fields["a"].minimum == 5
        assert derived.fields_match == "open"
        assert "a_range" in {check.id for check in Stricter.to_checks()}
        assert Generated.to_table_schema().fields["a"].minimum is None


class TestToTableSchema:
    def test_types_and_constraints(self):
        schema = UserContract.to_table_schema()
        assert schema.fields["id"].type == UniversalType.INTEGER
        assert schema.fields["email"].constraints.pattern == r".+@.+"
        assert schema.fields["note"].constraints.required is False

    def test_returns_an_independent_schema(self):
        schema = UserContract.to_table_schema()
        schema.fields.pop("note")
        assert "note" in UserContract.to_table_schema().fields

    def test_natural_key_survives_as_primary_key(self):
        # Config.natural_key must survive the TableSchema round-trip as
        # primary_key so DAG validation resolves keyed identity for
        # natural_key-only contracts.
        assert UserContract.to_table_schema().primary_key == ["id"]

    def test_schema_to_contract_preserves_full_definitions(self):
        schema = TableSchema(
            fields={
                "qty": FieldDefinition(
                    type=UniversalType.INTEGER, required=True, minimum=0,
                    exclusive_maximum=100, severity="warning", rename_from="quantity",
                ),
                "tag": FieldDefinition(
                    type=UniversalType.STRING, str_startswith="t", notin=["tx"],
                ),
            },
            fields_match="open",
        )
        round_tripped = contract_from_table_schema(schema).to_table_schema()
        assert list(round_tripped.fields) == ["qty", "tag"]
        assert round_tripped.fields == schema.fields
        assert round_tripped.fields_match == "open"

    def test_to_checks_ids(self):
        ids = [c.id for c in UserContract.to_checks()]
        assert "id__not_null" in ids
        assert "email__not_null" in ids
        assert "email_pattern" in ids
        assert "age_range" in ids

    def test_to_checks_includes_primary_key_unique(self):
        ids = [c.id for c in UserContract.to_checks()]
        assert "primary_key_unique" in ids  # UserContract: Config.natural_key = ["id"]

    def test_to_checks_includes_primary_key_unique_for_primary_key_config(self):
        class OrderContract(BaseDataContract):
            order_id: int = FieldDefinition(type=UniversalType.INTEGER, required=True)

            class Config:
                name = "orders"
                primary_key = ["order_id"]

        ids = [c.id for c in OrderContract.to_checks()]
        assert "primary_key_unique" in ids


def test_to_checks_matches_compile_datacontract_check_ids():
    from mountainash.datacontracts.compiler import compile_datacontract

    schema = UserContract.to_table_schema()
    compiled_ids = {c.id for c in compile_datacontract(schema).checks}
    contract_ids = {c.id for c in contract_from_table_schema(schema).to_checks()}
    assert compiled_ids == contract_ids


def _check_signature(checks):
    return [
        (
            type(check).__name__, check.id, check.severity, tuple(check.fields or ()),
            getattr(check, "validator", None), getattr(check, "options", None),
        )
        for check in checks
    ]


def test_every_route_compiles_the_same_requirements_and_severity():
    """Direct definitions, compiled schemas, schema-generated contracts and
    class-authored contracts keep one meaning for the full constraint vocabulary."""
    from mountainash.datacontracts.compiler import compile_datacontract

    definitions = {
        "amount": FieldDefinition(
            type=UniversalType.NUMBER, required=True, unique=True, minimum=1, maximum=10,
            exclusive_minimum=0, exclusive_maximum=11, enum=[1, 2], enum_weights={"1": 1.0},
            severity="warning",
        ),
        "value": FieldDefinition(
            type=UniversalType.INTEGER, eq=1, ne=2, notin=[-1], severity="warning"
        ),
        "text": FieldDefinition(
            type=UniversalType.STRING, str_contains="1", str_startswith="1", str_endswith="1",
        ),
        "label": FieldDefinition(
            type=UniversalType.STRING, min_length=1, max_length=8, pattern=r"[a-z]+",
            enum=["draft"], categories=["draft"],
        ),
        "payload": FieldDefinition(
            type=UniversalType.OBJECT,
            fields={"child": FieldDefinition(type=UniversalType.STRING, required=True)},
            json_schema={"type": "object"},
        ),
        "items": FieldDefinition(
            type=UniversalType.ARRAY,
            element=FieldDefinition(type=UniversalType.INTEGER, minimum=0),
        ),
        "shape": FieldDefinition(type=UniversalType.GEOJSON),
    }
    schema = TableSchema(fields=definitions)
    authored = type(
        "Authored",
        (BaseDataContract,),
        {"__annotations__": {name: object for name in definitions}, **definitions},
    )

    direct = [c for name, d in schema.fields.items() for c in d.to_checks(name)]
    compiled = list(compile_datacontract(schema).checks)
    routes = {
        "direct": _check_signature(direct),
        "compiled": _check_signature(compiled),
        "generated": _check_signature(schema.to_contract().to_checks()),
        "authored": _check_signature(authored.to_checks()),
        "authored_schema": _check_signature(authored.to_table_schema().to_contract().to_checks()),
    }

    reference = routes["direct"]
    assert {check_id for _, check_id, *_ in reference} >= {
        "amount__not_null", "amount_range", "amount_enum_membership", "amount_unique",
        "value__eq", "value__ne", "value__notin",
        "text__str_contains", "text__str_startswith", "text__str_endswith",
        "label_length", "label_pattern", "label_category_membership",
        "payload_json_schema", "payload_nested", "items_nested", "shape_geojson",
    }
    for name, signature in routes.items():
        assert signature == reference, name
    severities = {check_id: severity for _, check_id, severity, *_ in reference}
    assert {severities[i] for i in ("amount_range", "amount_unique", "value__eq")} == {"warning"}
    assert severities["label_pattern"] == "blocking"


class TestValidate:
    def test_valid_data_passes(self):
        df = pl.DataFrame(
            {"id": [1, 2], "email": ["a@b.c", "d@e.f"], "age": [30, 40], "note": ["x", "y"]}
        )
        result = UserContract.validate_datacontract(df)
        assert result.passes
        assert result.datacontract_name == "users"

    def test_invalid_data_returns_not_raises(self):
        # ids stay unique here: UserContract's natural_key=["id"] means duplicate
        # ids raise IdentityInvalidError before checks run (that path is tested
        # in test_runner_mechanics); this test exercises failing CHECKS.
        df = pl.DataFrame(
            {"id": [1, 2], "email": ["nope", "d@e.f"], "age": [-1, 40], "note": ["x", "y"]}
        )
        result = UserContract.validate_datacontract(df)
        assert result.passes is False
        failing = set(
            result.check_summaries.filter(
                result.check_summaries["status"] != "passed"
            )["check_id"].to_list()
        )
        assert {"email_pattern", "age_range"} <= failing
    def test_missing_coerce_config_preserves_default_coercion(self):
        class DefaultCoercionContract(BaseDataContract):
            value: int = FieldDefinition(type=UniversalType.INTEGER)

            class Config:
                name = "default-coercion"

        result = DefaultCoercionContract.validate_datacontract(
            pl.DataFrame({"value": ["7"]})
        )
        assert result.passes


    def test_keyed_identity_from_natural_key(self):
        df = pl.DataFrame(
            {"id": [1, 2], "email": ["nope", "d@e.f"], "age": [30, 40], "note": ["x", "y"]}
        )
        result = UserContract.validate_datacontract(df)
        assert result.identity.kind == "keyed"
        assert "id" in result.failure_cases.columns

    def test_quick_is_fail_fast_same_shapes(self):
        df = pl.DataFrame(
            {"id": [1, 2], "email": ["nope", "d@e.f"], "age": [-1, 40], "note": ["x", "y"]}
        )
        full = UserContract.validate_datacontract(df)
        quick = UserContract.validate_datacontract_quick(df)
        assert list(full.check_summaries.columns) == list(quick.check_summaries.columns)
        assert list(full.failure_cases.columns) == list(quick.failure_cases.columns)
        assert quick.check_summaries.height <= full.check_summaries.height

    def test_validate_datacontract_raises_by_default_on_duplicate_key(self):
        df = pl.DataFrame(
            {"id": [1, 1], "email": ["a@b.c", "d@e.f"], "age": [30, 40], "note": ["x", "y"]}
        )
        with pytest.raises(IdentityInvalidError):
            UserContract.validate_datacontract(df)

    def test_validate_datacontract_allow_imperfect_key_reports_primary_key_unique(self):
        df = pl.DataFrame(
            {"id": [1, 1], "email": ["a@b.c", "d@e.f"], "age": [30, 40], "note": ["x", "y"]}
        )
        result = UserContract.validate_datacontract(df, allow_imperfect_key=True)
        assert result.passes is False
        failing = set(
            result.check_summaries.filter(
                result.check_summaries["status"] != "passed"
            )["check_id"].to_list()
        )
        assert "primary_key_unique" in failing
        assert result.identity_diagnostics["duplicate_key_tuples"] == 1

    def test_validate_datacontract_quick_allow_imperfect_key_same_shape(self):
        df = pl.DataFrame(
            {"id": [1, 1], "email": ["a@b.c", "d@e.f"], "age": [30, 40], "note": ["x", "y"]}
        )
        result = UserContract.validate_datacontract_quick(df, allow_imperfect_key=True)
        assert result.passes is False
        assert result.identity_diagnostics["duplicate_key_tuples"] == 1


class NoKeyContract(BaseDataContract):
    id: int = FieldDefinition(type=UniversalType.INTEGER, unique=True)

    class Config:
        coerce = False


# ============================================================================
# TestSemanticStringNativeContract (item 113 Unit B, Task 2)
#
# DURATION/YEAR/YEARMONTH now compile to `str` Python annotations — their
# canonical mapping changed to the semantic-string XSD_* types (spec §8.2),
# so a native contract's Python type must be truthful about that, not still
# claim datetime.timedelta / int.
# ============================================================================

class TestSemanticStringNativeContract:
    @pytest.mark.parametrize(
        "universal",
        [UniversalType.DURATION, UniversalType.YEAR, UniversalType.YEARMONTH],
    )
    def test_semantic_string_fields_compile_to_str(self, universal) -> None:
        contract = contract_from_table_schema(
            TableSchema(fields={"value": FieldDefinition(type=universal)})
        )
        assert contract.__annotations__["value"] is str


def test_unique_failure_without_key_identity():
    """unique needs no key identity — duplicate ids fail the CHECK when no
    natural_key/primary_key declares them as identity."""
    df = pl.DataFrame({"id": [1, 1, 2]})
    result = NoKeyContract.validate_datacontract(df)
    assert result.passes is False
    assert result.identity.kind == "none"
    summary = result.check_summaries.filter(
        result.check_summaries["check_id"] == "id_unique"
    ).row(0, named=True)
    assert summary["check_id"] == "id_unique"
    assert summary["fail_count"] == 2  # both duplicated rows flagged
