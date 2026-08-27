"""Closed conversion-boundary census: exact inventory equality and wrapper
enforcement.

See ``mountainash-central/04.planning/mountainash/superpowers/specs/
2026-08-27-pandas-transit-elimination-design.md`` section 13.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from tests.core._transit_census import (
    RISKY_METHOD_NAMES,
    discover_transit_candidates,
    load_inventory,
)
from mountainash.core.transit import BOUNDARY_REGISTRY, BoundaryKey, TransitClass

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src" / "mountainash"
_TESTS_ROOT = _REPO_ROOT / "tests"
_INVENTORY_PATH = _REPO_ROOT / "tests" / "fixtures" / "transit_inventory.json"
_TRANSIT_MODULE = _SRC_ROOT / "core" / "transit.py"

_BOUNDARY_KEY_REF = re.compile(r"BoundaryKey\.([A-Z_][A-Z0-9_]*)")


def test_current_transit_inventory_is_complete():
    discovered = discover_transit_candidates(_SRC_ROOT)
    inventoried = load_inventory(_INVENTORY_PATH)
    assert {item.identity for item in discovered} == {
        item.identity for item in inventoried
    }


def test_inventory_entries_have_policy_reason_and_date():
    entries = load_inventory(_INVENTORY_PATH)
    valid_classes = {member.name for member in TransitClass}
    for entry in entries:
        assert entry.transit_class in valid_classes, entry
        assert entry.reason.strip(), entry
        date.fromisoformat(entry.since)


def test_new_unwrapped_to_pandas_call_fails_closed(tmp_path):
    module = tmp_path / "new_route.py"
    module.write_text("def convert(frame):\n    return frame.to_pandas()\n")
    discovered = discover_transit_candidates(tmp_path)
    assert discovered[0].wrapped is False


def test_census_fixture_rejects_every_undeclared_dispatch_shape(tmp_path):
    """One fixture module exercising every pattern the closed census must
    catch even though none of them route through `transit_call()`:
    a Narwhals constructor with a literal pandas destination, a stored bound
    method used as a callback, a `transit_call()` invocation with a computed
    (non-literal) `BoundaryKey`, and an unwrapped `getattr()` dispatch."""
    module = tmp_path / "undeclared.py"
    module.write_text(
        "import narwhals as nw\n"
        "from mountainash.core.transit import transit_call\n"
        "\n"
        "def convert(value, dynamic_key, values):\n"
        "    data = nw.from_dict({'a': [1]}, backend='pandas')\n"
        "    callback = value.to_pandas\n"
        "    mapped = list(map(callback, values))\n"
        "    result = transit_call(dynamic_key, value.execute)\n"
        "    other = getattr(value, 'execute')\n"
        "    return data, mapped, result, other\n"
    )
    discovered = discover_transit_candidates(tmp_path)
    by_callee = {}
    for candidate in discovered:
        by_callee.setdefault(candidate.callee, []).append(candidate)

    assert "from_dict" in by_callee
    assert all(not c.wrapped for c in by_callee["from_dict"])

    assert "to_pandas" in by_callee
    assert all(not c.wrapped for c in by_callee["to_pandas"])

    assert "execute" in by_callee
    assert len(by_callee["execute"]) == 2
    assert all(not c.wrapped for c in by_callee["execute"]), (
        "a computed BoundaryKey must never count as wrapped"
    )


def test_every_wrapped_candidate_uses_a_literal_boundary_key(tmp_path):
    """A `transit_call()` site is `wrapped=True` only when its key is a
    literal `BoundaryKey.MEMBER` attribute access."""
    module = tmp_path / "wrapped.py"
    module.write_text(
        "from mountainash.core.transit import BoundaryKey, transit_call\n"
        "\n"
        "def convert(value):\n"
        "    return transit_call(BoundaryKey.IBIS_NATIVE_CACHE, value.execute)\n"
    )
    discovered = discover_transit_candidates(tmp_path)
    assert len(discovered) == 1
    assert discovered[0].wrapped is True
    assert discovered[0].callee == "execute"


def test_risky_method_names_cover_the_documented_generic_set():
    assert RISKY_METHOD_NAMES == {
        "execute",
        "to_pandas",
        "to_pandas_batches",
        "from_pandas",
        "collect",
        "to_native",
        "to_polars",
        "to_arrow",
        "to_pyarrow",
        "memtable",
    }


def test_no_internal_execution_transit_key_has_a_production_reference():
    """spec section 13 Task 10 step 3: INTERNAL_EXECUTION_TRANSIT (e.g.
    ``IBIS_INTERNAL_EXECUTE``) is always prohibited -- its prohibition is
    proved only by the synthetic tests in test_transit_registry.py
    (``test_internal_execution_transit_is_always_prohibited``,
    ``test_untraced_prohibited_pandas_result_raises``). No real call site
    may reference it; the discovered inventory must carry zero such rows."""
    entries = load_inventory(_INVENTORY_PATH)
    prohibited = [
        entry for entry in entries if entry.transit_class == "INTERNAL_EXECUTION_TRANSIT"
    ]
    assert prohibited == []


def _boundary_key_names(root: Path, *, exclude: "Path | None" = None) -> set[str]:
    """Every literal ``BoundaryKey.<NAME>`` reference under `root`, filtered
    to real ``BoundaryKey`` members (spec section 13 Task 10 step 3's
    "referenced"/"exercised" sets). A regex scan, not an AST walk: it
    catches every reference regardless of surrounding shape (a
    ``transit_call()`` first argument, a docstring cross-reference, a
    monkeypatch target, a ``record.boundary_key is`` assertion, ...),
    which is exactly the closure this proof needs -- broader than
    ``discover_transit_candidates()``'s risky-callee-scoped inventory.
    Placeholder docstring text such as ``BoundaryKey.MEMBER`` never
    collides with a real member name, so no explicit exclusion is needed."""
    valid = {key.name for key in BoundaryKey}
    names: set[str] = set()
    for path in root.rglob("*.py"):
        if exclude is not None and path == exclude:
            continue
        names.update(n for n in _BOUNDARY_KEY_REF.findall(path.read_text()) if n in valid)
    return names


# Static-only entries (spec section 13 Task 10 step 3): every BoundaryKey
# referenced in production but never named in a test file by its literal
# `BoundaryKey.<NAME>` spelling. Each entry is exercised functionally --
# cross-backend collection/coercion/egress/reader tests assert the
# resulting VALUES and identities, not the specific boundary key -- so its
# absence here is a documented choice, not a coverage gap. See the cited
# test module for the functional proof.
_STATIC_ONLY_BOUNDARY_KEYS: "dict[str, tuple[str, str]]" = {
    "ARROW_TO_POLARS_EGRESS": (
        "Exercised functionally by tests/relations/test_native_materialization.py "
        "and tests/relations/cross_backend/ Arrow/Ibis-to-Polars egress assertions.",
        "2026-08-27",
    ),
    "ARROW_TO_PANDAS_EGRESS": (
        "Exercised functionally by tests/relations/test_native_materialization.py's "
        "explicit_pandas_egress() Arrow-source assertions.",
        "2026-08-27",
    ),
    "ARROW_TO_IBIS_ADAPTER": (
        "Exercised functionally by tests/relations/test_conversion_adapters.py's "
        "coerce_to_ibis() dict/list cross-type-join tests.",
        "2026-08-27",
    ),
    "IBIS_TO_ARROW_EGRESS": (
        "Exercised functionally by tests/relations/test_native_materialization.py's "
        "Ibis-to-Polars-via-Arrow egress tests.",
        "2026-08-27",
    ),
    "IBIS_TO_PANDAS_EGRESS": (
        "Exercised functionally by tests/relations/test_native_materialization.py's "
        "explicit_pandas_egress() Ibis-source assertions.",
        "2026-08-27",
    ),
    "IBIS_CONSTRUCTOR_ADAPTER": (
        "Exercised functionally by tests/relations/test_resource_transit_boundaries.py's "
        "Ibis reader trace tests and tests/relations/test_conversion_adapters.py's "
        "coerce_to_ibis() tests.",
        "2026-08-27",
    ),
    "IBIS_SCALAR_EXECUTE": (
        "Exercised functionally by tests/relations/test_resource_transit_boundaries.py's "
        "test_ibis_fetch_from_end_records_scalar_execute and cross-backend sample()/"
        "fetch_from_end() tests.",
        "2026-08-27",
    ),
    "NARWHALS_DIALECT_TO_ARROW": (
        "Exercised functionally by tests/relations/test_conversion_adapters.py's "
        "coerce_narwhals_dialect() pyarrow-target tests.",
        "2026-08-27",
    ),
    "NARWHALS_DIALECT_TO_PANDAS": (
        "Exercised functionally by tests/relations/test_conversion_adapters.py's "
        "coerce_narwhals_dialect() pandas-target tests.",
        "2026-08-27",
    ),
    "NARWHALS_DIALECT_TO_POLARS": (
        "Exercised functionally by tests/relations/test_conversion_adapters.py's "
        "coerce_narwhals_dialect() polars-target tests.",
        "2026-08-27",
    ),
    "NARWHALS_FROM_DICT_ADAPTER": (
        "Exercised functionally by tests/relations/test_conversion_adapters.py's "
        "coerce_to_narwhals() dict-operand cross-type-join tests.",
        "2026-08-27",
    ),
    "NARWHALS_FROM_DICTS_ADAPTER": (
        "Exercised functionally by tests/relations/test_conversion_adapters.py's "
        "coerce_to_narwhals() row-mapping-operand cross-type-join tests.",
        "2026-08-27",
    ),
    "NARWHALS_LAZY_COLLECT": (
        "Exercised functionally throughout tests/relations/cross_backend/ and "
        "tests/relations/test_native_materialization.py's Narwhals-lazy collection "
        "tests.",
        "2026-08-27",
    ),
    "NARWHALS_NATIVE_WRAP": (
        "Exercised functionally by tests/relations/test_resource_transit_boundaries.py's "
        "reader trace tests and tests/relations/dag/test_resource_read_cross_backend.py.",
        "2026-08-27",
    ),
    "NARWHALS_NATIVE_UNWRAP_NON_PANDAS": (
        "Exercised functionally by tests/relations/test_resource_transit_boundaries.py's "
        "schema-inspection tests and cross-backend collection tests.",
        "2026-08-27",
    ),
    "NARWHALS_SCHEMA_UNWRAP": (
        "Exercised functionally by tests/relations/test_resource_transit_boundaries.py's "
        "TestSchemaInspectionTrace (both the Polars- and pandas-backed unwrap paths).",
        "2026-08-27",
    ),
    "NARWHALS_TO_PANDAS_EGRESS": (
        "Exercised functionally by tests/relations/test_native_materialization.py's "
        "explicit_pandas_egress() non-pandas-Narwhals-source assertions.",
        "2026-08-27",
    ),
    "NARWHALS_TO_POLARS_EGRESS": (
        "Exercised functionally by tests/relations/test_native_materialization.py's "
        "explicit_polars_egress() Narwhals-source assertions.",
        "2026-08-27",
    ),
    "NATIVE_LAZY_COLLECT": (
        "Exercised functionally throughout tests/relations/, tests/datacontracts/"
        "test_result_processor_transit.py, and tests/relations/test_native_materialization.py.",
        "2026-08-27",
    ),
    "NON_PANDAS_ARROW_TERMINAL": (
        "Exercised functionally by tests/pydata/test_egress_all.py's to_pyarrow tests "
        "and tests/relations/test_resource_transit_boundaries.py's reader trace tests.",
        "2026-08-27",
    ),
    "PANDAS_TO_POLARS_EGRESS": (
        "Exercised functionally by tests/relations/test_native_materialization.py's "
        "explicit_polars_egress()/coerce_to_polars() pandas-source assertions.",
        "2026-08-27",
    ),
    "POLARS_TO_PANDAS_EGRESS": (
        "Exercised functionally by tests/relations/test_native_materialization.py's "
        "explicit_pandas_egress() Polars-source assertions and "
        "test_to_pandas_does_not_call_to_polars.",
        "2026-08-27",
    ),
    "DIAGNOSTIC_VIEW_FROM_ARROW": (
        "Exercised functionally by tests/relations/test_native_materialization.py's "
        "test_diagnostic_polars_view_from_ibis_uses_arrow_not_pandas.",
        "2026-08-27",
    ),
    "DIAGNOSTIC_VIEW_FROM_PANDAS": (
        "Exercised functionally by tests/relations/test_native_materialization.py's "
        "diagnostic-view pandas-source tests.",
        "2026-08-27",
    ),
    "DAG_PROTOTYPE_ADAPTER": (
        "Exercised functionally by tests/relations/dag/test_dag_cross_family_bare.py "
        "and test_dag_cross_family_derived.py's cross-dialect anchor-prototype tests.",
        "2026-08-27",
    ),
    "PIPELINE_STEP_EXECUTOR": (
        "Exercised functionally by tests/pipelines/'s PipelineStepRelNode executor "
        "tests; unrelated to any backend conversion, so no trace assertion applies.",
        "2026-08-27",
    ),
    "PYDATA_EXPLICIT_PANDAS_INPUT": (
        "Exercised functionally by tests/pydata/'s pandas-Series-dict ingress tests "
        "and tests/relations/dag/test_dag_cross_family_bare.py's prototype tests.",
        "2026-08-27",
    ),
    "PYDATA_EXPLICIT_PANDAS_EGRESS": (
        "Exercised functionally by tests/pydata/test_egress_all.py's "
        "test_to_pandas/test_to_dictionary_of_series_pandas.",
        "2026-08-27",
    ),
    "RELATION_TO_POLARS_TERMINAL": (
        "Exercised functionally across essentially every test in tests/relations/, "
        "tests/pydata/, tests/validation/, and tests/datacontracts/ that calls a "
        "Relation egress terminal or ValidationRunner rule.",
        "2026-08-27",
    ),
}


def test_every_boundary_key_is_referenced_in_production_or_tests():
    """spec section 13 Task 10 step 3: ``referenced_boundary_keys ==
    set(BOUNDARY_REGISTRY)`` -- no declared key is dead weight; every key
    is used at least once, in production code or a test."""
    referenced = _boundary_key_names(_SRC_ROOT, exclude=_TRANSIT_MODULE) | _boundary_key_names(
        _TESTS_ROOT
    )
    assert referenced == {key.name for key in BOUNDARY_REGISTRY}


def test_referenced_boundary_keys_are_exercised_or_documented_static_only():
    """spec section 13 Task 10 step 3: ``referenced_boundary_keys ==
    exercised_boundary_keys | static_only_boundary_keys``. A key is
    "exercised" when some test file names it literally (typically via
    `record.boundary_key is BoundaryKey.X` after `capture_conversion_trace()`,
    or a synthetic `transit_call(BoundaryKey.X, ...)` probe); otherwise it
    must appear in `_STATIC_ONLY_BOUNDARY_KEYS` with a reason and a valid
    ISO date."""
    referenced = _boundary_key_names(_SRC_ROOT, exclude=_TRANSIT_MODULE) | _boundary_key_names(
        _TESTS_ROOT
    )
    exercised = _boundary_key_names(_TESTS_ROOT)
    static_only = set(_STATIC_ONLY_BOUNDARY_KEYS)

    assert referenced == exercised | static_only
    # No stale entries: a key already exercised needs no static-only excuse.
    assert static_only.isdisjoint(exercised)
    all_names = {key.name for key in BoundaryKey}
    for name, (reason, since) in _STATIC_ONLY_BOUNDARY_KEYS.items():
        assert name in all_names, name
        assert len(reason) > 20, name
        date.fromisoformat(since)
