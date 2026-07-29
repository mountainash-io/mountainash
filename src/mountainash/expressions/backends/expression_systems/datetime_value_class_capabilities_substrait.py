"""Import-safe IANA_TIMEZONE value-class capability declarations (Substrait ops).

Physically separate from the MA value-class module (substrait-vs-mountainash:
physical MA/Substrait separation is ENFORCED — never one mixed module).

Covers `assume_timezone` and `local_timestamp` (Substrait scalar-datetime). `strftime` (also
Substrait) is honored on every fixture and value-agnostic, so it carries NO
fact.

Probe matrix — IANA_TIMEZONE on assume_timezone and local_timestamp (representative slice
{UTC, Australia/Sydney, America/New_York, Pacific/Kiritimati}), all fixtures:

| op              | polars  | ibis (ibis-duckdb) | narwhals-polars | narwhals-pandas |
|-----------------|---------|--------------------|-----------------|-----------------|
| assume_timezone | honored | SILENTLY-WRONG     | SILENTLY-WRONG  | SILENTLY-WRONG  |
| local_timestamp | honored | SILENTLY-WRONG     | honored         | honored         |

- polars attaches the timezone: the result is a tz-aware timestamp
  (`tzinfo=ZoneInfo(...)`).
- ibis + BOTH narwhals dialects SILENTLY DROP the timezone on assume_timezone: the result is a
  naive timestamp (verified natively — ibis `datetime64[us]`, narwhals
  `Datetime(time_zone=None)`), i.e. `assume_timezone` is a no-op there. Per
  consistency-guarantees this must be DECLARED so the gate raises a clean
  `BackendCapabilityError` instead of returning a silently-wrong naive value.
- ibis returns UTC wall clock on local_timestamp instead of converting to target zone.

The whole IANA_TIMEZONE class is unsupported for assume_timezone/local_timestamp on ibis
(the tz arg is ignored regardless of value), so a class fact — not per-value facts — is the
correct grain. Gate-domain == production-domain: the api-builder validates
`assume_timezone(timezone=...)` / `local_timestamp(timezone=...)` to exactly IANA_TIMEZONE.

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

_LOCAL_TS_MSG = (
    "local_timestamp returns the UTC wall clock, not the target-zone wall "
    "clock -- ibis has no timezone method and the naive re-cast discards the "
    "conversion (verified 2026-07-29, ibis 12.0.0/duckdb: 12:00 instead of "
    "17:30 for Asia/Kolkata)"
)


def _fact(
    op_key, message: str, backend, dialect: str | None, since: str = "2026-07-29"
) -> CapabilityFact:
    return CapabilityFact(
        operation_key=op_key,
        param="timezone",
        value_class=ValueClass.IANA_TIMEZONE,
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        dialect=dialect,
        message=message,
        since=since,
    )


_IBIS_FACTS = tuple(
    _fact(
        FK_SUB_DT.ASSUME_TIMEZONE,
        _ASSUME_TZ_MSG,
        CONST_BACKEND.IBIS,
        dialect,
        since=_SINCE,
    )
    for dialect in (None, "ibis-duckdb")
) + tuple(
    _fact(
        FK_SUB_DT.LOCAL_TIMESTAMP,
        _LOCAL_TS_MSG,
        CONST_BACKEND.IBIS,
        dialect,
        since="2026-07-29",
    )
    for dialect in (None, "ibis-duckdb")
)

_NARWHALS_FACTS = tuple(
    _fact(
        FK_SUB_DT.ASSUME_TIMEZONE,
        _ASSUME_TZ_MSG,
        CONST_BACKEND.NARWHALS,
        dialect,
        since=_SINCE,
    )
    for dialect in ("narwhals-polars", "narwhals-pandas")
)

CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, _IBIS_FACTS)
CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, _NARWHALS_FACTS)

