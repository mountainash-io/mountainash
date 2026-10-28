import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from mountainash.pipelines.core.result import StepMetadata, StepResult
from mountainash.pipelines.errors import InvalidStorageKeyError
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


class TestFileSystemStoragePathValidation:
    """F-12: step_name / cache_key are joined into cache paths and must not escape the base dir."""

    BAD_NAMES = [
        "..",
        "../escape",
        "..\\escape",
        "a/b",
        "a\\b",
        "/abs",
        "",
        ".",
        "step.name",
        "step\x00",
        "1step",
        "with space",
        "ünïcode",
        "step\n",
    ]

    def test_valid_step_names_unchanged(self, tmp_path):
        storage = FileSystemPipelineStorage(base_path=tmp_path)
        for name in ("fetch", "extract_data", "_private", "Step2"):
            storage.write_step_output(name, _make_result(step_name=name))
            assert (tmp_path / name / "key1.json").is_file()
            assert storage.read_step_output(name, "key1").data == [{"id": 1}]

    def test_hex_digest_cache_keys_unchanged(self, tmp_path):
        from mountainash.pipelines.core.cache_key import compute_cache_key

        key = compute_cache_key("v1", "fetch", {}, None)
        storage = FileSystemPipelineStorage(base_path=tmp_path)
        storage.write_step_output("fetch", _make_result(step_name="fetch", cache_key=key))
        assert (tmp_path / "fetch" / f"{key}.json").is_file()
        assert (tmp_path / "fetch" / f"{key}.meta.json").is_file()
        assert storage.read_step_output("fetch", key) is not None

    @pytest.mark.parametrize("bad", BAD_NAMES)
    def test_write_rejects_bad_step_name(self, tmp_path, bad):
        base = tmp_path / "cache"
        base.mkdir()
        storage = FileSystemPipelineStorage(base_path=base)
        with pytest.raises(InvalidStorageKeyError):
            storage.write_step_output(bad, _make_result())
        assert sorted(p.name for p in tmp_path.rglob("*") if p != base) == []

    @pytest.mark.parametrize("bad", BAD_NAMES)
    def test_read_and_is_fresh_reject_bad_step_name(self, tmp_path, bad):
        storage = FileSystemPipelineStorage(base_path=tmp_path)
        with pytest.raises(InvalidStorageKeyError):
            storage.read_step_output(bad, "key1")
        with pytest.raises(InvalidStorageKeyError):
            storage.is_fresh(bad, "key1")

    @pytest.mark.parametrize("bad", ["../key", "a/b", "a\\b", "", "..", "k.meta", "key\x00", "/abs"])
    def test_rejects_bad_cache_key(self, tmp_path, bad):
        storage = FileSystemPipelineStorage(base_path=tmp_path)
        with pytest.raises(InvalidStorageKeyError):
            storage.write_step_output("fetch", _make_result(cache_key=bad))
        with pytest.raises(InvalidStorageKeyError):
            storage.read_step_output("fetch", bad)

    def test_traversal_does_not_write_outside_base(self, tmp_path):
        base = tmp_path / "cache"
        base.mkdir()
        storage = FileSystemPipelineStorage(base_path=base)
        with pytest.raises(InvalidStorageKeyError):
            storage.write_step_output("../outside", _make_result())
        assert not (tmp_path / "outside").exists()

    def test_error_is_value_error_and_mountainash_error(self):
        from mountainash.core.errors import MountainashError

        assert issubclass(InvalidStorageKeyError, ValueError)
        assert issubclass(InvalidStorageKeyError, MountainashError)

    def test_error_message_names_the_field_and_value(self, tmp_path):
        storage = FileSystemPipelineStorage(base_path=tmp_path)
        with pytest.raises(InvalidStorageKeyError, match=r"step_name.*'\.\./escape'"):
            storage.read_step_output("../escape", "key1")

    def test_dual_storage_rejects_without_caching_in_memory(self, tmp_path):
        mem = MemoryPipelineStorage()
        dual = DualPipelineStorage(memory=mem, filesystem=FileSystemPipelineStorage(base_path=tmp_path))
        with pytest.raises(InvalidStorageKeyError):
            dual.write_step_output("../x", _make_result())
        assert mem.read_step_output("../x", "key1") is None

    def test_rejects_non_string_keys(self, tmp_path):
        storage = FileSystemPipelineStorage(base_path=tmp_path)
        with pytest.raises(InvalidStorageKeyError):
            storage.read_step_output(Path("../x"), "key1")
        with pytest.raises(InvalidStorageKeyError):
            storage.read_step_output("fetch", Path("../x"))

    def test_dual_is_fresh_rejects_bad_step_name(self, tmp_path):
        dual = DualPipelineStorage(
            memory=MemoryPipelineStorage(), filesystem=FileSystemPipelineStorage(base_path=tmp_path)
        )
        with pytest.raises(InvalidStorageKeyError):
            dual.is_fresh("../x", "key1")
