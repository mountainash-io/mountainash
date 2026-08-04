import pytest
import mountainash as ma
from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.capabilities.schema import CapabilityLevel, Boundary, Enforcement, WILDCARD_PARAM
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST,
)
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL
from tests.fixtures.capability_gating import (
    assert_capability_gated,
    capability_gate,
    identity_for,
    xfail_divergence,
)


class TestIdentityFor:
    def test_declared_dialect(self):
        idn = identity_for("ibis-polars")
        assert idn.family is CONST_BACKEND.IBIS and idn.dialect == "ibis-polars"

    def test_unknown_dialect_keeps_family(self):
        idn = identity_for("narwhals-pyarrow")
        assert idn.family is CONST_BACKEND.NARWHALS and idn.dialect is None

    def test_unresolvable_raises(self):
        with pytest.raises(ValueError, match="cannot resolve backend family"):
            identity_for("totally-unknown")


class TestCapabilityGate:
    def test_returns_gate_build_unsupported(self):
        op = RKEY_MOUNTAINASH_REL["WITH_ROW_INDEX"]
        fact = capability_gate(op, CONST_BACKEND.IBIS, dialect="ibis-polars")
        assert fact and fact.level is CapabilityLevel.UNSUPPORTED
        assert fact.enforcement is Enforcement.GATE and fact.boundary is Boundary.BUILD

    def test_ignores_router_metadata(self):
        op = RKEY_MOUNTAINASH_REL["READ_RESOURCE"]  # UNSUPPORTED but ROUTER_METADATA
        assert capability_gate(op, CONST_BACKEND.POLARS) is None

    def test_none_when_no_fact(self):
        op = RKEY_MOUNTAINASH_REL["WITH_ROW_INDEX"]
        assert capability_gate(op, CONST_BACKEND.IBIS, dialect="ibis-duckdb") is None



class TestAssertCapabilityGated:
    def test_build_gate_requires_correct_raise(self):
        op = RKEY_MOUNTAINASH_REL["WITH_ROW_INDEX"]
        fact = capability_gate(op, CONST_BACKEND.IBIS, dialect="ibis-polars")

        def build():
            raise BackendCapabilityError(
                "x", backend="ibis-polars", function_key=op, limitation=fact
            )

        assert (
            assert_capability_gated(
                op, CONST_BACKEND.IBIS, dialect="ibis-polars", build=build
            )
            is None
        )

    def test_build_gate_rejects_wrong_limitation(self):
        op = RKEY_MOUNTAINASH_REL["WITH_ROW_INDEX"]

        def build():
            raise BackendCapabilityError(
                "x", backend="ibis-polars", function_key=op, limitation=None
            )

        with pytest.raises(AssertionError, match="limitation"):
            assert_capability_gated(
                op, CONST_BACKEND.IBIS, dialect="ibis-polars", build=build
            )

    def test_materialize_residue_real_enrichment(self, backend_factory):
        # list.get(negative) is a MATERIALIZE_RESIDUE fact on narwhals-polars
        # (NW-LIST-04): the enriched BackendCapabilityError is raised at the
        # relation materialization boundary (rel.collect()), chaining the
        # native ValueError. The fact is keyed on param="index", so the gate
        # must be consulted with that param (WILDCARD does not match it).
        df = backend_factory.create({"x": [[1, 2, 3]]}, "narwhals-polars")
        expr = ma.col("x").list.get(-1)  # build succeeds; error is deferred
        assert_capability_gated(
            FKEY_MOUNTAINASH_SCALAR_LIST.GET,
            CONST_BACKEND.NARWHALS,
            dialect="narwhals-polars",
            param="index",
            build=lambda: ma.relation(df).select(expr.name.alias("r")),
            materialize=lambda rel: rel.collect(),  # raises the enriched error
        )

    def test_no_fact_returns_result(self):
        op = RKEY_MOUNTAINASH_REL["WITH_ROW_INDEX"]
        s = object()
        assert (
            assert_capability_gated(
                op, CONST_BACKEND.IBIS, dialect="ibis-duckdb", build=lambda: s
            )
            is s
        )


class TestDivergence:
    def test_applies_mark_for_listed_dialect_backend(self):
        m = xfail_divergence("IB-TYPE-02", backend="ibis-duckdb")
        assert m.name == "xfail"
        assert m.kwargs.get("strict") is True
        assert "IB-TYPE-02" in m.kwargs.get("reason")

    def test_applies_mark_for_family_scoped_backend(self):
        # MA-MATH-01 lists bare family strings ("polars", "narwhals", "ibis");
        # a dialect backend must match via fam = gate_family(backend).value.
        m = xfail_divergence("MA-MATH-01", backend="ibis-duckdb")
        assert m.name == "xfail"
        assert m.kwargs.get("strict") is True

    def test_strict_false_is_forwarded(self):
        m = xfail_divergence("IB-TYPE-02", backend="ibis-duckdb", strict=False)
        assert m.name == "xfail"
        assert m.kwargs.get("strict") is False

    def test_noop_for_unlisted_backend(self):
        m = xfail_divergence("IB-TYPE-02", backend="polars")
        assert m.name == "usefixtures"  # no-op mark
