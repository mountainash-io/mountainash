"""Closed build-time classifier for ``is_in`` / ``t_is_in`` membership arguments.

Implements the §4.1 structural disambiguation rule: classify the collection
argument **purely by Python argument TYPE** — no backend, no dtype, no
schema introspection. The classifier is the single correctness heart of the
membership unification; it maps a variadic ``args`` tuple to a canonical list
of member objects (preserving source order for list/tuple, sorting by
``(table_rank, value)`` for set/frozenset) or raises a typed build error for
any ambiguous, nested, empty, or unsupported shape.

Decision tree (per spec §4.1):
    * ``len(args) == 0`` or an empty container → ``[]`` (vacuously-false membership)
    * 1 arg, MA or backend-native expression → :class:`BareExpressionCollectionError`
    * 1 arg, container (exact ``list``/``tuple``/``set``/``frozenset``) → flatten to items
    * 1 arg, unsupported iterable (``ndarray``/``Mapping``/duck-typed) → :class:`UnsupportedCollectionError`
    * 1 arg, scalar literal → 1-element list
    * 2+ args → element-set (no flattening of nested containers)

After shape resolution, :func:`_validate_members` checks each member:
    * nested container or unsupported iterable → :class:`NestedCollectionError`
    * native expression → :class:`NativeExprMemberError` (member-context)
    * MA expression or scalar → OK

For a single ``set``/``frozenset``, :func:`_canonical_set` enforces the closed
ordering table ``(bool, int, float, str, bytes)`` sorted by
``(table_rank, value)``. It rejects NaN and any out-of-table type
(``Decimal``/``date``/``datetime``/``enum``/NumPy scalar) inside set/frozenset
form with :class:`UnsupportedCollectionError` — those types are accepted
**only** in ``list``/``tuple`` form.
"""
from __future__ import annotations

import enum
import math
from collections.abc import Mapping
from typing import Any

from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
from mountainash.expressions.core.expression_nodes.substrait.exn_base import ExpressionNode

from .errors import (
    BareExpressionCollectionError,
    NativeExprMemberError,
    NestedCollectionError,
    UnsupportedCollectionError,
)
from .native_expr import is_backend_native_expression


_CONTAINER_TYPES = (list, tuple, set, frozenset)
# Closed ordering table: (bool, int, float, str, bytes) — the only types
# accepted inside a `set` / `frozenset`. Types outside this table
# (`Decimal`, `date`, `datetime`, `enum`, NumPy scalar, `None`, custom
# objects) are accepted only in `list` / `tuple` form (brief §12.4).
_SCALAR_TABLE_TYPES = (bool, int, float, str, bytes)
_SCALAR_TABLE_RANK = {t: i for i, t in enumerate(_SCALAR_TABLE_TYPES)}


def _is_container(x: Any) -> bool:
    """True iff ``type(x)`` is exactly one of ``list``/``tuple``/``set``/``frozenset``.

    Subclasses (including ``namedtuple``) and duck-typed iterables are
    intentionally **excluded** — they fall into the unsupported-iterable path
    below or the scalar path; they are never silently treated as collections.
    """
    return type(x) in _CONTAINER_TYPES


def _is_expression(x: Any) -> bool:
    """True iff ``x`` is a MA expression (``BaseExpressionAPI``/``ExpressionNode``)
    or a backend-native expression (polars/narwhals/ibis)."""
    if isinstance(x, (BaseExpressionAPI, ExpressionNode)):
        return True
    return is_backend_native_expression(x)


def _is_unsupported_iterable(x: Any) -> bool:
    """True iff ``x`` is iterable but not a supported container/str/bytes/expression.

    Detects by **type**, never by calling ``iter(x)``: a 0-d numpy array
    raises ``TypeError`` under ``iter()`` and the rev-1 ``except TypeError:
    return False`` mis-classified it as a scalar. We check explicit types
    (``ndarray``, ``Mapping``) first, then fall back to a duck-typed probe
    on ``__iter__``/``__getitem__`` to catch generators, ``Series``,
    ``dict_keys``, ``range``, namedtuples, list/tuple subclasses, etc.

    Excluded from the "unsupported iterable" verdict (treated as scalars):
    * NumPy scalar types (``np.int64``, ``np.float64``, …) — have
      ``__getitem__`` on the type via inheritance, but are genuinely scalar
    * ``enum.Enum`` members — the *class* is iterable but members are scalars
    """
    if isinstance(x, (str, bytes)) or _is_container(x) or _is_expression(x):
        return False
    if isinstance(x, enum.Enum):
        return False
    try:
        import numpy as np

        if isinstance(x, np.ndarray):  # incl. 0-d → unsupported
            return True
        if isinstance(x, np.generic):  # NumPy scalar → not an iterable
            return False
    except ImportError:
        pass
    if isinstance(x, Mapping):
        return True
    # duck-typed iterables (generator, Series, dict_keys, namedtuple, range, …)
    if hasattr(type(x), "__iter__") or hasattr(type(x), "__getitem__"):
        return True
    return False  # genuinely non-iterable → scalar member


def _canonical_set(members: list) -> list:
    """Canonicalise a set/frozenset's members via the closed ordering table.

    Closed table: ``(bool, int, float, str, bytes)`` — the only types
    accepted inside a ``set`` / ``frozenset``. Sort key is
    ``(table_rank, value)`` where ``table_rank`` is the position in the
    closed table (bool < int < float < str < bytes) and ``value`` is the
    member's natural comparison key. Rejects:
        * NaN (float comparison is undefined)
        * any out-of-table type (``Decimal``, ``date``, ``datetime``, ``enum``,
          NumPy scalars, ``None``, custom objects) — those are accepted only
          in ``list``/``tuple`` form per spec §12.4 + Minor M-set.

    The type check is **exact** (``type(m) in _SCALAR_TABLE_TYPES``) rather
    than ``isinstance`` because numpy 2.x makes ``np.float64`` a subclass of
    ``float`` (but not ``np.int64`` a subclass of ``int``), so ``isinstance``
    would inconsistently allow numpy floats while excluding numpy ints. Exact
    type is the only way to get a stable closed table.

    Raises:
        UnsupportedCollectionError: if any member is out-of-table or NaN.
    """
    for m in members:
        if type(m) not in _SCALAR_TABLE_RANK:  # noqa: E721 — exact type is intentional
            raise UnsupportedCollectionError(m)
        if type(m) is float and math.isnan(m):  # noqa: E721 — exact type rejects np.float64
            raise UnsupportedCollectionError(m)
    return sorted(members, key=lambda x: (_SCALAR_TABLE_RANK[type(x)], x))


def _validate_members(members: list) -> None:
    """Validate each member of a resolved collection; raise typed errors.

    * Nested container or unsupported-iterable member → :class:`NestedCollectionError`
    * Backend-native expression member → :class:`NativeExprMemberError`
      (member-context message; brief §12.7)
    * MA expression (``BaseExpressionAPI``/``ExpressionNode``) → OK
    * scalar literal → OK
    """
    for m in members:
        if _is_container(m) or _is_unsupported_iterable(m):
            raise NestedCollectionError(m)
        if is_backend_native_expression(m):
            raise NativeExprMemberError(m)


def classify_members(args: tuple) -> list:
    """Classify a membership call's collection argument(s) into a canonical member list.

    Pure, build-time, no backend/dtype/schema introspection. Implements the
    §4.1 structural disambiguation rule (single source of truth for both
    boolean ``is_in``/``is_not_in`` and ternary ``t_is_in``/``t_is_not_in``).

    Args:
        args: The post-needle variadic collection arguments. Accepts:

            * ``()`` — no collection (empty)
            * ``(coll,)`` — a single collection argument
            * ``(a, b, …)`` — 2+ element-set members

    Returns:
        A list of member objects in canonical order:

            * source order for ``list``/``tuple`` containers and multi-arg
            * sorted by ``(table_rank, value)`` for ``set``/``frozenset``

    Returns ``[]`` for an empty collection (no args, or an empty container) —
    a vacuously-false membership test, not an error.

    Raises:
        BareExpressionCollectionError: a single MA or backend-native
            expression was passed as the *entire* collection. Use
            ``.list.contains()`` / ``.list.t_contains()`` instead.
        UnsupportedCollectionError: a single unsupported iterable
            (``ndarray``, ``Mapping``, generator, ``Series``, ``dict_keys``,
            ``range``, namedtuple, list/tuple subclasses, etc.) was passed
            as the collection, or a set/frozenset contains an out-of-table
            member (NaN, ``Decimal``, ``date``, ``datetime``, ``enum``,
            NumPy scalar, ``None``, custom object).
        NestedCollectionError: a resolved member is itself a container or
            unsupported iterable.
        NativeExprMemberError: a resolved member is a backend-native
            expression (use ``ma.col()`` / ``ma.lit()`` to wrap).
    """
    if not args:
        # Empty collection is a valid, vacuously-false membership test
        # (SQL `x IN ()` is FALSE); the backend kernels short-circuit it.
        return []

    if len(args) == 1:
        arg = args[0]
        if _is_expression(arg):
            raise BareExpressionCollectionError(arg)
        if _is_container(arg):
            members = list(arg)
        elif _is_unsupported_iterable(arg):
            raise UnsupportedCollectionError(arg)
        else:
            members = [arg]
    else:
        members = list(args)

    if not members:
        # Empty container (e.g. is_in([]) / is_in(set())) → vacuously false.
        return []

    _validate_members(members)

    if len(args) == 1 and type(args[0]) in (set, frozenset):
        return _canonical_set(members)

    return members
