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
        with pytest.raises(ValueError, match="Duplicate rule"):
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
