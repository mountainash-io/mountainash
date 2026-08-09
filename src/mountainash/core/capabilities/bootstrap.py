"""Load every capability declaration (spec rev 3, §2).

Declaration modules are DISCOVERED under the two capability package roots —
there is no manifest to forget. Exempt from the DECLARATIONS requirement:
__init__.py and ``_``-prefixed helper modules.
"""
from __future__ import annotations

import importlib
import pkgutil

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


def _load_into_registry() -> None:
    """Registry-internal hook; called ONLY under the registry load lock."""
    from mountainash.core.capabilities.registry import CapabilityRegistry

    for name in discover_declaration_modules():
        module = importlib.import_module(name)
        declarations = getattr(module, "DECLARATIONS", None)
        if declarations is None:
            raise TypeError(
                f"capability declaration module {name!r} exposes no "
                "DECLARATIONS tuple (spec 2026-08-07 §1); helper modules "
                "must be _-prefixed"
            )
        for declaration in declarations:
            CapabilityRegistry.register_declaration(declaration)


def load_all_capability_declarations() -> None:
    """Enumerating load entry: consumers that walk the *whole* declaration set
    call this. Unlike the query-path CapabilityRegistry.ensure_loaded() — which
    silently no-ops in ISOLATED so queries see an isolated registry's own facts
    — this refuses to run in ISOLATED (raises RuntimeError), so an enumerator
    never certifies a partial/isolated registry as complete. Queries autoload;
    enumeration demands a production load. From LOADED it is a no-op; otherwise
    it delegates to ensure_loaded()."""
    from mountainash.core.capabilities.registry import CapabilityRegistry, _LoadState

    state = CapabilityRegistry._load_state
    if state is _LoadState.LOADED:
        return
    if state is _LoadState.ISOLATED:
        raise RuntimeError(
            "registry is ISOLATED (reset() without restore()); refusing to "
            "load production declarations into an isolated registry"
        )
    CapabilityRegistry.ensure_loaded()
