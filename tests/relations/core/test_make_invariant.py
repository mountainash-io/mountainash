"""Enforce the _make invariant across the whole relation_api surface: no
type-eluding construction inside any instance method. Chaining and namespace
builders must go through self._make(...) / self._relation._make(...) so
subclasses (DAGRelation) survive every chained or dispatched call.

Forbidden inside an instance method body:
  * Relation(...) / DAGRelation(...)   — bare construction
  * type(self._relation)(...)          — reflective construction that drops
                                          the required dag arg on DAGRelation
"""
from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path

# NOTE: `relation_api/__init__.py` re-exports the module-level `relation()`
# factory function under the same name as the `relation` submodule
# (`from .relation import Relation, relation, concat`), which shadows the
# submodule attribute in the parent package's namespace. A plain
# `import mountainash...relation_api.relation as relation_mod` therefore
# binds to the *function*, not the module, and `Path(module.__file__)`
# below would blow up. `importlib.import_module` resolves via sys.modules
# by dotted name and is immune to that shadowing.
_API_BUILDERS_PKG = (
    "mountainash.relations.core.relation_api.api_builders"
)


def _discover_modules() -> list:
    """Every module whose instance methods can construct a relation and must
    therefore route through ``_make``.

    Explicitly: the ``relation`` and ``grouped_relation`` modules, plus EVERY
    module in the ``api_builders`` package — discovered programmatically so a
    future builder module cannot silently escape the scan (closed-by-default:
    the guardrail widens itself when the surface grows, never the reverse).
    """
    modules = [
        importlib.import_module(
            "mountainash.relations.core.relation_api.relation"
        ),
        importlib.import_module(
            "mountainash.relations.core.relation_api.grouped_relation"
        ),
    ]
    pkg = importlib.import_module(_API_BUILDERS_PKG)
    for info in pkgutil.iter_modules(pkg.__path__):
        modules.append(
            importlib.import_module(f"{_API_BUILDERS_PKG}.{info.name}")
        )
    return modules


_MODULES = _discover_modules()


def _is_forbidden_construction(call: ast.Call) -> bool:
    f = call.func
    # Relation(...) / DAGRelation(...)
    if isinstance(f, ast.Name) and f.id in ("Relation", "DAGRelation"):
        return True
    # type(self._relation)(...) — a Call whose func is itself type(...)
    if (
        isinstance(f, ast.Call)
        and isinstance(f.func, ast.Name)
        and f.func.id == "type"
    ):
        return True
    return False


def _offenders(module) -> list[str]:
    """'Class.method:lineno' for every forbidden construction lexically inside
    an instance method body (module-level functions are exempt).

    ``Relation._make`` itself is exempt: it is the single designated
    construction hook every other instance method must route through, so its
    own body is expected to contain the literal ``Relation(node)`` construction
    that subclasses (``DAGRelation``) override. The exemption is scoped to
    exactly ``Relation._make`` — a method named ``_make`` on any other class
    would still be scanned, so the exemption can never be widened by accident.
    """
    src = Path(module.__file__).read_text()
    tree = ast.parse(src)
    out: list[str] = []
    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        for fn in [n for n in cls.body if isinstance(n, ast.FunctionDef)]:
            if cls.name == "Relation" and fn.name == "_make":
                continue
            for call in ast.walk(fn):
                if isinstance(call, ast.Call) and _is_forbidden_construction(call):
                    out.append(f"{module.__name__}:{cls.name}.{fn.name}:{call.lineno}")
    return out


def test_scan_set_covers_known_construction_sites():
    """Guard the discovery itself: if the walk silently returned nothing (or
    dropped a known module), the main invariant test below would pass
    vacuously. Pin that the always-present construction sites are scanned."""
    scanned = {m.__name__.rsplit(".", 1)[-1] for m in _MODULES}
    required = {
        "relation",
        "grouped_relation",
        "rel_api_builder_base",
        "rel_bldr_projection",
    }
    missing = required - scanned
    assert not missing, f"invariant scan set is missing modules: {missing}"


def test_no_type_eluding_construction_in_instance_methods():
    offenders: list[str] = []
    for m in _MODULES:
        offenders += _offenders(m)
    assert offenders == [], (
        "Instance methods / builders must construct via self._make(...) or "
        "self._relation._make(...), never Relation(...)/DAGRelation(...)/"
        f"type(self._relation)(...), so DAGRelation survives. Offenders: {offenders}"
    )
