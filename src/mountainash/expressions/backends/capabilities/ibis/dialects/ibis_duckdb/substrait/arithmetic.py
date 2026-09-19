"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations


from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.ARITHMETIC,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
            layer=InformationLayer.NATIVE,
        ),
    ),
)
