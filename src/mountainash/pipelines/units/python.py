# src/mountainash/pipelines/units/python.py
from __future__ import annotations
from typing import Callable
from mountainash.pipelines.core.policies import EmptyPolicy
from mountainash.pipelines.core.values import Affinity
from mountainash.pipelines.units.base import BaseUnit


class PythonUnit(BaseUnit):
    def __init__(self, fn: Callable, *, name: str | None = None, version: str = "1", depends_on=(), empty=EmptyPolicy.WARN,
                 affinity: Affinity = Affinity.WORKER, partitions_preserved: bool = False) -> None:
        self.fn = fn; self.name = name or fn.__name__; self.version = version; self.depends_on = tuple(depends_on)
        self.empty = empty; self.affinity = affinity; self.partitions_preserved = partitions_preserved

    def run(self, upstream, ctx):
        return self.fn(*[upstream[k].payload for k in self.depends_on], ctx)


def unit(**kwargs):
    def deco(fn):
        u = PythonUnit(fn, **kwargs); u.__wrapped__ = fn; return u
    return deco
