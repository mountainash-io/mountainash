"""Deterministic parsers for Frictionless temporal lexical values."""
from __future__ import annotations

import re
import warnings
from datetime import date, datetime, time, timezone
from typing import Literal

from dateutil.parser import UnknownTimezoneWarning, parse, parserinfo

TemporalKind = Literal["date", "time", "datetime"]
PartialDateKind = Literal["year", "yearmonth"]

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


_TZ = r"(?:Z|[+-](?:0[0-9]|1[0-4]):[0-5][0-9])"
_DURATION = re.compile(
    r"^-?P"
    r"(?:[0-9]+Y)?(?:[0-9]+M)?(?:[0-9]+D)?"
    r"(?:T(?:[0-9]+H)?(?:[0-9]+M)?(?:(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)S)?)?$"
)


def parse_xsd_duration(value: str) -> str:
    """Validate and return an XSD duration lexical value."""
    if not isinstance(value, str):
        raise TypeError("XSD duration must be text")
    body = value[1:] if value.startswith("-") else value
    if body in {"P", "PT"} or body.endswith("T"):
        raise ValueError(f"invalid XSD duration: {value!r}")
    if _DURATION.fullmatch(value) is None:
        raise ValueError(f"invalid XSD duration: {value!r}")
    return value


_YEAR = r"(?:[0-9]{4}|[1-9][0-9]{4,})"
_NEGATIVE_YEAR = r"(?:-[0-9]{4}|-[1-9][0-9]{4,})"
_PARTIAL_DATE = {
    "year": re.compile(rf"^(?:{_YEAR}|{_NEGATIVE_YEAR}){_TZ}?$"),
    "yearmonth": re.compile(rf"^(?:{_YEAR}|{_NEGATIVE_YEAR})-(?:0[1-9]|1[0-2]){_TZ}?$"),
}


def parse_xsd_partial_date(value: str, *, kind: PartialDateKind) -> str:
    """Validate an XSD gYear or gYearMonth lexical value."""
    if not isinstance(value, str):
        raise TypeError("XSD partial date must be text")
    if kind not in _PARTIAL_DATE:
        raise ValueError(f"invalid XSD partial-date kind: {kind!r}")
    if _PARTIAL_DATE[kind].fullmatch(value) is None or value.startswith("-0000"):
        raise ValueError(f"invalid XSD partial date: {value!r}")
    tz_match = re.search(r"(?:Z|[+-][0-9]{2}:[0-9]{2})$", value)
    if tz_match and tz_match.group() != "Z":
        tz = tz_match.group()
        hours, minutes = int(tz[1:3]), int(tz[4:6])
        if hours > 14 or (hours == 14 and minutes != 0):
            raise ValueError(f"invalid XSD partial date: {value!r}")
    return value


_DEFAULT_DATETIME = re.compile(
    rf"^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}T"
    rf"[0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}}(?:\.[0-9]+)?(?:{_TZ})?$"
)


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def parse_default_datetime(value: str | date | time | datetime) -> datetime:
    """Parse a Frictionless default datetime value."""
    if type(value) is datetime:
        return _naive_utc(value)
    if type(value) is date:
        return datetime.combine(value, time())
    if type(value) is time:
        combined = datetime.combine(date(2000, 1, 1), value)
        return _naive_utc(combined)
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
    "PartialDateKind",
]
