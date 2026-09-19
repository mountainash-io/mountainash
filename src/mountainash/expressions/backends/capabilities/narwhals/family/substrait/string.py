"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING, subject="substring"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals str.replace_all()'s pattern argument does not accept a column expression on any dialect (pandas or polars-backed) -- count_substring's fold is built on replace_all, unlike sibling search-operand params that are pandas-only restricted.",
            workaround="Use a literal string value instead of a column reference",
            issue="NW-STR-03",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.LPAD, subject="characters"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals str.lpad() requires a single literal fill character, not a column expression",
            workaround="Use a literal single-character string",
            issue="NW-STR-06",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.RPAD, subject="characters"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals str.rpad() requires a single literal fill character, not a column expression",
            workaround="Use a literal single-character string",
            issue="NW-STR-06",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE, subject="*"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER, subject="*"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.SWAPCASE, subject="*"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-23",
            message="This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT, subject="*"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-13",
            message="Narwhals has no regex-split primitive at the pinned version -- ExprStringNamespace.split(by) is literal-substring-only, no other method performs regex splitting on any narwhals dialect",
            workaround="Use a Polars or ibis-duckdb/ibis-polars(literal) backend for regex split",
            issue="NW-STR-20",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.SPLIT, subject="separator"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-08-13",
            message="Narwhals str.split() requires a literal separator string, not an Expr -- raises TypeError even for an Expr-wrapped literal",
            workaround="Use a literal separator string",
            issue="NW-STR-21",
        ),
    ),
)
