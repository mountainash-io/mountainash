"""Immutable environment applicability declarations and prepared range algebra."""

from __future__ import annotations

import re
from dataclasses import KW_ONLY, dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from packaging.version import InvalidVersion, Version

from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate


class ComparisonScheme(str, Enum):
    """Supported version comparison semantics for an environment coordinate."""

    PEP440 = "pep440"
    NUMERIC_RELEASE = "numeric_release"
    OPAQUE = "opaque"


class ApplicabilityResult(str, Enum):
    """Three-valued result of matching an environment against a declaration."""

    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    INDETERMINATE = "indeterminate"


class EnvironmentDomainRelation(str, Enum):
    """What can be proven about the intersection of two authored domains."""

    DISJOINT = "disjoint"
    OVERLAP = "overlap"
    NOT_PROVEN = "not_proven"


_Requirement = tuple[str, str, ComparisonScheme]
_ParsedValue = Version | tuple[int, ...] | str


def _canonical_coordinate(kind: str, name: str) -> tuple[str, str]:
    coordinate = EnvironmentCoordinate(kind, name, None)
    return coordinate.kind, coordinate.name


def _require_version_text(value: str | None, label: str) -> None:
    if value is not None and (type(value) is not str or not value):
        raise ValueError(f"{label} must be non-empty version text or omitted")


def _parse_version(text: str, scheme: ComparisonScheme) -> _ParsedValue:
    if scheme is ComparisonScheme.PEP440:
        try:
            return Version(text)
        except InvalidVersion as error:
            raise ValueError("PEP440 coordinate requires a valid version") from error
    if scheme is ComparisonScheme.NUMERIC_RELEASE:
        if re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", text) is None:
            raise ValueError("numeric-release coordinate requires numeric components")
        components = [int(part) for part in text.split(".")]
        while len(components) > 1 and components[-1] == 0:
            components.pop()
        return tuple(components)
    return text


@dataclass(frozen=True)
class CoordinateConstraint:
    """One canonical environment coordinate's exact value or closed/open range."""

    kind: str
    name: str
    scheme: ComparisonScheme
    _: KW_ONLY
    lower: str | None = None
    upper: str | None = None
    lower_inclusive: bool = True
    upper_inclusive: bool = True
    equal: str | None = None

    def __post_init__(self) -> None:
        kind, name = _canonical_coordinate(self.kind, self.name)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "name", name)
        if type(self.scheme) is not ComparisonScheme:
            raise TypeError("coordinate constraint requires a comparison scheme")
        _require_version_text(self.lower, "lower bound")
        _require_version_text(self.upper, "upper bound")
        _require_version_text(self.equal, "exact value")
        if type(self.lower_inclusive) is not bool or type(self.upper_inclusive) is not bool:
            raise TypeError("range endpoint inclusivity must be boolean")
        if self.equal is not None and (self.lower is not None or self.upper is not None):
            raise ValueError("exact value cannot be combined with range bounds")
        if self.equal is None and self.lower is None and self.upper is None:
            raise ValueError("coordinate constraint requires an exact value or range bound")
        if self.scheme is ComparisonScheme.OPAQUE:
            if self.lower is not None or self.upper is not None:
                raise ValueError("opaque coordinates support exact equality only")
            if self.equal is None:
                raise ValueError("opaque coordinates require an exact value")

    @property
    def coordinate(self) -> tuple[str, str]:
        return self.kind, self.name


@dataclass(frozen=True)
class Region:
    """A conjunction of constraints over one possible environment region."""

    constraints: tuple[CoordinateConstraint, ...]

    def __post_init__(self) -> None:
        if type(self.constraints) is not tuple or not self.constraints:
            raise ValueError("region requires at least one immutable coordinate constraint")
        if any(type(constraint) is not CoordinateConstraint for constraint in self.constraints):
            raise TypeError("region requires coordinate constraints")
        coordinates = [constraint.coordinate for constraint in self.constraints]
        if len(set(coordinates)) != len(coordinates):
            raise ValueError("region cannot contain conflicting constraints for one coordinate")


@dataclass(frozen=True)
class Applicability:
    """A union of possible environment regions; ``None`` is the unrestricted domain."""

    regions: tuple[Region, ...] | None = None
    _prepared: PreparedApplicability = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.regions is not None:
            if type(self.regions) is not tuple or not self.regions:
                raise ValueError("applicability regions must be a non-empty immutable tuple or None")
            if any(type(region) is not Region for region in self.regions):
                raise TypeError("applicability requires regions")
        object.__setattr__(self, "_prepared", _prepare_applicability(self.regions))

    @property
    def requirements(self) -> frozenset[_Requirement]:
        if self.regions is None:
            return frozenset()
        return frozenset(
            (constraint.kind, constraint.name, constraint.scheme)
            for region in self.regions
            for constraint in region.constraints
        )

    def prepare(self) -> PreparedApplicability:
        """Return the publication-time parsed declaration."""
        return self._prepared

    def match(self, prepared_environment: PreparedEnvironment) -> ApplicabilityResult:
        return self._prepared.match(prepared_environment)


@dataclass(frozen=True)
class PreparedCoordinateConstraint:
    """A canonical coordinate constraint with all authored values parsed once."""

    coordinate: tuple[str, str]
    scheme: ComparisonScheme
    lower: _ParsedValue | None
    upper: _ParsedValue | None
    lower_inclusive: bool
    upper_inclusive: bool
    equal: _ParsedValue | None

    @property
    def requirement(self) -> _Requirement:
        return (*self.coordinate, self.scheme)

    def matches(self, value: _ParsedValue) -> bool:
        if self.equal is not None:
            return value == self.equal
        if self.lower is not None and (
            value < self.lower or (value == self.lower and not self.lower_inclusive)
        ):
            return False
        if self.upper is not None and (
            value > self.upper or (value == self.upper and not self.upper_inclusive)
        ):
            return False
        return True


@dataclass(frozen=True)
class PreparedRegion:
    """Prepared conjunction of constraints."""

    constraints: tuple[PreparedCoordinateConstraint, ...]


@dataclass(frozen=True)
class PreparedEnvironment:
    """An observed environment parsed only for the requested comparison schemes."""

    values: Mapping[_Requirement, _ParsedValue]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


@dataclass(frozen=True)
class PreparedApplicability:
    """Prepared union of canonical, parsed environment regions."""

    regions: tuple[PreparedRegion, ...] | None

    def match(self, environment: PreparedEnvironment) -> ApplicabilityResult:
        if type(environment) is not PreparedEnvironment:
            raise TypeError("applicability matching requires a prepared environment")
        if self.regions is None:
            return ApplicabilityResult.APPLICABLE
        union_unknown = False
        for region in self.regions:
            region_unknown = False
            for constraint in region.constraints:
                value = environment.values.get(constraint.requirement)
                if value is None:
                    region_unknown = True
                    continue
                if not constraint.matches(value):
                    break
            else:
                if not region_unknown:
                    return ApplicabilityResult.APPLICABLE
                union_unknown = True
        return (
            ApplicabilityResult.INDETERMINATE
            if union_unknown
            else ApplicabilityResult.NOT_APPLICABLE
        )


def _prepare_constraint(constraint: CoordinateConstraint) -> PreparedCoordinateConstraint:
    lower = _parse_version(constraint.lower, constraint.scheme) if constraint.lower is not None else None
    upper = _parse_version(constraint.upper, constraint.scheme) if constraint.upper is not None else None
    equal = _parse_version(constraint.equal, constraint.scheme) if constraint.equal is not None else None
    if lower is not None and upper is not None:
        if lower > upper or (lower == upper and (not constraint.lower_inclusive or not constraint.upper_inclusive)):
            raise ValueError("coordinate constraint has an empty interval")
    return PreparedCoordinateConstraint(
        constraint.coordinate,
        constraint.scheme,
        lower,
        upper,
        constraint.lower_inclusive,
        constraint.upper_inclusive,
        equal,
    )


def _prepare_applicability(regions: tuple[Region, ...] | None) -> PreparedApplicability:
    if regions is None:
        return PreparedApplicability(None)
    return PreparedApplicability(tuple(
        PreparedRegion(tuple(_prepare_constraint(constraint) for constraint in region.constraints))
        for region in regions
    ))


def prepare_environment(environment: Environment, requirements: frozenset[_Requirement]) -> PreparedEnvironment:
    """Parse observed versions for the declaration's required coordinates.

    Malformed or absent observations are deliberately omitted so matching reports
    uncertainty rather than rejecting an otherwise valid captured environment.
    """
    if type(environment) is not Environment:
        raise TypeError("environment preparation requires an Environment")
    if type(requirements) is not frozenset:
        raise TypeError("environment requirements must be a frozenset")

    normalized_requirements: set[_Requirement] = set()
    for requirement in requirements:
        if type(requirement) is not tuple or len(requirement) != 3:
            raise TypeError("environment requirement must be a coordinate and comparison scheme")
        kind, name, scheme = requirement
        if type(scheme) is not ComparisonScheme:
            raise TypeError("environment requirement requires a comparison scheme")
        normalized_requirements.add((*_canonical_coordinate(kind, name), scheme))

    observed = {(coordinate.kind, coordinate.name): coordinate.version for coordinate in environment.coordinates}
    values: dict[_Requirement, _ParsedValue] = {}
    for kind, name, scheme in normalized_requirements:
        raw_version = observed.get((kind, name))
        if raw_version is None:
            continue
        try:
            values[(kind, name, scheme)] = _parse_version(raw_version, scheme)
        except ValueError:
            continue
    return PreparedEnvironment(values)


def _effective_bounds(
    constraint: PreparedCoordinateConstraint,
) -> tuple[_ParsedValue | None, bool, _ParsedValue | None, bool]:
    if constraint.equal is not None:
        return constraint.equal, True, constraint.equal, True
    return constraint.lower, constraint.lower_inclusive, constraint.upper, constraint.upper_inclusive


def _stricter_lower(
    first: tuple[_ParsedValue | None, bool], second: tuple[_ParsedValue | None, bool],
) -> tuple[_ParsedValue | None, bool]:
    first_value, first_inclusive = first
    second_value, second_inclusive = second
    if first_value is None:
        return second
    if second_value is None:
        return first
    if first_value > second_value:
        return first
    if second_value > first_value:
        return second
    return first_value, first_inclusive and second_inclusive


def _stricter_upper(
    first: tuple[_ParsedValue | None, bool], second: tuple[_ParsedValue | None, bool],
) -> tuple[_ParsedValue | None, bool]:
    first_value, first_inclusive = first
    second_value, second_inclusive = second
    if first_value is None:
        return second
    if second_value is None:
        return first
    if first_value < second_value:
        return first
    if second_value < first_value:
        return second
    return first_value, first_inclusive and second_inclusive


def _constraints_intersect(
    left: PreparedCoordinateConstraint, right: PreparedCoordinateConstraint,
) -> bool:
    left_lower, left_lower_inclusive, left_upper, left_upper_inclusive = _effective_bounds(left)
    right_lower, right_lower_inclusive, right_upper, right_upper_inclusive = _effective_bounds(right)
    lower, lower_inclusive = _stricter_lower(
        (left_lower, left_lower_inclusive), (right_lower, right_lower_inclusive),
    )
    upper, upper_inclusive = _stricter_upper(
        (left_upper, left_upper_inclusive), (right_upper, right_upper_inclusive),
    )
    return lower is None or upper is None or lower < upper or (
        lower == upper and lower_inclusive and upper_inclusive
    )


def _compare_regions(left: PreparedRegion, right: PreparedRegion) -> EnvironmentDomainRelation:
    right_by_coordinate = {constraint.coordinate: constraint for constraint in right.constraints}
    not_proven = False
    for constraint in left.constraints:
        other = right_by_coordinate.get(constraint.coordinate)
        if other is None:
            continue
        if constraint.scheme is not other.scheme:
            not_proven = True
            continue
        if not _constraints_intersect(constraint, other):
            return EnvironmentDomainRelation.DISJOINT
    return EnvironmentDomainRelation.NOT_PROVEN if not_proven else EnvironmentDomainRelation.OVERLAP


def compare_applicability(left: Applicability, right: Applicability) -> EnvironmentDomainRelation:
    """Compare authored environment domains without interpreting a runtime observation."""
    if type(left) is not Applicability or type(right) is not Applicability:
        raise TypeError("applicability comparison requires applicability declarations")
    left_regions = left.prepare().regions
    right_regions = right.prepare().regions
    if left_regions is None or right_regions is None:
        return EnvironmentDomainRelation.OVERLAP

    not_proven = False
    for left_region in left_regions:
        for right_region in right_regions:
            relation = _compare_regions(left_region, right_region)
            if relation is EnvironmentDomainRelation.OVERLAP:
                return relation
            if relation is EnvironmentDomainRelation.NOT_PROVEN:
                not_proven = True
    return EnvironmentDomainRelation.NOT_PROVEN if not_proven else EnvironmentDomainRelation.DISJOINT
