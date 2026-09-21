"""Immutable environment applicability declarations and prepared range algebra."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import KW_ONLY, dataclass, field
from enum import Enum
from types import MappingProxyType

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
_ALLOWED_SCHEMES = {
    "package": frozenset({ComparisonScheme.PEP440}),
    "interpreter": frozenset({ComparisonScheme.PEP440}),
    "engine": frozenset({ComparisonScheme.NUMERIC_RELEASE, ComparisonScheme.OPAQUE}),
    "adapter": frozenset({ComparisonScheme.OPAQUE}),
    "platform": frozenset({ComparisonScheme.OPAQUE}),
}


def _canonical_coordinate(kind: str, name: str) -> tuple[str, str]:
    coordinate = EnvironmentCoordinate(kind, name, None)
    return coordinate.kind, coordinate.name


def _validate_scheme(kind: str, scheme: ComparisonScheme) -> None:
    if type(scheme) is not ComparisonScheme:
        raise TypeError("coordinate constraint requires a comparison scheme")
    if scheme not in _ALLOWED_SCHEMES[kind]:
        raise ValueError(f"{kind} coordinates do not support {scheme.value} comparison")


def _require_version_text(value: str | None, label: str) -> None:
    if value is not None and (type(value) is not str or not value):
        raise ValueError(f"{label} must be non-empty version text or omitted")


def _validate_endpoint_flags(
    lower: object | None,
    upper: object | None,
    equal: object | None,
    lower_inclusive: bool,
    upper_inclusive: bool,
) -> None:
    if type(lower_inclusive) is not bool or type(upper_inclusive) is not bool:
        raise TypeError("range endpoint inclusivity must be boolean")
    if equal is not None:
        if not lower_inclusive or not upper_inclusive:
            raise ValueError("exact values require inclusive endpoints")
        return
    if lower is None and not lower_inclusive:
        raise ValueError("an omitted lower endpoint cannot be exclusive")
    if upper is None and not upper_inclusive:
        raise ValueError("an omitted upper endpoint cannot be exclusive")


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


def _validate_parsed_value(value: object, scheme: ComparisonScheme) -> None:
    if scheme is ComparisonScheme.PEP440:
        if type(value) is not Version:
            raise TypeError("PEP440 prepared values must be packaging Version instances")
        return
    if scheme is ComparisonScheme.NUMERIC_RELEASE:
        if (
            type(value) is not tuple
            or not value
            or any(type(component) is not int or component < 0 for component in value)
            or (len(value) > 1 and value[-1] == 0)
        ):
            raise TypeError("numeric-release prepared values must be canonical immutable component tuples")
        return
    if type(value) is not str or not value:
        raise TypeError("opaque prepared values must be non-empty text")


def _validate_interval(
    lower: _ParsedValue | None,
    upper: _ParsedValue | None,
    lower_inclusive: bool,
    upper_inclusive: bool,
) -> None:
    if lower is not None and upper is not None and (
        lower > upper or (lower == upper and (not lower_inclusive or not upper_inclusive))
    ):
        raise ValueError("coordinate constraint has an empty interval")


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
        _validate_scheme(kind, self.scheme)
        _require_version_text(self.lower, "lower bound")
        _require_version_text(self.upper, "upper bound")
        _require_version_text(self.equal, "exact value")
        _validate_endpoint_flags(
            self.lower, self.upper, self.equal, self.lower_inclusive, self.upper_inclusive,
        )
        if self.equal is not None and (self.lower is not None or self.upper is not None):
            raise ValueError("exact value cannot be combined with range bounds")
        if self.equal is None and self.lower is None and self.upper is None:
            raise ValueError("coordinate constraint requires an exact value or range bound")
        if self.scheme is ComparisonScheme.OPAQUE and (self.lower is not None or self.upper is not None):
            raise ValueError("opaque coordinates support exact equality only")

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
        schemes_by_coordinate: dict[tuple[str, str], ComparisonScheme] = {}
        for constraint in self.constraints:
            prior = schemes_by_coordinate.setdefault(constraint.coordinate, constraint.scheme)
            if prior is not constraint.scheme:
                raise ValueError("region cannot combine incompatible schemes for one coordinate")


@dataclass(frozen=True)
class Applicability:
    """A union of possible environment regions; ``None`` is the unrestricted domain."""

    regions: tuple[Region, ...] | None = None

    def __post_init__(self) -> None:
        if self.regions is not None:
            if type(self.regions) is not tuple or not self.regions:
                raise ValueError("applicability regions must be a non-empty immutable tuple or None")
            if any(type(region) is not Region for region in self.regions):
                raise TypeError("applicability requires regions")

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
        """Parse authored bounds for publication or an explicit prepared lookup path."""
        return _prepare_applicability(self.regions)

    def match(self, prepared_environment: PreparedEnvironment) -> ApplicabilityResult:
        return self.prepare().match(prepared_environment)


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
    requirement: _Requirement = field(init=False)

    def __post_init__(self) -> None:
        if type(self.coordinate) is not tuple or len(self.coordinate) != 2:
            raise TypeError("prepared coordinate constraint requires a coordinate pair")
        kind, name = _canonical_coordinate(*self.coordinate)
        object.__setattr__(self, "coordinate", (kind, name))
        _validate_scheme(kind, self.scheme)
        _validate_endpoint_flags(
            self.lower, self.upper, self.equal, self.lower_inclusive, self.upper_inclusive,
        )
        if self.equal is not None and (self.lower is not None or self.upper is not None):
            raise ValueError("exact value cannot be combined with range bounds")
        if self.equal is None and self.lower is None and self.upper is None:
            raise ValueError("prepared coordinate constraint requires an exact value or range bound")
        if self.lower is not None:
            _validate_parsed_value(self.lower, self.scheme)
        if self.upper is not None:
            _validate_parsed_value(self.upper, self.scheme)
        if self.equal is not None:
            _validate_parsed_value(self.equal, self.scheme)
        if self.scheme is ComparisonScheme.OPAQUE and (self.lower is not None or self.upper is not None):
            raise ValueError("opaque coordinates support exact equality only")
        _validate_interval(self.lower, self.upper, self.lower_inclusive, self.upper_inclusive)
        object.__setattr__(self, "requirement", (kind, name, self.scheme))

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

    def __post_init__(self) -> None:
        if type(self.constraints) is not tuple or not self.constraints:
            raise ValueError("prepared region requires a non-empty immutable constraint tuple")
        if any(type(constraint) is not PreparedCoordinateConstraint for constraint in self.constraints):
            raise TypeError("prepared region requires prepared coordinate constraints")
        coordinates = [constraint.coordinate for constraint in self.constraints]
        if len(set(coordinates)) != len(coordinates):
            raise ValueError("prepared region cannot repeat a coordinate")


@dataclass(frozen=True)
class PreparedEnvironment:
    """An observed environment parsed only for the requested comparison schemes."""

    values: Mapping[_Requirement, _ParsedValue]

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping):
            raise TypeError("prepared environment requires a value mapping")
        normalized: dict[_Requirement, _ParsedValue] = {}
        for requirement, value in self.values.items():
            if type(requirement) is not tuple or len(requirement) != 3:
                raise TypeError("prepared environment requires coordinate-scheme keys")
            kind, name, scheme = requirement
            _validate_scheme(_canonical_coordinate(kind, name)[0], scheme)
            canonical_kind, canonical_name = _canonical_coordinate(kind, name)
            _validate_parsed_value(value, scheme)
            key = canonical_kind, canonical_name, scheme
            if key in normalized:
                raise ValueError("prepared environment contains duplicate canonical values")
            normalized[key] = value
        object.__setattr__(self, "values", MappingProxyType(normalized))


@dataclass(frozen=True)
class PreparedApplicability:
    """Prepared union of canonical, parsed environment regions."""

    regions: tuple[PreparedRegion, ...] | None

    def __post_init__(self) -> None:
        if self.regions is None:
            return
        if type(self.regions) is not tuple or not self.regions:
            raise ValueError("prepared applicability requires a non-empty immutable region tuple or None")
        if any(type(region) is not PreparedRegion for region in self.regions):
            raise TypeError("prepared applicability requires prepared regions")

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
    return PreparedCoordinateConstraint(
        constraint.coordinate,
        constraint.scheme,
        lower,
        upper,
        constraint.lower_inclusive,
        constraint.upper_inclusive,
        equal,
    )


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


def _merge_constraints(
    left: PreparedCoordinateConstraint,
    right: PreparedCoordinateConstraint,
) -> PreparedCoordinateConstraint:
    if left.coordinate != right.coordinate or left.scheme is not right.scheme:
        raise ValueError("cannot merge incompatible coordinate constraints")
    left_lower, left_lower_inclusive, left_upper, left_upper_inclusive = _effective_bounds(left)
    right_lower, right_lower_inclusive, right_upper, right_upper_inclusive = _effective_bounds(right)
    lower, lower_inclusive = _stricter_lower(
        (left_lower, left_lower_inclusive), (right_lower, right_lower_inclusive),
    )
    upper, upper_inclusive = _stricter_upper(
        (left_upper, left_upper_inclusive), (right_upper, right_upper_inclusive),
    )
    _validate_interval(lower, upper, lower_inclusive, upper_inclusive)
    if lower is not None and lower == upper:
        return PreparedCoordinateConstraint(
            left.coordinate, left.scheme, None, None, True, True, lower,
        )
    return PreparedCoordinateConstraint(
        left.coordinate, left.scheme, lower, upper, lower_inclusive, upper_inclusive, None,
    )


def _prepare_region(region: Region) -> PreparedRegion:
    merged: dict[tuple[str, str], PreparedCoordinateConstraint] = {}
    for raw_constraint in region.constraints:
        constraint = _prepare_constraint(raw_constraint)
        previous = merged.get(constraint.coordinate)
        merged[constraint.coordinate] = (
            constraint if previous is None else _merge_constraints(previous, constraint)
        )
    return PreparedRegion(tuple(merged.values()))


def _prepare_applicability(regions: tuple[Region, ...] | None) -> PreparedApplicability:
    if regions is None:
        return PreparedApplicability(None)
    return PreparedApplicability(tuple(_prepare_region(region) for region in regions))


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
        canonical_kind, canonical_name = _canonical_coordinate(kind, name)
        _validate_scheme(canonical_kind, scheme)
        normalized_requirements.add((canonical_kind, canonical_name, scheme))

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


def _constraints_intersect(
    left: PreparedCoordinateConstraint, right: PreparedCoordinateConstraint,
) -> bool:
    if left.scheme is not right.scheme:
        return False
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
