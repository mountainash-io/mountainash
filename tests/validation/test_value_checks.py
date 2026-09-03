"""Logical value-rule declaration and canonical-key behavior."""

from decimal import Decimal
from types import MappingProxyType

from mountainash.core.transit import BoundaryKey, capture_conversion_trace
from mountainash.validation import ValueRule, ValueValidatorKey, check_kind
from mountainash.validation.value import VALUE_RULE_REGISTRY, canonical_value_key


def test_value_rule_defensively_freezes_nested_inputs() -> None:
    """Mutating a declaration after construction must not change rule options."""
    fields = ["payload"]
    options = {"allowed": [1, {"nested": [2]}]}

    rule = ValueRule(
        id="payload_membership",
        fields=fields,
        validator=ValueValidatorKey.MEMBERSHIP,
        options=options,
    )
    fields.append("later")
    options["allowed"].append(3)

    assert rule.fields == ("payload",)
    assert rule.options["allowed"] == (1, MappingProxyType({"nested": (2,)}))
    assert check_kind(rule) == "value"


def test_value_rule_registry_is_closed() -> None:
    """Adding a validator without execution ownership must fail closed."""
    assert set(VALUE_RULE_REGISTRY) == set(ValueValidatorKey)


def test_value_rule_registry_entries_expose_evaluate_only() -> None:
    for entry in VALUE_RULE_REGISTRY.values():
        assert callable(entry.evaluate)
        assert not hasattr(entry, "execute")


def test_value_rule_fallback_materialization_records_terminal_boundary() -> None:
    import polars as pl

    import mountainash as ma
    from mountainash.validation import RowIdentity, ValidationRunner

    relation = ma.relation(pl.DataFrame({"state": ["open"]}))
    check = ValueRule(
        id="state_membership",
        fields=["state"],
        validator=ValueValidatorKey.MEMBERSHIP,
        options={"allowed": ["open"]},
    )
    runner = ValidationRunner()
    with capture_conversion_trace() as trace:
        runner._materialized_value_frame = None
        summary, failures = runner._run_value_rule(
            relation, check, RowIdentity("none"), failure_sample=None
        )
    assert summary.status == "passed"
    assert failures.height == 0
    assert any(
        record.boundary_key is BoundaryKey.RELATION_TO_POLARS_TERMINAL
        for record in trace.records
    )


def test_canonical_keys_do_not_collapse_bool_and_integer() -> None:
    """Typed key equality must preserve Python's bool/int distinction."""
    assert canonical_value_key(True) != canonical_value_key(1)
    assert canonical_value_key(Decimal("1.0")) == canonical_value_key(1)
    assert canonical_value_key(-0.0) == canonical_value_key(0.0)


def test_value_rule_rejects_invalid_registry_options() -> None:
    """A registry key owns its declaration options at construction time."""
    import pytest

    from mountainash.validation.errors import CheckDeclarationError

    with pytest.raises(CheckDeclarationError, match="requires sequence option 'allowed'"):
        ValueRule(
            id="invalid_membership",
            fields=["state"],
            validator=ValueValidatorKey.MEMBERSHIP,
            options={"allowed": "open"},
        )


def test_membership_rule_runs_on_logical_values() -> None:
    """A membership rule must report data failures, not an executor error."""
    import polars as pl

    from mountainash.validation import ValidationRunner

    result = ValidationRunner().validate_relation(
        pl.DataFrame({"state": ["open", "closed"]}),
        [
            ValueRule(
                id="state_membership",
                fields=["state"],
                validator=ValueValidatorKey.MEMBERSHIP,
                options={"allowed": ["open"]},
            )
        ],
    )

    summary = result.check_summaries.row(0, named=True)
    assert summary["check_kind"] == "value"
    assert summary["status"] == "failed"
    assert summary["fail_count"] == 1


def test_membership_rule_compares_structured_logical_values() -> None:
    """Structured enum values compare by canonical logical keys, not identity."""
    import polars as pl

    from mountainash.validation import ValidationRunner

    result = ValidationRunner().validate_relation(
        pl.DataFrame(
            {"payload": [{"child": "first", "rank": 1}, {"child": "later", "rank": 2}]}
        ),
        [
            ValueRule(
                id="payload_membership",
                fields=["payload"],
                validator=ValueValidatorKey.MEMBERSHIP,
                options={"allowed": [{"rank": 1, "child": "first"}]},
            )
        ],
    )

    summary = result.check_summaries.row(0, named=True)
    assert summary["status"] == "failed"
    assert summary["fail_count"] == 1


def test_compiled_plan_runner_conforms_once_before_checks(monkeypatch) -> None:
    """Plan execution conforms before intrinsic logical-value validation."""
    import polars as pl

    import mountainash as ma
    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.relations import Relation
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    from mountainash.validation import ValidationRunner

    relation = ma.relation(pl.DataFrame({"old": ["1", "2"]}))
    compilation_calls = 0
    original_compile = Relation._compile_and_execute_with_visitor

    def counted_compile(self, *args, **kwargs):
        nonlocal compilation_calls
        compilation_calls += 1
        return original_compile(self, *args, **kwargs)

    monkeypatch.setattr(Relation, "_compile_and_execute_with_visitor", counted_compile)
    plan = compile_datacontract(
        TypeSpec(
            fields=[
                FieldSpec(name="id", rename_from="old", type=UniversalType.INTEGER),
            ]
        )
    )

    result = ValidationRunner().validate_relation(relation, plan=plan)

    assert result.passes
    assert result._materialized_source.to_dict(as_series=False) == {"id": [1, 2]}
    assert compilation_calls == 1


def test_binary_string_format_uses_base64_lexical_validation() -> None:
    """Accepted binary-format declarations must not reject every value."""
    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    from mountainash.validation import ValidationRunner

    result = ValidationRunner().validate_relation(
        pl.DataFrame({"payload": ["AQI=", "not base64"]}),
        plan=compile_datacontract(
            TypeSpec(
                fields=[
                    FieldSpec(
                        name="payload",
                        type=UniversalType.STRING,
                        format="binary",
                    )
                ]
            )
        ),
    )

    summary = result.check_summaries.filter(
        pl.col("check_id") == "payload_string_format"
    ).row(0, named=True)
    assert summary["pass_count"] == 1
    assert summary["fail_count"] == 1


def test_value_rule_keeps_row_number_identity_from_cached_frame() -> None:
    """ValueRule failures retain row ordinals after one materialization."""
    import polars as pl

    from mountainash.validation import RowIdentity, ValidationRunner

    result = ValidationRunner().validate_relation(
        pl.DataFrame({"state": ["open", "closed"]}),
        [
            ValueRule(
                id="state_membership",
                fields=["state"],
                validator=ValueValidatorKey.MEMBERSHIP,
                options={"allowed": ["open"]},
            )
        ],
        identity=RowIdentity("row_number"),
    )

    assert result.check_summaries["status"].item() == "failed"
    assert result.failure_cases["row_number"].to_list() == [1]


def test_nested_object_rule_executes_instead_of_isolating_an_error() -> None:
    """Nested declarations must produce a data verdict for valid objects."""
    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    from mountainash.validation import ValidationRunner

    result = ValidationRunner().validate_relation(
        pl.DataFrame({"payload": [{"child": "ok"}]}),
        plan=compile_datacontract(
            TypeSpec(
                fields=[
                    FieldSpec(
                        name="payload",
                        type=UniversalType.OBJECT,
                        object_fields=[FieldSpec(name="child", type=UniversalType.STRING)],
                    )
                ]
            )
        ),
    )

    assert result.check_summaries.filter(pl.col("check_id") == "payload_nested")[
        "status"
    ].item() == "passed"
