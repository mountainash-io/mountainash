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
from pathlib import Path

# NOTE: `relation_api/__init__.py` re-exports the module-level `relation()`
# factory function under the same name as the `relation` submodule
# (`from .relation import Relation, relation, concat`), which shadows the
# submodule attribute in the parent package's namespace. A plain
# `import mountainash...relation_api.relation as relation_mod` therefore
# binds to the *function*, not the module, and `Path(module.__file__)`
# below would blow up. `importlib.import_module` resolves via sys.modules
# by dotted name and is immune to that shadowing.
relation_mod = importlib.import_module(
    "mountainash.relations.core.relation_api.relation"
)
grouped_mod = importlib.import_module(
    "mountainash.relations.core.relation_api.grouped_relation"
)
rel_api_builder_base = importlib.import_module(
    "mountainash.relations.core.relation_api.api_builders.rel_api_builder_base"
)
rel_bldr_projection = importlib.import_module(
    "mountainash.relations.core.relation_api.api_builders.rel_bldr_projection"
)

_MODULES = [relation_mod, grouped_mod, rel_api_builder_base, rel_bldr_projection]


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


def test_no_type_eluding_construction_in_instance_methods():
    offenders: list[str] = []
    for m in _MODULES:
        offenders += _offenders(m)
    assert offenders == [], (
        "Instance methods / builders must construct via self._make(...) or "
        "self._relation._make(...), never Relation(...)/DAGRelation(...)/"
        f"type(self._relation)(...), so DAGRelation survives. Offenders: {offenders}"
    )
