"""Backend-neutral conformance contract evaluation and AST lowering."""
from __future__ import annotations

import dataclasses
import enum
import warnings
from dataclasses import dataclass, field as dataclass_field
from typing import TYPE_CHECKING, Any, Callable, Mapping, Optional, Sequence, Union

from mountainash.conform.contract import ConformContract, resolve_contract
from mountainash.conform.errors import (
    ConformError,
    ExactFieldsMismatchError,
    ExtraFieldsError,
    IncompatibleSourceTypeError,
    MissingFieldsError,
    NoMatchingFieldsError,
    SchemaDriftError,
    UnresolvedSourceTypeError,
)
from mountainash.typespec.source_shape import SourceShape

if TYPE_CHECKING:
    from mountainash.conform.drift import ConformDrift, KeyDrift
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.spec import FieldSpec, ForeignKey, TypeSpec

_VALID_FIELDS_MATCH = frozenset({"open", "exact", "equal", "subset", "superset", "partial"})


class _DeclaredTypeSentinel(enum.Enum):
    PASSTHROUGH = "PASSTHROUGH"
    UNDETERMINED = "UNDETERMINED"


PASSTHROUGH = _DeclaredTypeSentinel.PASSTHROUGH
UNDETERMINED = _DeclaredTypeSentinel.UNDETERMINED
DeclaredType = Union["MountainashDtype", _DeclaredTypeSentinel]


@dataclass(frozen=True)
class EmittedField:
    field: "FieldSpec"
    source_name: str
    declared_type: DeclaredType
    renamed: bool
    type_action: str = "coerce"
    effective_type: Optional[Any] = None
    source_shape: SourceShape = SourceShape(None)


@dataclass(frozen=True)
class MaterializationResidueCheck:
    function_key: Any
    field_name: str
    marker: Any


@dataclass(frozen=True)
class FieldBuildResult:
    output: Any
    discard_row_filter: Any | None = None
    residue_checks: tuple[MaterializationResidueCheck, ...] = ()


@dataclass(frozen=True)
class ConformOutputContract:
    fields_match: str
    emitted: list[EmittedField]
    renamed_sources: set[str]
    drift: Optional["ConformDrift"] = None

    @property
    def keeps_unmapped(self) -> bool:
        return self.fields_match == "open"


@dataclass
class ConformResult:
    exprs: list[Any]
    fields_match: str
    renamed_sources: set[str] = dataclass_field(default_factory=set)
    drift: "ConformDrift | None" = None
    row_filters: list[Any] = dataclass_field(default_factory=list)
    residue_checks: list[MaterializationResidueCheck] = dataclass_field(default_factory=list)


def _source_root(source_name: str) -> str:
    return source_name.split(".", 1)[0] if "." in source_name else source_name


def _raise_drift(
    *,
    missing_columns: Optional[Sequence[str]] = None,
    extra_columns: Optional[Sequence[str]] = None,
    type_mismatches: Optional[Sequence[Any]] = None,
    key_changes: Optional[Sequence[Any]] = None,
    node_identity: Optional[tuple] = None,
) -> None:
    from mountainash.conform.drift import ColumnDrift, ConformDrift

    node_id, resource_name, spec_name = node_identity or (None, None, None)
    drift = ConformDrift(
        node_id=node_id,
        resource_name=resource_name,
        spec_name=spec_name,
        extra_columns=[ColumnDrift(name=n, action="freeze") for n in (extra_columns or ())],
        missing_columns=[ColumnDrift(name=n, action="freeze") for n in (missing_columns or ())],
        type_mismatches=list(type_mismatches or ()),
        key_changes=list(key_changes) if key_changes is not None else None,
    )
    if extra_columns:
        dimension = "extra_columns"
    elif missing_columns:
        dimension = "missing_columns"
    elif key_changes:
        dimension = "keys"
    else:
        dimension = "data_type"
    raise SchemaDriftError(f"{dimension} drift under freeze policy", drift=drift)


def _resolve_declared_type(fld: "FieldSpec", source_name: str) -> DeclaredType:
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.converters import resolve_field_canonical
    from mountainash.typespec.universal_types import UniversalType, to_canonical

    if fld.type == UniversalType.LIST:
        return to_canonical(UniversalType.LIST)  # type: ignore[return-value]
    if fld.categories is not None:
        return MountainashDtype.STRING
    if fld.type in {UniversalType.DATE, UniversalType.DATETIME, UniversalType.TIME} and fld.format not in ("default", None, "any"):
        return to_canonical(fld.type) or UNDETERMINED
    if fld.type == UniversalType.GEOPOINT:
        return resolve_field_canonical(fld) or UNDETERMINED
    if fld.type == UniversalType.BOOLEAN:
        return to_canonical(UniversalType.BOOLEAN) or UNDETERMINED
    if fld.type and fld.type is not UniversalType.ANY:
        return resolve_field_canonical(fld) or PASSTHROUGH
    if fld.null_fill is not None or "." in source_name:
        return UNDETERMINED
    return PASSTHROUGH


def _declared_canonical(fld: "FieldSpec") -> Optional["MountainashDtype"]:
    from mountainash.core.dtypes import MountainashDtype

    value = _resolve_declared_type(fld, fld.source_name)
    return value if isinstance(value, MountainashDtype) else None


def _shape_for(
    actual_shapes: Mapping[str, SourceShape] | None,
    source_name: str,
) -> SourceShape | None:
    if actual_shapes is None:
        return None
    shape = actual_shapes.get(source_name)
    if shape is not None or "." not in source_name:
        return shape
    root, *parts = source_name.split(".")
    shape = actual_shapes.get(root)
    for part in parts:
        if shape is None or shape.canonical_type is None:
            return None
        shape = dict(shape.struct_fields).get(part)
    return shape


def _shape_detail(shape: SourceShape | None) -> str | None:
    if shape is None or shape.canonical_type is None:
        return None
    if shape.canonical_type.name == "LIST" and shape.item_shape is not None:
        return f"LIST[{_shape_detail(shape.item_shape) or 'unknown'}]"
    if shape.canonical_type.name == "STRUCT":
        return "STRUCT{" + ",".join(
            f"{name}:{_shape_detail(child) or 'unknown'}"
            for name, child in shape.struct_fields
        ) + "}"
    return str(shape.canonical_type)


def _shape_diff(expected: SourceShape | None, actual: SourceShape | None) -> bool:
    if expected is None or actual is None:
        return False
    if expected.canonical_type != actual.canonical_type:
        return True
    if expected.canonical_type is None:
        return False
    if expected.canonical_type.name == "LIST":
        if (expected.item_shape is None) != (actual.item_shape is None):
            return True
        return _shape_diff(expected.item_shape, actual.item_shape)
    if expected.canonical_type.name == "STRUCT":
        actual_fields = dict(actual.struct_fields)
        if tuple(name for name, _ in expected.struct_fields) != tuple(actual_fields):
            return True
        return any(
            _shape_diff(child, actual_fields.get(name))
            for name, child in expected.struct_fields
        )
    return False


def _expected_shape(fld: "FieldSpec") -> SourceShape | None:
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.converters import resolve_field_canonical
    from mountainash.typespec.universal_types import parse_universal, to_canonical, UniversalType

    canonical = resolve_field_canonical(fld)
    if canonical is None:
        return None
    if fld.type is UniversalType.GEOPOINT:
        if fld.format == "array":
            return SourceShape(canonical, SourceShape(MountainashDtype.FP64))
        if fld.format == "object":
            return SourceShape(
                canonical,
                struct_fields=(
                    ("lon", SourceShape(MountainashDtype.FP64)),
                    ("lat", SourceShape(MountainashDtype.FP64)),
                ),
            )
    if canonical is MountainashDtype.LIST:
        if fld.item_type:
            item = to_canonical(parse_universal(fld.item_type))
            return SourceShape(canonical, SourceShape(item)) if item else SourceShape(canonical)
        if fld.item_object_fields:
            return SourceShape(
                canonical,
                SourceShape(
                    MountainashDtype.STRUCT,
                    struct_fields=tuple(
                        (inner.name, _expected_shape(inner) or SourceShape(None))
                        for inner in fld.item_object_fields
                    ),
                ),
            )
        return SourceShape(canonical, SourceShape(MountainashDtype.STRING))
    if canonical is MountainashDtype.STRUCT and fld.object_fields:
        return SourceShape(
            canonical,
            struct_fields=tuple(
                (inner.name, _expected_shape(inner) or SourceShape(None))
                for inner in fld.object_fields
            ),
        )
    return SourceShape(canonical)


def resolve_conform_output(
    spec: "TypeSpec",
    available_columns: Sequence[str] | None = None,
    *,
    actual_dtypes: Mapping[str, Any] | None = None,
    actual_shapes: Mapping[str, SourceShape] | None = None,
    contract: ConformContract | None = None,
    node_identity: tuple | None = None,
    raise_on_freeze: bool = True,
    key_fks: Sequence["ForeignKey"] | None = None,
    key_resource_name: str | None = None,
    schema_of: Callable[[str], Mapping[str, Any]] | None = None,
    apply_value_transforms: bool = True,
) -> ConformOutputContract:
    """Resolve structure, source evidence, drift, and per-field action policy."""
    from mountainash.conform.drift import ColumnDrift, ConformDrift, KeyDrift, TypeDrift
    from mountainash.core.dtypes import CastSafety, MountainashDtype, classify_cast
    from mountainash.relations.schema_inference import SchemaTypeStatus

    fields_match = spec.fields_match
    if fields_match not in _VALID_FIELDS_MATCH:
        raise ConformError(f"Invalid fields_match={fields_match!r}. Must be one of: {sorted(_VALID_FIELDS_MATCH)}")
    if fields_match != "open" and available_columns is None:
        raise ConformError(f"fieldsMatch={fields_match!r} requires available_columns to be provided")
    contract = contract or resolve_contract(fields_match)

    available_set: set[str] | None = set(available_columns) if available_columns is not None else None
    spec_sources = tuple(field.source_name for field in spec.fields)
    missing: list[str] = []
    extra: list[str] = []
    if available_columns is not None:
        if fields_match == "exact":
            if any("." in source for source in spec_sources):
                raise ExactFieldsMismatchError(expected=spec_sources, actual=tuple(available_columns), reason="nested_source")
            if len(available_columns) != len(spec_sources):
                raise ExactFieldsMismatchError(expected=spec_sources, actual=tuple(available_columns), reason="count")
            if set(available_columns) != set(spec_sources):
                raise ExactFieldsMismatchError(expected=spec_sources, actual=tuple(available_columns), reason="name")
            if tuple(available_columns) != spec_sources:
                raise ExactFieldsMismatchError(expected=spec_sources, actual=tuple(available_columns), reason="order")
        roots = {_source_root(source) for source in spec_sources}
        if contract.mapping == "by_name":
            if contract.minimum_overlap and len(roots & available_set) < contract.minimum_overlap:
                raise NoMatchingFieldsError(spec_fields=sorted(spec_sources), available_columns=sorted(available_set))
            missing = sorted(roots - available_set)
            extra = sorted(available_set - roots)
            if contract.missing_columns == "freeze" and missing:
                if contract.from_preset:
                    raise MissingFieldsError(missing_fields=missing, fields_match=fields_match)
                if raise_on_freeze:
                    _raise_drift(missing_columns=missing, node_identity=node_identity)
            if contract.extra_columns == "freeze" and extra:
                if contract.from_preset:
                    raise ExtraFieldsError(extra_fields=extra, fields_match=fields_match)
                if raise_on_freeze:
                    _raise_drift(extra_columns=extra, node_identity=node_identity)

    emitted: list[EmittedField] = []
    renamed_sources: set[str] = set()
    for field in spec.fields:
        source_name = field.source_name
        if available_set is not None and _source_root(source_name) not in available_set:
            if contract.missing_columns == "null_fill":
                declared = _declared_canonical(field)
                emitted.append(EmittedField(field, source_name, declared or UNDETERMINED, False, "null_fill", source_shape=SourceShape(None)))
            continue
        renamed = "." not in source_name and source_name != field.name
        if renamed:
            renamed_sources.add(source_name)
        emitted.append(EmittedField(field, source_name, _resolve_declared_type(field, source_name), renamed, source_shape=_shape_for(actual_shapes, source_name)))  # type: ignore[arg-type]

    type_mismatches: list[TypeDrift] = []
    resolved: list[EmittedField] = []
    for em in emitted:
        if em.type_action == "null_fill":
            resolved.append(em)
            continue
        actual_shape = _shape_for(actual_shapes, em.source_name)
        if "." in em.source_name and actual_shape is None:
            resolved.append(em)
            continue
        declared = _declared_canonical(em.field)
        actual_dtype = (actual_dtypes or {}).get(em.source_name)
        mismatch: TypeDrift | None = None
        if declared is not None and actual_shapes is not None:
            expected_shape = _expected_shape(em.field)
            requirement = _shape_detail(expected_shape) or str(declared)
            if actual_shape is None or actual_shape.canonical_type is None:
                mismatch = TypeDrift(em.field.name, declared, None, "unknown", None, "unknown", requirement=requirement, applied=apply_value_transforms)
            elif actual_shape.canonical_type != declared:
                safety = classify_cast(actual_shape.canonical_type, declared)
                numeric = {
                    MountainashDtype.I8, MountainashDtype.I16, MountainashDtype.I32, MountainashDtype.I64,
                    MountainashDtype.U8, MountainashDtype.U16, MountainashDtype.U32, MountainashDtype.U64,
                    MountainashDtype.FP32, MountainashDtype.FP64,
                }
                if safety is not CastSafety.SAFE or actual_shape.canonical_type not in numeric or declared not in numeric:
                    reason = "cast_safety" if safety is not CastSafety.SAFE else "representation"
                    mismatch = TypeDrift(em.field.name, declared, actual_shape.canonical_type, safety.value, None, reason, _shape_detail(actual_shape), requirement, apply_value_transforms)
            elif _shape_diff(expected_shape, actual_shape):
                mismatch = TypeDrift(em.field.name, declared, actual_shape.canonical_type, "unsafe", None, "shape", _shape_detail(actual_shape), requirement, apply_value_transforms)
        elif declared is not None and actual_dtypes is not None:
            requirement = _shape_detail(_expected_shape(em.field)) or str(declared)
            if actual_dtype is None or isinstance(actual_dtype, SchemaTypeStatus):
                mismatch = TypeDrift(em.field.name, declared, actual_dtype, "unknown", None, "unknown", None, requirement, apply_value_transforms)
            elif classify_cast(actual_dtype, declared) is not CastSafety.SAFE:
                mismatch = TypeDrift(em.field.name, declared, actual_dtype, "unsafe", None, "cast_safety", str(actual_dtype), requirement, apply_value_transforms)
        if mismatch is None:
            resolved.append(em)
            continue
        action = contract.data_type if apply_value_transforms and mismatch.reason != "unknown" else None
        applied = bool(apply_value_transforms and action is not None)
        mismatch = dataclasses.replace(mismatch, action=action, applied=applied)
        type_mismatches.append(mismatch)
        if action == "evolve":
            em = dataclasses.replace(em, type_action="evolve", effective_type=mismatch.actual)
        elif action in {"discard_value", "discard_row"}:
            em = dataclasses.replace(em, type_action=action)
        resolved.append(em)
    emitted = resolved

    if apply_value_transforms and contract.data_type == "freeze" and any(item.reason != "unknown" for item in type_mismatches) and raise_on_freeze:
        _raise_drift(type_mismatches=type_mismatches, node_identity=node_identity)

    key_changes: list["KeyDrift"] | None = None
    if key_fks is not None:
        key_changes = []
        emitted_by_name = {em.field.name: em for em in emitted}
        for fk in key_fks:
            target = fk.reference.resource or key_resource_name
            dropped = [name for name in fk.fields if name not in emitted_by_name]
            if dropped:
                key_changes.append(KeyDrift("fk_field_dropped", dropped, target, action=contract.keys))
                continue
            if target is None:
                key_changes.append(KeyDrift("dangling_reference", list(fk.fields), target, action=contract.keys))
                continue
            try:
                parent = schema_of(target) if schema_of else {}
            except KeyError:
                key_changes.append(KeyDrift("dangling_reference", list(fk.fields), target, action=contract.keys))
                continue
            if any(name not in parent for name in fk.reference.fields):
                key_changes.append(KeyDrift("dangling_reference", list(fk.fields), target, action=contract.keys))
                continue
            for local, remote in zip(fk.fields, fk.reference.fields):
                child = emitted_by_name.get(local)
                child_type = child.effective_type if child and child.effective_type is not None else (child.declared_type if child else None)
                parent_type = parent.get(remote)
                if isinstance(child_type, MountainashDtype) and isinstance(parent_type, MountainashDtype) and classify_cast(child_type, parent_type) is CastSafety.UNSAFE:
                    key_changes.append(KeyDrift("fk_type_mismatch", [local], target, declared=parent_type, actual=child_type, action=contract.keys))
        if contract.keys == "freeze" and key_changes and raise_on_freeze:
            _raise_drift(key_changes=key_changes, node_identity=node_identity)

    drift = None
    if available_set is not None or actual_dtypes is not None or actual_shapes is not None or key_changes is not None:
        node_id, resource_name, spec_name = node_identity or (None, None, None)
        drift = ConformDrift(
            node_id=node_id,
            resource_name=resource_name,
            spec_name=spec_name,
            extra_columns=[ColumnDrift(name=n, action=contract.extra_columns) for n in extra],
            missing_columns=[ColumnDrift(name=n, action=contract.missing_columns) for n in missing],
            type_mismatches=type_mismatches,
            key_changes=key_changes,
        )
    return ConformOutputContract(fields_match, emitted, renamed_sources, drift)


def _build_field_expr(
    field: "FieldSpec",
    source_name: str,
    schema_missing_values: Sequence[str] = (),
    *,
    type_action: str = "coerce",
    declared_type: Optional[DeclaredType] = None,
    source_shape: SourceShape | None = None,
) -> FieldBuildResult:
    """Lower one field through the backend-neutral expression API."""
    import mountainash as ma
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour
    from mountainash.typespec.universal_types import UniversalType, to_canonical

    fld = field
    if type_action == "null_fill":
        output = ma.lit(None)
        if isinstance(declared_type, MountainashDtype):
            output = output.cast(declared_type)
        return FieldBuildResult(output.name.alias(fld.name))

    is_dotted = "." in source_name
    if is_dotted:
        expr = ma.col(source_name.split(".", 1)[0])
        for part in source_name.split(".")[1:]:
            expr = expr.struct.field(part)
    else:
        expr = ma.col(source_name)

    shape_known = source_shape is not None
    shape = source_shape or SourceShape(None)
    canonical = shape.canonical_type
    if shape_known and canonical is None and fld.type in {UniversalType.LIST, UniversalType.ARRAY, UniversalType.OBJECT, UniversalType.GEOPOINT, UniversalType.GEOJSON}:
        raise UnresolvedSourceTypeError(field_name=fld.name, requirement="source shape for typed operation")
    if shape_known:
        allowed = {
            UniversalType.LIST: {MountainashDtype.STRING, MountainashDtype.LIST},
            UniversalType.ARRAY: {MountainashDtype.LIST},
            UniversalType.OBJECT: {MountainashDtype.STRUCT},
            UniversalType.GEOPOINT: {MountainashDtype.STRING, MountainashDtype.LIST, MountainashDtype.STRUCT},
            UniversalType.GEOJSON: {MountainashDtype.STRING, MountainashDtype.JSON},
        }
        if fld.type in allowed and canonical not in allowed[fld.type]:
            raise IncompatibleSourceTypeError(field_name=fld.name, source_detail=_shape_detail(shape) or "unknown", requirement=f"{fld.type.value} source")
    scalar_types = {
        UniversalType.STRING,
        UniversalType.NUMBER,
        UniversalType.INTEGER,
        UniversalType.BOOLEAN,
        UniversalType.DATE,
        UniversalType.DATETIME,
        UniversalType.TIME,
        UniversalType.YEAR,
        UniversalType.YEARMONTH,
        UniversalType.DURATION,
        UniversalType.LIST,
        UniversalType.GEOPOINT,
        UniversalType.GEOJSON,
    }
    lexical = not shape_known or canonical is None or canonical is MountainashDtype.STRING
    sentinels = fld.missing_values if fld.missing_values is not None else schema_missing_values
    from mountainash.typespec._categorical import categorical_values
    sentinel_values = categorical_values(list(sentinels))
    if sentinel_values and fld.type in scalar_types and lexical:
        if fld.type == UniversalType.BOOLEAN:
            true_values = fld.true_values or ["true", "True", "TRUE", "1"]
            false_values = fld.false_values or ["false", "False", "FALSE", "0"]
            overlap = set(sentinel_values) & set(true_values + false_values)
            if overlap:
                warnings.warn(f"Field {fld.name!r}: missingValues overlap boolean values", UserWarning, stacklevel=3)
        expr = ma.when(expr.is_in(*sentinel_values)).then(ma.lit(None)).otherwise(expr)

    if lexical and fld.type in (UniversalType.NUMBER, UniversalType.INTEGER):
        if fld.bare_number is False:
            expr = expr.str.regexp_replace(r"^[^\d\-+.]+", "").str.regexp_replace(r"[^\d.]+$", "")
        if fld.group_char is not None:
            expr = expr.str.replace(fld.group_char, "")
        if fld.decimal_char is not None and fld.decimal_char != ".":
            expr = expr.str.replace(fld.decimal_char, ".")
    post_missing = expr
    transform_input = expr
    if fld.null_fill is not None:
        expr = ma.coalesce(expr, ma.lit(fld.null_fill))
        transform_input = expr
    if type_action == "evolve":
        return FieldBuildResult(transform_input.name.alias(fld.name))
    failure = CaseFailureBehaviour.THROW if type_action == "coerce" else CaseFailureBehaviour.NULL
    residue: list[MaterializationResidueCheck] = []
    if fld.type == UniversalType.LIST and lexical:
        expr = expr.str.parse_list(item_type=fld.item_type or "string", delimiter=fld.delimiter or ",", field_name=fld.name, failure_behavior=failure)
    elif fld.type == UniversalType.LIST and canonical is MountainashDtype.LIST and not lexical:
        expr = expr.list.cast_items(
            item_type=fld.item_type or "string",
            field_name=fld.name,
            failure_behavior=failure,
        )
    elif fld.type == UniversalType.ARRAY and canonical is MountainashDtype.LIST and fld.item_object_fields and not lexical:
        expr = expr.list.cast_items(item_object_fields=tuple(fld.item_object_fields), field_name=fld.name, failure_behavior=failure)
    elif fld.type == UniversalType.BOOLEAN:
        true_values = tuple(fld.true_values or ["true", "True", "TRUE", "1"])
        false_values = tuple(fld.false_values or ["false", "False", "FALSE", "0"])
        expr = expr.parse_boolean(
            true_values=true_values,
            false_values=false_values,
            field_name=fld.name,
            failure_behavior=failure,
        )
    elif fld.type == UniversalType.OBJECT and fld.object_fields and not lexical:
        expr = expr.struct.cast(fields=tuple(fld.object_fields), field_name=fld.name, failure_behavior=failure)
    elif fld.categories is not None:
        from mountainash.typespec._categorical import categorical_values
        expr = expr.cat.cast(
            value_type=(fld.type.value if fld.type and fld.type is not UniversalType.ANY else "string"),
            categories=tuple(categorical_values(fld.categories)),
            ordered=bool(fld.categories_ordered),
            field_name=fld.name,
            failure_behavior=failure,
        )
    elif fld.type == UniversalType.GEOPOINT:
        fmt = fld.format
        if shape_known:
            if canonical is MountainashDtype.STRING:
                if fmt == "object":
                    raise IncompatibleSourceTypeError(field_name=fld.name, source_detail="STRING", requirement="native object or lexical array/default geopoint")
            elif canonical is MountainashDtype.LIST:
                if fmt != "array" or shape.item_shape is None or shape.item_shape.canonical_type not in {
                    MountainashDtype.I8, MountainashDtype.I16, MountainashDtype.I32, MountainashDtype.I64,
                    MountainashDtype.U8, MountainashDtype.U16, MountainashDtype.U32, MountainashDtype.U64,
                    MountainashDtype.FP32, MountainashDtype.FP64,
                }:
                    raise IncompatibleSourceTypeError(field_name=fld.name, source_detail=_shape_detail(shape) or "unknown", requirement="numeric native array geopoint")
            elif canonical is MountainashDtype.STRUCT:
                names = {name for name, child in shape.struct_fields}
                if fmt != "object" or names != {"lon", "lat"} or any(
                    child.canonical_type not in {
                        MountainashDtype.I8, MountainashDtype.I16, MountainashDtype.I32, MountainashDtype.I64,
                        MountainashDtype.U8, MountainashDtype.U16, MountainashDtype.U32, MountainashDtype.U64,
                        MountainashDtype.FP32, MountainashDtype.FP64,
                    }
                    for _, child in shape.struct_fields
                ):
                    raise IncompatibleSourceTypeError(field_name=fld.name, source_detail=_shape_detail(shape) or "unknown", requirement="numeric lon/lat native object geopoint")
        representation = "lexical" if lexical else "native"
        expr = expr.geo.parse_geopoint(format=fmt, source_representation=representation, field_name=fld.name, failure_behavior=failure)
    elif fld.type == UniversalType.GEOJSON and lexical:
        fmt = fld.format if fld.format in {"default", "topojson"} else "default"
        expr = expr.geo.parse_geojson(format=fmt, field_name=fld.name, failure_behavior=failure)
    elif fld.type in {UniversalType.DATE, UniversalType.DATETIME, UniversalType.TIME} and fld.format not in ("default", None, "any") and lexical:
        method = {UniversalType.DATE: expr.str.to_date, UniversalType.DATETIME: expr.str.to_datetime, UniversalType.TIME: expr.str.to_time}[fld.type]
        expr = method(fld.format, field_name=fld.name, failure_behavior=failure)
    elif fld.type == UniversalType.DATETIME and fld.format == "default" and lexical:
        expr = expr.dt.parse_default(field_name=fld.name, failure_behavior=failure)
    elif fld.type == UniversalType.DURATION and lexical:
        expr = expr.dt.parse_xsd_duration(field_name=fld.name, failure_behavior=CaseFailureBehaviour.NULL)
        if type_action == "coerce":
            residue.append(MaterializationResidueCheck(expr.node.function_key, fld.name, transform_input.is_not_null() & expr.is_null()))
    elif fld.type in {UniversalType.YEAR, UniversalType.YEARMONTH} and lexical:
        expr = expr.dt.parse_xsd_partial_date(kind=fld.type.value, field_name=fld.name, failure_behavior=CaseFailureBehaviour.NULL)
        if type_action == "coerce":
            residue.append(MaterializationResidueCheck(expr.node.function_key, fld.name, transform_input.is_not_null() & expr.is_null()))
    elif fld.type in {UniversalType.DATE, UniversalType.TIME} and fld.format == "any" and lexical:
        expr = expr.dt.parse_temporal_any(fld.type.value, field_name=fld.name, failure_behavior=failure)
    elif fld.type == UniversalType.DATETIME and fld.format == "any" and lexical:
        expr = expr.dt.parse_temporal_any("datetime", field_name=fld.name, failure_behavior=failure)
    elif fld.type and fld.type is not UniversalType.ANY:
        target = to_canonical(fld.type)
        if target is not None:
            expr = expr.cast(target, failure_behavior=failure)

    output = expr.name.alias(fld.name)
    discard = None
    if type_action == "discard_row":
        discard = ~(post_missing.is_not_null() & expr.is_null())
    return FieldBuildResult(output, discard, tuple(residue))


def _build_conform_exprs(
    spec: "TypeSpec",
    *,
    available_columns: Sequence[str] | None = None,
    actual_dtypes: Mapping[str, Any] | None = None,
    actual_shapes: Mapping[str, SourceShape] | None = None,
    contract: ConformContract | None = None,
    node_identity: tuple | None = None,
    key_fks: Sequence["ForeignKey"] | None = None,
    key_resource_name: str | None = None,
    schema_of: Callable[[str], Mapping[str, Any]] | None = None,
    apply_value_transforms: bool = True,
) -> ConformResult:
    schema_missing_values = spec.missing_values or []
    output_contract = resolve_conform_output(
        spec,
        available_columns,
        actual_dtypes=actual_dtypes,
        actual_shapes=actual_shapes,
        contract=contract,
        node_identity=node_identity,
        key_fks=key_fks,
        key_resource_name=key_resource_name,
        schema_of=schema_of,
        apply_value_transforms=apply_value_transforms,
    )
    exprs: list[Any] = []
    row_filters: list[Any] = []
    residue_checks: list[MaterializationResidueCheck] = []
    from mountainash.core.dtypes import MountainashDtype
    for emitted in output_contract.emitted:
        if not apply_value_transforms:
            import mountainash as ma
            if emitted.type_action == "null_fill":
                source = ma.lit(None)
                if isinstance(emitted.declared_type, MountainashDtype):
                    source = source.cast(emitted.declared_type)
                exprs.append(source.name.alias(emitted.field.name))
                continue
            source = ma.col(emitted.source_name.split(".", 1)[0])
            for part in emitted.source_name.split(".")[1:]:
                source = source.struct.field(part)
            shape = emitted.source_shape
            lexical_source = shape is None or shape.canonical_type in {None, MountainashDtype.STRING}
            sentinels = emitted.field.missing_values if emitted.field.missing_values is not None else schema_missing_values
            from mountainash.typespec._categorical import categorical_values
            values = categorical_values(list(sentinels))
            if lexical_source and values:
                source = ma.when(source.is_in(*values)).then(ma.lit(None)).otherwise(source)
            exprs.append(source.name.alias(emitted.field.name))
            continue
        built = _build_field_expr(
            emitted.field,
            emitted.source_name,
            schema_missing_values,
            type_action=emitted.type_action,
            declared_type=emitted.declared_type,
            source_shape=emitted.source_shape,
        )
        exprs.append(built.output)
        if built.discard_row_filter is not None:
            row_filters.append(built.discard_row_filter)
        residue_checks.extend(built.residue_checks)
    return ConformResult(
        exprs,
        output_contract.fields_match,
        output_contract.renamed_sources,
        output_contract.drift,
        row_filters,
        residue_checks,
    )
