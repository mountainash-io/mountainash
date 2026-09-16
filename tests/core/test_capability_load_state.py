"""Atomic registry loading, guarded callbacks, and opaque snapshot behavior."""

from __future__ import annotations

import threading
from dataclasses import replace

import pytest

from mountainash.core.capabilities import (
    CapabilityDeclaration,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Domain,
    FactSource,
    ProbeEvidence,
    load_all_capability_declarations,
)
from mountainash.core.capabilities import bootstrap
from mountainash.core.capabilities.registry import _empty_state, _LoadState
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def _decl():
    return CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS,
        domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=(
            CapabilityFact(
                operation_key=FK_STR.CENTER,
                param="length",
                level=CapabilityLevel.LITERAL_ONLY,
                backend=CONST_BACKEND.IBIS,
                message="test",
                since="2026-08-07",
                probe_exempt="test",
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


def test_empty_declaration_evidence_survives_load_and_restore(monkeypatch):
    empty = replace(
        _decl(),
        facts=(),
        evidence=ProbeEvidence(
            "2026-09-15",
            (("library", "1"),),
            ("empty-bundle",),
        ),
    )
    monkeypatch.setattr(bootstrap, "_load_declarations", lambda: (empty,))
    load_all_capability_declarations()
    assert CapabilityRegistry.declarations() == (empty,)
    snap = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    CapabilityRegistry.restore(snap)
    assert CapabilityRegistry._report_inputs() == ((), (empty,))


def test_late_load_failure_retains_prior_data_and_original_error(monkeypatch):
    prior = _decl()
    CapabilityRegistry.register_declaration(prior)
    late = replace(prior, facts=(replace(prior.facts[0], param="character"),))
    monkeypatch.setattr(bootstrap, "_load_declarations", lambda: (late, prior))
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
    assert CapabilityRegistry.declarations() == (prior,)
    CapabilityRegistry.restore(failed)
    with pytest.raises(ValueError) as restored:
        load_all_capability_declarations()
    assert restored.value is first.value


def test_uninitialized_snapshot_retries_after_restore(monkeypatch):
    cold = CapabilityRegistry.snapshot()
    sentinel = RuntimeError("failed load")

    def fail():
        raise sentinel

    monkeypatch.setattr(bootstrap, "_load_declarations", fail)
    with pytest.raises(RuntimeError) as error:
        CapabilityRegistry.facts()
    assert error.value is sentinel
    CapabilityRegistry.restore(cold)
    declaration = _decl()
    monkeypatch.setattr(bootstrap, "_load_declarations", lambda: (declaration,))
    assert CapabilityRegistry.facts() == list(declaration.facts)


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

    monkeypatch.setattr(bootstrap, "_load_declarations", collect)
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

    monkeypatch.setattr(bootstrap, "_load_declarations", forbidden)
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


@pytest.mark.parametrize("action", ["reset", "restore", "register_backend", "register_declaration", "query"])
def test_first_load_reentrancy_is_rejected(monkeypatch, action):
    snap = CapabilityRegistry.snapshot()

    def collect():
        if action == "reset":
            CapabilityRegistry.reset()
        elif action == "restore":
            CapabilityRegistry.restore(snap)
        elif action == "register_backend":
            CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, ())
        elif action == "register_declaration":
            CapabilityRegistry.register_declaration(_decl())
        else:
            CapabilityRegistry.facts()
        return ()

    monkeypatch.setattr(bootstrap, "_load_declarations", collect)
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
    CapabilityRegistry.register_declaration(prior)
    new = replace(prior.facts[0], param="character")
    with pytest.raises(ValueError, match="duplicate"):
        CapabilityRegistry.register_declaration(replace(prior, facts=(new, prior.facts[0])))
    assert CapabilityRegistry.facts() == list(prior.facts)
    assert CapabilityRegistry.declarations() == (prior,)


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
    CapabilityRegistry.register_declaration(_decl())
    old = CapabilityRegistry.snapshot()
    reference = weakref.ref(old)
    CapabilityRegistry.reset()
    CapabilityRegistry.restore(old)
    assert CapabilityRegistry.declarations() == (_decl(),)
    CapabilityRegistry.reset()
    del old
    gc.collect()
    assert reference() is None
