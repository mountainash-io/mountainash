from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, TYPE_CHECKING

from mountainash.pipelines.core.cache_key import compute_cache_key
from mountainash.pipelines.core.params import resolve_step_params
from mountainash.pipelines.core.policies import EmptyPolicy
from mountainash.pipelines.core.result import StepMetadata, StepResult, infer_record_count
from mountainash.pipelines.core.step import StepContext
# Back-compat: StepEmptyError moved to mountainash.pipelines.errors.
# This alias is permanent enough to survive pickles + external imports;
# do not remove without a deprecation cycle.
from mountainash.pipelines.errors import StepEmptyError  # noqa: F401

if TYPE_CHECKING:
    from mountainash.pipelines.core.spec import PipelineSpec

logger = logging.getLogger(__name__)


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
        self.last_executed: tuple[str, ...] = ()

    def run(
        self,
        params: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
        force: bool = False,
        target: str | None = None,
        step_params: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, StepResult]:
        if target is not None and target not in self._spec.steps:
            raise ValueError(
                f"Target step '{target}' not found in pipeline '{self._spec.name}'"
            )
        merged_config = {**self._config, **(config or {})}

        order = self._spec.topological_order(target=target)
        results: dict[str, StepResult] = {}
        executed: list[str] = []

        for step_name in order:
            defn = self._spec.steps[step_name]

            upstream_keys = {dep: results[dep].cache_key for dep in defn.depends_on}
            effective_params = resolve_step_params(step_name, params, step_params)
            cache_key = compute_cache_key(
                self._spec.version, step_name, upstream_keys, effective_params,
            )

            if not force:
                cached = self._storage.read_step_output(step_name, cache_key)
                if cached is not None and self._storage.is_fresh(step_name, cache_key, defn.cache_ttl):
                    results[step_name] = cached
                    continue

            upstream_data = {dep: results[dep].data for dep in defn.depends_on}
            ctx = StepContext(
                params=effective_params,
                pipeline_storage=self._storage,
                storage_facade=merged_config.get("storage_facade"),
                config=merged_config,
                step_name=step_name,
                workflow_id=None,
                cache_key=cache_key,
            )

            data = defn.fn(ctx, **upstream_data)

            self._check_empty(step_name, data, defn.empty_policy)

            metadata = StepMetadata(
                step_name=step_name,
                completed_at=datetime.now(),
                record_count=infer_record_count(data),
                input_cache_keys=upstream_keys,
                params=effective_params,
            )
            result = StepResult(data=data, metadata=metadata, cache_key=cache_key)
            self._storage.write_step_output(step_name, result)
            results[step_name] = result
            executed.append(step_name)

        self.last_executed = tuple(executed)
        return results

    def as_executor(self) -> _RunnerExecutorAdapter:
        return _RunnerExecutorAdapter(self)

    def _check_empty(self, step_name: str, data: Any, policy: EmptyPolicy) -> None:
        is_empty = (
            (isinstance(data, list) and len(data) == 0)
            or (isinstance(data, dict) and all(
                isinstance(v, list) and len(v) == 0 for v in data.values()
            ))
            or (hasattr(data, "num_rows") and data.num_rows == 0)
        )
        if not is_empty:
            return

        if policy == EmptyPolicy.FAIL:
            raise StepEmptyError(f"Step '{step_name}' returned empty data")
        elif policy == EmptyPolicy.WARN:
            logger.warning("Step '%s' returned empty data", step_name)


class _RunnerExecutorAdapter:
    def __init__(self, runner: SimplePipelineRunner) -> None:
        self._runner = runner

    def execute(
        self,
        pipeline: PipelineSpec,
        step_name: str,
        params: dict[str, Any],
        data_key: str | None,
    ) -> Any:
        import polars as pl

        results = self._runner.run(params=params, target=step_name)
        if step_name not in results:
            raise KeyError(f"Step '{step_name}' not found in pipeline results")
        data = results[step_name].data
        if data_key is not None:
            if not isinstance(data, dict) or data_key not in data:
                raise KeyError(
                    f"data_key '{data_key}' not found in step '{step_name}' output"
                )
            data = data[data_key]
        if isinstance(data, pl.LazyFrame):
            return data
        if isinstance(data, pl.DataFrame):
            return data.lazy()
        if isinstance(data, list) and len(data) == 0:
            return pl.DataFrame().lazy()
        if hasattr(data, "num_rows"):
            return pl.from_arrow(data).lazy()
        from mountainash.pydata.ingress import PydataIngress
        return PydataIngress.convert(data).lazy()
