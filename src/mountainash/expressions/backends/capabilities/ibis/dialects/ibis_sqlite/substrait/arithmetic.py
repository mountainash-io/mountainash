"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations
from mountainash.core.capabilities.capture import CapturedAddress
from mountainash.core.capabilities.capture import CapturedAssertion
from mountainash.core.capabilities.declarations import QualifiedManifestationKey
from mountainash.core.capabilities.identity import Dialect
from mountainash.core.capabilities.identity import Scope
from mountainash.core.capabilities.retired import AssertionChange
from mountainash.core.capabilities.retired import ChangeDisposition
from mountainash.core.constants import CONST_BACKEND

from mountainash.core.capabilities.declarations import CapabilitySegment
from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import Domain
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import OperationTarget
from mountainash.core.capabilities.schema import Scenario
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

SEGMENT = CapabilitySegment(
    domain=Domain.ARITHMETIC,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+1"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="acosh(2.0)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite"),
                    ),
                ),
            ),
            impact="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite",
            since="2026-07-05",
            workaround="Any backend other than ibis-sqlite",
            issue="IB-MATH-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="asinh(1.0)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite"),
                    ),
                ),
            ),
            impact="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite",
            since="2026-07-05",
            workaround="Any backend other than ibis-sqlite",
            issue="IB-MATH-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p-1"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="atanh(0.5)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite"),
                    ),
                ),
            ),
            impact="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite",
            since="2026-07-05",
            workaround="Any backend other than ibis-sqlite",
            issue="IB-MATH-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                CaptureValue(tag="text", value="cosh(1.0)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite"),
                    ),
                ),
            ),
            impact="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite",
            since="2026-07-05",
            workaround="Any backend other than ibis-sqlite",
            issue="IB-MATH-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="-10"),
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="-10"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="-3"),
                                                CaptureValue(tag="integer", value="-3"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="-2"),
                                CaptureValue(tag="integer", value="-1"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical SQL dividend-sign modulo"),
                    ),
                ),
            ),
            impact="Cyclic calculations and hash bucketing with negative dividends diverge",
            since="2026-07-05",
            workaround="Ensure the dividend is non-negative or normalize with a conditional expression",
            issue="IB-MATH-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="sinh(1.0)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite"),
                    ),
                ),
            ),
            impact="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite",
            since="2026-07-05",
            workaround="Any backend other than ibis-sqlite",
            issue="IB-MATH-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="tanh(1.0)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite"),
                    ),
                ),
            ),
            impact="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite",
            since="2026-07-05",
            workaround="Any backend other than ibis-sqlite",
            issue="IB-MATH-02",
        ),
    ),
    changes=(
        AssertionChange(
            change_ref=CapturedAddress(
                repository="mountainash-central",
                path="04.planning/mountainash/superpowers/plans/2026-09-17-manifestation-positive-retirements.json",
                entry="changes[0]",
                revision=None,
                artifact=b'{\n  "execution_source_revision": "e7b5cfb969034ba6fa5ea16c94311dae833921a7",\n  "recorded_at": "2026-09-17",\n  "changes": [\n    {\n      "legacy_provenance": "IB-MATH-04",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-sqlite\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE), scenario=Scenario(arguments=((\'x\', CaptureValue(tag=\'mapping\', value=((\'field\', CaptureValue(tag=\'text\', value=\'left\'),),)),), (\'y\', CaptureValue(tag=\'mapping\', value=((\'field\', CaptureValue(tag=\'text\', value=\'right\'),),)),),), options=(), input_schema=(), input_data=((\'fixture\', CaptureValue(tag=\'mapping\', value=((\'left\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'5\'), CaptureValue(tag=\'integer\', value=\'7\'),)),), (\'right\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'2\'), CaptureValue(tag=\'integer\', value=\'2\'),)),),)),),), execution=((\'mode\', CaptureValue(tag=\'text\', value=\'public-and-direct-native\'),),))))",\n      "disposition": "incorrect_declaration",\n      "reason": "The retained public and direct-native SQLite division observation yields [2.5, 3.5], not integer division. The existing cross-backend division contract remains positive; no version interval is inferred.",\n      "evidence_entry": "integer_division",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-MATH-04",\n        "impact": "Division expecting float results silently truncates on ibis-sqlite",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.SEMANTICS",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "catalogue-only-candidate",\n        "since": "2026-07-05",\n        "source_mentions": [],\n        "summary": "SQLite performs integer division for two integer operands",\n        "upstream_ref": "IB-MATH-04",\n        "workaround": "Cast one operand to float before dividing"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[7].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-09",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-duckdb\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'fixture\', CaptureValue(tag=\'mapping\', value=((\'a\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'1\'),)),),)),),), execution=((\'mode\', CaptureValue(tag=\'text\', value=\'public-native-type-inspection\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "Retire only the TODAY type assertion: the compiled native expression is Date and the materialized value is datetime.date. NOW timing/timezone claims remain independent; this is public compilation/materialization evidence, not a direct-native execution.",\n      "evidence_entry": "today_type",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-duckdb",\n          "ibis-polars",\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-duckdb"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-polars"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-09",\n        "impact": "today() snapshot type differs on all ibis backends; now() evaluation instant differs on ibis-duckdb/ibis-sqlite (UTC, query-time)",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.SEMANTICS",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.NOW"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-07-05",\n        "source_mentions": [\n          {\n            "line": 19,\n            "path": "tests/expressions/cross_backend/test_datetime_snapshot.py"\n          }\n        ],\n        "summary": "Ibis today() upcasts date to timestamp on ALL ibis backends; now() compiles to query-time UTC SQL on ibis-duckdb and ibis-sqlite only (ibis-polars evaluates now() like Polars/Narwhals)",\n        "upstream_ref": "IB-DT-09",\n        "workaround": "Use Polars or Narwhals for exact date types; account for UTC query-time now() on ibis-duckdb/ibis-sqlite"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[11].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-09",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-polars\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'fixture\', CaptureValue(tag=\'mapping\', value=((\'a\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'1\'),)),),)),),), execution=((\'mode\', CaptureValue(tag=\'text\', value=\'public-native-type-inspection\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "Retire only the TODAY type assertion: the compiled native expression is Date and the materialized value is datetime.date. NOW timing/timezone claims remain independent; this is public compilation/materialization evidence, not a direct-native execution.",\n      "evidence_entry": "today_type",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-duckdb",\n          "ibis-polars",\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-duckdb"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-polars"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-09",\n        "impact": "today() snapshot type differs on all ibis backends; now() evaluation instant differs on ibis-duckdb/ibis-sqlite (UTC, query-time)",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.SEMANTICS",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.NOW"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-07-05",\n        "source_mentions": [\n          {\n            "line": 19,\n            "path": "tests/expressions/cross_backend/test_datetime_snapshot.py"\n          }\n        ],\n        "summary": "Ibis today() upcasts date to timestamp on ALL ibis backends; now() compiles to query-time UTC SQL on ibis-duckdb and ibis-sqlite only (ibis-polars evaluates now() like Polars/Narwhals)",\n        "upstream_ref": "IB-DT-09",\n        "workaround": "Use Polars or Narwhals for exact date types; account for UTC query-time now() on ibis-duckdb/ibis-sqlite"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[11].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-09",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-sqlite\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'fixture\', CaptureValue(tag=\'mapping\', value=((\'a\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'1\'),)),),)),),), execution=((\'mode\', CaptureValue(tag=\'text\', value=\'public-native-type-inspection\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "Retire only the TODAY type assertion: the compiled native expression is Date and the materialized value is datetime.date. NOW timing/timezone claims remain independent; this is public compilation/materialization evidence, not a direct-native execution.",\n      "evidence_entry": "today_type",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-duckdb",\n          "ibis-polars",\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-duckdb"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-polars"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-09",\n        "impact": "today() snapshot type differs on all ibis backends; now() evaluation instant differs on ibis-duckdb/ibis-sqlite (UTC, query-time)",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.SEMANTICS",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.NOW"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-07-05",\n        "source_mentions": [\n          {\n            "line": 19,\n            "path": "tests/expressions/cross_backend/test_datetime_snapshot.py"\n          }\n        ],\n        "summary": "Ibis today() upcasts date to timestamp on ALL ibis backends; now() compiles to query-time UTC SQL on ibis-duckdb and ibis-sqlite only (ibis-polars evaluates now() like Polars/Narwhals)",\n        "upstream_ref": "IB-DT-09",\n        "workaround": "Use Polars or Narwhals for exact date types; account for UTC query-time now() on ibis-duckdb/ibis-sqlite"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[11].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-14",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-sqlite\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'timestamp\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-01-01T10:00\'), CaptureValue(tag=\'text\', value=\'2024-06-15T14:30\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression offset=1d2h SQLite<3.46\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "The selected SQLite scenario is an unmarked passing control in the retained operational run. Preserve the historical older-engine claim without asserting a release interval or expected failure in this observed environment.",\n      "evidence_entry": "dt14_offset",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-14",\n        "impact": "calendar/offset arithmetic raises on ibis-sqlite when the linked SQLite is < 3.46; >= 3.46 computes them",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.ENGINE_LENIENCY",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-08-06",\n        "source_mentions": [\n          {\n            "line": 15,\n            "path": "tests/expressions/cross_backend/test_datetime_enrichment.py"\n          },\n          {\n            "line": 21,\n            "path": "tests/expressions/cross_backend/test_parameter_sensitivity.py"\n          },\n          {\n            "line": 23,\n            "path": "tests/expressions/cross_backend/test_temporal_advanced.py"\n          }\n        ],\n        "summary": "SQLite < 3.46 lacks time-shift modifiers, so calendar arithmetic (add_days/add_months/month_end/days_in_month/combined offsets) is unavailable on ibis-sqlite; SQLite >= 3.46 supports them (environment-conditional \xe2\x80\x94 the mark is applied only below 3.46)",\n        "upstream_ref": null,\n        "workaround": "Upgrade SQLite to >= 3.46, or use another backend for calendar arithmetic"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[36].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-14",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-sqlite\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'ts\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-02-15\'), CaptureValue(tag=\'text\', value=\'2024-03-15\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression SQLite<3.46\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "The selected SQLite scenario is an unmarked passing control in the retained operational run. Preserve the historical older-engine claim without asserting a release interval or expected failure in this observed environment.",\n      "evidence_entry": "dt14_month_end",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-14",\n        "impact": "calendar/offset arithmetic raises on ibis-sqlite when the linked SQLite is < 3.46; >= 3.46 computes them",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.ENGINE_LENIENCY",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-08-06",\n        "source_mentions": [\n          {\n            "line": 15,\n            "path": "tests/expressions/cross_backend/test_datetime_enrichment.py"\n          },\n          {\n            "line": 21,\n            "path": "tests/expressions/cross_backend/test_parameter_sensitivity.py"\n          },\n          {\n            "line": 23,\n            "path": "tests/expressions/cross_backend/test_temporal_advanced.py"\n          }\n        ],\n        "summary": "SQLite < 3.46 lacks time-shift modifiers, so calendar arithmetic (add_days/add_months/month_end/days_in_month/combined offsets) is unavailable on ibis-sqlite; SQLite >= 3.46 supports them (environment-conditional \xe2\x80\x94 the mark is applied only below 3.46)",\n        "upstream_ref": null,\n        "workaround": "Upgrade SQLite to >= 3.46, or use another backend for calendar arithmetic"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[36].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-14",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-sqlite\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'ts\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-02-15\'), CaptureValue(tag=\'text\', value=\'2024-03-15\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression SQLite<3.46\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "The selected SQLite scenario is an unmarked passing control in the retained operational run. Preserve the historical older-engine claim without asserting a release interval or expected failure in this observed environment.",\n      "evidence_entry": "dt14_days_in_month",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-14",\n        "impact": "calendar/offset arithmetic raises on ibis-sqlite when the linked SQLite is < 3.46; >= 3.46 computes them",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.ENGINE_LENIENCY",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-08-06",\n        "source_mentions": [\n          {\n            "line": 15,\n            "path": "tests/expressions/cross_backend/test_datetime_enrichment.py"\n          },\n          {\n            "line": 21,\n            "path": "tests/expressions/cross_backend/test_parameter_sensitivity.py"\n          },\n          {\n            "line": 23,\n            "path": "tests/expressions/cross_backend/test_temporal_advanced.py"\n          }\n        ],\n        "summary": "SQLite < 3.46 lacks time-shift modifiers, so calendar arithmetic (add_days/add_months/month_end/days_in_month/combined offsets) is unavailable on ibis-sqlite; SQLite >= 3.46 supports them (environment-conditional \xe2\x80\x94 the mark is applied only below 3.46)",\n        "upstream_ref": null,\n        "workaround": "Upgrade SQLite to >= 3.46, or use another backend for calendar arithmetic"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[36].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    }\n  ],\n  "positive_controls": [\n    {\n      "nodeid": "tests/expressions/cross_backend/test_temporal_advanced.py::TestFlexibleOffsetBy::test_offset_add_days_and_hours[ibis-sqlite]",\n      "claim": "DivergenceManifestation(key=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'timestamp\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-01-01T10:00\'), CaptureValue(tag=\'text\', value=\'2024-06-15T14:30\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression offset=1d2h SQLite<3.46\'),),))), kind=DivergenceKind.ENGINE_LENIENCY, expected=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-01-02T12:00\'), CaptureValue(tag=\'text\', value=\'2024-06-16T16:30\'),)),),)), observed=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'text\', value=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\'),),)), impact=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\', since=\'2026-08-06\', workaround=\'Upgrade SQLite to >= 3.46, or use another backend\', issue=None)",\n      "outcome": {\n        "nodeid": "tests/expressions/cross_backend/test_temporal_advanced.py::TestFlexibleOffsetBy::test_offset_add_days_and_hours[ibis-sqlite]",\n        "path": "tests/expressions/cross_backend/test_temporal_advanced.py",\n        "function": "TestFlexibleOffsetBy.test_offset_add_days_and_hours",\n        "parameters": {\n          "backend_name": "\'ibis-sqlite\'"\n        },\n        "phase": "call",\n        "outcome": "passed",\n        "expected_failure": null,\n        "error": null,\n        "detail": null\n      }\n    },\n    {\n      "nodeid": "tests/expressions/cross_backend/test_datetime_enrichment.py::TestMonthEnd::test_month_end[ibis-sqlite]",\n      "claim": "DivergenceManifestation(key=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'ts\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-02-15\'), CaptureValue(tag=\'text\', value=\'2024-03-15\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression SQLite<3.46\'),),))), kind=DivergenceKind.ENGINE_LENIENCY, expected=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'29\'), CaptureValue(tag=\'integer\', value=\'31\'),)),),)), observed=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'text\', value=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\'),),)), impact=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\', since=\'2026-08-06\', workaround=\'Upgrade SQLite to >= 3.46, or use another backend\', issue=None)",\n      "outcome": {\n        "nodeid": "tests/expressions/cross_backend/test_datetime_enrichment.py::TestMonthEnd::test_month_end[ibis-sqlite]",\n        "path": "tests/expressions/cross_backend/test_datetime_enrichment.py",\n        "function": "TestMonthEnd.test_month_end",\n        "parameters": {\n          "backend_name": "\'ibis-sqlite\'"\n        },\n        "phase": "call",\n        "outcome": "passed",\n        "expected_failure": null,\n        "error": null,\n        "detail": null\n      }\n    },\n    {\n      "nodeid": "tests/expressions/cross_backend/test_datetime_enrichment.py::TestDaysInMonth::test_days_in_month[ibis-sqlite]",\n      "claim": "DivergenceManifestation(key=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'ts\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-02-15\'), CaptureValue(tag=\'text\', value=\'2024-03-15\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression SQLite<3.46\'),),))), kind=DivergenceKind.ENGINE_LENIENCY, expected=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'29\'), CaptureValue(tag=\'integer\', value=\'31\'),)),),)), observed=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'text\', value=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\'),),)), impact=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\', since=\'2026-08-06\', workaround=\'Upgrade SQLite to >= 3.46, or use another backend\', issue=None)",\n      "outcome": {\n        "nodeid": "tests/expressions/cross_backend/test_datetime_enrichment.py::TestDaysInMonth::test_days_in_month[ibis-sqlite]",\n        "path": "tests/expressions/cross_backend/test_datetime_enrichment.py",\n        "function": "TestDaysInMonth.test_days_in_month",\n        "parameters": {\n          "backend_name": "\'ibis-sqlite\'"\n        },\n        "phase": "call",\n        "outcome": "passed",\n        "expected_failure": null,\n        "error": null,\n        "detail": null\n      }\n    }\n  ]\n}',
            ),
            prior=CapturedAssertion(
                family="manifestation",
                key=QualifiedManifestationKey(
                    scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name="ibis-sqlite")),
                    local=ManifestationKey(
                        target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE),
                        scenario=Scenario(
                            arguments=(
                                (
                                    "x",
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "field",
                                                CaptureValue(tag="text", value="left"),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "y",
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "field",
                                                CaptureValue(tag="text", value="right"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                            options=(),
                            input_schema=(),
                            input_data=(
                                (
                                    "fixture",
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "left",
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="7"),
                                                    ),
                                                ),
                                            ),
                                            (
                                                "right",
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                            execution=(
                                (
                                    "mode",
                                    CaptureValue(tag="text", value="public-and-direct-native"),
                                ),
                            ),
                        ),
                    ),
                ),
                payload=CaptureValue(
                    tag="mapping",
                    value=(
                        (
                            "backends",
                            CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="ibis-sqlite"),)),
                        ),
                        (
                            "capability_candidates_not_semantic_joins",
                            CaptureValue(tag="sequence", value=()),
                        ),
                        (
                            "classification_owner",
                            CaptureValue(tag="text", value="item100"),
                        ),
                        (
                            "declared_scope_obligations",
                            CaptureValue(
                                tag="sequence",
                                value=(
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "date",
                                                CaptureValue(tag="text", value="2026-09-15"),
                                            ),
                                            (
                                                "direct_probe",
                                                CaptureValue(
                                                    tag="text",
                                                    value="unverified except explicitly recorded behavioral cohort",
                                                ),
                                            ),
                                            (
                                                "operational_binding",
                                                CaptureValue(
                                                    tag="text", value="source incidence only; variant recovery required"
                                                ),
                                            ),
                                            (
                                                "owner",
                                                CaptureValue(tag="text", value="item100"),
                                            ),
                                            (
                                                "scope",
                                                CaptureValue(tag="text", value="ibis-sqlite"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "id",
                            CaptureValue(tag="text", value="IB-MATH-04"),
                        ),
                        (
                            "impact",
                            CaptureValue(
                                tag="text", value="Division expecting float results silently truncates on ibis-sqlite"
                            ),
                        ),
                        (
                            "kind",
                            CaptureValue(
                                tag="text", value="mountainash.core.capabilities.schema.DivergenceKind.SEMANTICS"
                            ),
                        ),
                        (
                            "operation_keys",
                            CaptureValue(
                                tag="sequence",
                                value=(
                                    CaptureValue(
                                        tag="text",
                                        value="mountainash.expressions.core.expression_system.function_keys.enums.FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE",
                                    ),
                                ),
                            ),
                        ),
                        (
                            "original_record_status",
                            CaptureValue(
                                tag="text",
                                value="Captured source declaration; prose claims are not automatically fresh observations.",
                            ),
                        ),
                        (
                            "probe_status",
                            CaptureValue(
                                tag="text",
                                value="unverified; no per-scope direct-probe binding inferred from ID mentions",
                            ),
                        ),
                        (
                            "reachability",
                            CaptureValue(tag="text", value="catalogue-only-candidate"),
                        ),
                        (
                            "since",
                            CaptureValue(tag="text", value="2026-07-05"),
                        ),
                        (
                            "source_mentions",
                            CaptureValue(tag="sequence", value=()),
                        ),
                        (
                            "summary",
                            CaptureValue(tag="text", value="SQLite performs integer division for two integer operands"),
                        ),
                        (
                            "upstream_ref",
                            CaptureValue(tag="text", value="IB-MATH-04"),
                        ),
                        (
                            "workaround",
                            CaptureValue(tag="text", value="Cast one operand to float before dividing"),
                        ),
                    ),
                ),
                address=CapturedAddress(
                    repository="mountainash-central",
                    path="04.planning/mountainash/superpowers/plans/2026-09-17-manifestation-positive-retirements.json",
                    entry="changes[0].prior_complete_payload",
                    revision=None,
                    artifact=b'{\n  "execution_source_revision": "e7b5cfb969034ba6fa5ea16c94311dae833921a7",\n  "recorded_at": "2026-09-17",\n  "changes": [\n    {\n      "legacy_provenance": "IB-MATH-04",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-sqlite\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE), scenario=Scenario(arguments=((\'x\', CaptureValue(tag=\'mapping\', value=((\'field\', CaptureValue(tag=\'text\', value=\'left\'),),)),), (\'y\', CaptureValue(tag=\'mapping\', value=((\'field\', CaptureValue(tag=\'text\', value=\'right\'),),)),),), options=(), input_schema=(), input_data=((\'fixture\', CaptureValue(tag=\'mapping\', value=((\'left\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'5\'), CaptureValue(tag=\'integer\', value=\'7\'),)),), (\'right\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'2\'), CaptureValue(tag=\'integer\', value=\'2\'),)),),)),),), execution=((\'mode\', CaptureValue(tag=\'text\', value=\'public-and-direct-native\'),),))))",\n      "disposition": "incorrect_declaration",\n      "reason": "The retained public and direct-native SQLite division observation yields [2.5, 3.5], not integer division. The existing cross-backend division contract remains positive; no version interval is inferred.",\n      "evidence_entry": "integer_division",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-MATH-04",\n        "impact": "Division expecting float results silently truncates on ibis-sqlite",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.SEMANTICS",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "catalogue-only-candidate",\n        "since": "2026-07-05",\n        "source_mentions": [],\n        "summary": "SQLite performs integer division for two integer operands",\n        "upstream_ref": "IB-MATH-04",\n        "workaround": "Cast one operand to float before dividing"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[7].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-09",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-duckdb\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'fixture\', CaptureValue(tag=\'mapping\', value=((\'a\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'1\'),)),),)),),), execution=((\'mode\', CaptureValue(tag=\'text\', value=\'public-native-type-inspection\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "Retire only the TODAY type assertion: the compiled native expression is Date and the materialized value is datetime.date. NOW timing/timezone claims remain independent; this is public compilation/materialization evidence, not a direct-native execution.",\n      "evidence_entry": "today_type",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-duckdb",\n          "ibis-polars",\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-duckdb"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-polars"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-09",\n        "impact": "today() snapshot type differs on all ibis backends; now() evaluation instant differs on ibis-duckdb/ibis-sqlite (UTC, query-time)",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.SEMANTICS",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.NOW"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-07-05",\n        "source_mentions": [\n          {\n            "line": 19,\n            "path": "tests/expressions/cross_backend/test_datetime_snapshot.py"\n          }\n        ],\n        "summary": "Ibis today() upcasts date to timestamp on ALL ibis backends; now() compiles to query-time UTC SQL on ibis-duckdb and ibis-sqlite only (ibis-polars evaluates now() like Polars/Narwhals)",\n        "upstream_ref": "IB-DT-09",\n        "workaround": "Use Polars or Narwhals for exact date types; account for UTC query-time now() on ibis-duckdb/ibis-sqlite"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[11].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-09",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-polars\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'fixture\', CaptureValue(tag=\'mapping\', value=((\'a\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'1\'),)),),)),),), execution=((\'mode\', CaptureValue(tag=\'text\', value=\'public-native-type-inspection\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "Retire only the TODAY type assertion: the compiled native expression is Date and the materialized value is datetime.date. NOW timing/timezone claims remain independent; this is public compilation/materialization evidence, not a direct-native execution.",\n      "evidence_entry": "today_type",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-duckdb",\n          "ibis-polars",\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-duckdb"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-polars"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-09",\n        "impact": "today() snapshot type differs on all ibis backends; now() evaluation instant differs on ibis-duckdb/ibis-sqlite (UTC, query-time)",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.SEMANTICS",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.NOW"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-07-05",\n        "source_mentions": [\n          {\n            "line": 19,\n            "path": "tests/expressions/cross_backend/test_datetime_snapshot.py"\n          }\n        ],\n        "summary": "Ibis today() upcasts date to timestamp on ALL ibis backends; now() compiles to query-time UTC SQL on ibis-duckdb and ibis-sqlite only (ibis-polars evaluates now() like Polars/Narwhals)",\n        "upstream_ref": "IB-DT-09",\n        "workaround": "Use Polars or Narwhals for exact date types; account for UTC query-time now() on ibis-duckdb/ibis-sqlite"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[11].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-09",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-sqlite\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'fixture\', CaptureValue(tag=\'mapping\', value=((\'a\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'1\'),)),),)),),), execution=((\'mode\', CaptureValue(tag=\'text\', value=\'public-native-type-inspection\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "Retire only the TODAY type assertion: the compiled native expression is Date and the materialized value is datetime.date. NOW timing/timezone claims remain independent; this is public compilation/materialization evidence, not a direct-native execution.",\n      "evidence_entry": "today_type",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-duckdb",\n          "ibis-polars",\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-duckdb"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-polars"\n          },\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-09",\n        "impact": "today() snapshot type differs on all ibis backends; now() evaluation instant differs on ibis-duckdb/ibis-sqlite (UTC, query-time)",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.SEMANTICS",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.NOW"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-07-05",\n        "source_mentions": [\n          {\n            "line": 19,\n            "path": "tests/expressions/cross_backend/test_datetime_snapshot.py"\n          }\n        ],\n        "summary": "Ibis today() upcasts date to timestamp on ALL ibis backends; now() compiles to query-time UTC SQL on ibis-duckdb and ibis-sqlite only (ibis-polars evaluates now() like Polars/Narwhals)",\n        "upstream_ref": "IB-DT-09",\n        "workaround": "Use Polars or Narwhals for exact date types; account for UTC query-time now() on ibis-duckdb/ibis-sqlite"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[11].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-14",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-sqlite\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'timestamp\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-01-01T10:00\'), CaptureValue(tag=\'text\', value=\'2024-06-15T14:30\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression offset=1d2h SQLite<3.46\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "The selected SQLite scenario is an unmarked passing control in the retained operational run. Preserve the historical older-engine claim without asserting a release interval or expected failure in this observed environment.",\n      "evidence_entry": "dt14_offset",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-14",\n        "impact": "calendar/offset arithmetic raises on ibis-sqlite when the linked SQLite is < 3.46; >= 3.46 computes them",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.ENGINE_LENIENCY",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-08-06",\n        "source_mentions": [\n          {\n            "line": 15,\n            "path": "tests/expressions/cross_backend/test_datetime_enrichment.py"\n          },\n          {\n            "line": 21,\n            "path": "tests/expressions/cross_backend/test_parameter_sensitivity.py"\n          },\n          {\n            "line": 23,\n            "path": "tests/expressions/cross_backend/test_temporal_advanced.py"\n          }\n        ],\n        "summary": "SQLite < 3.46 lacks time-shift modifiers, so calendar arithmetic (add_days/add_months/month_end/days_in_month/combined offsets) is unavailable on ibis-sqlite; SQLite >= 3.46 supports them (environment-conditional \xe2\x80\x94 the mark is applied only below 3.46)",\n        "upstream_ref": null,\n        "workaround": "Upgrade SQLite to >= 3.46, or use another backend for calendar arithmetic"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[36].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-14",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-sqlite\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'ts\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-02-15\'), CaptureValue(tag=\'text\', value=\'2024-03-15\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression SQLite<3.46\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "The selected SQLite scenario is an unmarked passing control in the retained operational run. Preserve the historical older-engine claim without asserting a release interval or expected failure in this observed environment.",\n      "evidence_entry": "dt14_month_end",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-14",\n        "impact": "calendar/offset arithmetic raises on ibis-sqlite when the linked SQLite is < 3.46; >= 3.46 computes them",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.ENGINE_LENIENCY",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-08-06",\n        "source_mentions": [\n          {\n            "line": 15,\n            "path": "tests/expressions/cross_backend/test_datetime_enrichment.py"\n          },\n          {\n            "line": 21,\n            "path": "tests/expressions/cross_backend/test_parameter_sensitivity.py"\n          },\n          {\n            "line": 23,\n            "path": "tests/expressions/cross_backend/test_temporal_advanced.py"\n          }\n        ],\n        "summary": "SQLite < 3.46 lacks time-shift modifiers, so calendar arithmetic (add_days/add_months/month_end/days_in_month/combined offsets) is unavailable on ibis-sqlite; SQLite >= 3.46 supports them (environment-conditional \xe2\x80\x94 the mark is applied only below 3.46)",\n        "upstream_ref": null,\n        "workaround": "Upgrade SQLite to >= 3.46, or use another backend for calendar arithmetic"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[36].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    },\n    {\n      "legacy_provenance": "IB-DT-14",\n      "qualified_key": "QualifiedManifestationKey(scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name=\'ibis-sqlite\')), local=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'ts\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-02-15\'), CaptureValue(tag=\'text\', value=\'2024-03-15\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression SQLite<3.46\'),),))))",\n      "disposition": "narrowed_applicability",\n      "reason": "The selected SQLite scenario is an unmarked passing control in the retained operational run. Preserve the historical older-engine claim without asserting a release interval or expected failure in this observed environment.",\n      "evidence_entry": "dt14_days_in_month",\n      "prior_complete_payload": {\n        "backends": [\n          "ibis-sqlite"\n        ],\n        "capability_candidates_not_semantic_joins": [],\n        "classification_owner": "item100",\n        "declared_scope_obligations": [\n          {\n            "date": "2026-09-15",\n            "direct_probe": "unverified except explicitly recorded behavioral cohort",\n            "operational_binding": "source incidence only; variant recovery required",\n            "owner": "item100",\n            "scope": "ibis-sqlite"\n          }\n        ],\n        "id": "IB-DT-14",\n        "impact": "calendar/offset arithmetic raises on ibis-sqlite when the linked SQLite is < 3.46; >= 3.46 computes them",\n        "kind": "mountainash.core.capabilities.schema.DivergenceKind.ENGINE_LENIENCY",\n        "operation_keys": [\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH",\n          "mountainash.expressions.core.expression_system.function_keys.enums.FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY"\n        ],\n        "original_record_status": "Captured source declaration; prose claims are not automatically fresh observations.",\n        "probe_status": "unverified; no per-scope direct-probe binding inferred from ID mentions",\n        "reachability": "source-test-route",\n        "since": "2026-08-06",\n        "source_mentions": [\n          {\n            "line": 15,\n            "path": "tests/expressions/cross_backend/test_datetime_enrichment.py"\n          },\n          {\n            "line": 21,\n            "path": "tests/expressions/cross_backend/test_parameter_sensitivity.py"\n          },\n          {\n            "line": 23,\n            "path": "tests/expressions/cross_backend/test_temporal_advanced.py"\n          }\n        ],\n        "summary": "SQLite < 3.46 lacks time-shift modifiers, so calendar arithmetic (add_days/add_months/month_end/days_in_month/combined offsets) is unavailable on ibis-sqlite; SQLite >= 3.46 supports them (environment-conditional \xe2\x80\x94 the mark is applied only below 3.46)",\n        "upstream_ref": null,\n        "workaround": "Upgrade SQLite to >= 3.46, or use another backend for calendar arithmetic"\n      },\n      "prior_payload_source": {\n        "repository": "mountainash-central",\n        "path": "04.planning/mountainash/superpowers/plans/2026-09-15-capability-manifestation-migration.json",\n        "entry": "cases[36].prior_complete_payload",\n        "sha256": "93c61c25de0bfca2181775fa0ac014b35c5dbfba9b0f96456952ad5a5487779c"\n      }\n    }\n  ],\n  "positive_controls": [\n    {\n      "nodeid": "tests/expressions/cross_backend/test_temporal_advanced.py::TestFlexibleOffsetBy::test_offset_add_days_and_hours[ibis-sqlite]",\n      "claim": "DivergenceManifestation(key=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'timestamp\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-01-01T10:00\'), CaptureValue(tag=\'text\', value=\'2024-06-15T14:30\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression offset=1d2h SQLite<3.46\'),),))), kind=DivergenceKind.ENGINE_LENIENCY, expected=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-01-02T12:00\'), CaptureValue(tag=\'text\', value=\'2024-06-16T16:30\'),)),),)), observed=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'text\', value=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\'),),)), impact=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\', since=\'2026-08-06\', workaround=\'Upgrade SQLite to >= 3.46, or use another backend\', issue=None)",\n      "outcome": {\n        "nodeid": "tests/expressions/cross_backend/test_temporal_advanced.py::TestFlexibleOffsetBy::test_offset_add_days_and_hours[ibis-sqlite]",\n        "path": "tests/expressions/cross_backend/test_temporal_advanced.py",\n        "function": "TestFlexibleOffsetBy.test_offset_add_days_and_hours",\n        "parameters": {\n          "backend_name": "\'ibis-sqlite\'"\n        },\n        "phase": "call",\n        "outcome": "passed",\n        "expected_failure": null,\n        "error": null,\n        "detail": null\n      }\n    },\n    {\n      "nodeid": "tests/expressions/cross_backend/test_datetime_enrichment.py::TestMonthEnd::test_month_end[ibis-sqlite]",\n      "claim": "DivergenceManifestation(key=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'ts\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-02-15\'), CaptureValue(tag=\'text\', value=\'2024-03-15\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression SQLite<3.46\'),),))), kind=DivergenceKind.ENGINE_LENIENCY, expected=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'29\'), CaptureValue(tag=\'integer\', value=\'31\'),)),),)), observed=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'text\', value=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\'),),)), impact=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\', since=\'2026-08-06\', workaround=\'Upgrade SQLite to >= 3.46, or use another backend\', issue=None)",\n      "outcome": {\n        "nodeid": "tests/expressions/cross_backend/test_datetime_enrichment.py::TestMonthEnd::test_month_end[ibis-sqlite]",\n        "path": "tests/expressions/cross_backend/test_datetime_enrichment.py",\n        "function": "TestMonthEnd.test_month_end",\n        "parameters": {\n          "backend_name": "\'ibis-sqlite\'"\n        },\n        "phase": "call",\n        "outcome": "passed",\n        "expected_failure": null,\n        "error": null,\n        "detail": null\n      }\n    },\n    {\n      "nodeid": "tests/expressions/cross_backend/test_datetime_enrichment.py::TestDaysInMonth::test_days_in_month[ibis-sqlite]",\n      "claim": "DivergenceManifestation(key=ManifestationKey(target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH), scenario=Scenario(arguments=(), options=(), input_schema=(), input_data=((\'values\', CaptureValue(tag=\'mapping\', value=((\'ts\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'text\', value=\'2024-02-15\'), CaptureValue(tag=\'text\', value=\'2024-03-15\'),)),),)),),), execution=((\'shape\', CaptureValue(tag=\'text\', value=\'collect expression SQLite<3.46\'),),))), kind=DivergenceKind.ENGINE_LENIENCY, expected=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'sequence\', value=(CaptureValue(tag=\'integer\', value=\'29\'), CaptureValue(tag=\'integer\', value=\'31\'),)),),)), observed=CaptureValue(tag=\'mapping\', value=((\'historical_source_claim\', CaptureValue(tag=\'text\', value=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\'),),)), impact=\'calendar/offset arithmetic raises on ibis-sqlite below SQLite 3.46\', since=\'2026-08-06\', workaround=\'Upgrade SQLite to >= 3.46, or use another backend\', issue=None)",\n      "outcome": {\n        "nodeid": "tests/expressions/cross_backend/test_datetime_enrichment.py::TestDaysInMonth::test_days_in_month[ibis-sqlite]",\n        "path": "tests/expressions/cross_backend/test_datetime_enrichment.py",\n        "function": "TestDaysInMonth.test_days_in_month",\n        "parameters": {\n          "backend_name": "\'ibis-sqlite\'"\n        },\n        "phase": "call",\n        "outcome": "passed",\n        "expected_failure": null,\n        "error": null,\n        "detail": null\n      }\n    }\n  ]\n}',
                ),
                reference_context=(),
            ),
            disposition=ChangeDisposition.INCORRECT_DECLARATION,
            recorded_at="2026-09-17",
            reason="The retained public and direct-native SQLite division observation yields [2.5, 3.5], not integer division. The existing cross-backend division contract remains positive; no version interval is inferred.",
            successors=(),
            evidence_refs=(
                CapturedAddress(
                    repository="mountainash-central",
                    path="04.planning/mountainash/superpowers/plans/2026-09-15-corrected-manifestation-observations.json",
                    entry="integer_division",
                    revision=None,
                    artifact=b'{\n  "integer_division": {\n    "legacy_provenance": "IB-MATH-04",\n    "input": {\n      "left": [\n        5,\n        7\n      ],\n      "right": [\n        2,\n        2\n      ]\n    },\n    "public": {\n      "polars": [\n        2.5,\n        3.5\n      ],\n      "ibis-sqlite": [\n        2.5,\n        3.5\n      ]\n    },\n    "direct_native": {\n      "polars": [\n        2.5,\n        3.5\n      ],\n      "ibis-sqlite": [\n        2.5,\n        3.5\n      ]\n    },\n    "positive_contract": "tests/expressions/cross_backend/test_arithmetic.py::TestBasicArithmetic::test_division",\n    "verification": "9 passed --ma-backend-scope=full",\n    "source": "from pathlib import Path\\nimport sys\\nsys.path.insert(0, str(Path.cwd() / \\"tests\\"))\\nimport mountainash as ma\\nfrom fixtures.backend_helpers import BackendDataFrameFactory\\n\\nfor provider in (\\"polars\\", \\"ibis-sqlite\\"):\\n    frame = BackendDataFrameFactory.create({\\"left\\": [5, 7], \\"right\\": [2, 2]}, provider)\\n    public = ma.relation(frame).select((ma.col(\\"left\\") / ma.col(\\"right\\")).alias(\\"result\\")).to_dict()[\\"result\\"]\\n    if provider == \\"ibis-sqlite\\":\\n        native = frame.select((frame.left / frame.right).name(\\"result\\")).execute()[\\"result\\"].tolist()\\n    else:\\n        import polars as pl\\n        native = frame.select((pl.col(\\"left\\") / pl.col(\\"right\\")).alias(\\"result\\")).get_column(\\"result\\").to_list()\\n    print(provider, \\"public\\", public, \\"native\\", native)\\n    assert public == native\\n",\n    "recovery_correction": "Retained source recovery incorrectly described divisors as non-integral; actual fixture uses integers and fractional expected values."\n  },\n  "today_type": {\n    "legacy_provenance": "IB-DT-09 TODAY portion only",\n    "providers": [\n      "polars",\n      "ibis-duckdb",\n      "ibis-polars",\n      "ibis-sqlite"\n    ],\n    "compiled_native_types": [\n      "Date",\n      "date",\n      "date",\n      "date"\n    ],\n    "materialized_dtype": "Date",\n    "python_type": "datetime.date",\n    "layer": "public compilation/materialization, not independent native",\n    "source": "from pathlib import Path\\nimport sys\\nsys.path.insert(0, str(Path.cwd() / \\"tests\\"))\\nimport mountainash as ma\\nfrom fixtures.backend_helpers import BackendDataFrameFactory\\n\\nfor provider in (\\"polars\\", \\"ibis-duckdb\\", \\"ibis-polars\\", \\"ibis-sqlite\\"):\\n    frame = BackendDataFrameFactory.create({\\"a\\": [1]}, provider)\\n    native = ma.today().compile(frame)\\n    result = ma.relation(frame).with_columns(ma.today().alias(\\"day\\")).to_polars()\\n    value = result[\\"day\\"][0]\\n    native_type = str(native.type()) if provider.startswith(\\"ibis\\") else str(result.schema[\\"day\\"])\\n    print(provider, \\"compiled native type\\", native_type, \\"materialized dtype\\", str(result.schema[\\"day\\"]), \\"Python type\\", type(value).__module__ + \\".\\" + type(value).__qualname__)\\n",\n    "remaining": "NOW candidate unchanged; type-specific positive scenario still required"\n  },\n  "environment": {\n    "ibis-framework": "12.0.0",\n    "polars": "1.44.2",\n    "sqlite_engine": "3.53.1"\n  },\n  "disposition": "Historical source claims retained; corrected scoped portions require AssertionChange during cutover. No active record published yet."\n}\n',
                ),
            ),
            fixed_versions=None,
        ),
    ),
)
