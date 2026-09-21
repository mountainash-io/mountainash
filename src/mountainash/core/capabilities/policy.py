"""Immutable execution-policy preferences and request-local scopes."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, fields
from enum import Enum
from typing import Iterator

from mountainash.core.capabilities.schema import CapabilityIssueClass, PolicyConsumer


class ProtectionMechanism(Enum):
    """Protection surfaces enabled for a selected capability issue."""

    GATE = "gate"
    MATERIALIZATION = "materialization"


Selection = str | frozenset[CapabilityIssueClass] | None


def _validate_selection(selection: Selection, field_name: str) -> None:
    if selection is None or (type(selection) is str and selection in ("all", "none")):
        return
    if type(selection) is not frozenset:
        raise TypeError(f"{field_name} requires 'all', 'none', or a frozen issue-class set")
    if any(type(issue_class) is not CapabilityIssueClass for issue_class in selection):
        raise TypeError(f"{field_name} requires only CapabilityIssueClass members")


def _validate_mechanisms(mechanisms: frozenset[ProtectionMechanism] | None) -> None:
    if mechanisms is None:
        return
    if type(mechanisms) is not frozenset:
        raise TypeError("mechanisms requires a frozen ProtectionMechanism set")
    if any(type(mechanism) is not ProtectionMechanism for mechanism in mechanisms):
        raise TypeError("mechanisms requires only ProtectionMechanism members")


def _selection_matches(
    selection: str | frozenset[CapabilityIssueClass],
    issue_classes: frozenset[CapabilityIssueClass],
) -> bool:
    if selection == "all":
        return True
    if selection == "none":
        return False
    return not selection.isdisjoint(issue_classes)


@dataclass(frozen=True)
class CapabilityPolicy:
    """Partial configuration or fully resolved execution preferences."""

    protection: Selection = None
    error_enrichment: Selection = None
    disclosure: Selection = None
    mechanisms: frozenset[ProtectionMechanism] | None = None

    def __post_init__(self) -> None:
        _validate_selection(self.protection, "protection")
        _validate_selection(self.error_enrichment, "error_enrichment")
        _validate_selection(self.disclosure, "disclosure")
        _validate_mechanisms(self.mechanisms)

    @classmethod
    def checked(cls, **overrides: object) -> "CapabilityPolicy":
        return cls._preset({
            "protection": "all",
            "error_enrichment": "all",
            "disclosure": "all",
            "mechanisms": frozenset(ProtectionMechanism),
        }, overrides)

    @classmethod
    def native_debugging(cls, **overrides: object) -> "CapabilityPolicy":
        return cls._preset({
            "protection": "all",
            "error_enrichment": "none",
            "disclosure": "all",
            "mechanisms": frozenset(ProtectionMechanism),
        }, overrides)

    @classmethod
    def trusted(cls, **overrides: object) -> "CapabilityPolicy":
        return cls._preset({
            "protection": "none",
            "error_enrichment": "none",
            "disclosure": "none",
            "mechanisms": frozenset(),
        }, overrides)

    @classmethod
    def _preset(
        cls,
        defaults: dict[str, object],
        overrides: dict[str, object],
    ) -> "CapabilityPolicy":
        for name, value in overrides.items():
            if value is not None or name not in defaults:
                defaults[name] = value
        return cls(**defaults)

    def _resolved(self) -> None:
        if any(getattr(self, field.name) is None for field in fields(self)):
            raise ValueError("policy selection requires resolved preferences")

    def selects(
        self,
        consumer: PolicyConsumer,
        issue_classes: frozenset[CapabilityIssueClass],
    ) -> bool:
        self._resolved()
        if type(consumer) is not PolicyConsumer:
            raise TypeError("consumer requires PolicyConsumer")
        if type(issue_classes) is not frozenset or any(
            type(issue_class) is not CapabilityIssueClass for issue_class in issue_classes
        ):
            raise TypeError("issue classes require a frozen CapabilityIssueClass set")
        if consumer is PolicyConsumer.GATE:
            return (
                ProtectionMechanism.GATE in self.mechanisms
                and _selection_matches(self.protection, issue_classes)
            )
        if consumer is PolicyConsumer.RESULT_PROTECTION:
            return (
                ProtectionMechanism.MATERIALIZATION in self.mechanisms
                and _selection_matches(self.protection, issue_classes)
            )
        if consumer in (PolicyConsumer.IMMEDIATE_ERROR, PolicyConsumer.MATERIALIZATION_ERROR):
            return _selection_matches(self.error_enrichment, issue_classes)
        raise TypeError("consumer requires PolicyConsumer")

    def has_demand(self, consumer: PolicyConsumer) -> bool:
        self._resolved()
        if type(consumer) is not PolicyConsumer:
            raise TypeError("consumer requires PolicyConsumer")
        if consumer is PolicyConsumer.GATE:
            return (
                ProtectionMechanism.GATE in self.mechanisms
                and self.protection != "none"
                and self.protection != frozenset()
            )
        if consumer is PolicyConsumer.RESULT_PROTECTION:
            return (
                ProtectionMechanism.MATERIALIZATION in self.mechanisms
                and self.protection != "none"
                and self.protection != frozenset()
            )
        if consumer in (PolicyConsumer.IMMEDIATE_ERROR, PolicyConsumer.MATERIALIZATION_ERROR):
            return self.error_enrichment != "none" and self.error_enrichment != frozenset()
        raise TypeError("consumer requires PolicyConsumer")

    def discloses(self, issue_classes: frozenset[CapabilityIssueClass]) -> bool:
        self._resolved()
        if type(issue_classes) is not frozenset or any(
            type(issue_class) is not CapabilityIssueClass for issue_class in issue_classes
        ):
            raise TypeError("issue classes require a frozen CapabilityIssueClass set")
        return _selection_matches(self.disclosure, issue_classes)


def _overlay_policy(base: CapabilityPolicy, override: CapabilityPolicy) -> CapabilityPolicy:
    if type(base) is not CapabilityPolicy or type(override) is not CapabilityPolicy:
        raise TypeError("policy overlay requires CapabilityPolicy")
    return CapabilityPolicy(**{
        field.name: (
            getattr(base, field.name)
            if getattr(override, field.name) is None
            else getattr(override, field.name)
        )
        for field in fields(CapabilityPolicy)
    })


_AMBIENT_POLICY = ContextVar("mountainash_capability_policy", default=CapabilityPolicy.checked())


def _resolve_policy() -> CapabilityPolicy:
    return _AMBIENT_POLICY.get()


@contextmanager
def capability_policy(policy: CapabilityPolicy) -> Iterator[CapabilityPolicy]:
    """Overlay ``policy`` for the active context and always restore it."""

    if type(policy) is not CapabilityPolicy:
        raise TypeError("policy requires CapabilityPolicy")
    resolved = _overlay_policy(_resolve_policy(), policy)
    token = _AMBIENT_POLICY.set(resolved)
    try:
        yield resolved
    finally:
        _AMBIENT_POLICY.reset(token)
