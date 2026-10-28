# src/mountainash/pipelines/units/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
import threading
from typing import Any, ClassVar, Mapping, Protocol, runtime_checkable
from mountainash.pipelines.core.policies import EmptyPolicy
from mountainash.pipelines.core.values import Affinity, Identity, SourceState, Value


@runtime_checkable
class Unit(Protocol):
    """The declared unit contract the Runner, lifecycles and ``Pipeline.graph`` are typed against.

    Structural: ``BaseUnit`` is the convenient implementation, not a requirement (design spec §7).
    """

    lifecycle: ClassVar[type]  # UnitLifecycle | SourceLifecycle | NestedLifecycle (runtime.lifecycle)
    name: str
    version: str
    affinity: Affinity
    empty: EmptyPolicy
    partitions_preserved: bool

    @property
    def exec_lock(self) -> threading.Lock:
        """One lock per unit instance: a unit never runs concurrently with itself (spec §7; F14)."""
        ...

    def inputs(self) -> tuple[str, ...]: ...

    def identity(
        self, upstream: Mapping[str, Identity], params: Mapping[str, Any], state: SourceState | None
    ) -> Identity: ...

    def reference_exists(self, ref) -> bool: ...

    def run(self, upstream: Mapping[str, Value], ctx) -> Any: ...


class BaseUnit(ABC, Unit):
    lifecycle: ClassVar[type]  # assigned by mountainash.pipelines.runtime.lifecycle at import
    name: str
    version: str = "1"
    affinity: Affinity = Affinity.WORKER
    depends_on: tuple[str, ...] = ()
    empty: EmptyPolicy = EmptyPolicy.WARN
    partitions_preserved: bool = False

    def inputs(self) -> tuple[str, ...]:
        return self.depends_on

    def identity(
        self, upstream: Mapping[str, Identity], params: Mapping[str, Any], state: SourceState | None
    ) -> Identity:
        return Identity.of(
            type(self).__name__,
            self.version,
            dict(params),
            {k: upstream[k] for k in self.inputs()},
            state,
            self._extras(),
        )

    def _extras(self) -> Any:
        return None

    def reference_exists(self, ref) -> bool:
        """Destination-owned liveness for a REFERENCE this unit produced earlier. Default: trust it. Sinks override."""
        return True

    @property
    def exec_lock(self) -> threading.Lock:
        """One lock per unit instance: a unit never runs concurrently with itself (spec §7; F14)."""
        return self.__dict__.setdefault("_exec_lock", threading.Lock())

    @abstractmethod
    def run(self, upstream: Mapping[str, Value], ctx) -> Any: ...
