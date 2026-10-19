"""Logical-value primitives shared by every backend-neutral validation rule.

This module owns value-only concerns: immutable rule registry declarations,
semantic-string parsing, canonical equality, and deterministic rendering.  It
intentionally does not materialize relations or create backend expressions.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
import math
import re
from types import MappingProxyType
from typing import Any, Literal

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


def _nested_contextual_value(value: Any, candidate: Any) -> Any:
    """Parse lexical nested bounds against the already-typed field value."""
    from datetime import date, datetime, time

    if candidate is None:
        return value
    if isinstance(candidate, datetime) and isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return value
    if isinstance(candidate, date) and not isinstance(candidate, datetime) and isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return value
    if isinstance(candidate, time) and isinstance(value, str):
        try:
            return time.fromisoformat(value)
        except ValueError:
            return value
    if isinstance(candidate, Decimal) and isinstance(value, (str, int, float)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return value
    return value


def _nested_field_valid(
    value: Any,
    field: Any,
    *,
    severity_group: str | None = None,
) -> bool:
    """Evaluate a field's declarations in its own severity scope."""
    effective_severity = field.severity or "blocking"
    if value is not None and field.type.value in {"array", "object"}:
        value = parse_logical_value(value, type_name=field.type.value)
        if value is INVALID_VALUE:
            return severity_group is None or severity_group == effective_severity
    constraints = field.constraints
    if value is None:
        if severity_group is not None and severity_group != effective_severity:
            return True
        return not (constraints and constraints.required)
    if not _type_format_execute(value, {"type": field.type.value, "format": field.format}):
        return severity_group is None or severity_group == effective_severity
    check_own = severity_group is None or severity_group == effective_severity
    if check_own and constraints:
        for name, bound in {
            "minimum": constraints.minimum, "maximum": constraints.maximum,
            "exclusive_minimum": constraints.exclusive_minimum,
            "exclusive_maximum": constraints.exclusive_maximum,
        }.items():
            if bound is not None and not _range_execute(
                value, {name: _nested_contextual_value(bound, value)}
            ):
                return False
        for name, bound in {
            "min_length": constraints.min_length, "max_length": constraints.max_length,
        }.items():
            if bound is not None and not _length_execute(value, {name: bound}):
                return False
        if constraints.pattern is not None and not _pattern_execute(value, {"pattern": constraints.pattern}):
            return False
        if constraints.enum is not None and not _membership_execute(
            value,
            {"allowed": tuple(_nested_contextual_value(item, value) for item in constraints.enum)},
        ):
            return False
        if constraints.json_schema is not None and not _json_schema_execute(value, {"schema": constraints.json_schema}):
            return False
        if constraints.eq is not None and canonical_value_key(value) != canonical_value_key(
            _nested_contextual_value(constraints.eq, value)
        ):
            return False
        if constraints.ne is not None and canonical_value_key(value) == canonical_value_key(
            _nested_contextual_value(constraints.ne, value)
        ):
            return False
        if constraints.notin is not None and any(
            canonical_value_key(value)
            == canonical_value_key(_nested_contextual_value(item, value))
            for item in constraints.notin
        ):
            return False
        if constraints.str_contains is not None and constraints.str_contains not in value:
            return False
        if constraints.str_startswith is not None and not value.startswith(constraints.str_startswith):
            return False
        if constraints.str_endswith is not None and not value.endswith(constraints.str_endswith):
            return False
    if check_own and field.categories is not None:
        from mountainash.typespec._categorical import categorical_values
        if not _membership_execute(
            value,
            {"allowed": tuple(
                _nested_contextual_value(item, value)
                for item in categorical_values(field.categories)
            )},
        ):
            return False
    if field.fields is not None:
        if not isinstance(value, Mapping):
            return check_own
        return _nested_object_valid(value, field.fields, severity_group=severity_group)
    if field.element is not None:
        if not isinstance(value, (list, tuple)):
            return check_own
        dimensions = getattr(field, "dimensions", None)
        if isinstance(dimensions, tuple) and dimensions:
            return _nested_dimensional_collection_valid(
                value, field.element, len(dimensions),
                severity_group=severity_group,
            )
        return _nested_collection_valid(
            value, field.element, severity_group=severity_group
        )
    return True


def _nested_dimensional_collection_valid(
    value: Any,
    element: Any,
    remaining_dimensions: int,
    *,
    severity_group: str | None = None,
) -> bool:
    """Apply element declarations only at the declared fixed-array leaves."""
    if value is None or not isinstance(value, (list, tuple)):
        return True
    if remaining_dimensions == 1:
        return all(
            _nested_field_valid(item, element, severity_group=severity_group)
            for item in value
        )
    return all(
        _nested_dimensional_collection_valid(
            item, element, remaining_dimensions - 1,
            severity_group=severity_group,
        )
        for item in value
    )


def _nested_object_valid(
    value: Any,
    fields: Mapping[str, Any],
    *,
    severity_group: str | None = None,
) -> bool:
    if not isinstance(value, Mapping):
        return True
    return all(
        _nested_field_valid(
            value.get(name), definition, severity_group=severity_group
        )
        for name, definition in fields.items()
    )


def _nested_collection_valid(
    value: Any,
    element: Any,
    *,
    severity_group: str | None = None,
) -> bool:
    if value is None or not isinstance(value, (list, tuple)):
        return True
    return all(
        _nested_field_valid(item, element, severity_group=severity_group)
        for item in value
    )


def _nested_execute(value: Any, options: Mapping[str, Any]) -> bool | None:
    if value is INVALID_VALUE:
        return None
    if value is None:
        return True
    from mountainash.validation.plan import thaw_value

    fields = thaw_value(options["fields"]) if options.get("fields") is not None else None
    element = thaw_value(options["element"]) if options.get("element") is not None else None
    severity_group = options.get("severity_group")
    if fields is not None:
        return _nested_object_valid(value, fields, severity_group=severity_group)
    if element is not None:
        return _nested_collection_valid(value, element, severity_group=severity_group)
    return True


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
        ValueValidatorKey.UNIQUE: _entry(_mapping_only, _unavailable_execute, "unique", "column"),
        ValueValidatorKey.NESTED: _entry(_mapping_only, _nested_execute, "nested", "row"),
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
