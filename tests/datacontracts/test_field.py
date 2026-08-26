"""Native Field descriptor and constraint->check compilation."""
import polars as pl

import mountainash as ma
from mountainash.datacontracts.field import Field
from mountainash.validation import RowRule, ValidationRunner


def _ids(checks):
    return [c.id for c in checks]


class TestFieldToChecks:
    def test_not_nullable_emits_not_null(self):
        checks = Field(nullable=False).to_checks("age")
        assert _ids(checks) == ["age_type_format", "age__not_null"]

    def test_range_checks_guarded_when_nullable(self):
        checks = Field(ge=0, le=100).to_checks("age")
        assert _ids(checks) == ["age_type_format", "age_range"]
        # guarded: a null age is not a range violation
        df = pl.DataFrame({"age": [50, None]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        assert result.passes

    def test_unguarded_when_not_nullable(self):
        checks = Field(nullable=False, ge=0).to_checks("age")
        df = pl.DataFrame({"age": [1, None]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        # not_null check fails on the null row; ge check is unguarded so the
        # null surfaces as unknown there rather than being silently passed
        assert not result.passes

    def test_string_constraints(self):
        checks = Field(
            str_matches=r".+@.+", str_length={"min_value": 3, "max_value": 50}
        ).to_checks("email")
        assert _ids(checks) == ["email_type_format", "email_length", "email_pattern"]

    def test_isin(self):
        checks = Field(isin=["open", "closed"]).to_checks("status")
        assert _ids(checks) == ["status_type_format", "status_enum_membership"]
        df = pl.DataFrame({"status": ["open", "bogus", None]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        summary = result.check_summaries.filter(
            result.check_summaries["check_id"] == "status_enum_membership"
        ).row(0, named=True)
        assert summary["fail_count"] == 1      # "bogus"
        assert summary["pass_count"] == 2      # "open" + guarded null passes

    def test_unique_uses_canonical_value_keys(self):
        checks = Field(unique=True).to_checks("id")
        assert _ids(checks) == ["id_type_format", "id_unique"]
        df = pl.DataFrame({"id": [1, 2, 2]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        summary = result.check_summaries.filter(
            result.check_summaries["check_id"] == "id_unique"
        ).row(0, named=True)
        assert summary["fail_count"] == 2  # both duplicate rows flagged

    def test_fields_attribute_set_for_column_attribution(self):
        checks = Field(ge=0).to_checks("age")
        assert checks[1].fields == ("age",)

    def test_full_vocabulary_kwargs(self):
        """spec §9.1 third amendment: the beyond-Frictionless comparison/
        membership/string kwargs each compile to a guarded RowRule."""
        checks = Field(
            eq=5, ne=0, gt=1, lt=9, notin=[7],
            str_contains="a", str_startswith="b", str_endswith="c",
        ).to_checks("x")
        assert _ids(checks) == [
            "x_type_format",
            "x__eq", "x__ne", "x__gt", "x__lt", "x__notin",
            "x__str_contains", "x__str_startswith", "x__str_endswith",
        ]
        # guarded: nulls are not violations of any of these
        df = pl.DataFrame({"v": ["banana_c", None]})
        result = ValidationRunner().validate_relation(
            ma.relation(df),
            Field(str_startswith="b", str_endswith="c").to_checks("v"),
        )
        assert result.passes

    def test_severity_flows_onto_emitted_checks(self):
        checks = Field(nullable=False, ge=0, severity="warning").to_checks("age")
        assert all(c.severity == "warning" for c in checks)
        df = pl.DataFrame({"age": [-1, 5]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        assert result.passes  # failed warning never blocks (spec §8)
        assert "failed" in result.check_summaries["status"].to_list()


class TestFieldToConstraints:
    def test_round_trip_kwargs(self):
        constraints = Field(
            nullable=False, ge=0, le=10, isin=[1, 2],
            str_matches=r"\d+", str_length={"min_value": 1, "max_value": 2},
            unique=True,
        ).to_constraints()
        assert constraints.required is True
        assert constraints.unique is True
        assert (constraints.minimum, constraints.maximum) == (0, 10)
        assert (constraints.min_length, constraints.max_length) == (1, 2)
        assert constraints.pattern == r"\d+"
        assert constraints.enum == [1, 2]


class TestPrimaryKeyUnique:
    """spec §9.3 third amendment: TypeSpec.primary_key -> composite-uniqueness
    RelationRule, reported as a check result independent of identity use."""

    def test_composite_primary_key_emits_relation_rule(self):
        from mountainash.datacontracts.compiler import compile_datacontract
        from mountainash.typespec.spec import FieldSpec, TypeSpec
        from mountainash.typespec.universal_types import UniversalType
        from mountainash.validation import RelationRule

        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.ANY), FieldSpec(name="b", type=UniversalType.ANY)], primary_key=["a", "b"]
        )
        plan = compile_datacontract(spec)
        pk = [c for c in plan.checks if c.id == "primary_key_unique"]
        assert len(pk) == 1 and isinstance(pk[0], RelationRule)

        df = pl.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "x"]})
        result = ValidationRunner().validate_relation(ma.relation(df), pk)
        summary = result.check_summaries.row(0, named=True)
        assert summary["status"] == "failed"
        assert summary["fail_count"] == 1  # one duplicated key tuple (1, "x")

    def test_no_primary_key_no_check(self):
        from mountainash.datacontracts.compiler import compile_datacontract
        from mountainash.typespec.spec import FieldSpec, TypeSpec
        from mountainash.typespec.universal_types import UniversalType

        plan = compile_datacontract(
            TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.ANY)])
        )
        assert "primary_key_unique" not in [c.id for c in plan.checks]
