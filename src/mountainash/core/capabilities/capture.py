"""Cold immutable evidence and source captures; never imported by lookup paths."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from mountainash.core.capabilities.identity import Scope
from mountainash.core.capabilities.schema import Scenario


def require_immutable(value: Any) -> None:
    """Reject mutable descendants, including fields inside frozen dataclasses."""
    if value is None or type(value) in (str, bytes, bool, int, float):
        return
    if isinstance(value, Enum):
        require_immutable(value.value)
        return
    if isinstance(value, type) and issubclass(value, Exception):
        return
    if type(value) in (tuple, frozenset):
        for child in value:
            require_immutable(child)
        return
    if is_dataclass(value) and not isinstance(value, type) and value.__dataclass_params__.frozen:
        for field in fields(value):
            require_immutable(getattr(value, field.name))
        return
    raise TypeError(f"capture contains mutable or unsupported {type(value).__name__}")


@dataclass(frozen=True)
class CapturedAddress:
    repository: str
    path: str
    entry: str
    revision: str | None = None
    artifact: bytes | None = None

    def __post_init__(self) -> None:
        for name in ("repository", "path", "entry"):
            if type(getattr(self, name)) is not str or not getattr(self, name):
                raise ValueError(f"captured address requires {name}")
        if (self.revision is None) == (self.artifact is None):
            raise ValueError("capture requires exactly one immutable revision or retained artifact")
        if self.revision is not None and (
            type(self.revision) is not str or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", self.revision) is None
        ):
            raise ValueError("source revision must be a complete immutable commit identity")
        if self.artifact is not None and type(self.artifact) is not bytes:
            raise TypeError("artifact must retain immutable content bytes")


@dataclass(frozen=True)
class UnresolvedHistoricalValue:
    original_encoding: str
    source_address: CapturedAddress
    reason: str

    def __post_init__(self) -> None:
        if type(self.source_address) is not CapturedAddress:
            raise TypeError("unresolved history requires a captured source address")
        if type(self.original_encoding) is not str or type(self.reason) is not str or not self.reason:
            raise ValueError("unresolved history requires original text and a reason")


@dataclass(frozen=True)
class CapturedAssertion:
    family: str
    key: Any
    payload: Any
    address: CapturedAddress
    reference_context: tuple[CapturedAddress, ...] = ()

    def __post_init__(self) -> None:
        if self.family not in {"capability", "manifestation", "gap"}:
            raise ValueError("unknown captured assertion family")
        if type(self.address) is not CapturedAddress:
            raise TypeError("assertion capture requires CapturedAddress")
        if type(self.reference_context) is not tuple or any(
            type(ref) is not CapturedAddress for ref in self.reference_context
        ):
            raise TypeError("reference context requires captured addresses")
        require_immutable(self.key)
        require_immutable(self.payload)


class BindingRole(Enum):
    OPERATIONAL_CONTRACT = "operational_contract"
    DIRECT_CURRENT_STATE = "direct_current_state"
    STRUCTURAL_EVIDENCE = "structural_evidence"


@dataclass(frozen=True)
class VerificationBinding:
    """An immutable association between a captured assertion and its observer."""

    captured_claim: CapturedAssertion
    scenario: Scenario
    role: BindingRole
    observer: CapturedAddress
    scope: Scope
    oracle: CapturedAddress
    stage: str

    def __post_init__(self) -> None:
        if type(self.captured_claim) is not CapturedAssertion:
            raise TypeError("verification binding requires a captured assertion")
        if type(self.scenario) is not Scenario:
            raise TypeError("verification binding scenario requires Scenario")
        if type(self.role) is not BindingRole:
            raise TypeError("verification binding requires BindingRole")
        if type(self.observer) is not CapturedAddress or type(self.oracle) is not CapturedAddress:
            raise TypeError("verification binding observer and oracle require captured addresses")
        if self.observer == self.oracle:
            raise ValueError("verification binding requires an independent oracle address")
        if type(self.scope) is not Scope:
            raise TypeError("verification binding scope requires Scope")
        if type(self.stage) is not str:
            raise TypeError("verification binding stage requires text")
        if self.stage not in {"construction", "compilation", "materialization"}:
            raise ValueError("unknown verification binding stage")

        from mountainash.core.capabilities.declarations import (
            DivergenceManifestation,
            QualifiedCapabilityKey,
            QualifiedManifestation,
            QualifiedManifestationKey,
        )
        from mountainash.core.capabilities.gaps import GapKey, InventoryGap
        from mountainash.core.capabilities.schema import (
            CapabilityFact,
            ExternalEntrypointTarget,
            _validate_external_target_scope,
        )

        key = self.captured_claim.key
        if type(key) is GapKey:
            expected_family = "gap"
            claim_scope = key.coverage_scope
        elif type(key) is QualifiedCapabilityKey:
            expected_family = "capability"
            claim_scope = key.scope
        elif type(key) is QualifiedManifestationKey:
            expected_family = "manifestation"
            claim_scope = key.scope
        else:
            raise ValueError("verification binding requires a resolved qualified claim key")
        if self.captured_claim.family != expected_family:
            raise ValueError("verification binding requires a resolved qualified claim key")
        if type(claim_scope) is Scope and (
            claim_scope.backend is not self.scope.backend
            or (claim_scope.dialect is not None and claim_scope != self.scope)
        ):
            raise ValueError("verification binding scope contradicts captured assertion")
        if type(key) is QualifiedManifestationKey and key.local.scenario != self.scenario:
            raise ValueError("verification binding scenario contradicts captured manifestation")
        target = (
            key.local.target if type(key) is QualifiedManifestationKey else key.target if type(key) is GapKey else None
        )
        if type(target) is ExternalEntrypointTarget:
            _validate_external_target_scope(target, self.scope)
            if self.stage != target.stage.value:
                raise ValueError("verification binding stage contradicts external entrypoint")

        payload = self.captured_claim.payload
        if type(key) is QualifiedCapabilityKey:
            from mountainash.core.capabilities.declarations import CapabilityKey

            if type(payload) is not CapabilityFact:
                raise ValueError("verification binding capability payload requires CapabilityFact")
            if CapabilityKey.from_fact(payload) != key.local:
                raise ValueError("verification binding capability payload contradicts captured key")
            if payload.backend is not key.scope.backend or payload.dialect != key.scope.dialect:
                raise ValueError("verification binding capability payload contradicts captured scope")
        elif type(key) is QualifiedManifestationKey:
            if type(payload) is QualifiedManifestation:
                if payload.key != key:
                    raise ValueError("verification binding manifestation payload contradicts captured key")
            elif type(payload) is DivergenceManifestation:
                if payload.key != key.local:
                    raise ValueError("verification binding manifestation payload contradicts captured key")
            else:
                raise ValueError("verification binding manifestation payload requires a complete manifestation")
        elif type(payload) is not InventoryGap or payload.key != key:
            raise ValueError("verification binding gap payload contradicts captured key")
        require_immutable(self)


@dataclass(frozen=True, order=True)
class EnvironmentCoordinate:
    kind: str
    name: str
    version: str | None
    original_label: str = ""

    def __post_init__(self) -> None:
        if self.kind not in {"package", "engine", "adapter", "platform", "interpreter"}:
            raise ValueError("unknown environment coordinate kind")
        if type(self.name) is not str or not self.name:
            raise ValueError("environment coordinate requires a name")
        if self.version is not None and (type(self.version) is not str or not self.version):
            raise ValueError("version must be recorded text or explicit unknown")
        if type(self.original_label) is not str:
            raise TypeError("original label must be text")
        if not self.original_label:
            object.__setattr__(self, "original_label", self.name)
        if self.kind == "package":
            normalized = re.sub(r"[-_.]+", "-", self.name).lower()
            object.__setattr__(self, "name", "ibis-framework" if normalized == "ibis" else normalized)


@dataclass(frozen=True)
class Environment:
    coordinates: tuple[EnvironmentCoordinate, ...] = ()

    def __post_init__(self) -> None:
        if type(self.coordinates) is not tuple or any(
            type(coordinate) is not EnvironmentCoordinate for coordinate in self.coordinates
        ):
            raise TypeError("environment requires immutable typed coordinates")
        versions: dict[tuple[str, str], str | None] = {}
        for coordinate in self.coordinates:
            key = coordinate.kind, coordinate.name
            if key in versions and versions[key] != coordinate.version:
                raise ValueError(f"conflicting environment versions for {key}")
            versions[key] = coordinate.version
        object.__setattr__(
            self,
            "coordinates",
            tuple(sorted(set(self.coordinates), key=lambda c: (c.kind, c.name, c.original_label))),
        )


@dataclass(frozen=True)
class SourceOrigin:
    module: str
    scope: Any
    source: Any
    domain: Any
    entry: str
    captured: CapturedAddress | None = None

    def __post_init__(self) -> None:
        from mountainash.core.capabilities.declarations import Domain, FactSource
        from mountainash.core.capabilities.identity import Scope

        if type(self.module) is not str or not self.module or type(self.entry) is not str or not self.entry:
            raise ValueError("source origin requires module and entry locator")
        if type(self.scope) is not Scope or type(self.source) is not FactSource or type(self.domain) is not Domain:
            raise TypeError("source origin requires validated scope, source and domain")
        if self.captured is not None and type(self.captured) is not CapturedAddress:
            raise TypeError("durable source origin requires CapturedAddress")


@dataclass(frozen=True)
class RuntimeOrigin:
    generation: int
    batch: int
    ordinal: int

    def __post_init__(self) -> None:
        if any(type(value) is not int or value < 0 for value in (self.generation, self.batch, self.ordinal)):
            raise ValueError("runtime origin requires nonnegative generation/batch/ordinal")


@dataclass(frozen=True)
class EvidenceCapture:
    capture_ref: CapturedAddress
    subjects: tuple[CapturedAssertion, ...]
    observed_at: str | None
    environment: Environment
    fixtures: tuple[CapturedAddress | UnresolvedHistoricalValue, ...]
    observation_layer: str
    result: Any
    provenance: tuple[CapturedAddress, ...]

    def __post_init__(self) -> None:
        from datetime import datetime

        if type(self.capture_ref) is not CapturedAddress:
            raise TypeError("evidence requires an immutable capture address")
        if (
            type(self.subjects) is not tuple
            or not self.subjects
            or any(type(subject) is not CapturedAssertion for subject in self.subjects)
        ):
            raise ValueError("evidence requires nonempty captured subjects")
        if self.observed_at is not None:
            datetime.fromisoformat(self.observed_at)
        if type(self.environment) is not Environment:
            raise TypeError("evidence requires an observed environment")
        if self.observation_layer not in {"native", "public", "gate_disabled", "structural", "historical_unknown"}:
            raise ValueError("unknown observation layer")
        if self.result is None:
            raise ValueError("evidence result requires an explicit CaptureValue null or unavailable historical value")
        for values in (self.fixtures, self.provenance):
            if type(values) is not tuple:
                raise TypeError("evidence references require immutable tuples")
        if any(type(ref) not in (CapturedAddress, UnresolvedHistoricalValue) for ref in self.fixtures):
            raise TypeError("fixture references require captured or explicitly unresolved historical addresses")
        if any(type(ref) is not CapturedAddress for ref in self.provenance):
            raise TypeError("evidence provenance requires captured addresses")
        require_immutable(self.result)
