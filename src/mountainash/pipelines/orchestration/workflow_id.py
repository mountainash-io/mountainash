from __future__ import annotations

import hashlib
from typing import Any, TYPE_CHECKING

from mountainash.pipelines.core.cache_key import _serialize_for_hash

if TYPE_CHECKING:
    from mountainash.pipelines.core.capabilities import ResolvedPredicates


def compute_workflow_id(
    pipeline_name: str,
    spec_version: str,
    user_id: str,
    resolved_predicates: ResolvedPredicates,
    config: dict[str, Any],
    target: str | None = None,
) -> str:
    """
    Compute a deterministic workflow ID based on pipeline identity and execution context.

    The workflow ID is a 24-character hex string (SHA256 truncated) that uniquely
    identifies a workflow execution. It includes:
    - Pipeline name and version (specification identity)
    - User ID (execution scope)
    - Resolved predicates (data fetch parameters)
    - Configuration (execution environment)
    - Target step (if running a subgraph)

    Args:
        pipeline_name: Name of the pipeline
        spec_version: Version of the pipeline specification
        user_id: User ID scoping the workflow
        resolved_predicates: Resolved fetch predicates (date range, limit, fields, etc.)
        config: Runtime configuration dictionary
        target: Optional target step name for subgraph execution

    Returns:
        24-character hex string (SHA256 truncated)
    """
    parts = [
        pipeline_name,
        spec_version,
        user_id,
        _serialize_for_hash(resolved_predicates.date_start),
        _serialize_for_hash(resolved_predicates.date_end),
        _serialize_for_hash(resolved_predicates.limit),
        _serialize_for_hash(resolved_predicates.selected_fields),
        _serialize_for_hash(resolved_predicates.resolution_timestamp),
        _serialize_for_hash(config),
        _serialize_for_hash(target),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]
