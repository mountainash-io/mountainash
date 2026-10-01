"""Single naming rule for keyed join output.

Every consumer that needs to know a keyed join's output names -- schema
inference, ``visit_join`` at execution, and transport lineage -- asks this
module, so ``.columns``, collected data and lineage cannot disagree.

Contract (Substrait JoinRel shaped): all left columns in left order, then all
right columns in right order. A right column whose name exists on the left
becomes ``name + suffix``; if that is also taken, ``name + suffix + "_1"``,
``"_2"``, ... in right-column order (reported in ``collisions``). ``coalesce``
(``None`` = merge iff keys were declared with ``on``) folds each key pair into
the left key's name and position; the right key is removed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from mountainash.core.constants import JoinType

_KEYED = (JoinType.INNER, JoinType.LEFT, JoinType.RIGHT, JoinType.OUTER)


@dataclass(frozen=True)
class JoinLayout:
    """Output naming decisions for one keyed join."""

    right_rename: dict[str, str]
    left_keys: list[str]
    right_keys: list[str]
    """Final (post-rename) right key names, paired with ``left_keys``."""
    merge: list[tuple[str, str]] = field(default_factory=list)
    """``(left_key, right_key)`` pairs to coalesce into ``left_key``."""
    drop: list[str] = field(default_factory=list)
    collisions: list[tuple[str, str]] = field(default_factory=list)
    """``(original, final)`` for names that needed an ``_n`` increment."""


def keyed_layout_applies(node: Any) -> bool:
    """True for INNER/LEFT/RIGHT/OUTER joins declared with keys."""
    return node.join_type in _KEYED and bool(node.on or (node.left_on and node.right_on))


def _claim(name: str, suffix: str, taken: set[str]) -> tuple[str, bool]:
    final, n = name + suffix, 0
    while final in taken:
        n += 1
        final = f"{name}{suffix}_{n}"
    taken.add(final)
    return final, n > 0


def join_layout(
    left_names: list[str],
    right_names: list[str],
    *,
    join_type: JoinType,
    on: Optional[list[str]],
    left_on: Optional[list[str]],
    right_on: Optional[list[str]],
    suffix: str,
    coalesce: Optional[bool],
) -> JoinLayout:
    """Decide right-side renames and the key merge for a keyed join."""
    left_keys = list(on) if on else list(left_on or [])
    right_keys = list(on) if on else list(right_on or [])
    left_set = set(left_names)
    taken = left_set | set(right_names)
    rename: dict[str, str] = {}
    collisions: list[tuple[str, str]] = []
    for name in right_names:
        if name in left_set:
            final, incremented = _claim(name, suffix, taken)
            rename[name] = final
            if incremented:
                collisions.append((name, final))
    # Keys missing from an unknown/partial right schema take names through the
    # same claim, so they can never alias a left column a later drop removes.
    for key in right_keys:
        if key in left_set and key not in rename and key not in right_names:
            rename[key], _ = _claim(key, suffix, taken)

    final_keys = [rename.get(k, k) for k in right_keys]
    merge: list[tuple[str, str]] = []
    drop: list[str] = []
    if bool(on) if coalesce is None else coalesce:
        drop = list(final_keys)
        if join_type in (JoinType.RIGHT, JoinType.OUTER):
            merge = list(zip(left_keys, final_keys))
    return JoinLayout(rename, left_keys, final_keys, merge, drop, collisions)


def layout_for_node(node: Any, left_names: list[str], right_names: list[str]) -> JoinLayout:
    """``join_layout`` for a ``JoinRelNode``."""
    return join_layout(
        left_names, right_names,
        join_type=node.join_type, on=node.on, left_on=node.left_on,
        right_on=node.right_on, suffix=node.suffix, coalesce=node.coalesce,
    )


def native_column_names(native: Any) -> list[str]:
    """Ordered output column names of a compiled native relation."""
    from mountainash.relations.schema_inference import _schema_from_dataframe

    schema = _schema_from_dataframe(native)
    if schema:
        return list(schema)
    if hasattr(native, "collect_schema"):
        return list(native.collect_schema().names())
    return list(native.columns)
