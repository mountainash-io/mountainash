import pytest
from scripts.select_tests import load_registry, select

pytestmark = pytest.mark.contract

REG = load_registry()  # default tests/selection/selectors.yaml


def test_select_returns_paths_only_no_marker_filter():
    # C1: a single -m contract command would FILTER affected paths down to
    # only contract tests. select() must return plain paths; contract runs
    # as a separate invocation.
    sel = select(["src/mountainash/pydata/ingress/x.py"], REG)
    assert "-m" not in sel
    # The pydata rule also pulls tests/integration (the e2e test exercises the
    # ingress factory) — see selectors.yaml. Still plain paths, no -m filter.
    assert sel == ["tests/pydata", "tests/integration"]


def test_expressions_change_pulls_in_downstream_dependents():
    # I1: relations and conform embed expression compilation; the e2e
    # integration test exercises the expression API too (tests/integration).
    sel = select(["src/mountainash/expressions/core/foo.py"], REG)
    assert set(sel) == {
        "tests/expressions",
        "tests/relations",
        "tests/conform",
        "tests/integration",
    }


def test_relations_change_pulls_in_conform_dependency():
    sel = select(["src/mountainash/relations/dag/dag.py"], REG)
    assert set(sel) == {"tests/relations", "tests/conform", "tests/integration"}


def test_typespec_change_pulls_in_conform():
    sel = select(["src/mountainash/typespec/spec.py"], REG)
    assert set(sel) == {"tests/typespec", "tests/conform", "tests/integration"}


def test_conform_change_pulls_in_pydata_and_relations():
    # conform/_build_conform_exprs is called by pydata ingress custom-type
    # helpers and by the relations visitor (.conform()), so a conform change
    # must select those test dirs (plus the e2e integration test).
    sel = select(["src/mountainash/conform/expressions.py"], REG)
    assert set(sel) == {
        "tests/conform",
        "tests/pydata",
        "tests/relations",
        "tests/integration",
    }


def test_cross_cutting_path_triggers_full_suite():
    sel = select(["src/mountainash/core/dtypes/canon.py"], REG)
    assert sel == ["tests"]


def test_unmatched_path_falls_back_to_full_suite():
    sel = select(["README.md"], REG)
    assert sel == ["tests"]
