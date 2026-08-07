"""Coverage model for the expression coverage report (spec 2026-08-07 rev 3).

PURE over explicit inputs: no registry imports, no autoload, no wall clock.
Input gathering lives in render_markdown.gather_coverage_inputs().
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mountainash.core.capabilities.declarations import (
    Domain,
    FactSource,
    classify_domain,
    classify_source,
)


@dataclass(frozen=True)
class OpRecord:
    """One registered operation: the enum member and its enum class name."""

    operation_key: Any
    family: str


@dataclass(frozen=True)
class UnregisteredOp:
    """A key-enum member deliberately absent from the operation registries."""

    family: str
    member: str
    reason: str
    since: str  # YYYY-MM-DD


_UNREGISTERED_OPS: tuple[UnregisteredOp, ...] = (
    # AST-level composition — method body builds ScalarFunctionNode trees from
    # registered primitives (EQUAL / IS_NULL / AND / OR / NOT); the enum
    # member is not itself a ScalarFunction dispatch key.
    UnregisteredOp(
        family="FKEY_MOUNTAINASH_SCALAR_COMPARISON",
        member="EQ_MISSING",
        reason="AST-level composition in api_bldr_ext_ma_scalar_comparison.eq_missing "
               "(composes EQUAL, IS_NULL, AND, OR) — no ScalarFunctionNode dispatch",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_MOUNTAINASH_SCALAR_COMPARISON",
        member="NE_MISSING",
        reason="AST-level composition in api_bldr_ext_ma_scalar_comparison.ne_missing "
               "(composes EQUAL, IS_NULL, AND, OR, NOT) — no ScalarFunctionNode dispatch",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_MOUNTAINASH_SCALAR_COMPARISON",
        member="IS_CLOSE",
        reason="AST-level composition in api_bldr_ext_ma_scalar_comparison.is_close "
               "(composes SUBTRACT, ABS, MULTIPLY, ADD, LTE) — no ScalarFunctionNode dispatch",
        since="2026-08-07",
    ),
    # Reserved / un-implemented members — defined on the enum but no API
    # builder, no registry def, no source-code usages anywhere in src/.
    UnregisteredOp(
        family="FKEY_MOUNTAINASH_NULL",
        member="ALWAYS_NULL",
        reason="enum member defined with a string value but no API builder method, "
               "no registry entry, and no source-code usages — reserved for a "
               "future null-literal op",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_SCALAR_AGGREGATE",
        member="STRING_AGG",
        reason="enum member defined but no API builder, no registry def, and no "
               "source-code usages — string aggregate not yet wired",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_SCALAR_AGGREGATE",
        member="SUM0",
        reason="enum member referenced only as a fixture in "
               "tests/expressions/argument_types/test_arg_types_aggregate.py — no "
               "API builder, no registry def, no source-code implementation",
        since="2026-08-07",
    ),
    # Duplicate names — the live dispatch key lives on a different family.
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_SCALAR_BOOLEAN",
        member="IS_TRUE",
        reason="duplicate of FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_TRUE, which is the "
               "registered dispatch key; the boolean-family member has no source-code usages",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_SCALAR_BOOLEAN",
        member="IS_FALSE",
        reason="duplicate of FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FALSE, which is the "
               "registered dispatch key; the boolean-family member has no source-code usages",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_SCALAR_STRING",
        member="REGEXP_CONTAINS",
        reason="duplicate of FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS (singular "
               "REGEX), which is the registered mountainash extension; the "
               "substrait-family plural member has no source-code usages",
        since="2026-08-07",
    ),
    # Special node constructors — handled by FieldReferenceNode / LiteralNode
    # rather than ScalarFunctionNode, per the comment in
    # function_mapping/definitions.py ("col and lit are handled specially ...
    # not ScalarFunctionNode. They don't need registry entries.").
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_FIELD_REFERENCE",
        member="COL",
        reason="FieldReferenceNode constructor — col() is a dedicated node type, "
               "not a ScalarFunctionNode dispatch key (per definitions.py line 95)",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_LITERAL",
        member="CAST",
        reason="LiteralNode constructor — lit() is a dedicated node type, not a "
               "ScalarFunctionNode dispatch key (per definitions.py line 95); the "
               "registered type-cast op is FKEY_SUBSTRAIT_CAST.CAST",
        since="2026-08-07",
    ),
)


def audit_domain_for(operation_key: Any) -> tuple[FactSource, Domain] | None:
    """(source, domain) audit coordinates for an op, or None if unmapped.

    Mirrors the declaration-registration validators exactly (spec §3.2): this
    is the SAME classify_source/classify_domain the registry uses, wrapped to
    be total. None means the op's enum class has no declaration domain yet
    (e.g. SUBSTRAIT_ARITHMETIC_WINDOW) — rendered as UNDECLARED, never an error.
    """
    try:
        return (classify_source(operation_key), classify_domain(operation_key))
    except ValueError:
        return None
