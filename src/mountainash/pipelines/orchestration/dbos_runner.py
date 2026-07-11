from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING

from mountainash.pipelines.core.cache_key import compute_cache_key
from mountainash.pipelines.core.params import resolve_step_params
from mountainash.pipelines.core.result import StepMetadata, StepResult, infer_record_count
from mountainash.pipelines.core.step import StepContext
from mountainash.pipelines.orchestration.resolver import _global_registry
from mountainash.pipelines.orchestration.workflow_id import compute_workflow_id

if TYPE_CHECKING:
    from mountainash.pipelines.core.spec import PipelineSpec

try:
    from dbos import DBOS, SetWorkflowID
except ImportError as e:
    raise ImportError(
        "DBOS is required for DbosPipelineRunner. Install with: "
        "uv pip install 'mountainash-pipelines[dbos]'"
    ) from e

logger = logging.getLogger(__name__)


class DbosPipelineRunner:
    """Pipeline runner backed by DBOS durable execution.

    Workflows are identified by a deterministic ID derived from pipeline name,
    version, user, predicates, and config — so re-running with the same inputs
    resumes the existing workflow rather than starting a new one.  Pass
    ``force=True`` to generate a fresh UUID-based workflow ID and bypass
    idempotency.
    """

    def __init__(
        self,
        spec: PipelineSpec,
        storage: Any,
        user_id: str = "default",
        config: dict[str, Any] | None = None,
    ) -> None:
        self._spec = spec
        self._storage = storage
        self._user_id = user_id
        self._config = config or {}

        _global_registry.register(
            spec.name,
            user_id,
            spec=spec,
            storage=storage,
            config=self._config,
        )

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
        resolved_params = params or {}

        if force:
            wf_id = str(uuid.uuid4())
        else:
            wf_id = compute_workflow_id(
                self._spec.name,
                self._spec.version,
                self._user_id,
                resolved_params,
                merged_config,
                target=target,
                step_params=step_params,
            )

        with SetWorkflowID(wf_id):
            return _dbos_run_pipeline(
                spec_name=self._spec.name,
                spec_version=self._spec.version,
                user_id=self._user_id,
                params=resolved_params,
                config=merged_config,
                target=target,
                step_params=step_params,
            )


@DBOS.workflow()
def _dbos_run_pipeline(
    spec_name: str,
    spec_version: str,
    user_id: str,
    params: dict[str, Any],
    config: dict[str, Any],
    target: str | None = None,
    step_params: dict[str, dict[str, Any]] | None = None,
) -> dict[str, StepResult]:
    deps = _global_registry.resolve(spec_name, user_id)
    spec: PipelineSpec = deps["spec"]

    order = spec.topological_order(target=target)
    layers = spec.parallel_layers(order)
    results: dict[str, StepResult] = {}

    for layer in layers:
        for step_name in layer:
            result = _dbos_execute_step(
                spec_name=spec_name,
                user_id=user_id,
                step_name=step_name,
                upstream_cache_keys={
                    dep: results[dep].cache_key
                    for dep in spec.steps[step_name].depends_on
                },
                upstream_data={
                    dep: results[dep].data
                    for dep in spec.steps[step_name].depends_on
                },
                params=params,
                config=config,
                spec_version=spec_version,
                step_params=step_params,
            )
            results[step_name] = result

    return results


@DBOS.step()
def _dbos_execute_step(
    spec_name: str,
    user_id: str,
    step_name: str,
    upstream_cache_keys: dict[str, str],
    upstream_data: dict[str, Any],
    params: dict[str, Any],
    config: dict[str, Any],
    spec_version: str,
    step_params: dict[str, dict[str, Any]] | None = None,
) -> StepResult:
    deps = _global_registry.resolve(spec_name, user_id)
    spec: PipelineSpec = deps["spec"]
    storage = deps["storage"]
    defn = spec.steps[step_name]

    effective_params = resolve_step_params(step_name, params, step_params)
    cache_key = compute_cache_key(
        spec_version, step_name, upstream_cache_keys, effective_params
    )

    cached = storage.read_step_output(step_name, cache_key)
    if cached is not None and storage.is_fresh(step_name, cache_key, defn.cache_ttl):
        return cached

    ctx = StepContext(
        params=effective_params,
        pipeline_storage=storage,
        storage_facade=config.get("storage_facade"),
        config=config,
        step_name=step_name,
        workflow_id=DBOS.workflow_id,
        cache_key=cache_key,
    )

    data = defn.fn(ctx, **upstream_data)

    record_count = infer_record_count(data)
    metadata = StepMetadata(
        step_name=step_name,
        completed_at=datetime.now(),
        record_count=record_count,
        input_cache_keys=upstream_cache_keys,
        params=effective_params,
    )

    result = StepResult(data=data, metadata=metadata, cache_key=cache_key)
    storage.write_step_output(step_name, result)
    return result
