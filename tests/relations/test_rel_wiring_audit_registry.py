"""Closed-by-default wiring audit for relation operations (spec §3.10).

Mirrors tests/core/test_protocol_alignment.py TestWiringAudit for the
relations subsystem: every protocol method must have a registry row and an
implementation on all three backends, aspirational gaps are dated and
strict-xfailed, every RKEY has a def, and every node type is dispatchable.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass

import pytest

from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem
from mountainash.relations.core.relation_nodes.reln_base import RelationNode
from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)
from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitAggregateRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitReadRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
    RKEY_SUBSTRAIT_REL,
)
from mountainash.relations.core.relation_system.relation_mapping.registry import (
    RelationOperationRegistry,
)
from mountainash.relations.core.unified_visitor.visit_registry import (
    RelationVisitRegistry,
)

# Closed-by-default: no ImportError guards. If narwhals or ibis is missing
# from the test environment, this file must ERROR, not silently audit a
# smaller backend matrix (closed-by-default-verification principle). The
# existing cross-backend suites already import both unconditionally.
from mountainash.relations.backends.relation_systems.ibis import IbisRelationSystem
from mountainash.relations.backends.relation_systems.narwhals import (
    NarwhalsRelationSystem,
)

BACKENDS = {
    "Polars": PolarsRelationSystem,
    "Narwhals": NarwhalsRelationSystem,
    "Ibis": IbisRelationSystem,
}

REL_WIRING_PROTOCOL_REGISTRY = {
    SubstraitReadRelationSystemProtocol: "substrait_read",
    SubstraitProjectRelationSystemProtocol: "substrait_project",
    SubstraitFilterRelationSystemProtocol: "substrait_filter",
    SubstraitSortRelationSystemProtocol: "substrait_sort",
    SubstraitFetchRelationSystemProtocol: "substrait_fetch",
    SubstraitJoinRelationSystemProtocol: "substrait_join",
    SubstraitAggregateRelationSystemProtocol: "substrait_aggregate",
    SubstraitSetRelationSystemProtocol: "substrait_set",
    MountainashExtensionRelationSystemProtocol: "mountainash_extension",
}


@dataclass(frozen=True)
class KnownGap:
    reason: str
    since: str  # "Since YYYY-MM-DD ..."


KNOWN_ASPIRATIONAL: dict[tuple[type, str], KnownGap] = {
    (SubstraitSetRelationSystemProtocol, "union_multiset"): KnownGap(
        "Substrait SetOp domain; no consumer demand yet", "Since 2026-07-03"
    ),
    (SubstraitSetRelationSystemProtocol, "minus_primary"): KnownGap(
        "Substrait SetOp domain; no consumer demand yet", "Since 2026-07-03"
    ),
    (SubstraitSetRelationSystemProtocol, "minus_multiset"): KnownGap(
        "Substrait SetOp domain; no consumer demand yet", "Since 2026-07-03"
    ),
    (SubstraitSetRelationSystemProtocol, "intersection_primary"): KnownGap(
        "Substrait SetOp domain; no consumer demand yet", "Since 2026-07-03"
    ),
    (SubstraitSetRelationSystemProtocol, "intersection_multiset"): KnownGap(
        "Substrait SetOp domain; no consumer demand yet", "Since 2026-07-03"
    ),
}


def _protocol_methods(protocol_cls: type) -> list[str]:
    return sorted(
        n for n, m in vars(protocol_cls).items()
        if callable(m) and not n.startswith("_")
    )


def _registry_has(protocol_cls: type, method_name: str) -> bool:
    qual = f"{protocol_cls.__name__}.{method_name}"
    for key in RelationOperationRegistry.list_all():
        pm = RelationOperationRegistry.get(key).protocol_method
        if pm is None:
            continue
        if pm.__qualname__ == qual or pm is vars(protocol_cls).get(method_name):
            return True
    return False


_WIRED_CASES = [
    (proto, m)
    for proto in REL_WIRING_PROTOCOL_REGISTRY
    for m in _protocol_methods(proto)
    if (proto, m) not in KNOWN_ASPIRATIONAL
]
_ASPIRATIONAL_CASES = list(KNOWN_ASPIRATIONAL.items())


class TestWiringAudit:
    @pytest.mark.parametrize(
        "protocol_cls,method_name", _WIRED_CASES,
        ids=[f"{p.__name__}.{m}" for p, m in _WIRED_CASES],
    )
    def test_protocol_method_wired(self, protocol_cls, method_name):
        assert _registry_has(protocol_cls, method_name), (
            f"{protocol_cls.__name__}.{method_name} has no "
            f"RelationOperationRegistry row"
        )
        for backend_name, backend_cls in BACKENDS.items():
            assert hasattr(backend_cls, method_name), (
                f"{backend_name} lacks {method_name}"
            )

    @pytest.mark.parametrize(
        "case,gap", _ASPIRATIONAL_CASES,
        ids=[f"{p.__name__}.{m}" for (p, m), _ in _ASPIRATIONAL_CASES],
    )
    @pytest.mark.xfail(strict=True, reason="aspirational — see KNOWN_ASPIRATIONAL")
    def test_aspirational_method(self, case, gap):
        protocol_cls, method_name = case
        assert _registry_has(protocol_cls, method_name)

    def test_every_aspirational_entry_has_reason_and_date(self):
        for (proto, m), gap in KNOWN_ASPIRATIONAL.items():
            assert gap.reason, (proto, m)
            assert gap.since.startswith("Since 20"), (proto, m)

    def test_no_stale_aspirational_entries(self):
        for proto, m in KNOWN_ASPIRATIONAL:
            assert m in _protocol_methods(proto), (
                f"stale KNOWN_ASPIRATIONAL entry: {proto.__name__}.{m}"
            )


class TestNoOrphanKeys:
    def test_every_rkey_has_a_definition(self):
        registered = set(RelationOperationRegistry.list_all())
        all_keys = set(RKEY_SUBSTRAIT_REL) | set(RKEY_MOUNTAINASH_REL)
        missing = {k.name for k in (all_keys - registered)}
        assert not missing, f"RKEYs without registry defs: {sorted(missing)}"

    def test_every_definition_dispatches(self):
        for key in RelationOperationRegistry.list_all():
            d = RelationOperationRegistry.get(key)
            assert d.protocol_method is not None or d.handler is not None, key


class TestProvenanceClassification:
    def test_every_relation_def_has_valid_classification(self):
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            RelationOperationRegistry,
            classify_relation_def,
        )

        # NOTE: list_all() (registry.py:132-135) returns operation KEYS, not defs —
        # fetch each def with .get(key), matching the existing audit tests
        # (test_rel_wiring_audit_registry.py:103-107, :165-167).
        invalid = [
            key
            for key in RelationOperationRegistry.list_all()
            if classify_relation_def(RelationOperationRegistry.get(key)) is None
        ]
        assert not invalid, (
            "RelationOperationDefs with invalid serialization classification "
            "(each must be exactly one of direct / lowered / extension, spec §5.4):\n"
            + "\n".join(f"  - {k}" for k in invalid)
        )


class TestNodeCoverage:
    def _all_node_subclasses(self):
        import mountainash.relations  # noqa: F401  (loads core nodes)

        seen, stack = set(), [RelationNode]
        while stack:
            cls = stack.pop()
            for sub in cls.__subclasses__():
                if sub not in seen:
                    seen.add(sub)
                    stack.append(sub)
        return seen

    def test_every_node_type_is_dispatchable(self):
        undispatchable = []
        for cls in self._all_node_subclasses():
            if inspect.isabstract(cls):
                continue
            if cls.__name__.startswith("_"):
                continue
            if cls.__module__.startswith("tests."):
                continue
            has_handler = RelationVisitRegistry.get(cls) is not None
            has_key = (
                getattr(cls, "_operation_key", None) is not None
                or cls.operation_key is not RelationNode.operation_key
            )
            if not (has_handler or has_key):
                undispatchable.append(cls.__name__)
        assert not undispatchable, (
            f"RelationNode subclasses with no dispatch path: {undispatchable}"
        )


class TestBindingConformance:
    def test_registry_initializes_cleanly(self):
        # Registration-time validation ran for every def (spec §3.5).
        # No count assertion (count-based validation is an anti-pattern);
        # completeness is owned by TestNoOrphanKeys, which derives the
        # expected set from the enums themselves.
        RelationOperationRegistry.list_all()  # must not raise

    def test_declarative_defs_match_protocol_arity(self):
        for key in RelationOperationRegistry.list_all():
            d = RelationOperationRegistry.get(key)
            if d.handler is not None or d.protocol_method is None or d.node_type is None:
                continue
            sig = d.get_signature()
            positional = [
                p for p in list(sig.parameters.values())[1:]
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                              inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            assert len(positional) == len(d.args), key


from mountainash.core.limitations import MATERIALIZE_BOUNDARY, WILDCARD_PARAM


class TestLimitationKeyConformance:
    def test_limitation_keys_reference_real_params_or_wildcard(self):
        offenders = []
        for backend_name, backend_cls in BACKENDS.items():
            table = getattr(backend_cls, "KNOWN_REL_LIMITATIONS", {})
            for (op_key, param) in table:
                if param == WILDCARD_PARAM:
                    continue
                if op_key is MATERIALIZE_BOUNDARY:
                    continue
                try:
                    d = RelationOperationRegistry.get(op_key)
                except KeyError:
                    offenders.append(f"{backend_name}: unknown op {op_key}")
                    continue
                bound = {b.field for b in d.args} | set(d.options)
                if d.get_signature() is not None:
                    bound |= set(d.get_signature().parameters)
                if param not in bound:
                    offenders.append(f"{backend_name}: ({op_key}, {param!r})")
        assert not offenders, f"limitation keys referencing nothing real: {offenders}"
