"""Check-type IR declaration semantics."""
import pytest

import mountainash as ma
from mountainash.validation.checks import (
    BOOLEANIZERS,
    VERDICT_PASSING,
    DistributionRule,
    ForeignKeyRule,
    RelationRule,
    RowRule,
    ScalarRule,
    check_kind,
)
from mountainash.validation.errors import CheckDeclarationError


def test_row_rule_defaults():
    rule = RowRule(id="r1", expr=ma.col("age").ge(0))
    assert rule.mostly is None
    assert rule.booleanizer is None
    assert rule.severity == "blocking"
    assert rule.fields is None
    assert rule.metadata == {}


def test_severity_closed_vocabulary_on_every_check_type():
    RowRule(id="w", expr=ma.col("a").ge(0), severity="warning")
    ScalarRule(id="w2", expr=ma.col("a").mean().gt(0), severity="warning")
    RelationRule(id="w3", plan=lambda rel: rel, severity="warning")
    ForeignKeyRule(
        id="w4", child="orders", parent="customers",
        child_fields=["customer_id"], parent_fields=["id"], severity="warning",
    )
    for bad_kwargs in (
        dict(id="b1", expr=ma.col("a").ge(0), severity="warn"),
        dict(id="b2", expr=ma.col("a").ge(0), severity="BLOCKING"),
    ):
        with pytest.raises(CheckDeclarationError):
            RowRule(**bad_kwargs)
    with pytest.raises(CheckDeclarationError):
        RelationRule(id="b3", plan=lambda rel: rel, severity="advisory")


def test_row_rule_unknown_booleanizer_raises_at_declaration():
    with pytest.raises(CheckDeclarationError):
        RowRule(id="r1", expr=ma.col("age").ge(0), booleanizer="is_true")  # not t_is_true


def test_row_rule_mostly_bounds():
    RowRule(id="ok", expr=ma.col("a").ge(0), mostly=1.0)
    RowRule(id="ok2", expr=ma.col("a").ge(0), mostly=0.5)
    with pytest.raises(CheckDeclarationError):
        RowRule(id="bad", expr=ma.col("a").ge(0), mostly=0.0)
    with pytest.raises(CheckDeclarationError):
        RowRule(id="bad2", expr=ma.col("a").ge(0), mostly=1.5)


def test_row_rule_fields_validated_at_declaration():
    RowRule(id="ok", expr=ma.col("a").ge(0), fields=["a", "b"])
    with pytest.raises(CheckDeclarationError):
        RowRule(id="dup", expr=ma.col("a").ge(0), fields=["a", "a"])
    with pytest.raises(CheckDeclarationError):
        RowRule(id="empty", expr=ma.col("a").ge(0), fields=["a", ""])
    with pytest.raises(CheckDeclarationError):
        RowRule(id="none_entry", expr=ma.col("a").ge(0), fields=["a", None])


def test_require_as_of_contract():
    from datetime import datetime, timezone

    from mountainash.validation.checks import require_as_of

    aware = datetime(2026, 7, 10, tzinfo=timezone.utc)
    assert require_as_of({"as_of": aware}) is aware
    with pytest.raises(CheckDeclarationError):
        require_as_of({})  # absent
    with pytest.raises(CheckDeclarationError):
        require_as_of({"as_of": "2026-07-10"})  # not a datetime
    with pytest.raises(CheckDeclarationError):
        require_as_of({"as_of": datetime(2026, 7, 10)})  # naive


def test_verdict_passing_covers_all_booleanizers():
    assert set(VERDICT_PASSING) == set(BOOLEANIZERS)
    assert VERDICT_PASSING["t_is_true"] == frozenset({"pass"})
    assert VERDICT_PASSING["t_maybe_true"] == frozenset({"pass", "unknown"})
    assert VERDICT_PASSING["t_is_known"] == frozenset({"pass", "fail"})


def test_check_kind_mapping():
    assert check_kind(RowRule(id="r", expr=ma.col("a").ge(0))) == "row"
    assert check_kind(ScalarRule(id="s", expr=ma.col("a").mean().gt(0))) == "scalar"
    assert check_kind(RelationRule(id="q", plan=lambda rel: rel)) == "relation"
    assert (
        check_kind(
            ForeignKeyRule(
                id="fk", child="orders", parent="customers",
                child_fields=["customer_id"], parent_fields=["id"],
            )
        )
        == "foreign_key"
    )


def test_distribution_rule_reserved():
    with pytest.raises(NotImplementedError):
        DistributionRule()


def test_foreign_key_rule_arity_validated():
    with pytest.raises(CheckDeclarationError):
        ForeignKeyRule(
            id="fk", child="orders", parent="customers",
            child_fields=["a", "b"], parent_fields=["id"],
        )
