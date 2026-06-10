# src/mountainash/core/dtypes/targets.py
"""Type targets: the systems a canonical dtype can be mapped to/from.

Deliberately NOT CONST_BACKEND — pandas, pyarrow, and python are type
targets (egress/extraction/converters) but not execution backends.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional


class TypeTarget(str, Enum):
    POLARS = "polars"
    PANDAS = "pandas"
    PYARROW = "pyarrow"
    IBIS = "ibis"
    NARWHALS = "narwhals"
    PYTHON = "python"


_MODULE_PREFIX_TO_TARGET: dict[str, TypeTarget] = {
    "polars": TypeTarget.POLARS,
    "pyarrow": TypeTarget.PYARROW,
    "pandas": TypeTarget.PANDAS,
    "numpy": TypeTarget.PANDAS,
    "ibis": TypeTarget.IBIS,
    "narwhals": TypeTarget.NARWHALS,
}


def detect_target(native: Any) -> Optional[TypeTarget]:
    """Best-effort target detection for a native dtype object or class.

    Convenience for public entry points only — internal paths (extraction,
    converters, inference) always pass an explicit TypeTarget. Returns None
    for strings, plain Python types, and anything unrecognized.
    """
    if isinstance(native, str) or native is None:
        return None
    cls = native if isinstance(native, type) else type(native)
    module = getattr(cls, "__module__", "") or ""
    root = module.split(".", 1)[0]
    return _MODULE_PREFIX_TO_TARGET.get(root)
