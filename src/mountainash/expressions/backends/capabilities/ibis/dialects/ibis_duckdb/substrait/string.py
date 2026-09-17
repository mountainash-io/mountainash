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
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation",
            workaround="Lowercase the input and search operand explicitly before applying the case-sensitive operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation",
            workaround="Lowercase the input and search operand explicitly before applying the case-sensitive operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation",
            workaround="Lowercase the input and search operand explicitly before applying the case-sensitive operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation",
            workaround="Lowercase the input and search operand explicitly before applying the case-sensitive operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_DISABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_DISABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_DISABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_DISABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_DISABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_DISABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_ENABLED"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement this regexp flag's non-default Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="position",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH, subject="position"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied",
            probe_exempt="value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
                subject="position",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL, subject="position"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
            probe_exempt="value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
                subject="position",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS, subject="position"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
            probe_exempt="value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
                subject="position",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT, subject="position"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
            probe_exempt="value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="position",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE, subject="position"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied",
            probe_exempt="value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="occurrence",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH, subject="occurrence"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied",
            probe_exempt="value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
                subject="occurrence",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS, subject="occurrence"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
            probe_exempt="value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="occurrence",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE, subject="occurrence"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied",
            probe_exempt="value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
                subject="group",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL, subject="group"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
            probe_exempt="value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
                subject="char_set",
                selector=Selector(kind="exact", value="UTF8"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
                subject="char_set",
                selector=Selector(kind="exact", value="ASCII_ONLY"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER,
                subject="char_set",
                selector=Selector(kind="exact", value="UTF8"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER,
                subject="char_set",
                selector=Selector(kind="exact", value="ASCII_ONLY"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.SWAPCASE,
                subject="char_set",
                selector=Selector(kind="exact", value="UTF8"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.SWAPCASE,
                subject="char_set",
                selector=Selector(kind="exact", value="ASCII_ONLY"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE,
                subject="char_set",
                selector=Selector(kind="exact", value="UTF8"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE,
                subject="char_set",
                selector=Selector(kind="exact", value="ASCII_ONLY"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.TITLE,
                subject="char_set",
                selector=Selector(kind="exact", value="UTF8"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.TITLE,
                subject="char_set",
                selector=Selector(kind="exact", value="ASCII_ONLY"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP,
                subject="char_set",
                selector=Selector(kind="exact", value="UTF8"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP,
                subject="char_set",
                selector=Selector(kind="exact", value="ASCII_ONLY"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
                subject="padding",
                selector=Selector(kind="exact", value="RIGHT"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="RIGHT is the builder default, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="RIGHT is the builder default, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
                subject="padding",
                selector=Selector(kind="exact", value="LEFT"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement LEFT padding semantics for center",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
                subject="negative_start",
                selector=Selector(kind="exact", value="WRAP_FROM_END"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate",
            probe_exempt="The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
                subject="negative_start",
                selector=Selector(kind="exact", value="LEFT_OF_BEGINNING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement non-default negative_start semantics for substring",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
                subject="negative_start",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement non-default negative_start semantics for substring",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here)",
            workaround="Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here)",
            workaround="Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here)",
            workaround="Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here)",
            workaround="Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-12",
            message="The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics",
        ),
    ),
)
