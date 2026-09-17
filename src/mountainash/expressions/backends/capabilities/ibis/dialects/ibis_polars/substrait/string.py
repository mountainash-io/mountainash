"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import OperationTarget
from mountainash.core.capabilities.schema import Scenario

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="ibis-polars has no compilation rule for StringTranslate (OperationNotDefinedError); the ASCII-only fold CASE_INSENSITIVE_ASCII needs for contains/starts_with/ends_with is unavailable on this dialect, unlike ibis-duckdb/ibis-sqlite which both support .translate()",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="ibis-polars has no compilation rule for StringTranslate (OperationNotDefinedError); the ASCII-only fold CASE_INSENSITIVE_ASCII needs for contains/starts_with/ends_with is unavailable on this dialect, unlike ibis-duckdb/ibis-sqlite which both support .translate()",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="ibis-polars has no compilation rule for StringTranslate (OperationNotDefinedError); the ASCII-only fold CASE_INSENSITIVE_ASCII needs for contains/starts_with/ends_with is unavailable on this dialect, unlike ibis-duckdb/ibis-sqlite which both support .translate()",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE, subject="substring"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-08-12",
            message="ibis-polars compiles this to Polars' native str.replace()/str.replace_all(), which does not support a dynamic (column-valued) pattern argument (tracked upstream as PL-STR-01/PL-STR-02 for the raw polars backend; see backlog item 81)",
            workaround="Use a literal string pattern instead of a column reference",
            issue="PL-STR-02",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING, subject="substring"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-08-12",
            message="ibis-polars compiles this to Polars' native str.replace()/str.replace_all(), which does not support a dynamic (column-valued) pattern argument (tracked upstream as PL-STR-01/PL-STR-02 for the raw polars backend; see backlog item 81)",
            workaround="Use a literal string pattern instead of a column reference",
            issue="PL-STR-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE, subject="pattern"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-08-12",
            message="ibis-polars compiles this to Polars' native str.replace()/str.replace_all(), which does not support a dynamic (column-valued) pattern argument (tracked upstream as PL-STR-01/PL-STR-02 for the raw polars backend; see backlog item 81)",
            workaround="Use a literal string pattern instead of a column reference",
            issue="PL-STR-02",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="ibis-polars has no compilation rule for StringSQLLike (OperationNotDefinedError) for any pattern, literal or dynamic; ibis-duckdb/ibis-sqlite both translate LIKE to native SQL correctly",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend for LIKE patterns",
            issue="IB-STR-06",
            probe_exempt="whole-op gate on a dialect-scoped WILDCARD_PARAM fact; cannot be keyed on an OpSpec param — verified by the dedicated cross-backend gate test in test_pattern.py (TestLikeIbisPolarsGate) and the native-bypass self-healing probe in test_op_level_gate_probes.py (test_like_ibis_polars_native_still_broken)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH, subject="pattern"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-08-12",
            message="ibis-polars compiles this to Polars' native columnar-argument path, which raises Ibis's own UnsupportedArgumentError for a dynamic (column-valued) argument; a literal value works fine",
            workaround="Use a literal string pattern/separator instead of a column reference",
            issue="IB-STR-09",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.SPLIT, subject="separator"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-08-12",
            message="ibis-polars compiles this to Polars' native columnar-argument path, which raises Ibis's own UnsupportedArgumentError for a dynamic (column-valued) argument; a literal value works fine",
            workaround="Use a literal string pattern/separator instead of a column reference",
            issue="IB-STR-10",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT, subject="pattern"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-08-13",
            message="ibis-polars compiles regexp_string_split to Polars' native re_split, which raises Ibis's own IbisError for a dynamic (column-valued) pattern; a literal pattern works fine",
            workaround="Use a literal string pattern instead of a column reference",
            issue="IB-STR-13",
        ),
    ),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER),
                scenario=Scenario(
                    arguments=(
                        (
                            "character",
                            CaptureValue(tag="text", value="*"),
                        ),
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="val"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "length",
                            CaptureValue(tag="integer", value="5"),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="hi"),)),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="MA-STR-02"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="center width 5 computes"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="MA-STR-02"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="marked providers reject center"),
                    ),
                ),
            ),
            impact="str.center() raises on the marked providers.",
            since="2026-08-06",
            workaround="Use a polars or ibis SQL backend for str.center().",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER),
                scenario=Scenario(
                    arguments=(
                        (
                            "character",
                            CaptureValue(tag="text", value="*"),
                        ),
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="val"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "length",
                            CaptureValue(tag="integer", value="7"),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="hi"),
                                                CaptureValue(tag="text", value="hey"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="MA-STR-02"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="center width 7 computes"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="MA-STR-02"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="marked providers reject center"),
                    ),
                ),
            ),
            impact="str.center() raises on the marked providers.",
            since="2026-08-06",
            workaround="Use a polars or ibis SQL backend for str.center().",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER),
                scenario=Scenario(
                    arguments=(
                        (
                            "character",
                            CaptureValue(tag="text", value="*"),
                        ),
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="val"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "length",
                            CaptureValue(tag="integer", value="9"),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="hi"),)),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="MA-STR-02"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="center width 9 computes"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="MA-STR-02"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="marked providers reject center"),
                    ),
                ),
            ),
            impact="str.center() raises on the marked providers.",
            since="2026-08-06",
            workaround="Use a polars or ibis SQL backend for str.center().",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS),
                scenario=Scenario(
                    arguments=(
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="s"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "substring",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="needle"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "case_sensitivity",
                            CaptureValue(tag="text", value="CASE_SENSITIVE"),
                        ),
                    ),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "needle",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "s",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "needle",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="pie"),
                                                CaptureValue(tag="text", value="split"),
                                                CaptureValue(tag="text", value="XX"),
                                                CaptureValue(tag="text", value="dat"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "s",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="apple pie"),
                                                CaptureValue(tag="text", value="banana split"),
                                                CaptureValue(tag="text", value="cherry"),
                                                CaptureValue(tag="text", value="date"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="MA-STR-01"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="columnar contains computes"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="MA-STR-01"),
                    ),
                    (
                        "statement",
                        CaptureValue(
                            tag="text",
                            value="pandas raises enriched BackendCapabilityError; ibis-polars raises UnsupportedArgumentError",
                        ),
                    ),
                ),
            ),
            impact="Columnar literal contains raises on pandas and ibis-polars.",
            since="2026-08-06",
            workaround="Use a polars or ibis SQL backend for columnar substring patterns.",
            issue="MA-STR-01",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS),
                scenario=Scenario(
                    arguments=(
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="text"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "substring",
                            CaptureValue(tag="text", value="foo.bar"),
                        ),
                    ),
                    options=(
                        (
                            "case_sensitivity",
                            CaptureValue(tag="text", value="CASE_INSENSITIVE"),
                        ),
                    ),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="Hello World"),
                                                CaptureValue(tag="text", value="HELLO WORLD"),
                                                CaptureValue(tag="text", value="hello world"),
                                                CaptureValue(tag="text", value="Goodbye"),
                                                CaptureValue(tag="text", value="foo.bar"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="IB-STR-11"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="case-insensitive literal contains computes"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="IB-STR-11"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="ibis-polars raises UnsupportedArgumentError"),
                    ),
                ),
            ),
            impact="Case-insensitive matching raises on ibis-polars.",
            since="2026-08-06",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend.",
            issue="IB-STR-11",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS),
                scenario=Scenario(
                    arguments=(
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="text"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "substring",
                            CaptureValue(tag="text", value="hello"),
                        ),
                    ),
                    options=(
                        (
                            "case_sensitivity",
                            CaptureValue(tag="text", value="CASE_INSENSITIVE"),
                        ),
                    ),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="Hello World"),
                                                CaptureValue(tag="text", value="HELLO WORLD"),
                                                CaptureValue(tag="text", value="hello world"),
                                                CaptureValue(tag="text", value="Goodbye"),
                                                CaptureValue(tag="text", value="foo.bar"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="IB-STR-11"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="case-insensitive contains computes"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="IB-STR-11"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="ibis-polars raises UnsupportedArgumentError"),
                    ),
                ),
            ),
            impact="Case-insensitive matching raises on ibis-polars.",
            since="2026-08-06",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend.",
            issue="IB-STR-11",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH),
                scenario=Scenario(
                    arguments=(
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="text"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "substring",
                            CaptureValue(tag="text", value="world"),
                        ),
                    ),
                    options=(
                        (
                            "case_sensitivity",
                            CaptureValue(tag="text", value="CASE_INSENSITIVE"),
                        ),
                    ),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="Hello World"),
                                                CaptureValue(tag="text", value="HELLO WORLD"),
                                                CaptureValue(tag="text", value="hello world"),
                                                CaptureValue(tag="text", value="Goodbye"),
                                                CaptureValue(tag="text", value="foo.bar"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="IB-STR-11"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="case-insensitive ends_with computes"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="IB-STR-11"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="ibis-polars raises UnsupportedArgumentError"),
                    ),
                ),
            ),
            impact="Case-insensitive matching raises on ibis-polars.",
            since="2026-08-06",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend.",
            issue="IB-STR-11",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH),
                scenario=Scenario(
                    arguments=(
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="text"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "substring",
                            CaptureValue(tag="text", value="hello"),
                        ),
                    ),
                    options=(
                        (
                            "case_sensitivity",
                            CaptureValue(tag="text", value="CASE_INSENSITIVE"),
                        ),
                    ),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="Hello World"),
                                                CaptureValue(tag="text", value="HELLO WORLD"),
                                                CaptureValue(tag="text", value="hello world"),
                                                CaptureValue(tag="text", value="Goodbye"),
                                                CaptureValue(tag="text", value="foo.bar"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="IB-STR-11"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="case-insensitive starts_with computes"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="IB-STR-11"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="ibis-polars raises UnsupportedArgumentError"),
                    ),
                ),
            ),
            impact="Case-insensitive matching raises on ibis-polars.",
            since="2026-08-06",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend.",
            issue="IB-STR-11",
        ),
    ),
)
