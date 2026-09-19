"""Atomic policy-segment loading and immutable retained generations."""
from __future__ import annotations

import importlib
import sys
import threading
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry, Domain, load_all_capability_declarations
from mountainash.core.capabilities import bootstrap
from mountainash.core.capabilities.declarations import BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.registry import _empty_state, _LoadState
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR

_SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))


def _decl(subject="length", suffix=""):
    return BoundSegment(
        "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.substrait.string" + suffix,
        _SCOPE,
        CapabilitySegment(Domain.STRING, policies=(CapabilityPolicyRule(
            CapabilityKey(FK_STR.CENTER, subject), CapabilityLevel.LITERAL_ONLY,
            "2026-09-18", "test policy", PolicyConsumer.GATE, PolicyAction.BLOCK,
        ),)),
    )


@pytest.fixture(autouse=True)
def registry_isolation():
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.restore(_empty_state())
    try:
        yield
    finally:
        CapabilityRegistry.restore(snapshot)


def test_reset_disables_enumerating_capture():
    CapabilityRegistry.reset()
    assert CapabilityRegistry.capability_for(FK_STR.CENTER, "length", CONST_BACKEND.IBIS, "ibis-duckdb") is None
    with pytest.raises(RuntimeError, match="ISOLATED"):
        load_all_capability_declarations()


def test_segment_publication_keeps_policy_origins_atomic():
    CapabilityRegistry.reset()
    segment = _decl()
    CapabilityRegistry.register_segment(segment)
    before = CapabilityRegistry.snapshot()
    policy = CapabilityRegistry.reader(_SCOPE).policy(segment.segment.policies[0].key)
    assert policy.origins[0].entry == "policies[0]"
    with pytest.raises(ValueError, match="duplicate"):
        CapabilityRegistry.register_segment(segment)
    assert CapabilityRegistry.snapshot() is before
    assert CapabilityRegistry.reader(_SCOPE).policy(segment.segment.policies[0].key) is policy


def test_late_load_failure_keeps_prior_generation_and_original_error(monkeypatch):
    prior = _decl()
    CapabilityRegistry.register_segment(prior)
    late = _decl("character", suffix=".late")
    monkeypatch.setattr(bootstrap, "_load_segments", lambda: (late, prior))
    with pytest.raises(ValueError) as first:
        CapabilityRegistry.capture()
    failed = CapabilityRegistry.snapshot()
    with pytest.raises(ValueError) as again:
        CapabilityRegistry.capture()
    assert again.value is first.value
    CapabilityRegistry.restore(replace(failed, load_state=_LoadState.ISOLATED, load_error=None))
    assert CapabilityRegistry.reader(_SCOPE).policy(prior.segment.policies[0].key).assertion is prior.segment.policies[0]


def test_concurrent_first_readers_observe_one_complete_load(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    declaration = _decl()
    attempts, results = [], []

    def collect():
        attempts.append(True)
        entered.set()
        assert release.wait(10)
        return (declaration,)

    monkeypatch.setattr(bootstrap, "_load_segments", collect)

    def query():
        results.append(CapabilityRegistry.capability_for(FK_STR.CENTER, "length", CONST_BACKEND.IBIS, "ibis-duckdb"))

    threads = [threading.Thread(target=query) for _ in range(2)]
    threads[0].start()
    assert entered.wait(10)
    threads[1].start()
    release.set()
    for thread in threads:
        thread.join(10)
        assert not thread.is_alive()
    assert attempts == [True]
    assert results == [declaration.segment.policies[0].qualify(_SCOPE)] * 2


def test_failed_segment_registration_retains_existing_policy():
    CapabilityRegistry.reset()
    initial = _decl()
    CapabilityRegistry.register_segment(initial)
    duplicate = _decl("length", suffix=".duplicate")
    with pytest.raises(ValueError, match="duplicate"):
        CapabilityRegistry.register_segment(duplicate)
    assert CapabilityRegistry.segments() == (initial,)
    assert CapabilityRegistry.reader(_SCOPE).policy(initial.segment.policies[0].key).assertion is initial.segment.policies[0]


def test_loader_uses_declared_root_source_not_cached_leaf_file(monkeypatch):
    original_module = _decl().module
    original = bootstrap._source_path(original_module).read_bytes()
    root = "mountainash.expressions.backends.capabilities"
    module_name = root + ".ibis.family.substrait.string"
    with TemporaryDirectory() as directory:
        root_path = Path(directory, "capabilities")
        package = root_path
        for part in module_name.removeprefix(root + ".").split(".")[:-1]:
            package /= part
            package.mkdir(parents=True, exist_ok=True)
            (package / "__init__.py").touch()
        source_path = package / "string.py"
        changed = original + b"\nfrom dataclasses import replace\nSEGMENT = replace(SEGMENT, policies=())\n"
        source_path.write_bytes(changed)
        scope_path = root_path / "ibis" / "family" / "_scope.py"
        scope_path.write_text("from mountainash.core.capabilities.identity import FamilyWide, Scope\nfrom mountainash.core.constants import CONST_BACKEND\nSCOPE = Scope(CONST_BACKEND.IBIS, FamilyWide())\n")
        temporary_root = ModuleType(root)
        temporary_root.__path__ = (str(root_path),)
        for name in tuple(sys.modules):
            if name.startswith(root + "."):
                monkeypatch.delitem(sys.modules, name)
        monkeypatch.setitem(sys.modules, root, temporary_root)
        monkeypatch.setattr(bootstrap, "_ROOTS", (root,))
        monkeypatch.setattr(bootstrap, "discover_declaration_modules", lambda: (module_name,))
        try:
            cached = importlib.import_module(module_name)
            monkeypatch.setattr(cached, "__file__", str(Path(directory, "unrelated.py")))
            acquired = bootstrap._load_segments()[0]
        finally:
            for name in tuple(sys.modules):
                if name == root or name.startswith(root + "."):
                    sys.modules.pop(name)
    assert acquired.segment.policies == ()
    assert acquired.source_capture.artifact == changed
