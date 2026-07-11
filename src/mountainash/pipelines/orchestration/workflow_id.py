from __future__ import annotations

import hashlib
from typing import Any

from mountainash.pipelines.core.cache_key import _serialize_for_hash


def compute_workflow_id(
    pipeline_name: str,
    spec_version: str,
    user_id: str,
    params: dict[str, Any] | None,
    config: dict[str, Any],
    target: str | None = None,
    step_params: dict[str, Any] | None = None,
) -> str:
    parts = [
        pipeline_name,
        spec_version,
        user_id,
        _serialize_for_hash(params),
        _serialize_for_hash(config),
        _serialize_for_hash(target),
    ]
    if step_params is not None:
        parts.append(_serialize_for_hash(step_params))
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]
