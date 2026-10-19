"""FieldSpec declaration checks and validation behavior."""
import polars as pl

import mountainash as ma
from mountainash.typespec import FieldSpec, UniversalType
from mountainash.validation import ValidationRunner


def _ids(checks):
    return [check.id for check in checks]


def test_direct_member_compilation_preserves_extended_constraints_and_null_guards():
    definition = FieldSpec(
        type=UniversalType.STRING,
        required=False,
        eq="abc",
        ne="no",
        notin=["z"],
        str_contains="a",
        str_startswith="a",
        str_endswith="c",
    )
    checks = definition.to_checks("value")
    assert _ids(checks) == [
        "value_type_format", "value__eq", "value__ne", "value__notin",
        "value__str_contains", "value__str_startswith", "value__str_endswith",
    ]
    result = ValidationRunner().validate_relation(
        ma.relation(pl.DataFrame({"value": [None, "abc"]})), checks
    )
    assert result.passes


def test_direct_member_compilation_preserves_severity_and_strict_bounds():
    checks = FieldSpec(exclusive_minimum=0, severity="warning").to_checks("age")
    assert all(check.severity == "warning" for check in checks)
    result = ValidationRunner().validate_relation(
        ma.relation(pl.DataFrame({"age": [0, 1]})), checks
    )
    summary = result.check_summaries.filter(
        pl.col("check_id") == "age_range"
    ).row(0, named=True)
    assert summary["fail_count"] == 1
    assert result.passes


def test_constraints_reverse_conversion_retains_extended_vocabulary():
    from mountainash.datacontracts.compiler import contract_from_typespec
    from mountainash.typespec import TypeSpec, UniversalType

    definition = FieldSpec(
        type=UniversalType.STRING,
        eq="x",
        ne="z",
        notin=["bad"],
        str_contains="a",
        str_startswith="b",
        str_endswith="c",
        severity="warning",
    )
    generated = contract_from_typespec(
        TypeSpec(fields={"value": definition}), name="Generated"
    )
    assert generated._contract_fields["value"] is definition
    checks = generated.to_checks()
    assert {check.id for check in checks if check.id.startswith("value__")} == {
        "value__eq", "value__ne", "value__notin", "value__str_contains",
        "value__str_startswith", "value__str_endswith",
    }
    assert all(check.severity == "warning" for check in checks)


def _summary(result, check_id):
    row = result.check_summaries.filter(pl.col("check_id") == check_id).row(0, named=True)
    return row["status"], row["pass_count"], row["fail_count"]


def test_range_is_guarded_for_optional_values():
    checks = FieldSpec(type=UniversalType.INTEGER, minimum=0, maximum=100).to_checks("age")
    assert _ids(checks) == ["age_type_format", "age_range"]
    assert checks[1].fields == ("age",)
    result = ValidationRunner().validate_relation(ma.relation(pl.DataFrame({"age": [50, None]})), checks)
    assert result.passes


def test_required_value_reports_null_as_violation():
    checks = FieldSpec(type=UniversalType.INTEGER, required=True, minimum=0).to_checks("age")
    assert _ids(checks) == ["age_type_format", "age__not_null", "age_range"]
    result = ValidationRunner().validate_relation(ma.relation(pl.DataFrame({"age": [1, None]})), checks)
    assert _summary(result, "age__not_null") == ("failed", 1, 1)
    assert not result.passes


def test_enum_membership_counts_guarded_nulls_as_passing():
    checks = FieldSpec(type=UniversalType.STRING, enum=["open", "closed"]).to_checks("status")
    assert _ids(checks) == ["status_type_format", "status_enum_membership"]
    result = ValidationRunner().validate_relation(
        ma.relation(pl.DataFrame({"status": ["open", "bogus", None]})), checks
    )
    assert _summary(result, "status_enum_membership") == ("failed", 2, 1)


def test_unique_flags_every_duplicate_row():
    checks = FieldSpec(type=UniversalType.INTEGER, unique=True).to_checks("id")
    result = ValidationRunner().validate_relation(ma.relation(pl.DataFrame({"id": [1, 2, 2]})), checks)
    assert _summary(result, "id_unique") == ("failed", 1, 2)


def test_length_and_pattern_report_independent_outcomes():
    checks = FieldSpec(type=UniversalType.STRING, pattern=r".+@.+", min_length=3, max_length=50).to_checks("email")
    assert _ids(checks) == ["email_type_format", "email_length", "email_pattern"]
    result = ValidationRunner().validate_relation(
        ma.relation(pl.DataFrame({"email": ["a@b.c", "ab", "abcdef"]})), checks
    )
    assert _summary(result, "email_length") == ("failed", 2, 1)
    assert _summary(result, "email_pattern") == ("failed", 1, 2)


def test_warning_severity_failure_does_not_block():
    checks = FieldSpec(type=UniversalType.INTEGER, required=True, minimum=0, severity="warning").to_checks("age")
    assert all(check.severity == "warning" for check in checks)
    result = ValidationRunner().validate_relation(ma.relation(pl.DataFrame({"age": [-1, 5]})), checks)
    assert _summary(result, "age_range") == ("failed", 1, 1)
    assert result.passes


class TestPrimaryKeyUnique:
    """TypeSpec.primary_key produces a composite uniqueness rule."""

    def test_composite_primary_key_emits_relation_rule(self):
        from mountainash.datacontracts.compiler import compile_datacontract
        from mountainash.typespec import TypeSpec, UniversalType
        from mountainash.validation import RelationRule

        spec = TypeSpec(fields={"a": FieldSpec(type=UniversalType.ANY), "b": FieldSpec(type=UniversalType.ANY)}, primary_key=["a", "b"])
        plan = compile_datacontract(spec)
        pk = [check for check in plan.checks if check.id == "primary_key_unique"]
        assert len(pk) == 1 and isinstance(pk[0], RelationRule)

        data = pl.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "x"]})
        result = ValidationRunner().validate_relation(ma.relation(data), pk)
        summary = result.check_summaries.row(0, named=True)
        assert summary["status"] == "failed"
        assert summary["fail_count"] == 1

    def test_no_primary_key_no_check(self):
        from mountainash.datacontracts.compiler import compile_datacontract
        from mountainash.typespec import TypeSpec, UniversalType

        plan = compile_datacontract(TypeSpec(fields={"a": FieldSpec(type=UniversalType.ANY)}))
        assert "primary_key_unique" not in [check.id for check in plan.checks]
