import pytest
from fixtures.backend_registry import REGISTRY, PR_BACKENDS, resolve_backend_scope

pytestmark = pytest.mark.contract


def test_full_scope_is_entire_registry():
    assert resolve_backend_scope("full") == list(REGISTRY)


def test_pr_scope_is_one_per_family():
    pr = resolve_backend_scope("pr")
    assert pr == ["polars", "narwhals-polars", "ibis-duckdb"]
    families = {REGISTRY[name].family for name in pr}
    assert families == {"polars-eager", "narwhals", "ibis"}


def test_pr_backends_constant_matches_resolver():
    assert PR_BACKENDS == resolve_backend_scope("pr")


def test_unknown_scope_falls_back_to_full():
    assert resolve_backend_scope("nonsense") == list(REGISTRY)


def test_pr_scope_filters_parametrize_ids_correctly(pytester):
    # A backend-specific xfail must stay attached to the right backend param
    # when the matrix is scope-filtered — no id shifting / misattribution.
    tests_dir = str(__import__('pathlib').Path(__file__).parent.parent)
    pytester.makeconftest(
        "import sys; sys.path.insert(0, r'%s')\n"
        "import os, sys as _sys\n"
        "for _i, _a in enumerate(_sys.argv):\n"
        "    if _a == '--ma-backend-scope' and _i + 1 < len(_sys.argv):\n"
        "        os.environ['MA_BACKEND_SCOPE'] = _sys.argv[_i + 1]\n"
        "    elif _a.startswith('--ma-backend-scope='):\n"
        "        os.environ['MA_BACKEND_SCOPE'] = _a.split('=', 1)[1]\n"
        "def pytest_addoption(parser):\n"
        "    parser.addoption('--ma-backend-scope', action='store', default=None,\n"
        "        choices=['pr', 'full'],\n"
        "        help='Backend matrix scope')\n"
        % tests_dir
    )
    pytester.makepyfile(
        """
        import pytest
        from fixtures.backend_registry import ALL_BACKENDS

        @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
        def test_matrix(backend_name):
            if backend_name == "ibis-duckdb":
                pytest.xfail("known: ibis-duckdb")
            assert backend_name
        """
    )
    result = pytester.runpytest_subprocess("--ma-backend-scope", "pr", "-q")
    # 3 backends in pr scope: polars + narwhals-polars pass, ibis-duckdb xfails.
    result.assert_outcomes(passed=2, xfailed=1)
