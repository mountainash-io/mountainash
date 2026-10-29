"""The package advertises ``Typing :: Typed``, so the PEP 561 marker must ship."""
from __future__ import annotations

from importlib.resources import files


def test_py_typed_marker_is_packaged():
    assert (files("mountainash") / "py.typed").is_file()
