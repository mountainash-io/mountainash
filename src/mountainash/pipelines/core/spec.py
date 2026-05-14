from __future__ import annotations

from dataclasses import dataclass
from collections import deque

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

    def topological_order(self, target: str | None = None) -> list[str]:
        if target is not None:
            relevant = self.ancestors(target) | {target}
        else:
            relevant = set(self.steps.keys())

        in_degree: dict[str, int] = {name: 0 for name in relevant}
        for name in relevant:
            for dep in self.steps[name].depends_on:
                if dep in relevant:
                    in_degree[name] += 1

        queue: deque[str] = deque(name for name, deg in in_degree.items() if deg == 0)
        order: list[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for name in relevant:
                if node in self.steps[name].depends_on:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)

        if len(order) != len(relevant):
            raise ValueError(
                f"Cycle detected in pipeline '{self.name}': "
                f"could not order {relevant - set(order)}"
            )

        return order

    def parallel_layers(self, order: list[str]) -> list[list[str]]:
        order_set = set(order)
        depth: dict[str, int] = {}

        for name in order:
            deps_in_scope = [d for d in self.steps[name].depends_on if d in order_set]
            if not deps_in_scope:
                depth[name] = 0
            else:
                depth[name] = max(depth[d] for d in deps_in_scope) + 1

        max_depth = max(depth.values()) if depth else 0
        layers: list[list[str]] = [[] for _ in range(max_depth + 1)]
        for name in order:
            layers[depth[name]].append(name)

        return layers

    def ancestors(self, step_name: str) -> set[str]:
        result: set[str] = set()
        queue: deque[str] = deque(self.steps[step_name].depends_on)
        while queue:
            dep = queue.popleft()
            if dep not in result:
                result.add(dep)
                queue.extend(self.steps[dep].depends_on)
        return result
