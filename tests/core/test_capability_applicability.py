"""Public capability applicability algebra contracts."""

import pytest


@pytest.mark.parametrize(("wrapper", "engine", "expected"), [
    ("12.0.0", "1.1", "not_applicable"),
    ("12.0.0", "1.2", "applicable"),
    ("12.0.0", "1.3", "not_applicable"),
    ("12.0.0", "1.4", "applicable"),
    ("12.0.0", None, "indeterminate"),
    ("12.0.0", "vendor-build", "indeterminate"),
    ("11.0.0", None, "not_applicable"),
])
def test_wrapper_engine_recurrence_preserves_gap_and_uncertainty(wrapper, engine, expected):
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
        prepare_environment,
    )
    from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate

    claim = Applicability(tuple(
        Region((
            CoordinateConstraint("package", "IBIS", ComparisonScheme.PEP440, equal="12.0.0"),
            CoordinateConstraint(
                "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
                lower=lower, upper=upper, upper_inclusive=False,
            ),
        ))
        for lower, upper in (("1.2", "1.3"), ("1.4", "1.5"))
    ))
    observed = Environment((
        EnvironmentCoordinate("package", "ibis-framework", wrapper),
        EnvironmentCoordinate("engine", "duckdb", engine),
    ))

    assert claim.match(prepare_environment(observed, claim.requirements)).value == expected


@pytest.mark.parametrize(("observed", "expected"), [
    ("1.0a1", "not_applicable"),
    ("1.0rc1", "applicable"),
    ("1.0", "applicable"),
    ("1.0+build.7", "applicable"),
    ("1.0.post1", "not_applicable"),
])
def test_pep440_bounds_order_prerelease_postrelease_and_local_versions(observed, expected):
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
        prepare_environment,
    )
    from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate

    claim = Applicability((Region((
        CoordinateConstraint(
            "package", "ibis", ComparisonScheme.PEP440,
            lower="1.0rc1", upper="1.0.post1", upper_inclusive=False,
        ),
    )),))
    environment = Environment((EnvironmentCoordinate("package", "ibis", observed),))

    assert claim.match(prepare_environment(environment, claim.requirements)).value == expected


def test_numeric_release_equates_trailing_zero_components():
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
        prepare_environment,
    )
    from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate

    claim = Applicability((Region((
        CoordinateConstraint("engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE, equal="1.2"),
    )),))
    environment = Environment((EnvironmentCoordinate("engine", "duckdb", "1.2.0"),))

    assert claim.match(prepare_environment(environment, claim.requirements)).value == "applicable"


@pytest.mark.parametrize(("observed", "expected"), [
    ("vendor-build", "applicable"),
    ("vendor-build.1", "not_applicable"),
])
def test_opaque_constraints_require_exact_observed_equality(observed, expected):
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
        prepare_environment,
    )
    from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate

    claim = Applicability((Region((
        CoordinateConstraint("adapter", "driver", ComparisonScheme.OPAQUE, equal="vendor-build"),
    )),))
    environment = Environment((EnvironmentCoordinate("adapter", "driver", observed),))

    assert claim.match(prepare_environment(environment, claim.requirements)).value == expected


def test_opaque_constraints_reject_ordered_bounds():
    from mountainash.core.capabilities.applicability import ComparisonScheme, CoordinateConstraint

    with pytest.raises(ValueError):
        CoordinateConstraint("adapter", "driver", ComparisonScheme.OPAQUE, lower="vendor-build")


def test_definite_match_and_mismatch_dominate_unknown_coordinates():
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
        prepare_environment,
    )
    from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate

    matching_wrapper = Region((
        CoordinateConstraint("package", "ibis", ComparisonScheme.PEP440, equal="12.0.0"),
    ))
    unknown_engine = Region((
        CoordinateConstraint("engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE, equal="1.2"),
    ))
    mismatched_wrapper_and_unknown_engine = Region((
        CoordinateConstraint("package", "ibis", ComparisonScheme.PEP440, equal="11.0.0"),
        CoordinateConstraint("engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE, equal="1.2"),
    ))
    observed = Environment((EnvironmentCoordinate("package", "ibis", "12.0.0"),))

    matching_union = Applicability((unknown_engine, matching_wrapper))
    mismatched_conjunction = Applicability((mismatched_wrapper_and_unknown_engine,))

    assert matching_union.match(
        prepare_environment(observed, matching_union.requirements)
    ).value == "applicable"
    assert mismatched_conjunction.match(
        prepare_environment(observed, mismatched_conjunction.requirements)
    ).value == "not_applicable"


def test_malformed_authored_bounds_reject_but_malformed_observation_is_indeterminate():
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
        prepare_environment,
    )
    from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate

    with pytest.raises(ValueError):
        Applicability((Region((
            CoordinateConstraint("engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE, lower="vendor-build"),
        )),)).prepare()

    valid_claim = Applicability((Region((
        CoordinateConstraint("engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE, lower="1.2"),
    )),))
    malformed_observation = Environment((
        EnvironmentCoordinate("engine", "duckdb", "vendor-build"),
    ))

    prepared = prepare_environment(malformed_observation, valid_claim.requirements)
    assert valid_claim.match(prepared).value == "indeterminate"


def test_empty_region_and_union_reject_empty_domains():
    from mountainash.core.capabilities.applicability import Applicability, Region

    with pytest.raises(ValueError):
        Region(())
    with pytest.raises(ValueError):
        Applicability(())


def test_impossible_coordinate_interval_rejects_declaration():
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
    )

    with pytest.raises(ValueError):
        Applicability((Region((
            CoordinateConstraint(
                "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
                lower="1.2", upper="1.2", lower_inclusive=True, upper_inclusive=False,
            ),
        )),)).prepare()


def test_region_rejects_conflicting_constraints_for_one_coordinate():
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
    )

    with pytest.raises(ValueError):
        Applicability((Region((
            CoordinateConstraint("engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE, lower="1.2"),
            CoordinateConstraint(
                "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
                upper="1.2", upper_inclusive=False,
            ),
        )),)).prepare()


def test_region_rejects_incompatible_schemes_for_one_coordinate():
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
    )

    with pytest.raises(ValueError):
        Applicability((Region((
            CoordinateConstraint("engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE, lower="1.2"),
            CoordinateConstraint("engine", "duckdb", ComparisonScheme.PEP440, lower="1.2"),
        )),)).prepare()


def test_constraint_rejects_equality_combined_with_ordered_bounds():
    from mountainash.core.capabilities.applicability import ComparisonScheme, CoordinateConstraint

    with pytest.raises(ValueError):
        CoordinateConstraint(
            "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
            equal="1.2", lower="1.2",
        )


@pytest.mark.parametrize(("left_inclusive", "right_inclusive", "expected"), [
    (True, True, "overlap"),
    (False, True, "disjoint"),
])
def test_domain_intersection_respects_adjacent_endpoint_inclusivity(
    left_inclusive, right_inclusive, expected,
):
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
        compare_applicability,
    )

    left = Applicability((Region((
        CoordinateConstraint(
            "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
            lower="1.2", upper="1.3", upper_inclusive=left_inclusive,
        ),
    )),))
    right = Applicability((Region((
        CoordinateConstraint(
            "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
            lower="1.3", lower_inclusive=right_inclusive, upper="1.4",
        ),
    )),))

    assert compare_applicability(left, right).value == expected


def test_domain_intersection_is_not_proven_for_incompatible_schemes():
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
        compare_applicability,
    )

    numeric = Applicability((Region((
        CoordinateConstraint("engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE, lower="1.2"),
    )),))
    pep440 = Applicability((Region((
        CoordinateConstraint("engine", "duckdb", ComparisonScheme.PEP440, lower="1.2"),
    )),))

    assert compare_applicability(numeric, pep440).value == "not_proven"
