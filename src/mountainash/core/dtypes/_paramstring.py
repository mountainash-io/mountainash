"""Shared safe parser for constructor-call-style dtype repr strings.

Polars and Narwhals dtype reprs (``str(pl.Datetime(time_unit='us',
time_zone='UTC'))``, ``str(pl.List(pl.Int64))``,
``str(nw.Enum(categories=['a','b']))``) are valid Python constructor-call
syntax against their own module namespace. This walks the AST and evaluates
ONLY a bounded grammar — a bare Name (resolved against ``namespace``), or a
Call(Name, *args, **kwargs) whose arguments are themselves only
Constant / Name (resolved against the SAME ``namespace``) / list[arg] /
tuple[arg] — before ever calling ``eval()``. Anything else (attribute access,
subscripts, comprehensions, imports, starred/double-starred unpacking,
arbitrary calls) is rejected before eval ever runs.

GLM-5.2 review (2026-08-16) Critical finding: an earlier draft's
``_safe_literal`` accepted only Constant/List/Tuple, rejecting a bare
``Name`` inside ``args`` — which broke ``List(Int64)`` and
``Array(Int64, shape=(5,))``, the exact motivating round-trip cases
(``Int64``/``shape`` values are bare Names in the AST, not Constants). Fixed
here: a Name node inside an argument position resolves against the same
closed ``namespace`` the top-level Call already validated against — never a
wider lookup.
"""
from __future__ import annotations

import ast
from typing import Any, Mapping, Optional


def _safe_arg(node: ast.AST, namespace: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in namespace:
            raise ValueError(f"name {node.id!r} not in whitelist")
        return namespace[node.id]
    if isinstance(node, (ast.List, ast.Tuple)):
        vals = [_safe_arg(e, namespace) for e in node.elts]
        return vals if isinstance(node, ast.List) else tuple(vals)
    raise ValueError(f"unsupported argument node: {ast.dump(node)}")


def parse_constructor_repr(s: str, namespace: Mapping[str, Any]) -> Optional[Any]:
    """Parse `s` as a bare name or constructor call against `namespace`.

    Returns the constructed value, or None if `s` doesn't match the bounded
    grammar or references a name outside `namespace`. Never calls eval()/exec()
    on unvalidated input — the AST is walked and every node type-checked first.

    Note: `**dict`-unpacked keywords (`ast.keyword(arg=None)`, e.g.
    `Datetime(**{'time_zone': 'UTC'})`) are deliberately DROPPED, not rejected —
    real Polars/Narwhals `str()` output never emits this form, so it is
    robustness-only; §7.2 adversarially tests that the drop (not a silent
    wrong-value construction) is what happens.
    """
    try:
        tree = ast.parse(s, mode="eval")
    except SyntaxError:
        return None
    node = tree.body

    if isinstance(node, ast.Name):
        return namespace.get(node.id)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in namespace:
            return None
        target = namespace[node.func.id]
        try:
            args = [_safe_arg(a, namespace) for a in node.args]
            kwargs = {
                kw.arg: _safe_arg(kw.value, namespace)
                for kw in node.keywords if kw.arg  # kw.arg is None for **unpack — dropped
            }
        except ValueError:
            return None
        try:
            return target(*args, **kwargs)
        except Exception:
            return None

    return None
