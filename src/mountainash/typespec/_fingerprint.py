"""Stable hashes for frozen TypeSpec declarations."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
from typing import Any


def _canonical_bytes(value: Any) -> bytes:
    """Encode the closed frozen-declaration vocabulary deterministically."""
    if value is None:
        return b"n"
    if type(value) is bool:  # noqa: E721 — bool has its own canonical tag
        return b"b1" if value else b"b0"
    if type(value) is int:  # noqa: E721 — bool must not become an integer
        return f"i{value}".encode()
    if type(value) is float:  # noqa: E721 — preserve exact float encoding
        return f"f{value.hex()}".encode()
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return b"s" + str(len(encoded)).encode() + b":" + encoded
    if isinstance(value, bytes):
        return b"y" + str(len(value)).encode() + b":" + value
    if isinstance(value, Mapping):
        parts = sorted(
            (_canonical_bytes(key), _canonical_bytes(item)) for key, item in value.items()
        )
        return b"m" + b"".join(
            str(len(key)).encode() + b":" + key + str(len(item)).encode() + b":" + item
            for key, item in parts
        )
    if isinstance(value, (tuple, list, frozenset, set)):
        parts = (
            sorted(_canonical_bytes(item) for item in value)
            if isinstance(value, (frozenset, set))
            else [_canonical_bytes(item) for item in value]
        )
        return b"q" + b"".join(str(len(item)).encode() + b":" + item for item in parts)
    raise TypeError(f"unsupported frozen declaration value: {type(value)!r}")


def declaration_fingerprint(value: Any) -> str:
    """Return the stable SHA-256 identity of one frozen declaration value."""
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()
