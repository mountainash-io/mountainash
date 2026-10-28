# src/mountainash/pipelines/units/nested.py
from __future__ import annotations
from mountainash.pipelines.core.values import Affinity
from mountainash.pipelines.units.base import BaseUnit


class PipelineUnit(BaseUnit):
    def __init__(self, pipeline, target: str, *, name: str, depends_on=(), version="1") -> None:
        self.pipeline, self.target, self.name, self.depends_on, self.version = (
            pipeline,
            target,
            name,
            tuple(depends_on),
            version,
        )

    @property
    def affinity(self) -> Affinity:
        return (
            Affinity.MAIN
            if any(u.affinity is Affinity.MAIN for u in self.pipeline.graph.nodes.values())
            else Affinity.WORKER
        )

    def reference_exists(
        self, ref
    ) -> bool:  # the outer record holds the inner target's REFERENCE: ask its real owner (F32/P8), recursively
        return self.pipeline.graph.nodes[self.target].reference_exists(ref)

    def run(self, upstream, ctx):  # never called directly; NestedLifecycle drives the inner runner
        raise RuntimeError("PipelineUnit is executed by NestedLifecycle")
