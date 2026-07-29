"""Schema-level tests for the capability spine fact types."""
from datetime import date

import pytest

from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    DivergenceFact,
    DivergenceKind,
    Enforcement,
    GapKind,
    KnownGap,
    ValueClass,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def _fact(**overrides):
    base = dict(
        operation_key=FK_STR.LPAD,
        param="characters",
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.POLARS,
        message="Polars str.lpad() requires a single literal fill character",
        workaround="Use a literal single-character string",
        since="2026-07-05",
    )
    base.update(overrides)
    return CapabilityFact(**base)


class TestCapabilityFact:
    def test_frozen_and_defaults(self):
        f = _fact()
        assert f.dialect is None
        assert f.boundary is Boundary.BUILD
        assert f.native_errors == ()
        assert f.condition is None
        assert f.probe_exempt is None
        assert f.upstream_ref is None
        assert f.fidelity is None
        with pytest.raises(AttributeError):
            f.level = CapabilityLevel.UNSUPPORTED  # frozen

    def test_wildcard_param_constant(self):
        assert WILDCARD_PARAM == "*"
        f = _fact(param=WILDCARD_PARAM, level=CapabilityLevel.UNSUPPORTED)
        assert f.param == "*"

    def test_since_format_validated(self):
        with pytest.raises(ValueError, match="since"):
            _fact(since="July 2026")
        _fact(since="2026-07-05")  # valid — no raise

    def test_materialize_requires_native_errors(self):
        with pytest.raises(ValueError, match="native_errors"):
            _fact(enforcement=Enforcement.MATERIALIZE_RESIDUE, boundary=Boundary.MATERIALIZE)
        _fact(enforcement=Enforcement.MATERIALIZE_RESIDUE, boundary=Boundary.MATERIALIZE, native_errors=(TypeError,))  # ok

    def test_expr_capable_only_as_dialect_refinement(self):
        # Explicit EXPR_CAPABLE is only legal dialect-scoped (spec Section 1)
        with pytest.raises(ValueError, match="dialect"):
            _fact(level=CapabilityLevel.EXPR_CAPABLE)
        _fact(level=CapabilityLevel.EXPR_CAPABLE, dialect="narwhals-polars",
              backend=CONST_BACKEND.NARWHALS)  # ok


class TestKnownGap:
    def test_since_required_and_validated(self):
        with pytest.raises(ValueError, match="since"):
            KnownGap(gap_kind=GapKind.ASPIRATIONAL, reason="not wired", since="bad")
        g = KnownGap(gap_kind=GapKind.ASPIRATIONAL, reason="not wired", since="2026-05-12")
        assert g.reason == "not wired"

    def test_is_stale(self):
        old = KnownGap(gap_kind=GapKind.ASPIRATIONAL, reason="r", since="2025-01-01")
        new = KnownGap(gap_kind=GapKind.ASPIRATIONAL, reason="r",
                       since=date.today().isoformat())
        assert old.is_stale(today=date.today())
        assert not new.is_stale(today=date.today())


class TestDivergenceFact:
    def test_construction(self):
        d = DivergenceFact(
            id="IB-CAST-01",
            kind=DivergenceKind.PRECISION,
            operation_keys=(FK_STR.LPAD,),
            backends=("ibis-duckdb",),
            summary="DuckDB banker's rounding on cast",
            impact="cast(int) rounds half-to-even",
            since="2026-07-05",
        )
        assert d.id == "IB-CAST-01"

    def test_id_grammar_validated(self):
        with pytest.raises(ValueError, match="id"):
            DivergenceFact(
                id="not a valid id", kind=DivergenceKind.SEMANTICS,
                operation_keys=(), backends=("polars",),
                summary="s", impact="i", since="2026-07-05",
            )


def test_value_class_and_option_value_are_mutually_exclusive():
    with pytest.raises(ValueError, match="exactly one"):
        _fact(option_value="2d", value_class=ValueClass.DURATION_MULTIPLIER)

def test_value_class_fact_rejects_wildcard_param():
    with pytest.raises(ValueError, match="value-class"):
        _fact(param=WILDCARD_PARAM, value_class=ValueClass.DURATION_MULTIPLIER)

def test_value_class_fact_rejects_materialize_boundary():
    with pytest.raises(ValueError, match="value-class"):
        _fact(enforcement=Enforcement.MATERIALIZE_RESIDUE, value_class=ValueClass.DURATION_MULTIPLIER, boundary=Boundary.MATERIALIZE,
              native_errors=(ValueError,))

def test_value_class_fact_valid_shape_constructs():
    f = _fact(value_class=ValueClass.DURATION_MULTIPLIER)
    assert f.value_class is ValueClass.DURATION_MULTIPLIER
    assert f.option_value is None

