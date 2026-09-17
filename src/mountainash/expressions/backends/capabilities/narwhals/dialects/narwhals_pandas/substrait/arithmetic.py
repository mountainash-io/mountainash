"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import OperationTarget
from mountainash.core.capabilities.schema import Scenario

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.ARITHMETIC,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
                subject="overflow",
                selector=Selector(kind="exact", value="SATURATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
                subject="overflow",
                selector=Selector(kind="exact", value="SILENT"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            probe_exempt="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
                subject="overflow",
                selector=Selector(kind="exact", value="SATURATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
                subject="overflow",
                selector=Selector(kind="exact", value="SILENT"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            probe_exempt="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
                subject="overflow",
                selector=Selector(kind="exact", value="SATURATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
                subject="overflow",
                selector=Selector(kind="exact", value="SILENT"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            probe_exempt="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
                subject="overflow",
                selector=Selector(kind="exact", value="SATURATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
                subject="overflow",
                selector=Selector(kind="exact", value="SILENT"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            probe_exempt="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="overflow",
                selector=Selector(kind="exact", value="SATURATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="overflow",
                selector=Selector(kind="exact", value="SILENT"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
                subject="overflow",
                selector=Selector(kind="exact", value="SATURATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
                subject="overflow",
                selector=Selector(kind="exact", value="SILENT"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            probe_exempt="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE,
                subject="overflow",
                selector=Selector(kind="exact", value="SATURATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait integer overflow mode",
            workaround="Cast operands to a wider integer dtype before the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE,
                subject="overflow",
                selector=Selector(kind="exact", value="SILENT"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Cast operands to a wider integer dtype before the operation",
            probe_exempt="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,
                subject="overflow",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait i64 power overflow mode",
            workaround="Pre-check the i64 base and exponent and handle out-of-range powers before calling power()",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,
                subject="overflow",
                selector=Selector(kind="exact", value="SATURATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait i64 power overflow mode",
            workaround="Pre-check the i64 base and exponent and handle out-of-range powers before calling power()",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,
                subject="overflow",
                selector=Selector(kind="exact", value="SILENT"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="Explicit SILENT selects the native backend's i64 power wrapping behavior, so it is observably equivalent to omission and cannot discriminate",
            workaround="Pre-check the i64 base and exponent and handle out-of-range powers before calling power()",
            probe_exempt="The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="NAN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="NAN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="NAN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="NAN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="NAN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="NAN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="NAN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="NULL"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
            probe_exempt="The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="on_division_by_zero",
                selector=Selector(kind="exact", value="IEEE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="on_division_by_zero",
                selector=Selector(kind="exact", value="LIMIT"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="on_division_by_zero",
                selector=Selector(kind="exact", value="NULL"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
            probe_exempt="The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="on_division_by_zero",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
                subject="division_type",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
                subject="division_type",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
            probe_exempt="The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="NULL"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-21",
            message="The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
            probe_exempt="The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
                subject="on_domain_error",
                selector=Selector(kind="exact", value="ERROR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait arithmetic option semantics",
            workaround="Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS,
                subject="rounding",
                selector=Selector(kind="exact", value="CEILING"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS,
                subject="rounding",
                selector=Selector(kind="exact", value="FLOOR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_AWAY_FROM_ZERO"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS,
                subject="rounding",
                selector=Selector(kind="exact", value="TIE_TO_EVEN"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS,
                subject="rounding",
                selector=Selector(kind="exact", value="TRUNCATE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-21",
            message="The native backend does not implement the requested Substrait IEEE rounding mode",
            workaround="Evaluate with native rounding, then apply an explicit application-level numeric policy",
        ),
    ),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="pi/2"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+1"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="math.acosh(2.0)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="pi/2"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="math.asinh(1.0)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="pi/4"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "x",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "y",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="pi/2"),
                                CaptureValue(tag="float", value="0x0.0p+0"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p-1"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="math.atanh(0.5)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="text", value="pi/2"),
                                                CaptureValue(tag="text", value="pi"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="float", value="-0x1.0000000000000p+0"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                CaptureValue(tag="text", value="math.cosh(1.0)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="text", value="pi/2"),
                                                CaptureValue(tag="text", value="pi"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="float", value="0x1.6800000000000p+6"),
                                CaptureValue(tag="float", value="0x1.6800000000000p+7"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.6800000000000p+6"),
                                                CaptureValue(tag="float", value="0x1.6800000000000p+7"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="pi/2"),
                                CaptureValue(tag="text", value="pi"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="text", value="pi/2"),
                                                CaptureValue(tag="text", value="pi"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                CaptureValue(tag="float", value="0x0.0p+0"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="math.sinh(1.0)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="text", value="pi/4"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="math.tanh(1.0)"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="trig, angular, and hyperbolic functions raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for these math functions",
            issue="NW-MATH-10",
        ),
    ),
)
