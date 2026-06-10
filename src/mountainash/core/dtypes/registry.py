# src/mountainash/core/dtypes/registry.py
"""Single per-target dtype mapping registry.

Lazy per-target loading: importing mountainash never imports
pandas/pyarrow/ibis; a missing optional dependency only raises when its
target is actually requested.
"""
from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any, Optional

from .errors import DtypeMappingError, UnknownDtypeError
from .targets import TypeTarget, detect_target

if TYPE_CHECKING:
    from types import ModuleType

    from .canonical import MountainashDtype

_MODULES: dict[TypeTarget, str] = {
    TypeTarget.POLARS: "target_polars",
    TypeTarget.PANDAS: "target_pandas",
    TypeTarget.PYARROW: "target_pyarrow",
    TypeTarget.IBIS: "target_ibis",
    TypeTarget.NARWHALS: "target_narwhals",
    TypeTarget.PYTHON: "target_python",
}


class DtypeRegistry:
    def __init__(self) -> None:
        self._loaded: dict[TypeTarget, ModuleType] = {}

    def _target(self, target: TypeTarget) -> ModuleType:
        if target not in self._loaded:
            self._loaded[target] = importlib.import_module(
                f".{_MODULES[target]}", package=__package__
            )
        return self._loaded[target]

    def to_native_schema(self, dtype: MountainashDtype, target: TypeTarget) -> Any:
        """Native type for schema/materialization use. Complete over all members."""
        mod = self._target(target)
        try:
            return mod.SCHEMA_TYPES[dtype]
        except KeyError:
            raise DtypeMappingError(
                f"No {target.value} schema mapping for {dtype.value!r}. "
                f"Supported: {sorted(d.value for d in mod.SCHEMA_TYPES)}"
            ) from None

    def to_native_cast(self, dtype: MountainashDtype, target: TypeTarget) -> Any:
        """Native type for expression cast use. Bare containers raise."""
        mod = self._target(target)
        if dtype in mod.CAST_UNSUPPORTED:
            supported = sorted(
                d.value for d in mod.SCHEMA_TYPES if d not in mod.CAST_UNSUPPORTED
            )
            raise DtypeMappingError(
                f"{dtype.value!r} is not a valid bare cast target on "
                f"{target.value} (a container cast needs an element type — "
                f"pass a native dtype for a parameterized cast). "
                f"Supported cast targets: {supported}"
            )
        return self.to_native_schema(dtype, target)

    def from_native(
        self, native: Any, target: Optional[TypeTarget] = None
    ) -> Optional[MountainashDtype]:
        """Collapse a native dtype to canon. None = explicitly untyped native.

        target=None auto-detects from the object's module — convenience for
        public entry points; internal paths pass an explicit target.
        """
        if target is None:
            target = detect_target(native)
            if target is None:
                raise UnknownDtypeError(
                    f"Cannot auto-detect a type target for {native!r}; "
                    f"pass target= explicitly."
                )
        return self._target(target).from_native(native)

    def parse_type_string(self, s: str, target: TypeTarget) -> Optional[Any]:
        """Best-effort FieldSpec.backend_type parser. None = unparseable."""
        return self._target(target).parse_type_string(s)


registry = DtypeRegistry()
