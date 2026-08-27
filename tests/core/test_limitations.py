"""Core limitation-enrichment helper (spec §3.8)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.limitations import (
    MATERIALIZE_BOUNDARY,
    WILDCARD_PARAM,
    call_with_limitation_enrichment,
    enrich_materialization,
)
from mountainash.core.types import BackendCapabilityError

KEY = "op_key"
LIM = CapabilityFact(
    operation_key=KEY,
    param="tolerance",
    level=CapabilityLevel.LITERAL_ONLY,
    backend=CONST_BACKEND.NARWHALS,
    message="known quirk",
    workaround="use polars",
    enforcement=Enforcement.MATERIALIZE_RESIDUE,
    boundary=Boundary.MATERIALIZE,
    native_errors=(NotImplementedError,),
    since="2026-07-05",
)


def _boom():
    raise NotImplementedError("native")


class TestEnrichment:
    def test_named_param_match_enriches(self):
        with pytest.raises(BackendCapabilityError) as exc:
            call_with_limitation_enrichment(
                _boom,
                limitations={(KEY, "tolerance"): LIM},
                backend_name="narwhals",
                operation_key=KEY,
                named_args=("tolerance",),
            )
        assert exc.value.limitation is LIM
        assert exc.value.__cause__.__class__ is NotImplementedError

    def test_wildcard_match_enriches_without_named_args(self):
        with pytest.raises(BackendCapabilityError):
            call_with_limitation_enrichment(
                _boom,
                limitations={(KEY, WILDCARD_PARAM): LIM},
                backend_name="narwhals",
                operation_key=KEY,
                named_args=(),
            )

    def test_no_match_reraises_original(self):
        with pytest.raises(NotImplementedError):
            call_with_limitation_enrichment(
                _boom,
                limitations={("other_key", WILDCARD_PARAM): LIM},
                backend_name="narwhals",
                operation_key=KEY,
                named_args=("x",),
            )

    def test_wrong_error_type_reraises_original(self):
        def type_boom():
            raise TypeError("different")

        with pytest.raises(TypeError):
            call_with_limitation_enrichment(
                type_boom,
                limitations={(KEY, WILDCARD_PARAM): LIM},
                backend_name="narwhals",
                operation_key=KEY,
                named_args=(),
            )

    def test_backend_capability_error_passes_through_unwrapped(self):
        inner = BackendCapabilityError(
            "already enriched", backend="polars", function_key=KEY, limitation=LIM
        )

        def raise_bce():
            raise inner

        with pytest.raises(BackendCapabilityError) as exc:
            call_with_limitation_enrichment(
                raise_bce,
                limitations={(KEY, WILDCARD_PARAM): LIM},
                backend_name="narwhals",
                operation_key=KEY,
                named_args=(),
            )
        assert exc.value is inner  # not re-wrapped

    def test_success_passes_value_through(self):
        out = call_with_limitation_enrichment(
            lambda: 42,
            limitations={},
            backend_name="polars",
            operation_key=KEY,
            named_args=(),
        )
        assert out == 42

    def test_materialize_boundary_sentinel_is_hashable_key(self):
        {(MATERIALIZE_BOUNDARY, WILDCARD_PARAM): LIM}


class _FakeBackend:
    """Minimal backend stub exposing exactly what enrich_materialization
    reads: backend_type (family), dialect, BACKEND_NAME."""

    def __init__(self, backend_type, dialect, backend_name="fake"):
        self.backend_type = backend_type
        self.dialect = dialect
        self.BACKEND_NAME = backend_name


@pytest.fixture
def _two_colliding_residue_facts():
    """Two isolated MATERIALIZE_RESIDUE facts sharing a native_errors type
    on the same backend+dialect -- the exact shape that made NW-LIST-01 vs
    NW-STR-22 ambiguous before the prefer_operation_keys/exactly-one-match
    fix (backlog item 88). Uses two real, otherwise-unrelated string FKEYs
    (registration validates operation_key against a real registered
    operation) that carry no MATERIALIZE_RESIDUE fact of their own today.
    """
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
    )

    key_a, key_b = FK_STR.UPPER, FK_STR.LOWER
    fact_a = CapabilityFact(
        operation_key=key_a, param=WILDCARD_PARAM, level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.NARWHALS, dialect="narwhals-pandas",
        message="a", workaround="use polars", enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE, native_errors=(TypeError,), since="2026-08-13",
    )
    fact_b = CapabilityFact(
        operation_key=key_b, param=WILDCARD_PARAM, level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.NARWHALS, dialect="narwhals-pandas",
        message="b", workaround="use polars", enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE, native_errors=(TypeError,), since="2026-08-13",
    )
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, (fact_a, fact_b))
        yield key_a, key_b
    finally:
        CapabilityRegistry.restore(snap)


class TestEnrichMaterializationPreferOperationKeys:
    """enrich_materialization's prefer_operation_keys param (backlog item 88):
    None = legacy backend-wide; non-None (even empty) is authoritative; a
    raised error is enriched only on an EXACT single match."""

    def _boom_type_error(self):
        raise TypeError("native boom")

    def test_none_with_genuine_ambiguity_raises_raw(self, _two_colliding_residue_facts):
        backend = _FakeBackend(CONST_BACKEND.NARWHALS, "narwhals-pandas")
        with pytest.raises(TypeError, match="native boom"):
            enrich_materialization(backend, self._boom_type_error)

    def test_empty_preferred_set_is_authoritative_no_fallback(self, _two_colliding_residue_facts):
        backend = _FakeBackend(CONST_BACKEND.NARWHALS, "narwhals-pandas")
        with pytest.raises(TypeError, match="native boom"):
            enrich_materialization(
                backend, self._boom_type_error, prefer_operation_keys=frozenset(),
            )

    def test_single_candidate_preferred_set_enriches_correctly(self, _two_colliding_residue_facts):
        backend = _FakeBackend(CONST_BACKEND.NARWHALS, "narwhals-pandas")
        key_a, _key_b = _two_colliding_residue_facts
        with pytest.raises(BackendCapabilityError) as exc:
            enrich_materialization(
                backend, self._boom_type_error, prefer_operation_keys=frozenset({key_a}),
            )
        assert exc.value.function_key == key_a
        assert exc.value.limitation.message == "a"
        assert isinstance(exc.value.__cause__, TypeError)

    def test_matching_key_wrong_exception_type_raises_raw(self, _two_colliding_residue_facts):
        # A structurally-present, correctly-preferred key whose fact
        # requires TypeError must never be force-matched against a
        # different exception type -- prefer_operation_keys narrows
        # candidates, it never overrides the native_errors type check.
        backend = _FakeBackend(CONST_BACKEND.NARWHALS, "narwhals-pandas")
        key_a, _key_b = _two_colliding_residue_facts

        def _boom_value_error():
            raise ValueError("unrelated")

        with pytest.raises(ValueError, match="unrelated"):
            enrich_materialization(
                backend, _boom_value_error, prefer_operation_keys=frozenset({key_a}),
            )

    def test_both_candidates_preferred_still_ambiguous_raises_raw(self, _two_colliding_residue_facts):
        backend = _FakeBackend(CONST_BACKEND.NARWHALS, "narwhals-pandas")
        key_a, key_b = _two_colliding_residue_facts
        with pytest.raises(TypeError, match="native boom"):
            enrich_materialization(
                backend, self._boom_type_error,
                prefer_operation_keys=frozenset({key_a, key_b}),
            )

    def test_nonmatching_preferred_set_raises_raw(self, _two_colliding_residue_facts):
        backend = _FakeBackend(CONST_BACKEND.NARWHALS, "narwhals-pandas")
        with pytest.raises(TypeError, match="native boom"):
            enrich_materialization(
                backend, self._boom_type_error,
                prefer_operation_keys=frozenset({"some_unrelated_op"}),
            )


def test_enrich_materialization_does_not_execute_successful_ibis_table():
    from types import SimpleNamespace

    import ibis

    table = ibis.memtable({"x": [1]})
    backend = SimpleNamespace(
        backend_type=CONST_BACKEND.IBIS,
        dialect=None,
        BACKEND_NAME="ibis",
    )
    trace = SimpleNamespace(records=())
    result = enrich_materialization(
        backend,
        lambda: table,
        diagnostic_trace=trace,
    )
    assert result is table
