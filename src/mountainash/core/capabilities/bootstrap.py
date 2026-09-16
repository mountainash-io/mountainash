"""Load every capability declaration (spec rev 3, §2).

Declaration modules are DISCOVERED under the two capability package roots —
there is no manifest to forget. Exempt from the DECLARATIONS requirement:
__init__.py and ``_``-prefixed helper modules.
"""

from __future__ import annotations

import importlib
import pkgutil

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.core.capabilities.declarations import CapabilityDeclaration
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


def _load_declarations() -> tuple[CapabilityDeclaration, ...]:
    """Collect sorted import-safe declarations without mutating the registry."""
    collected: list[CapabilityDeclaration] = []
    for name in discover_declaration_modules():
        module = importlib.import_module(name)
        declarations = getattr(module, "DECLARATIONS", None)
        if declarations is None:
            raise TypeError(
                f"capability declaration module {name!r} exposes no "
                "DECLARATIONS tuple (spec 2026-08-07 §1); helper modules "
                "must be _-prefixed"
            )
        if type(declarations) is not tuple:
            raise ValueError(f"capability module {name!r} requires an exact DECLARATIONS tuple")
        collected.extend(declarations)
    return tuple(collected)


def load_all_capability_declarations() -> None:
    """Require a complete production load; refuse ISOLATED enumeration.

    Eligibility and data are acquired from one generation. Failed loads retain
    pre-attempt data and rethrow their original exception without retry.
    """
    from mountainash.core.capabilities.registry import CapabilityRegistry

    CapabilityRegistry._acquire_state(enumeration=True)
