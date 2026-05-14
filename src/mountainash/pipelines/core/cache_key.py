from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any

from mountainash.pipelines.core.capabilities import ResolvedPredicates


def _serialize_for_hash(obj: Any) -> str:
    if obj is None:
        return "null"
    if isinstance(obj, (str, int, float, bool)):
        return json.dumps(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return json.dumps({k: _serialize_for_hash(v) for k, v in sorted(obj.items())})
    if isinstance(obj, (list, tuple)):
        return json.dumps([_serialize_for_hash(v) for v in obj])
    return str(obj)


def compute_cache_key(
    spec_version: str,
    step_name: str,
    upstream_cache_keys: dict[str, str],
    resolved_predicates: ResolvedPredicates,
) -> str:
    parts = [
        spec_version,
        step_name,
        _serialize_for_hash(upstream_cache_keys),
        _serialize_for_hash(resolved_predicates.date_start),
        _serialize_for_hash(resolved_predicates.date_end),
        _serialize_for_hash(resolved_predicates.limit),
        _serialize_for_hash(resolved_predicates.selected_fields),
        # resolution_timestamp is excluded: it records when predicates were resolved
        # but does not affect what data would be fetched, so must not affect the key.
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
