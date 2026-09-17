"""Expected failures must belong to the selected call, never fixture setup."""

from pathlib import Path

import pytest

pytest_plugins = ["pytester"]
pytestmark = pytest.mark.contract


def test_exact_cell_and_error_do_not_absorb_other_failures(pytester, monkeypatch):
    for name in (
        "COVERAGE_PROCESS_START",
        "COVERAGE_PROCESS_CONFIG",
        "COVERAGE_FILE",
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COV_CORE_DATAFILE",
        "COV_CORE_CONTEXT",
    ):
        monkeypatch.delenv(name, raising=False)
    tests_root = str(Path(__file__).resolve().parents[1])
    pytester.makeconftest(f"""
import sys
sys.path.insert(0, {tests_root!r})
from fixtures.verification_bindings import ObserverSpec, attach_expectations, classify_call
from mountainash.core.capabilities.declarations import ManifestationKey, QualifiedManifestationKey
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import OperationTarget, Scenario
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK

key = QualifiedManifestationKey(
    Scope(CONST_BACKEND.POLARS, Dialect("polars")),
    ManifestationKey(OperationTarget(FK.LPAD), Scenario()),
)
specs = tuple(
    ObserverSpec(
        path="test_cases.py", function=name,
        parameters=(("case", "selected"),), key=key,
        oracle="test_cases.py::oracle", stage="materialization",
        errors=(("test_cases", "DeclaredError"),) if name == "test_subclass_error" else (("builtins", "AssertionError"),),
    )
    for name in (
        "test_selected",
        "test_other_error",
        "test_setup_error",
        "test_teardown_error",
        "test_unexpected_success",
        "test_subclass_error",
    )
)

def pytest_collection_modifyitems(items):
    attach_expectations(items, specs, reasons={{key: "known result difference"}}, root=__import__("pathlib").Path(__file__).parent)

import pytest

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    classify_call(item, call, outcome.get_result())
""")
    pytester.makepyfile(
        test_cases="""
import pytest

class DeclaredError(Exception):
    pass


class DerivedError(DeclaredError):
    pass


@pytest.mark.parametrize("case", ["selected", "other"])
def test_selected(case):
    assert False

@pytest.mark.parametrize("case", ["selected"])
def test_other_error(case):
    raise RuntimeError("unrelated execution error")

@pytest.fixture
def broken_setup():
    raise AssertionError("unrelated setup error")

@pytest.mark.parametrize("case", ["selected"])
def test_setup_error(case, broken_setup):
    assert False

@pytest.fixture
def broken_teardown():
    yield
    raise AssertionError("unrelated teardown error")

@pytest.mark.parametrize("case", ["selected"])
def test_teardown_error(case, broken_teardown):
    assert False


@pytest.mark.parametrize("case", ["selected"])
def test_subclass_error(case):
    raise DerivedError("subclass execution error")
@pytest.mark.parametrize("case", ["selected"])
def test_unexpected_success(case):
    pass
"""
    )
    result = pytester.runpytest_subprocess("-q", "--tb=short")
    result.assert_outcomes(xfailed=2, failed=4, errors=2)
    result.stdout.fnmatch_lines(
        [
            "*unrelated setup error*",
            "*unrelated teardown error*",
            "*unrelated execution error*",
            "*subclass execution error*",
        ]
    )


def test_missing_claim_is_a_collection_error(pytester, monkeypatch):
    for name in (
        "COVERAGE_PROCESS_START",
        "COVERAGE_PROCESS_CONFIG",
        "COVERAGE_FILE",
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COV_CORE_DATAFILE",
        "COV_CORE_CONTEXT",
    ):
        monkeypatch.delenv(name, raising=False)
    tests_root = str(Path(__file__).resolve().parents[1])
    pytester.makeconftest(f"""
import sys
sys.path.insert(0, {tests_root!r})
from fixtures.verification_bindings import ObserverSpec, attach_expectations
from mountainash.core.capabilities.declarations import ManifestationKey, QualifiedManifestationKey
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import OperationTarget, Scenario
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK
key = QualifiedManifestationKey(
    Scope(CONST_BACKEND.POLARS, Dialect("polars")),
    ManifestationKey(OperationTarget(FK.LPAD), Scenario()),
)
def pytest_collection_modifyitems(items):
    spec = ObserverSpec("test_case.py", "test_case", (), key, "oracle", "materialization", (("builtins", "AssertionError"),))
    attach_expectations(items, (spec,), reasons={{}}, root=__import__("pathlib").Path(__file__).parent)
""")
    pytester.makepyfile(test_case="def test_case():\n    assert False\n")
    result = pytester.runpytest_subprocess("-q")
    assert result.ret != 0
    assert "KeyError" in result.stdout.str()
    assert "xfailed" not in result.stdout.str()


@pytest.mark.parametrize("reader_name", ("capture_native_observations", "capture_selected_observations"))
def test_retained_native_outcome_cannot_silently_follow_a_changed_claim(reader_name):
    from dataclasses import replace
    from types import MappingProxyType

    from mountainash.core.capabilities.registry import CapabilityRegistry
    from tests.fixtures import verification_bindings

    reader = getattr(verification_bindings, reader_name)

    catalogue = CapabilityRegistry.capture()
    bindings, evidence = reader(catalogue)
    original = evidence[0].subjects[0]
    record = catalogue.get(original.key)
    changed = replace(record, assertion=replace(record.assertion, impact="changed impact"))
    manifestations = dict(catalogue._manifestations)
    manifestations[original.key] = changed
    newer = replace(catalogue, _manifestations=MappingProxyType(manifestations))

    with pytest.raises(ValueError, match="retained .* assertion digest"):
        reader(newer)

    moved_origin = replace(record.origins[0], entry="later-origin")
    moved_record = replace(record, origins=(moved_origin, *record.origins[1:]))
    manifestations[original.key] = moved_record
    later_catalogue = replace(catalogue, _manifestations=MappingProxyType(manifestations))
    _, later_evidence = reader(later_catalogue)

    assert later_evidence[0].subjects[0].address == original.address
    assert evidence[0].subjects[0].payload == record.assertion
    assert bindings[0].captured_claim == original


def test_selected_observation_retains_captured_interpreter_coordinate():
    import json

    from mountainash.core.capabilities.capture import EnvironmentCoordinate
    from mountainash.core.capabilities.registry import CapabilityRegistry
    from tests.fixtures.verification_bindings import capture_selected_observations

    _, evidence = capture_selected_observations(CapabilityRegistry.capture())
    artifact = Path(__file__).resolve().parents[1] / "fixtures/observations/selected_materialization.json"
    captured_python = json.loads(artifact.read_text())["python"]

    assert EnvironmentCoordinate("interpreter", "python", captured_python) in evidence[0].environment.coordinates


@pytest.mark.parametrize(
    "selector",
    (".", "test_case.py", "test_case.py::TestCase", "test_case.py::TestCase::test_case"),
    ids=("directory", "file", "class", "method"),
)
def test_observer_missing_required_parameter_is_a_collection_error(pytester, monkeypatch, selector):
    for name in (
        "COVERAGE_PROCESS_START",
        "COVERAGE_PROCESS_CONFIG",
        "COVERAGE_FILE",
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COV_CORE_DATAFILE",
        "COV_CORE_CONTEXT",
    ):
        monkeypatch.delenv(name, raising=False)
    tests_root = str(Path(__file__).resolve().parents[1])
    pytester.makeconftest(f"""
import sys
sys.path.insert(0, {tests_root!r})
from fixtures.verification_bindings import ObserverSpec, attach_expectations
from mountainash.core.capabilities.declarations import ManifestationKey, QualifiedManifestationKey
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import OperationTarget, Scenario
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK

key = QualifiedManifestationKey(
    Scope(CONST_BACKEND.POLARS, Dialect("polars")),
    ManifestationKey(OperationTarget(FK.LPAD), Scenario()),
)

def pytest_collection_modifyitems(config, items):
    spec = ObserverSpec(
        "test_case.py", "TestCase.test_case", (("case", "selected"),), key,
        "oracle", "materialization", (("builtins", "AssertionError"),),
    )
    attach_expectations(
        items, (spec,), reasons={{key: "known result difference"}},
        root=__import__("pathlib").Path(__file__).parent, requested=config.args,
    )
""")
    pytester.makepyfile(
        test_case="""
import pytest

class TestCase:
    @pytest.mark.parametrize("case", ["other"])
    def test_case(self, case):
        assert False
"""
    )
    result = pytester.runpytest_subprocess("-q", selector)
    assert result.ret != 0
    assert "observer did not match exactly one collected test cell" in result.stdout.str()


def test_deleted_or_renamed_observer_is_a_collection_error(pytester, monkeypatch):
    for name in (
        "COVERAGE_PROCESS_START",
        "COVERAGE_PROCESS_CONFIG",
        "COVERAGE_FILE",
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COV_CORE_DATAFILE",
        "COV_CORE_CONTEXT",
    ):
        monkeypatch.delenv(name, raising=False)
    tests_root = str(Path(__file__).resolve().parents[1])
    pytester.makeconftest(f"""
import sys
sys.path.insert(0, {tests_root!r})
from fixtures.verification_bindings import ObserverSpec, attach_expectations
from mountainash.core.capabilities.declarations import ManifestationKey, QualifiedManifestationKey
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import OperationTarget, Scenario
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK

key = QualifiedManifestationKey(
    Scope(CONST_BACKEND.POLARS, Dialect("polars")),
    ManifestationKey(OperationTarget(FK.LPAD), Scenario()),
)

def pytest_collection_modifyitems(config, items):
    spec = ObserverSpec(
        "test_case.py", "test_observer_was_renamed", (), key,
        "oracle", "materialization", (("builtins", "AssertionError"),),
    )
    attach_expectations(
        items, (spec,), reasons={{key: "known result difference"}},
        root=__import__("pathlib").Path(__file__).parent, requested=config.args,
    )
""")
    pytester.makepyfile(test_case="def test_case():\n    assert False\n")
    result = pytester.runpytest_subprocess("-q")
    assert result.ret != 0
    assert "observer did not match exactly one collected test cell" in result.stdout.str()


def test_explicit_parameter_selection_does_not_require_unselected_observer_cells(pytester, monkeypatch):
    for name in (
        "COVERAGE_PROCESS_START",
        "COVERAGE_PROCESS_CONFIG",
        "COVERAGE_FILE",
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COV_CORE_DATAFILE",
        "COV_CORE_CONTEXT",
    ):
        monkeypatch.delenv(name, raising=False)
    tests_root = str(Path(__file__).resolve().parents[1])
    pytester.makeconftest(f"""
import sys
sys.path.insert(0, {tests_root!r})
from fixtures.verification_bindings import ObserverSpec, attach_expectations
from mountainash.core.capabilities.declarations import ManifestationKey, QualifiedManifestationKey
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import OperationTarget, Scenario
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK

key = QualifiedManifestationKey(
    Scope(CONST_BACKEND.POLARS, Dialect("polars")),
    ManifestationKey(OperationTarget(FK.LPAD), Scenario()),
)

def pytest_collection_modifyitems(config, items):
    spec = ObserverSpec(
        "test_case.py", "test_case", (("case", "unselected"),), key,
        "oracle", "materialization", (("builtins", "AssertionError"),),
    )
    attach_expectations(
        items, (spec,), reasons={{key: "known result difference"}},
        root=__import__("pathlib").Path(__file__).parent, requested=config.args,
    )
""")
    pytester.makepyfile(
        test_case="""
import pytest

@pytest.mark.parametrize("case", ["selected", "unselected"])
def test_case(case):
    assert case == "selected"
"""
    )
    result = pytester.runpytest_subprocess("-q", "test_case.py::test_case[selected]")
    result.assert_outcomes(passed=1)


def test_relative_selector_uses_invocation_directory(tmp_path, monkeypatch):
    from dataclasses import replace

    from tests.fixtures.verification_bindings import attach_expectations, observer_specs

    nested = tmp_path / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    spec = replace(observer_specs()[0], path="nested/test_missing.py", function="test_missing", parameters=())

    with pytest.raises(ValueError, match="observer did not match exactly one collected test cell"):
        attach_expectations(
            (), (spec,), reasons={spec.key: "missing observer"}, root=tmp_path, requested=("test_missing.py",)
        )
