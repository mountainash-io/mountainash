from __future__ import annotations

import dis
import hashlib
import importlib
import inspect
import json
import pkgutil
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, fields as dataclass_fields
from pathlib import Path
from types import CodeType, ModuleType
from typing import Any, get_args, get_origin


_PROFILE_COMMIT = "6a201af8ed2eacbb3a2440e82e4c55d5807f9c09"
_PROFILE_NAMES = ("datapackage.json", "dataresource.json", "tabledialect.json", "tableschema.json")
_ROOT_KINDS = frozenset({"package", "resource", "dialect", "schema"})
_SCHEMA_ANNOTATION_KEYS = frozenset(
    {
        "$schema",
        "$id",
        "$ref",
        "$defs",
        "definitions",
        "$comment",
        "title",
        "description",
        "default",
        "examples",
        "readOnly",
        "writeOnly",
        "deprecated",
        "type",
        "required",
        "additionalProperties",
        "additionalItems",
        "patternProperties",
        "propertyNames",
        "minProperties",
        "maxProperties",
        "minItems",
        "maxItems",
        "uniqueItems",
        "contains",
        "minLength",
        "maxLength",
        "pattern",
        "format",
        "multipleOf",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "const",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "if",
        "then",
        "else",
        "dependentRequired",
        "dependentSchemas",
        "unevaluatedItems",
        "unevaluatedProperties",
        "contentEncoding",
        "contentMediaType",
    }
)


@dataclass(frozen=True)
class ProfileCapability:
    capability_id: str
    source_pointers: tuple[str, ...]
    branch_predicates: tuple[str, ...]
    absent_from_profile: bool = False


@dataclass(frozen=True)
class CoverageDisposition:
    status: str
    reason: str | None = None
    since: str | None = None
    owner_unit: str | None = None
    acceptance_reference: str | None = None
    discrepancy_id: str | None = None
    decision_reference: str | None = None
    review_date: str | None = None


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON document at {path} must be an object")
    return value


def load_profile_set(profile_dir: Path) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for name in _PROFILE_NAMES:
        path = profile_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"missing profile snapshot: {name}")
        profiles[name] = load_json(path)
    return profiles


def verify_snapshot_digests(profile_dir: Path) -> list[str]:
    try:
        sources = load_json(profile_dir / "profile-sources.json")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        return [f"profile-sources.json: {exc}"]

    profiles = sources.get("profiles")
    if not isinstance(profiles, dict):
        return ["profile-sources.json: profiles must be an object"]

    errors: list[str] = []
    expected_names = set(_PROFILE_NAMES)
    actual_names = set(profiles)
    for name in sorted(expected_names - actual_names):
        errors.append(f"{name}: provenance record missing")
    for name in sorted(actual_names - expected_names):
        errors.append(f"{name}: unexpected provenance record")
    for name in sorted(actual_names & expected_names):
        record = profiles[name]
        if not isinstance(record, dict):
            errors.append(f"{name}: provenance record is not an object")
            continue
        expected = record.get("sha256")
        path = profile_dir / name
        if not path.is_file():
            errors.append(f"{name}: snapshot missing")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{name}: snapshot digest mismatch")
    return errors


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _json_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _resolve_local_ref(root: Mapping[str, Any], ref: str) -> tuple[Mapping[str, Any] | None, str | None]:
    if not ref.startswith("#/"):
        return None, None
    current: Any = root
    pointer = "#"
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, Mapping) or part not in current:
            return None, None
        current = current[part]
        pointer += "/" + _escape_pointer(part)
    return current if isinstance(current, Mapping) else None, pointer


def extract_profile_capabilities(
    profile: Mapping[str, Any], *, root_kind: str
) -> dict[str, ProfileCapability]:
    if root_kind not in _ROOT_KINDS:
        raise ValueError(f"unknown profile root kind: {root_kind}")

    pointers: dict[str, list[str]] = defaultdict(list)
    predicates: dict[str, list[str]] = defaultdict(list)
    seen_refs: set[tuple[str, str, tuple[str, ...]]] = set()

    def add(capability_id: str, pointer: str, branch: tuple[str, ...]) -> None:
        if not capability_id or capability_id.endswith(":"):
            return
        pointers[capability_id].append(pointer)
        predicates[capability_id].extend(branch)

    def visit(
        node: Any,
        path: str,
        pointer: str,
        branch: tuple[str, ...] = (),
    ) -> None:
        if not isinstance(node, Mapping):
            return

        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/"):
            ref_key = (ref, path, branch)
            if ref_key not in seen_refs:
                seen_refs.add(ref_key)
                target, target_pointer = _resolve_local_ref(profile, ref)
                if target is not None and target_pointer is not None:
                    visit(target, path, target_pointer, branch)
        properties = node.get("properties")
        if isinstance(properties, Mapping):
            for name, child in properties.items():
                if not isinstance(name, str):
                    continue
                child_path = f"{path}.{name}" if path else name
                child_pointer = f"{pointer}/properties/{_escape_pointer(name)}"
                shape_child = child
                if isinstance(child, Mapping):
                    child_ref = child.get("$ref")
                    if isinstance(child_ref, str) and child_ref.startswith("#/"):
                        resolved, _resolved_pointer = _resolve_local_ref(profile, child_ref)
                        if resolved is not None:
                            shape_child = resolved
                is_array = isinstance(shape_child, Mapping) and (
                    shape_child.get("type") == "array" or "items" in shape_child
                )
                capability_id = f"{root_kind}:{child_path}{'[]' if is_array else ''}"
                add(capability_id, child_pointer, branch)
                if isinstance(shape_child, Mapping):
                    enum_values = shape_child.get("enum")
                    if isinstance(enum_values, list):
                        for enum_value in enum_values:
                            add(
                                f"{capability_id}=value:{_json_value(enum_value)}",
                                child_pointer,
                                branch,
                            )
                visit(child, child_path + ("[]" if is_array else ""), child_pointer, branch)

        items = node.get("items")
        if isinstance(items, Mapping):
            visit(items, path, f"{pointer}/items", branch)

        for keyword in ("oneOf", "anyOf", "allOf"):
            branches = node.get(keyword)
            if isinstance(branches, list):
                for index, child in enumerate(branches):
                    branch_pointer = f"{pointer}/{keyword}/{index}"
                    branch_path = path
                    if isinstance(child, Mapping) and (
                        child.get("type") == "array" or "items" in child
                    ) and path:
                        branch_path = path + "[]"
                        add(f"{root_kind}:{branch_path}", branch_pointer, branch + (branch_pointer,))
                    visit(child, branch_path, branch_pointer, branch + (branch_pointer,))

    visit(profile, "", "")
    return {
        capability_id: ProfileCapability(
            capability_id=capability_id,
            source_pointers=tuple(source_pointers),
            branch_predicates=tuple(branch_predicates),
        )
        for capability_id, source_pointers in sorted(pointers.items())
        for branch_predicates in [predicates[capability_id]]
    }


def _merge_capability(
    target: dict[str, ProfileCapability], capability: ProfileCapability, capability_id: str
) -> None:
    existing = target.get(capability_id)
    if existing is None:
        target[capability_id] = ProfileCapability(
            capability_id=capability_id,
            source_pointers=capability.source_pointers,
            branch_predicates=capability.branch_predicates,
            absent_from_profile=capability.absent_from_profile,
        )
    else:
        target[capability_id] = ProfileCapability(
            capability_id=capability_id,
            source_pointers=existing.source_pointers + capability.source_pointers,
            branch_predicates=existing.branch_predicates + capability.branch_predicates,
            absent_from_profile=existing.absent_from_profile or capability.absent_from_profile,
        )


def _rebase_embedded_capability(capability: ProfileCapability) -> str | None:
    capability_id = capability.capability_id
    if capability_id.startswith("package:resources[]"):
        suffix = capability_id[len("package:resources[]") :]
        if suffix == "":
            return None
        if suffix.startswith(".schema"):
            suffix = suffix[len(".schema") :].lstrip(".")
            return None if not suffix else "schema:" + suffix
        if suffix.startswith(".dialect"):
            suffix = suffix[len(".dialect") :].lstrip(".")
            return None if not suffix else "dialect:" + suffix
        return "resource:" + suffix.lstrip(".")
    for prefix, root in (("resource:schema", "schema:"), ("resource:dialect", "dialect:")):
        if capability_id == prefix:
            return None
        if capability_id.startswith(prefix + "."):
            return root + capability_id[len(prefix) + 1 :]
    return capability_id


def load_official_profile_capabilities(profile_dir: Path) -> dict[str, ProfileCapability]:
    profiles = load_profile_set(profile_dir)
    return _load_official_profile_capabilities_from_mapping(profiles)


def _load_official_profile_capabilities_from_mapping(
    profiles: Mapping[str, Mapping[str, Any]],
) -> dict[str, ProfileCapability]:
    root_for_name = {
        "datapackage.json": "package",
        "dataresource.json": "resource",
        "tabledialect.json": "dialect",
        "tableschema.json": "schema",
    }
    capabilities: dict[str, ProfileCapability] = {}
    for name, root_kind in root_for_name.items():
        profile = profiles.get(name)
        if profile is None:
            continue
        extracted = extract_profile_capabilities(profile, root_kind=root_kind)
        for capability_id, capability in extracted.items():
            rebased = _rebase_embedded_capability(capability)
            if rebased is None:
                continue
            _merge_capability(capabilities, capability, rebased)
    return dict(sorted(capabilities.items()))


def _array_suffixes(annotation: Any) -> set[str]:
    origin = get_origin(annotation)
    if origin in (list, tuple, set, frozenset):
        return {"[]"}
    if origin is not None:
        suffixes: set[str] = set()
        for argument in get_args(annotation):
            if argument is type(None):
                continue
            suffixes.update(_array_suffixes(argument))
        return suffixes or {""}
    return {""}


def _is_array_annotation(annotation: Any) -> bool:
    return "[]" in _array_suffixes(annotation)


def _camel_case(name: str) -> str:
    if name == "schema_url":
        return "$schema"
    parts = name.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])




_MODEL_ROOTS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("mountainash.typespec.datapackage", "DataPackage", ("package:",)),
    ("mountainash.typespec.datapackage", "DataResource", ("resource:",)),
    ("mountainash.typespec.datapackage", "TableDialect", ("dialect:",)),
    ("mountainash.typespec.spec", "TypeSpec", ("schema:",)),
    ("mountainash.typespec.spec", "FieldSpec", ("schema:fields[].",)),
    ("mountainash.typespec.spec", "FieldConstraints", ("schema:fields[].constraints.",)),
    (
        "mountainash.typespec.frictionless_codec",
        "_ContributorDescriptor",
        ("package:contributors[].",),
    ),
    (
        "mountainash.typespec.frictionless_codec",
        "_LicenseDescriptor",
        ("package:licenses[].", "resource:licenses[]."),
    ),
    (
        "mountainash.typespec.frictionless_codec",
        "_SourceDescriptor",
        ("package:sources[].", "resource:sources[]."),
    ),
)


def _model_field_names(cls: type[Any]) -> list[tuple[str, str, Any]]:
    model_fields = getattr(cls, "model_fields", None)
    if model_fields is not None:
        return [
            (name, str(getattr(field, "alias", None) or name), getattr(field, "annotation", Any))
            for name, field in model_fields.items()
            if name != "extras"
        ]
    hints = __import__("typing").get_type_hints(cls)
    return [
        (field.name, _camel_case(field.name), hints.get(field.name, field.type))
        for field in dataclass_fields(cls)
    ]
def _field_capability_paths(
    class_name: str,
    roots: tuple[str, ...],
    field_name: str,
    alias: str,
    annotation: Any,
) -> set[str]:
    suffixes = _array_suffixes(annotation)
    extension_name: str | None = None
    extension_only = False
    if class_name == "TypeSpec" and field_name == "contract":
        extension_name = "contract"
        extension_only = True
    elif class_name == "TypeSpec" and field_name == "fields_match":
        extension_name = "fields_match"
    elif class_name == "FieldSpec" and field_name in {
        "backend_type",
        "custom_cast",
        "null_fill",
        "object_fields",
        "rename_from",
    }:
        extension_name = field_name
        extension_only = True
    elif class_name == "FieldConstraints" and field_name == "enum_weights":
        extension_name = "enum_weights"
        extension_only = True

    paths: set[str] = set()
    if not extension_only:
        for root in roots:
            paths.update(f"{root}{alias}{suffix}" for suffix in suffixes)
    if extension_name is not None:
        for root in roots:
            paths.update(
                f"x-mountainash:{root}{extension_name}{suffix}" for suffix in suffixes
            )
    return paths


def _model_capabilities() -> set[str]:
    capabilities: set[str] = set()
    for module_name, class_name, roots in _MODEL_ROOTS:
        cls = getattr(importlib.import_module(module_name), class_name)
        for field_name, alias, annotation in _model_field_names(cls):
            if alias == "extras":
                continue
            capabilities.update(
                _field_capability_paths(
                    class_name, roots, field_name, alias, annotation
                )
            )
    # A resource's embedded descriptor boundaries are represented by the
    # standalone schema and dialect roots in the official profile set.
    capabilities.discard("resource:schema")
    capabilities.discard("resource:dialect")
    return capabilities


def _code_objects(code: CodeType) -> list[CodeType]:
    found = [code]
    for constant in code.co_consts:
        if isinstance(constant, CodeType):
            found.extend(_code_objects(constant))
    return found


def _code_field_names(module: ModuleType) -> set[str]:
    names: set[str] = set()
    for value in vars(module).values():
        if inspect.isfunction(value) and value.__module__ == module.__name__:
            for code in _code_objects(value.__code__):
                names.update(
                    instruction.argval
                    for instruction in dis.get_instructions(code)
                    if instruction.opname in {"LOAD_ATTR", "LOAD_METHOD"}
                    and isinstance(instruction.argval, str)
                )
    return names


def _dataclass_internal_fields() -> set[str]:
    classes = []
    for module_name, class_name in (
        ("mountainash.typespec.spec", "TypeSpec"),
        ("mountainash.typespec.spec", "FieldSpec"),
        ("mountainash.typespec.spec", "FieldConstraints"),
    ):
        cls = getattr(importlib.import_module(module_name), class_name)
        classes.extend(field.name for field in dataclass_fields(cls))
    return set(classes)


def _code_field_capabilities(field_name: str) -> set[str]:
    if field_name not in _dataclass_internal_fields():
        return set()
    for module_name, class_name, roots in _MODEL_ROOTS:
        cls = getattr(importlib.import_module(module_name), class_name)
        if not hasattr(cls, "__dataclass_fields__"):
            continue
        if field_name not in cls.__dataclass_fields__:
            continue
        alias = _camel_case(field_name)
        annotation = __import__("typing").get_type_hints(cls).get(
            field_name, cls.__dataclass_fields__[field_name].type
        )
        return _field_capability_paths(
            class_name, roots, field_name, alias, annotation
        )
    return set()


def discover_code_field_capabilities(module: ModuleType) -> set[str]:
    capabilities: set[str] = set()
    for field_name in _code_field_names(module):
        capabilities.update(_code_field_capabilities(field_name))
    return capabilities




def discover_validation_rule_capabilities() -> set[str]:
    validation = importlib.import_module("mountainash.validation")
    module_names = [validation.__name__]
    if hasattr(validation, "__path__"):
        module_names.extend(
            module_info.name
            for module_info in pkgutil.walk_packages(validation.__path__, validation.__name__ + ".")
        )
    capabilities: set[str] = set()
    for module_name in module_names:
        module = importlib.import_module(module_name)
        for value in vars(module).values():
            if (
                inspect.isclass(value)
                and value.__module__ == module.__name__
                and value.__name__.endswith("Rule")
            ):
                name = value.__name__[:-4]
                kebab = "".join(
                    ("-" if char.isupper() and index else "") + char.lower()
                    for index, char in enumerate(name)
                )
                capabilities.add(f"x-mountainash:validation.rule.{kebab}")
    return capabilities


def discover_dialect_reader_capabilities() -> set[str]:
    reader = importlib.import_module(
        "mountainash.relations.backends.relation_systems.resource_files"
    )
    dialect = getattr(importlib.import_module("mountainash.typespec.datapackage"), "TableDialect")
    model_fields = getattr(dialect, "model_fields", {})
    names: set[str] = set()
    for set_name in (
        "_MAPPABLE_DIALECT_FIELDS",
        "_NATIVE_SAFE_DIALECT_FIELDS",
        "_IGNORED_DIALECT_FIELDS",
    ):
        for internal_name in getattr(reader, set_name):
            field = model_fields.get(internal_name)
            if field is None:
                raise ValueError(
                    f"{set_name}: reader field {internal_name!r} has no TableDialect field"
                )
            alias = str(getattr(field, "alias", None) or internal_name)
            names.add(f"dialect:{alias}")
    return names


def discover_mountainash_capabilities() -> set[str]:
    expressions = importlib.import_module("mountainash.conform.expressions")
    from mountainash.typespec.universal_types import UniversalType

    universal_type_capabilities = {
        f"schema:fields[].type=value:{_json_value(value.value)}"
        for value in UniversalType
    }
    return (
        _model_capabilities()
        | universal_type_capabilities
        | discover_code_field_capabilities(expressions)
        | discover_validation_rule_capabilities()
        | discover_dialect_reader_capabilities()
    )


def _disposition_errors(capability: str, disposition: Any, dimension: str) -> list[str]:
    if not isinstance(disposition, Mapping):
        return [f"{capability}: {dimension} disposition must be an object"]
    status = disposition.get("status")
    if status not in {"implemented", "deferred", "upstream_exception", "local_policy"}:
        return [f"{capability}: {dimension} status {status!r} is invalid"]
    required: tuple[str, ...]
    if status == "deferred":
        required = ("reason", "since", "owner_unit", "acceptance_reference")
    elif status == "upstream_exception":
        required = ("reason", "discrepancy_id", "review_date")
    elif status == "local_policy":
        required = ("reason", "decision_reference", "review_date")
    else:
        required = ()
    return [
        f"{capability}: {dimension} disposition missing {key}"
        for key in required
        if not disposition.get(key)
    ]


def validate_profile_coverage(
    *,
    profiles: Mapping[str, Mapping[str, Any]],
    manifest: Mapping[str, Any],
    discovered_capabilities: set[str] | None = None,
) -> list[str]:
    official = _load_official_profile_capabilities_from_mapping(profiles)
    discovered = (
        discover_mountainash_capabilities()
        if discovered_capabilities is None
        else set(discovered_capabilities)
    )
    errors: list[tuple[str, str]] = []
    expected_profiles = set(_PROFILE_NAMES)
    for name in sorted(set(profiles) - expected_profiles):
        errors.append((name, f"{name}: orphan snapshot profile"))
    for name in sorted(expected_profiles - set(profiles)):
        errors.append((name, f"{name}: missing snapshot profile"))
    rows = manifest.get("rows", [])
    if not isinstance(rows, list):
        return [error for _capability, error in sorted(errors)] + ["manifest: rows must be a list"]
    row_map: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append((f"manifest-row-{index}", f"manifest row {index}: row must be an object"))
            continue
        capability = row.get("capability")
        if not isinstance(capability, str):
            errors.append((f"manifest-row-{index}", f"manifest row {index}: capability is required"))
            continue
        if capability in row_map:
            errors.append((capability, f"{capability}: duplicate manifest row"))
        row_map[capability] = row
        for dimension in ("storage", "typed", "execution"):
            errors.extend(
                (capability, error)
                for error in _disposition_errors(capability, row.get(dimension), dimension)
            )

    prose = manifest.get("prose_capabilities", [])
    prose_ids = {
        item.get("capability")
        for item in prose
        if isinstance(item, Mapping) and isinstance(item.get("capability"), str)
    }
    for item in prose:
        if not isinstance(item, Mapping):
            continue
        capability = item.get("capability")
        if not isinstance(capability, str):
            continue
        if not item.get("source_url") or not item.get("section_anchor") or not item.get("quotation"):
            errors.append((capability, f"{capability}: prose evidence is incomplete"))
    for capability in sorted(set(official) & prose_ids):
        if any(
            isinstance(item, Mapping)
            and item.get("capability") == capability
            and item.get("absent_from_profile") is True
            for item in prose
        ):
            errors.append(
                (
                    capability,
                    f"{capability}: absent_from_profile prose overlaps official capability",
                )
            )

    for capability in sorted(prose_ids):
        if capability not in row_map:
            errors.append((capability, f"{capability}: prose capability lacks manifest row"))
    known_ids = set(official) | discovered | prose_ids
    for capability in sorted(official):
        if capability not in row_map:
            errors.append((capability, f"{capability}: missing manifest row"))
    for capability, row in row_map.items():
        if capability not in known_ids:
            errors.append((capability, f"{capability}: orphan manifest row"))
        if row.get("absent_from_profile") is True and capability not in prose_ids:
            errors.append((capability, f"{capability}: absent_from_profile row lacks prose evidence"))
        if capability in prose_ids and row.get("absent_from_profile") is not True:
            errors.append((capability, f"{capability}: prose capability must be absent_from_profile"))
    for capability in sorted(discovered):
        if capability not in row_map:
            errors.append((capability, f"{capability}: discovered capability lacks manifest row"))

    source_commit = manifest.get("source_commit")
    if source_commit != _PROFILE_COMMIT:
        errors.append(("manifest", "source_commit: manifest commit does not match pinned profile commit"))
    for exception in manifest.get("upstream_exceptions", []):
        if not isinstance(exception, Mapping):
            errors.append(("manifest", "upstream exception: record must be an object"))
            continue
        evidence_commit = exception.get("evidence_commit")
        if evidence_commit != source_commit:
            affected = exception.get("affected_path") or exception.get("discrepancy_id") or "unknown"
            errors.append((str(affected), f"{affected}: evidence_commit does not match source_commit"))

    return [error for _capability, error in sorted(errors, key=lambda item: (item[0], item[1]))]
