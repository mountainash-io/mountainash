from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from mountainash_pipelines.core.result import StepMetadata, StepResult


class FileSystemPipelineStorage:
    def __init__(self, base_path: Path) -> None:
        self._base = base_path

    def _step_dir(self, step_name: str) -> Path:
        return self._base / step_name

    def _data_path(self, step_name: str, cache_key: str) -> Path:
        return self._step_dir(step_name) / f"{cache_key}.json"

    def _meta_path(self, step_name: str, cache_key: str) -> Path:
        return self._step_dir(step_name) / f"{cache_key}.meta.json"

    def write_step_output(self, step_name: str, result: StepResult) -> None:
        step_dir = self._step_dir(step_name)
        step_dir.mkdir(parents=True, exist_ok=True)

        data_path = self._data_path(step_name, result.cache_key)
        data_path.write_text(json.dumps(result.data, default=str), encoding="utf-8")

        meta = {
            "step_name": result.metadata.step_name,
            "completed_at": result.metadata.completed_at.isoformat(),
            "record_count": result.metadata.record_count,
            "cache_key": result.cache_key,
            "input_cache_keys": result.metadata.input_cache_keys,
        }
        meta_path = self._meta_path(step_name, result.cache_key)
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def read_step_output(self, step_name: str, cache_key: str) -> StepResult | None:
        data_path = self._data_path(step_name, cache_key)
        meta_path = self._meta_path(step_name, cache_key)
        if not data_path.exists() or not meta_path.exists():
            return None

        data = json.loads(data_path.read_text(encoding="utf-8"))
        meta_raw = json.loads(meta_path.read_text(encoding="utf-8"))

        metadata = StepMetadata(
            step_name=meta_raw["step_name"],
            completed_at=datetime.fromisoformat(meta_raw["completed_at"]),
            record_count=meta_raw.get("record_count"),
            input_cache_keys=meta_raw.get("input_cache_keys", {}),
        )

        return StepResult(data=data, metadata=metadata, cache_key=cache_key)

    def is_fresh(self, step_name: str, cache_key: str, max_age: timedelta | None = None) -> bool:
        result = self.read_step_output(step_name, cache_key)
        if result is None:
            return False
        if max_age is None:
            return True
        age = datetime.now() - result.metadata.completed_at
        return age <= max_age
