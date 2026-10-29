"""Immutable environment applicability declarations and prepared range algebra."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import KW_ONLY, dataclass, field
from enum import Enum
from types import MappingProxyType

from packaging.ranges import VersionRange
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate


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


_Requirement = tuple[str, str, bool]


def _canonical_coordinate(kind: str, name: str) -> tuple[str, str]:
    coordinate = EnvironmentCoordinate(kind, name, None)
    return coordinate.kind, coordinate.name


@dataclass(frozen=True)
class CoordinateConstraint:
    """One canonical environment coordinate's version set or opaque label."""

    kind: str
    name: str
    _: KW_ONLY
    specifier: str | None = None
    opaque_equal: str | None = None

    def __post_init__(self) -> None:
        kind, name = _canonical_coordinate(self.kind, self.name)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "name", name)
        if (self.specifier is None) == (self.opaque_equal is None):
            raise ValueError("coordinate requires exactly one constraint form")
        if self.specifier is not None:
            if kind not in {"package", "interpreter", "engine"}:
                raise ValueError("coordinate kind does not support version specifiers")
            if type(self.specifier) is not str:
                raise TypeError("specifier requires text")
            if not SpecifierSet(self.specifier, prereleases=None):
                raise ValueError("version constraint requires at least one specifier clause")
        else:
            if kind not in {"engine", "adapter", "platform"}:
                raise ValueError("coordinate kind does not support opaque equality")
            if type(self.opaque_equal) is not str or not self.opaque_equal:
                raise ValueError("opaque equality requires nonempty text")

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
        return self.prepare().requirements

    def prepare(self) -> PreparedApplicability:
        """Prepare library specifiers and ranges once for publication or explicit use."""
        return _prepare_applicability(self.regions)

    def match(self, prepared_environment: PreparedEnvironment) -> ApplicabilityResult:
        return self.prepare().match(prepared_environment)


unbounded = Applicability()


@dataclass(frozen=True)
class PreparedObservation:
    """An observed raw label and its optional parsed PEP 440 version."""

    raw: str
    version: Version | None

    def __post_init__(self) -> None:
        if type(self.raw) is not str or not self.raw:
            raise TypeError("prepared observation requires non-empty raw text")
        if self.version is not None and type(self.version) is not Version:
            raise TypeError("prepared observation version must be a Version or None")


@dataclass(frozen=True)
class PreparedCoordinateConstraint:
    """Prepared coordinate semantics; library objects are built before matching."""

    coordinate: tuple[str, str]
    literal_specifiers: tuple[Specifier, ...]
    version_specifiers: SpecifierSet | None
    version_range: VersionRange | None
    opaque_equal: str | None
    requires_version: bool

    def __post_init__(self) -> None:
        if type(self.coordinate) is not tuple or len(self.coordinate) != 2:
            raise TypeError("prepared coordinate constraint requires a coordinate pair")
        kind, name = _canonical_coordinate(*self.coordinate)
        object.__setattr__(self, "coordinate", (kind, name))
        if type(self.literal_specifiers) is not tuple or any(
            type(specifier) is not Specifier or specifier.operator != "===" for specifier in self.literal_specifiers
        ):
            raise TypeError("prepared literal specifiers must be an immutable tuple of === clauses")
        if self.version_specifiers is not None and type(self.version_specifiers) is not SpecifierSet:
            raise TypeError("prepared version specifiers must be a SpecifierSet or None")
        if self.version_range is not None and type(self.version_range) is not VersionRange:
            raise TypeError("prepared version range must be a VersionRange or None")
        if self.opaque_equal is not None:
            if type(self.opaque_equal) is not str or not self.opaque_equal:
                raise ValueError("prepared opaque equality requires nonempty text")
            if self.literal_specifiers or self.version_specifiers is not None or self.version_range is not None:
                raise ValueError("prepared coordinate cannot mix opaque and version constraints")
        elif self.version_range is None:
            raise ValueError("prepared version constraint requires a range")
        if type(self.requires_version) is not bool:
            raise TypeError("requires_version must be boolean")

    @property
    def requirement(self) -> _Requirement:
        return (*self.coordinate, self.requires_version)

    def matches(self, value: PreparedObservation | None) -> ApplicabilityResult:
        if value is None:
            return ApplicabilityResult.INDETERMINATE
        if self.opaque_equal is not None:
            return (
                ApplicabilityResult.APPLICABLE if value.raw == self.opaque_equal else ApplicabilityResult.NOT_APPLICABLE
            )
        if any(not clause.contains(value.raw, prereleases=None) for clause in self.literal_specifiers):
            return ApplicabilityResult.NOT_APPLICABLE
        if self.requires_version:
            if value.version is None:
                return ApplicabilityResult.INDETERMINATE
            assert self.version_specifiers is not None
            if not self.version_specifiers.contains(value.version, prereleases=None):
                return ApplicabilityResult.NOT_APPLICABLE
        return ApplicabilityResult.APPLICABLE


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
    """Immutable observations prepared only for coordinates required by a declaration."""

    values: Mapping[tuple[str, str], PreparedObservation]

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping):
            raise TypeError("prepared environment requires a value mapping")
        normalized: dict[tuple[str, str], PreparedObservation] = {}
        for coordinate, observation in self.values.items():
            if type(coordinate) is not tuple or len(coordinate) != 2:
                raise TypeError("prepared environment requires coordinate-pair keys")
            canonical = _canonical_coordinate(*coordinate)
            if type(observation) is not PreparedObservation:
                raise TypeError("prepared environment values must be PreparedObservation instances")
            if canonical in normalized:
                raise ValueError("prepared environment contains duplicate canonical values")
            normalized[canonical] = observation
        object.__setattr__(self, "values", MappingProxyType(normalized))


@dataclass(frozen=True)
class PreparedApplicability:
    """Prepared union of canonical, parsed environment regions."""

    regions: tuple[PreparedRegion, ...] | None
    requirements: frozenset[_Requirement] = field(init=False)

    def __post_init__(self) -> None:
        if self.regions is not None:
            if type(self.regions) is not tuple or not self.regions:
                raise ValueError("prepared applicability requires a non-empty immutable region tuple or None")
            if any(type(region) is not PreparedRegion for region in self.regions):
                raise TypeError("prepared applicability requires prepared regions")
        requirements = frozenset(
            constraint.requirement for region in (self.regions or ()) for constraint in region.constraints
        )
        object.__setattr__(self, "requirements", requirements)

    def match(self, environment: PreparedEnvironment) -> ApplicabilityResult:
        if type(environment) is not PreparedEnvironment:
            raise TypeError("applicability matching requires a prepared environment")
        if self.regions is None:
            return ApplicabilityResult.APPLICABLE
        union_unknown = False
        for region in self.regions:
            region_unknown = False
            for constraint in region.constraints:
                result = constraint.matches(environment.values.get(constraint.coordinate))
                if result is ApplicabilityResult.NOT_APPLICABLE:
                    break
                if result is ApplicabilityResult.INDETERMINATE:
                    region_unknown = True
            else:
                if not region_unknown:
                    return ApplicabilityResult.APPLICABLE
                union_unknown = True
        return ApplicabilityResult.INDETERMINATE if union_unknown else ApplicabilityResult.NOT_APPLICABLE


def _prepare_region(region: Region) -> PreparedRegion | None:
    by_coordinate: dict[tuple[str, str], list[CoordinateConstraint]] = {}
    for constraint in region.constraints:
        by_coordinate.setdefault(constraint.coordinate, []).append(constraint)

    prepared: list[PreparedCoordinateConstraint] = []
    empty = False
    for coordinate, constraints in by_coordinate.items():
        # Construct every library object before deciding whether this region is dead.
        specifier_sets = [
            SpecifierSet(constraint.specifier, prereleases=None)
            for constraint in constraints
            if constraint.specifier is not None
        ]
        opaque_labels = [constraint.opaque_equal for constraint in constraints if constraint.opaque_equal is not None]
        if specifier_sets and opaque_labels:
            raise ValueError("region cannot mix version and opaque constraints for one coordinate")
        if opaque_labels:
            if len(set(opaque_labels)) != 1:
                empty = True
                continue
            prepared.append(PreparedCoordinateConstraint(coordinate, (), None, None, opaque_labels[0], False))
            continue

        combined = specifier_sets[0]
        for specifier_set in specifier_sets[1:]:
            combined = combined & specifier_set
        version_range = combined.to_range()
        if version_range.is_empty:
            empty = True
        literal_specifiers = tuple(specifier for specifier in combined if specifier.operator == "===")
        version_clauses = tuple(specifier for specifier in combined if specifier.operator != "===")
        version_specifiers = (
            SpecifierSet(",".join(str(specifier) for specifier in version_clauses), prereleases=None)
            if version_clauses
            else None
        )
        prepared.append(
            PreparedCoordinateConstraint(
                coordinate,
                literal_specifiers,
                version_specifiers,
                version_range,
                None,
                bool(version_clauses),
            )
        )
    if empty:
        return None
    return PreparedRegion(tuple(prepared))


def _prepare_applicability(regions: tuple[Region, ...] | None) -> PreparedApplicability:
    if regions is None:
        return PreparedApplicability(None)
    prepared = tuple(result for region in regions if (result := _prepare_region(region)) is not None)
    if not prepared:
        raise ValueError("applicability declaration has an empty domain")
    return PreparedApplicability(prepared)


def prepare_environment(environment: Environment, requirements: frozenset[_Requirement]) -> PreparedEnvironment:
    """Parse each required observed version at most once while retaining raw text."""
    if type(environment) is not Environment:
        raise TypeError("environment preparation requires an Environment")
    if type(requirements) is not frozenset:
        raise TypeError("environment requirements must be a frozenset")

    needs_version: dict[tuple[str, str], bool] = {}
    for requirement in requirements:
        if type(requirement) is not tuple or len(requirement) != 3:
            raise TypeError("environment requirement must be a coordinate and version-parse flag")
        kind, name, requires_version = requirement
        if type(requires_version) is not bool:
            raise TypeError("environment requirement version-parse flag must be boolean")
        coordinate = _canonical_coordinate(kind, name)
        needs_version[coordinate] = needs_version.get(coordinate, False) or requires_version

    observed = {(coordinate.kind, coordinate.name): coordinate.version for coordinate in environment.coordinates}
    values: dict[tuple[str, str], PreparedObservation] = {}
    for coordinate, requires_version in needs_version.items():
        raw = observed.get(coordinate)
        if raw is None:
            continue
        version = None
        if requires_version:
            try:
                version = Version(raw)
            except InvalidVersion:
                pass
        values[coordinate] = PreparedObservation(raw, version)
    return PreparedEnvironment(values)


def _constraints_intersect(
    left: PreparedCoordinateConstraint,
    right: PreparedCoordinateConstraint,
) -> bool | None:
    if left.opaque_equal is not None and right.opaque_equal is not None:
        return left.opaque_equal == right.opaque_equal
    if left.opaque_equal is not None or right.opaque_equal is not None:
        return None
    assert left.version_range is not None and right.version_range is not None
    return not left.version_range.is_disjoint(right.version_range)


def _compare_regions(left: PreparedRegion, right: PreparedRegion) -> EnvironmentDomainRelation:
    right_by_coordinate = {constraint.coordinate: constraint for constraint in right.constraints}
    not_proven = False
    for constraint in left.constraints:
        other = right_by_coordinate.get(constraint.coordinate)
        if other is None:
            continue
        intersection = _constraints_intersect(constraint, other)
        if intersection is False:
            return EnvironmentDomainRelation.DISJOINT
        if intersection is None:
            not_proven = True
    return EnvironmentDomainRelation.NOT_PROVEN if not_proven else EnvironmentDomainRelation.OVERLAP


def _compare_prepared_applicability(
    left: PreparedApplicability,
    right: PreparedApplicability,
) -> EnvironmentDomainRelation:
    if type(left) is not PreparedApplicability or type(right) is not PreparedApplicability:
        raise TypeError("prepared applicability comparison requires prepared domains")
    if left.regions is None or right.regions is None:
        return EnvironmentDomainRelation.OVERLAP
    not_proven = False
    for left_region in left.regions:
        for right_region in right.regions:
            relation = _compare_regions(left_region, right_region)
            if relation is EnvironmentDomainRelation.OVERLAP:
                return relation
            if relation is EnvironmentDomainRelation.NOT_PROVEN:
                not_proven = True
    return EnvironmentDomainRelation.NOT_PROVEN if not_proven else EnvironmentDomainRelation.DISJOINT


def compare_applicability(left: Applicability, right: Applicability) -> EnvironmentDomainRelation:
    """Compare authored environment domains without interpreting runtime observations."""
    if type(left) is not Applicability or type(right) is not Applicability:
        raise TypeError("applicability comparison requires applicability declarations")
    return _compare_prepared_applicability(left.prepare(), right.prepare())
