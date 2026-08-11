"""Direct regression coverage for `_param_name_for` (visitor.py).

Backlog item 61 generalized `_param_name_for` to map ANY protocol-argument
index at or beyond the VAR_POSITIONAL parameter's position to that
parameter's name — not just an index that exactly matches the LAST protocol
parameter, as the pre-fix algorithm required. The pre-fix algorithm already
silently mis-mapped `is_in`'s (and siblings') 3rd+ variadic argument today
(harmless only because no CapabilityFact was registered against the wrong
names it produced); `concat`'s new `(*input, null_handling=None)` shape
(added in a later task of this same item) is the first protocol signature to
combine a VAR_POSITIONAL parameter with a trailing named parameter, which the
pre-fix algorithm could not handle at all.
"""
from __future__ import annotations

import inspect

import pytest

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash.prtcl_expsys_ext_ma_scalar_set import (
    SubstraitScalarSetExpressionSystemProtocol,
)
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash.prtcl_expsys_ext_ma_scalar_ternary import (
    MountainAshScalarTernaryExpressionSystemProtocol,
)
from mountainash.expressions.core.unified_visitor.visitor import (
    _param_name_for,
    _protocol_sig_params,
)


def _old_param_name_for(sig_params: tuple, index: int) -> str | None:
    """The pre-fix algorithm, preserved ONLY to prove the regression this fix
    corrects — mirrors the exact code this task replaces in visitor.py.
    NEVER call this outside a test."""
    if index < len(sig_params):
        return sig_params[index].name
    if sig_params and sig_params[-1].kind is inspect.Parameter.VAR_POSITIONAL:
        return sig_params[-1].name
    return None


# (protocol_method, {index: expected_NEW_mapping}, {index: expected_OLD_mapping})
# 5 indices (0-4) exercise a needle/element + 4 variadic members each — enough
# to walk past both trailing keyword-only params (unknown_values,
# member_unknown_values) the old algorithm mis-mapped onto.
_CASES = [
    pytest.param(
        SubstraitScalarSetExpressionSystemProtocol.is_in,
        {0: "needle", 1: "haystack", 2: "haystack", 3: "haystack", 4: "haystack"},
        {0: "needle", 1: "haystack", 2: "unknown_values", 3: "member_unknown_values", 4: None},
        id="is_in",
    ),
    pytest.param(
        SubstraitScalarSetExpressionSystemProtocol.is_not_in,
        {0: "needle", 1: "haystack", 2: "haystack", 3: "haystack", 4: "haystack"},
        {0: "needle", 1: "haystack", 2: "unknown_values", 3: "member_unknown_values", 4: None},
        id="is_not_in",
    ),
    pytest.param(
        MountainAshScalarTernaryExpressionSystemProtocol.t_is_in,
        {0: "element", 1: "members", 2: "members", 3: "members", 4: "members"},
        {0: "element", 1: "members", 2: "unknown_values", 3: "member_unknown_values", 4: None},
        id="t_is_in",
    ),
    pytest.param(
        MountainAshScalarTernaryExpressionSystemProtocol.t_is_not_in,
        {0: "element", 1: "members", 2: "members", 3: "members", 4: "members"},
        {0: "element", 1: "members", 2: "unknown_values", 3: "member_unknown_values", 4: None},
        id="t_is_not_in",
    ),
]


@pytest.mark.parametrize("protocol_method,expected_new,expected_old", _CASES)
def test_param_name_for_maps_every_variadic_index_to_the_var_positional_name(
    protocol_method, expected_new, expected_old
) -> None:
    """The fixed algorithm: every index at/after VAR_POSITIONAL maps to its name."""
    sig_params = _protocol_sig_params(protocol_method)
    for index, expected in expected_new.items():
        assert _param_name_for(sig_params, index) == expected, (
            f"{protocol_method.__qualname__} index {index}: expected {expected!r}"
        )


@pytest.mark.parametrize("protocol_method,expected_new,expected_old", _CASES)
def test_old_algorithm_mis_mapped_trailing_variadic_arguments(
    protocol_method, expected_new, expected_old
) -> None:
    """Proves the regression: with 4+ variadic arguments, the pre-fix
    algorithm mis-mapped every index beyond the first two — silently, with no
    error, which is exactly why it went undetected before this item."""
    sig_params = _protocol_sig_params(protocol_method)
    for index, expected in expected_old.items():
        assert _old_param_name_for(sig_params, index) == expected, (
            f"{protocol_method.__qualname__} index {index}: expected "
            f"pre-fix (buggy) mapping {expected!r}"
        )
