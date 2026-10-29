"""Cold immutable evidence and source captures; never imported by lookup paths."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any


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
        if self.family not in {"capability", "gap"}:
            raise ValueError("unknown captured assertion family")
        if type(self.address) is not CapturedAddress:
            raise TypeError("assertion capture requires CapturedAddress")
        if type(self.reference_context) is not tuple or any(
            type(ref) is not CapturedAddress for ref in self.reference_context
        ):
            raise TypeError("reference context requires captured addresses")
        require_immutable(self.key)
        require_immutable(self.payload)


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
