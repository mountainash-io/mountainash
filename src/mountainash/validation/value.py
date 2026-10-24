"""Logical-value primitives shared by every backend-neutral validation rule.

This module owns value-only concerns: immutable rule registry declarations,
semantic-string parsing, canonical equality, and deterministic rendering.  It
intentionally does not materialize relations or create backend expressions.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
import json
import math
import re
from types import MappingProxyType
from typing import Any, Literal

from mountainash.core.dtypes import SchemaTypeStatus
from mountainash.typespec.temporal import parse_xsd_duration, parse_xsd_partial_date
from mountainash.validation.checks import ValueValidatorKey
from mountainash.validation.errors import CheckDeclarationError


@dataclass(frozen=True)
class DurationValue:
    """An XML Schema duration preserving calendar months and decimal seconds."""

    months: int
    seconds: Decimal


@dataclass(frozen=True)
class PartialDateValue:
    """A gYear or gYearMonth without Python ``date``'s year limits."""

    year: int
    month: int | None
    timezone_minutes: int | None


class _InvalidValue:
    """Private identity sentinel for one failed intrinsic value parse."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "INVALID_VALUE"


INVALID_VALUE = _InvalidValue()

_DURATION_PARTS = re.compile(
    r"^(?P<sign>-)?P"
    r"(?:(?P<years>[0-9]+)Y)?(?:(?P<months>[0-9]+)M)?(?:(?P<days>[0-9]+)D)?"
    r"(?:T(?:(?P<hours>[0-9]+)H)?(?:(?P<minutes>[0-9]+)M)?"
    r"(?:(?P<seconds>(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))S)?)?$"
)
_PARTIAL_VALUE = re.compile(
    r"^(?P<year>-?(?:0[0-9]{3}|[1-9][0-9]{3,}))"
    r"(?:-(?P<month>0[1-9]|1[0-2]))?"
    r"(?P<timezone>Z|[+-](?:0[0-9]|1[0-4]):[0-5][0-9])?$"
)


def parse_duration_value(value: Any) -> DurationValue | _InvalidValue:
    """Parse an XSD duration into its non-interchangeable month/time parts."""
    try:
        parse_xsd_duration(value)
    except (TypeError, ValueError):
        return INVALID_VALUE
    match = _DURATION_PARTS.fullmatch(value)
    if match is None:  # defensive: retains one failure shape if grammar changes
        return INVALID_VALUE
    groups = match.groupdict()
    sign = -1 if groups["sign"] else 1
    months = int(groups["years"] or 0) * 12 + int(groups["months"] or 0)
    seconds = (
        Decimal(int(groups["days"] or 0)) * Decimal(86_400)
        + Decimal(int(groups["hours"] or 0)) * Decimal(3_600)
        + Decimal(int(groups["minutes"] or 0)) * Decimal(60)
        + Decimal(groups["seconds"] or "0")
    )
    return DurationValue(months=sign * months, seconds=sign * seconds)


def parse_partial_date_value(
    value: Any,
    *,
    kind: Literal["year", "yearmonth"],
) -> PartialDateValue | _InvalidValue:
    """Parse a gYear/gYearMonth, including arbitrary years and timezone offsets."""
    try:
        parse_xsd_partial_date(value, kind=kind)
    except (TypeError, ValueError):
        return INVALID_VALUE
    match = _PARTIAL_VALUE.fullmatch(value)
    if match is None:
        return INVALID_VALUE
    groups = match.groupdict()
    month = int(groups["month"]) if groups["month"] else None
    if (kind == "year") != (month is None):
        return INVALID_VALUE
    timezone = groups["timezone"]
    if timezone is None:
        timezone_minutes = None
    elif timezone == "Z":
        timezone_minutes = 0
    else:
        offset = int(timezone[1:3]) * 60 + int(timezone[4:6])
        timezone_minutes = offset if timezone[0] == "+" else -offset
    return PartialDateValue(
        year=int(groups["year"]), month=month, timezone_minutes=timezone_minutes
    )


def parse_logical_value(value: Any, *, type_name: str) -> Any:
    """Parse Unit C semantic-string values without touching backend objects.

    ``array``/``object`` route through the shared structured decoder
    (``mountainash.conform.structured_transport``) -- the fallback for a
    declared structured field with no transport plan (spec Task 6 step 5).
    A transport-plan-covered field's value already arrives pre-decoded via
    ``PreparedValidationInput.logical_snapshot``; this function is never
    called a second time for it.
    """
    if value is None:
        return None
    if type_name == "duration":
        return parse_duration_value(value)
    if type_name == "year":
        return parse_partial_date_value(value, kind="year")
    if type_name == "yearmonth":
        return parse_partial_date_value(value, kind="yearmonth")
    if type_name == "array":
        from mountainash.conform.structured_transport import (
            INVALID_STRUCTURED_VALUE,
            StructuredRoot,
            decode_structured_value,
        )

        decoded = decode_structured_value(value, expected_root=StructuredRoot.ARRAY)
        return INVALID_VALUE if decoded is INVALID_STRUCTURED_VALUE else decoded
    if type_name == "object":
        from mountainash.conform.structured_transport import (
            INVALID_STRUCTURED_VALUE,
            StructuredRoot,
            decode_structured_value,
        )

        decoded = decode_structured_value(value, expected_root=StructuredRoot.OBJECT)
        return INVALID_VALUE if decoded is INVALID_STRUCTURED_VALUE else decoded
    return value


def canonical_value_key(value: Any) -> tuple[Any, ...]:
    """Encode logical equality without Python's bool/int or mutable-value traps."""
    if value is INVALID_VALUE:
        return ("invalid",)
    if value is None:
        return ("null",)
    if type(value) is bool:  # noqa: E721 — bool never equals a number
        return ("bool", value)
    if isinstance(value, Decimal):
        if value.is_nan():
            return ("nan",)
        if value.is_infinite():
            return ("infinity", 1 if value > 0 else -1)
        return ("number", value.normalize())
    if type(value) is int:  # noqa: E721 — bool never equals a number
        return ("number", Decimal(value))
    if type(value) is float:  # noqa: E721 — use float's round-trip decimal
        if math.isnan(value):
            return ("nan",)
        if math.isinf(value):
            return ("infinity", 1 if value > 0 else -1)
        return ("number", Decimal(str(value)).normalize())
    if isinstance(value, str):
        return ("string", value)
    if isinstance(value, bytes):
        return ("bytes", value)
    if isinstance(value, DurationValue):
        return ("duration", value.months, canonical_value_key(value.seconds))
    if isinstance(value, PartialDateValue):
        return ("partial_date", value.year, value.month, value.timezone_minutes)
    if isinstance(value, Mapping):
        return (
            "mapping",
            tuple(
                sorted(
                    (canonical_value_key(key), canonical_value_key(item))
                    for key, item in value.items()
                )
            ),
        )
    if isinstance(value, (list, tuple)):
        return ("sequence", tuple(canonical_value_key(item) for item in value))
    if isinstance(value, (set, frozenset)):
        return ("set", tuple(sorted(canonical_value_key(item) for item in value)))
    return ("object", type(value).__module__, type(value).__qualname__, repr(value))


def _render_json_value(value: Any) -> Any:
    if value is INVALID_VALUE:
        return {"$invalid": True}
    if value is None or type(value) is bool or isinstance(value, (str, int, float)):  # noqa: E721 — preserve JSON bool identity
        return value
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, bytes):
        return {"$bytes": value.hex()}
    if isinstance(value, DurationValue):
        return {"$duration": {"months": value.months, "seconds": str(value.seconds)}}
    if isinstance(value, PartialDateValue):
        return {
            "$partial_date": {
                "year": value.year,
                "month": value.month,
                "timezone_minutes": value.timezone_minutes,
            }
        }
    if isinstance(value, Mapping):
        return {
            str(key): _render_json_value(item)
            for key, item in sorted(value.items(), key=lambda pair: canonical_value_key(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_render_json_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return {
            "$set": [
                _render_json_value(item)
                for item in sorted(value, key=canonical_value_key)
            ]
        }
    return {"$object": f"{type(value).__module__}.{type(value).__qualname__}", "repr": repr(value)}


def render_value(value: Any) -> str:
    """Render a logical value as canonical JSON for deterministic diagnostics."""
    return json.dumps(_render_json_value(value), separators=(",", ":"), sort_keys=True)


ValueScope = Literal["row", "column"]
ValueExecutor = Callable[[Any, Mapping[str, Any]], bool | None]
OptionValidator = Callable[[Mapping[str, Any]], None]


@dataclass(frozen=True)
class ValueRuleRegistryEntry:
    """Closed declaration and execution ownership for one logical validator."""

    validate_options: OptionValidator
    evaluate: ValueExecutor
    diagnostic_prefix: str
    scope: ValueScope


def _mapping_only(options: Mapping[str, Any]) -> None:
    """Accept a frozen mapping when no further Task-3 shape is intrinsic."""
    if not isinstance(options, Mapping):
        raise CheckDeclarationError("value rule options must be a mapping")


def _membership_options(options: Mapping[str, Any]) -> None:
    _mapping_only(options)
    allowed = options.get("allowed")
    if isinstance(allowed, (str, bytes)) or not isinstance(allowed, Sequence):
        raise CheckDeclarationError("membership value rule requires sequence option 'allowed'")


def _range_options(options: Mapping[str, Any]) -> None:
    _mapping_only(options)
    if not {"minimum", "maximum", "exclusive_minimum", "exclusive_maximum"} & set(options):
        raise CheckDeclarationError("range value rule requires at least one bound option")


def _length_options(options: Mapping[str, Any]) -> None:
    _mapping_only(options)
    if not {"min_length", "max_length"} & set(options):
        raise CheckDeclarationError("length value rule requires min_length or max_length")


def _pattern_options(options: Mapping[str, Any]) -> None:
    _mapping_only(options)
    if not isinstance(options.get("pattern"), str):
        raise CheckDeclarationError("pattern value rule requires text option 'pattern'")


def _membership_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    return canonical_value_key(value) in {
        canonical_value_key(allowed) for allowed in options["allowed"]
    }


def _type_format_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        # Spec 12.2: an already-invalid decode fails TYPE_FORMAT outright --
        # it can never satisfy any declared shape -- while every other
        # value rule (LENGTH/RANGE/pattern/...) treats it as unknown.
        return False
    if value is None:
        return True
    type_name = options.get("type")
    if type_name == "any":
        return True
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return type(value) is int  # noqa: E721 — bool is not an integer
    if type_name == "number":
        return type(value) in {int, float} or isinstance(value, Decimal)  # noqa: E721 — bool is not numeric
    if type_name == "boolean":
        return type(value) is bool  # noqa: E721 — subclasses are invalid
    if type_name in {"list", "array"}:
        return isinstance(value, (list, tuple))
    if type_name == "object":
        return isinstance(value, Mapping)
    if type_name == "duration":
        return parse_duration_value(value) is not INVALID_VALUE
    if type_name == "year":
        return parse_partial_date_value(value, kind="year") is not INVALID_VALUE
    if type_name == "yearmonth":
        return parse_partial_date_value(value, kind="yearmonth") is not INVALID_VALUE
    if type_name == "geojson":
        return isinstance(value, Mapping)
    if type_name == "geopoint":
        return isinstance(value, (list, tuple)) and len(value) in {2, 3}
    from datetime import date, datetime, time

    if type_name == "date":
        return isinstance(value, date) and not isinstance(value, datetime)
    if type_name == "time":
        return isinstance(value, time)
    if type_name == "datetime":
        return isinstance(value, datetime)
    return False


def _length_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    try:
        length = len(value)
    except TypeError:
        return False
    minimum = options.get("min_length")
    maximum = options.get("max_length")
    return (minimum is None or length >= minimum) and (maximum is None or length <= maximum)


def _range_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    try:
        return (
            (options.get("minimum") is None or value >= options["minimum"])
            and (options.get("maximum") is None or value <= options["maximum"])
            and (
                options.get("exclusive_minimum") is None
                or value > options["exclusive_minimum"]
            )
            and (
                options.get("exclusive_maximum") is None
                or value < options["exclusive_maximum"]
            )
        )
    except TypeError:
        return False


def _string_format_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    format_name = options.get("format")
    if format_name in {None, "default"}:
        return True
    if format_name == "email":
        return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) is not None
    if format_name == "uuid":
        from uuid import UUID

        try:
            UUID(value)
        except ValueError:
            return False
        return True
    if format_name == "uri":
        from urllib.parse import urlparse

        return bool(urlparse(value).scheme)
    if format_name == "binary":
        from base64 import b64decode

        try:
            b64decode(value, validate=True)
        except ValueError:
            return False
        return True
    return False


def _pattern_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    return isinstance(value, str) and re.search(options["pattern"], value) is not None


def _json_schema_options(options: Mapping[str, Any]) -> None:
    _mapping_only(options)
    if not isinstance(options.get("schema"), Mapping):
        raise CheckDeclarationError("JSON Schema value rule requires mapping option 'schema'")


def _json_schema_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    from mountainash.validation.jsonschema import compile_json_schema

    return not compile_json_schema(options["schema"]).validate(value)


@dataclass(frozen=True)
class NestedViolation:
    """One unmet member/element requirement and the location it was found at.

    ``instance_path`` is an RFC 6901 pointer of literal member names and element
    indices below the checked field, so a dotted member name stays one segment.
    ``severity`` is the violated definition's own severity (system default when
    unspecified); it is never inherited from an enclosing definition.
    """

    instance_path: str
    schema_path: str | None
    validator: str
    message: str
    severity: str


def _nested_definition(options: Mapping[str, Any]) -> Any:
    """Thaw the plan-owned definition snapshot only for one logical evaluation."""
    from mountainash.validation.plan import thaw_value

    return thaw_value(options["definition"])


def _nested_options(options: Mapping[str, Any]) -> None:
    _mapping_only(options)
    if not isinstance(options.get("definition"), Mapping):
        raise CheckDeclarationError(
            "nested value rule requires the declaring FieldDefinition snapshot as 'definition'"
        )
    severity = options.get("severity")
    if severity is not None:
        from mountainash.validation.checks import validate_severity

        validate_severity("nested value rule", severity)


def _equal_execute(value: Any, options: Mapping[str, Any]) -> bool:
    return canonical_value_key(value) == canonical_value_key(options["expected"])


def _unequal_execute(value: Any, options: Mapping[str, Any]) -> bool:
    return not _equal_execute(value, options)


def _excluded_execute(value: Any, options: Mapping[str, Any]) -> bool:
    return not _membership_execute(value, {"allowed": options["excluded"]})


def _text_part_execute(value: Any, options: Mapping[str, Any]) -> bool:
    part, operation = options["part"], options["operation"]
    if not isinstance(value, str):
        return False
    if operation == "str_contains":
        return part in value
    return value.startswith(part) if operation == "str_startswith" else value.endswith(part)


def _nested_requirements(definition: Any):
    """Yield ``(validator, evaluate, options)`` for each scalar requirement declared.

    Every requirement delegates to the same executor the top-level rule uses.
    """
    constraints = definition.constraints
    for name in ("minimum", "maximum", "exclusive_minimum", "exclusive_maximum"):
        if getattr(constraints, name) is not None:
            yield name, _range_execute, {name: getattr(constraints, name)}
    for name in ("min_length", "max_length"):
        if getattr(constraints, name) is not None:
            yield name, _length_execute, {name: getattr(constraints, name)}
    if definition.type.value == "string" and definition.format != "default":
        yield "format", _string_format_execute, {"format": definition.format}
    if constraints.pattern is not None:
        yield "pattern", _pattern_execute, {"pattern": constraints.pattern}
    if definition.categories:
        from mountainash.typespec._categorical import categorical_values

        allowed = categorical_values(definition.categories)
        if allowed:
            yield "categories", _membership_execute, {"allowed": allowed}
    if constraints.enum is not None:
        yield "enum", _membership_execute, {"allowed": constraints.enum}
    if constraints.eq is not None:
        yield "eq", _equal_execute, {"expected": constraints.eq}
    if constraints.ne is not None:
        yield "ne", _unequal_execute, {"expected": constraints.ne}
    if constraints.notin is not None:
        yield "notin", _excluded_execute, {"excluded": constraints.notin}
    for name in ("str_contains", "str_startswith", "str_endswith"):
        if getattr(constraints, name) is not None:
            yield name, _text_part_execute, {"part": getattr(constraints, name), "operation": name}


def _nested_structured_violations(value: Any, definition: Any, pointer: str, severity: str):
    """JSON Schema and GeoJSON/TopoJSON diagnostics, located below ``pointer``."""
    schema = definition.constraints.json_schema
    if schema is not None:
        from mountainash.validation.jsonschema import compile_json_schema

        for item in compile_json_schema(schema).validate(value):
            yield NestedViolation(
                pointer + item.instance_path, item.schema_path, item.validator, item.message,
                severity,
            )
    if definition.type.value != "geojson":
        return
    from mountainash.validation.geospatial import (
        validate_geojson,
        validate_geojson_winding,
        validate_topojson,
    )

    if definition.format == "topojson":
        found = [(item, severity) for item in validate_topojson(value)]
    else:
        found = [(item, severity) for item in validate_geojson(value)]
        found += [(item, "warning") for item in validate_geojson_winding(value)]
    for item, level in found:
        yield NestedViolation(pointer + item.instance_path, None, item.validator, item.message, level)


def _nested_value_violations(value: Any, definition: Any, path: tuple[Any, ...]):
    """Every requirement ``definition`` places on one member/element value."""
    from mountainash.validation.jsonschema import _json_pointer

    severity = definition.severity or "blocking"
    pointer = _json_pointer(path)
    if value is None:
        if definition.constraints.required:
            yield NestedViolation(pointer, None, "required", "a value is required", severity)
        return
    if not _type_format_execute(
        value, {"type": definition.type.value, "format": definition.format}
    ):
        yield NestedViolation(
            pointer, None, "type", f"value is not a valid {definition.type.value}", severity
        )
        return
    for validator, evaluate, options in _nested_requirements(definition):
        if not evaluate(value, options):
            yield NestedViolation(
                pointer, None, validator, f"value does not satisfy {validator}", severity
            )
    yield from _nested_structured_violations(value, definition, pointer, severity)
    yield from _nested_shape_violations(value, definition, path)


def _nested_shape_violations(value: Any, definition: Any, path: tuple[Any, ...]):
    """Violations of the members or element a definition declares.

    Unknown shape (``UNKNOWN``) and an empty record declare nothing to check.
    """
    from mountainash.validation.jsonschema import _json_pointer

    severity = definition.severity or "blocking"
    members = definition.fields
    if isinstance(members, Mapping) and members:
        if not isinstance(value, Mapping):
            yield NestedViolation(_json_pointer(path), None, "type", "value is not a record", severity)
            return
        for name, child in members.items():
            yield from _nested_value_violations(value.get(name), child, (*path, name))
        return
    element = definition.element
    if element is not None and element is not SchemaTypeStatus.UNKNOWN:
        if not isinstance(value, (list, tuple)):
            yield NestedViolation(
                _json_pointer(path), None, "type", "value is not a collection", severity
            )
            return
        for index, item in enumerate(value):
            yield from _nested_value_violations(item, element, (*path, index))


def _selected_nested_violations(
    value: Any, options: Mapping[str, Any]
) -> tuple[NestedViolation, ...]:
    """The violations one nested rule owns: all, or only the severity it was built for."""
    severity = options.get("severity")
    return tuple(
        violation
        for violation in _nested_shape_violations(value, _nested_definition(options), ())
        if severity is None or violation.severity == severity
    )


def _nested_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    """Apply member and element declarations recursively to object and array values."""
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    return not _selected_nested_violations(value, options)


def _unique_options(options: Mapping[str, Any]) -> None:
    _mapping_only(options)
    path = options.get("path")
    if path is not None and (
        isinstance(path, (str, bytes))
        or not isinstance(path, Sequence)
        or any(segment is not None and not isinstance(segment, str) for segment in path)
    ):
        raise CheckDeclarationError(
            "unique value rule 'path' must be a sequence of member names and None element markers"
        )


def nested_unique_occurrences(
    value: Any, path: Sequence[str | None]
) -> list[tuple[tuple[Any, ...] | None, tuple[Any, ...], tuple[Any, ...]]]:
    """Non-null values found at a declaration ``path`` below one row's cell value.

    ``path`` segments are literal member names, or None where a collection's
    elements are entered. Each occurrence is ``(domain, canonical key, location)``.
    The uniqueness domain follows the field meaning in its active row domain: with no
    collection on the path it is None (the containing records of every row); once
    a collection is entered it is that collection instance's location, so values
    only compete within the collection that contains them.
    """
    found: list[tuple[tuple[Any, ...] | None, tuple[Any, ...], tuple[Any, ...]]] = []

    def walk(current: Any, remaining: Sequence[str | None], location: tuple[Any, ...],
             domain: tuple[Any, ...] | None) -> None:
        if current is None:
            return
        if not remaining:
            found.append((domain, canonical_value_key(current), location))
            return
        segment, rest = remaining[0], remaining[1:]
        if segment is None:
            if isinstance(current, (list, tuple)):
                for index, item in enumerate(current):
                    walk(item, rest, (*location, index), location)
        elif isinstance(current, Mapping):
            walk(current.get(segment), rest, (*location, segment), domain)

    walk(value, tuple(path), (), None)
    return found


def _geojson_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    from mountainash.validation.geospatial import validate_geojson

    return not validate_geojson(value)


def _geojson_winding_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    from mountainash.validation.geospatial import validate_geojson_winding

    return not validate_geojson_winding(value)


def _topojson_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    from mountainash.validation.geospatial import validate_topojson

    return not validate_topojson(value)



@dataclass(frozen=True)
class StructuredValueDiagnostic:
    """One deterministic nested-value failure suitable for result transport."""

    instance_path: str
    schema_path: str | None
    validator: str
    message: str


def structured_value_diagnostics(
    validator: ValueValidatorKey, value: Any, options: Mapping[str, Any]
) -> tuple[StructuredValueDiagnostic, ...]:
    """Return every nested diagnostic for an already-failed logical value."""
    if value is INVALID_VALUE or value is None:
        return ()
    if validator is ValueValidatorKey.NESTED:
        return tuple(
            StructuredValueDiagnostic(
                instance_path=item.instance_path,
                schema_path=item.schema_path,
                validator=item.validator,
                message=item.message,
            )
            for item in _selected_nested_violations(value, options)
        )
    if validator is ValueValidatorKey.JSON_SCHEMA:
        from mountainash.validation.jsonschema import compile_json_schema

        return tuple(
            StructuredValueDiagnostic(
                instance_path=item.instance_path,
                schema_path=item.schema_path,
                validator=item.validator,
                message=item.message,
            )
            for item in compile_json_schema(options["schema"]).validate(value)
        )
    if validator is ValueValidatorKey.GEOJSON:
        from mountainash.validation.geospatial import validate_geojson

        return tuple(
            StructuredValueDiagnostic(
                instance_path=item.instance_path,
                schema_path=None,
                validator=item.validator,
                message=item.message,
            )
            for item in validate_geojson(value)
        )
    if validator is ValueValidatorKey.GEOJSON_WINDING:
        from mountainash.validation.geospatial import validate_geojson_winding

        return tuple(
            StructuredValueDiagnostic(
                instance_path=item.instance_path,
                schema_path=None,
                validator=item.validator,
                message=item.message,
            )
            for item in validate_geojson_winding(value)
        )
    if validator is ValueValidatorKey.TOPOJSON:
        from mountainash.validation.geospatial import validate_topojson

        return tuple(
            StructuredValueDiagnostic(
                instance_path=item.instance_path,
                schema_path=None,
                validator=item.validator,
                message=item.message,
            )
            for item in validate_topojson(value)
        )
    return ()
def _unavailable_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    """A named later-unit executor; it cannot be selected by a default path."""
    del value, options
    raise NotImplementedError("this logical validator is not available until its owning unit")


def _entry(
    validator: OptionValidator,
    evaluate: ValueExecutor,
    prefix: str,
    scope: ValueScope,
) -> ValueRuleRegistryEntry:
    return ValueRuleRegistryEntry(validator, evaluate, prefix, scope)


VALUE_RULE_REGISTRY = MappingProxyType(
    {
        ValueValidatorKey.TYPE_FORMAT: _entry(_mapping_only, _type_format_execute, "type", "column"),
        ValueValidatorKey.LENGTH: _entry(_length_options, _length_execute, "length", "row"),
        ValueValidatorKey.RANGE: _entry(_range_options, _range_execute, "range", "row"),
        ValueValidatorKey.STRING_FORMAT: _entry(_mapping_only, _string_format_execute, "format", "row"),
        ValueValidatorKey.XSD_PATTERN: _entry(_pattern_options, _pattern_execute, "pattern", "row"),
        ValueValidatorKey.MEMBERSHIP: _entry(_membership_options, _membership_execute, "membership", "row"),
        ValueValidatorKey.UNIQUE: _entry(_unique_options, _unavailable_execute, "unique", "column"),
        ValueValidatorKey.NESTED: _entry(_nested_options, _nested_execute, "nested", "row"),
        ValueValidatorKey.JSON_SCHEMA: _entry(_json_schema_options, _json_schema_execute, "json_schema", "row"),
        ValueValidatorKey.GEOJSON: _entry(_mapping_only, _geojson_execute, "geojson", "row"),
        ValueValidatorKey.GEOJSON_WINDING: _entry(_mapping_only, _geojson_winding_execute, "geojson_winding", "row"),
        ValueValidatorKey.TOPOJSON: _entry(_mapping_only, _topojson_execute, "topojson", "row"),
    }
)


def validate_value_rule_options(
    validator: ValueValidatorKey, options: Mapping[str, Any]
) -> None:
    """Validate options through the closed registry; unknown keys never default."""
    try:
        entry = VALUE_RULE_REGISTRY[validator]
    except KeyError:
        raise CheckDeclarationError(f"unknown logical validator {validator!r}") from None
    entry.validate_options(options)


__all__ = []
