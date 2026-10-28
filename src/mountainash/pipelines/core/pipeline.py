# src/mountainash/pipelines/core/pipeline.py
from __future__ import annotations
from typing import TYPE_CHECKING, Iterable
from mountainash.graph.container import Graph

if TYPE_CHECKING:
    from mountainash.pipelines.units.base import BaseUnit


class Pipeline:
    def __init__(self, name: str, *, inputs: Iterable[str] = ()) -> None:
        self.name = name
        self.inputs = frozenset(inputs)
        self.graph: Graph[BaseUnit] = Graph()

    def add(self, unit: BaseUnit) -> "Pipeline":
        internal = [d for d in unit.inputs() if d not in self.inputs]
        for d in internal:
            if d not in self.graph.nodes:
                raise KeyError(
                    f"{unit.name!r} depends on {d!r}, which is neither a unit of {self.name!r} nor a declared input"
                )
        self.graph.add(unit.name, unit, depends_on=internal)
        return self

    def consumers_of(self, external: str) -> set[str]:
        return {n for n, u in self.graph.nodes.items() if external in u.inputs()}
