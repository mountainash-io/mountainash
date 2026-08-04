"""Identity-keyed capability inventory — the closed allowlist that Task 7's
compile_smoke harness consumes as an inline closed rule (spec
2026-08-01-spine-derived-test-expectations, Task 6).

The committed ``tests/_spine_expectation_inventory.yaml`` is GENERATED from the
migration census (``build_census()``): every ``inventoried``-bucket
``CensusEntry`` becomes exactly one ``InventoryEntry`` row, in the census's own
deterministic ``(path, line, node_id)`` order. It is never hand-authored — run
``regenerate_inventory()`` to rebuild it.

Each row is keyed by its full identity
``f"{node_id}|{op}|{backend}|{param}|{option_value}"``; any slot may carry the
``UNRESOLVED`` sentinel when the census could not statically recover it. A row
whose identity is ``UNRESOLVED``-slotted can never be matched against a live
raise, so it is ``runtime_observable: false`` by construction — only a
fully-resolved compile_smoke-harness site is observable at runtime.

There is deliberately no ``reconcile_smoke``: stale/missing detection happens
inline at the compile_smoke harness in Task 7. A ``runtime_observable: false``
catalogue row is never reconciled against a live raise.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from tests.fixtures.capability_census import UNRESOLVED, CensusEntry, build_census

_TESTS_DIR = Path(__file__).resolve().parent.parent
_INVENTORY_PATH = _TESTS_DIR / "_spine_expectation_inventory.yaml"

# Provenance marker for every generated row: this backlog snapshot was
# catalogued during SP1 of the 2026-08-01 spine-derived-test-expectations plan.
# A stable constant keeps ``regenerate_inventory()`` idempotent (no per-run dates).
_INVENTORY_SINCE = "2026-08-01"

# The compile_smoke harness files whose live ``BackendCapabilityError`` raises
# Task 7 reconciles against runtime-observable rows. A row is runtime-observable
# ONLY when it sits at one of these sites AND its identity is fully resolved.
_COMPILE_SMOKE_SITES = frozenset(
    {
        "tests/core/test_compile_smoke.py",
        "tests/core/test_rel_collect_smoke.py",
    }
)

VALID_CLASSIFICATIONS = ("clear-cut-gap", "possibly-stale", "conditional-raise")
VALID_FOUND_VIA = ("imperative-xfail", "static-marker", "manual-map", "catch-all")

# census ``kind`` -> inventory ``found_via`` (how the expectation was discovered).
# scope-(a) parametrized cases and scope-(c) map entries both derive from the
# production broken-ops map, so both are catalogued as ``manual-map``.
_FOUND_VIA_BY_KIND = {
    "imperative-xfail": "imperative-xfail",
    "static-marker": "static-marker",
    "catch-all": "catch-all",
    "manual-map": "manual-map",
    "parametrized-case": "manual-map",
}

# census ``kind`` -> inventory ``classification``. A production-map gap is a
# clear-cut gap; a raw marker/xfail with no matching spine fact is possibly
# stale; a runtime capability-spine catch-all absorber raises conditionally.
_CLASSIFICATION_BY_KIND = {
    "manual-map": "clear-cut-gap",
    "parametrized-case": "clear-cut-gap",
    "static-marker": "possibly-stale",
    "imperative-xfail": "possibly-stale",
    "catch-all": "conditional-raise",
}

_FIELDS = (
    "key",
    "node_id",
    "operation_key",
    "backend",
    "param",
    "option_value",
    "current_reason",
    "classification",
    "found_via",
    "runtime_observable",
    "since",
    "display_site",
)


class InventoryError(Exception):
    """Raised when the inventory YAML is malformed — a duplicate identity key, a
    key that disagrees with its own slots, an invalid enum, an unmappable census
    kind, or a row that violates the ``runtime_observable`` invariant."""


@dataclass(frozen=True)
class InventoryEntry:
    key: str
    node_id: str
    operation_key: str
    backend: str
    param: str
    option_value: str | None
    current_reason: str
    classification: str
    found_via: str
    runtime_observable: bool
    since: str
    display_site: str


def _identity_key(node_id, operation_key, backend, param, option_value) -> str:
    return f"{node_id}|{operation_key}|{backend}|{param}|{option_value}"


def _fully_resolved(operation_key, backend, param, option_value) -> bool:
    """True iff no identity slot carries the ``UNRESOLVED`` sentinel. ``None``
    ``option_value`` is a resolved 'no option', not an unrecovered selector."""
    return UNRESOLVED not in (operation_key, backend, param, option_value)


def _entry_from_census(ce: CensusEntry) -> InventoryEntry:
    found_via = _FOUND_VIA_BY_KIND.get(ce.kind)
    classification = _CLASSIFICATION_BY_KIND.get(ce.kind)
    if found_via is None or classification is None:
        raise InventoryError(
            f"{ce.path}:{ce.line} inventoried entry has unmappable census kind "
            f"{ce.kind!r}"
        )
    runtime_observable = ce.path in _COMPILE_SMOKE_SITES and _fully_resolved(
        ce.operation_key, ce.backend, ce.param, ce.option_value
    )
    return InventoryEntry(
        key=_identity_key(
            ce.node_id, ce.operation_key, ce.backend, ce.param, ce.option_value
        ),
        node_id=ce.node_id,
        operation_key=ce.operation_key,
        backend=ce.backend,
        param=ce.param,
        option_value=ce.option_value,
        current_reason=ce.current_reason,
        classification=classification,
        found_via=found_via,
        runtime_observable=runtime_observable,
        since=_INVENTORY_SINCE,
        display_site=f"{ce.path}:{ce.line}",
    )


def _entry_from_row(row: object) -> InventoryEntry:
    if not isinstance(row, dict):
        raise InventoryError(f"inventory row is not a mapping: {row!r}")
    missing = [f for f in _FIELDS if f not in row]
    if missing:
        raise InventoryError(f"inventory row missing fields {missing}: {row!r}")
    node_id = row["node_id"]
    operation_key = row["operation_key"]
    backend = row["backend"]
    param = row["param"]
    option_value = row["option_value"]
    expected_key = _identity_key(node_id, operation_key, backend, param, option_value)
    if row["key"] != expected_key:
        raise InventoryError(
            f"row key {row['key']!r} does not match its identity {expected_key!r}"
        )
    if row["classification"] not in VALID_CLASSIFICATIONS:
        raise InventoryError(f"invalid classification {row['classification']!r}")
    if row["found_via"] not in VALID_FOUND_VIA:
        raise InventoryError(f"invalid found_via {row['found_via']!r}")
    runtime_observable = row["runtime_observable"]
    if not isinstance(runtime_observable, bool):
        raise InventoryError(
            f"runtime_observable must be a bool: {runtime_observable!r}"
        )
    if runtime_observable and not _fully_resolved(
        operation_key, backend, param, option_value
    ):
        raise InventoryError(
            f"{expected_key}: UNRESOLVED-slotted row cannot be runtime_observable"
        )
    return InventoryEntry(
        key=expected_key,
        node_id=node_id,
        operation_key=operation_key,
        backend=backend,
        param=param,
        option_value=option_value,
        current_reason=row["current_reason"],
        classification=row["classification"],
        found_via=row["found_via"],
        runtime_observable=runtime_observable,
        since=row["since"],
        display_site=row["display_site"],
    )


def load_inventory(path: Path | None = None) -> dict[str, InventoryEntry]:
    """Parse and validate the inventory YAML into an identity-keyed mapping.

    Raises :class:`InventoryError` on any duplicate key or malformed row."""
    path = path or _INVENTORY_PATH
    raw = yaml.safe_load(Path(path).read_text()) or []
    out: dict[str, InventoryEntry] = {}
    for row in raw:
        entry = _entry_from_row(row)
        if entry.key in out:
            raise InventoryError(f"duplicate identity key: {entry.key}")
        out[entry.key] = entry
    return out


def inventory_has(
    node_id,
    operation_key,
    backend,
    param,
    option_value,
    *,
    inventory: dict[str, InventoryEntry] | None = None,
) -> bool:
    """Exact-identity membership test used by Task 7's inline closed rule. A
    near-miss on any single slot is not a member. Pass a preloaded ``inventory``
    to avoid re-parsing the YAML on every call."""
    inv = inventory if inventory is not None else load_inventory()
    return _identity_key(node_id, operation_key, backend, param, option_value) in inv


def regenerate_inventory(path: Path | None = None) -> Path:
    """(Re)write the committed inventory YAML from the census ``inventoried``
    bucket, in the census's deterministic ``(path, line, node_id)`` order."""
    path = path or _INVENTORY_PATH
    entries = [
        _entry_from_census(ce)
        for ce in build_census()
        if ce.bucket == "inventoried"
    ]
    seen: set[str] = set()
    rows: list[dict[str, object]] = []
    for entry in entries:
        if entry.key in seen:
            raise InventoryError(f"duplicate identity key: {entry.key}")
        seen.add(entry.key)
        rows.append({field: getattr(entry, field) for field in _FIELDS})
    Path(path).write_text(
        yaml.safe_dump(
            rows, sort_keys=False, default_flow_style=False, allow_unicode=True
        )
    )
    return path
