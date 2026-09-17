"""Atomic registry loading, guarded callbacks, and opaque snapshot behavior."""

from __future__ import annotations

import importlib
import sys
import threading
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType

import pytest

from mountainash.core.capabilities import (
    CapabilityLevel,
    CapabilityRegistry,
    Domain,
    load_all_capability_declarations,
)
from mountainash.core.capabilities import bootstrap
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityAssertion,
    CapabilityKey,
    CapabilitySegment,
)
from mountainash.core.capabilities.identity import FamilyWide, Scope
from mountainash.core.capabilities.registry import _empty_state, _LoadState
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def _decl(*subjects, suffix=""):
    return BoundSegment(
        "mountainash.expressions.backends.capabilities.ibis.family.substrait.string" + suffix,
        Scope(CONST_BACKEND.IBIS, FamilyWide()),
        CapabilitySegment(
            Domain.STRING,
            tuple(
                CapabilityAssertion(
                    CapabilityKey(FK_STR.CENTER, subject),
                    CapabilityLevel.LITERAL_ONLY,
                    "2026-08-07",
                    message="test",
                    probe_exempt="test",
                )
                for subject in (subjects or ("length",))
            ),
        ),
    )


@pytest.fixture(autouse=True)
def registry_isolation():
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.restore(_empty_state())
        yield
    finally:
        CapabilityRegistry.restore(snap)


def test_reset_disables_autoload():
    CapabilityRegistry.reset()
    assert CapabilityRegistry.facts() == []
    with pytest.raises(RuntimeError, match="ISOLATED"):
        load_all_capability_declarations()


def test_segment_publication_keeps_derived_origins_atomic():
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilityAssertion,
        CapabilityKey,
        CapabilitySegment,
    )
    from mountainash.core.capabilities.identity import FamilyWide, Scope

    CapabilityRegistry.reset()
    scope = Scope(CONST_BACKEND.IBIS, FamilyWide())
    assertion = CapabilityAssertion(
        CapabilityKey(FK_STR.CENTER, "length"),
        CapabilityLevel.LITERAL_ONLY,
        "2026-08-07",
        message="test",
    )
    segment = BoundSegment(
        "mountainash.expressions.backends.capabilities.ibis.family.substrait.string",
        scope,
        CapabilitySegment(Domain.STRING, (assertion,)),
    )
    CapabilityRegistry.register_segment(segment)
    before = CapabilityRegistry.snapshot()
    origins = CapabilityRegistry.origins()
    assert tuple(origins.values())[0][0].entry == "capabilities[0]"
    with pytest.raises(ValueError, match="duplicate"):
        CapabilityRegistry.register_segment(segment)
    assert CapabilityRegistry.snapshot() is before
    assert CapabilityRegistry.origins() is origins
    CapabilityRegistry.reset()
    CapabilityRegistry.restore(before)
    assert CapabilityRegistry.origins() is origins


def test_late_load_failure_retains_prior_data_and_original_error(monkeypatch):
    prior = _decl()
    CapabilityRegistry.register_segment(prior)
    late = _decl("character", suffix=".late")
    monkeypatch.setattr(bootstrap, "_load_segments", lambda: (late, prior))
    with pytest.raises(ValueError) as first:
        CapabilityRegistry.facts()
    failed = CapabilityRegistry.snapshot()
    for _ in range(2):
        with pytest.raises(ValueError) as again:
            CapabilityRegistry.facts()
        assert again.value is first.value
    # FAILED intentionally disallows public queries; captured pre-attempt data
    # must remain queryable when explicitly restored as isolated test state.
    CapabilityRegistry.restore(replace(failed, load_state=_LoadState.ISOLATED, load_error=None))
    assert CapabilityRegistry.facts() == list(prior.facts)
    assert CapabilityRegistry.segments() == (prior,)
    CapabilityRegistry.restore(failed)
    with pytest.raises(ValueError) as restored:
        load_all_capability_declarations()
    assert restored.value is first.value


def test_uninitialized_snapshot_retries_after_restore(monkeypatch):
    cold = CapabilityRegistry.snapshot()
    sentinel = RuntimeError("failed load")

    def fail():
        raise sentinel

    monkeypatch.setattr(bootstrap, "_load_segments", fail)
    with pytest.raises(RuntimeError) as error:
        CapabilityRegistry.facts()
    assert error.value is sentinel
    CapabilityRegistry.restore(cold)
    declaration = _decl()
    monkeypatch.setattr(bootstrap, "_load_segments", lambda: (declaration,))
    assert CapabilityRegistry.facts() == list(declaration.facts)


def test_retiring_one_dialect_preserves_other_scope_and_shared_evidence(monkeypatch):
    from mountainash.core.capabilities.capture import CapturedAddress, CapturedAssertion, Environment, EvidenceCapture
    from mountainash.core.capabilities.catalogue import CatalogueQuery, ChangeQuery, EvidenceQuery
    from mountainash.core.capabilities.declarations import QualifiedCapabilityKey
    from mountainash.core.capabilities.identity import Dialect
    from mountainash.core.capabilities.retired import AssertionChange, ChangeDisposition

    cold = CapabilityRegistry.snapshot()
    local = _decl().segment
    segments = tuple(
        BoundSegment(
            f"mountainash.expressions.backends.capabilities.ibis.dialects.{dialect.replace('-', '_')}.substrait.string",
            Scope(CONST_BACKEND.IBIS, Dialect(dialect)),
            local,
        )
        for dialect in ("ibis-duckdb", "ibis-sqlite")
    )
    source = CapturedAddress(
        "mountainash",
        "tests/core/test_capability_load_state.py",
        "dialect lifecycle fixture",
        artifact=Path(__file__).read_bytes(),
    )
    claims = tuple(
        CapturedAssertion(
            "capability",
            QualifiedCapabilityKey(segment.scope, local.capabilities[0].key),
            segment.facts[0],
            replace(source, entry=segment.scope.dialect),
        )
        for segment in segments
    )
    evidence = EvidenceCapture(
        source,
        claims,
        None,
        Environment(),
        (source,),
        "structural",
        ("shared two-dialect observation",),
        (source,),
    )
    monkeypatch.setattr(bootstrap, "_load_segments", lambda: segments)
    before = CapabilityRegistry.capture(evidence=(evidence,))
    prior, unaffected = claims
    change = AssertionChange(
        replace(source, entry="duckdb retirement"),
        prior,
        ChangeDisposition.INCORRECT_DECLARATION,
        "2026-09-17",
        "Retire only the DuckDB fixture claim.",
        evidence_refs=(source,),
    )
    retired = replace(segments[0], segment=replace(local, capabilities=(), changes=(change,)))
    CapabilityRegistry.restore(cold)
    monkeypatch.setattr(bootstrap, "_load_segments", lambda: (retired, segments[1]))
    after = CapabilityRegistry.capture(evidence=(evidence,))

    assert after.get_optional(prior.key) is None
    assert after.get(unaffected.key) == before.get(unaffected.key)
    assert before.get(prior.key) == prior.payload
    assert before.search(CatalogueQuery(changes=ChangeQuery(family="capability"))).changes == ()
    assert after.search(CatalogueQuery(changes=ChangeQuery(prior=prior))).changes == (change,)
    assert after.search(CatalogueQuery(changes=ChangeQuery(prior=unaffected))).changes == ()
    for claim in claims:
        assert after.search(
            CatalogueQuery(scopes=frozenset((claim.key.scope,)), evidence=EvidenceQuery(subject=claim))
        ).evidence == (evidence,)
    assert evidence.subjects == claims


@pytest.mark.parametrize("fails", [False, True])
def test_concurrent_first_readers_observe_one_complete_load(monkeypatch, fails):
    entered, release = threading.Event(), threading.Event()
    declaration = _decl()
    sentinel = RuntimeError("load failure")
    attempts = []

    def collect():
        attempts.append(True)
        entered.set()
        assert release.wait(10)
        if fails:
            raise sentinel
        return (declaration,)

    monkeypatch.setattr(bootstrap, "_load_segments", collect)
    results, errors = [], []

    def query():
        try:
            results.append(CapabilityRegistry.facts())
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=query) for _ in range(2)]
    try:
        threads[0].start()
        assert entered.wait(10)
        threads[1].start()
    finally:
        release.set()
        for thread in threads:
            if thread.ident is not None:
                thread.join(10)
                assert not thread.is_alive()
    assert attempts == [True]
    if fails:
        assert results == []
        assert errors == [sentinel, sentinel]
    else:
        assert errors == []
        assert results == [list(declaration.facts), list(declaration.facts)]


@pytest.mark.parametrize("catch", [False, True])
def test_cold_query_during_iteration_never_loads_or_publishes_failure(monkeypatch, catch):
    def forbidden():
        pytest.fail("guarded cold query attempted declaration loading")

    monkeypatch.setattr(bootstrap, "_load_segments", forbidden)
    fact = _decl().facts[0]

    def incoming():
        if catch:
            with pytest.raises(RuntimeError):
                CapabilityRegistry.facts()
        else:
            CapabilityRegistry.facts()
        yield fact

    if catch:
        CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, incoming())
    else:
        with pytest.raises(RuntimeError):
            CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, incoming())
    state = CapabilityRegistry.snapshot()
    assert state.load_state is _LoadState.UNINITIALIZED
    CapabilityRegistry.restore(replace(state, load_state=_LoadState.ISOLATED))
    assert CapabilityRegistry.facts() == ([fact] if catch else [])


@pytest.mark.parametrize("action", ["reset", "restore", "register_backend", "register_segment", "query"])
def test_first_load_reentrancy_is_rejected(monkeypatch, action):
    snap = CapabilityRegistry.snapshot()

    def collect():
        if action == "reset":
            CapabilityRegistry.reset()
        elif action == "restore":
            CapabilityRegistry.restore(snap)
        elif action == "register_backend":
            CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, ())
        elif action == "register_segment":
            CapabilityRegistry.register_segment(_decl())
        else:
            CapabilityRegistry.facts()
        return ()

    monkeypatch.setattr(bootstrap, "_load_segments", collect)
    with pytest.raises(RuntimeError) as first:
        CapabilityRegistry.facts()
    with pytest.raises(RuntimeError) as second:
        CapabilityRegistry.facts()
    assert second.value is first.value


def test_iterable_can_join_independent_writer_without_losing_its_facts():
    CapabilityRegistry.reset()
    first = _decl().facts[0]
    second = replace(first, param="character")
    errors = []

    def independent():
        try:
            CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, (second,))
        except BaseException as error:
            errors.append(error)

    def incoming():
        thread = threading.Thread(target=independent)
        thread.start()
        thread.join(10)
        assert not thread.is_alive()
        yield first

    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, incoming())
    assert errors == []
    assert CapabilityRegistry.capability_for(FK_STR.CENTER, "length", CONST_BACKEND.IBIS) is first
    assert CapabilityRegistry.capability_for(FK_STR.CENTER, "character", CONST_BACKEND.IBIS) is second


def test_registration_failure_keeps_original_facts_and_declarations():
    CapabilityRegistry.reset()
    prior = _decl()
    CapabilityRegistry.register_segment(prior)
    late = _decl("character", "length", suffix=".late")
    with pytest.raises(ValueError, match="duplicate") as error:
        CapabilityRegistry.register_segment(late)
    assert f"{prior.module}:capabilities[0]" in str(error.value)
    assert f"{late.module}:capabilities[1]" in str(error.value)
    assert CapabilityRegistry.facts() == list(prior.facts)
    assert CapabilityRegistry.segments() == (prior,)


@pytest.mark.parametrize("marker", list(_LoadState))
@pytest.mark.parametrize("enumeration", [False, True])
def test_registration_callback_queries_follow_captured_load_state(marker, enumeration, monkeypatch):
    sentinel = RuntimeError("cached failure")
    state = replace(_empty_state(marker), load_error=sentinel if marker is _LoadState.FAILED else None)
    CapabilityRegistry.restore(state)
    declaration = _decl()

    def incoming():
        query = load_all_capability_declarations if enumeration else CapabilityRegistry.facts
        if marker is _LoadState.FAILED:
            with pytest.raises(RuntimeError) as caught:
                query()
            assert caught.value is sentinel
        elif marker is _LoadState.UNINITIALIZED or (enumeration and marker is _LoadState.ISOLATED):
            with pytest.raises(RuntimeError):
                query()
        elif enumeration:
            assert query() is None
        else:
            assert query() == []
        yield declaration.facts[0]

    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, incoming())
    captured = CapabilityRegistry.snapshot()
    CapabilityRegistry.restore(replace(captured, load_state=_LoadState.ISOLATED, load_error=None))
    assert CapabilityRegistry.facts() == list(declaration.facts)


def test_reader_observes_complete_old_generation_during_preparation(monkeypatch):
    import mountainash.core.capabilities.registry as registry

    CapabilityRegistry.reset()
    old = _decl().facts[0]
    new = replace(old, param="character")
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [old])
    entered, release = threading.Event(), threading.Event()
    prepare = registry._prepare_state
    errors = []

    def blocked_prepare(**kwargs):
        entered.set()
        assert release.wait(10)
        return prepare(**kwargs)

    def writer():
        try:
            CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [new])
        except BaseException as exc:
            errors.append(exc)

    with monkeypatch.context() as patch:
        patch.setattr(registry, "_prepare_state", blocked_prepare)
        thread = threading.Thread(target=writer)
        thread.start()
        try:
            assert entered.wait(10)
            assert CapabilityRegistry.facts() == [old]
            assert CapabilityRegistry.capability_for(FK_STR.CENTER, "character", CONST_BACKEND.IBIS) is None
        finally:
            release.set()
            thread.join(10)
            assert not thread.is_alive()
    assert errors == []
    assert CapabilityRegistry.capability_for(FK_STR.CENTER, "character", CONST_BACKEND.IBIS) is new


def test_released_snapshots_do_not_retain_registry_history():
    import gc
    import weakref

    CapabilityRegistry.reset()
    CapabilityRegistry.register_segment(_decl())
    old = CapabilityRegistry.snapshot()
    reference = weakref.ref(old)
    CapabilityRegistry.reset()
    CapabilityRegistry.restore(old)
    assert CapabilityRegistry.segments() == (_decl(),)
    CapabilityRegistry.reset()
    del old
    gc.collect()
    assert reference() is None


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
        changed = original + b"\nfrom dataclasses import replace\n" + b"SEGMENT = replace(SEGMENT, capabilities=())\n"
        source_path.write_bytes(changed)
        scope_path = root_path / "ibis" / "family" / "_scope.py"
        scope_path.write_text(
            "from mountainash.core.capabilities.identity import FamilyWide, Scope\n"
            "from mountainash.core.constants import CONST_BACKEND\n"
            "SCOPE = Scope(CONST_BACKEND.IBIS, FamilyWide())\n"
        )
        unrelated = Path(directory, "unrelated.py")
        unrelated.write_text("raise RuntimeError('unrelated source executed')\n")

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
            monkeypatch.setattr(cached, "__file__", str(unrelated))
            acquired = bootstrap._load_segments()[0]
        finally:
            for name in tuple(sys.modules):
                if name == root or name.startswith(root + "."):
                    sys.modules.pop(name)

    assert acquired.segment.capabilities == ()
    assert acquired.source_capture.artifact == changed
