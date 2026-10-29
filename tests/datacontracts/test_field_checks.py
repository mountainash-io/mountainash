"""FieldDefinition constraint->check compilation (one shared evaluator)."""
import polars as pl

import mountainash as ma
from mountainash.typespec import FieldDefinition, TableSchema, UniversalType
from mountainash.validation import RowRule, ValidationRunner


def _ids(checks):
    return [c.id for c in checks]


def _summary(result, check_id):
    return result.check_summaries.filter(
        result.check_summaries["check_id"] == check_id
    ).row(0, named=True)


class TestDefinitionToChecks:
    def test_required_emits_not_null(self):
        checks = FieldDefinition(required=True).to_checks("age")
        assert _ids(checks) == ["age_type_format", "age__not_null"]

    def test_range_checks_guarded_when_nullable(self):
        checks = FieldDefinition(minimum=0, maximum=100).to_checks("age")
        assert _ids(checks) == ["age_type_format", "age_range"]
        # guarded: a null age is not a range violation
        df = pl.DataFrame({"age": [50, None]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        assert result.passes

    def test_unguarded_when_required(self):
        checks = FieldDefinition(required=True, minimum=0).to_checks("age")
        df = pl.DataFrame({"age": [1, None]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        # not_null check fails on the null row; the range check is unguarded so
        # the null surfaces as unknown there rather than being silently passed
        assert not result.passes

    def test_string_constraints(self):
        checks = FieldDefinition(
            pattern=r".+@.+", min_length=3, max_length=50
        ).to_checks("email")
        assert _ids(checks) == ["email_type_format", "email_length", "email_pattern"]

    def test_enum(self):
        checks = FieldDefinition(enum=["open", "closed"]).to_checks("status")
        assert _ids(checks) == ["status_type_format", "status_enum_membership"]
        df = pl.DataFrame({"status": ["open", "bogus", None]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        summary = _summary(result, "status_enum_membership")
        assert summary["fail_count"] == 1      # "bogus"
        assert summary["pass_count"] == 2      # "open" + guarded null passes

    def test_unique_uses_canonical_value_keys(self):
        checks = FieldDefinition(unique=True).to_checks("id")
        assert _ids(checks) == ["id_type_format", "id_unique"]
        df = pl.DataFrame({"id": [1, 2, 2]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        assert _summary(result, "id_unique")["fail_count"] == 2  # both duplicate rows flagged

    def test_fields_attribute_set_for_column_attribution(self):
        checks = FieldDefinition(minimum=0).to_checks("age")
        assert checks[1].fields == ("age",)

    def test_full_vocabulary(self):
        """spec §9.1 third amendment: the complete constraint vocabulary compiles
        to checks; strict bounds share the range rule, the comparison/membership/
        string constraints each compile to a guarded RowRule."""
        checks = FieldDefinition(
            eq=5, ne=0, exclusive_minimum=1, exclusive_maximum=9, notin=[7],
            str_contains="a", str_startswith="b", str_endswith="c",
        ).to_checks("x")
        assert _ids(checks) == [
            "x_type_format",
            "x_range",
            "x__eq", "x__ne", "x__notin",
            "x__str_contains", "x__str_startswith", "x__str_endswith",
        ]
        # guarded: nulls are not violations of any of these
        df = pl.DataFrame({"v": ["banana_c", None]})
        result = ValidationRunner().validate_relation(
            ma.relation(df),
            FieldDefinition(str_startswith="b", str_endswith="c").to_checks("v"),
        )
        assert result.passes

    def test_strict_bounds_exclude_the_boundary(self):
        checks = FieldDefinition(exclusive_minimum=0, exclusive_maximum=10).to_checks("n")
        df = pl.DataFrame({"n": [0, 5, 10]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        assert _summary(result, "n_range")["fail_count"] == 2  # both boundaries

    def test_severity_flows_onto_emitted_checks(self):
        checks = FieldDefinition(required=True, minimum=0, severity="warning").to_checks("age")
        assert all(c.severity == "warning" for c in checks)
        df = pl.DataFrame({"age": [-1, 5]})
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        assert result.passes  # failed warning never blocks (spec §8)
        assert "failed" in result.check_summaries["status"].to_list()

    def test_severity_defaults_to_blocking(self):
        checks = FieldDefinition(required=True, eq=1).to_checks("v")
        assert {c.severity for c in checks} == {"blocking"}

    def test_one_definition_compiles_under_each_local_name(self):
        """Names are contextual: the same unnamed definition addresses each column."""
        quantity = FieldDefinition(
            type=UniversalType.INTEGER, required=True, minimum=0, severity="warning"
        )
        ordered = quantity.to_checks("ordered")
        shipped = quantity.to_checks("shipped")
        assert _ids(ordered) == ["ordered_type_format", "ordered__not_null", "ordered_range"]
        assert _ids(shipped) == ["shipped_type_format", "shipped__not_null", "shipped_range"]
        assert all(isinstance(c, RowRule) or c.fields == ("shipped",) for c in shipped)
        df = pl.DataFrame({"ordered": [1, 2], "shipped": [-1, 2]})
        result = ValidationRunner().validate_relation(ma.relation(df), [*ordered, *shipped])
        assert _summary(result, "shipped_range")["fail_count"] == 1
        assert _summary(result, "ordered_range")["fail_count"] == 0


class TestPrimaryKeyUnique:
    """spec §9.3 third amendment: TableSchema.primary_key -> composite-uniqueness
    RelationRule, reported as a check result independent of identity use."""

    def test_composite_primary_key_emits_relation_rule(self):
        from mountainash.datacontracts.compiler import compile_datacontract
        from mountainash.validation import RelationRule

        schema = TableSchema(
            fields={"a": FieldDefinition(), "b": FieldDefinition()},
            primary_key=["a", "b"],
        )
        plan = compile_datacontract(schema)
        pk = [c for c in plan.checks if c.id == "primary_key_unique"]
        assert len(pk) == 1 and isinstance(pk[0], RelationRule)

        df = pl.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "x"]})
        result = ValidationRunner().validate_relation(ma.relation(df), pk)
        summary = result.check_summaries.row(0, named=True)
        assert summary["status"] == "failed"
        assert summary["fail_count"] == 1  # one duplicated key tuple (1, "x")

    def test_no_primary_key_no_check(self):
        from mountainash.datacontracts.compiler import compile_datacontract

        plan = compile_datacontract(TableSchema(fields={"a": FieldDefinition()}))
        assert "primary_key_unique" not in [c.id for c in plan.checks]
