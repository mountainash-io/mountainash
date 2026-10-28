# src/mountainash/pipelines/units/source.py
from __future__ import annotations
from abc import abstractmethod
from typing import Callable
from mountainash.pipelines.core.policies import EmptyPolicy
from mountainash.pipelines.core.values import Affinity, SourceResult
from mountainash.pipelines.units.base import BaseUnit


class SourceUnit(BaseUnit):
    partitions_preserved = True

    @abstractmethod
    def fetch(self, upstream, params, state) -> SourceResult: ...
    def run(self, upstream, ctx) -> SourceResult:
        return self.fetch(upstream, ctx.params, ctx.state)


class CallableSource(SourceUnit):
    def __init__(
        self, fn: Callable, *, name: str, version="1", depends_on=(), affinity=Affinity.WORKER, empty=EmptyPolicy.WARN
    ) -> None:
        self.fn, self.name, self.version, self.depends_on, self.affinity, self.empty = (
            fn,
            name,
            version,
            tuple(depends_on),
            affinity,
            empty,
        )

    def fetch(self, upstream, params, state):
        return self.fn(upstream, params, state)
