"""
Constants for mountainash-pydata.

Contains enumerations for Python data format types used in ingress/egress operations.
"""
from __future__ import annotations

from enum import Enum, auto


class CONST_PYTHON_DATAFORMAT(Enum):
    """Enumeration of supported Python data formats for ingress operations."""

    DATACLASS = auto()
    PYDANTIC = auto()
    PYDICT = auto()
    PYLIST = auto()
    NAMEDTUPLE = auto()
    TUPLE = auto()
    INDEXED_DATA = auto()
    SERIES_DICT = auto()
    COLLECTION = auto()
    UNKNOWN = auto()


__all__ = [
    "CONST_PYTHON_DATAFORMAT",
]
