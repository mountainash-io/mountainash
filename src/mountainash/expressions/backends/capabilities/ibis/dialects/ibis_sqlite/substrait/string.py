"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="ibis-sqlite's native LOWER()/UPPER() are ASCII-only (no ICU extension loaded); CASE_INSENSITIVE's Unicode-aware-lowercasing contract (e.g. Kelvin Sign U+212A -> 'k') is unavailable on this dialect alone in the Ibis family — gated unconditionally for every ibis-sqlite connection and every input (including purely-ASCII input, which SQLite's native LOWER() handles correctly, and any caller-supplied connection with a custom Unicode-aware LOWER()/UPPER() override loaded onto it) because the capability fact is keyed on (backend, dialect), a static identity, with no visibility into a specific connection's actual loaded extensions or a specific call's runtime string content",
            workaround="Use CASE_INSENSITIVE_ASCII instead if ASCII-only folding is sufficient (genuinely honored on ibis-sqlite via native translate()); otherwise Unicode-normalize both operands in Python (e.g. str.lower()) and reissue the comparison as CASE_SENSITIVE (NOT CASE_INSENSITIVE — this dialect-scoped gate is unconditional and still rejects CASE_INSENSITIVE even after preprocessing), or run this expression against a different Ibis dialect (ibis-duckdb) instead of ibis-sqlite",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="ibis-sqlite's native LOWER()/UPPER() are ASCII-only (no ICU extension loaded); CASE_INSENSITIVE's Unicode-aware-lowercasing contract (e.g. Kelvin Sign U+212A -> 'k') is unavailable on this dialect alone in the Ibis family — gated unconditionally for every ibis-sqlite connection and every input (including purely-ASCII input, which SQLite's native LOWER() handles correctly, and any caller-supplied connection with a custom Unicode-aware LOWER()/UPPER() override loaded onto it) because the capability fact is keyed on (backend, dialect), a static identity, with no visibility into a specific connection's actual loaded extensions or a specific call's runtime string content",
            workaround="Use CASE_INSENSITIVE_ASCII instead if ASCII-only folding is sufficient (genuinely honored on ibis-sqlite via native translate()); otherwise Unicode-normalize both operands in Python (e.g. str.lower()) and reissue the comparison as CASE_SENSITIVE (NOT CASE_INSENSITIVE — this dialect-scoped gate is unconditional and still rejects CASE_INSENSITIVE even after preprocessing), or run this expression against a different Ibis dialect (ibis-duckdb) instead of ibis-sqlite",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="ibis-sqlite's native LOWER()/UPPER() are ASCII-only (no ICU extension loaded); CASE_INSENSITIVE's Unicode-aware-lowercasing contract (e.g. Kelvin Sign U+212A -> 'k') is unavailable on this dialect alone in the Ibis family — gated unconditionally for every ibis-sqlite connection and every input (including purely-ASCII input, which SQLite's native LOWER() handles correctly, and any caller-supplied connection with a custom Unicode-aware LOWER()/UPPER() override loaded onto it) because the capability fact is keyed on (backend, dialect), a static identity, with no visibility into a specific connection's actual loaded extensions or a specific call's runtime string content",
            workaround="Use CASE_INSENSITIVE_ASCII instead if ASCII-only folding is sufficient (genuinely honored on ibis-sqlite via native translate()); otherwise Unicode-normalize both operands in Python (e.g. str.lower()) and reissue the comparison as CASE_SENSITIVE (NOT CASE_INSENSITIVE — this dialect-scoped gate is unconditional and still rejects CASE_INSENSITIVE even after preprocessing), or run this expression against a different Ibis dialect (ibis-duckdb) instead of ibis-sqlite",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-13",
            message="ibis-sqlite has no compilation rule for RegexSplit (OperationNotDefinedError) for any pattern, literal or dynamic; ibis-duckdb translates it to native SQL correctly and ibis-polars supports a literal pattern",
            workaround="Use ibis-duckdb, ibis-polars with a literal pattern, or a Polars backend for regex split",
            issue="IB-STR-12",
            layer=InformationLayer.NATIVE,
        ),
    ),
)
