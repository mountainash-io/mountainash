"""Case-local expectations must not swallow unrelated or fixture failures."""

from pathlib import Path

import pytest

pytest_plugins = ["pytester"]
pytestmark = pytest.mark.contract


def test_known_call_failure_preserves_xpass_and_unrelated_errors(pytester, monkeypatch):
    """Wrong phase, exception subtype, or successful call cannot satisfy a defect."""
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
    pytester.makeconftest(f"import sys\nsys.path.insert(0, {tests_root!r})\n")
    pytester.makepyfile(
        test_cases="""
import pytest
from fixtures.call_expectations import expect_call_failure


class DeclaredError(Exception):
    pass


class DerivedError(DeclaredError):
    pass


@pytest.mark.parametrize("selected", [True, False])
def test_call(selected):
    with expect_call_failure(
        when=selected, reason="known wrong result", errors=(AssertionError,)
    ):
        assert 1 == 2


def test_unrelated_error():
    with expect_call_failure(reason="known wrong result", errors=(AssertionError,)):
        raise RuntimeError("unrelated execution error")


def test_subclass_error():
    with expect_call_failure(reason="known native issue", errors=(DeclaredError,)):
        raise DerivedError("different native error subtype")


def test_corrected_result():
    with expect_call_failure(reason="known wrong result", errors=(AssertionError,)):
        assert 2 + 2 == 4


@pytest.fixture
def broken_setup():
    raise AssertionError("unrelated setup error")


def test_setup_error(broken_setup):
    with expect_call_failure(reason="known wrong result", errors=(AssertionError,)):
        assert 1 == 2


@pytest.fixture
def broken_teardown():
    yield
    raise AssertionError("unrelated teardown error")


def test_teardown_error(broken_teardown):
    with expect_call_failure(reason="known wrong result", errors=(AssertionError,)):
        assert 1 == 2


from dataclasses import replace

import mountainash as ma
import polars as pl
from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.applicability import (
    Applicability,
    ApplicabilityResult,
    ComparisonScheme,
    CoordinateConstraint,
    Region,
    prepare_environment,
)
from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityInformation,
    CapabilityKey,
    CapabilitySegment,
    Domain,
    QualifiedInformationKey,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.registry import _LoadState, _empty_state
from mountainash.core.capabilities.schema import InformationLayer
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK,
)


_EXPECTATION_SCOPE = Scope(CONST_BACKEND.POLARS, Dialect("polars"))
_REFERENCE = QualifiedInformationKey(
    _EXPECTATION_SCOPE,
    CapabilityKey(FK.CONTAINS, "substring"),
    InformationLayer.NATIVE,
)
_CLAIM = Applicability((
    Region((
        CoordinateConstraint(
            "package",
            "polars",
            ComparisonScheme.PEP440,
            lower="1.2",
            upper="1.3",
            upper_inclusive=False,
        ),
    )),
))

CapabilityRegistry.restore(_empty_state(_LoadState.LOADED))
CapabilityRegistry.register_segment(BoundSegment(
    "mountainash.expressions.backends.capabilities.polars.dialects.polars.substrait.string.expectations",
    _EXPECTATION_SCOPE,
    CapabilitySegment(
        Domain.STRING,
        information=(CapabilityInformation(
            key=_REFERENCE.local,
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-09-21",
            message="Controlled test-owned expectation reference",
            applicability=_CLAIM,
        ),),
    ),
))


@pytest.mark.parametrize("mode", ("checked", "native_debugging", "trusted"))
@pytest.mark.parametrize("observed", ("1.2", "1.3", None))
def test_exact_reference_is_checked_before_inactive_or_unknown_applicability(mode, observed):
    # This exact lookup is deliberately before environment construction/matching for
    # every cell, including the inactive (1.3) and indeterminate (None) cells.
    information = CapabilityRegistry.capture().get(_REFERENCE)
    environment = Environment((EnvironmentCoordinate("package", "polars", observed),))
    applicability = information.assertion.applicability
    result = applicability.match(prepare_environment(environment, applicability.requirements))

    with ma.capability_policy(getattr(ma.CapabilityPolicy, mode)()):
        with expect_call_failure(
            reason="controlled test-owned result defect",
            errors=(AssertionError,),
            when=result is ApplicabilityResult.APPLICABLE,
        ):
            actual = pl.DataFrame({"text": ["a", "b"]}).select(
                pl.col("text").str.contains("a").alias("found")
            )["found"].to_list()
            assert actual == [False, False]  # deliberately failing test-owned oracle


@pytest.mark.parametrize("mode", ("checked", "native_debugging", "trusted"))
def test_exact_reference_keeps_corrected_result_strict_xpass_under_every_policy(mode):
    # Lookup remains unconditional and precedes matching; runtime policy only wraps
    # the ordinary assertion and cannot relax this strict-XPASS path.
    information = CapabilityRegistry.capture().get(_REFERENCE)
    environment = Environment((EnvironmentCoordinate("package", "polars", "1.2"),))
    applicability = information.assertion.applicability
    result = applicability.match(prepare_environment(environment, applicability.requirements))

    with ma.capability_policy(getattr(ma.CapabilityPolicy, mode)()):
        with expect_call_failure(
            reason="controlled test-owned result defect",
            errors=(AssertionError,),
            when=result is ApplicabilityResult.APPLICABLE,
        ):
            actual = pl.DataFrame({"text": ["a", "b"]}).select(
                pl.col("text").str.contains("a").alias("found")
            )["found"].to_list()
            assert actual == [True, False]


@pytest.mark.parametrize("mode", ("checked", "native_debugging", "trusted"))
@pytest.mark.parametrize("observed", ("1.3", None))
def test_missing_exact_reference_is_not_hidden_by_inactive_or_unknown_scope(mode, observed):
    missing = replace(_REFERENCE, local=replace(_REFERENCE.local, variant="missing"))
    with ma.capability_policy(getattr(ma.CapabilityPolicy, mode)()):
        information = CapabilityRegistry.capture().get(missing)
        environment = Environment((EnvironmentCoordinate("package", "polars", observed),))
        applicability = information.assertion.applicability
        result = applicability.match(prepare_environment(environment, applicability.requirements))
        with expect_call_failure(
            reason="controlled missing reference",
            errors=(AssertionError,),
            when=result is ApplicabilityResult.APPLICABLE,
        ):
            actual = pl.DataFrame({"text": ["a", "b"]}).select(
                pl.col("text").str.contains("a").alias("found")
            )["found"].to_list()
            assert actual == [True, False]
"""
    )
    result = pytester.runpytest_subprocess("-q", "--tb=short")
    result.assert_outcomes(xfailed=5, failed=19, errors=2)
    result.stdout.fnmatch_lines(
        [
            "*unrelated setup error*",
            "*unrelated teardown error*",
            "*unrelated execution error*",
            "*different native error subtype*",
            "*XPASS(strict)*",
        ]
    )
