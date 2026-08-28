"""Row identity: tiered resolution + keyed-identity validation (spec §7).

Tiers: keyed (natural_key / TypeSpec.primary_key; validated against the
data) > row_number (opt-in diagnostic ordinal, never a join key) > none.
No silent fallback between tiers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal


from mountainash.validation.value import INVALID_VALUE, canonical_value_key

from mountainash.validation.errors import (
    CheckDeclarationError,
    IdentityInvalidError,
    IdentityRequiredError,
)

if TYPE_CHECKING:
    from mountainash.relations.core.logical_snapshot import ResolvedLogicalSnapshot
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
    logical_snapshot: "ResolvedLogicalSnapshot",
    identity: RowIdentity,
    *,
    allow_imperfect_key: bool = False,
) -> dict[str, Any]:
    """Verify keyed identity using the shared canonical logical-key algebra.

    Reads key columns by name from the prepared logical snapshot (spec
    section 15, Task 7 step 5) -- never ``Relation.to_polars()``, which
    would re-execute the relation and, for a `coerce`-action structured
    key field, raise on an invalid value instead of reporting it as an
    unknown key component.
    """
    from mountainash.relations.core.logical_snapshot import logical_column_values

    columns = logical_snapshot.logical_columns
    missing = [name for name in identity.key_fields if name not in columns]
    if missing:
        raise IdentityInvalidError(
            f"keyed identity {identity.key_fields}: key fields missing from data: {missing}"
        )

    null_key_rows = 0
    unknown_key_rows = 0
    first_row_by_key: dict[tuple[Any, ...], int] = {}
    duplicate_keys: set[tuple[Any, ...]] = set()
    field_columns = [
        logical_column_values(logical_snapshot, name) for name in identity.key_fields
    ]
    for row_index, values in enumerate(zip(*field_columns, strict=True)):
        if any(value is INVALID_VALUE for value in values):
            unknown_key_rows += 1
            continue
        if any(value is None for value in values):
            null_key_rows += 1
            continue
        key = tuple(canonical_value_key(value) for value in values)
        if key in first_row_by_key:
            duplicate_keys.add(key)
        else:
            first_row_by_key[key] = row_index

    diagnostics = {
        "null_key_rows": null_key_rows,
        "unknown_key_rows": unknown_key_rows,
        "duplicate_key_tuples": len(duplicate_keys),
    }
    if (null_key_rows or unknown_key_rows or duplicate_keys) and not allow_imperfect_key:
        raise IdentityInvalidError(
            f"keyed identity {identity.key_fields} does not hold: "
            f"{null_key_rows} null-key rows, {unknown_key_rows} unknown-key rows, "
            f"{len(duplicate_keys)} duplicate key tuples. "
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
