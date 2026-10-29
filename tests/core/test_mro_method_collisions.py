"""Fail-closed guard on the visitor's getattr-by-name dispatch.

The unified visitor resolves a backend method by the BARE name
`protocol_method.__name__` and calls `getattr(backend, name)` on the
composed ExpressionSystem. If two DIFFERENT protocol methods (declared on
different protocol classes) share that bare name, every FKEY bound to the
MRO-losing protocol silently dispatches to the winner's impl — exactly
the datetime `round`/`ceil`/`floor` vs numeric-rounding `round`/`ceil`/`floor`
collision this plan fixes.

We audit only the getattr-dispatched universe (the names the registry
actually resolves through), so non-dispatched method-name overlaps are
out of scope by construction. Any NEW ambiguity fails closed; a known-safe
pre-existing ambiguity — where the colliding protocols resolve to the SAME
underlying impl because the MA extension system is the Substrait system
re-exported under an alias — is listed in `_ALIAS_SAFE` with its reason.
"""
from __future__ import annotations

from collections import defaultdict

from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)

# Pre-existing bare-name overlaps proven SAFE: the colliding protocol
# methods resolve to ONE impl (alias re-export — see
# `backends/expression_systems/<backend>/__init__.py`). Each entry MUST
# carry a reason. A genuinely divergent overlap does NOT belong here —
# file backlog `audit-mro-dispatch-collisions` and rename. Populated in
# Step 8's classification.
_ALIAS_SAFE: dict[str, str] = {}


def test_no_dispatched_protocol_method_name_is_ambiguous() -> None:
    by_name: dict[str, set[str]] = defaultdict(set)
    for fkey in ExpressionFunctionRegistry.list_all():
        pm = ExpressionFunctionRegistry.get_protocol_method(fkey)
        if pm is None:  # missing-op FKEYs carry no protocol method
            continue
        by_name[pm.__name__].add(pm.__qualname__)  # __qualname__ includes declaring class
    ambiguous = {
        name: sorted(quals)
        for name, quals in by_name.items()
        if len(quals) > 1 and name not in _ALIAS_SAFE
    }
    assert not ambiguous, (
        "FKEYs dispatch these bare method names through >1 distinct protocol "
        f"(ambiguous getattr-by-name resolution): {ambiguous}. Rename to a "
        "unique name (see the datetime *_dt fix) or, if the colliding "
        "protocols resolve to the same impl via alias, add the name to "
        "_ALIAS_SAFE with a reason."
    )
