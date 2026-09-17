"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE, subject="substring"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars does not support dynamic column patterns in str.replace",
            workaround="Use a literal string substring; replacement can be a column reference",
            issue="PL-STR-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE, subject="pattern"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars does not support dynamic column patterns in str.replace_all/str.replace with regex",
            workaround="Use a literal string regex pattern; replacement can be a column reference",
            issue="PL-STR-02",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT, subject="count"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars str.repeat() requires a literal integer count, not a column expression",
            workaround="Use a literal integer count value",
            issue="PL-STR-03",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER, subject="length"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars str.center() requires a literal integer length, not a column expression",
            workaround="Use a literal integer length value",
            issue="PL-STR-03",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER, subject="character"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars str.center() requires a single literal fill character, not a column expression",
            workaround="Use a literal single-character string",
            issue="PL-STR-03",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE, subject="start"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars str.replace_slice() requires a literal integer start, not a column expression",
            workaround="Use a literal integer start value",
            issue="PL-STR-03",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE, subject="length"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars str.replace_slice() requires a literal integer length, not a column expression",
            workaround="Use a literal integer length value",
            issue="PL-STR-03",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.LPAD, subject="characters"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars str.pad_start() requires a single literal fill character, not a column expression",
            workaround="Use a literal single-character string",
            issue="PL-STR-03",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.RPAD, subject="characters"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars str.pad_end() requires a single literal fill character, not a column expression",
            workaround="Use a literal single-character string",
            issue="PL-STR-03",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE, subject="match"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars LIKE requires a literal pattern — the SQL-LIKE to regex conversion happens in Python",
            workaround="Use a literal SQL LIKE pattern string",
            probe_exempt="dynamic arg silently miscompiles: the SQL-LIKE→regex conversion runs on str(Expr), producing a pattern that matches nothing rather than raising — cannot be confirmed by an exception-based probe",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE, subject="replacement"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Polars str.replace_slice() requires a literal replacement string, not a column expression",
            workaround="Use a literal replacement string",
            probe_exempt="dynamic arg silently miscompiles: str(Expr) bakes the unresolved expression's Python repr into the output as a literal string rather than raising — cannot be confirmed by an exception-based probe",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT, subject="pattern"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-08-13",
            message="Polars regexp_string_split requires a literal pattern -- the map_elements fallback binds pattern as a Python closure value, not a column expression",
            workaround="Use a literal string regex pattern",
            issue="PL-STR-04",
        ),
    ),
)
