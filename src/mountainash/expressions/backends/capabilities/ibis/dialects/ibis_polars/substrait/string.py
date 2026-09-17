"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

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
)
