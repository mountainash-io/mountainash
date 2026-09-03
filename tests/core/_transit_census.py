"""AST-based discovery of pandas-transit boundary candidates.

Support library for `test_conversion_boundary_census.py` and
`scripts/generate_transit_inventory.py` — not a test module itself.

A *candidate* is any production call-site expression that can produce a
pandas value: a pandas constructor/function call, a Narwhals namespace
conversion call, or one of the generic risky attribute names (``execute``,
``to_pandas``, ``collect``, ...). A candidate is *wrapped* only when it is
the literal callable argument of a ``transit_call(BoundaryKey.MEMBER, ...)``
invocation; every other occurrence — a direct call, a stored bound method, a
callback argument — is unwrapped. See
``mountainash-central/04.planning/mountainash/superpowers/specs/
2026-08-27-pandas-transit-elimination-design.md`` section 13.1.
"""
from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from mountainash.core.transit import BOUNDARY_REGISTRY, BoundaryKey

# Generic risky attribute names: flagged regardless of the base object's
# statically-resolved type, since the base is usually not staticaly
# resolvable (spec 13.1).
RISKY_METHOD_NAMES: frozenset[str] = frozenset(
    {
        "execute",
        "to_pandas",
        "to_pandas_batches",
        "from_pandas",
        "collect",
        "to_native",
        "to_polars",
        "to_arrow",
        "to_pyarrow",
        "memtable",
    }
)

# Narwhals namespace conversion callables (spec 13.1's initial set). Only
# flagged when the call base resolves to the imported `narwhals` module.
NARWHALS_RISKY_NAMES: frozenset[str] = frozenset(
    {
        "from_dict",
        "from_dicts",
        "from_native",
        "from_arrow",
        "from_numpy",
        "narwhalify",
    }
)

# pandas constructors/functions. Only flagged when the call base resolves to
# the imported `pandas` module (or a name imported directly from it).
PANDAS_RISKY_NAMES: frozenset[str] = frozenset({"DataFrame", "Series", "Index", "concat"})

# `import X as Y` is not the only way a module ends up bound to a local
# name: the codebase's own lazy-import convention (see
# f.development-practices/import-conventions.md, "lazy_imports for runtime
# optional backends") assigns a module via a factory call instead --
# `nw = import_narwhals()` binds `nw` to the `narwhals` module exactly as
# `import narwhals as nw` would. Without recognizing this, every
# `NARWHALS_RISKY_NAMES`/`PANDAS_RISKY_NAMES` namespace call reached through
# the lazy-import convention is invisible to the census -- a structural
# blind spot, not a handful of one-off sites.
_LAZY_IMPORT_FACTORY_MODULE: dict[str, str] = {
    "import_pandas": "pandas",
    "import_narwhals": "narwhals",
    "import_polars": "polars",
    "import_ibis": "ibis",
    "import_pyarrow": "pyarrow",
}

_DYNAMIC_DISPATCH_OWNERS: frozenset[str] = frozenset({"getattr", "methodcaller", "partial"})


@dataclass(frozen=True, order=True)
class TransitCandidate:
    """One discovered risky call-site expression."""

    module: str
    owner: str
    callee: str
    fingerprint: str
    wrapped: bool
    boundary_key: str | None = None

    @property
    def identity(self) -> tuple[str, str, str, str]:
        return self.module, self.owner, self.callee, self.fingerprint


@dataclass(frozen=True)
class InventoryEntry:
    """One characterized row from `tests/fixtures/transit_inventory.json`."""

    module: str
    owner: str
    callee: str
    fingerprint: str
    boundary_key: str
    transit_class: str
    reason: str
    since: str
    legacy_unwrapped: bool = False

    @property
    def identity(self) -> tuple[str, str, str, str]:
        return self.module, self.owner, self.callee, self.fingerprint


@dataclass(frozen=True)
class LegacyDisposition:
    """Explicit policy for a known direct (legacy) candidate."""

    boundary_key: str
    reason: str
    since: str
    owner: str


LEGACY_UNWRAPPED: Mapping[tuple[str, str, str, str], LegacyDisposition] = {}


class UnclassifiedCandidateError(RuntimeError):
    """A discovered candidate could not be classified from declared policy."""


def _fingerprint(node: ast.AST) -> str:
    dumped = ast.dump(node, include_attributes=False)
    return hashlib.sha256(dumped.encode()).hexdigest()[:16]


def _module_name(root: Path, file_path: Path) -> str:
    package_name = root.name
    rel_parts = list(file_path.relative_to(root).parts)
    if rel_parts[-1] == "__init__.py":
        rel_parts = rel_parts[:-1]
    else:
        rel_parts[-1] = rel_parts[-1][: -len(".py")]
    return ".".join([package_name, *rel_parts]) if rel_parts else package_name


class _AliasMap:
    """Import-alias resolution for one module: local name -> origin module."""

    def __init__(self) -> None:
        # local name -> module dotted path this name refers to as a module
        # (e.g. `import pandas as pd` -> {"pd": "pandas"}).
        self.module_aliases: dict[str, str] = {}
        # local name -> (origin module, original name) for `from X import Y`.
        self.imported_symbols: dict[str, tuple[str, str]] = {}

    def collect(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[0]
                    self.module_aliases[local] = alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    local = alias.asname or alias.name
                    self.imported_symbols[local] = (node.module, alias.name)
        # Second pass: `target = import_narwhals()` (or `import_pandas`/
        # `import_polars`/`import_ibis`/`import_pyarrow`) binds `target` to
        # that module, same as a literal `import` statement. Requires
        # `imported_symbols` from the first pass to resolve the factory
        # call's own origin.
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            value = node.value
            if not isinstance(target, ast.Name) or not isinstance(value, ast.Call):
                continue
            func = value.func
            if not isinstance(func, ast.Name):
                continue
            origin = self.imported_symbols.get(func.id)
            if origin is None:
                continue
            _origin_module, original_name = origin
            module = _LAZY_IMPORT_FACTORY_MODULE.get(original_name)
            if module is not None:
                self.module_aliases[target.id] = module

    def resolves_to_module(self, name_node: ast.expr, module: str) -> bool:
        return isinstance(name_node, ast.Name) and self.module_aliases.get(name_node.id) == module

    def name_call_origin(self, name: str) -> tuple[str, str] | None:
        return self.imported_symbols.get(name)


def _risky_callee(func_node: ast.expr, aliases: _AliasMap) -> str | None:
    """Return the risky callee name `func_node` refers to, or None."""
    if isinstance(func_node, ast.Attribute):
        if func_node.attr in RISKY_METHOD_NAMES:
            return func_node.attr
        if func_node.attr in NARWHALS_RISKY_NAMES and aliases.resolves_to_module(
            func_node.value, "narwhals"
        ):
            return func_node.attr
        if func_node.attr in PANDAS_RISKY_NAMES and aliases.resolves_to_module(
            func_node.value, "pandas"
        ):
            return func_node.attr
        return None
    if isinstance(func_node, ast.Name):
        origin = aliases.name_call_origin(func_node.id)
        if origin is None:
            return None
        origin_module, original_name = origin
        if origin_module == "pandas" and original_name in PANDAS_RISKY_NAMES:
            return original_name
        if origin_module == "narwhals" and original_name in NARWHALS_RISKY_NAMES:
            return original_name
        return None
    return None


def _is_transit_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "transit_call"
    if isinstance(func, ast.Attribute):
        return func.attr == "transit_call"
    return False


def _transit_fn_arg(node: ast.Call) -> ast.expr | None:
    """Return positional argument one from the public transit_call signature."""
    return node.args[1] if len(node.args) >= 2 else None


def _iter_children(value: object) -> list[ast.AST]:
    if isinstance(value, ast.AST):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, ast.AST)]
    return []


def _owner_for(function_name: str, class_name: str | None) -> str:
    return f"{class_name}.{function_name}" if class_name else function_name


def _literal_boundary_key(node: ast.Call) -> str | None:
    """Return a literal ``BoundaryKey.MEMBER`` name, if present."""
    if not node.args:
        return None
    key_arg = node.args[0]
    if (
        isinstance(key_arg, ast.Attribute)
        and isinstance(key_arg.value, ast.Name)
        and key_arg.value.id == "BoundaryKey"
    ):
        return key_arg.attr
    return None


def _walk_dynamic_dispatch(
    node: ast.Call,
    module: str,
    owner: str,
    out: list[TransitCandidate],
) -> None:
    """Flag `getattr(x, "execute")`, `methodcaller("to_pandas")`, and
    `partial(x.to_pandas)` — dynamic or stored dispatch of a risky name that
    a literal `BoundaryKey` census can never verify (spec 13.1)."""
    func = node.func
    name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
    if name == "getattr" and len(node.args) >= 2:
        target = node.args[1]
        if isinstance(target, ast.Constant) and isinstance(target.value, str):
            if target.value in RISKY_METHOD_NAMES:
                out.append(
                    TransitCandidate(
                        module, owner, target.value, _fingerprint(node), wrapped=False, boundary_key=None
                    )
                )
    elif name == "methodcaller" and node.args:
        target = node.args[0]
        if isinstance(target, ast.Constant) and isinstance(target.value, str):
            if target.value in RISKY_METHOD_NAMES:
                out.append(
                    TransitCandidate(
                        module, owner, target.value, _fingerprint(node), wrapped=False, boundary_key=None
                    )
                )
    elif name == "partial" and node.args:
        target = node.args[0]
        if isinstance(target, ast.Attribute) and target.attr in RISKY_METHOD_NAMES:
            out.append(
                TransitCandidate(
                    module, owner, target.attr, _fingerprint(node), wrapped=False, boundary_key=None
                )
            )


def _visit(
    node: ast.AST,
    module: str,
    class_name: str | None,
    owner: str,
    aliases: _AliasMap,
    out: list[TransitCandidate],
) -> None:
    if isinstance(node, ast.ClassDef):
        for child in node.body:
            _visit(child, module, node.name, owner, aliases, out)
        return

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        new_owner = _owner_for(node.name, class_name)
        for child in ast.iter_child_nodes(node):
            _visit(child, module, class_name, new_owner, aliases, out)
        return

    if isinstance(node, ast.Attribute) and node.attr in RISKY_METHOD_NAMES:
        # A bare risky reference not reached via the ast.Call branch below
        # (stored bound method, callback argument, chained access, ...).
        out.append(
            TransitCandidate(
                module, owner, node.attr, _fingerprint(node), wrapped=False, boundary_key=None
            )
        )
        _visit(node.value, module, class_name, owner, aliases, out)
        return

    if isinstance(node, ast.Call):
        skip_ids: set[int] = set()
        boundary_key = _literal_boundary_key(node)
        if _is_transit_call(node) and boundary_key is not None:
            fn_arg = _transit_fn_arg(node)
            if fn_arg is not None:
                risky = _risky_callee(fn_arg, aliases)
                if risky is not None:
                    out.append(
                        TransitCandidate(
                            module,
                            owner,
                            risky,
                            _fingerprint(node),
                            wrapped=True,
                            boundary_key=boundary_key,
                        )
                    )
                    skip_ids.add(id(fn_arg))
        else:
            risky = _risky_callee(node.func, aliases)
            if risky is not None:
                out.append(
                    TransitCandidate(
                        module, owner, risky, _fingerprint(node), wrapped=False, boundary_key=None
                    )
                )
                skip_ids.add(id(node.func))
            else:
                _walk_dynamic_dispatch(node, module, owner, out)
        for field_name, value in ast.iter_fields(node):
            for child in _iter_children(value):
                if id(child) in skip_ids:
                    continue
                _visit(child, module, class_name, owner, aliases, out)
        return

    for field_name, value in ast.iter_fields(node):
        for child in _iter_children(value):
            _visit(child, module, class_name, owner, aliases, out)


def discover_transit_candidates(root: Path) -> tuple[TransitCandidate, ...]:
    """Discover every risky call-site expression under `root`.

    `root` names a package directory (e.g. ``Path("src/mountainash")``);
    every ``*.py`` file beneath it is parsed and scanned.
    """
    candidates: list[TransitCandidate] = []
    for file_path in sorted(root.rglob("*.py")):
        source = file_path.read_text()
        tree = ast.parse(source, filename=str(file_path))
        module = _module_name(root, file_path)
        aliases = _AliasMap()
        aliases.collect(tree)
        _visit(tree, module, None, "<module>", aliases, candidates)
    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                *candidate.identity,
                candidate.wrapped,
                candidate.boundary_key or "",
            ),
        )
    )


def _candidate_error(candidate: TransitCandidate) -> str:
    observed_key = candidate.boundary_key if candidate.boundary_key is not None else "<none>"
    disposition = "wrapped" if candidate.wrapped else "direct"
    return (
        f"Unclassified {disposition} candidate {candidate.module}.{candidate.owner} "
        f"-> {candidate.callee}() [{candidate.fingerprint}], observed key "
        f"{observed_key!r}. Add a literal transit_call boundary, correct the key, "
        "or add an explicitly governed legacy exception."
    )


def build_inventory(root: Path) -> tuple[InventoryEntry, ...]:
    """Discover and classify every risky call site from canonical policy."""
    entries: list[InventoryEntry] = []
    for candidate in discover_transit_candidates(root):
        if candidate.wrapped:
            try:
                key = BoundaryKey[candidate.boundary_key]
                spec = BOUNDARY_REGISTRY[key]
            except (KeyError, TypeError) as exc:
                raise UnclassifiedCandidateError(_candidate_error(candidate)) from exc
            entry = InventoryEntry(
                module=candidate.module,
                owner=candidate.owner,
                callee=candidate.callee,
                fingerprint=candidate.fingerprint,
                boundary_key=key.name,
                transit_class=spec.transit_class.name,
                reason=spec.reason,
                since=spec.since.isoformat(),
                legacy_unwrapped=False,
            )
        else:
            disposition = LEGACY_UNWRAPPED.get(candidate.identity)
            if disposition is None:
                raise UnclassifiedCandidateError(_candidate_error(candidate))
            try:
                key = BoundaryKey[disposition.boundary_key]
                spec = BOUNDARY_REGISTRY[key]
            except (KeyError, TypeError) as exc:
                raise UnclassifiedCandidateError(_candidate_error(candidate)) from exc
            entry = InventoryEntry(
                module=candidate.module,
                owner=candidate.owner,
                callee=candidate.callee,
                fingerprint=candidate.fingerprint,
                boundary_key=key.name,
                transit_class=spec.transit_class.name,
                reason=disposition.reason,
                since=disposition.since,
                legacy_unwrapped=True,
            )
        entries.append(entry)
    return tuple(sorted(entries, key=lambda entry: entry.identity))


def render_inventory(entries: Sequence[InventoryEntry]) -> str:
    """Serialize inventory entries deterministically as JSON."""
    return json.dumps([asdict(entry) for entry in entries], indent=2) + "\n"


def load_inventory(path: Path) -> tuple[InventoryEntry, ...]:
    """Load the characterized inventory fixture."""
    raw = json.loads(path.read_text())
    return tuple(InventoryEntry(**entry) for entry in raw)
