"""Build-time predicate for backend-native expression objects.

``is_backend_native_expression(x)`` returns ``True`` for polars ``Expr``,
narwhals ``Expr``/``Series``, and ibis ``Expr``/``Deferred``; ``False``
for all other values (scalars, mountainash types, containers, str/bytes).
All backend imports are lazy — the predicate works with any subset installed.
"""

from __future__ import annotations

from typing import Any


def is_backend_native_expression(x: Any) -> bool:
    """Return True if *x* is a backend-native expression object.

    Checks against polars ``Expr``, narwhals ``Expr``/``Series``, and
    ibis ``Expr``/``Deferred`` via lazy optional imports.  Returns False
    for all other values.
    """
    try:
        import polars as pl

        if isinstance(x, pl.Expr):
            return True
    except ImportError:
        pass

    try:
        import narwhals as nw

        if isinstance(x, (nw.Expr, nw.Series)):
            return True
    except ImportError:
        pass

    try:
        import ibis.expr.types as ir
        import ibis.common.deferred as idd

        if isinstance(x, (ir.Expr, idd.Deferred)):
            return True
    except ImportError:
        pass

    return False
