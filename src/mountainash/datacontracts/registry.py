"""RuleRegistry — composable rule collection with context-aware applicability
gating (spec §9.6). The registry owns applicability; rule bodies stay pure
expressions (never `lit(True)`-to-skip)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable

from mountainash.validation.errors import CheckDeclarationError

if TYPE_CHECKING:
    from mountainash.datacontracts.rule import ContextualRule, Rule


@dataclass(frozen=True)
class ExcludedRule:
    """A rule left out of a resolution, with the human-readable reason
    (surfaced downstream as a status='skipped' CheckSummary)."""

    rule: "Rule | ContextualRule"
    reason: str


@dataclass(frozen=True)
class ResolvedRules:
    included: "list[Rule]"
    excluded: "list[ExcludedRule]"


def _render(condition: Any) -> str:
    if callable(condition):
        name = getattr(condition, "__name__", "<lambda>")
        return "<predicate>" if name == "<lambda>" else f"<{name}>"
    return repr(condition)


def _matches(condition: Any, value: Any) -> bool:
    """Scalar -> equality; set/frozenset/list/tuple -> membership;
    callable -> predicate. (spec §9.6)"""
    if callable(condition):
        return bool(condition(value))
    if isinstance(condition, (set, frozenset, list, tuple)):
        return value in condition
    return value == condition


class RuleRegistry:
    """A composable collection of Rules with context-aware applicability gating."""

    def __init__(self, rules: "Iterable[Rule | ContextualRule]") -> None:
        self._rules: "dict[str, Rule | ContextualRule]" = {}
        for rule in rules:
            existing = self._rules.get(rule.id)
            if existing is rule:
                continue  # identical object twice: composition, not conflict
            if existing is not None:
                # CheckDeclarationError subclasses ValueError (spec §11), so
                # callers catching the old ValueError keep working
                raise CheckDeclarationError(
                    f"duplicate rule id {rule.id!r}: two distinct declarations "
                    "under one id (rename one, or share the same object)"
                )
            self._rules[rule.id] = rule
        self._exclusions: list[tuple[str, dict[str, Any]]] = []
        self._inclusion_gates: list[tuple[str, dict[str, Any]]] = []

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules

    def __getitem__(self, rule_id: str) -> "Rule | ContextualRule":
        return self._rules[rule_id]

    def __add__(self, other: "RuleRegistry") -> "RuleRegistry":
        combined = RuleRegistry(list(self._rules.values()) + list(other._rules.values()))
        combined._exclusions = list(self._exclusions) + list(other._exclusions)
        combined._inclusion_gates = (
            list(self._inclusion_gates) + list(other._inclusion_gates)
        )
        return combined

    def exclude(self, rule_id: str, *, when: dict[str, Any]) -> None:
        """Exclude the rule when ALL conditions match. An absent context key
        never matches — exclusion requires positive evidence."""
        if rule_id not in self._rules:
            raise KeyError(f"Rule {rule_id!r} not in registry")
        self._exclusions.append((rule_id, when))

    def only_when(self, rule_id: str, *, when: dict[str, Any]) -> None:
        """Include-gate: the rule runs only when ALL conditions match. An
        absent context key -> not applicable (closed-by-default). Multiple
        gates on one rule conjoin."""
        if rule_id not in self._rules:
            raise KeyError(f"Rule {rule_id!r} not in registry")
        self._inclusion_gates.append((rule_id, when))

    # -- resolution -----------------------------------------------------------

    def _has_contextual_rules(self) -> bool:
        from mountainash.datacontracts.rule import ContextualRule

        return any(isinstance(r, ContextualRule) for r in self._rules.values())

    def _match_or_raise(
        self, rule_id: str, key: str, condition: Any, value: Any
    ) -> bool:
        """Matcher evaluation is declaration-phase code (spec §9.6): a raising
        predicate is a misdeclared suite, surfaced as CheckDeclarationError."""
        try:
            return _matches(condition, value)
        except Exception as exc:
            raise CheckDeclarationError(
                f"gate predicate for rule {rule_id!r}, context key {key!r} "
                f"raised {type(exc).__name__}: {exc}"
            ) from exc

    def _exclusion_reason(
        self, rule_id: str, context: dict[str, Any]
    ) -> "str | None":
        # Normative precedence (spec §9.6): include-gates BEFORE exclusions —
        # a rule that does not apply is "not applicable" even when an
        # exclusion would also match. Registration order within each
        # polarity; the first decisive clause supplies the reason.
        for gated_id, when in self._inclusion_gates:
            if gated_id != rule_id:
                continue
            for key, condition in when.items():
                if key not in context:
                    return f"not applicable: context key {key!r} absent"
                if not self._match_or_raise(rule_id, key, condition, context[key]):
                    return (
                        f"not applicable: {key} does not match {_render(condition)}"
                        f" (got {context[key]!r})"
                    )
        for excluded_id, when in self._exclusions:
            if excluded_id != rule_id:
                continue
            if all(
                key in context
                and self._match_or_raise(rule_id, key, condition, context[key])
                for key, condition in when.items()
            ):
                clauses = ", ".join(
                    f"{key} matches {_render(condition)}"
                    for key, condition in when.items()
                )
                return f"excluded: {clauses}"
        return None

    def _materialise(
        self, rule: "Rule | ContextualRule", context: dict[str, Any]
    ) -> "Rule":
        from mountainash.datacontracts.rule import ContextualRule, Rule

        if not isinstance(rule, ContextualRule):
            return rule
        try:
            expr = rule.build(dict(context))
        except Exception as exc:
            raise CheckDeclarationError(
                f"ContextualRule {rule.id!r} build failed: {type(exc).__name__}: {exc}"
            ) from exc
        if not hasattr(expr, "_node"):
            # spec §9.6: a builder returning a raw datetime / Polars expr /
            # anything else must fail here, not as a classify crash later
            raise CheckDeclarationError(
                f"ContextualRule {rule.id!r} build returned "
                f"{type(expr).__name__} — not a mountainash expression "
                "(BaseExpressionAPI)"
            )
        return Rule(
            rule.id, expr=expr, mostly=rule.mostly, booleanizer=rule.booleanizer,
            severity=rule.severity, error_message=rule.error_message,
            fields=rule.fields, metadata=rule.metadata,
        )

    def resolve_detailed(
        self, *, context: "dict[str, Any] | None" = None
    ) -> ResolvedRules:
        if context is None:
            if self._inclusion_gates or self._has_contextual_rules():
                raise CheckDeclarationError(
                    "registry has only_when gates or ContextualRules; resolve "
                    "requires a context dict (pass context={} to evaluate "
                    "gates against an empty context)"
                )
            return ResolvedRules(list(self._rules.values()), [])

        included: "list[Rule]" = []
        excluded: list[ExcludedRule] = []
        for rule in self._rules.values():
            reason = self._exclusion_reason(rule.id, context)
            if reason is not None:
                excluded.append(ExcludedRule(rule, reason))
            else:
                included.append(self._materialise(rule, context))
        return ResolvedRules(included, excluded)

    def resolve(self, *, context: "dict[str, Any] | None" = None) -> "list[Rule]":
        return self.resolve_detailed(context=context).included
