"""Row identity: tiered resolution + keyed-identity validation (spec §7).

Tiers: keyed (natural_key / TypeSpec.primary_key; validated against the
data) > row_number (opt-in diagnostic ordinal, never a join key) > none.
No silent fallback between tiers.
"""
from __future__ import annotations

import operator
from dataclasses import dataclass
from functools import reduce
from typing import TYPE_CHECKING, Any, Literal

from mountainash.validation.errors import (
    CheckDeclarationError,
    IdentityInvalidError,
    IdentityRequiredError,
)

if TYPE_CHECKING:
    from mountainash.relations import Relation
    from mountainash.typespec.spec import TypeSpec


@dataclass(frozen=True)
class RowIdentity:
    kind: Literal["keyed", "row_number", "none"]
    key_fields: tuple[str, ...] = ()


def resolve_identity(
    *,
    natural_key: list[str] | None = None,
    spec: "TypeSpec | None" = None,
    row_identity: str | None = None,
) -> RowIdentity:
    """Resolve the identity tier: explicit natural_key > spec primary_key >
    explicit row_number opt-in > none."""
    if natural_key:
        return RowIdentity(kind="keyed", key_fields=tuple(natural_key))
    primary_key = getattr(spec, "primary_key", None) if spec is not None else None
    if primary_key:
        keys = list(primary_key)
        return RowIdentity(kind="keyed", key_fields=tuple(keys))
    if row_identity == "row_number":
        return RowIdentity(kind="row_number")
    if row_identity not in (None, "none"):
        raise CheckDeclarationError(
            f"unknown row_identity {row_identity!r}; expected 'row_number' or None"
        )
    return RowIdentity(kind="none")


def validate_keyed_identity(
    rel: "Relation",
    identity: RowIdentity,
    *,
    allow_imperfect_key: bool = False,
) -> dict[str, Any]:
    """Verify declared keyed identity holds against the data (spec §7).

    Raises IdentityInvalidError on missing key fields always, and on
    null-key rows / duplicate key tuples unless allow_imperfect_key=True —
    in which case the counts are returned as diagnostics.
    """
    import mountainash as ma

    schema_cols = set(rel.schema.keys())
    missing = [k for k in identity.key_fields if k not in schema_cols]
    if missing:
        raise IdentityInvalidError(
            f"keyed identity {identity.key_fields}: key fields missing from data: {missing}"
        )

    null_predicate = reduce(operator.or_, (ma.col(k).is_null() for k in identity.key_fields))
    null_key_rows = rel.filter(null_predicate).count_rows()

    duplicate_key_tuples = (
        rel.group_by(*identity.key_fields)
        .agg(ma.count_records().alias("__ma_key_count__"))
        .filter(ma.col("__ma_key_count__").gt(ma.lit(1)))
        .count_rows()
    )

    diagnostics = {
        "null_key_rows": null_key_rows,
        "duplicate_key_tuples": duplicate_key_tuples,
    }
    if (null_key_rows or duplicate_key_tuples) and not allow_imperfect_key:
        raise IdentityInvalidError(
            f"keyed identity {identity.key_fields} does not hold: "
            f"{null_key_rows} null-key rows, {duplicate_key_tuples} duplicate key tuples. "
            "Pass allow_imperfect_key=True to proceed with diagnostics recorded."
        )
    return diagnostics


def require_keyed(identity: RowIdentity, *, feature: str) -> None:
    """Gate a keyed-only capability; no silent fallback to positional identity."""
    if identity.kind != "keyed":
        raise IdentityRequiredError(
            f"{feature} requires keyed row identity (natural_key or TypeSpec.primary_key); "
            f"current identity tier is {identity.kind!r}"
        )
