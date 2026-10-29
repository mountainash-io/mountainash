"""Tests for RuleRegistry — composable rule collection with exclusions."""
from __future__ import annotations

import pytest
import mountainash as ma
from mountainash.datacontracts.rule import Rule
from mountainash.datacontracts.registry import RuleRegistry


@pytest.fixture
def sample_rules() -> list[Rule]:
    return [
        Rule("VR01", expr=ma.col("a").gt(0)),
        Rule("VR02", expr=ma.col("b").gt(0)),
        Rule("VR03", expr=ma.col("c").gt(0)),
    ]


class TestRuleRegistry:

    def test_create_from_list(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        assert len(registry.resolve()) == 3

    def test_resolve_returns_all_rules_without_context(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        resolved = registry.resolve()
        assert [r.id for r in resolved] == ["VR01", "VR02", "VR03"]

    def test_get_rule_by_id(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        assert registry["VR02"].id == "VR02"

    def test_get_rule_by_id_missing_raises(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        with pytest.raises(KeyError):
            registry["VR99"]

    def test_contains(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        assert "VR01" in registry
        assert "VR99" not in registry


class TestRuleRegistryComposition:

    def test_add_registries(self):
        r1 = RuleRegistry([Rule("VR01", expr=ma.col("a").gt(0))])
        r2 = RuleRegistry([Rule("VR02", expr=ma.col("b").gt(0))])
        combined = r1 + r2
        assert len(combined.resolve()) == 2
        assert [r.id for r in combined.resolve()] == ["VR01", "VR02"]

    def test_add_does_not_mutate_originals(self):
        r1 = RuleRegistry([Rule("VR01", expr=ma.col("a").gt(0))])
        r2 = RuleRegistry([Rule("VR02", expr=ma.col("b").gt(0))])
        _ = r1 + r2
        assert len(r1.resolve()) == 1
        assert len(r2.resolve()) == 1

    def test_duplicate_rule_ids_raises(self):
        # E1b: message case changed ("Duplicate rule id:" -> "duplicate rule
        # id ...") and the type is now CheckDeclarationError (a ValueError
        # subclass); intent (distinct duplicate ids raise) is unchanged.
        with pytest.raises(ValueError, match="duplicate rule"):
            RuleRegistry([
                Rule("VR01", expr=ma.col("a").gt(0)),
                Rule("VR01", expr=ma.col("b").gt(0)),
            ])


class TestRuleRegistryExclusions:

    def test_exclude_rule_for_context(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        registry.exclude("VR02", when={"version": "0102"})
        resolved = registry.resolve(context={"version": "0102"})
        assert [r.id for r in resolved] == ["VR01", "VR03"]

    def test_exclude_does_not_affect_other_contexts(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        registry.exclude("VR02", when={"version": "0102"})
        resolved = registry.resolve(context={"version": "0300"})
        assert [r.id for r in resolved] == ["VR01", "VR02", "VR03"]

    def test_exclude_without_context_returns_all(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        registry.exclude("VR02", when={"version": "0102"})
        resolved = registry.resolve()
        assert len(resolved) == 3

    def test_multiple_exclusions_same_context(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        registry.exclude("VR01", when={"version": "0102"})
        registry.exclude("VR03", when={"version": "0102"})
        resolved = registry.resolve(context={"version": "0102"})
        assert [r.id for r in resolved] == ["VR02"]

    def test_exclude_nonexistent_rule_raises(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        with pytest.raises(KeyError):
            registry.exclude("VR99", when={"version": "0102"})

    def test_multi_key_context_matching(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        registry.exclude("VR01", when={"version": "0102", "region": "AU"})
        # Partial match — rule not excluded
        resolved = registry.resolve(context={"version": "0102"})
        assert len(resolved) == 3
        # Full match — rule excluded
        resolved = registry.resolve(context={"version": "0102", "region": "AU"})
        assert [r.id for r in resolved] == ["VR02", "VR03"]


from mountainash.datacontracts.registry import ExcludedRule, ResolvedRules
from mountainash.datacontracts.rule import ContextualRule
from mountainash.validation.errors import CheckDeclarationError


def _rule(rule_id="r1"):
    return Rule(rule_id, expr=ma.col("a").ge(0))


class TestMatchers:
    def test_exclude_set_membership(self):
        reg = RuleRegistry([_rule()])
        reg.exclude("r1", when={"region": {"test", "dev"}})
        assert reg.resolve(context={"region": "dev"}) == []
        assert len(reg.resolve(context={"region": "prod"})) == 1

    def test_exclude_predicate(self):
        reg = RuleRegistry([_rule()])
        reg.exclude("r1", when={"version": lambda v: v < "0300"})
        assert reg.resolve(context={"version": "0200"}) == []
        assert len(reg.resolve(context={"version": "0400"})) == 1

    def test_exclude_absent_key_means_rule_runs(self):
        reg = RuleRegistry([_rule()])
        reg.exclude("r1", when={"region": "test"})
        assert len(reg.resolve(context={})) == 1  # exclusion needs positive evidence


class TestOnlyWhen:
    def test_only_when_gates_inclusion(self):
        reg = RuleRegistry([_rule("tiered")])
        reg.only_when("tiered", when={"batch_tier": {"C", "P"}})
        assert len(reg.resolve(context={"batch_tier": "C"})) == 1
        resolved = reg.resolve_detailed(context={"batch_tier": "N"})
        assert resolved.included == []
        assert "not applicable" in resolved.excluded[0].reason

    def test_only_when_absent_key_is_not_applicable(self):
        reg = RuleRegistry([_rule("tiered")])
        reg.only_when("tiered", when={"batch_tier": "C"})
        resolved = reg.resolve_detailed(context={})
        assert resolved.included == []
        assert "context key 'batch_tier' absent" in resolved.excluded[0].reason

    def test_gated_registry_requires_context(self):
        reg = RuleRegistry([_rule("tiered")])
        reg.only_when("tiered", when={"batch_tier": "C"})
        with pytest.raises(CheckDeclarationError):
            reg.resolve(context=None)

    def test_ungated_registry_keeps_none_shortcircuit(self):
        reg = RuleRegistry([_rule()])
        reg.exclude("r1", when={"region": "test"})
        assert len(reg.resolve(context=None)) == 1  # back-compat


class TestContextualRules:
    def test_contextual_rule_materialises(self):
        contextual = ContextualRule(
            "enum_by_version",
            build=lambda ctx: ma.col("code").is_in(
                ["A", "B"] if ctx["version"] == "0102" else ["A", "B", "C"]
            ),
            fields=["code"],
        )
        reg = RuleRegistry([contextual])
        (rule,) = reg.resolve(context={"version": "0102"})
        assert isinstance(rule, Rule)
        assert rule.id == "enum_by_version"
        assert rule.fields == ["code"]

    def test_contextual_build_failure_is_declaration_error(self):
        reg = RuleRegistry([ContextualRule("as_of_rule",
                                           build=lambda ctx: ctx["as_of"])])
        with pytest.raises(CheckDeclarationError):
            reg.resolve(context={})  # KeyError('as_of') -> declaration phase

    def test_contextual_registry_requires_context(self):
        reg = RuleRegistry([ContextualRule("c", build=lambda ctx: ma.lit(True))])
        with pytest.raises(CheckDeclarationError):
            reg.resolve(context=None)


def test_resolve_detailed_reasons_render():
    reg = RuleRegistry([_rule("a"), _rule("b")])
    reg.exclude("a", when={"region": "test"})
    reg.only_when("b", when={"tier": {"C", "P"}})
    resolved = reg.resolve_detailed(context={"region": "test", "tier": "N"})
    reasons = {e.rule.id: e.reason for e in resolved.excluded}
    assert reasons["a"].startswith("excluded:")
    assert reasons["b"].startswith("not applicable:")


class TestGateRobustness:
    def test_raising_predicate_is_declaration_error(self):
        reg = RuleRegistry([_rule()])
        reg.exclude("r1", when={"version": lambda v: v.undefined_attr})
        with pytest.raises(CheckDeclarationError, match="r1.*version"):
            reg.resolve(context={"version": "0300"})

    def test_only_when_precedes_exclude(self):
        """spec §9.6 normative precedence: not-applicable beats excluded."""
        reg = RuleRegistry([_rule()])
        reg.only_when("r1", when={"tier": "C"})
        reg.exclude("r1", when={"region": "test"})
        resolved = reg.resolve_detailed(context={"tier": "N", "region": "test"})
        assert resolved.excluded[0].reason.startswith("not applicable:")

    def test_build_must_return_expression(self):
        from datetime import datetime, timezone

        reg = RuleRegistry([ContextualRule(
            "bad", build=lambda ctx: datetime(2026, 1, 1, tzinfo=timezone.utc),
        )])
        with pytest.raises(CheckDeclarationError, match="not a mountainash expression"):
            reg.resolve(context={})


class TestCompositionPolicy:
    def test_duplicate_distinct_declarations_raise(self):
        with pytest.raises(CheckDeclarationError):
            RuleRegistry([_rule("r1"), _rule("r1")])  # two distinct objects, one id

    def test_add_with_distinct_duplicates_raises(self):
        with pytest.raises(CheckDeclarationError):
            RuleRegistry([_rule("r1")]) + RuleRegistry([_rule("r1")])

    def test_add_identical_object_dedupes_and_merges_gates(self):
        shared = _rule("shared")
        a = RuleRegistry([shared, _rule("only_a")])
        a.exclude("shared", when={"region": "test"})
        b = RuleRegistry([shared])
        b.only_when("shared", when={"tier": "C"})
        combined = a + b
        assert set(r.id for r in combined.resolve(context={"tier": "C", "region": "prod"})) == {
            "shared", "only_a",
        }
        resolved = combined.resolve_detailed(context={"tier": "N", "region": "prod"})
        assert {e.rule.id for e in resolved.excluded} == {"shared"}  # b's gate survived the merge
