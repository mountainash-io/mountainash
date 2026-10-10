"""Mountainash cast surface: adds ``rounding=`` for ``DecimalDtype`` targets.

Takes over the flat ``.cast`` name through extension-first lookup (``_FLAT_NAMESPACES``).
A ``DecimalDtype`` target builds the Mountainash ``DECIMAL_CAST`` node; every other target
builds the unchanged Substrait ``CastNode``, the same way extension aliases build Substrait
nodes (short-aliases principle: the function key decides the operation's domain).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from mountainash.core.dtypes import DecimalDtype, parse_cast_target
from mountainash.expressions.core.expression_api.api_builders.api_builder_base import (
    BaseExpressionAPIBuilder,
)
from mountainash.expressions.core.expression_nodes import CastNode, ScalarFunctionNode
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import (
    MountainAshCastAPIBuilderProtocol,
)
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
    CaseFailureBehaviour,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_VALUE,
)

from ._operation_options import invalid

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI

ROUNDING_MODES = ("half_to_even", "half_away_from_zero", "to_zero")
# R20: the intermediate keeps one spare integer digit and one spare fractional digit beyond the
# target only while precision <= 36 (a precision-38 intermediate has no room above that).
MAX_CAST_PRECISION = 36


class MountainAshCastAPIBuilder(BaseExpressionAPIBuilder, MountainAshCastAPIBuilderProtocol):
    """``.cast`` with an explicit rounding mode for decimal targets."""

    def cast(
        self,
        dtype: Union[str, type, Any],
        *,
        failure_behavior: Optional[CaseFailureBehaviour] = CaseFailureBehaviour.THROW,
        rounding: Optional[str] = None,
    ) -> BaseExpressionAPI:
        """Cast to ``dtype``.

        Args:
            dtype: Target type: a canonical name or Python type, a ``DecimalDtype``,
                or a native backend dtype.
            failure_behavior: ``"throw"`` raises on invalid input (default); ``"null"``
                returns null for invalid input.
            rounding: ``"half_to_even"``, ``"half_away_from_zero"`` or ``"to_zero"``.
                Required when ``dtype`` is a ``DecimalDtype``; rejected otherwise.

        Integer-part overflow after rounding always raises, under both failure behaviours.
        """
        target = parse_cast_target(dtype)
        try:
            fb = CaseFailureBehaviour(failure_behavior).value
        except ValueError:
            invalid("cast", "failure_behavior", f"{failure_behavior!r} is not one of 'throw', 'null'")

        if not isinstance(target, DecimalDtype):
            if rounding is not None:
                invalid("cast", "rounding", "only valid for DecimalDtype targets")
            # Same node as SubstraitCastAPIBuilder.cast (api_bldr_cast.py); keep the two in sync.
            return self._build(CastNode(input=self._node, target_type=target, failure_behavior=fb))

        modes = ", ".join(ROUNDING_MODES)
        if rounding is None:
            invalid("cast", "rounding", f"required for DecimalDtype targets: one of {modes}")
        if rounding not in ROUNDING_MODES:
            invalid("cast", "rounding", f"{rounding!r} is not one of {modes}")
        if target.precision > MAX_CAST_PRECISION:
            invalid(
                "cast",
                "dtype",
                f"decimal cast targets support precision <= {MAX_CAST_PRECISION}, got {target.precision}",
            )
        return self._build(
            ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST,
                arguments=[self._node],
                options={
                    "precision": target.precision,
                    "scale": target.scale,
                    "rounding": rounding,
                    "failure_behavior": fb,
                },
            )
        )
