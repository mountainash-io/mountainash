"""Closed-by-default coverage for the shared KnownGap collection."""

from pathlib import Path
import sys

import core.test_protocol_alignment as pa
from expressions.argument_types import test_coverage_guard as cg
import relations.test_rel_wiring_audit_registry as rw

from mountainash.core.capabilities import KnownGap
from mountainash.core.capabilities.schema import ProtocolMethodTarget
from tests.fixtures.gap_collection import collect_all_gap_sets


def test_every_core_known_gap_dict_is_collected():
    """Every module-level core KnownGap dict must be exposed for reporting."""
    gap_modules = (pa, cg, rw)
    root = Path(__file__).resolve().parents[2]
    discovered = {
        (Path(module.__file__).resolve().relative_to(root).as_posix(), name): f"{module.__name__}.{name}"
        for module in gap_modules
        for name, value in vars(module).items()
        if isinstance(value, dict)
        and value
        and all(isinstance(gap, KnownGap) for gap in value.values())
    }
    collected = {
        (inventory.owner.path, inventory.owner.entry)
        for inventory in collect_all_gap_sets().inventories
    }

    missing = set(discovered) - collected
    assert not missing, "\n".join(
        "core-KnownGap dict "
        f"{discovered[gap_id]} is not in the captured inventories — add it "
        "(closed-by-default)"
        for gap_id in sorted(missing, key=discovered.__getitem__)
    )


def test_gap_capture_preserves_original_protocol_keys_and_payloads():
    from mountainash.core.capabilities.schema import CallableRef

    capture = collect_all_gap_sets()
    inventory = next(item for item in capture.inventories if item.name == "expr.aspirational")
    expected = {
        (CallableRef(protocol.__module__, protocol.__qualname__), method): gap
        for (protocol, method), gap in pa.KNOWN_ASPIRATIONAL.items()
    }
    assert {record.original_key: record.payload for record in inventory.gaps} == expected



def test_gap_capture_preserves_all_owner_keys_payloads_and_histories():
    from mountainash.core.capabilities.schema import CallableRef

    owners = (
        ("expr.aspirational", pa, "KNOWN_ASPIRATIONAL"),
        ("expr.aspirational_and_tested", pa, "KNOWN_ASPIRATIONAL_AND_TESTED"),
        ("rel.aspirational", rw, "KNOWN_ASPIRATIONAL"),
        ("argtypes.untested_argument", cg, "_KNOWN_UNTESTED_ARGUMENT_PARAMS"),
        ("argtypes.metadata_only", cg, "_KNOWN_METADATA_ONLY_TESTED_PARAMS"),
        ("argtypes.untested_option", cg, "_KNOWN_UNTESTED_OPTION_PARAMS"),
        ("argtypes.unwired_ops", cg, "_KNOWN_UNWIRED_TESTED_OPS"),
        ("argtypes.unresolved_params", cg, "_KNOWN_UNRESOLVED_TESTED_PARAMS"),
        ("argtypes.special_node_unwired_ops", cg, "_KNOWN_SPECIAL_NODE_UNWIRED_OPS"),
        ("argtypes.unresolved_param_gaps", cg, "_KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_GAPS"),
        ("argtypes.allowed_cross_category", cg, "_ALLOWED_CROSS_CATEGORY_TESTED_PARAMS"),
    )
    snapshot = collect_all_gap_sets()

    assert len(snapshot.inventories) == 11
    assert len(snapshot.gaps) == 664
    for name, module, attribute in owners:
        inventory = next(item for item in snapshot.inventories if item.name == name)
        expected = {
            tuple(
                CallableRef(part.__module__, part.__qualname__) if isinstance(part, type) else part
                for part in original
            ): payload
            for original, payload in getattr(module, attribute).items()
        }
        assert {record.original_key: record.payload for record in inventory.gaps} == expected
        assert inventory.changes == tuple(
            change for change in module.GAP_CHANGES if change.prior.key.inventory == name
        )


def test_gap_capture_retains_resolved_protocol_authorities_after_source_changes(monkeypatch):
    snapshot = collect_all_gap_sets()
    record = next(gap for gap in snapshot.gaps if type(gap.key.target) is ProtocolMethodTarget)
    target = record.key.target
    protocol = next(
        candidate
        for _, candidate in cg._iter_protocol_classes()
        if (candidate.__module__, candidate.__qualname__)
        == (target.protocol.module, target.protocol.qualname)
    )
    authority_path = Path(sys.modules[protocol.__module__].__file__).resolve()
    root = Path(__file__).resolve().parents[2]
    authority = next(
        reference
        for reference in record.reference_context
        if reference.path == authority_path.relative_to(root).as_posix()
        and reference.entry == protocol.__qualname__
    )
    original = authority.artifact
    assert original == authority_path.read_bytes()
    same_source_references = [
        reference
        for gap in snapshot.gaps
        for reference in gap.reference_context
        if reference.path == authority.path
    ]
    assert same_source_references
    assert all(reference.artifact is original for reference in same_source_references)

    defining_class = next(
        candidate for candidate in protocol.__mro__ if target.method in candidate.__dict__
    )
    if defining_class is not protocol:
        defining_path = Path(sys.modules[defining_class.__module__].__file__).resolve()
        assert any(
            reference.path == defining_path.relative_to(root).as_posix()
            and reference.entry == f"{defining_class.__qualname__}.{target.method}"
            for reference in record.reference_context
        )

    original_read_bytes = Path.read_bytes

    def changed_read_bytes(path):
        if path.resolve() == authority_path:
            return b"changed protocol authority"
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", changed_read_bytes)
    later = collect_all_gap_sets()
    later_record = next(gap for gap in later.gaps if gap.key == record.key)
    later_authority = next(
        reference
        for reference in later_record.reference_context
        if reference.path == authority.path and reference.entry == authority.entry
    )
    assert authority.artifact == original
    assert later_authority.artifact == b"changed protocol authority"

def test_catalogue_requires_explicit_verification_capture():
    import pytest

    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.capabilities.catalogue import (
        CatalogueQuery, GapQuery, UncapturedNamespaceError,
    )
    from mountainash.core.capabilities.gaps import VerificationSnapshot

    query = CatalogueQuery(gaps=GapQuery(inventory="expr.aspirational"))
    with pytest.raises(UncapturedNamespaceError):
        CapabilityRegistry.capture().search(query)
    snapshot = collect_all_gap_sets()
    capture = CapabilityRegistry.capture(verification=snapshot)
    expected = tuple(record for record in snapshot.gaps if record.key.inventory == "expr.aspirational")
    assert capture.search(query).gaps == expected
    assert capture.search(query).gaps[0] is expected[0]
    empty = CapabilityRegistry.capture(verification=VerificationSnapshot(()))
    assert empty.search(CatalogueQuery(gaps=GapQuery())).gaps == ()
    with pytest.raises(UncapturedNamespaceError):
        empty.search(query)


def test_gap_retirement_preserves_predecessor_and_old_snapshot(monkeypatch):
    from mountainash.core.capabilities.capture import CapturedAddress, CapturedAssertion
    from mountainash.core.capabilities.retired import AssertionChange, ChangeDisposition
    from mountainash.core.capabilities.catalogue import CatalogueQuery, ChangeQuery
    from mountainash.core.capabilities.registry import CapabilityRegistry

    before = collect_all_gap_sets()
    inventory = next(item for item in before.inventories if item.name == "expr.aspirational")
    record = inventory.gaps[0]
    original = next(key for key, gap in pa.KNOWN_ASPIRATIONAL.items() if gap is record.payload)
    source = Path(__file__)
    change = AssertionChange(
        CapturedAddress("mountainash", "tests/core/test_gap_collection_complete.py", "retirement fixture", artifact=source.read_bytes()),
        CapturedAssertion("gap", record.key, record, record.origins[0]),
        ChangeDisposition.LOCAL_IMPLEMENTATION_FIX,
        "2026-09-16", "Retirement fixture verifies independent history retention",
    )
    monkeypatch.setattr(pa, "GAP_CHANGES", (*pa.GAP_CHANGES, change))
    monkeypatch.delitem(pa.KNOWN_ASPIRATIONAL, original)
    after = collect_all_gap_sets()
    assert record in before.gaps
    assert all(gap.key != record.key for gap in after.gaps)
    assert after.changes[-1].prior.payload is record
    assert change not in before.changes
    query = CatalogueQuery(changes=ChangeQuery(inventory=inventory.name, prior=change.prior))
    assert CapabilityRegistry.capture(verification=before).search(query).changes == ()
    retained = CapabilityRegistry.capture(verification=after).search(query).changes
    assert retained == (change,)
    assert retained[0].prior.payload is record
    assert CapabilityRegistry.capture(verification=after).search(
        CatalogueQuery(changes=ChangeQuery(inventory=inventory.name), scopes=frozenset())
    ).changes == ()
