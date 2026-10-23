# src/mountainash/core/dtypes/registry.py
"""Lazy dtype dispatch façade over the per-target native type adapters.

Lazy per-target loading: importing mountainash never imports
pandas/pyarrow/ibis; a missing optional dependency only raises when its
target is actually requested. The registry selects and retains one stateless
adapter per target and delegates complete operations to it; it holds no
mapping tables, native validation or backend branches.
"""
from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any, Optional

from ._lowering import native_of
from .canonical import CastTarget, SchemaTypeStatus
from .errors import UnknownDtypeError
from .protocols import NativeArrowTransportAdapter, NativeTypeAdapter
from .targets import TypeTarget, detect_target

if TYPE_CHECKING:
    from types import ModuleType

_MODULES: dict[TypeTarget, str] = {
    TypeTarget.POLARS: "target_polars",
    TypeTarget.PANDAS: "target_pandas",
    TypeTarget.PYARROW: "target_pyarrow",
    TypeTarget.IBIS: "target_ibis",
    TypeTarget.NARWHALS: "target_narwhals",
    TypeTarget.PYTHON: "target_python",
}

_ADAPTER_CLASSES: dict[TypeTarget, str] = {
    TypeTarget.POLARS: "PolarsTypeAdapter",
    TypeTarget.PANDAS: "PandasTypeAdapter",
    TypeTarget.PYARROW: "PyArrowTypeAdapter",
    TypeTarget.IBIS: "IbisTypeAdapter",
    TypeTarget.NARWHALS: "NarwhalsTypeAdapter",
    TypeTarget.PYTHON: "PythonTypeAdapter",
}


class DtypeRegistry:
    def __init__(self) -> None:
        self._loaded: dict[TypeTarget, ModuleType] = {}
        self._adapters: dict[TypeTarget, NativeTypeAdapter[Any]] = {}

    def _target(self, target: TypeTarget) -> ModuleType:
        if target not in self._loaded:
            self._loaded[target] = importlib.import_module(
                f".{_MODULES[target]}", package=__package__
            )
        return self._loaded[target]

    def _adapter(self, target: TypeTarget) -> NativeTypeAdapter[Any]:
        """The target's one stateless adapter; it serves both native type contracts."""
        if target not in self._adapters:
            self._adapters[target] = getattr(self._target(target), _ADAPTER_CLASSES[target])()
        return self._adapters[target]

    def to_native_schema(self, dtype: Any, target: TypeTarget) -> Any:
        """Convert schema types without silently discarding descriptor parameters."""
        return self._adapter(target).to_native_schema(dtype)

    def to_native_cast(self, dtype: CastTarget, target: TypeTarget) -> Any:
        """Native type for expression cast use. Bare containers raise."""
        return self._adapter(target).to_native_cast(dtype)

    def from_native(self, native: Any, target: Optional[TypeTarget] = None) -> Any:
        """Decode detailed native type metadata through its owning adapter."""
        if target is None:
            target = detect_target(native)
            if target is None:
                raise UnknownDtypeError(
                    f"Cannot auto-detect a type target for {native!r}; pass target= explicitly."
                )
        return self._adapter(target).from_native(native)

    def parse_type_string(self, s: str, target: TypeTarget) -> Optional[Any]:
        """Best-effort FieldDefinition.backend_type parser. None = unparseable."""
        return self._adapter(target).parse_type_string(s)

    def types_equal(self, left: Any, right: Any, target: TypeTarget) -> bool:
        """Whether two native types of ``target`` are equivalent, retaining parameters."""
        return self._adapter(target).types_equal(left, right)

    def to_arrow_transport(self, dtype: Any) -> Any:
        """Arrow dtype that transports an effective type; None stays None.

        A native type or refinement is converted by its owning target. A
        portable type is constructed by Arrow's own portable construction,
        whose container children come back through this entrypoint so native
        children reach their own owners.
        """
        if dtype is None:
            return None
        if dtype is SchemaTypeStatus.UNKNOWN:
            return self._adapter(TypeTarget.PYARROW).to_arrow_transport(dtype)
        native = native_of(dtype)
        if native is not None:
            owner: NativeArrowTransportAdapter[Any, Any] = self._adapter(native.target)  # type: ignore[assignment]
            return owner.to_arrow_transport(native.value)
        return self._target(TypeTarget.PYARROW).to_arrow_portable(dtype, self.to_arrow_transport)


registry = DtypeRegistry()
