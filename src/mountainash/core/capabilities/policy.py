"""Immutable execution-policy preferences and request-local scopes."""
from __future__ import annotations

import sys
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, fields
from enum import Enum
from typing import TYPE_CHECKING, Iterator

from mountainash.core.capabilities.schema import CapabilityIssueClass, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND

if TYPE_CHECKING:
    from mountainash.core.capabilities.applicability import PreparedEnvironment
    from mountainash.core.capabilities.capture import Environment
    from mountainash.core.capabilities.identity import BackendIdentity


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


@dataclass(frozen=True, eq=False)
class _CapabilityTarget:
    """The actual native owner that supplies one execution environment."""

    identity: "BackendIdentity"
    owner: object

    def __post_init__(self) -> None:
        from mountainash.core.capabilities.identity import BackendIdentity

        if type(self.identity) is not BackendIdentity:
            raise TypeError("capability target requires BackendIdentity")

    @property
    def token(self) -> tuple[CONST_BACKEND, str | None, int]:
        return self.identity.family, self.identity.dialect, id(self.owner)

    def __eq__(self, other: object) -> bool:
        if type(other) is not _CapabilityTarget:
            return NotImplemented
        return self.token == other.token

    def __hash__(self) -> int:
        return hash(self.token)


@dataclass(frozen=True)
class _ExecutionContext:
    """Resolved policy and immutable observations for one actual target."""

    policy: CapabilityPolicy
    target: _CapabilityTarget
    observations: "Environment"
    environment: "PreparedEnvironment"

    def __post_init__(self) -> None:
        from mountainash.core.capabilities.applicability import PreparedEnvironment
        from mountainash.core.capabilities.capture import Environment

        if type(self.policy) is not CapabilityPolicy:
            raise TypeError("execution context requires CapabilityPolicy")
        if type(self.target) is not _CapabilityTarget:
            raise TypeError("execution context requires _CapabilityTarget")
        if type(self.observations) is not Environment:
            raise TypeError("execution context requires Environment observations")
        if type(self.environment) is not PreparedEnvironment:
            raise TypeError("execution context requires PreparedEnvironment")


def _loaded_module_version(name: str) -> str | None:
    module = sys.modules.get(name)
    version = getattr(module, "__version__", None)
    return version if type(version) is str else None


def _polars_engine_version(target: _CapabilityTarget) -> str | None:
    if target.identity.family is CONST_BACKEND.POLARS:
        polars = sys.modules.get("polars")
        if polars is None or not isinstance(target.owner, (polars.DataFrame, polars.LazyFrame)):
            return None
    elif target.identity.family is CONST_BACKEND.NARWHALS:
        implementation = getattr(target.owner, "implementation", None)
        if getattr(implementation, "value", None) != "polars":
            return None
    return _loaded_module_version("polars")


def _engine_version(target: _CapabilityTarget, name: str) -> str | None:
    """Read a requested engine version only from an already-bound driver."""
    if type(target) is not _CapabilityTarget or type(name) is not str:
        return None
    identity = target.identity
    if name == "polars":
        if identity.family is CONST_BACKEND.POLARS:
            return _polars_engine_version(target)
        if identity.family is CONST_BACKEND.NARWHALS:
            return _polars_engine_version(target)
        if (
            identity.family is CONST_BACKEND.IBIS
            and identity.dialect == "ibis-polars"
            and type(target.owner).__module__.startswith("ibis.backends.polars")
        ):
            return _polars_engine_version(target)
        return None
    if (
        name == "duckdb"
        and identity.family is CONST_BACKEND.IBIS
        and identity.dialect == "ibis-duckdb"
    ):
        module = sys.modules.get("duckdb")
        connection_type = getattr(module, "DuckDBPyConnection", None)
        native_connection = getattr(target.owner, "con", None)
        if isinstance(connection_type, type) and isinstance(native_connection, connection_type):
            return _loaded_module_version("duckdb")
        return None
    if (
        name == "sqlite"
        and identity.family is CONST_BACKEND.IBIS
        and identity.dialect == "ibis-sqlite"
    ):
        import sqlite3

        if isinstance(getattr(target.owner, "con", None), sqlite3.Connection):
            return sqlite3.sqlite_version
    return None


def _identify_capability_target(
    data: object | None,
    *,
    family_override: CONST_BACKEND | None = None,
) -> _CapabilityTarget:
    """Bind target identity to its real native owner without opening connections."""
    from mountainash.core.backend_detection import (
        bound_ibis_backend,
        identify_backend,
        identify_backend_identity,
    )
    from mountainash.core.capabilities.identity import BackendIdentity

    if family_override is not None and type(family_override) is not CONST_BACKEND:
        raise TypeError("family_override requires CONST_BACKEND or None")
    # Polars has exactly one dialect (mirrors _resolve_backend_and_dialect's
    # own rule): a placeholder target for an overridden or otherwise
    # data-less Polars destination must still carry "polars", never an
    # unnecessarily lossy None that hides its own environment requirements
    # (spec 10.3: destination applicability, not source borrowing).
    placeholder_dialect = "polars" if family_override is CONST_BACKEND.POLARS else None
    if data is None:
        if family_override is None:
            raise ValueError("capability target requires data or family_override")
        return _CapabilityTarget(BackendIdentity(family_override, placeholder_dialect), object())

    try:
        detected_family = identify_backend(data)
    except ValueError:
        if family_override is None:
            raise
        return _CapabilityTarget(BackendIdentity(family_override, placeholder_dialect), object())
    if family_override is not None and family_override is not detected_family:
        return _CapabilityTarget(BackendIdentity(family_override, placeholder_dialect), object())
    if isinstance(data, (str, CONST_BACKEND)):
        return _CapabilityTarget(identify_backend_identity(data), object())

    if detected_family is CONST_BACKEND.IBIS:
        backend = bound_ibis_backend(data)
        name = getattr(backend, "name", None)
        if backend is None or type(name) is not str or not name:
            return _CapabilityTarget(BackendIdentity(CONST_BACKEND.IBIS, None), object())
        return _CapabilityTarget(
            BackendIdentity(CONST_BACKEND.IBIS, f"ibis-{name}"),
            backend,
        )
    return _CapabilityTarget(identify_backend_identity(data), data)


def _prepare_capability_context(
    policy: CapabilityPolicy,
    target: _CapabilityTarget,
    *,
    package_versions: dict[str, str | None],
    diagnostics_requested: bool = False,
) -> _ExecutionContext:
    """Acquire only selected policy coordinates for an actual target."""
    from importlib.metadata import PackageNotFoundError, version as distribution_version

    from mountainash.core.capabilities.applicability import prepare_environment
    from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate
    from mountainash.core.capabilities.registry import CapabilityRegistry

    if type(policy) is not CapabilityPolicy:
        raise TypeError("policy requires CapabilityPolicy")
    if type(target) is not _CapabilityTarget:
        raise TypeError("target requires _CapabilityTarget")
    if type(package_versions) is not dict:
        raise TypeError("package_versions requires a request-local dict")
    if type(diagnostics_requested) is not bool:
        raise TypeError("diagnostics_requested must be bool")

    demanded = any(policy.has_demand(consumer) for consumer in PolicyConsumer)
    disclosure = diagnostics_requested and policy.disclosure != "none" and bool(policy.disclosure)
    if not demanded and not disclosure:
        observations = Environment()
        prepared = prepare_environment(observations, frozenset())
        return _ExecutionContext(policy, target, observations, prepared)

    CapabilityRegistry.ensure_loaded()
    requirements = CapabilityRegistry.environment_requirements(
        target.identity.family,
        target.identity.dialect,
        policy,
        diagnostics_requested,
    )
    coordinates = []
    for kind, name in sorted({(kind, name) for kind, name, _ in requirements}):
        value = None
        if kind == "package":
            if name not in package_versions:
                try:
                    package_versions[name] = distribution_version(name)
                except PackageNotFoundError:
                    package_versions[name] = None
            value = package_versions[name]
        elif kind == "engine":
            value = _engine_version(target, name)
        elif kind == "interpreter" and name == "python":
            release = sys.version_info
            suffix = {
                "alpha": "a",
                "beta": "b",
                "candidate": "rc",
                "final": "",
            }[release.releaselevel]
            value = f"{release.major}.{release.minor}.{release.micro}"
            if suffix:
                value += f"{suffix}{release.serial}"
        coordinates.append(EnvironmentCoordinate(kind, name, value))
    observations = Environment(tuple(coordinates))
    prepared = prepare_environment(observations, requirements)
    return _ExecutionContext(policy, target, observations, prepared)


def _new_execution_context(
    data: object | None,
    *,
    family_override: CONST_BACKEND | None = None,
    policy: CapabilityPolicy | None = None,
    package_versions: dict[str, str | None] | None = None,
) -> _ExecutionContext:
    """Resolve one request's policy and context for a concrete target."""
    resolved = _resolve_policy() if policy is None else policy
    target = _identify_capability_target(data, family_override=family_override)
    return _prepare_capability_context(
        resolved,
        target,
        package_versions={} if package_versions is None else package_versions,
    )
