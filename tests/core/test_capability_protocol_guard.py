"""Closed-by-default guards for information/policy declaration modules."""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType

import pytest

from mountainash.core.capabilities import bootstrap
from mountainash.core.capabilities.declarations import QualifiedCapabilityKey, QualifiedInformationKey


def test_loaded_segments_have_unique_qualified_information_and_policy_keys():
    segments = bootstrap._load_segments()
    information = [
        QualifiedInformationKey(segment.scope, record.key, record.layer)
        for segment in segments for record in segment.segment.information
    ]
    policies = [
        QualifiedCapabilityKey(segment.scope, record.key)
        for segment in segments for record in segment.segment.policies
    ]
    assert len(information) == len(set(information))
    assert len(policies) == len(set(policies))


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


def test_import_safety_without_optional_backends():
    code = textwrap.dedent("""
        import importlib
        import sys
        class Block:
            def find_spec(self, fullname, path=None, target=None):
                if fullname.split('.')[0] in {'ibis', 'narwhals'}:
                    raise ModuleNotFoundError('blocked optional backend: ' + fullname)
                return None
        sys.meta_path.insert(0, Block())
        from mountainash.core.capabilities.bootstrap import discover_declaration_modules
        for name in discover_declaration_modules():
            module = importlib.import_module(name)
            assert hasattr(module, 'SEGMENT')
        print('OK')
    """)
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "OK\n"


def test_importing_declarations_has_no_registration_side_effects():
    code = textwrap.dedent("""
        import importlib
        from mountainash.core.capabilities.bootstrap import discover_declaration_modules
        from mountainash.core.capabilities.registry import CapabilityRegistry, _LoadState
        for name in discover_declaration_modules():
            importlib.import_module(name)
        assert CapabilityRegistry.snapshot().load_state is _LoadState.UNINITIALIZED
        print('OK')
    """)
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr
