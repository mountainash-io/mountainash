from __future__ import annotations

from dataclasses import dataclass

from mountainash.graph.algorithms import (
    ancestors as _ancestors,
    parallel_layers as _parallel_layers,
    topological_order as _topo_order,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.pipelines.core.step import StepDefinition


@dataclass(frozen=True)
class PipelineSpec:
    name: str
    version: str
    steps: dict[str, StepDefinition]

    def __post_init__(self) -> None:
        for step_name, defn in self.steps.items():
            for dep in defn.depends_on:
                if dep not in self.steps:
                    raise ValueError(
                        f"Step '{step_name}' depends on '{dep}' which is missing from the pipeline"
                    )

    def _edges(self) -> set[tuple[str, str]]:
        return {(dep, name) for name, defn in self.steps.items() for dep in defn.depends_on}

    def topological_order(self, target: str | None = None) -> list[str]:
        return _topo_order(set(self.steps.keys()), self._edges(), target)

    def parallel_layers(self, order: list[str]) -> list[list[str]]:
        return _parallel_layers(self._edges(), order)

    def ancestors(self, step_name: str) -> set[str]:
        return _ancestors(self._edges(), step_name)
