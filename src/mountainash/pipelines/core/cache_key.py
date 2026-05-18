from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any


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
    params: dict[str, Any] | None,
) -> str:
    parts = [
        spec_version,
        step_name,
        _serialize_for_hash(upstream_cache_keys),
        _serialize_for_hash(params),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
