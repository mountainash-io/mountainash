import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from mountainash.pipelines.core.result import StepMetadata, StepResult
from mountainash.pipelines.storage.memory import MemoryPipelineStorage
from mountainash.pipelines.storage.filesystem import FileSystemPipelineStorage
from mountainash.pipelines.storage.dual import DualPipelineStorage


def _make_result(step_name: str = "test", data: list | None = None, cache_key: str = "key1") -> StepResult:
    return StepResult(
        data=data or [{"id": 1}],
        metadata=StepMetadata(step_name=step_name, completed_at=datetime.now(), record_count=1),
        cache_key=cache_key,
    )


class TestMemoryStorage:
    def test_write_and_read(self):
        storage = MemoryPipelineStorage()
        result = _make_result()
        storage.write_step_output("test", result)
        retrieved = storage.read_step_output("test", "key1")
        assert retrieved is not None
        assert retrieved.data == [{"id": 1}]

    def test_read_missing(self):
        storage = MemoryPipelineStorage()
        assert storage.read_step_output("test", "nonexistent") is None

    def test_is_fresh_no_ttl(self):
        storage = MemoryPipelineStorage()
        result = _make_result()
        storage.write_step_output("test", result)
        assert storage.is_fresh("test", "key1") is True

    def test_is_fresh_within_ttl(self):
        storage = MemoryPipelineStorage()
        result = _make_result()
        storage.write_step_output("test", result)
        assert storage.is_fresh("test", "key1", max_age=timedelta(hours=1)) is True

    def test_is_fresh_expired(self):
        storage = MemoryPipelineStorage()
        old_meta = StepMetadata(
            step_name="test",
            completed_at=datetime.now() - timedelta(hours=2),
        )
        result = StepResult(data=[], metadata=old_meta, cache_key="key1")
        storage.write_step_output("test", result)
        assert storage.is_fresh("test", "key1", max_age=timedelta(hours=1)) is False

    def test_different_cache_keys_coexist(self):
        storage = MemoryPipelineStorage()
        storage.write_step_output("test", _make_result(data=[{"v": 1}], cache_key="k1"))
        storage.write_step_output("test", _make_result(data=[{"v": 2}], cache_key="k2"))
        r1 = storage.read_step_output("test", "k1")
        r2 = storage.read_step_output("test", "k2")
        assert r1.data == [{"v": 1}]
        assert r2.data == [{"v": 2}]


class TestFileSystemStorage:
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileSystemPipelineStorage(base_path=Path(tmpdir))
            result = _make_result()
            storage.write_step_output("test", result)
            retrieved = storage.read_step_output("test", "key1")
            assert retrieved is not None
            assert retrieved.data == [{"id": 1}]

    def test_read_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileSystemPipelineStorage(base_path=Path(tmpdir))
            assert storage.read_step_output("test", "nonexistent") is None

    def test_creates_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileSystemPipelineStorage(base_path=Path(tmpdir))
            storage.write_step_output("my_step", _make_result(step_name="my_step"))
            assert (Path(tmpdir) / "my_step").is_dir()


class TestDualStorage:
    def test_reads_from_memory_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = MemoryPipelineStorage()
            fs = FileSystemPipelineStorage(base_path=Path(tmpdir))
            dual = DualPipelineStorage(memory=mem, filesystem=fs)

            result = _make_result()
            dual.write_step_output("test", result)

            retrieved = dual.read_step_output("test", "key1")
            assert retrieved is not None
            assert retrieved.data == [{"id": 1}]

    def test_falls_back_to_filesystem(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = FileSystemPipelineStorage(base_path=Path(tmpdir))
            fs.write_step_output("test", _make_result())

            mem = MemoryPipelineStorage()
            dual = DualPipelineStorage(memory=mem, filesystem=fs)

            retrieved = dual.read_step_output("test", "key1")
            assert retrieved is not None
