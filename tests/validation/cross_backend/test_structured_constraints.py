"""Structured Frictionless constraints execute against logical containers cross-backend."""

import pytest

import mountainash as ma
from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.typespec import FieldConstraints, FieldSpec, TypeSpec, UniversalType
from mountainash.validation import ValidationRunner

from fixtures.backend_registry import ALL_BACKENDS

from fixtures.capability_gating import xfail_divergence

_STRUCTURED_BACKENDS = [
    pytest.param(
        backend,
        marks=xfail_divergence("MA-CONF-04", backend=backend),
    )
    for backend in ALL_BACKENDS
]


@pytest.mark.parametrize("backend_name", _STRUCTURED_BACKENDS)
def test_compiled_json_schema_reports_logical_object_failure(backend_name, backend_factory):
    """JSON Schema receives a logical object rather than backend-native state."""
    plan = compile_datacontract(
        TypeSpec(
            fields=[
                FieldSpec(
                    name="payload",
                    type=UniversalType.OBJECT,
                    constraints=FieldConstraints(
                        json_schema={
                            "type": "object",
                            "required": ["id"],
                            "properties": {"id": {"type": "integer", "minimum": 1}},
                        }
                    ),
                )
            ]
        )
    )

    result = ValidationRunner().validate_relation(
        ma.relation(backend_factory.create({"payload": [{"id": 0}]}, backend_name)),
        plan=plan,
    )

    summary = result.check_summaries.filter(
        result.check_summaries["check_id"] == "payload_json_schema"
    ).row(0, named=True)
    assert summary["status"] == "failed", backend_name
    failure = result.failure_cases.row(0, named=True)
    assert failure["instance_path"] == "/id", backend_name
    assert failure["validator"] == "minimum", backend_name


# ---------------------------------------------------------------------------
# Task 10 step 1: complete structured (ARRAY/OBJECT) validation matrix.
#
# Every test below ingresses through portable JSON text (spec's primary
# ARRAY/OBJECT vehicle) rather than a native Python container cell value --
# MA-CONF-04 covers native STRUCT *source construction* on ibis-sqlite,
# which a string-typed JSON-text column never triggers, so this whole
# matrix runs unconditionally across the complete `ALL_BACKENDS` set.
# ---------------------------------------------------------------------------


def _object_relation(
    backend_name, backend_factory, values, *, action="coerce", apply_value_transforms=True
):
    df = backend_factory.create({"payload": values}, backend_name)
    spec = TypeSpec(
        fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.OBJECT)]
    )
    return ma.relation(df).conform(
        spec, contract={"data_type": action}, apply_value_transforms=apply_value_transforms
    )


def _array_relation(
    backend_name, backend_factory, values, *, action="coerce", apply_value_transforms=True
):
    df = backend_factory.create({"payload": values}, backend_name)
    spec = TypeSpec(
        fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)]
    )
    return ma.relation(df).conform(
        spec, contract={"data_type": action}, apply_value_transforms=apply_value_transforms
    )


def _value_check(rel, validator, *, options, mostly=None):
    from mountainash.validation import ValueRule, ValueValidatorKey

    return ValidationRunner().validate_relation(
        rel,
        [
            ValueRule(
                id="payload_check",
                fields=["payload"],
                validator=getattr(ValueValidatorKey, validator),
                options=options,
                mostly=mostly,
            )
        ],
    )


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestObjectAndArrayJSONSchema:
    def test_object_json_schema_passes_for_valid_values(self, backend_name, backend_factory):
        plan = compile_datacontract(
            TypeSpec(fields=[FieldSpec(
                name="payload", type=UniversalType.OBJECT,
                constraints=FieldConstraints(json_schema={
                    "type": "object", "required": ["id"],
                    "properties": {"id": {"type": "integer", "minimum": 1}},
                }),
            )])
        )
        result = ValidationRunner().validate_relation(
            _object_relation(backend_name, backend_factory, ['{"id": 5}']), plan=plan,
        )
        summary = result.check_summaries.filter(
            result.check_summaries["check_id"] == "payload_json_schema"
        ).row(0, named=True)
        assert summary["status"] == "passed", backend_name
        assert result.failure_cases.height == 0, backend_name

    def test_array_json_schema_reports_logical_failure(self, backend_name, backend_factory):
        plan = compile_datacontract(
            TypeSpec(fields=[FieldSpec(
                name="payload", type=UniversalType.ARRAY,
                constraints=FieldConstraints(json_schema={
                    "type": "array", "minItems": 2, "items": {"type": "integer"},
                }),
            )])
        )
        result = ValidationRunner().validate_relation(
            _array_relation(backend_name, backend_factory, ["[1]"]), plan=plan,
        )
        summary = result.check_summaries.filter(
            result.check_summaries["check_id"] == "payload_json_schema"
        ).row(0, named=True)
        assert summary["status"] == "failed", backend_name
        failure = result.failure_cases.row(0, named=True)
        assert failure["instance_path"] == "", backend_name
        assert failure["validator"] == "minItems", backend_name

    def test_array_json_schema_passes_for_valid_values(self, backend_name, backend_factory):
        plan = compile_datacontract(
            TypeSpec(fields=[FieldSpec(
                name="payload", type=UniversalType.ARRAY,
                constraints=FieldConstraints(json_schema={
                    "type": "array", "minItems": 2, "items": {"type": "integer"},
                }),
            )])
        )
        result = ValidationRunner().validate_relation(
            _array_relation(backend_name, backend_factory, ["[1, 2, 3]"]), plan=plan,
        )
        summary = result.check_summaries.filter(
            result.check_summaries["check_id"] == "payload_json_schema"
        ).row(0, named=True)
        assert summary["status"] == "passed", backend_name
        assert result.failure_cases.height == 0, backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRecursiveStructuredFields:
    def test_recursive_object_field_reports_the_nested_instance_path(
        self, backend_name, backend_factory
    ):
        """A JSON Schema violation two levels deep reports its full path
        against the fully-decoded native Python structure -- recursive
        validation is inherent to JSON Schema itself, not special-cased."""
        plan = compile_datacontract(
            TypeSpec(fields=[FieldSpec(
                name="payload", type=UniversalType.OBJECT,
                constraints=FieldConstraints(json_schema={
                    "type": "object",
                    "properties": {
                        "child": {
                            "type": "object",
                            "properties": {"id": {"type": "integer", "minimum": 1}},
                        }
                    },
                }),
            )])
        )
        result = ValidationRunner().validate_relation(
            _object_relation(backend_name, backend_factory, ['{"child": {"id": 0}}']),
            plan=plan,
        )
        failure = result.failure_cases.row(0, named=True)
        assert failure["instance_path"] == "/child/id", backend_name
        assert failure["validator"] == "minimum", backend_name

    def test_recursive_array_item_object_field_reports_the_item_index(
        self, backend_name, backend_factory
    ):
        plan = compile_datacontract(
            TypeSpec(fields=[FieldSpec(
                name="payload", type=UniversalType.ARRAY,
                constraints=FieldConstraints(json_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"id": {"type": "integer", "minimum": 1}},
                    },
                }),
            )])
        )
        result = ValidationRunner().validate_relation(
            _array_relation(
                backend_name, backend_factory, ['[{"id": 1}, {"id": 0}]']
            ),
            plan=plan,
        )
        failure = result.failure_cases.row(0, named=True)
        assert failure["instance_path"] == "/1/id", backend_name
        assert failure["validator"] == "minimum", backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStructuredLengthAndMembership:
    def test_array_length_constraint_uses_the_decoded_element_count(
        self, backend_name, backend_factory
    ):
        rel = _array_relation(backend_name, backend_factory, ["[1]", "[1, 2, 3]"])
        result = _value_check(rel, "LENGTH", options={"min_length": 2})
        summary = result.check_summaries.row(0, named=True)
        assert summary["status"] == "failed", backend_name
        assert summary["fail_count"] == 1, backend_name

    def test_object_membership_uses_canonical_structural_equality(
        self, backend_name, backend_factory
    ):
        """Enum membership on a structured field compares logical values,
        not physical text -- whitespace and object-key order never change
        the outcome (spec 15's canonical_value_key algebra)."""
        rel = _object_relation(
            backend_name, backend_factory, ['{ "b": 2, "a": 1 }', '{"a": 9}']
        )
        result = _value_check(
            rel, "MEMBERSHIP", options={"allowed": [{"a": 1, "b": 2}]},
        )
        summary = result.check_summaries.row(0, named=True)
        assert summary["status"] == "failed", backend_name
        assert summary["fail_count"] == 1, backend_name

    def test_array_membership_uses_canonical_structural_equality(
        self, backend_name, backend_factory
    ):
        rel = _array_relation(backend_name, backend_factory, ["[1, 2]", "[2, 1]"])
        result = _value_check(rel, "MEMBERSHIP", options={"allowed": [[1, 2]]})
        summary = result.check_summaries.row(0, named=True)
        assert summary["status"] == "failed", backend_name
        assert summary["fail_count"] == 1, backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStructuredUniqueness:
    def test_object_uniqueness_uses_canonical_structural_equality(
        self, backend_name, backend_factory
    ):
        rel = _object_relation(
            backend_name, backend_factory, ['{"a": 1}', '{ "a" : 1 }', '{"a": 2}']
        )
        result = _value_check(rel, "UNIQUE", options={})
        summary = result.check_summaries.row(0, named=True)
        assert summary["status"] == "failed", backend_name
        assert summary["fail_count"] == 2, backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStructuredCompositeKeys:
    def test_composite_key_mixing_scalar_and_structured_fields_deduplicates(
        self, backend_name, backend_factory
    ):
        from mountainash.validation.identity import RowIdentity

        df = backend_factory.create(
            {"id": [1, 1], "tags": ["[1, 2]", "[1,2]"], "meta": ['{"a": 1}', '{"a":1}']},
            backend_name,
        )
        spec = TypeSpec(
            fields_match="open",
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(name="tags", type=UniversalType.ARRAY),
                FieldSpec(name="meta", type=UniversalType.OBJECT),
            ],
        )
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
        result = ValidationRunner().validate_relation(
            rel,
            identity=RowIdentity("keyed", ("id", "tags", "meta")),
            allow_imperfect_key=True,
        )
        assert result.identity_diagnostics["duplicate_key_tuples"] == 1, backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStructuredForeignKeys:
    def test_object_key_orphan_is_reported_cross_backend(self, backend_name, backend_factory):
        from mountainash.relations.dag.dag import RelationDAG
        from mountainash.validation import ForeignKeyRule

        parent_spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="meta", type=UniversalType.OBJECT)]
        )
        child_spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="meta", type=UniversalType.OBJECT)]
        )
        parent_rel = ma.relation(
            backend_factory.create({"meta": ['{"a": 1}']}, backend_name)
        ).conform(parent_spec, contract={"data_type": "coerce"})
        child_rel = ma.relation(
            backend_factory.create({"meta": ['{ "a" : 1 }', '{"a": 2}']}, backend_name)
        ).conform(child_spec, contract={"data_type": "coerce"})
        dag = RelationDAG()
        dag.add("parents", parent_rel)
        dag.add("children", child_rel)
        result = ValidationRunner().validate_dag(
            dag,
            {"children": [ForeignKeyRule(
                id="fk__children__meta__parents",
                child="children", parent="parents",
                child_fields=["meta"], parent_fields=["meta"],
            )]},
        )
        assert not result.fk_result.passes, backend_name
        summary = result.fk_result.check_summaries.row(0, named=True)
        assert summary["fail_count"] == 1, backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMalformedAndWrongRootStructuredInput:
    def test_malformed_json_text_is_unknown_not_a_crash(self, backend_name, backend_factory):
        rel = _object_relation(backend_name, backend_factory, ["{broken", '{"a": 1}'])
        result = _value_check(rel, "LENGTH", options={"min_length": 1})
        summary = result.check_summaries.row(0, named=True)
        assert summary["unknown_count"] == 1, backend_name
        assert summary["fail_count"] == 0, backend_name
        assert summary["status"] == "failed", backend_name  # unknown is not tolerated by default

    def test_wrong_root_is_unknown_not_a_crash(self, backend_name, backend_factory):
        """An ARRAY-declared field whose JSON text decodes to an object
        root is a structural mismatch, not a value the check ever sees."""
        rel = _array_relation(backend_name, backend_factory, ['{"a": 1}', "[1, 2]"])
        result = _value_check(rel, "LENGTH", options={"min_length": 1})
        summary = result.check_summaries.row(0, named=True)
        assert summary["unknown_count"] == 1, backend_name
        assert summary["fail_count"] == 0, backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCoerceFalseStructuredValidation:
    def test_json_schema_validates_the_logical_value_without_physical_transform(
        self, backend_name, backend_factory
    ):
        """`data_type=False` never applies the value transform, but
        validation still runs against the decoded logical value (spec
        Task 7 step 2/2.3) -- a `coerce=False` relation is exactly as
        strict as a coercing one."""
        plan = compile_datacontract(
            TypeSpec(fields=[FieldSpec(
                name="payload", type=UniversalType.OBJECT,
                constraints=FieldConstraints(json_schema={
                    "type": "object", "required": ["id"],
                    "properties": {"id": {"type": "integer", "minimum": 1}},
                }),
            )])
        )
        rel = _object_relation(
            backend_name, backend_factory, ['{"id": 0}'], apply_value_transforms=False,
        )
        result = ValidationRunner().validate_relation(rel, plan=plan)
        summary = result.check_summaries.filter(
            result.check_summaries["check_id"] == "payload_json_schema"
        ).row(0, named=True)
        assert summary["status"] == "failed", backend_name
        failure = result.failure_cases.row(0, named=True)
        assert failure["instance_path"] == "/id", backend_name
