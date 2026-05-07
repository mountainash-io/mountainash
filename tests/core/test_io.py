"""Tests for core.io — shared storage helpers."""
from __future__ import annotations

import pytest

from mountainash.core.io import is_remote


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/tmp/data.csv", False),
        ("relative/path.parquet", False),
        ("./local.json", False),
        ("s3://bucket/key.csv", True),
        ("r2://bucket/key.csv", True),
        ("minio://bucket/key.parquet", True),
        ("https://example.com/data.csv", True),
        ("http://example.com/data.json", True),
        ("b2://bucket/key.csv", True),
        ("s3express://bucket/key.csv", True),
    ],
)
def test_is_remote(path: str, expected: bool) -> None:
    assert is_remote(path) is expected


def test_facade_read_bytes_dispatches_via_facade(monkeypatch):
    """Verify facade_read_bytes calls StorageFacade.from_path().read()."""
    import sys
    import types

    calls: list[str] = []

    class FakeFacade:
        def read(self, path: str) -> bytes:
            calls.append(path)
            return b"fake-data"

        @staticmethod
        def from_path(path, auth_params=None):
            return FakeFacade()

    # Build a fake module hierarchy so the lazy import inside facade_read_bytes works
    fake_top = types.ModuleType("mountainash_utils_files")
    fake_sf = types.ModuleType("mountainash_utils_files.storage_facade")
    fake_facade_mod = types.ModuleType("mountainash_utils_files.storage_facade.facade")
    fake_facade_mod.StorageFacade = FakeFacade  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "mountainash_utils_files", fake_top)
    monkeypatch.setitem(sys.modules, "mountainash_utils_files.storage_facade", fake_sf)
    monkeypatch.setitem(sys.modules, "mountainash_utils_files.storage_facade.facade", fake_facade_mod)

    from mountainash.core.io import facade_read_bytes

    result = facade_read_bytes("s3://bucket/test.csv")
    assert result == b"fake-data"
    assert calls == ["s3://bucket/test.csv"]


def test_facade_read_bytes_missing_package(monkeypatch):
    """When mountainash_utils_files is not installed, raise descriptive ImportError."""
    import builtins

    original_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name.startswith("mountainash_utils_files"):
            raise ImportError("mocked missing package")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    from mountainash.core.io import facade_read_bytes

    with pytest.raises(ImportError, match="storage.*extra"):
        facade_read_bytes("s3://bucket/test.csv")
