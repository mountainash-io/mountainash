"""Actual execution-target environment acquisition witnesses."""
from __future__ import annotations

import pytest


@pytest.mark.parametrize("engine", ("duckdb", "sqlite"))
def test_actual_driver_coordinates_select_the_registered_policy(engine):
    """A bound Ibis target acquires its engine version from its real driver."""
    from importlib.metadata import version

    import ibis
    import polars as pl
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
    )
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilityKey,
        CapabilityPolicyRule,
        CapabilitySegment,
        Domain,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.policy import _new_execution_context
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING as FK,
    )

    if engine == "duckdb":
        import duckdb

        engine_version = duckdb.__version__
        native_connection_type = duckdb.DuckDBPyConnection
    else:
        import sqlite3

        engine_version = sqlite3.sqlite_version
        native_connection_type = sqlite3.Connection

    connection = getattr(ibis, engine).connect(":memory:")
    before = CapabilityRegistry.snapshot()
    try:
        assert isinstance(connection.con, native_connection_type)
        table = connection.create_table("capability_target", obj=pl.DataFrame({"x": [1]}))
        CapabilityRegistry.reset()
        claim = Applicability((Region((
            CoordinateConstraint(
                "package", "ibis", ComparisonScheme.PEP440,
                equal=version("ibis-framework"),
            ),
            CoordinateConstraint(
                "engine", engine, ComparisonScheme.NUMERIC_RELEASE,
                equal=engine_version,
            ),
        )),))
        rule = CapabilityPolicyRule(
            CapabilityKey(FK.CONTAINS, "substring"), CapabilityLevel.UNSUPPORTED,
            "2026-09-21", "controlled acquisition witness", PolicyConsumer.GATE,
            PolicyAction.BLOCK, applicability=claim,
        )
        dialect = f"ibis-{engine}"
        CapabilityRegistry.register_segment(BoundSegment(
            f"mountainash.expressions.backends.capabilities.ibis.dialects."
            f"ibis_{engine}.substrait.string",
            Scope(CONST_BACKEND.IBIS, Dialect(dialect)),
            CapabilitySegment(Domain.STRING, policies=(rule,)),
        ))

        context = _new_execution_context(table)
        assert context.target.owner is connection
        result = CapabilityRegistry.capability_for(
            FK.CONTAINS, "substring", CONST_BACKEND.IBIS, dialect,
            execution_context=context,
        )

        assert result is not None
        assert result.consumer is PolicyConsumer.GATE
    finally:
        CapabilityRegistry.restore(before)
        connection.con.close()


@pytest.mark.parametrize("engine", ("duckdb", "sqlite"))
def test_same_dialect_bound_connections_keep_distinct_actual_target_owners(engine):
    """Same-dialect Ibis tables must not share an execution target by dialect."""
    import ibis
    import polars as pl
    from mountainash.core.capabilities.policy import _new_execution_context

    first_connection = getattr(ibis, engine).connect(":memory:")
    second_connection = getattr(ibis, engine).connect(":memory:")
    try:
        first = first_connection.create_table("first_target", obj=pl.DataFrame({"x": [1]}))
        second = second_connection.create_table("second_target", obj=pl.DataFrame({"x": [2]}))

        first_context = _new_execution_context(first)
        second_context = _new_execution_context(second)

        assert first_context.target.identity == second_context.target.identity
        assert first_context.target.owner is first_connection
        assert second_context.target.owner is second_connection
        assert first_context.target.owner is not second_context.target.owner
    finally:
        first_connection.con.close()
        second_connection.con.close()


@pytest.mark.parametrize("unbound", (True, False), ids=("unbound-ibis", "bare-override"))
def test_non_native_ibis_targets_have_unknown_engines_and_fresh_owners(unbound):
    """Unbound and override-only Ibis paths never borrow a native engine."""
    import ibis
    from mountainash.core.backend_detection import identify_backend_identity
    from mountainash.core.capabilities.identity import BackendIdentity
    from mountainash.core.capabilities.policy import (
        _engine_version,
        _identify_capability_target,
    )
    from mountainash.core.constants import CONST_BACKEND

    if unbound:
        data = ibis.table({"x": "int64"}, name="unbound_capability_target")
        first = _identify_capability_target(data)
        second = _identify_capability_target(data)
        assert identify_backend_identity(data) == BackendIdentity(CONST_BACKEND.IBIS, None)
    else:
        first = _identify_capability_target(None, family_override=CONST_BACKEND.IBIS)
        second = _identify_capability_target(None, family_override=CONST_BACKEND.IBIS)

    assert first.identity == BackendIdentity(CONST_BACKEND.IBIS, None)
    assert second.identity == BackendIdentity(CONST_BACKEND.IBIS, None)
    assert first.owner is not second.owner
    assert _engine_version(first, "duckdb") is None
    assert _engine_version(first, "sqlite") is None


@pytest.mark.parametrize("selector", (None, "polars"), ids=("override-only", "bare-selector"))
def test_synthetic_polars_target_cannot_borrow_loaded_engine(selector):
    from importlib import import_module

    import_module("polars")
    from mountainash.core.capabilities.policy import _engine_version, _identify_capability_target
    from mountainash.core.constants import CONST_BACKEND

    target = _identify_capability_target(selector, family_override=CONST_BACKEND.POLARS)
    assert _engine_version(target, "polars") is None


def test_actual_polars_frames_retain_their_engine_observation():
    import polars as pl
    from mountainash.core.capabilities.policy import _engine_version, _identify_capability_target

    frame = pl.DataFrame({"x": [1]})
    for native in (frame, frame.lazy()):
        assert _engine_version(_identify_capability_target(native), "polars") == pl.__version__


def test_multibackend_ibis_expression_propagates_native_target_error():
    import ibis
    import polars as pl
    from ibis.common.exceptions import IbisError
    from mountainash.core.capabilities.policy import _new_execution_context

    first = ibis.duckdb.connect(":memory:")
    second = ibis.sqlite.connect(":memory:")
    try:
        left = first.create_table("left_target", obj=pl.DataFrame({"x": [1]}))
        right = second.create_table("right_target", obj=pl.DataFrame({"y": [2]}))
        with pytest.raises(IbisError):
            _new_execution_context(left.cross_join(right))
    finally:
        first.con.close()
        second.con.close()


def test_cold_loading_precedes_driver_requirement_selection(monkeypatch):
    """A first checked request loads declarations before its environment is fixed."""
    import duckdb
    import ibis
    import polars as pl
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities import bootstrap
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
    )
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilityKey,
        CapabilityPolicyRule,
        CapabilitySegment,
        Domain,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.policy import _new_execution_context
    from mountainash.core.capabilities.registry import _empty_state
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING as FK,
    )

    rule = CapabilityPolicyRule(
        CapabilityKey(FK.CONTAINS, "substring"),
        CapabilityLevel.UNSUPPORTED,
        "2026-09-21",
        "cold loading acquisition witness",
        PolicyConsumer.GATE,
        PolicyAction.BLOCK,
        applicability=Applicability((Region((
            CoordinateConstraint(
                "engine",
                "duckdb",
                ComparisonScheme.NUMERIC_RELEASE,
                equal=duckdb.__version__,
            ),
        )),)),
    )
    segment = BoundSegment(
        "mountainash.expressions.backends.capabilities.ibis.dialects."
        "ibis_duckdb.substrait.string.cold_loading",
        Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
        CapabilitySegment(Domain.STRING, policies=(rule,)),
    )
    connection = ibis.duckdb.connect(":memory:")
    before = CapabilityRegistry.snapshot()
    try:
        table = connection.create_table("cold_loading_target", obj=pl.DataFrame({"x": [1]}))
        CapabilityRegistry.restore(_empty_state())
        monkeypatch.setattr(bootstrap, "_load_segments", lambda: (segment,))

        context = _new_execution_context(table)
        selected = CapabilityRegistry.capability_for(
            FK.CONTAINS,
            "substring",
            CONST_BACKEND.IBIS,
            "ibis-duckdb",
            execution_context=context,
        )

        assert selected is not None
        assert selected.message == "cold loading acquisition witness"
    finally:
        CapabilityRegistry.restore(before)
        connection.con.close()


def test_later_setup_registration_requires_a_fresh_context_to_select_new_environment_rule():
    """A completed request keeps its environment while a later request sees setup."""
    import duckdb
    import ibis
    import polars as pl
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
    )
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilityKey,
        CapabilityPolicyRule,
        CapabilitySegment,
        Domain,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.policy import _new_execution_context
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING as FK,
    )

    scope = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))
    initial = CapabilityPolicyRule(
        CapabilityKey(FK.CENTER, "length"),
        CapabilityLevel.UNSUPPORTED,
        "2026-09-21",
        "initial request policy",
        PolicyConsumer.GATE,
        PolicyAction.BLOCK,
    )
    later = CapabilityPolicyRule(
        CapabilityKey(FK.CONTAINS, "substring"),
        CapabilityLevel.UNSUPPORTED,
        "2026-09-21",
        "later setup policy",
        PolicyConsumer.GATE,
        PolicyAction.BLOCK,
        applicability=Applicability((Region((
            CoordinateConstraint(
                "engine",
                "duckdb",
                ComparisonScheme.NUMERIC_RELEASE,
                equal=duckdb.__version__,
            ),
        )),)),
    )
    connection = ibis.duckdb.connect(":memory:")
    before = CapabilityRegistry.snapshot()
    try:
        table = connection.create_table("later_setup_target", obj=pl.DataFrame({"x": [1]}))
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.ibis.dialects."
            "ibis_duckdb.substrait.string.initial_request",
            scope,
            CapabilitySegment(Domain.STRING, policies=(initial,)),
        ))

        first_context = _new_execution_context(table)
        initial_selection = CapabilityRegistry.capability_for(
            FK.CENTER,
            "length",
            CONST_BACKEND.IBIS,
            "ibis-duckdb",
            execution_context=first_context,
        )
        assert initial_selection is not None
        assert initial_selection.message == "initial request policy"

        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.ibis.dialects."
            "ibis_duckdb.substrait.string.later_setup",
            scope,
            CapabilitySegment(Domain.STRING, policies=(later,)),
        ))
        later_context = _new_execution_context(table)

        assert CapabilityRegistry.capability_for(
            FK.CONTAINS,
            "substring",
            CONST_BACKEND.IBIS,
            "ibis-duckdb",
            execution_context=first_context,
        ) is None
        later_selection = CapabilityRegistry.capability_for(
            FK.CONTAINS,
            "substring",
            CONST_BACKEND.IBIS,
            "ibis-duckdb",
            execution_context=later_context,
        )
        assert later_selection is not None
        assert later_selection.message == "later setup policy"
    finally:
        CapabilityRegistry.restore(before)
        connection.con.close()


def test_trusted_policy_needs_no_registry_loading_or_environment_observations():
    """Trusted execution is an honest no-demand context even while isolated."""
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.capabilities.capture import Environment
    from mountainash.core.capabilities.policy import CapabilityPolicy, _new_execution_context
    from mountainash.core.constants import CONST_BACKEND

    before = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        context = _new_execution_context(
            None,
            family_override=CONST_BACKEND.IBIS,
            policy=CapabilityPolicy.trusted(),
        )

        assert context.observations == Environment()
    finally:
        CapabilityRegistry.restore(before)
