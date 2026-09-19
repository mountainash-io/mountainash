"""Discover physical SEGMENT leaves and bind their enclosing SCOPE context.

Package initializers and underscore-prefixed helpers are not declaration leaves.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.core.capabilities.declarations import BoundSegment
_ROOTS = (
    "mountainash.expressions.backends.capabilities",
    "mountainash.relations.backends.capabilities",
)


def discover_declaration_modules() -> tuple[str, ...]:
    names: list[str] = []
    for root in _ROOTS:
        pkg = importlib.import_module(root)
        for info in pkgutil.walk_packages(pkg.__path__, prefix=root + "."):
            leaf = info.name.rsplit(".", 1)[1]
            if leaf.startswith("_"):
                continue
            if not info.ispkg:
                names.append(info.name)
    return tuple(sorted(names))


def _source_path(name: str) -> Path:
    """Locate a declaration leaf beneath its imported declared package root."""
    roots = tuple(root for root in _ROOTS if name.startswith(root + "."))
    if len(roots) != 1:
        raise ValueError(f"capability module {name!r} is not beneath one declared root")
    root = roots[0]
    package = importlib.import_module(root)
    suffix = name.removeprefix(root + ".").split(".")
    for location in package.__path__:
        root_path = Path(location).resolve()
        source_path = (root_path.joinpath(*suffix).with_suffix(".py")).resolve()
        try:
            source_path.relative_to(root_path)
        except ValueError:
            raise ValueError(f"capability module {name!r} resolves outside declared root {root!r}") from None
        if source_path.is_file():
            return source_path
    raise ValueError(f"capability module {name!r} has no source file")


def _segment_from_source(name: str, source_path: Path, source: bytes):
    """Evaluate exact retained bytes in a private declaration namespace."""
    module = ModuleType(name)
    module.__file__ = str(source_path)
    module.__package__ = name.rpartition(".")[0]
    exec(compile(source, str(source_path), "exec"), vars(module))
    return getattr(module, "SEGMENT", None)


def _load_segments() -> tuple[BoundSegment, ...]:
    """Collect and qualify every physical segment without publishing any state."""
    from mountainash.core.capabilities.capture import CapturedAddress
    from mountainash.core.capabilities.declarations import BoundSegment, CapabilitySegment

    collected: list[BoundSegment] = []
    for name in discover_declaration_modules():
        source_path = _source_path(name)
        source_bytes = source_path.read_bytes()
        segment = _segment_from_source(name, source_path, source_bytes)
        if type(segment) is not CapabilitySegment:
            raise TypeError(f"capability module {name!r} requires a CapabilitySegment SEGMENT")
        parts = name.split(".")
        if len(parts) < 8 or parts[5] not in {"family", "dialects"}:
            raise ValueError(f"capability module {name!r} lacks a physical scope")
        source_index = 6 if parts[5] == "family" else 7
        scope_module = importlib.import_module(".".join(parts[:source_index]) + "._scope")
        source = CapturedAddress(
            "mountainash",
            "src/" + name.replace(".", "/") + ".py",
            "SEGMENT",
            artifact=source_bytes,
        )
        collected.append(BoundSegment(name, getattr(scope_module, "SCOPE", None), segment, source))
    return tuple(collected)


def load_all_capability_declarations() -> None:
    """Require a complete production load; refuse ISOLATED enumeration.

    Eligibility and data are acquired from one generation. Failed loads retain
    pre-attempt data and rethrow their original exception without retry.
    """
    from mountainash.core.capabilities.registry import CapabilityRegistry

    CapabilityRegistry._acquire_state(enumeration=True)
