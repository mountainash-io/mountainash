"""Protocol contract for capability declaration modules (spec rev 3, §1)."""

from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel
from mountainash.core.capabilities.declarations import (
    Domain,
    FactSource,
    ProbeEvidence,
    classify_domain,
    classify_source,
)
from mountainash.core.capabilities import CapabilityRegistry
from mountainash.core.capabilities.predicates import BoundCall
from mountainash.core.capabilities.schema import ClauseOp, Enforcement
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.dtypes.metadata import OperandType
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_CATEGORICAL as FK_CAT,
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
    FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL as FK_GEO,
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT,
    FKEY_MOUNTAINASH_SCALAR_VALUE as FK_VALUE,
    FKEY_SUBSTRAIT_SCALAR_COMPARISON as FK_CMP,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)


def _fact(op, backend, **kw):
    return CapabilityFact(
        operation_key=op,
        param="*",
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        message="t",
        since="2026-08-07",
        probe_exempt="test fact",
        **kw,
    )


def test_classify_source():
    assert classify_source(FK_STR.CENTER) is FactSource.SUBSTRAIT
    assert classify_source(FK_DT.ADD_DAYS) is FactSource.MOUNTAINASH
    assert classify_source(RKEY_MOUNTAINASH_REL.UNNEST) is FactSource.MOUNTAINASH


def test_substrait_relation_keeps_standard_operation_home():
    from mountainash.core.capabilities.schema import OperationTarget, target_home
    from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL

    operation = next(iter(RKEY_SUBSTRAIT_REL))
    assert classify_source(operation) is FactSource.SUBSTRAIT
    assert target_home(OperationTarget(operation)) == ("relations", FactSource.SUBSTRAIT, Domain.RELATION)


@pytest.mark.parametrize(
    "payload",
    [
        {"changes": ({},)},
        {"changes": ("change",)},
        {"evidence_refs": ("unresolved-address",)},
    ],
)
def test_segment_rejects_untyped_history_and_evidence(payload):
    from mountainash.core.capabilities.declarations import CapabilitySegment

    with pytest.raises(TypeError):
        CapabilitySegment(Domain.STRING, **payload)


def test_segment_keeps_type_distinct_predicate_operands():
    from mountainash.core.capabilities.declarations import (
        CapabilityAssertion,
        CapabilityKey,
        CapabilitySegment,
        LocalOrigin,
        Selector,
    )
    from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate

    assertions = tuple(
        CapabilityAssertion(
            CapabilityKey(
                FK_STR.CENTER,
                "length",
                Selector(
                    "predicate",
                    Predicate((Clause("length", ClauseOp.EQ, value),)),
                ),
            ),
            CapabilityLevel.UNSUPPORTED,
            "2026-08-07",
            (LocalOrigin(str(value)),),
        )
        for value in (True, 1)
    )
    segment = CapabilitySegment(Domain.STRING, assertions)
    assert len({assertion.key for assertion in segment.capabilities}) == 2


def test_classify_domain():
    assert classify_domain(FK_STR.CENTER) is Domain.STRING
    assert classify_domain(FK_DT.ADD_DAYS) is Domain.DATETIME
    assert classify_domain(RKEY_MOUNTAINASH_REL.UNNEST) is Domain.RELATION


def test_dispatch_operation_families_have_distinct_canonical_homes():
    from mountainash.expressions.core.expression_system.function_keys import enums

    required = {
        "FKEY_SUBSTRAIT_CAST": "cast",
        "FKEY_SUBSTRAIT_CONDITIONAL": "conditional",
        "FKEY_SUBSTRAIT_SCALAR_AGGREGATE": "aggregate",
        "FKEY_SUBSTRAIT_SCALAR_COMPARISON": "comparison",
        "FKEY_MOUNTAINASH_SCALAR_COMPARISON": "comparison",
        "FKEY_MOUNTAINASH_NULL": "null",
        "SUBSTRAIT_ARITHMETIC_WINDOW": "window",
        "FKEY_MOUNTAINASH_WINDOW": "window",
    }
    for family_name, domain in required.items():
        for operation in getattr(enums, family_name):
            assert classify_domain(operation).value == domain


def test_local_assertion_qualification_preserves_runtime_identity():
    from mountainash.core.capabilities.declarations import (
        CapabilityAssertion,
        CapabilityKey,
        LocalOrigin,
        Selector,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope

    assertion = CapabilityAssertion(
        key=CapabilityKey(FK_STR.CENTER, "*", Selector()),
        level=CapabilityLevel.UNSUPPORTED,
        message="t",
        since="2026-08-07",
        probe_exempt="test fact",
        origins=(LocalOrigin("center"),),
    )
    duckdb = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))
    sqlite = Scope(CONST_BACKEND.IBIS, Dialect("ibis-sqlite"))
    first = assertion.qualify(duckdb)
    second = assertion.qualify(sqlite)
    assert first.fact_key == _fact(FK_STR.CENTER, CONST_BACKEND.IBIS, dialect="ibis-duckdb").fact_key
    assert first.fact_key != second.fact_key
    assert first == _fact(FK_STR.CENTER, CONST_BACKEND.IBIS, dialect="ibis-duckdb")
    with pytest.raises(ValueError, match="parameter"):
        CapabilityAssertion(
            key=CapabilityKey(FK_STR.CENTER, "missing", Selector()),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-07",
            origins=(LocalOrigin("bad"),),
        ).qualify(duckdb)


def test_segment_context_rejects_reinterpretation_and_duplicate_keys():
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilityAssertion,
        CapabilityKey,
        CapabilitySegment,
        LocalOrigin,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope

    assertion = CapabilityAssertion(
        key=CapabilityKey(FK_STR.CENTER, "*"),
        level=CapabilityLevel.UNSUPPORTED,
        since="2026-08-07",
        origins=(LocalOrigin("center"),),
    )
    segment = CapabilitySegment(domain=Domain.STRING, capabilities=(assertion,))
    module = "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.substrait.string"
    scope = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))
    bound = BoundSegment(module, scope, segment)
    assert bound.source is FactSource.SUBSTRAIT
    with pytest.raises(ValueError, match="scope"):
        BoundSegment(module, Scope(CONST_BACKEND.IBIS, Dialect("ibis-sqlite")), segment)
    with pytest.raises(ValueError, match="source"):
        BoundSegment(module.replace(".substrait.", ".extensions_mountainash."), scope, segment)
    with pytest.raises(ValueError, match="domain"):
        CapabilitySegment(domain=Domain.DATETIME, capabilities=(assertion,))
    with pytest.raises(ValueError, match="duplicate"):
        CapabilitySegment(domain=Domain.STRING, capabilities=(assertion, assertion))


def test_manifestation_key_is_scenario_not_observed_outcome():
    from dataclasses import replace
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilitySegment,
        DivergenceManifestation,
        LocalOrigin,
        ManifestationKey,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.schema import CaptureValue, DivergenceKind, OperationTarget, Scenario

    key = ManifestationKey(
        OperationTarget(FK_STR.CENTER),
        Scenario(arguments=(("input", CaptureValue.of("abc")),)),
    )
    claim = DivergenceManifestation(
        key,
        DivergenceKind.SEMANTICS,
        CaptureValue.of(" abc "),
        CaptureValue.of("abc"),
        "padding ignored",
        "2026-09-15",
        (LocalOrigin("center-padding"),),
    )
    revised = replace(claim, observed=CaptureValue.of(" abc"))
    assert claim.key == revised.key
    with pytest.raises(ValueError, match="duplicate"):
        CapabilitySegment(Domain.STRING, manifestations=(claim, revised))
    segment = CapabilitySegment(Domain.STRING, manifestations=(claim,))
    module = "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.substrait.string"
    BoundSegment(module, Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")), segment)
    with pytest.raises(ValueError, match="home"):
        BoundSegment(
            module.replace(".substrait.", ".extensions_mountainash."),
            Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
            segment,
        )


@pytest.mark.parametrize("channel", ["arguments", "options"])
def test_manifestation_rejects_unknown_scenario_parameter(channel):
    from mountainash.core.capabilities.declarations import ManifestationKey
    from mountainash.core.capabilities.schema import CaptureValue, OperationTarget, Scenario

    with pytest.raises(ValueError, match="parameter"):
        ManifestationKey(
            OperationTarget(FK_STR.CENTER),
            Scenario(**{channel: (("lenght", CaptureValue.of(4)),)}),
        )


def test_manifestation_scenario_uses_authoritative_option_metadata():
    from mountainash.core.capabilities.declarations import ManifestationKey
    from mountainash.core.capabilities.schema import CaptureValue, OperationTarget, Scenario

    target = OperationTarget(FK_CMP.BETWEEN)
    ManifestationKey(target, Scenario(options=(("closed", CaptureValue.of("both")),)))
    with pytest.raises(ValueError, match="option"):
        ManifestationKey(target, Scenario(arguments=(("closed", CaptureValue.of("both")),)))
    with pytest.raises(ValueError, match="option"):
        ManifestationKey(
            OperationTarget(FK_STR.CENTER),
            Scenario(options=(("length", CaptureValue.of(5)),)),
        )


def test_protocol_scenario_uses_captured_callable_after_export_replacement():
    import importlib
    from unittest.mock import patch

    from mountainash.core.capabilities.declarations import ManifestationKey
    from mountainash.core.capabilities.schema import (
        CallableRef,
        CaptureValue,
        ProtocolMethodTarget,
        Scenario,
    )
    from mountainash.core.capabilities.registry import _definition_for

    method = _definition_for(FK_STR.CENTER)[1].protocol_method
    owner_name = method.__qualname__.split(".")[0]
    target = ProtocolMethodTarget(CallableRef(method.__module__, owner_name), "center")
    scenario = Scenario(arguments=(("length", CaptureValue.of(5)),))
    expected = ManifestationKey(target, scenario)
    owner_module = importlib.import_module(method.__module__.rsplit(".", 1)[0])
    replacement = type(owner_name, (), {"__module__": method.__module__, "center": lambda self, input: None})

    with patch.object(owner_module, owner_name, replacement):
        assert ManifestationKey(target, scenario) == expected


def test_active_declarations_require_current_origin_and_valid_issue():
    from mountainash.core.capabilities.capture import CapturedAddress, SourceOrigin
    from mountainash.core.capabilities.declarations import (
        CapabilityAssertion,
        CapabilityKey,
        DivergenceManifestation,
        FactSource,
        LocalOrigin,
        ManifestationKey,
    )
    from mountainash.core.capabilities.identity import FamilyWide, Scope
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.core.capabilities.schema import (
        CaptureValue,
        DivergenceKind,
        OperationTarget,
        Scenario,
    )

    origins = (LocalOrigin("current"),)
    assertion = CapabilityAssertion(
        CapabilityKey(FK_STR.CENTER, "length"),
        CapabilityLevel.UNSUPPORTED,
        "2026-09-15",
        origins,
    )
    manifestation = DivergenceManifestation(
        ManifestationKey(OperationTarget(FK_STR.CENTER), Scenario()),
        DivergenceKind.SEMANTICS,
        CaptureValue.of(0),
        CaptureValue.of(1),
        "fixture",
        "2026-09-15",
        origins,
    )
    prior = SourceOrigin(
        "mountainash.legacy",
        Scope(CONST_BACKEND.IBIS, FamilyWide()),
        FactSource.SUBSTRAIT,
        Domain.STRING,
        "old",
        CapturedAddress("mountainash", "old.py", "old", artifact=b"old"),
    )
    with pytest.raises(ValueError, match="current"):
        CapabilityAssertion(
            assertion.key,
            assertion.level,
            assertion.since,
            (prior,),
        )
    with pytest.raises(ValueError, match="current"):
        DivergenceManifestation(
            manifestation.key,
            manifestation.kind,
            manifestation.expected,
            manifestation.observed,
            manifestation.impact,
            manifestation.since,
            (prior,),
        )
    with pytest.raises(ValueError, match="issue"):
        DivergenceManifestation(
            manifestation.key,
            manifestation.kind,
            manifestation.expected,
            manifestation.observed,
            manifestation.impact,
            manifestation.since,
            origins,
            issue="malformed",
        )


def test_every_unit_c_matrix_cell_has_one_winning_fact() -> None:
    """Every declared Unit C gate/residue cell resolves through its consumer."""
    unit_c_keys = (
        set(FK_CAT)
        | set(FK_DT)
        | set(FK_GEO)
        | set(FK_LIST)
        | set(FK_VALUE)
        | set(FK_STRUCT)
        | {
            FK_DT.PARSE_DEFAULT,
            FK_DT.PARSE_XSD_DURATION,
            FK_DT.PARSE_XSD_PARTIAL_DATE,
            FK_DT.PARSE_TEMPORAL_ANY,
        }
    )
    cells = [
        fact
        for fact in CapabilityRegistry.facts()
        if fact.operation_key in unit_c_keys
        and fact.level is CapabilityLevel.UNSUPPORTED
        and fact.enforcement
        in {
            Enforcement.GATE,
            Enforcement.MATERIALIZE_RESIDUE,
        }
    ]
    for fact in cells:
        if fact.enforcement is Enforcement.MATERIALIZE_RESIDUE:
            winner = CapabilityRegistry.residue_for(fact.backend, fact.dialect).get((fact.operation_key, fact.param))
            assert winner is fact, fact.fact_key
            continue
        if fact.predicate is not None:
            bindings = {}
            operand_fields: dict[str, dict[str, object]] = {}
            predicate_facts = (
                fact,
                *CapabilityRegistry.facts(backend=fact.backend),
            )
            for candidate in predicate_facts:
                if (
                    candidate.operation_key != fact.operation_key
                    or candidate.predicate is None
                    or (candidate.dialect is not None and candidate.dialect != fact.dialect)
                ):
                    continue
                for clause in candidate.predicate.clauses:
                    if clause.path.startswith("__operand_types__."):
                        _, operand, field = clause.path.split(".")
                        fields = operand_fields.setdefault(
                            operand,
                            {
                                "logical_kind": "unknown",
                                "storage_kind": "polars_object",
                                "nullable": None,
                            },
                        )
                        if clause.op is ClauseOp.EQ:
                            fields[field] = clause.operand
                        elif clause.op is ClauseOp.IN:
                            fields[field] = sorted(clause.operand, key=str)[0]
                        else:
                            raise AssertionError(f"unhandled metadata selector: {clause.op}")
                        continue
                    if clause.path in bindings:
                        continue
                    if clause.op is ClauseOp.EQ:
                        bindings[clause.path] = clause.operand
                    elif clause.op is ClauseOp.IN:
                        bindings[clause.path] = sorted(clause.operand, key=str)[0]
                    elif clause.op is ClauseOp.IS_SET:
                        bindings[clause.path] = "set"
                    elif clause.op is ClauseOp.IS_NULL:
                        bindings[clause.path] = None
                    else:
                        raise AssertionError(f"unhandled Unit C selector: {clause.op}")
            operand_types = {operand: OperandType(**fields) for operand, fields in operand_fields.items()}
            winners = CapabilityRegistry.violations_for(
                BoundCall(
                    fact.operation_key,
                    fact.backend,
                    fact.dialect,
                    bindings,
                    frozenset(bindings),
                    operand_types=operand_types or None,
                )
            )
            winners = {winner for winner in winners if winner.dialect == fact.dialect}
            assert winners == {fact}, fact.fact_key
            continue
        if fact.value_class is not None:
            samples = {
                "duration_multiplier": "2d",
                "iana_timezone": "UTC",
                "polars_offset": "2d",
            }
            option_value = samples[fact.value_class.value]
        else:
            option_value = fact.option_value
        winner = CapabilityRegistry.capability_for(
            fact.operation_key,
            fact.param,
            fact.backend,
            dialect=fact.dialect,
            option_value=option_value,
        )
        assert winner is fact, fact.fact_key


def test_probe_evidence_validates_date():
    with pytest.raises(ValueError, match="probe_date"):
        ProbeEvidence(probe_date="not-a-date", library_versions=(), fixtures=())


def test_narwhals_lazy_categorical_gate_is_declared_once() -> None:
    facts = [
        fact
        for fact in CapabilityRegistry.facts()
        if fact.operation_key is FK_CAT.CAST
        and fact.backend is CONST_BACKEND.NARWHALS
        and fact.dialect == "narwhals-lazy"
        and fact.param == "value_type"
        and fact.predicate is not None
    ]

    assert len(facts) == 1
    gate = facts[0]
    assert gate.level is CapabilityLevel.UNSUPPORTED
    assert gate.option_value is None
    clauses = {(clause.path, clause.operand) for clause in gate.predicate.clauses if clause.op is ClauseOp.EQ}
    assert clauses == {("value_type", "integer"), ("failure_behavior", "null")}


@pytest.mark.parametrize(
    "dialect,data",
    [
        ("ibis-duckdb", {"a": [1, 2], "b": [None, None]}),
        ("ibis-sqlite", {"addr": [{"street": "Main St", "zip": "12345"}]}),
    ],
)
def test_external_manifestations_cannot_claim_mountainash_execution(dialect, data):
    from dataclasses import replace
    from pathlib import Path

    from mountainash.core.capabilities.capture import (
        BindingRole,
        CapturedAddress,
        CapturedAssertion,
        VerificationBinding,
    )
    from mountainash.core.capabilities.catalogue import BindingQuery, CatalogueQuery
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilitySegment,
        DivergenceManifestation,
        LocalOrigin,
        ManifestationKey,
        QualifiedManifestationKey,
    )
    from mountainash.core.capabilities.gaps import GapKey, InventoryWide, VerificationSnapshot
    from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
    from mountainash.core.capabilities.schema import (
        CaptureValue,
        DivergenceKind,
        EntrypointStage,
        ExternalCallableRef,
        ExternalEntrypointTarget,
        Scenario,
    )

    target = ExternalEntrypointTarget(
        ExternalCallableRef("ibis.backends." + dialect.removeprefix("ibis-"), "Backend.create_table"),
        EntrypointStage.CONSTRUCTION,
    )
    scenario = Scenario(
        arguments=(("obj", CaptureValue.of(data)),),
        options=(("name", CaptureValue.of("test_table")), ("overwrite", CaptureValue.of(True))),
    )
    key = ManifestationKey(target, scenario)
    scope = Scope(CONST_BACKEND.IBIS, Dialect(dialect))
    qualified = QualifiedManifestationKey(scope, key)
    assertion = DivergenceManifestation(
        key,
        DivergenceKind.ENGINE_LENIENCY,
        CaptureValue.of({"construction": "table preserving source data"}),
        CaptureValue.of({"historical_claim": "native input construction rejected"}),
        "Native construction prevents the later Mountainash call",
        "2026-09-15",
        (LocalOrigin("native construction"),),
    )
    segment = CapabilitySegment(Domain.NATIVE_INPUT, manifestations=(assertion,))
    module = (
        "mountainash.relations.backends.capabilities.ibis.dialects."
        + dialect.replace("-", "_")
        + ".extensions_mountainash.native_input"
    )
    BoundSegment(module, scope, segment)
    with pytest.raises(ValueError):
        BoundSegment(module.replace("relations.", "expressions.", 1), scope, segment)
    with pytest.raises(ValueError):
        CapabilitySegment(Domain.RELATION, manifestations=(assertion,))
    other = "ibis-sqlite" if dialect == "ibis-duckdb" else "ibis-duckdb"
    with pytest.raises(ValueError):
        GapKey("native-input", target, "construct table", InventoryWide())
    for wrong_scope in (
        Scope(CONST_BACKEND.IBIS, Dialect(other)),
        Scope(CONST_BACKEND.IBIS, FamilyWide()),
        Scope(CONST_BACKEND.POLARS, FamilyWide()),
    ):
        with pytest.raises(ValueError):
            QualifiedManifestationKey(wrong_scope, key)
        with pytest.raises(ValueError):
            GapKey("native-input", target, "construct table", wrong_scope)
    for wrong_scenario in (
        Scenario(arguments=(("overwrite", CaptureValue.of(True)),)),
        Scenario(options=(("obj", CaptureValue.of(data)),)),
        Scenario(arguments=(("unknown", CaptureValue.of(None)),)),
    ):
        with pytest.raises(ValueError):
            ManifestationKey(target, wrong_scenario)

    source = CapturedAddress(
        "mountainash",
        "tests/core/test_capability_declarations.py",
        "native construction declaration",
        artifact=Path(__file__).read_bytes(),
    )
    claim = CapturedAssertion("manifestation", qualified, assertion, source)
    binding = VerificationBinding(
        claim,
        scenario,
        BindingRole.OPERATIONAL_CONTRACT,
        replace(source, entry=f"native construction observer[{dialect}]"),
        scope,
        replace(source, entry="construction oracle"),
        "construction",
    )
    captured = CapabilityRegistry.capture(verification=VerificationSnapshot((), bindings=(binding,)))
    assert captured.search(
        CatalogueQuery(
            scopes=frozenset({scope}),
            bindings=BindingQuery(captured_claim=claim),
        )
    ).bindings == (binding,)
    assert (
        captured.search(
            CatalogueQuery(
                bindings=BindingQuery(stage="materialization"),
            )
        ).bindings
        == ()
    )
    with pytest.raises(ValueError):
        replace(binding, stage="materialization")
    with pytest.raises(ValueError):
        replace(target, stage=EntrypointStage.COMPILATION)
    with pytest.raises(ValueError):
        ExternalCallableRef("os", "system")
    with pytest.raises(ValueError):
        ExternalCallableRef("ibis.backends.sqlite", "Backend.unknown")
