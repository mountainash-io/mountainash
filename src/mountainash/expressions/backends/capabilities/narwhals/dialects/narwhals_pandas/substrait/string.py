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
from mountainash.core.capabilities.schema import Boundary
from mountainash.core.capabilities.schema import Enforcement
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
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
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
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
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
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored",
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
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="group",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH, subject="group"),
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
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE,
                subject="char_set",
                selector=Selector(kind="exact", value="ASCII_ONLY"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.TITLE,
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
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.TITLE,
                subject="char_set",
                selector=Selector(kind="exact", value="ASCII_ONLY"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP,
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
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP,
                subject="char_set",
                selector=Selector(kind="exact", value="ASCII_ONLY"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
                subject="padding",
                selector=Selector(kind="exact", value="RIGHT"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="center is a no-op on this backend, so padding cannot be honored",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
                subject="padding",
                selector=Selector(kind="exact", value="LEFT"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="center is a no-op on this backend, so padding cannot be honored",
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
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.SPLIT, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-13",
            message="narwhals-pandas' str.split() requires a pyarrow-backed pandas series (raises TypeError: 'This operation requires a pyarrow-backed series') against the plain numpy-backed storage most pandas DataFrames use; a pyarrow-backed pandas DataFrame (e.g. via .convert_dtypes(dtype_backend='pyarrow')) works correctly, as does narwhals-polars for any storage",
            workaround="Use a pyarrow-backed pandas DataFrame, narwhals-polars, Polars, or Ibis for string_split",
            issue="NW-STR-22",
            boundary=Boundary.MATERIALIZE,
            native_errors=(TypeError,),
            probe_exempt="whole-op materialize-time storage residue (narwhals-pandas pyarrow-backed-series requirement) -- storage-dependent, not an intrinsic dialect-wide gap: a pyarrow-backed pandas DataFrame genuinely works, so this cannot be a build-time GATE (mirrors NW-LIST-01's identical pyarrow-storage-dependent CONTAINS/T_CONTAINS pattern)",
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
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
                            CaptureValue(tag="text", value="x"),
                        ),
                    ),
                    options=(
                        (
                            "case_sensitivity",
                            CaptureValue(tag="text", value="CASE_INSENSITIVE_ASCII"),
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
                                                    CaptureValue(tag="bool", value="true"),
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
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="text", value="anchor"),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue.of({"claim_status": "retained_native_observation", "values": [None, False]}),
            observed=CaptureValue.of({"claim_status": "retained_native_observation", "values": [False, False]}),
            impact="A null input row yields False rather than propagating null.",
            since="2026-08-12",
            workaround="Use a polars, narwhals-polars, narwhals-lazy, or ibis backend where null must propagate.",
            issue=None,
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
                            CaptureValue(tag="text", value="x"),
                        ),
                    ),
                    options=(
                        (
                            "case_sensitivity",
                            CaptureValue(tag="text", value="CASE_INSENSITIVE_ASCII"),
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
                                                    CaptureValue(tag="bool", value="true"),
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
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="text", value="anchor"),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_retained_observation"),
                    ),
                    (
                        "evidence_address",
                        CaptureValue(
                            tag="text",
                            value="central/04.planning/mountainash/superpowers/plans/2026-09-15-null-string-manifestation-observation.json#observations.polars",
                        ),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="retained Polars public/direct-Narwhals-adapter result"),
                    ),
                    (
                        "values",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="null", value=""),
                                CaptureValue(tag="bool", value="false"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_retained_observation"),
                    ),
                    (
                        "evidence_address",
                        CaptureValue(
                            tag="text",
                            value="central/04.planning/mountainash/superpowers/plans/2026-09-15-null-string-manifestation-observation.json#observations.narwhals-pandas",
                        ),
                    ),
                    (
                        "statement",
                        CaptureValue(
                            tag="text", value="retained narwhals-pandas public/direct-Narwhals-adapter result"
                        ),
                    ),
                    (
                        "values",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="false"),
                            ),
                        ),
                    ),
                ),
            ),
            impact="A null input row yields False rather than propagating null.",
            since="2026-08-12",
            workaround="Use a polars, narwhals-polars, narwhals-lazy, or ibis backend where null must propagate.",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP),
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
                    ),
                    options=(),
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
                                                CaptureValue(tag="text", value="ße"),
                                                CaptureValue(tag="text", value="ﬃle"),
                                                CaptureValue(tag="text", value="hello world"),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_retained_observation"),
                    ),
                    (
                        "evidence_address",
                        CaptureValue(
                            tag="text",
                            value="central/04.planning/mountainash/superpowers/plans/2026-09-15-unicode-manifestation-observation.json#direct_native.polars.result",
                        ),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="retained direct Polars titlecase result"),
                    ),
                    (
                        "values",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="SSe"),
                                CaptureValue(tag="text", value="FFIle"),
                                CaptureValue(tag="text", value="Hello World"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_retained_observation"),
                    ),
                    (
                        "evidence_address",
                        CaptureValue(
                            tag="text",
                            value="central/04.planning/mountainash/superpowers/plans/2026-09-15-unicode-manifestation-observation.json#public",
                        ),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="retained public narwhals-pandas title/initcap result"),
                    ),
                    (
                        "values",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="ẞe"),
                                CaptureValue(tag="text", value="ﬃle"),
                                CaptureValue(tag="text", value="Hello World"),
                            ),
                        ),
                    ),
                ),
            ),
            impact="initcap() differs from Polars on sharp-S and ligature inputs.",
            since="2026-07-29",
            workaround="Use polars or narwhals-polars for exact Polars non-ASCII titlecasing.",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM),
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
                    ),
                    options=(),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
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
                                        "s",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="  hello  "),
                                                CaptureValue(tag="text", value=" world"),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="leading-only alias trim is expected"),
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
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="directional trim strips both sides"),
                    ),
                ),
            ),
            impact="Directional trimming over-strips both ends.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for directional trimming.",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM),
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
                    ),
                    options=(),
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
                                                CaptureValue(tag="text", value="  hello  "),
                                                CaptureValue(tag="text", value="  world  "),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="leading-only trim is expected"),
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
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="directional trim strips both sides"),
                    ),
                ),
            ),
            impact="Directional trimming over-strips both ends.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for directional trimming.",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT),
                scenario=Scenario(
                    arguments=(
                        (
                            "count",
                            CaptureValue(tag="integer", value="2"),
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
                                                CaptureValue(tag="text", value="ab"),
                                                CaptureValue(tag="text", value="cd"),
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
                        CaptureValue(tag="text", value="NW-STR-17"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="repeat count 2 differs from count 3"),
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
                        CaptureValue(tag="text", value="NW-STR-17"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="no repeat translation is wired"),
                    ),
                ),
            ),
            impact="str.repeat() raises on the marked providers.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for str.repeat().",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT),
                scenario=Scenario(
                    arguments=(
                        (
                            "count",
                            CaptureValue(tag="integer", value="3"),
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
                                                CaptureValue(tag="text", value="ab"),
                                                CaptureValue(tag="text", value="cd"),
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
                        CaptureValue(tag="text", value="NW-STR-17"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="repeat count 3 differs from count 2"),
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
                        CaptureValue(tag="text", value="NW-STR-17"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="no repeat translation is wired"),
                    ),
                ),
            ),
            impact="str.repeat() raises on the marked providers.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for str.repeat().",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE),
                scenario=Scenario(
                    arguments=(
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
                            CaptureValue(tag="integer", value="1"),
                        ),
                        (
                            "replacement",
                            CaptureValue(tag="text", value="X"),
                        ),
                        (
                            "start",
                            CaptureValue(tag="integer", value="1"),
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
                                        CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="hello"),)),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-18"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="length 1 differs from length 3"),
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
                        CaptureValue(tag="text", value="NW-STR-18"),
                    ),
                    (
                        "statement",
                        CaptureValue(
                            tag="text", value="slice arguments do not reach the backend and input is unchanged"
                        ),
                    ),
                ),
            ),
            impact="str.replace_slice() returns input unchanged.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for str.replace_slice().",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE),
                scenario=Scenario(
                    arguments=(
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
                            CaptureValue(tag="integer", value="3"),
                        ),
                        (
                            "replacement",
                            CaptureValue(tag="text", value="X"),
                        ),
                        (
                            "start",
                            CaptureValue(tag="integer", value="1"),
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
                                        CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="hello"),)),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-18"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="length 3 differs from length 1"),
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
                        CaptureValue(tag="text", value="NW-STR-18"),
                    ),
                    (
                        "statement",
                        CaptureValue(
                            tag="text", value="slice arguments do not reach the backend and input is unchanged"
                        ),
                    ),
                ),
            ),
            impact="str.replace_slice() returns input unchanged.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for str.replace_slice().",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE),
                scenario=Scenario(
                    arguments=(
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
                            CaptureValue(tag="integer", value="3"),
                        ),
                        (
                            "replacement",
                            CaptureValue(tag="text", value="XY"),
                        ),
                        (
                            "start",
                            CaptureValue(tag="integer", value="1"),
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
                                                CaptureValue(tag="text", value="hello"),
                                                CaptureValue(tag="text", value="world"),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-18"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="replacement changes the input"),
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
                        CaptureValue(tag="text", value="NW-STR-18"),
                    ),
                    (
                        "statement",
                        CaptureValue(
                            tag="text", value="slice arguments do not reach the backend and input is unchanged"
                        ),
                    ),
                ),
            ),
            impact="str.replace_slice() returns input unchanged.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for str.replace_slice().",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM),
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
                    ),
                    options=(),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
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
                                        "s",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="  hello  "),
                                                CaptureValue(tag="text", value="world "),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="trailing-only alias trim is expected"),
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
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="directional trim strips both sides"),
                    ),
                ),
            ),
            impact="Directional trimming over-strips both ends.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for directional trimming.",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM),
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
                    ),
                    options=(),
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
                                                CaptureValue(tag="text", value="  hello  "),
                                                CaptureValue(tag="text", value="  world  "),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="trailing-only trim is expected"),
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
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="directional trim strips both sides"),
                    ),
                ),
            ),
            impact="Directional trimming over-strips both ends.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for directional trimming.",
            issue=None,
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
                            CaptureValue(tag="text", value="x"),
                        ),
                    ),
                    options=(
                        (
                            "case_sensitivity",
                            CaptureValue(tag="text", value="CASE_INSENSITIVE_ASCII"),
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
                                                    CaptureValue(tag="bool", value="true"),
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
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="text", value="anchor"),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_retained_observation"),
                    ),
                    (
                        "evidence_address",
                        CaptureValue(
                            tag="text",
                            value="central/04.planning/mountainash/superpowers/plans/2026-09-15-null-string-manifestation-observation.json#observations.polars",
                        ),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="retained Polars public/direct-Narwhals-adapter result"),
                    ),
                    (
                        "values",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="null", value=""),
                                CaptureValue(tag="bool", value="false"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_retained_observation"),
                    ),
                    (
                        "evidence_address",
                        CaptureValue(
                            tag="text",
                            value="central/04.planning/mountainash/superpowers/plans/2026-09-15-null-string-manifestation-observation.json#observations.narwhals-pandas",
                        ),
                    ),
                    (
                        "statement",
                        CaptureValue(
                            tag="text", value="retained narwhals-pandas public/direct-Narwhals-adapter result"
                        ),
                    ),
                    (
                        "values",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="false"),
                            ),
                        ),
                    ),
                ),
            ),
            impact="A null input row yields False rather than propagating null.",
            since="2026-08-12",
            workaround="Use a polars, narwhals-polars, narwhals-lazy, or ibis backend where null must propagate.",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.TITLE),
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
                    ),
                    options=(),
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
                                                CaptureValue(tag="text", value="ße"),
                                                CaptureValue(tag="text", value="ﬃle"),
                                                CaptureValue(tag="text", value="hello world"),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_retained_observation"),
                    ),
                    (
                        "evidence_address",
                        CaptureValue(
                            tag="text",
                            value="central/04.planning/mountainash/superpowers/plans/2026-09-15-unicode-manifestation-observation.json#direct_native.polars.result",
                        ),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="retained direct Polars titlecase result"),
                    ),
                    (
                        "values",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="SSe"),
                                CaptureValue(tag="text", value="FFIle"),
                                CaptureValue(tag="text", value="Hello World"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_retained_observation"),
                    ),
                    (
                        "evidence_address",
                        CaptureValue(
                            tag="text",
                            value="central/04.planning/mountainash/superpowers/plans/2026-09-15-unicode-manifestation-observation.json#public",
                        ),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="retained public narwhals-pandas title/initcap result"),
                    ),
                    (
                        "values",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="ẞe"),
                                CaptureValue(tag="text", value="ﬃle"),
                                CaptureValue(tag="text", value="Hello World"),
                            ),
                        ),
                    ),
                ),
            ),
            impact="title() differs from Polars on sharp-S and ligature inputs.",
            since="2026-07-29",
            workaround="Use polars or narwhals-polars for exact Polars non-ASCII titlecasing.",
            issue=None,
        ),
    ),
)
