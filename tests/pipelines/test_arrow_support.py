from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pytest

from mountainash.pipelines.core.policies import EmptyPolicy
from mountainash.pipelines.core.result import StepMetadata, StepResult
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner, StepEmptyError
from mountainash.pipelines.storage.filesystem import FileSystemPipelineStorage


class TestCheckEmptyArrow:
    def test_empty_arrow_table_fail(self):
        runner = SimplePipelineRunner.__new__(SimplePipelineRunner)
        table = pa.table({"x": pa.array([], type=pa.int64())})
        with pytest.raises(StepEmptyError):
            runner._check_empty("test", table, EmptyPolicy.FAIL)

    def test_nonempty_arrow_table_pass(self):
        runner = SimplePipelineRunner.__new__(SimplePipelineRunner)
        table = pa.table({"x": [1, 2, 3]})
        runner._check_empty("test", table, EmptyPolicy.FAIL)

    def test_empty_arrow_table_warn(self):
        runner = SimplePipelineRunner.__new__(SimplePipelineRunner)
        table = pa.table({"x": pa.array([], type=pa.int64())})
        runner._check_empty("test", table, EmptyPolicy.WARN)

    def test_empty_arrow_table_silent(self):
        runner = SimplePipelineRunner.__new__(SimplePipelineRunner)
        table = pa.table({"x": pa.array([], type=pa.int64())})
        runner._check_empty("test", table, EmptyPolicy.SILENT)


class TestFileSystemStorageArrow:
    def test_arrow_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileSystemPipelineStorage(base_path=Path(tmpdir))
            table = pa.table({"x": [1, 2, 3], "y": ["a", "b", "c"]})
            result = StepResult(
                data=table,
                metadata=StepMetadata(
                    step_name="test",
                    completed_at=datetime.now(),
                    record_count=3,
                ),
                cache_key="arrow_key",
            )
            storage.write_step_output("test", result)
            retrieved = storage.read_step_output("test", "arrow_key")
            assert retrieved is not None
            assert retrieved.data.equals(table)
            assert retrieved.metadata.record_count == 3

    def test_arrow_creates_parquet_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileSystemPipelineStorage(base_path=Path(tmpdir))
            table = pa.table({"x": [1]})
            result = StepResult(
                data=table,
                metadata=StepMetadata(
                    step_name="test",
                    completed_at=datetime.now(),
                    record_count=1,
                ),
                cache_key="pq_key",
            )
            storage.write_step_output("test", result)
            assert (Path(tmpdir) / "test" / "pq_key.parquet").exists()
            assert not (Path(tmpdir) / "test" / "pq_key.json").exists()
