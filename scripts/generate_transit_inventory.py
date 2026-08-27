#!/usr/bin/env python3
"""Deterministic AST-derived transit inventory generator.

Discovers every risky call-site candidate under ``src/mountainash`` (via
``tests.core._transit_census.discover_transit_candidates``), assigns each one
its TARGET (post-migration) `BoundaryKey`/`TransitClass` disposition, and
writes the characterized inventory consumed by
``tests/core/test_conversion_boundary_census.py``.

A candidate with no classification rule below is a hard failure: the closed
census (spec section 13, and the closed-by-default-verification principle)
requires every discovered candidate to have an explicit, dated disposition
before it can be checked in.

Run:
    hatch run test:python scripts/generate_transit_inventory.py \\
        --write tests/fixtures/transit_inventory.json
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from tests.core._transit_census import (  # noqa: E402
    InventoryEntry,
    TransitCandidate,
    discover_transit_candidates,
)

_SINCE = "2026-08-27"

Disposition = tuple[str, str, str]  # (boundary_key, transit_class, reason)


class UnclassifiedCandidateError(RuntimeError):
    """A discovered candidate matched no classification rule (fail closed)."""


# Per-(module, owner, callee) overrides for call sites whose target
# disposition cannot be derived from the callee name alone. Each entry cites
# the evidence read directly from source. See
# `mountainash-central/04.planning/mountainash/superpowers/specs/
# 2026-08-27-pandas-transit-elimination-design.md` section 4 for the
# corresponding failure narrative.
_OVERRIDES: dict[tuple[str, str, str], Disposition] = {
    (
        "mountainash.core.limitations",
        "enrich_materialization",
        "execute",
    ): (
        "IBIS_INTERNAL_EXECUTE",
        "INTERNAL_EXECUTION_TRANSIT",
        "Ibis Table.execute() on a successful result converts it to pandas "
        "before relation wrapping (spec 4.1) -- the documented root-cause bug "
        "this migration removes.",
    ),
    (
        "mountainash.relations.dag.dag",
        "RelationDAG.collect",
        "memtable",
    ): (
        "IBIS_INTERNAL_EXECUTE",
        "INTERNAL_EXECUTION_TRANSIT",
        "Wraps a pandas-transited residue with ibis.memtable() to restore a "
        "lazy marker without restoring the original dialect or null "
        "representation (spec 4.2's DAG target residue failure).",
    ),
    (
        "mountainash.relations.dag.dag",
        "RelationDAG._compile_with_refs",
        "memtable",
    ): (
        "IBIS_INTERNAL_EXECUTE",
        "INTERNAL_EXECUTION_TRANSIT",
        "Wraps a pandas-transited dependency residue with ibis.memtable() to "
        "restore a lazy marker, changing backend identity (spec 4.2's DAG "
        "dependency residue failure).",
    ),
    (
        "mountainash.relations.core.unified_visitor.relation_visitor",
        "UnifiedRelationVisitor._coerce_to_match",
        "DataFrame",
    ): (
        "PROHIBITED_NARWHALS_DICT_PANDAS_FALLBACK",
        "INTERNAL_EXECUTION_TRANSIT",
        "pd.DataFrame(value) as the Narwhals-target dict/row-dict fallback "
        "(spec 4.3) -- prohibited; Task 5 replaces it with a destination-"
        "native constructor.",
    ),
    (
        "mountainash.relations.core.unified_visitor.relation_visitor",
        "UnifiedRelationVisitor._coerce_to_match",
        "to_pandas",
    ): (
        "PROHIBITED_POLARS_NARWHALS_PANDAS_FALLBACK",
        "INTERNAL_EXECUTION_TRANSIT",
        "Narwhals native.to_pandas() as the Polars-target fallback for an "
        "otherwise unknown input (spec 4.3) -- prohibited; Task 5 replaces "
        "it with the Arrow-first adapter (spec 4.4).",
    ),
    (
        "mountainash.relations.core.unified_visitor.relation_visitor",
        "UnifiedRelationVisitor._coerce_to_match",
        "collect",
    ): (
        "CROSS_TYPE_JOIN_ADAPTER",
        "SEMANTICS_PRESERVING_ADAPTER",
        "Materializes a Polars LazyFrame operand mid cross-type-join adapter "
        "before Narwhals ingestion; part of the declared adapter route.",
    ),
    (
        "mountainash.relations.core.unified_visitor.relation_visitor",
        "UnifiedRelationVisitor._coerce_to_match",
        "to_pyarrow",
    ): (
        "CROSS_TYPE_JOIN_ADAPTER",
        "SEMANTICS_PRESERVING_ADAPTER",
        "Arrow-preferred conversion step of the declared cross-type-join "
        "adapter (spec 4.4's Arrow-before-pandas rule).",
    ),
    (
        "mountainash.relations.core.unified_visitor.relation_visitor",
        "UnifiedRelationVisitor._coerce_to_match",
        "to_native",
    ): (
        "CROSS_TYPE_JOIN_ADAPTER",
        "SEMANTICS_PRESERVING_ADAPTER",
        "Unwraps a Narwhals lazy operand immediately before ibis.memtable() "
        "ingestion; part of the declared cross-type-join adapter route.",
    ),
    (
        "mountainash.relations.core.unified_visitor.relation_visitor",
        "UnifiedRelationVisitor._coerce_to_match",
        "memtable",
    ): (
        "CROSS_TYPE_JOIN_ADAPTER",
        "SEMANTICS_PRESERVING_ADAPTER",
        "Ibis-target construction step of the declared cross-type-join "
        "adapter; Task 5 routes its dict/row-dict input through Arrow first "
        "(spec 4.4).",
    ),
    (
        "mountainash.relations.core.unified_visitor.relation_visitor",
        "UnifiedRelationVisitor._coerce_to_match",
        "from_native",
    ): (
        "CROSS_TYPE_JOIN_ADAPTER",
        "SEMANTICS_PRESERVING_ADAPTER",
        "Narwhals ingestion step of the declared cross-type-join adapter "
        "route.",
    ),
    (
        "mountainash.relations.core.unified_visitor.relation_visitor",
        "UnifiedRelationVisitor._coerce_same_family_dialect",
        "from_native",
    ): (
        "NARWHALS_DIALECT_COERCION_ADAPTER",
        "SEMANTICS_PRESERVING_ADAPTER",
        "Re-wraps a converted native value after same-family Narwhals "
        "dialect coercion (e.g. .to_pandas()/.to_polars()/.to_arrow()); part "
        "of the declared dialect-coercion adapter route.",
    ),
    (
        "mountainash.relations.dag.dag",
        "_anchor_prototype",
        "from_native",
    ): (
        "DAG_PROTOTYPE_ADAPTER",
        "SEMANTICS_PRESERVING_ADAPTER",
        "Wraps an empty native placeholder (Polars/PyArrow/pandas) into "
        "Narwhals for the DAG's declared cross-dialect prototype adapter.",
    ),
    (
        "mountainash.pydata.ingress.custom_type_helpers",
        "_apply_narwhals_custom_converters",
        "to_native",
    ): (
        "NARWHALS_NATIVE_UNWRAP_PANDAS",
        "EXPLICIT_PANDAS_INPUT",
        "Round-trips a Narwhals wrapper back to the caller's own originally-"
        "selected native type (`was_native`), preserving a pandas source "
        "identity when the caller supplied one.",
    ),
    (
        "mountainash.relations.core.relation_api.relation",
        "_materialize",
        "to_native",
    ): (
        "NARWHALS_NATIVE_UNWRAP_PANDAS",
        "EXPLICIT_PANDAS_INPUT",
        "Relation.collect()'s terminal unwrap of an eager Narwhals frame to "
        "its native value -- returns pandas when the caller's selected "
        "source was pandas (spec 6.2's identity-preservation rule).",
    ),
    (
        "mountainash.pipelines.integration.relation",
        "_visit_pipeline_step",
        "execute",
    ): (
        "PIPELINE_STEP_EXECUTOR",
        "NON_PANDAS_OPERATION",
        "node.executor.execute(...) is a pipeline-step executor call, "
        "unrelated to Ibis Table.execute() or any backend conversion; "
        "syntactically risky-named only.",
    ),
}

# Default disposition by risky callee name, applied when no per-site override
# exists above. Each is the TARGET (post-migration) disposition; a discovered
# candidate with no `transit_call()` wrapper is `legacy_unwrapped=True` until
# the task that owns its call site wires it.
_DEFAULT_BY_CALLEE: dict[str, Disposition] = {
    "to_polars": (
        "RELATION_TO_POLARS_TERMINAL",
        "NON_PANDAS_OPERATION",
        "A declared Polars-producing terminal or intermediate call; its "
        "result is never pandas by contract.",
    ),
    "to_pandas": (
        "PYDATA_EXPLICIT_PANDAS_EGRESS",
        "EXPLICIT_PANDAS_EGRESS",
        "A declared, user-visible pandas terminal.",
    ),
    "to_arrow": (
        "NON_PANDAS_ARROW_TERMINAL",
        "NON_PANDAS_OPERATION",
        "A declared PyArrow-producing terminal; never pandas.",
    ),
    "to_pyarrow": (
        "NON_PANDAS_ARROW_TERMINAL",
        "NON_PANDAS_OPERATION",
        "A declared PyArrow-producing terminal; never pandas.",
    ),
    "collect": (
        "NATIVE_LAZY_COLLECT",
        "NON_PANDAS_OPERATION",
        "Native materialization of a Polars/Narwhals lazy frame or a "
        "Mountainash relation whose declared terminal never itself "
        "constructs pandas.",
    ),
    "from_pandas": (
        "PYDATA_EXPLICIT_PANDAS_INPUT",
        "EXPLICIT_PANDAS_INPUT",
        "pl.from_pandas(): a declared pandas-selected source conversion.",
    ),
    "from_native": (
        "NARWHALS_NATIVE_WRAP",
        "NON_PANDAS_OPERATION",
        "Wraps an arbitrary native value into a Narwhals frame for "
        "inspection, resource reading, or adapter ingestion; the wrap call "
        "itself never constructs pandas.",
    ),
    "to_native": (
        "NARWHALS_NATIVE_UNWRAP_NON_PANDAS",
        "NON_PANDAS_OPERATION",
        "Unwraps a Narwhals frame to its native value for schema/metadata "
        "inspection only.",
    ),
    "memtable": (
        "IBIS_CONSTRUCTOR_ADAPTER",
        "SEMANTICS_PRESERVING_ADAPTER",
        "Declared Ibis table construction from Arrow or resource-native "
        "input.",
    ),
    "execute": (
        "IBIS_SCALAR_EXECUTE",
        "NON_PANDAS_OPERATION",
        "Ibis scalar/count execution; the result is a Python scalar, never "
        "a pandas frame.",
    ),
    "DataFrame": (
        "PYDATA_EXPLICIT_PANDAS_INPUT",
        "EXPLICIT_PANDAS_INPUT",
        "pd.DataFrame(): a declared pandas-selected source or destination "
        "construction.",
    ),
    "from_dict": (
        "NARWHALS_CONSTRUCTOR_ADAPTER",
        "SEMANTICS_PRESERVING_ADAPTER",
        "Narwhals constructor call; permitted only for a declared "
        "destination identity.",
    ),
}

# Fingerprint-scoped overrides: for the rare case where the SAME owner
# invokes the SAME risky callee twice with different dispositions (e.g. one
# legitimate call and one prohibited fallback sharing an owner+callee pair).
# Checked before `_OVERRIDES`.
_FINGERPRINT_OVERRIDES: dict[tuple[str, str, str, str], Disposition] = {
    (
        "mountainash.relations.core.relation_api.relation",
        "Relation.to_polars",
        "to_pandas",
        "f50942d2466f8df7",
    ): (
        "PROHIBITED_IBIS_TO_POLARS_PANDAS_FALLBACK",
        "INTERNAL_EXECUTION_TRANSIT",
        "result.to_pandas() as Relation.to_polars()'s last-resort fallback "
        "when the result is neither Polars, pandas, nor exposes "
        "to_pyarrow() -- spec 4.3's 'Ibis to Polars terminal' failure; "
        "Task 4 removes the fallback (Arrow-only, then error).",
    ),
    (
        "mountainash.relations.core.relation_api.relation",
        "Relation.to_polars",
        "from_pandas",
        "1afed9b161f56825",
    ): (
        "PROHIBITED_IBIS_TO_POLARS_PANDAS_FALLBACK",
        "INTERNAL_EXECUTION_TRANSIT",
        "pl.from_pandas(result.to_pandas()) wraps the same prohibited "
        "last-resort fallback's pandas result; inseparable from the "
        "to_pandas() call it wraps (spec 4.3).",
    ),
}


def classify(candidate: TransitCandidate) -> Disposition:
    fingerprint_key = (
        candidate.module,
        candidate.owner,
        candidate.callee,
        candidate.fingerprint,
    )
    override = _FINGERPRINT_OVERRIDES.get(fingerprint_key)
    if override is not None:
        return override
    override = _OVERRIDES.get((candidate.module, candidate.owner, candidate.callee))
    if override is not None:
        return override
    default = _DEFAULT_BY_CALLEE.get(candidate.callee)
    if default is None:
        raise UnclassifiedCandidateError(
            f"No classification rule for {candidate.module}.{candidate.owner} "
            f"-> {candidate.callee}() [{candidate.fingerprint}]. Add a rule to "
            "_OVERRIDES or _DEFAULT_BY_CALLEE in "
            "scripts/generate_transit_inventory.py before checking in the "
            "inventory."
        )
    return default


def build_inventory(root: Path) -> list[InventoryEntry]:
    candidates = discover_transit_candidates(root)
    by_identity: dict[tuple[str, str, str, str], InventoryEntry] = {}
    for candidate in candidates:
        boundary_key, transit_class, reason = classify(candidate)
        entry = InventoryEntry(
            module=candidate.module,
            owner=candidate.owner,
            callee=candidate.callee,
            fingerprint=candidate.fingerprint,
            boundary_key=boundary_key,
            transit_class=transit_class,
            reason=reason,
            since=_SINCE,
            legacy_unwrapped=not candidate.wrapped,
        )
        by_identity[entry.identity] = entry
    return sorted(by_identity.values(), key=lambda entry: entry.identity)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        type=Path,
        default=None,
        help="Path to write the JSON inventory (prints to stdout if omitted)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=_REPO_ROOT / "src" / "mountainash",
        help="Package directory to scan (default: src/mountainash)",
    )
    args = parser.parse_args(argv)

    entries = build_inventory(args.root)
    payload = [asdict(entry) for entry in entries]
    text = json.dumps(payload, indent=2) + "\n"

    if args.write:
        args.write.write_text(text)
        print(f"wrote {len(payload)} entries to {args.write}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
