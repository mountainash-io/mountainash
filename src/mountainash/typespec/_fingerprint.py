"""Stable hashes for frozen TypeSpec declarations."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
from types import MappingProxyType
from typing import Any


def freeze_declaration(value: Any) -> Any:
    """Recursively replace mutable declaration values with immutable tagged data."""
    if isinstance(value, Enum):
        return ("__enum__", value.__class__.__module__, value.__class__.__qualname__, value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return MappingProxyType(
            {
                "__dataclass__": f"{value.__class__.__module__}:{value.__class__.__qualname__}",
                "fields": MappingProxyType(
                    {
                        item.name: freeze_declaration(getattr(value, item.name))
                        for item in fields(value)
                    }
                ),
            }
        )
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: freeze_declaration(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(freeze_declaration(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze_declaration(item) for item in value)
    return value


def freeze_typespec(spec: Any) -> Mapping[str, Any]:
    """Freeze every TypeSpec field before compiling executable metadata."""
    frozen = freeze_declaration(spec)
    assert isinstance(frozen, Mapping)
    return frozen


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
