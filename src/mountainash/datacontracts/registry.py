"""RuleRegistry — composable rule collection with version-aware exclusions."""
from __future__ import annotations

from typing import Any, Iterable

from mountainash.datacontracts.rule import Rule


class RuleRegistry:
    """A composable collection of Rules with context-aware exclusions."""

    def __init__(self, rules: Iterable[Rule]) -> None:
        self._rules: dict[str, Rule] = {}
        for rule in rules:
            if rule.id in self._rules:
                raise ValueError(f"Duplicate rule id: {rule.id!r}")
            self._rules[rule.id] = rule
        self._exclusions: list[tuple[str, dict[str, Any]]] = []

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules

    def __getitem__(self, rule_id: str) -> Rule:
        return self._rules[rule_id]

    def __add__(self, other: RuleRegistry) -> RuleRegistry:
        combined = RuleRegistry(list(self._rules.values()) + list(other._rules.values()))
        combined._exclusions = list(self._exclusions) + list(other._exclusions)
        return combined

    def exclude(self, rule_id: str, *, when: dict[str, Any]) -> None:
        if rule_id not in self._rules:
            raise KeyError(f"Rule {rule_id!r} not in registry")
        self._exclusions.append((rule_id, when))

    def resolve(self, *, context: dict[str, Any] | None = None) -> list[Rule]:
        if context is None:
            return list(self._rules.values())

        excluded_ids: set[str] = set()
        for rule_id, when in self._exclusions:
            if all(context.get(k) == v for k, v in when.items()):
                excluded_ids.add(rule_id)

        return [r for r in self._rules.values() if r.id not in excluded_ids]
