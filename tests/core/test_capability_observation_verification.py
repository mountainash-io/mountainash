"""Controlled verification rejects unknown observations independently of matching."""

import pytest

from mountainash.core.capabilities.applicability import (
    Applicability,
    CoordinateConstraint,
    Region,
    prepare_environment,
    unbounded,
)
from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate
from tests.fixtures.capability_observations import require_observations


def test_nonmatch_and_union_match_do_not_excuse_missing_engine():
    package = CoordinateConstraint("package", "ibis", specifier="==11")
    engine = CoordinateConstraint("engine", "duckdb", specifier=">=1")
    conjunction = Applicability((Region((package, engine)),))
    union = Applicability((Region((package,)), Region((engine,))))
    wrong = Environment((EnvironmentCoordinate("package", "ibis", "12"),))
    matching = Environment((EnvironmentCoordinate("package", "ibis", "11"),))
    assert conjunction.match(prepare_environment(wrong, conjunction.requirements)).value == "not_applicable"
    assert union.match(prepare_environment(matching, union.requirements)).value == "applicable"
    with pytest.raises(AssertionError):
        require_observations(conjunction, wrong)
    with pytest.raises(AssertionError):
        require_observations(union, matching)


@pytest.mark.parametrize("raw", [None, "vendor-build"])
def test_required_version_observation_cannot_pass_as_fallback(raw):
    claim = Applicability((Region((CoordinateConstraint("engine", "duckdb", specifier="!=1"),)),))
    with pytest.raises(AssertionError):
        require_observations(claim, Environment((EnvironmentCoordinate("engine", "duckdb", raw),)))


def test_valid_nonmatch_and_unbounded_are_valid_verification_inputs():
    claim = Applicability((Region((CoordinateConstraint("package", "ibis", specifier="==11"),)),))
    environment = Environment((EnvironmentCoordinate("package", "ibis", "12"),))
    assert claim.match(require_observations(claim, environment)).value == "not_applicable"
    assert unbounded.match(require_observations(unbounded, Environment())).value == "applicable"


def test_literal_and_opaque_labels_do_not_require_version_parsing():
    claim = Applicability(
        (
            Region(
                (
                    CoordinateConstraint("package", "ibis", specifier="===vendor-build"),
                    CoordinateConstraint("adapter", "driver", opaque_equal="ACME"),
                )
            ),
        )
    )
    environment = Environment(
        (
            EnvironmentCoordinate("package", "ibis", "vendor-build"),
            EnvironmentCoordinate("adapter", "driver", "ACME"),
        )
    )
    assert claim.match(require_observations(claim, environment)).value == "applicable"
