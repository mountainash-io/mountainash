"""Operation-level option cells for Unit C wildcard capability gates."""
from __future__ import annotations

import mountainash as ma

from expressions.argument_types._option_helpers import OptionSpec
from expressions.argument_types.option_disposition import (
    OPTION_DISPOSITIONS,
    REGISTERED_OPTION_PROBES,
    OptionCell,
    OptionProbeRegistration,
)
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
    CaseFailureBehaviour,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
    FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL as FK_GEO,
)

_DATETIME_PROTOCOL = "SubstraitScalarDatetimeExpressionSystemProtocol"
_GEOSPATIAL_PROTOCOL = "MountainAshScalarGeospatialExpressionSystemProtocol"
_GATED_FIXTURES = ("ibis", "narwhals-polars", "narwhals-pandas")


def _build(
    fkey,
    option_param: str,
    option_value: str,
    *,
    explicit: bool,
) -> object:
    failure = CaseFailureBehaviour.THROW if explicit else None
    if fkey is FK_DT.PARSE_DEFAULT:
        return ma.col("c").dt.parse_default(
            field_name="c",
            **({"failure_behavior": failure} if failure is not None else {}),
        )
    if fkey is FK_DT.PARSE_TEMPORAL_ANY:
        return ma.col("c").dt.parse_temporal_any(
            "date",
            field_name="c",
            **({"failure_behavior": failure} if failure is not None else {}),
        )
    if fkey is FK_GEO.PARSE_GEOJSON:
        return ma.col("c").geo.parse_geojson(
            format="default",
            field_name="c",
            **({"failure_behavior": failure} if failure is not None else {}),
        )
    if fkey is FK_GEO.SERIALIZE_GEOJSON:
        return ma.col("c").geo.serialize_geojson(
            format="default",
            field_name="c",
            **({"failure_behavior": failure} if failure is not None else {}),
        )
    raise AssertionError(f"unsupported Unit C FKEY: {fkey!r}")


_CASES: tuple[tuple[object, str, str, str, dict[str, list[object]]], ...] = (
    (
        FK_DT.PARSE_DEFAULT,
        _DATETIME_PROTOCOL,
        "parse_datetime_default",
        "failure_behavior",
        {"c": ["2024-01-05T06:07:08"]},
    ),
    (
        FK_DT.PARSE_TEMPORAL_ANY,
        _DATETIME_PROTOCOL,
        "parse_temporal_any",
        "kind",
        {"c": ["2024-01-05"]},
    ),
    (
        FK_DT.PARSE_TEMPORAL_ANY,
        _DATETIME_PROTOCOL,
        "parse_temporal_any",
        "failure_behavior",
        {"c": ["2024-01-05"]},
    ),
    (
        FK_GEO.PARSE_GEOJSON,
        _GEOSPATIAL_PROTOCOL,
        "parse_geojson",
        "format",
        {"c": ['{"type":"Point","coordinates":[1,2]}']},
    ),
    (
        FK_GEO.PARSE_GEOJSON,
        _GEOSPATIAL_PROTOCOL,
        "parse_geojson",
        "failure_behavior",
        {"c": ['{"type":"Point","coordinates":[1,2]}']},
    ),
    (
        FK_GEO.SERIALIZE_GEOJSON,
        _GEOSPATIAL_PROTOCOL,
        "serialize_geojson",
        "format",
        {"c": [{"type": "Point", "coordinates": [1, 2]}]},
    ),
    (
        FK_GEO.SERIALIZE_GEOJSON,
        _GEOSPATIAL_PROTOCOL,
        "serialize_geojson",
        "failure_behavior",
        {"c": [{"type": "Point", "coordinates": [1, 2]}]},
    ),
)


def _cell_disposition(fkey: object, fixture: str) -> tuple[str, str, type[BaseException] | None]:
    if fixture == "polars":
        return "honored", "absence", None
    if fkey in {FK_GEO.PARSE_GEOJSON, FK_GEO.SERIALIZE_GEOJSON}:
        return "declared_unsupported", "op-level", NotImplementedError
    return "probe_exempt", "op-level", None


for fkey, protocol, operation, option_param, data in _CASES:
    option_value = "date" if option_param == "kind" else (
        "default" if option_param == "format" else "throw"
    )
    for fixture in _GATED_FIXTURES:
        disposition, backing_mode, native_failure = _cell_disposition(fkey, fixture)
        OPTION_DISPOSITIONS.append(
            OptionCell(
                fkey,
                protocol,
                operation,
                option_param,
                fixture,
                option_value,
                "str",
                disposition,
                "Unit C operation-level wildcard gate; representative emitted option",
                backing_mode,
            )
        )
        REGISTERED_OPTION_PROBES.append(
            OptionProbeRegistration(
                OptionSpec(
                    fkey,
                    option_param,
                    option_value,
                    "str",
                    lambda f=fkey, p=option_param, v=option_value: _build(
                        f, p, v, explicit=True
                    ),
                    lambda f=fkey, p=option_param, v=option_value: _build(
                        f, p, v, explicit=False
                    ),
                    data,
                    expected_discriminates=False,
                ),
                fixture,
                disposition,
                native_failure,
            )
        )
