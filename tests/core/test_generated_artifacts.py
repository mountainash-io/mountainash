from __future__ import annotations

import os
from unittest.mock import Mock

import pytest

from mountainash.core.generated_artifacts import write_text_if_changed


def test_equal_content_is_not_replaced(tmp_path):
    path = tmp_path / "artifact.txt"
    path.write_text("same")
    before = path.stat().st_mtime_ns
    assert write_text_if_changed(path, "same") is False
    assert path.stat().st_mtime_ns == before


def test_changed_content_replaces_destination(tmp_path):
    path = tmp_path / "artifact.txt"
    path.write_text("old")
    assert write_text_if_changed(path, "new") is True
    assert path.read_text() == "new"


def test_replace_failure_keeps_old_destination_and_removes_temp(tmp_path, monkeypatch):
    path = tmp_path / "artifact.txt"
    path.write_text("old")
    monkeypatch.setattr(os, "replace", Mock(side_effect=OSError("replace failed")))
    with pytest.raises(OSError, match="replace failed"):
        write_text_if_changed(path, "new")
    assert path.read_text() == "old"
    assert sorted(tmp_path.iterdir()) == [path]
