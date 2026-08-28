"""Backend-neutral conformance contract evaluation and AST lowering."""
from __future__ import annotations

import dataclasses
import enum
import warnings
from dataclasses import dataclass, field as dataclass_field
from types import MappingProxyType
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
from mountainash.conform.structured_transport import (
    StructuredCarrier,
    StructuredFieldPlan,
    StructuredFieldPlanMap,
    StructuredRoot,
    freeze_structured_field_plans,
    freeze_structured_value,
)
from mountainash.typespec._fingerprint import declaration_fingerprint, freeze_typespec
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
    structured_field_plans: StructuredFieldPlanMap = dataclass_field(
        default_factory=lambda: MappingProxyType({})
    )


def _structured_carrier(
    field: "FieldSpec", source_shape: SourceShape | None
) -> StructuredCarrier | None:
    """Classify a declared structured field from schema evidence only."""
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.universal_types import UniversalType

    if field.type not in {UniversalType.ARRAY, UniversalType.OBJECT}:
        return None
    canonical = source_shape.canonical_type if source_shape is not None else None
    native = (
        MountainashDtype.LIST
        if field.type is UniversalType.ARRAY
        else MountainashDtype.STRUCT
    )
    if canonical is native:
        return StructuredCarrier.NATIVE
    if canonical in {MountainashDtype.STRING, MountainashDtype.JSON}:
        return StructuredCarrier.JSON_TEXT
    if canonical is None:
        return StructuredCarrier.OPAQUE
    return None


def _build_structured_field_plans(
    emitted: Sequence[EmittedField],
    *,
    schema_missing_values: Sequence[Any],
    data_type_action: str,
    apply_value_transforms: bool,
    declaration_fingerprint: str,
    node_identity: tuple | None,
) -> StructuredFieldPlanMap:
    """Freeze one transport plan for every declared ARRAY and OBJECT output field."""
    from mountainash.typespec._categorical import categorical_values
    from mountainash.typespec.universal_types import UniversalType

    plans: dict[str, StructuredFieldPlan] = {}
    origin_node_id = str(node_identity[0]) if node_identity else "standalone"
    for item in emitted:
        if item.field.type not in {UniversalType.ARRAY, UniversalType.OBJECT}:
            continue
        values = (
            item.field.missing_values
            if item.field.missing_values is not None
            else schema_missing_values
        )
        missing_values = tuple(
            value for value in categorical_values(list(values)) if isinstance(value, str)
        )
        carrier = _structured_carrier(item.field, item.source_shape)
        if carrier is None:
            continue
        plans[item.field.name] = StructuredFieldPlan(
            field_name=item.field.name,
            root=(
                StructuredRoot.ARRAY
                if item.field.type is UniversalType.ARRAY
                else StructuredRoot.OBJECT
            ),
            carrier=carrier,
            configured_action=data_type_action,  # type: ignore[arg-type]
            apply_value_transforms=apply_value_transforms,
            missing_values=missing_values,
            null_fill=freeze_structured_value(item.field.null_fill),
            declaration_fingerprint=declaration_fingerprint,
            origin_node_id=origin_node_id,
        )
    return freeze_structured_field_plans(plans)


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
    from mountainash.typespec.converters import resolve_field_canonical
    from mountainash.typespec.universal_types import UniversalType, to_canonical

    if fld.type == UniversalType.LIST:
        return to_canonical(UniversalType.LIST)  # type: ignore[return-value]
    if fld.categories is not None:
        return resolve_field_canonical(fld) or UNDETERMINED
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
    if shape is not None:
        return shape
    if "." not in source_name:
        return SourceShape(None)
    root, *parts = source_name.split(".")
    shape = actual_shapes.get(root)
    for part in parts:
        if shape is None or shape.canonical_type is None:
            return SourceShape(None)
        shape = dict(shape.struct_fields).get(part)
    return shape if shape is not None else SourceShape(None)


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


def _shape_diff(
    expected: SourceShape | None,
    actual: SourceShape | None,
    *,
    numeric_children: bool = False,
) -> bool:
    if expected is None or actual is None:
        return False
    if expected.canonical_type is None:
        return False
    if actual.canonical_type is None:
        return True
    if numeric_children and expected.canonical_type.name.startswith(("I", "U", "FP")):
        return not actual.canonical_type.name.startswith(("I", "U", "FP"))
    if expected.canonical_type != actual.canonical_type:
        return True
    if expected.canonical_type.name == "LIST":
        if expected.item_shape is None:
            return False
        if actual.item_shape is None:
            return True
        return _shape_diff(
            expected.item_shape,
            actual.item_shape,
            numeric_children=numeric_children,
        )
    if expected.canonical_type.name == "STRUCT":
        if not expected.struct_fields:
            return False
        actual_fields = dict(actual.struct_fields)
        expected_names = tuple(name for name, _ in expected.struct_fields)
        actual_names = tuple(actual_fields)
        if numeric_children and set(expected_names) == {"lon", "lat"}:
            if set(actual_names) != {"lon", "lat"}:
                return True
        elif expected_names != actual_names:
            return True
        return any(
            _shape_diff(
                child,
                actual_fields.get(name),
                numeric_children=numeric_children,
            )
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
        return SourceShape(canonical)
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
    from mountainash.typespec.universal_types import UniversalType

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
    has_non_native_structured_representation = False
    for em in emitted:
        if em.type_action == "null_fill":
            resolved.append(em)
            continue
        actual_shape = _shape_for(actual_shapes, em.source_name)
        if (
            actual_shapes is not None
            and em.field.type in {UniversalType.ARRAY, UniversalType.OBJECT}
            and _structured_carrier(em.field, actual_shape) is not StructuredCarrier.NATIVE
        ):
            has_non_native_structured_representation = True
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
                mismatch = TypeDrift(
                    em.field.name,
                    declared,
                    None,
                    "unknown",
                    None,
                    "unknown",
                    requirement=requirement,
                    applied=apply_value_transforms,
                )
            elif (
                em.field.type is UniversalType.LIST
                and actual_shape.canonical_type is MountainashDtype.LIST
            ):
                mismatch = TypeDrift(
                    em.field.name,
                    declared,
                    actual_shape.canonical_type,
                    "unsafe",
                    None,
                    "representation",
                    _shape_detail(actual_shape),
                    requirement,
                    apply_value_transforms,
                )
            elif actual_shape.canonical_type != declared:
                safety = classify_cast(actual_shape.canonical_type, declared)
                numeric = {
                    MountainashDtype.I8, MountainashDtype.I16, MountainashDtype.I32, MountainashDtype.I64,
                    MountainashDtype.U8, MountainashDtype.U16, MountainashDtype.U32, MountainashDtype.U64,
                    MountainashDtype.FP32, MountainashDtype.FP64,
                }
                if safety is not CastSafety.SAFE or actual_shape.canonical_type not in numeric or declared not in numeric:
                    reason = "cast_safety" if safety is not CastSafety.SAFE else "representation"
                    mismatch = TypeDrift(
                        em.field.name,
                        declared,
                        actual_shape.canonical_type,
                        safety.value,
                        None,
                        reason,
                        _shape_detail(actual_shape),
                        requirement,
                        apply_value_transforms,
                    )
            elif _shape_diff(
                expected_shape,
                actual_shape,
                numeric_children=em.field.type is UniversalType.GEOPOINT,
            ):
                mismatch = TypeDrift(
                    em.field.name,
                    declared,
                    actual_shape.canonical_type,
                    "unsafe",
                    None,
                    "shape",
                    _shape_detail(actual_shape),
                    requirement,
                    apply_value_transforms,
                )
        elif declared is not None and actual_dtypes is not None:
            requirement = _shape_detail(_expected_shape(em.field)) or str(declared)
            if actual_dtype is None or isinstance(actual_dtype, SchemaTypeStatus):
                mismatch = TypeDrift(
                    em.field.name,
                    declared,
                    actual_dtype,
                    "unknown",
                    None,
                    "unknown",
                    None,
                    requirement,
                    apply_value_transforms,
                )
            elif classify_cast(actual_dtype, declared) is not CastSafety.SAFE:
                mismatch = TypeDrift(
                    em.field.name,
                    declared,
                    actual_dtype,
                    "unsafe",
                    None,
                    "cast_safety",
                    str(actual_dtype),
                    requirement,
                    apply_value_transforms,
                )
        if mismatch is None:
            resolved.append(em)
            continue
        reported_action = contract.data_type
        action = reported_action if apply_value_transforms else None
        applied = bool(
            apply_value_transforms
            and action in {"coerce", "discard_value", "discard_row"}
        )
        mismatch = dataclasses.replace(mismatch, action=reported_action, applied=applied)
        type_mismatches.append(mismatch)
        if action == "evolve":
            em = dataclasses.replace(em, type_action="evolve", effective_type=mismatch.actual)
        elif action in {"discard_value", "discard_row"}:
            em = dataclasses.replace(em, type_action=action)
        resolved.append(em)
    emitted = resolved

    if (
        apply_value_transforms
        and contract.data_type == "freeze"
        and (
            has_non_native_structured_representation
            or any(item.reason != "unknown" for item in type_mismatches)
        )
        and raise_on_freeze
    ):
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
    from mountainash.typespec.spec import FieldSpec
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
    if _structured_carrier(fld, shape) in {
        StructuredCarrier.JSON_TEXT,
        StructuredCarrier.OPAQUE,
    }:
        return FieldBuildResult(expr.name.alias(fld.name))
    typed_shapes = {
        UniversalType.LIST,
        UniversalType.ARRAY,
        UniversalType.OBJECT,
        UniversalType.GEOPOINT,
        UniversalType.GEOJSON,
    }
    unknown_lexical = (
        fld.type == UniversalType.LIST
        or (fld.type == UniversalType.GEOPOINT and fld.format == "default")
    )
    unknown_temporal = (
        fld.type is UniversalType.YEAR
        or (
            fld.type in {
                UniversalType.DATE,
                UniversalType.TIME,
                UniversalType.DATETIME,
            }
            and fld.format not in ("default", None)
        )
    )
    if (
        shape_known
        and canonical is None
        and (
            (fld.type in typed_shapes and not unknown_lexical)
            or unknown_temporal
        )
        and type_action != "evolve"
    ):
        raise UnresolvedSourceTypeError(
            field_name=fld.name,
            requirement="source shape for typed operation",
        )
    incompatible_source = False
    if shape_known:
        allowed = {
            UniversalType.LIST: {MountainashDtype.STRING},
            UniversalType.ARRAY: {MountainashDtype.LIST},
            UniversalType.OBJECT: {MountainashDtype.STRUCT},
            UniversalType.GEOPOINT: {
                MountainashDtype.STRING,
                MountainashDtype.LIST,
                MountainashDtype.STRUCT,
            },
            UniversalType.GEOJSON: {
                MountainashDtype.STRING,
                MountainashDtype.JSON,
                MountainashDtype.STRUCT,
            },
        }
        if canonical is not None and fld.type in allowed and canonical not in allowed[fld.type]:
            incompatible_source = True
        if canonical in {MountainashDtype.LIST, MountainashDtype.STRUCT} and fld.type not in {
            UniversalType.ARRAY,
            UniversalType.OBJECT,
            UniversalType.GEOPOINT,
            UniversalType.GEOJSON,
            UniversalType.ANY,
        }:
            incompatible_source = True
        temporal_canonicals = {
            MountainashDtype.DATE,
            MountainashDtype.TIME,
            MountainashDtype.TIMESTAMP,
            MountainashDtype.DURATION,
            MountainashDtype.XSD_DURATION,
            MountainashDtype.XSD_YEAR,
            MountainashDtype.XSD_YEARMONTH,
        }
        numeric = {
            MountainashDtype.I8, MountainashDtype.I16, MountainashDtype.I32, MountainashDtype.I64,
            MountainashDtype.U8, MountainashDtype.U16, MountainashDtype.U32, MountainashDtype.U64,
            MountainashDtype.FP32, MountainashDtype.FP64,
        }
        integer = numeric - {MountainashDtype.FP32, MountainashDtype.FP64}
        temporal_fields = {
            UniversalType.DATE: {MountainashDtype.DATE, MountainashDtype.STRING},
            UniversalType.TIME: {MountainashDtype.TIME, MountainashDtype.STRING},
            UniversalType.DATETIME: {MountainashDtype.TIMESTAMP, MountainashDtype.STRING},
            UniversalType.DURATION: {
                MountainashDtype.XSD_DURATION,
                MountainashDtype.STRING,
            },
            UniversalType.YEAR: {
                MountainashDtype.XSD_YEAR,
                MountainashDtype.STRING,
                *integer,
            },
            UniversalType.YEARMONTH: {
                MountainashDtype.XSD_YEARMONTH,
                MountainashDtype.STRING,
            },
        }
        if fld.type in temporal_fields and canonical is not None:
            if canonical not in temporal_fields[fld.type]:
                incompatible_source = True
        elif (
            fld.type is UniversalType.STRING
            and canonical in {
                MountainashDtype.DATE,
                MountainashDtype.TIME,
                MountainashDtype.TIMESTAMP,
            }
        ):
            # Native temporal values have a defined lexical cast to STRING.
            incompatible_source = False
        elif canonical in temporal_canonicals and fld.type is not UniversalType.ANY:
            # No other target has a defined reverse temporal representation.
            incompatible_source = True
        if canonical is MountainashDtype.JSON and fld.type not in {
            UniversalType.GEOJSON,
            UniversalType.ANY,
        }:
            incompatible_source = True
        if fld.type == UniversalType.GEOPOINT:
            numeric = {
                MountainashDtype.I8, MountainashDtype.I16, MountainashDtype.I32, MountainashDtype.I64,
                MountainashDtype.U8, MountainashDtype.U16, MountainashDtype.U32, MountainashDtype.U64,
                MountainashDtype.FP32, MountainashDtype.FP64,
            }
            if canonical is MountainashDtype.STRING:
                incompatible_source |= fld.format == "object"
            elif canonical is MountainashDtype.LIST:
                incompatible_source |= (
                    fld.format != "array"
                    or shape.item_shape is None
                    or shape.item_shape.canonical_type not in numeric
                )
            elif canonical is MountainashDtype.STRUCT:
                names = {name for name, _ in shape.struct_fields}
                incompatible_source |= (
                    fld.format != "object"
                    or names != {"lon", "lat"}
                    or any(child.canonical_type not in numeric for _, child in shape.struct_fields)
                )
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
    lexical = (
        not shape_known
        or canonical is None
        or canonical is MountainashDtype.STRING
        or (fld.type is UniversalType.GEOJSON and canonical is MountainashDtype.JSON)
    )
    sentinels = fld.missing_values if fld.missing_values is not None else schema_missing_values
    from mountainash.typespec._categorical import categorical_values
    sentinel_values = categorical_values(list(sentinels))
    if sentinel_values and (fld.type in scalar_types or canonical is MountainashDtype.STRING) and lexical:
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
    if incompatible_source:
        if type_action == "coerce":
            raise IncompatibleSourceTypeError(
                field_name=fld.name,
                source_detail=_shape_detail(shape) or "unknown",
                requirement=f"{fld.type.value} source",
            )
        if type_action in {"discard_value", "discard_row"}:
            output = ma.lit(None)
            typed_value = None

            def _placeholder(inner):
                if inner.object_fields:
                    return {
                        child.name: _placeholder(child)
                        for child in inner.object_fields
                    }
                return None

            if fld.type in {UniversalType.LIST, UniversalType.ARRAY}:
                if fld.item_object_fields:
                    typed_value = ma.lit([]).list.cast_items(
                        item_object_fields=tuple(fld.item_object_fields),
                        field_name=fld.name,
                        failure_behavior=CaseFailureBehaviour.NULL,
                    )
                elif fld.item_type:
                    typed_value = ma.lit([]).list.cast_items(
                        item_type=fld.item_type,
                        field_name=fld.name,
                        failure_behavior=CaseFailureBehaviour.NULL,
                    )
                else:
                    typed_value = ma.lit([])
            elif fld.type == UniversalType.GEOPOINT and fld.format == "array":
                typed_value = ma.lit([]).list.cast_items(
                    item_type="number",
                    field_name=fld.name,
                    failure_behavior=CaseFailureBehaviour.NULL,
                )
            elif fld.type == UniversalType.OBJECT and fld.object_fields:
                typed_value = ma.lit(_placeholder(fld)).struct.cast(
                    fields=tuple(fld.object_fields),
                    field_name=fld.name,
                    failure_behavior=CaseFailureBehaviour.NULL,
                )
            elif fld.type == UniversalType.GEOPOINT and fld.format == "object":
                coordinate_fields = (
                    FieldSpec(name="lon", type=UniversalType.NUMBER),
                    FieldSpec(name="lat", type=UniversalType.NUMBER),
                )
                typed_value = ma.lit({"lon": None, "lat": None}).struct.cast(
                    fields=coordinate_fields,
                    field_name=fld.name,
                    failure_behavior=CaseFailureBehaviour.NULL,
                )
            if typed_value is not None:
                output = ma.when(ma.lit(False)).then(typed_value).otherwise(output)
            elif isinstance(declared_type, MountainashDtype):
                output = output.cast(declared_type)
            discard = None
            if type_action == "discard_row":
                discard = ~(post_missing.is_not_null() & output.is_null())
            return FieldBuildResult(output.name.alias(fld.name), discard)
    failure = CaseFailureBehaviour.THROW if type_action == "coerce" else CaseFailureBehaviour.NULL
    residue: list[MaterializationResidueCheck] = []
    if type_action == "evolve":
        return FieldBuildResult(transform_input.name.alias(fld.name))
    if fld.type == UniversalType.LIST and lexical:
        expr = expr.str.parse_list(
            item_type=fld.item_type or "string",
            delimiter=fld.delimiter or ",",
            field_name=fld.name,
            failure_behavior=failure,
        )
    elif (
        fld.type == UniversalType.ARRAY
        and canonical is MountainashDtype.LIST
        and (fld.item_object_fields or fld.item_type)
        and not lexical
    ):
        if fld.item_object_fields:
            expr = expr.list.cast_items(
                item_object_fields=tuple(fld.item_object_fields),
                field_name=fld.name,
                failure_behavior=failure,
            )
        else:
            expr = expr.list.cast_items(
                item_type=fld.item_type,
                field_name=fld.name,
                failure_behavior=failure,
            )
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
    elif fld.type in {UniversalType.ARRAY, UniversalType.OBJECT}:
        # Plain native containers have no child schema to apply.  The source
        # already has the required physical representation; preserve it.
        pass
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
        representation = "lexical" if lexical else "native"
        expr = expr.geo.parse_geopoint(
            format=fmt,
            source_representation=representation,
            field_name=fld.name,
            failure_behavior=failure,
        )
    elif fld.type == UniversalType.GEOJSON and canonical is MountainashDtype.STRUCT and not lexical:
        fmt = fld.format if fld.format in {"default", "topojson"} else "default"
        expr = expr.geo.serialize_geojson(format=fmt, field_name=fld.name)
    elif fld.type == UniversalType.GEOJSON and lexical:
        fmt = fld.format if fld.format in {"default", "topojson"} else "default"
        expr = expr.geo.parse_geojson(format=fmt, field_name=fld.name, failure_behavior=failure)
    elif fld.type == UniversalType.YEAR and canonical in {
        MountainashDtype.I8, MountainashDtype.I16, MountainashDtype.I32, MountainashDtype.I64,
        MountainashDtype.U8, MountainashDtype.U16, MountainashDtype.U32, MountainashDtype.U64,
    }:
        text = expr.cast(MountainashDtype.STRING)
        absolute = text.str.regexp_replace(r"^-", "").str.lpad(4, "0")
        expr = ma.when(text.str.starts_with("-")).then(
            ma.lit("-").str.concat(absolute)
        ).otherwise(absolute)
        expr = expr.dt.parse_xsd_partial_date(
            kind="year",
            field_name=fld.name,
            failure_behavior=failure,
        )
        if type_action == "coerce":
            residue.append(MaterializationResidueCheck(expr.node.function_key, fld.name, transform_input.is_not_null() & expr.is_null()))
    elif fld.type == UniversalType.DURATION and lexical:
        expr = expr.dt.parse_xsd_duration(field_name=fld.name, failure_behavior=failure)
        if type_action == "coerce":
            residue.append(MaterializationResidueCheck(expr.node.function_key, fld.name, transform_input.is_not_null() & expr.is_null()))
    elif fld.type in {UniversalType.YEAR, UniversalType.YEARMONTH} and lexical:
        expr = expr.dt.parse_xsd_partial_date(kind=fld.type.value, field_name=fld.name, failure_behavior=failure)
        if type_action == "coerce":
            residue.append(MaterializationResidueCheck(expr.node.function_key, fld.name, transform_input.is_not_null() & expr.is_null()))
    elif fld.type in {UniversalType.DATE, UniversalType.TIME} and fld.format == "any" and lexical:
        expr = expr.dt.parse_temporal_any(fld.type.value, field_name=fld.name, failure_behavior=failure)
    elif fld.type == UniversalType.DATETIME and fld.format == "any" and lexical:
        expr = expr.dt.parse_temporal_any("datetime", field_name=fld.name, failure_behavior=failure)
    elif fld.type in {UniversalType.DATE, UniversalType.DATETIME, UniversalType.TIME} and fld.format not in ("default", None, "any") and lexical:
        method = {UniversalType.DATE: expr.str.to_date, UniversalType.DATETIME: expr.str.to_datetime, UniversalType.TIME: expr.str.to_time}[fld.type]
        expr = method(fld.format, field_name=fld.name, failure_behavior=failure)
    elif fld.type == UniversalType.DATETIME and fld.format == "default" and lexical:
        expr = expr.dt.parse_default(field_name=fld.name, failure_behavior=failure)
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
    resolved_contract = contract or resolve_contract(spec.fields_match)
    output_contract = resolve_conform_output(
        spec,
        available_columns,
        actual_dtypes=actual_dtypes,
        actual_shapes=actual_shapes,
        contract=resolved_contract,
        node_identity=node_identity,
        key_fks=key_fks,
        key_resource_name=key_resource_name,
        schema_of=schema_of,
        apply_value_transforms=apply_value_transforms,
    )
    structured_field_plans = _build_structured_field_plans(
        output_contract.emitted,
        schema_missing_values=schema_missing_values,
        data_type_action=resolved_contract.data_type,
        apply_value_transforms=apply_value_transforms,
        declaration_fingerprint=declaration_fingerprint(freeze_typespec(spec)),
        node_identity=node_identity,
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
        structured_field_plans,
    )
