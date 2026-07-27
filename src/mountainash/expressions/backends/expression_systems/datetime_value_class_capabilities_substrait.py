"""Import-safe IANA_TIMEZONE value-class capability declarations (Substrait ops).

Physically separate from the MA value-class module (substrait-vs-mountainash:
physical MA/Substrait separation is ENFORCED — never one mixed module).

Covers `assume_timezone` (Substrait scalar-datetime). `strftime` (also
Substrait) is honored on every fixture and value-agnostic, so it carries NO
fact. `local_timestamp` is unwired at the function-mapping layer and is deferred
to backlog item 62 (substrait-datetime-missing-ops).

Probe matrix — IANA_TIMEZONE on assume_timezone (representative slice
{UTC, Australia/Sydney, America/New_York, Pacific/Kiritimati}), all fixtures:

| op              | polars  | ibis (ibis-duckdb) | narwhals-polars | narwhals-pandas |
|-----------------|---------|--------------------|-----------------|-----------------|
| assume_timezone | honored | SILENTLY-WRONG     | SILENTLY-WRONG  | SILENTLY-WRONG  |

- polars attaches the timezone: the result is a tz-aware timestamp
  (`tzinfo=ZoneInfo(...)`).
- ibis + BOTH narwhals dialects SILENTLY DROP the timezone: the result is a
  naive timestamp (verified natively — ibis `datetime64[us]`, narwhals
  `Datetime(time_zone=None)`), i.e. `assume_timezone` is a no-op there. Per
  consistency-guarantees this must be DECLARED so the gate raises a clean
  `BackendCapabilityError` instead of returning a silently-wrong naive value.

The whole IANA_TIMEZONE class is unsupported on these backends (the tz arg is
ignored regardless of value), so a class fact — not per-value facts — is the
correct grain. Gate-domain == production-domain: the api-builder validates
`assume_timezone(timezone=...)` to exactly IANA_TIMEZONE (spec Section 3.2).

Family / dialect discipline: ibis family-default (dialect=None) + ibis-duckdb;
narwhals per-dialect only (narwhals-polars AND narwhals-pandas).
"""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    ValueClass,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME as FK_SUB_DT,
)

_SINCE = "2026-07-25"

_ASSUME_TZ_MSG = (
    "assume_timezone silently drops the timezone (returns a naive timestamp) — "
    "the tz argument is ignored; only polars attaches the timezone"
)


def _tz_fact(backend, dialect: str | None) -> CapabilityFact:
    return CapabilityFact(
        operation_key=FK_SUB_DT.ASSUME_TIMEZONE,
        param="timezone",
        value_class=ValueClass.IANA_TIMEZONE,
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        dialect=dialect,
        message=_ASSUME_TZ_MSG,
        since=_SINCE,
    )


_IBIS_FACTS = tuple(
    _tz_fact(CONST_BACKEND.IBIS, dialect) for dialect in (None, "ibis-duckdb")
)
_NARWHALS_FACTS = tuple(
    _tz_fact(CONST_BACKEND.NARWHALS, dialect)
    for dialect in ("narwhals-polars", "narwhals-pandas")
)

CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, _IBIS_FACTS)
CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, _NARWHALS_FACTS)
