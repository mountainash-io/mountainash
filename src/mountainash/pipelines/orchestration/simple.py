from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from mountainash_pipelines.core.cache_key import compute_cache_key
from mountainash_pipelines.core.capabilities import PushedPredicates, ResolvedPredicates
from mountainash_pipelines.core.policies import EmptyPolicy
from mountainash_pipelines.core.result import StepMetadata, StepResult
from mountainash_pipelines.core.spec import PipelineSpec
from mountainash_pipelines.core.step import StepContext

logger = logging.getLogger(__name__)


class StepEmptyError(Exception):
    pass


class SimplePipelineRunner:
    def __init__(
        self,
        spec: PipelineSpec,
        storage: Any,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._spec = spec
        self._storage = storage
        self._config = config or {}

    def run(
        self,
        predicates: PushedPredicates | None = None,
        config: dict[str, Any] | None = None,
        force: bool = False,
    ) -> dict[str, StepResult]:
        merged_config = {**self._config, **(config or {})}
        resolved = self._resolve_predicates(predicates)

        order = self._spec.topological_order()
        results: dict[str, StepResult] = {}

        for step_name in order:
            defn = self._spec.steps[step_name]

            upstream_keys = {dep: results[dep].cache_key for dep in defn.depends_on}
            cache_key = compute_cache_key(
                self._spec.version, step_name, upstream_keys, resolved,
            )

            if not force:
                cached = self._storage.read_step_output(step_name, cache_key)
                if cached is not None and self._storage.is_fresh(step_name, cache_key, defn.cache_ttl):
                    results[step_name] = cached
                    continue

            upstream_data = {dep: results[dep].data for dep in defn.depends_on}
            ctx = StepContext(
                predicates=resolved,
                pipeline_storage=self._storage,
                storage_facade=merged_config.get("storage_facade"),
                config=merged_config,
                step_name=step_name,
                workflow_id=None,
            )

            data = defn.fn(ctx, **upstream_data)

            self._check_empty(step_name, data, defn.empty_policy)

            record_count = len(data) if isinstance(data, list) else None
            metadata = StepMetadata(
                step_name=step_name,
                completed_at=datetime.now(),
                record_count=record_count,
                input_cache_keys=upstream_keys,
                resolved_predicates=resolved,
            )
            result = StepResult(data=data, metadata=metadata, cache_key=cache_key)
            self._storage.write_step_output(step_name, result)
            results[step_name] = result

        return results

    def _resolve_predicates(self, pushed: PushedPredicates | None) -> ResolvedPredicates:
        if pushed is None:
            return ResolvedPredicates(resolution_timestamp=datetime.now())
        return ResolvedPredicates(
            date_start=pushed.date_start,
            date_end=pushed.date_end,
            limit=pushed.limit,
            selected_fields=pushed.selected_fields,
            pagination_hint=pushed.pagination_hint,
            resolution_timestamp=datetime.now(),
        )

    def _check_empty(self, step_name: str, data: Any, policy: EmptyPolicy) -> None:
        is_empty = (
            (isinstance(data, list) and len(data) == 0)
            or (isinstance(data, dict) and all(
                isinstance(v, list) and len(v) == 0 for v in data.values()
            ))
        )
        if not is_empty:
            return

        if policy == EmptyPolicy.FAIL:
            raise StepEmptyError(f"Step '{step_name}' returned empty data")
        elif policy == EmptyPolicy.WARN:
            logger.warning("Step '%s' returned empty data", step_name)
