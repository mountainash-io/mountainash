"""
Shared schema declarations — FieldDefinition, FieldConstraints, TableSchema.

A ``FieldDefinition`` is an immutable, unnamed declaration (type, constraints,
conversion instructions, native overrides, source binding, severity). A
``TableSchema`` supplies local names and order through a copied, ordered
mapping of definitions plus table-level declarations.

This module is backend-agnostic and has ZERO imports of DataFrame libraries,
ensuring fast imports and true portability.

Reference: https://specs.frictionlessdata.io/table-schema/
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import InitVar, dataclass, field, fields as dataclass_fields, replace
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


class FrozenDict(dict):
    """Read-only dict that keeps ``dict`` compatibility (json, isinstance, equality)."""

    __slots__ = ()

    def _readonly(self, *args: Any, **kwargs: Any) -> Any:
        raise TypeError("declaration mappings are immutable")

    __setitem__ = __delitem__ = __ior__ = _readonly
    update = pop = popitem = clear = setdefault = _readonly

    def __reduce__(self) -> Any:
        return (FrozenDict, (dict(self),))

    def __copy__(self) -> "FrozenDict":
        return self

    def __deepcopy__(self, memo: Any) -> "FrozenDict":
        return FrozenDict((deepcopy(k, memo), deepcopy(v, memo)) for k, v in self.items())


def _own(value: Any) -> Any:
    """Return an immutable owned copy of plain declaration data."""
    if value is None or isinstance(value, (str, bytes)):
        return value
    if isinstance(value, Mapping):
        return FrozenDict((key, _own(item)) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return tuple(_own(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_own(item) for item in value)
    return value


def _own_sequence(value: Any) -> Any:
    return None if value is None else tuple(_own(item) for item in value)


@dataclass(frozen=True)
class LabeledValue:
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
        object.__setattr__(self, "value", _own(self.value))


MissingValue = Union[str, LabeledValue]


def _validate_key_shape(value: Any, label: str) -> None:
    """Module-private helper shared by TableSchema, ForeignKey, and
    ForeignKeyReference — every key-shaped field validates through this one
    function. Raises InvalidKeyShapeError unless ``value`` is a list[str]."""
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise InvalidKeyShapeError(label, value, "list[str]")


@dataclass(frozen=True)
class FieldConstraints:
    """Immutable constraints for a field (Frictionless Table Schema compliant)."""

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
    eq: Optional[Any] = None
    ne: Optional[Any] = None
    notin: Optional[List[Any]] = None
    str_contains: Optional[str] = None
    str_startswith: Optional[str] = None
    str_endswith: Optional[str] = None

    def __post_init__(self) -> None:
        for name in ("minimum", "maximum", "exclusive_minimum", "exclusive_maximum",
                     "enum", "enum_weights", "json_schema", "eq", "ne", "notin"):
            object.__setattr__(self, name, _own(getattr(self, name)))


_CONSTRAINT_KEYS = tuple(item.name for item in dataclass_fields(FieldConstraints))


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



_PORTABLE_DTYPES = (
    MountainashDtype, DecimalDtype, TimestampDtype, TimeDtype,
    DurationDtype, ListDtype, ArrayDtype, StructDtype,
)


def _canonical_of(definition: "FieldDefinition") -> Any:
    """Canonical type a definition contributes as a nested member or element."""
    if definition.dtype is not None:
        return definition.dtype
    if isinstance(definition.backend_type, NativeDtype):
        return definition.backend_type
    from mountainash.typespec.converters import _resolve_broad_field_canonical
    return _resolve_broad_field_canonical(definition) or SchemaTypeStatus.UNKNOWN


@dataclass(frozen=True, kw_only=True)
class FieldDefinition:
    """An immutable, unnamed field declaration (Frictionless Table Schema compliant).

    Names and order come from the enclosing ``TableSchema`` mapping (or the
    parent's ``fields``); the source column is ``rename_from`` when set,
    otherwise the local name. Nested shape is declared with ``fields`` (ordered
    named members), ``element`` and ``dimensions``; ``dtype`` is then derived.
    ``fields``/``element``/``dimensions`` accept ``SchemaTypeStatus.UNKNOWN``
    (unknown shape, distinct from an empty ``fields={}``).

    Constraint keywords (``minimum=...``) overlay ``constraints`` after it is
    taken, and are readable as flat properties.
    """

    type: UniversalType = UniversalType.ANY
    format: str = "default"
    title: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[FieldConstraints] = None
    missing_values: Optional[List[MissingValue]] = None
    true_values: Optional[List[str]] = None
    false_values: Optional[List[str]] = None
    categories: Optional[List[Union[Any, LabeledValue]]] = None
    categories_ordered: Optional[bool] = None
    example: Optional[Any] = None
    rdf_type: Optional[str] = None
    decimal_char: Optional[str] = None
    group_char: Optional[str] = None
    bare_number: Optional[bool] = None
    item_type: Optional[str] = None  # valid only when type is LIST (lexical)
    fields: Any = None  # ordered {name: FieldDefinition} | UNKNOWN | None
    element: Any = None  # FieldDefinition | UNKNOWN | None
    dimensions: Any = None  # tuple[int, ...] | UNKNOWN | None
    delimiter: Optional[str] = None  # valid only when type is LIST (lexical)
    backend_type: Any = None  # str or native dtype; native objects normalize to NativeDtype
    dtype: PortableDtype | SchemaTypeStatus | None = None
    null_fill: Any = None
    rename_from: Optional[str] = None
    custom_cast: Optional[str] = None
    rounding: str | None = None  # x-mountainash: conversion instruction, not dtype identity
    severity: Optional[str] = None  # None = system default
    __ordered_named_fields__ = ("fields",)  # snapshot: ordered pairs, not a sorted map
    # Constraint keywords overlaying ``constraints`` (None = unspecified).
    required: InitVar[Optional[bool]] = None
    unique: InitVar[Optional[bool]] = None
    minimum: InitVar[Any] = None
    maximum: InitVar[Any] = None
    exclusive_minimum: InitVar[Any] = None
    exclusive_maximum: InitVar[Any] = None
    min_length: InitVar[Optional[int]] = None
    max_length: InitVar[Optional[int]] = None
    pattern: InitVar[Optional[str]] = None
    enum: InitVar[Any] = None
    enum_weights: InitVar[Any] = None
    json_schema: InitVar[Any] = None
    eq: InitVar[Any] = None
    ne: InitVar[Any] = None
    notin: InitVar[Any] = None
    str_contains: InitVar[Optional[str]] = None
    str_startswith: InitVar[Optional[str]] = None
    str_endswith: InitVar[Optional[str]] = None

    def __post_init__(self, *overlay: Any) -> None:
        def set_(name: str, value: Any) -> None:
            object.__setattr__(self, name, value)

        # constraints: replacement object first, then keyword overlay
        constraints = self.constraints if self.constraints is not None else FieldConstraints()
        changes = {k: v for k, v in zip(_CONSTRAINT_KEYS, overlay) if v is not None}
        set_("constraints", replace(constraints, **changes) if changes else constraints)
        for name in ("missing_values", "true_values", "false_values", "categories"):
            set_(name, _own_sequence(getattr(self, name)))
        set_("example", _own(self.example))
        set_("null_fill", _own(self.null_fill))
        if self.severity is not None:
            from mountainash.validation.checks import validate_severity
            validate_severity("FieldDefinition", self.severity)

        self._declare_composition(set_)

        if self.dtype is not None and self.dtype is not SchemaTypeStatus.UNKNOWN:
            if not isinstance(self.dtype, _PORTABLE_DTYPES):
                raise InvalidDtypeDeclaration(
                    None, "dtype requires a portable dtype or UNKNOWN", self.dtype
                )
            broad, fmt = from_canonical(self.dtype)
            if isinstance(self.dtype, DurationDtype):
                broad = UniversalType.ANY
            if self.dtype in (MountainashDtype.JSON, MountainashDtype.DURATION):
                broad = UniversalType.ANY
            if self.type is UniversalType.ANY:
                set_("type", broad)
            elif self.type is UniversalType.GEOPOINT:
                from mountainash.typespec.converters import _resolve_broad_field_canonical
                if _resolve_broad_field_canonical(self) != self.dtype:
                    raise IncompatibleFieldPropertiesError(None, "dtype", self.type, (broad,))
            elif not (
                self.type is broad
                or (self.dtype is MountainashDtype.JSON and self.type is UniversalType.GEOJSON)
                or (self.dtype is MountainashDtype.LIST and self.type is UniversalType.LIST)
            ):
                raise IncompatibleFieldPropertiesError(None, "dtype", self.type, (broad,))
            if fmt is not None:
                if self.format not in ("default", fmt):
                    raise InvalidDtypeDeclaration(None, "dtype contradicts field format", self.format)
                set_("format", fmt)
            if self.dtype is MountainashDtype.STRING and self.format == "binary":
                raise InvalidDtypeDeclaration(None, "string dtype contradicts binary format")
            set_("dtype", deepcopy(self.dtype))
        if self.backend_type is not None and not isinstance(self.backend_type, str):
            native = parse_cast_target(self.backend_type)
            if not isinstance(native, NativeDtype):
                raise InvalidDtypeDeclaration(None, "backend_type requires a native dtype", self.backend_type)
            set_("backend_type", deepcopy(native))
        for prop, owner in (("item_type", self.item_type), ("delimiter", self.delimiter)):
            if owner is not None and self.type is not UniversalType.LIST:
                raise IncompatibleFieldPropertiesError(None, prop, self.type, (UniversalType.LIST,))
        if self.element is not None or self.dimensions is not None:
            for prop, value in (("element", self.element), ("dimensions", self.dimensions)):
                if value is not None and self.type is not UniversalType.ARRAY:
                    raise IncompatibleFieldPropertiesError(None, prop, self.type, (UniversalType.ARRAY,))
        if self.fields is not None and self.type is not UniversalType.OBJECT:
            raise IncompatibleFieldPropertiesError(None, "fields", self.type, (UniversalType.OBJECT,))
        if isinstance(self.dtype, DecimalDtype) and self.categories is not None:
            raise InvalidDtypeDeclaration(None, "dtype and categories cannot be combined")
        if self.rounding is not None:
            if not isinstance(self.dtype, DecimalDtype):
                raise InvalidDtypeDeclaration(None, "rounding requires a DecimalDtype")
            if not isinstance(self.rounding, str) or self.rounding not in DECIMAL_ROUNDING_MODES:
                raise InvalidDtypeDeclaration(None, "invalid decimal rounding mode", self.rounding)

    def _declare_composition(self, set_: Any) -> None:
        """Own fields/element/dimensions and derive the recursive portable dtype."""
        unknown = SchemaTypeStatus.UNKNOWN
        fields = self.fields
        if fields is not None and fields is not unknown:
            if not isinstance(fields, Mapping) or not all(
                isinstance(name, str) and isinstance(child, FieldDefinition)
                for name, child in fields.items()
            ):
                raise InvalidDtypeDeclaration(None, "fields requires a mapping of name to FieldDefinition", fields)
            fields = FrozenDict(fields)
            set_("fields", fields)
        element = self.element
        if element is not None and element is not unknown and not isinstance(element, FieldDefinition):
            raise InvalidDtypeDeclaration(None, "element requires a FieldDefinition or UNKNOWN", element)
        dimensions = self.dimensions
        if dimensions is not None and dimensions is not unknown:
            if not isinstance(dimensions, (tuple, list)):
                raise InvalidDtypeDeclaration(None, "dimensions requires a tuple of sizes or UNKNOWN", dimensions)
            dimensions = tuple(dimensions)
            set_("dimensions", dimensions)
        if fields is None and element is None and dimensions is None:
            return
        if fields is not None and (element is not None or dimensions is not None):
            raise InvalidDtypeDeclaration(None, "fields cannot be combined with element or dimensions")
        if fields is not None:
            derived: Any = StructDtype(fields=unknown if fields is unknown else tuple(
                (name, _canonical_of(child)) for name, child in fields.items()
            ))
        else:
            inner = unknown if element is None or element is unknown else _canonical_of(element)
            derived = (
                ListDtype(element=inner) if dimensions is None
                else ArrayDtype(element=inner, dimensions=dimensions)
            )
        if self.dtype is not None:
            raise InvalidDtypeDeclaration(
                None, "dtype cannot be combined with fields, element or dimensions", self.dtype
            )
        set_("dtype", derived)

    def to_checks(self, name: str) -> "list[Any]":
        """Compile this definition's constraints into validation checks for column ``name``."""
        from mountainash.datacontracts.compiler import compile_field_checks
        return list(compile_field_checks(self, name))

    def _snapshot_omitted_fields(self) -> tuple[str, ...]:
        """Derived members omitted from operation snapshots (rebuilt on thaw)."""
        nested = (self.fields, self.element, self.dimensions)
        return ("dtype",) if any(value is not None for value in nested) else ()

    def variant(self, **changes: Any) -> "FieldDefinition":
        """Return an independent copy with ``changes`` applied.

        Unspecified properties (including every unspecified constraint) are
        retained. A ``constraints`` replacement is applied first, then constraint
        keywords overlay it. Changing nested shape re-derives ``dtype``.
        """
        values = {item.name: getattr(self, item.name) for item in dataclass_fields(self) if item.init}
        nested = ("fields", "element", "dimensions")
        if any(values[name] is not None for name in nested) and "dtype" not in changes:
            values["dtype"] = None  # derived from the nested declaration
        if set(nested) & changes.keys() and "dtype" not in changes:
            values.update(fields=None, element=None, dimensions=None)
        values.update(changes)
        return FieldDefinition(**values)


def _constraint_property(key: str) -> property:
    return property(lambda self: getattr(self.constraints, key), doc=f"Flat view of constraints.{key}.")


for _key in _CONSTRAINT_KEYS:
    setattr(FieldDefinition, _key, _constraint_property(_key))
del _key


@dataclass
class TableSchema:
    """Schema definition for a dataset (Frictionless Table Schema representation).

    ``fields`` is a copied, mutable, ordered ``{name: FieldDefinition}`` mapping;
    mapping keys supply names and order. Operations capture snapshots.

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

    __ordered_named_fields__ = ("fields",)  # snapshot: ordered pairs, not a sorted map

    fields: Dict[str, FieldDefinition] = field(default_factory=dict)
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
            raise TypeError("TableSchema.schema_url is immutable after construction")
        if name == "fields":
            value = self._copy_fields(value)
        super().__setattr__(name, value)

    @staticmethod
    def _copy_fields(value: Any) -> Dict[str, FieldDefinition]:
        if not isinstance(value, Mapping) or not all(
            isinstance(name, str) and isinstance(item, FieldDefinition)
            for name, item in value.items()
        ):
            raise InvalidDtypeDeclaration(
                None, "TableSchema.fields requires a mapping of name to FieldDefinition", value
            )
        return dict(value)

    def __post_init__(self) -> None:
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
    def from_simple_dict(cls, columns: Dict[str, str], **metadata: Any) -> TableSchema:
        """Create a TableSchema from a simple {name: type_string} dict.

        Args:
            columns: Dict mapping column names to type strings (e.g. "integer", "string")
            **metadata: Additional metadata (title, description, primary_key)

        Example:
            >>> schema = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        """
        return cls(
            fields={
                name: FieldDefinition(type=parse_universal(type_str))
                for name, type_str in columns.items()
            },
            title=metadata.get("title"),
            description=metadata.get("description"),
            primary_key=metadata.get("primary_key"),
        )

    @classmethod
    def from_frictionless(cls, descriptor: Dict[str, Any]) -> TableSchema:
        """Create a TableSchema from a Frictionless Table Schema descriptor dict."""
        from mountainash.typespec.frictionless import table_schema_from_frictionless
        return table_schema_from_frictionless(descriptor)

    def to_frictionless(self) -> Dict[str, Any]:
        """Convert this TableSchema to a Frictionless Table Schema descriptor dict."""
        from mountainash.typespec.frictionless import table_schema_to_frictionless
        return table_schema_to_frictionless(self)

    def to_contract(self, *, name: Optional[str] = None) -> Any:
        """Generate a native BaseDataContract subclass from this schema.

        Lazy import — typespec has no static dependency on datacontracts.
        """
        from mountainash.datacontracts.compiler import contract_from_table_schema
        return contract_from_table_schema(self, name=name)

    def get_field(self, name: str) -> Optional[FieldDefinition]:
        """Get a field definition by name."""
        return self.fields.get(name)

    @property
    def field_names(self) -> List[str]:
        """Get list of field names in declaration order."""
        return list(self.fields)


@dataclass
class SpecDiff:
    """Result of comparing two TableSchemas."""

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
    source: TableSchema,
    target: TableSchema,
    check_constraints: bool = True,
) -> SpecDiff:
    """Compare two TableSchemas and return a SpecDiff.

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
        source_field = source.fields[name]
        target_field = target.fields[name]
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
    "FieldDefinition",
    "TableSchema",
    "SpecDiff",
    "compare_specs",
]
