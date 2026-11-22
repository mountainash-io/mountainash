"""What a mountainash error may show of a location (W8 safe-location display).

Errors show only parts known to be safe, built up from the input rather than
masked down from it, so a credential shape nobody anticipated is left out.
Stdlib only and linear in the input: no regex runs except anchored at the start.
Canonical URIs stay intact internally for resolution and caching; this module
renders them at error boundaries only.
"""
from __future__ import annotations

import os
import re
from collections.abc import Collection, Mapping
from typing import Any, NoReturn

REDACTED = "***"

# An RFC 3986 scheme at the start of the string; anchored, so matching is linear.
_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*:")
_C0_OR_SPACE = "".join(chr(code) for code in range(0x21))


def _first(text: str, characters: str, start: int, end: int) -> int:
    """Index of the first of *characters* in text[start:end], or *end*."""
    found = end
    for character in characters:
        index = text.find(character, start, found)
        if index != -1:
            found = index
    return found


def safe_location(location: str | os.PathLike[str]) -> str:
    """Return the part of *location* an error may show.

    ``scheme://…`` and ``//…``: scheme, host, port and path; userinfo (to the
    last ``@`` of the authority), query and fragment are left out. Any other
    string that starts with a scheme: ``***``. Anything else is a local path
    (including ``C:/`` and ``C:\\`` drives) and is returned unchanged.
    """
    text = os.fspath(location).lstrip(_C0_OR_SPACE)
    for character in "\t\r\n":
        text = text.replace(character, "")
    scheme = _SCHEME.match(text)
    if text.startswith("//"):
        authority_start = 2
    elif scheme is None:
        return text
    elif text.startswith("//", scheme.end()):
        authority_start = scheme.end() + 2
    elif scheme.end() == 2 and text[2:3] in ("/", "\\"):
        return text  # Windows drive letter
    else:
        return REDACTED
    authority_end = _first(text, "/?#", authority_start, len(text))
    at = text.rfind("@", authority_start, authority_end)
    host_start = authority_start if at == -1 else at + 1
    path_end = _first(text, "?#", authority_end, len(text))
    return text[:authority_start] + text[host_start:authority_end] + text[authority_end:path_end]


_MAX_DEPTH = 32


def display_value(value: Any, _depth: int = 0) -> Any:
    """Display form of a value carried on an error attribute.

    Strings and path-likes become :func:`safe_location`; mappings, lists and
    tuples are rendered element by element (keys included); bytes are decoded
    (replacing undecodable bytes) and rendered as strings; ``None`` and plain
    numbers/booleans are kept. Any other object is reduced to its type name, so
    an attribute never retains a caller object that could hold a credential.
    Containers nested deeper than 32 levels (including self-referential ones)
    are reduced to their type name too.
    """
    if isinstance(value, str):
        return safe_location(value)
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    if isinstance(value, (bytes, bytearray)):
        return safe_location(bytes(value).decode("utf-8", "replace"))
    if isinstance(value, os.PathLike):
        text = os.fspath(value)
        if not isinstance(text, str):
            return f"<{type(value).__name__}>"
        if not type(value).__module__.startswith("pathlib") and _SCHEME.match(text) and text[2:3] not in ("/", "\\"):
            # A third-party path object (universal_pathlib) may already have moved userinfo
            # into its path; its string form is not a location this module can parse.
            return REDACTED
        return safe_location(text)
    if isinstance(value, (Mapping, list, tuple)) and _depth < _MAX_DEPTH:
        nested = _depth + 1
        if isinstance(value, Mapping):
            return {
                display_value(key, nested): display_value(item, nested)
                for key, item in value.items()
            }
        items = [display_value(item, nested) for item in value]
        return items if isinstance(value, list) else tuple(items)
    return f"<{type(value).__name__}>"


def _fresh_os_error(exc: OSError, filename: str | None = None) -> OSError:
    """A new exception of *exc*'s type from errno and strerror only (plus a display filename)."""
    args: tuple[Any, ...] = (exc.errno, exc.strerror)
    if filename is not None:
        args += (filename,)
    try:
        return type(exc)(*args)
    except Exception:  # noqa: BLE001 - a subclass constructor that rejects (errno, strerror)
        return OSError(*args)


def safe_cause(exc: BaseException, trusted: Collection[type] = ()) -> BaseException | None:
    """The exception an error may chain as ``__cause__`` in place of *exc*.

    ``OSError`` with an errno: a fresh exception of the same type with only
    ``errno`` and ``strerror``. A *trusted* type (exact match, own errors whose
    message and attributes are built under this rule): *exc*. Anything else:
    ``None``. The decision depends on the type only, never on the text.
    """
    if isinstance(exc, OSError):
        return None if exc.errno is None else _fresh_os_error(exc)
    return exc if type(exc) in trusted else None


def raise_safe(
    error: BaseException, native: BaseException, trusted: Collection[type] = ()
) -> NoReturn:
    """Raise *error* with only :func:`safe_cause` of *native* reachable.

    Call inside the ``except`` block handling *native*. ``__context__`` is
    always cleared: ``raise ... from`` alone keeps *native* there, and so does
    any context *native* itself accumulated in an ambient handler.
    """
    try:
        raise error from safe_cause(native, trusted)
    finally:
        error.__context__ = None


def safe_os_error(exc: OSError, location: str | os.PathLike[str]) -> OSError:
    """A fresh exception of *exc*'s type for *location*, built from errno and strerror.

    ``filename`` holds the display form of *location*, taken from the caller's
    original input rather than the path the OS saw (``pathlib`` collapses
    ``https://`` to ``https:/``). Without an errno, only the class name and
    display form are shown.
    """
    shown = safe_location(location)
    if exc.errno is None:
        return OSError(f"{shown}: {type(exc).__name__}")
    return _fresh_os_error(exc, shown)


def raise_os_error(exc: OSError, location: str | os.PathLike[str]) -> NoReturn:
    """Raise :func:`safe_os_error` for *exc* with no cause and no context.

    Call inside the ``except`` block handling *exc*.
    """
    error = safe_os_error(exc, location)
    try:
        raise error from None
    finally:
        error.__context__ = None


__all__ = [
    "REDACTED",
    "display_value",
    "raise_os_error",
    "raise_safe",
    "safe_cause",
    "safe_location",
    "safe_os_error",
]
