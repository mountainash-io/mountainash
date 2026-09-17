"""Closed-by-default guards for the declaration protocol (spec rev 3, §7)."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType

import pytest

from mountainash.core.capabilities import bootstrap
from mountainash.core.capabilities.bootstrap import discover_declaration_modules
from mountainash.core.capabilities.declarations import QualifiedCapabilityKey


def test_loaded_segments_have_unique_qualified_capability_keys():
    segments = bootstrap._load_segments()
    keys = [
        QualifiedCapabilityKey(segment.scope, assertion.key)
        for segment in segments for assertion in segment.segment.capabilities
    ]
    assert len(keys) == len(set(keys))


def test_discovered_leaf_without_segment_fails_loading(monkeypatch):
    root = "mountainash.expressions.backends.capabilities"
    name = root + ".ibis.family.substrait.string"

    with TemporaryDirectory() as directory:
        root_path = Path(directory, "capabilities")
        package = root_path
        for part in name.removeprefix(root + ".").split(".")[:-1]:
            package /= part
            package.mkdir(parents=True, exist_ok=True)
            (package / "__init__.py").touch()
        (package / "string.py").write_text("# No authored segment.\n")

        temporary_root = ModuleType(root)
        temporary_root.__path__ = (str(root_path),)
        for module_name in tuple(sys.modules):
            if module_name.startswith(root + "."):
                monkeypatch.delitem(sys.modules, module_name)
        monkeypatch.setitem(sys.modules, root, temporary_root)
        monkeypatch.setattr(bootstrap, "_ROOTS", (root,))
        monkeypatch.setattr(bootstrap, "discover_declaration_modules", lambda: (name,))
        try:
            with pytest.raises(TypeError, match="SEGMENT"):
                bootstrap._load_segments()
        finally:
            for module_name in tuple(sys.modules):
                if module_name == root or module_name.startswith(root + "."):
                    sys.modules.pop(module_name)


_SUBPROCESS_PRELUDE = """
import sys

class _Block:
    def __init__(self, names): self.names = names
    def find_spec(self, fullname, path=None, target=None):
        # Modern meta-path hook (find_module/load_module were removed in 3.12);
        # raising here surfaces as the import's ModuleNotFoundError.
        if fullname.split(".")[0] in self.names:
            raise ModuleNotFoundError(f"blocked optional backend: {fullname}")
        return None

sys.meta_path.insert(0, _Block({"ibis", "narwhals"}))
"""


def test_import_safety_without_optional_backends():
    code = _SUBPROCESS_PRELUDE + textwrap.dedent("""
        from mountainash.core.capabilities.bootstrap import (
            discover_declaration_modules,
        )
        import importlib
        total = 0
        for name in discover_declaration_modules():
            module = importlib.import_module(name)
            total += len(module.SEGMENT.capabilities)
        print("OK", total)
    """)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
    assert out.returncode == 0, out.stderr
    assert out.stdout.startswith("OK "), out.stdout


def test_no_registration_side_effects_on_import():
    code = textwrap.dedent("""
        import importlib
        from mountainash.core.capabilities.bootstrap import (
            discover_declaration_modules,
        )
        from mountainash.core.capabilities.registry import CapabilityRegistry
        for name in discover_declaration_modules():
            importlib.import_module(name)
        state = CapabilityRegistry.snapshot()
        assert not state.facts, "import side-effect registration"
        assert not state.value_class_facts
        assert not state.predicate_facts
        assert not state.kinds
        print("OK")
    """)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
    assert out.returncode == 0, out.stderr


