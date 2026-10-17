"""Protect the qualified PostgreSQL null-on-invalid Decimal contract."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import Applicability, CoordinateConstraint, Region
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
    QualifiedInformationKey,
    Selector,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import (
    CapabilityIssueClass,
    CapabilityLevel,
    Clause,
    ClauseOp,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
    Predicate,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_VALUE

_SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-postgres"))
_KEY = CapabilityKey(FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST, "failure_behavior", Selector("predicate", Predicate((
    Clause("failure_behavior", ClauseOp.EQ, "null"),
))))
_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "ibis-framework", specifier="==12.0.0"),
    CoordinateConstraint("package", "sqlglot", specifier="==29.0.1"),
    CoordinateConstraint("engine", "postgres", specifier="==16.15"),
)),))
_MESSAGE = (
    "Ibis 12.0.0 with SQLGlot 29.0.1 on PostgreSQL 16.15 lowers TryCast to a strict cast; "
    "Decimal failure_behavior='null' cannot return null for invalid text. "
    "This mode is refused even for valid inputs; use failure_behavior='throw' for strict conversion."
)

SEGMENT = CapabilitySegment(
    domain=Domain.VALUE,
    information=(CapabilityInformation(
        key=_KEY,
        layer=InformationLayer.PUBLIC,
        level=CapabilityLevel.UNSUPPORTED,
        message=_MESSAGE,
        issue="IB-CAST-04",
        applicability=_APPLICABILITY,
    ),),
    policies=(CapabilityPolicyRule(
        key=_KEY,
        level=CapabilityLevel.UNSUPPORTED,
        message=_MESSAGE,
        consumer=PolicyConsumer.GATE,
        action=PolicyAction.BLOCK,
        information=QualifiedInformationKey(_SCOPE, _KEY, InformationLayer.PUBLIC),
        applicability=_APPLICABILITY,
        issue_classes=frozenset({CapabilityIssueClass.SEMANTICS}),
    ),),
)
