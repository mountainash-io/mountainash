import pytest
from selection.tiers import TIERS, resolve_tier

pytestmark = pytest.mark.contract


@pytest.mark.parametrize("nodeid,expected", [
    ("tests/expressions/cross_backend/test_window_results.py::test_x", "cross_backend"),
    ("tests/relations/cross_backend/test_rel_join_results.py::test_x", "cross_backend"),
    ("tests/relations/dag/test_dag.py::test_x", "integration"),
    ("tests/integration/test_end_to_end.py::test_x", "integration"),
    ("tests/pipelines/integration/test_pipe.py::test_x", "integration"),
    ("tests/core/test_signature_conformance.py::test_x", "contract"),
    ("tests/expressions/test_protocol_alignment.py::test_x", "contract"),
    ("tests/expressions/ast/test_nodes.py::test_x", "unit"),
    ("tests/pydata/mappers/test_map.py::test_x", "unit"),
])
def test_resolve_known_paths(nodeid, expected):
    assert resolve_tier(nodeid) == expected


def test_resolver_only_returns_valid_tiers_or_none():
    assert resolve_tier("tests/somewhere/unknown_shape.py::t") in (*TIERS, None)


def test_unknown_root_is_none_not_silently_defaulted():
    # Closed-by-default: a test under a root with no rule must return None so
    # the audit fails, not be silently classified.
    assert resolve_tier("tests/brand_new_module/test_x.py::t") is None


def test_tiers_are_the_canonical_four():
    assert TIERS == ("unit", "cross_backend", "integration", "contract")
