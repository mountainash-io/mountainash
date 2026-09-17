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
        _fact(
            enforcement=Enforcement.MATERIALIZE_RESIDUE, boundary=Boundary.MATERIALIZE, native_errors=(TypeError,)
        )  # ok

    def test_expr_capable_only_as_dialect_refinement(self):
        # Explicit EXPR_CAPABLE is only legal dialect-scoped (spec Section 1)
        with pytest.raises(ValueError, match="dialect"):
            _fact(level=CapabilityLevel.EXPR_CAPABLE)
        _fact(level=CapabilityLevel.EXPR_CAPABLE, dialect="narwhals-polars", backend=CONST_BACKEND.NARWHALS)  # ok


class TestKnownGap:
    def test_since_required_and_validated(self):
        with pytest.raises(ValueError, match="since"):
            KnownGap(gap_kind=GapKind.ASPIRATIONAL, reason="not wired", since="bad")
        g = KnownGap(gap_kind=GapKind.ASPIRATIONAL, reason="not wired", since="2026-05-12")
        assert g.reason == "not wired"

    def test_is_stale(self):
        old = KnownGap(gap_kind=GapKind.ASPIRATIONAL, reason="r", since="2025-01-01")
        new = KnownGap(gap_kind=GapKind.ASPIRATIONAL, reason="r", since=date.today().isoformat())
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
                id="not a valid id",
                kind=DivergenceKind.SEMANTICS,
                operation_keys=(),
                backends=("polars",),
                summary="s",
                impact="i",
                since="2026-07-05",
            )


def test_value_class_and_option_value_are_mutually_exclusive():
    with pytest.raises(ValueError, match="exactly one"):
        _fact(option_value="2d", value_class=ValueClass.DURATION_MULTIPLIER)


def test_value_class_fact_rejects_wildcard_param():
    with pytest.raises(ValueError, match="value-class"):
        _fact(param=WILDCARD_PARAM, value_class=ValueClass.DURATION_MULTIPLIER)


def test_value_class_fact_rejects_materialize_boundary():
    with pytest.raises(ValueError, match="value-class"):
        _fact(
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            value_class=ValueClass.DURATION_MULTIPLIER,
            boundary=Boundary.MATERIALIZE,
            native_errors=(ValueError,),
        )


def test_value_class_fact_valid_shape_constructs():
    f = _fact(value_class=ValueClass.DURATION_MULTIPLIER)
    assert f.value_class is ValueClass.DURATION_MULTIPLIER
    assert f.option_value is None


def test_gate_wildcard_literal_only_rejected():
    # A whole-op (WILDCARD) LITERAL_ONLY arg-fact means "every argument is literal-only",
    # which by arguments-vs-options.md must be an option, not an argument — so it is illegal.
    with pytest.raises(ValueError, match="WILDCARD"):
        CapabilityFact(
            operation_key=FK_STR.SWAPCASE,
            param=WILDCARD_PARAM,
            level=CapabilityLevel.LITERAL_ONLY,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-duckdb",
            message="x",
            since="2026-07-29",
        )


def test_gate_wildcard_literal_only_rejected_even_with_probe_exempt():
    # probe_exempt must NOT open an escape hatch: LITERAL_ONLY at the whole-op level is
    # illegal regardless of whether the fact carries a probe exemption.
    with pytest.raises(ValueError, match="WILDCARD"):
        CapabilityFact(
            operation_key=FK_STR.SWAPCASE,
            param=WILDCARD_PARAM,
            level=CapabilityLevel.LITERAL_ONLY,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-duckdb",
            message="x",
            since="2026-07-29",
            probe_exempt="whole-op gate",
        )


def test_gate_wildcard_unsupported_ok():
    CapabilityFact(
        operation_key=FK_STR.SWAPCASE,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect=None,
        message="x",
        since="2026-07-29",
    )  # no raise


def test_gate_wildcard_polymorphic_ok():
    # Whole-op POLYMORPHIC declaration (the established COLLECT_VALUES / capabilities/polymorphic.py
    # pattern): every argument is literal-or-expression. Legal, and probe-exempt by design.
    CapabilityFact(
        operation_key=FK_STR.SWAPCASE,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.POLYMORPHIC,
        backend=CONST_BACKEND.IBIS,
        dialect=None,
        message="x",
        since="2026-07-29",
        probe_exempt="polymorphic — both paths supported by design",
    )  # no raise


def test_capture_values_preserve_typed_distinctions_and_canonical_order():
    from mountainash.core.capabilities.schema import CaptureValue, Scenario

    capture = CaptureValue.of
    assert capture(True) != capture(1)
    assert capture(-0.0) != capture(0.0)
    assert capture(float("nan")) == capture(float("nan"))
    assert capture({"b": 2, "a": 1}) == capture({"a": 1, "b": 2})
    assert capture({1, 2}) == capture({2, 1})
    assert capture((1, 2)) != capture((2, 1))
    assert Scenario() != Scenario(options=(("x", capture(None)),))
    assert Scenario(options=(("b", capture(2)), ("a", capture(1)))) == Scenario(
        options=(("a", capture(1)), ("b", capture(2)))
    )
    with pytest.raises(ValueError, match="duplicate"):
        Scenario(options=(("x", capture(1)), ("x", capture(2))))


def test_capture_values_detach_from_mutable_inputs_and_reject_opaque_objects():
    from mountainash.core.capabilities.schema import CaptureValue

    original = {"values": [1, 2]}
    captured = CaptureValue.of(original)
    original["values"].append(3)
    assert captured == CaptureValue.of({"values": [1, 2]})
    with pytest.raises(TypeError):
        CaptureValue.of(object())


def test_targets_resolve_public_authorities_and_canonical_homes():
    from mountainash.core.capabilities.declarations import Domain, FactSource
    from mountainash.core.capabilities.schema import (
        CallableRef,
        CompositionTarget,
        EntrypointStage,
        EntrypointStageTarget,
        OperationTarget,
        ProtocolMethodTarget,
        TargetSurface,
        target_home,
        target_order_key,
    )
    from mountainash.expressions.core.expression_api import entrypoints
    from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
        SubstraitScalarStringExpressionSystemProtocol,
    )
    from mountainash.relations.core.relation_api import relation as relation_api
    from mountainash.relations.core.relation_protocols import RelationAPIProtocol

    entrypoint_alias = CallableRef("mountainash.expressions.core.expression_api", "col")
    entrypoint_definition = CallableRef(entrypoints.col.__module__, entrypoints.col.__qualname__)
    assert entrypoint_alias == entrypoint_definition
    assert CallableRef("mountainash", "col") == entrypoint_definition
    assert CallableRef("mountainash.expressions", "col") == entrypoint_definition
    relation_definition = CallableRef(relation_api.__module__, relation_api.__qualname__)
    assert CallableRef("mountainash", "relation") == relation_definition
    assert CallableRef("mountainash.relations", "relation") == relation_definition

    operation = OperationTarget(FK_STR.LPAD)
    composition = CompositionTarget(
        TargetSurface.EXPRESSION,
        CallableRef(entrypoints.coalesce.__module__, entrypoints.coalesce.__qualname__),
        (FK_STR.LPAD,),
    )
    protocol = ProtocolMethodTarget(
        CallableRef(
            SubstraitScalarStringExpressionSystemProtocol.__module__,
            SubstraitScalarStringExpressionSystemProtocol.__qualname__,
        ),
        "lpad",
    )
    entrypoint = EntrypointStageTarget(
        TargetSurface.RELATION,
        CallableRef(relation_api.__module__, relation_api.__qualname__),
        EntrypointStage.CONSTRUCTION,
    )

    assert target_home(operation) == ("expressions", FactSource.SUBSTRAIT, Domain.STRING)
    assert target_home(protocol) == ("expressions", FactSource.SUBSTRAIT, Domain.STRING)
    assert target_home(composition) == ("expressions", FactSource.MOUNTAINASH, Domain.VALUE)
    assert target_home(entrypoint) == ("relations", FactSource.MOUNTAINASH, Domain.RELATION)

    unmapped_protocol = ProtocolMethodTarget(
        CallableRef(RelationAPIProtocol.__module__, RelationAPIProtocol.__qualname__),
        "collect",
    )
    assert target_home(unmapped_protocol) == (
        "relations",
        FactSource.MOUNTAINASH,
        Domain.RELATION,
    )
    assert target_order_key(composition) == (
        "composition",
        "expression",
        (entrypoints.coalesce.__module__, entrypoints.coalesce.__qualname__),
        ((type(FK_STR.LPAD).__module__, type(FK_STR.LPAD).__qualname__, "LPAD"),),
    )


def test_targets_reject_unknown_references_and_wrong_surface():
    from enum import Enum

    from mountainash.core.capabilities.schema import (
        CallableRef,
        EntrypointStage,
        EntrypointStageTarget,
        OperationTarget,
        TargetSurface,
    )
    from mountainash.relations.core.relation_api import relation as relation_api

    class UnknownOperation(Enum):
        VALUE = "value"

    with pytest.raises(ValueError, match="unknown callable reference"):
        CallableRef("os", "system")
    with pytest.raises(ValueError, match="operation"):
        OperationTarget(UnknownOperation.VALUE)
    with pytest.raises(ValueError, match="surface"):
        EntrypointStageTarget(
            TargetSurface.EXPRESSION,
            CallableRef(relation_api.__module__, relation_api.__qualname__),
            EntrypointStage.CONSTRUCTION,
        )


def test_capture_values_validate_enum_authorities_and_input_data_references():
    from enum import Enum

    from mountainash.core.capabilities.schema import CaptureValue, InputDataRef, Scenario

    class UnknownEnum(Enum):
        VALUE = "value"

    data = InputDataRef("sha256:" + "0" * 64, "cases/simple")
    captured = CaptureValue.of(data)
    assert captured == CaptureValue("input_data", data)
    with pytest.raises(AttributeError):
        data.entry = "other"

    canonical = CaptureValue.of(FK_STR.LPAD)
    assert canonical == CaptureValue(
        "enum",
        (type(FK_STR.LPAD).__module__, type(FK_STR.LPAD).__qualname__, "LPAD"),
    )
    with pytest.raises(ValueError, match="unknown enum"):
        CaptureValue.of(UnknownEnum.VALUE)
    with pytest.raises(ValueError, match="unknown enum"):
        CaptureValue("enum", (UnknownEnum.__module__, UnknownEnum.__qualname__, "VALUE"))
    with pytest.raises(ValueError, match="noncanonical float"):
        CaptureValue("float", "+0x0.0p+0")

    assert Scenario(options=(("x", captured),)) < Scenario(arguments=(("x", captured),))


def test_capture_cast_failure_option_preserves_enum_identity():
    from mountainash import CaseFailureBehaviour
    from mountainash.core.capabilities.schema import CaptureValue

    captured = CaptureValue.of(CaseFailureBehaviour.NULL)
    assert captured == CaptureValue(
        "enum",
        (
            CaseFailureBehaviour.__module__,
            CaseFailureBehaviour.__qualname__,
            "NULL",
        ),
    )
    assert captured != CaptureValue.of(CaseFailureBehaviour.THROW)


def test_external_targets_validate_scenarios_without_importing_optional_backends():
    """A descriptive native-input claim must remain usable in a minimal install."""
    import subprocess
    import sys
    import textwrap

    script = textwrap.dedent(
        """
        import sys

        forbidden = {"ibis", "duckdb", "polars", "narwhals", "pandas", "pyarrow"}
        attempts = []

        class _BlockOptional:
            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] in forbidden:
                    attempts.append(name)
                    raise ModuleNotFoundError("blocked optional backend: " + name)
                return None

        sys.meta_path.insert(0, _BlockOptional())

        from mountainash.core.capabilities.declarations import ManifestationKey
        from mountainash.core.capabilities.schema import (
            CaptureValue,
            EntrypointStage,
            ExternalCallableRef,
            ExternalEntrypointTarget,
            Scenario,
        )

        scenario = Scenario(
            arguments=(("obj", CaptureValue.of({"a": [1]})),),
            options=(
                ("name", CaptureValue.of("native_input")),
                ("schema", CaptureValue.of({"a": "int64"})),
                ("database", CaptureValue.of("main")),
                ("temp", CaptureValue.of(False)),
                ("overwrite", CaptureValue.of(True)),
            ),
        )
        for module in ("ibis.backends.duckdb", "ibis.backends.sqlite"):
            target = ExternalEntrypointTarget(
                ExternalCallableRef(module, "Backend.create_table"),
                EntrypointStage.CONSTRUCTION,
            )
            ManifestationKey(target, scenario)

        assert not attempts, attempts
        assert not any(name.split(".")[0] in forbidden for name in sys.modules)
        """
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, "subprocess failed:\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr


@pytest.mark.parametrize("module", ("ibis.backends.duckdb", "ibis.backends.sqlite"))
def test_external_create_table_scenario_metadata_matches_native_signature(module):
    """A stale authority table cannot silently accept the wrong scenario shape."""
    import importlib
    import inspect

    from mountainash.core.capabilities.declarations import _scenario_authority
    from mountainash.core.capabilities.schema import (
        EntrypointStage,
        ExternalCallableRef,
        ExternalEntrypointTarget,
    )

    target = ExternalEntrypointTarget(
        ExternalCallableRef(module, "Backend.create_table"),
        EntrypointStage.CONSTRUCTION,
    )
    authority_parameters, _ = _scenario_authority(target)
    native = importlib.import_module(module).Backend.create_table
    assert (native.__module__, native.__qualname__) == (
        target.entrypoint.module,
        target.entrypoint.qualname,
    )
    native_parameters = inspect.signature(native).parameters
    assert tuple((name, parameter.kind) for name, parameter in authority_parameters.items()) == tuple(
        (name, parameter.kind) for name, parameter in native_parameters.items() if name != "self"
    )
