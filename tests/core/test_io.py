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
        # Regression: these schemes were misclassified as local under the old
        # prefix-list fallback (which omitted them), so remote SSH/SFTP/FTP
        # resources were routed to a local Path read that always failed.
        # Locked in here.
        ("sftp://host/key.csv", True),
        ("ssh://host/key.csv", True),
        ("ftp://host/key.csv", True),
    ],
)
def test_is_remote(path: str, expected: bool) -> None:
    assert is_remote(path) is expected


def test_facade_read_bytes_dispatches_via_facade(monkeypatch):
    """Verify facade_read_bytes calls StorageFacade.from_path().read()."""
    import sys
    import types

    from_path_calls: list[str] = []
    read_calls: list[str] = []

    class FakeFacade:
        def read(self, path: str) -> bytes:
            read_calls.append(path)
            return b"fake-data"

        @staticmethod
        def from_path(path):
            from_path_calls.append(path)
            return FakeFacade()

    # Build a fake module hierarchy so the lazy import inside facade_read_bytes
    # resolves the transport facade without importing the real package.
    fake_top = types.ModuleType("mountainash_transport")
    fake_storage = types.ModuleType("mountainash_transport.storage")
    fake_facade_pkg = types.ModuleType("mountainash_transport.storage.facade")
    fake_facade_mod = types.ModuleType("mountainash_transport.storage.facade.facade")
    fake_facade_mod.StorageFacade = FakeFacade  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "mountainash_transport", fake_top)
    monkeypatch.setitem(sys.modules, "mountainash_transport.storage", fake_storage)
    monkeypatch.setitem(
        sys.modules, "mountainash_transport.storage.facade", fake_facade_pkg
    )
    monkeypatch.setitem(
        sys.modules,
        "mountainash_transport.storage.facade.facade",
        fake_facade_mod,
    )

    from mountainash.core.io import facade_read_bytes

    result = facade_read_bytes("s3://bucket/test.csv")
    assert result == b"fake-data"
    assert from_path_calls == ["s3://bucket/test.csv"]
    assert read_calls == ["s3://bucket/test.csv"]


def test_facade_read_bytes_missing_package(monkeypatch):
    """When mountainash_transport is not installed, raise descriptive ImportError."""
    import builtins

    original_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name.startswith("mountainash_transport"):
            raise ImportError("mocked missing package")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    from mountainash.core.io import facade_read_bytes

    with pytest.raises(ImportError, match="storage.*extra"):
        facade_read_bytes("s3://bucket/test.csv")
