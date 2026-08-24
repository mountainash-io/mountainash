"""Deterministic parsers for Frictionless temporal lexical values."""
from __future__ import annotations

import re
import warnings
from datetime import date, datetime, time, timezone
from typing import Literal

from dateutil.parser import UnknownTimezoneWarning, parse, parserinfo

TemporalKind = Literal["date", "time", "datetime"]


class _FixedParserInfo(parserinfo):
    def convertyear(self, year: int, century_specified: bool = False) -> int:
        if century_specified or year >= 100:
            return year
        return 2000 + year if year <= 68 else 1900 + year


_PARSER_INFO = _FixedParserInfo(dayfirst=False, yearfirst=True)
_DEFAULT = datetime(2000, 1, 1)
_TZINFOS = {"UTC": timezone.utc, "GMT": timezone.utc}


def parse_temporal_any(
    value: str | date | time | datetime,
    *,
    kind: TemporalKind,
) -> date | time | datetime:
    """Parse a temporal value using one deterministic dateutil policy.

    Native values are passed through only when their exact runtime type matches
    ``kind``. Text with a timezone is normalised to naive UTC, matching the
    canonical temporal values used by the expression layer.
    """
    expected_type = {"date": date, "time": time, "datetime": datetime}[kind]
    if type(value) is expected_type:
        return value
    if not isinstance(value, str):
        raise TypeError(f"{kind} value must be text or a native {kind}")
    with warnings.catch_warnings():
        warnings.simplefilter("error", UnknownTimezoneWarning)
        parsed = parse(
            value,
            parserinfo=_PARSER_INFO,
            default=_DEFAULT,
            fuzzy=False,
            tzinfos=_TZINFOS,
        )
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    if kind == "date":
        return parsed.date()
    if kind == "time":
        return parsed.time()
    return parsed


_TZ = r"(?:Z|[+-](?:0\d|1[0-4]):[0-5]\d)"
_DURATION = re.compile(
    r"^-?P(?=\d|T(?:\d|\.))"
    r"(?:\d+Y)?"
    r"(?:\d+M)?"
    r"(?:\d+D)?"
    r"(?:T(?:(?:\d+H)?(?:\d+M)?(?:(?:\d+(?:\.\d*)?|\.\d+)S)?))?$"
)


def parse_xsd_duration(value: str) -> str:
    """Validate and return an XSD duration lexical value."""
    if not isinstance(value, str) or not _DURATION.fullmatch(value):
        raise ValueError(f"invalid XSD duration: {value!r}")
    body = value[1:] if value.startswith("-") else value
    if body == "P" or body.endswith("T"):
        raise ValueError(f"invalid XSD duration: {value!r}")
    return value


_PARTIAL_DATE = re.compile(rf"^(?P<year>-?[0-9]+)(?:-(?P<month>0[1-9]|1[0-2]))?(?P<tz>{_TZ})?$")


def parse_xsd_partial_date(value: str) -> str:
    """Validate an XSD gYear/gYearMonth lexical value."""
    if not isinstance(value, str):
        raise TypeError("XSD partial date must be text")
    match = _PARTIAL_DATE.fullmatch(value)
    if match is None:
        raise ValueError(f"invalid XSD partial date: {value!r}")
    year = match.group("year")
    if not year.lstrip("-") or set(year.lstrip("-")) == {"0"}:
        raise ValueError(f"invalid XSD partial date: {value!r}")
    tz = match.group("tz")
    if tz and tz not in {"Z"}:
        hours, minutes = map(int, tz[1:].split(":"))
        if hours > 14 or (hours == 14 and minutes != 0):
            raise ValueError(f"invalid XSD partial date: {value!r}")
    return value


_DEFAULT_DATETIME = re.compile(
    rf"^(?:"
    rf"\d{{4}}-\d{{2}}-\d{{2}}"
    rf"(?:[T ]\d{{2}}:\d{{2}}:\d{{2}}(?:\.\d+)?(?:{_TZ})?)?"
    rf")$"
)


def parse_default_datetime(value: str | date | time | datetime) -> datetime:
    """Parse a Frictionless default datetime value."""
    if type(value) is datetime:
        return value
    if type(value) is date:
        return datetime.combine(value, time())
    if type(value) is time:
        return datetime.combine(date(2000, 1, 1), value)
    if not isinstance(value, str):
        raise TypeError("datetime value must be text or a native temporal value")
    if _DEFAULT_DATETIME.fullmatch(value) is None:
        raise ValueError(f"invalid default datetime: {value!r}")
    parsed = parse_temporal_any(value, kind="datetime")
    assert isinstance(parsed, datetime)
    return parsed


__all__ = [
    "TemporalKind",
    "parse_default_datetime",
    "parse_temporal_any",
    "parse_xsd_duration",
    "parse_xsd_partial_date",
]
