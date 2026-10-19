"""Backend-agnostic immutable field declarations and ordered table schemas.

Names belong to uses of FieldSpec, not to reusable definitions. Frictionless
interchange and backend execution remain separate consumer boundaries.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import MISSING, dataclass, field, fields as dataclass_fields, replace
from datetime import date, time
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, List, Optional, Union

from mountainash.core.constants import DECIMAL_ROUNDING_MODES
from mountainash.core.dtypes import (
    ArrayDtype, DecimalDtype, DurationDtype, ListDtype, MountainashDtype,
    NativeDtype, PortableDtype, SchemaTypeStatus, StructDtype, TimeDtype,
    TimestampDtype, parse_cast_target,
)
from mountainash.typespec.universal_types import UniversalType, from_canonical, parse_universal
from mountainash.typespec.errors import (
    IncompatibleFieldPropertiesError,
    InvalidDescriptorRelationship,
    InvalidKeyShapeError,
    InvalidDtypeDeclaration,
)
from mountainash.typespec.frictionless_invariants import (
    InvariantLocation,
    reject_typed_profile_at,
)


@dataclass(frozen=True)
class _OwnedPayload:
    """Owned opaque values are exposed only as defensive copies."""

    value: Any


def _copy_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _copy_payload(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_copy_payload(item) for item in value)
    if isinstance(value, list):
        return [_copy_payload(item) for item in value]
    return deepcopy(value)


class _ImmutableDeclaration:
    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        return _copy_payload(value.value) if isinstance(value, _OwnedPayload) else value

    def __deepcopy__(self, memo: dict) -> Any:
        return self


@dataclass(frozen=True)
class LabeledValue(_ImmutableDeclaration):
    """A value with an optional human-readable label.

    Shared typed shape for Frictionless v2's missingValues and categories
    labeled-object forms. ``value``'s Python type follows the property that
    carries it: always str for missing values (Frictionless requires
    string-typed sentinels so comparison happens before casting); the
    field's declared type for categories (e.g. int for an integer field).
    """

    value: Any
    label: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _own_value(self.value))


MissingValue = Union[str, LabeledValue]


def _validate_key_shape(value: Any, label: str) -> None:
    """Module-private helper shared by TypeSpec, ForeignKey, and
    ForeignKeyReference — every key-shaped field validates through this one
    function. Raises InvalidKeyShapeError unless ``value`` is a list[str]."""
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise InvalidKeyShapeError(label, value, "list[str]")


@dataclass(frozen=True)
class FieldConstraints(_ImmutableDeclaration):
    """Constraints for a schema field (Frictionless Table Schema compliant)."""

    required: bool = False
    unique: bool = False
    minimum: Optional[Any] = None
    maximum: Optional[Any] = None
    exclusive_minimum: Optional[Any] = None  # standard v2 property
    exclusive_maximum: Optional[Any] = None  # standard v2 property
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum: Optional[List[Any]] = None
    enum_weights: Optional[Dict[str, float]] = None  # x-mountainash extension
    json_schema: Optional[Dict[str, Any]] = None  # standard v2 property
    eq: Any = None
    ne: Any = None
    notin: Any = None
    str_contains: str | None = None
    str_startswith: str | None = None
    str_endswith: str | None = None

    def __post_init__(self) -> None:
        for item in dataclass_fields(self):
            object.__setattr__(self, item.name, _own_value(getattr(self, item.name)))

    def __deepcopy__(self, memo: dict) -> FieldConstraints:
        return self


_CONSTRAINT_NAMES = frozenset(item.name for item in dataclass_fields(FieldConstraints))
_MIGRATION_GUIDE = "See docs/guides/composable-field-migration.md."
_RETIRED_FIELD_PROPERTIES = {
    "name": "names come from the mapping key where the definition is attached, e.g. TypeSpec(fields={'id': FieldSpec(...)})",
    "source_name": "use rename_from on the definition; the effective source is rename_from or the mapping key",
    "object_fields": "use fields={'member': FieldSpec(...)}",
    "item_object_fields": "use element=FieldSpec(fields={...})",
}


def _own_value(value: Any) -> Any:
    """Freeze plain containers; defensively own supported opaque payloads."""
    if isinstance(value, _ImmutableDeclaration):
        return value
    if isinstance(value, Mapping):
        owned = {key: _own_value(item) for key, item in value.items()}
        if any(isinstance(item, _OwnedPayload) for item in owned.values()):
            return _OwnedPayload(_copy_payload(value))
        return MappingProxyType(owned)
    if isinstance(value, (tuple, list)):
        owned = tuple(_own_value(item) for item in value)
        if any(isinstance(item, _OwnedPayload) for item in owned):
            return _OwnedPayload(_copy_payload(value))
        return owned
    if isinstance(value, (set, frozenset)):
        return frozenset(_own_value(item) for item in value)
    if value is None or isinstance(value, (str, bytes, int, float, Enum, date, time, Decimal)):
        return value
    if isinstance(value, (
        DecimalDtype, TimestampDtype, TimeDtype, DurationDtype,
        ListDtype, ArrayDtype, StructDtype,
    )):
        # Share portable records unless a native override is reachable.
        if all(not isinstance(_own_value(getattr(value, item.name)), _OwnedPayload)
               for item in dataclass_fields(value)):
            return value
    return _OwnedPayload(_copy_payload(value))


@dataclass
class ForeignKeyReference:
    """Reference target for a foreign key (Frictionless Table Schema compliant).

    Attributes:
        resource: Name of the referenced table. ``None`` for self-referencing.
        fields: Field name(s) in the referenced table.
    """
    resource: str | None  # None = self-reference
    fields: list[str]

    def __post_init__(self) -> None:
        _validate_key_shape(self.fields, "foreign_key.reference.fields")
        if self.resource is not None and (
            not isinstance(self.resource, str) or not self.resource
        ):
            raise InvalidDescriptorRelationship(
                "typed foreign-key resource is invalid",
                descriptor_kind="schema",
                descriptor_path="foreign_key.reference.resource",
                rejected_value=self.resource,
                required_form="None or non-empty resource name string",
            )


@dataclass
class ForeignKey:
    """Foreign key constraint (Frictionless Table Schema compliant).

    Attributes:
        fields: Field name(s) in this table.
        reference: The target table and fields being referenced.
    """
    fields: List[str]
    reference: ForeignKeyReference

    def __post_init__(self) -> None:
        _validate_key_shape(self.fields, "foreign_key.fields")


@dataclass(frozen=True, init=False)
class FieldSpec(_ImmutableDeclaration):
    """An immutable, unnamed declaration reusable in named or element contexts."""

    type: UniversalType = UniversalType.ANY
    format: str = "default"
    title: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[FieldConstraints] = None
    missing_values: Optional[tuple[MissingValue, ...]] = None
    true_values: Optional[tuple[str, ...]] = None
    false_values: Optional[tuple[str, ...]] = None
    categories: Optional[tuple[Any, ...]] = None
    categories_ordered: Optional[bool] = None
    example: Any = None
    rdf_type: Optional[str] = None
    decimal_char: Optional[str] = None
    group_char: Optional[str] = None
    bare_number: Optional[bool] = None
    item_type: Optional[str] = None
    fields: Mapping[str, FieldSpec] | None = None
    element: FieldSpec | None = None
    dimensions: tuple[int, ...] | SchemaTypeStatus | None = None
    delimiter: Optional[str] = None
    backend_type: Any = None
    dtype: PortableDtype | SchemaTypeStatus | None = None
    null_fill: Any = None
    rename_from: Optional[str] = None
    custom_cast: Optional[str] = None
    rounding: str | None = None
    severity: str | None = None

    def __init__(self, *args: Any, **properties: Any) -> None:
        if args:
            raise TypeError(
                "FieldSpec takes keyword properties only and has no name; attach it under a name instead, "
                f"e.g. TypeSpec(fields={{'id': FieldSpec(type=...)}}). {_MIGRATION_GUIDE}"
            )
        retired = sorted(_RETIRED_FIELD_PROPERTIES.keys() & properties.keys())
        if retired:
            raise TypeError(
                f"FieldSpec no longer accepts {', '.join(retired)}: "
                + "; ".join(_RETIRED_FIELD_PROPERTIES[name] for name in retired)
                + f". {_MIGRATION_GUIDE}"
            )
        constraint_changes = {
            name: properties.pop(name) for name in _CONSTRAINT_NAMES if name in properties
        }
        if constraint_changes:
            base = properties.get("constraints") or FieldConstraints()
            properties["constraints"] = replace(base, **constraint_changes)
        for item in dataclass_fields(self):
            value = properties.pop(item.name, item.default)
            if value is MISSING:
                value = item.default_factory()
            object.__setattr__(self, item.name, _own_value(value))
        if properties:
            raise TypeError(f"unexpected FieldSpec properties: {', '.join(sorted(properties))}")
        self.__post_init__()

    def __getattr__(self, name: str) -> Any:
        if name in _RETIRED_FIELD_PROPERTIES:
            raise AttributeError(
                f"FieldSpec has no {name!r}: {_RETIRED_FIELD_PROPERTIES[name]}. {_MIGRATION_GUIDE}"
            )
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    def __post_init__(self) -> None:
        composed = self.fields is not None or self.element is not None
        if self.fields is not None and self.element is not None:
            raise InvalidDtypeDeclaration(None, "fields and element describe alternative shapes")
        if composed and self.dtype is not None:
            raise InvalidDtypeDeclaration(None, "compose with fields or element instead of a second dtype tree")
        if self.dimensions is not None and self.element is None:
            raise InvalidDtypeDeclaration(None, "dimensions requires an element declaration")
        if self.fields is not None:
            if not isinstance(self.fields, Mapping) or any(
                not isinstance(name, str) or not isinstance(child, FieldSpec)
                for name, child in self.fields.items()
            ):
                raise InvalidDtypeDeclaration(None, "fields requires a name-to-FieldSpec mapping")
            from mountainash.typespec.converters import resolve_field_canonical
            object.__setattr__(self, "dtype", _own_value(StructDtype(tuple(
                (name, resolve_field_canonical(child) or SchemaTypeStatus.UNKNOWN)
                for name, child in self.fields.items()
            ))))
        elif self.element is not None:
            if not isinstance(self.element, FieldSpec):
                raise InvalidDtypeDeclaration(None, "element requires a FieldSpec")
            from mountainash.typespec.converters import resolve_field_canonical
            child_dtype = resolve_field_canonical(self.element) or SchemaTypeStatus.UNKNOWN
            dtype = (
                ListDtype(child_dtype) if self.dimensions is None
                else ArrayDtype(child_dtype, self.dimensions)
            )
            object.__setattr__(self, "dtype", _own_value(dtype))

        dtype = self.dtype
        if dtype is not None and dtype is not SchemaTypeStatus.UNKNOWN:
            if not isinstance(dtype, (
                MountainashDtype, DecimalDtype, TimestampDtype, TimeDtype,
                DurationDtype, ListDtype, ArrayDtype, StructDtype,
            )):
                raise InvalidDtypeDeclaration(None, "dtype requires a portable dtype or UNKNOWN", dtype)
            broad, fmt = from_canonical(dtype)
            if isinstance(dtype, DurationDtype) or dtype in (
                MountainashDtype.JSON, MountainashDtype.DURATION,
            ):
                broad = UniversalType.ANY
            if self.type is UniversalType.ANY:
                object.__setattr__(self, "type", broad)
            elif self.type is UniversalType.GEOPOINT:
                from mountainash.typespec.converters import _resolve_broad_field_canonical
                if _resolve_broad_field_canonical(self) != dtype:
                    raise IncompatibleFieldPropertiesError(None, "dtype", self.type, (broad,))
            elif not (
                self.type is broad
                or (dtype is MountainashDtype.JSON and self.type is UniversalType.GEOJSON)
                or (
                    self.type is UniversalType.LIST
                    and (dtype is MountainashDtype.LIST or isinstance(dtype, ListDtype))
                )
            ):
                raise IncompatibleFieldPropertiesError(None, "dtype", self.type, (broad,))
            if fmt is not None:
                if self.format not in ("default", fmt):
                    raise InvalidDtypeDeclaration(None, "dtype contradicts field format", self.format)
                object.__setattr__(self, "format", fmt)
            if dtype is MountainashDtype.STRING and self.format == "binary":
                raise InvalidDtypeDeclaration(None, "string dtype contradicts binary format")
        if self.backend_type is not None and not isinstance(self.backend_type, str):
            native = parse_cast_target(self.backend_type)
            if not isinstance(native, NativeDtype):
                raise InvalidDtypeDeclaration(None, "backend_type requires a native dtype", self.backend_type)
            object.__setattr__(self, "backend_type", _own_value(native))
        for name in ("item_type", "delimiter"):
            if getattr(self, name) is not None and self.type is not UniversalType.LIST:
                raise IncompatibleFieldPropertiesError(None, name, self.type, (UniversalType.LIST,))
        if isinstance(dtype, DecimalDtype) and self.categories is not None:
            raise InvalidDtypeDeclaration(None, "dtype and categories cannot be combined")
        if self.rounding is not None:
            if not isinstance(dtype, DecimalDtype):
                raise InvalidDtypeDeclaration(None, "rounding requires a DecimalDtype")
            if not isinstance(self.rounding, str) or self.rounding not in DECIMAL_ROUNDING_MODES:
                raise InvalidDtypeDeclaration(None, "invalid decimal rounding mode", self.rounding)
        from mountainash.typespec._field_values import normalize_field_values
        normalize_field_values(self)

    def _constructor_properties(self) -> dict[str, Any]:
        properties = {item.name: getattr(self, item.name) for item in dataclass_fields(self)}
        if self.fields is not None or self.element is not None:
            properties.pop("dtype")
        return properties

    def variant(self, **properties: Any) -> FieldSpec:
        values = self._constructor_properties()
        values.update(properties)
        return type(self)(**values)

    def to_checks(self, local_name: str) -> tuple[Any, ...]:
        from mountainash.datacontracts.compiler import compile_field_checks
        return compile_field_checks(local_name, self)

    def __deepcopy__(self, memo: dict) -> FieldSpec:
        return self


@dataclass
class TypeSpec:
    """Schema definition for a dataset (Frictionless Table Schema representation).

    Replaces the old TableSchema with additional features.

    ``fields_match`` sets how conform treats columns that differ from the
    declared fields. For an *undeclared* (extra) column:

    - ``exact``, ``equal``, ``superset``: rejected (conform raises).
    - ``subset``, ``partial``: silently dropped.
    - ``open``: retained.

    ``exact`` also rejects reordered fields; ``equal`` accepts them. ``equal``
    and ``subset`` reject a missing declared field; ``superset``, ``partial``
    and ``open`` tolerate one. ``exact`` is the default and is never weakened
    implicitly. Combine ``open`` with
    ``contract={"missing_columns": "freeze"}`` to keep extras but still fail on
    a missing declared field.

    A validation rule that reads a *support* column (one outside the contract,
    e.g. a freshness rule reading ``extract_date``) needs that column to survive
    conform: either declare it as a field, or use ``open``. Under ``subset`` or
    ``partial`` the column is dropped and the rule reports an error.
    """

    fields: Dict[str, FieldSpec] = field(default_factory=dict)
    title: Optional[str] = None
    description: Optional[str] = None
    primary_key: Optional[List[str]] = None
    foreign_keys: Optional[List[ForeignKey]] = None
    missing_values: Optional[List[MissingValue]] = field(default_factory=lambda: [""])
    fields_match: str = "exact"  # exact/equal/subset/superset/partial/open
    unique_keys: Optional[List[List[str]]] = None  # Gap 4: composite unique-key constraints
    schema_url: Optional[str] = None

    contract: Optional[Dict[str, str]] = None  # item 48: reconciliation contract, layered
                                                # under conform(contract=...) overrides

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "schema_url" and getattr(self, "_schema_url_frozen", False):
            raise TypeError("TypeSpec.schema_url is immutable after construction")
        super().__setattr__(name, value)

    def __post_init__(self) -> None:
        if not isinstance(self.fields, Mapping):
            raise TypeError(
                "TypeSpec.fields requires a name-to-FieldSpec mapping, "
                f"e.g. TypeSpec(fields={{'id': FieldSpec(type=...)}}). {_MIGRATION_GUIDE}"
            )
        if any(not isinstance(name, str) or not isinstance(value, FieldSpec)
               for name, value in self.fields.items()):
            raise TypeError("TypeSpec.fields requires string names and FieldSpec definitions")
        self.fields = dict(self.fields)
        reject_typed_profile_at(
            self.schema_url,
            descriptor_kind="schema",
            extras=None,
            location=InvariantLocation("$"),
        )
        # An explicitly-empty dict carries no dimensions and must never be
        # mistaken for an explicit layer downstream (resolve_contract flips
        # `from_preset=False` on any non-None contract) — normalise to None.
        if self.contract is not None and len(self.contract) == 0:
            self.contract = None
        if self.primary_key is not None:
            _validate_key_shape(self.primary_key, "primary_key")
        if self.unique_keys is not None:
            for i, uk in enumerate(self.unique_keys):
                _validate_key_shape(uk, f"unique_keys[{i}]")
        object.__setattr__(self, "_schema_url_frozen", True)

    @classmethod
    def from_simple_dict(cls, columns: Dict[str, str], **metadata: Any) -> TypeSpec:
        """Create TypeSpec from a simple {name: type_string} dict.

        Args:
            columns: Dict mapping column names to type strings (e.g. "integer", "string")
            **metadata: Additional metadata (title, description, primary_key)

        Returns:
            TypeSpec with fields derived from the dict

        Example:
            >>> spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        """
        fields = {
            name: FieldSpec(type=parse_universal(type_str))
            for name, type_str in columns.items()
        }
        return cls(
            fields=fields,
            title=metadata.get("title"),
            description=metadata.get("description"),
            primary_key=metadata.get("primary_key"),
        )

    @classmethod
    def from_frictionless(cls, descriptor: Dict[str, Any]) -> TypeSpec:
        """Create TypeSpec from a Frictionless Table Schema descriptor dict.

        Delegates to the frictionless module (Task 3).
        """
        from mountainash.typespec.frictionless import typespec_from_frictionless
        return typespec_from_frictionless(descriptor)

    def to_frictionless(self) -> Dict[str, Any]:
        """Convert TypeSpec to a Frictionless Table Schema descriptor dict.

        Delegates to the frictionless module (Task 3).
        """
        from mountainash.typespec.frictionless import typespec_to_frictionless
        return typespec_to_frictionless(self)

    def to_contract(self, *, name: Optional[str] = None) -> Any:
        """Generate a native BaseDataContract subclass from this spec.

        Lazy import (same pattern as from_frictionless) — typespec has no
        static dependency on datacontracts.
        """
        from mountainash.datacontracts.compiler import contract_from_typespec
        return contract_from_typespec(self, name=name)

    def get_field(self, name: str) -> Optional[FieldSpec]:
        """Get a field by name."""
        return self.fields.get(name)

    @property
    def field_names(self) -> List[str]:
        """Get list of field names."""
        return list(self.fields)


@dataclass
class SpecDiff:
    """Result of comparing two TypeSpecs."""

    added_fields: List[str] = field(default_factory=list)
    removed_fields: List[str] = field(default_factory=list)
    type_changes: Dict[str, tuple] = field(default_factory=dict)
    is_compatible: bool = True

    @property
    def has_changes(self) -> bool:
        return bool(self.added_fields or self.removed_fields or self.type_changes)

    # ---- Aliases for validator compatibility ----

    @property
    def missing_columns(self) -> List[str]:
        """Columns present in expected (target) but absent in actual (source)."""
        return self.added_fields

    @property
    def extra_columns(self) -> List[str]:
        """Columns present in actual (source) but absent in expected (target)."""
        return self.removed_fields

    @property
    def type_mismatches(self) -> List[tuple]:
        """List of (column, actual_type, expected_type) tuples."""
        return [(col, actual, expected) for col, (actual, expected) in self.type_changes.items()]


def compare_specs(
    source: TypeSpec,
    target: TypeSpec,
    check_constraints: bool = True,
) -> SpecDiff:
    """Compare two TypeSpecs and return a SpecDiff.

    Args:
        source: The actual / output spec
        target: The expected spec to compare against
        check_constraints: Ignored (reserved for future constraint comparison)

    Returns:
        SpecDiff describing the differences
    """
    source_names = set(source.field_names)
    target_names = set(target.field_names)

    diff = SpecDiff(
        # Fields in target but not in source → missing from actual output
        added_fields=sorted(target_names - source_names),
        # Fields in source but not in target → extra in actual output
        removed_fields=sorted(source_names - target_names),
    )

    # Check type changes for common fields
    for name in source_names & target_names:
        source_field = source.get_field(name)
        target_field = target.get_field(name)
        if not (source_field and target_field):
            continue
        if source_field.type != target_field.type:
            diff.type_changes[name] = (source_field.type, target_field.type)
        elif source_field.dtype != target_field.dtype:
            # Compare authored identities, not backend-dependent effective targets.
            diff.type_changes[name] = (source_field.dtype or source_field.type,
                                       target_field.dtype or target_field.type)

    diff.is_compatible = not diff.added_fields and not diff.type_changes
    return diff


__all__ = [
    "LabeledValue",
    "MissingValue",
    "FieldConstraints",
    "ForeignKeyReference",
    "ForeignKey",
    "FieldSpec",
    "TypeSpec",
    "SpecDiff",
    "compare_specs",
]
