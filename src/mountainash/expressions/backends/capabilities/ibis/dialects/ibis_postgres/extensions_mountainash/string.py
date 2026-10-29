"""Protect the qualified PostgreSQL dynamic-insensitive regex compiler defect."""

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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING

_SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-postgres"))
_KEY = CapabilityKey(FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS, "pattern", Selector("predicate", Predicate((
    Clause("pattern", ClauseOp.IS_DYNAMIC),
    Clause("case_sensitivity", ClauseOp.EQ, "CASE_INSENSITIVE"),
))))
_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "ibis-framework", specifier="==12.0.0"),
    CoordinateConstraint("package", "sqlglot", specifier="==29.0.1"),
    CoordinateConstraint("engine", "postgres", specifier="==16.15"),
)),))
_MESSAGE = (
    "Ibis 12.0.0 with SQLGlot 29.0.1 on PostgreSQL 16.15 loses pattern-concatenation "
    "grouping for dynamic case-insensitive regex matching."
)

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    information=(CapabilityInformation(
        key=_KEY,
        layer=InformationLayer.NATIVE,
        level=CapabilityLevel.UNSUPPORTED,
        message=_MESSAGE,
        issue="IB-STR-16",
        applicability=_APPLICABILITY,
    ),),
    policies=(CapabilityPolicyRule(
        key=_KEY,
        level=CapabilityLevel.UNSUPPORTED,
        message=_MESSAGE,
        consumer=PolicyConsumer.GATE,
        action=PolicyAction.BLOCK,
        information=QualifiedInformationKey(_SCOPE, _KEY, InformationLayer.NATIVE),
        applicability=_APPLICABILITY,
        issue_classes=frozenset({CapabilityIssueClass.SEMANTICS}),
    ),),
)
