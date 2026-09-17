"""Closed migration census — the SCOPE authority for spine-derived test
expectations (spec 2026-08-01-spine-derived-test-expectations §3, Task 5).

``build_census()`` enumerates an **independent, closed** scope of every
capability-encoding expectation site and classifies each into exactly one
bucket, with an explicit reason. The scope is three families:

  (a) pytest collection metadata for every parametrized whole-operation gate
      case in the op-level gate-probe suite;
  (b) the **raw forms being migrated** — every ``pytest.xfail(`` call and every
      *capability-encoding* ``pytest.mark.xfail`` / ``xfail_divergence`` marker,
      discovered structurally via the :mod:`ast` module; and
  (c) each registered physical segment source row for a whole-operation build
      gate, addressed by its own module and local origin rather than an old
      declaration assignment line.

Classification is total over the discovered scope:

  * a fact selected by :func:`capability_gate` / an id-keyed divergence, or a
    marker whose reason is *built from* a spine ``CapabilityFact`` → ``migrated``;
  * a ``LITERAL_ONLY`` / ``ROUTER_METADATA`` fact → ``retained``;
  * a capability-shaped raw form with no matching fact → ``inventoried`` (the
    ``UNRESOLVED`` sentinel fills any selector that genuinely cannot be
    recovered statically — it is never guessed);
  * a curated non-capability predicate (explicit per-family reasons) →
    ``non-capability``.

An expectation-producing call whose *form* the census cannot parse at all
raises :class:`UnclassifiedExpectation` — a census failure, never a silent
omission (closed-by-default, rev-2 I6).

Entries are emitted in deterministic ``(path, address)`` order and
``build_census`` also writes the committed catalogue
``tests/_spine_expectation_census.md`` that Task 6's inventory and SP2 read.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mountainash.core.capabilities.declarations import LocalOrigin
from mountainash.core.capabilities.divergences import divergence_by_id
from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityLevel,
    Enforcement,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from tests.fixtures.capability_gating import (
    capability_gate,
    identity_for,
    whole_operation_gates,
)

# The sentinel used wherever a selector genuinely cannot be recovered from a
# static site — NEVER a guess. A sentinel is a non-empty, non-None string, so an
# ``inventoried``/``migrated`` entry that carries it still satisfies the
# "needs op+backend" contract while remaining honestly unresolved.
UNRESOLVED = "UNRESOLVED"

VALID_BUCKETS = ("migrated", "retained", "inventoried", "non-capability")

_TESTS_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _TESTS_DIR.parent
_REPORT_PATH = _TESTS_DIR / "_spine_expectation_census.md"

# The known-expectation-API provider (scope a) derives its parametrized
# runtime variants from canonical operation enums and the scoped registry,
# crossed with this suite's fixture matrix.
_PROBE_REL = "tests/expressions/argument_types/test_op_level_gate_probes.py"

# Roots that identify a reason built from a live spine object (→ migrated).
_SPINE_REFS = frozenset({"fact", "limitation", "residue", "wildcard_residue", "divergence"})

# A ``pytest.mark.xfail`` marker is capability-encoding (scope b, marker family)
# on a STRUCTURAL signal, not incidental reason wording: its ``raises=`` argument
# is (or includes) ``BackendCapabilityError`` — the spine's own gate error — or
# its reason is built from a live spine object (see ``_SPINE_REFS``). A bare
# native-exception marker (``NotImplementedError``/``AttributeError``/``Exception``)
# whose prose merely says "not supported" is a native-library-gap marker: it is
# out of this spine census's scope by design (SP2's broader sweep), regardless of
# whether its wording happens to contain a capability-sounding word.


class UnclassifiedExpectation(Exception):
    """A discovered expectation-producing call whose form the census cannot
    parse. Raised (never swallowed) so an unclassifiable site fails the census
    loudly rather than being silently omitted."""


@dataclass(frozen=True)
class CensusEntry:
    node_id: str
    path: str
    line: int | str
    kind: str
    operation_key: Any
    backend: Any
    param: Any
    option_value: Any
    current_reason: Any
    bucket: str
    reason: str


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def build_census() -> list[CensusEntry]:
    """Discover and classify the full closed scope, write the committed report,
    and return entries in deterministic ``(path, address, node_id)`` order."""
    entries: list[CensusEntry] = []
    entries.extend(_scope_c_entries())
    entries.extend(_scope_a_entries())
    entries.extend(_scope_b_entries())
    entries.sort(key=lambda e: (e.path, str(e.line), e.node_id))
    _write_report(entries)
    return entries


# ---------------------------------------------------------------------------
# Shared classification of a recovered (op, backend) selector against the spine.
# ---------------------------------------------------------------------------
def _classify_selector(
    operation_key,
    family: CONST_BACKEND,
    *,
    dialect: str | None = None,
    param: str = WILDCARD_PARAM,
    option_value: str | None = None,
) -> tuple[str, str | None]:
    """Return ``(bucket, reason)`` for a fully-recovered selector.

    ``reason`` is ``None`` for the ``inventoried`` fall-through so the caller can
    supply a scope-specific inventory reason.
    """
    fact = capability_gate(
        operation_key, family, dialect=dialect, param=param, option_value=option_value
    )
    if fact is not None:
        scope = f"{family.value}{'/' + dialect if dialect else ''}"
        return (
            "migrated",
            f"spine gate fact ({fact.level.value}/{fact.enforcement.value}) on {scope} — derivable via capability_gate",
        )
    raw = CapabilityRegistry.capability_for(
        operation_key, param, family, dialect=dialect, option_value=option_value
    )
    if raw is not None and (
        raw.level is CapabilityLevel.LITERAL_ONLY
        or raw.enforcement is Enforcement.ROUTER_METADATA
    ):
        return (
            "retained",
            f"spine {raw.level.value}/{raw.enforcement.value} fact — retained (not an assertable gate)",
        )
    return "inventoried", None


# ---------------------------------------------------------------------------
# Scope (c): physical source rows for all whole-operation build gates.
# ---------------------------------------------------------------------------
def _scope_c_entries() -> list[CensusEntry]:
    segments = CapabilityRegistry.segments()
    entries: list[CensusEntry] = []
    for segment in segments:
        for assertion, fact in zip(segment.segment.capabilities, segment.facts):
            if (
                fact.param != WILDCARD_PARAM
                or fact.level is not CapabilityLevel.UNSUPPORTED
                or fact.boundary is not Boundary.BUILD
                or fact.enforcement is not Enforcement.GATE
            ):
                continue
            local = tuple(
                origin for origin in assertion.origins if type(origin) is LocalOrigin
            )
            if len(local) != 1:
                raise UnclassifiedExpectation(
                    f"{segment.module}:{assertion.key!r}: expected one physical "
                    f"local origin, got {assertion.origins!r}"
                )
            origin = local[0]
            bucket, reason = _classify_selector(
                fact.operation_key,
                segment.scope.backend,
                dialect=segment.scope.dialect,
            )
            if reason is None:
                raise UnclassifiedExpectation(
                    f"{segment.module}:{origin.entry}: registered whole-operation "
                    "gate is not queryable through the capability spine"
                )
            captures = tuple(
                prior.captured
                for prior in assertion.origins
                if getattr(prior, "captured", None) is not None
            )
            capture_note = (
                "; historical capture retained: "
                + ", ".join(
                    f"{capture.path}:{capture.entry}@{capture.revision or 'artifact'}"
                    for capture in captures
                )
                if captures
                else "; no historical capture attached"
            )
            entries.append(
                CensusEntry(
                    node_id=f"{segment.module}::{origin.entry}",
                    path=segment.module,
                    line=origin.entry,
                    kind="segment-source",
                    operation_key=fact.operation_key.name,
                    backend=segment.scope.backend.value,
                    param=WILDCARD_PARAM,
                    option_value=None,
                    current_reason=(
                        "registered physical whole-operation gate source row"
                        + capture_note
                    ),
                    bucket=bucket,
                    reason=reason,
                )
            )
    return entries


# ---------------------------------------------------------------------------
# Scope (a): runtime collection variants for the op-level gate-probe suite.
# ---------------------------------------------------------------------------
def _scope_a_entries() -> list[CensusEntry]:
    src = _REPO_ROOT / _PROBE_REL
    if not src.exists():  # pragma: no cover - the probe suite ships with the repo
        return []
    tree = ast.parse(src.read_text(), filename=str(src))
    fixtures = _read_family_fixtures(tree)
    operation_keys = _read_probe_operation_keys(tree)
    funcs = _parametrized_op_backend_funcs(tree)
    entries: list[CensusEntry] = []
    for fname, lineno in funcs:
        for family in _sorted_families(fixtures):
            for fixture in fixtures[family]:
                identity = identity_for(fixture)
                for fact in whole_operation_gates(operation_keys, fixture):
                    bucket, reason = _classify_selector(
                        fact.operation_key,
                        identity.family,
                        dialect=identity.dialect,
                    )
                    if reason is None:
                        raise UnclassifiedExpectation(
                            f"{_PROBE_REL}::{fname}[{fact.operation_key.name}-{fixture}]: "
                            "runtime provider emitted an unqueryable whole-operation gate"
                        )
                    entries.append(
                        CensusEntry(
                            node_id=(
                                f"{_PROBE_REL}::{fname}"
                                f"[{fact.operation_key.name.lower()}-{fixture}]"
                            ),
                            path=_PROBE_REL,
                            line=lineno,
                            kind="parametrized-case",
                            operation_key=fact.operation_key.name,
                            backend=fixture,
                            param=WILDCARD_PARAM,
                            option_value=None,
                            current_reason=(
                                "runtime whole-operation gate provider variant "
                                f"({fact.operation_key.name}, {fixture})"
                            ),
                            bucket=bucket,
                            reason=reason,
                        )
                    )
    return entries


# ---------------------------------------------------------------------------
# Scope (b): raw xfail forms discovered via the ast module.
# ---------------------------------------------------------------------------
def _scope_b_entries() -> list[CensusEntry]:
    entries: list[CensusEntry] = []
    for pyfile in sorted(_TESTS_DIR.rglob("*.py")):
        rel = _relpath(pyfile)
        # Skip the spine surface fixtures themselves — they DEFINE mark
        # factories (e.g. xfail_divergence); they are not expectation sites.
        if rel.startswith("tests/fixtures/") or "__pycache__" in rel:
            continue
        try:
            tree = ast.parse(pyfile.read_text(), filename=str(pyfile))
        except (SyntaxError, UnicodeDecodeError):  # pragma: no cover - defensive
            continue
        parents = _parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            kind = _call_kind(node)
            if kind is None:
                continue
            if _has_star(node):
                raise UnclassifiedExpectation(
                    f"{rel}:{node.lineno}: {kind} call uses */** unpacking — the "
                    "census cannot statically recover its selector"
                )
            qual = _enclosing_qualname(node, parents)
            backends = _enclosing_backends(node, parents)
            entries.extend(_site_entries(node, kind, rel, qual, backends))
    return entries


def _site_entries(
    node: ast.Call, kind: str, rel: str, qual: str, backends: list[str]
) -> list[CensusEntry]:
    if kind == "divergence":
        return _divergence_site(node, rel, qual)
    if kind == "mark_xfail":
        return _marker_site(node, rel, qual, backends)
    if kind == "xfail":
        return _imperative_site(node, rel, qual, backends)
    raise UnclassifiedExpectation(  # pragma: no cover - _call_kind is exhaustive
        f"{rel}:{node.lineno}: unrecognized expectation call kind {kind!r}"
    )


def _divergence_site(node: ast.Call, rel: str, qual: str) -> list[CensusEntry]:
    div_id = _static_str(node.args[0]) if node.args else _kwarg_str(node, "divergence_id")
    backend = _kwarg_str(node, "backend") or UNRESOLVED
    resolved = div_id or UNRESOLVED
    if div_id is not None:
        try:  # validate the id resolves; a bad id is a real census failure
            divergence_by_id(div_id)
        except KeyError as exc:
            raise UnclassifiedExpectation(
                f"{rel}:{node.lineno}: xfail_divergence references unknown divergence "
                f"id {div_id!r}"
            ) from exc
    return [
        CensusEntry(
            node_id=f"{rel}::{qual}::L{node.lineno}[{backend}]",
            path=rel,
            line=node.lineno,
            kind="static-marker",
            operation_key=UNRESOLVED,  # divergences are id-keyed / op-diffuse
            backend=backend,
            param=UNRESOLVED,
            option_value=None,
            current_reason=f"xfail_divergence('{resolved}', backend={backend!r})",
            bucket="migrated",
            reason=f"spine-derived id-keyed divergence mark via xfail_divergence('{resolved}') — migrated",
        )
    ]


def _marker_site(
    node: ast.Call, rel: str, qual: str, backends: list[str]
) -> list[CensusEntry]:
    reason_expr = _kwarg_expr(node, "reason")
    reason_text = _static_str(reason_expr) if reason_expr is not None else None
    refs = _ref_names(reason_expr) if reason_expr is not None else frozenset()
    raises = _raises_names(node)
    if not _marker_is_capability(refs, raises):
        return []  # not a capability-encoding marker — out of this census's scope
    spine_derived = bool(refs & _SPINE_REFS)
    current = reason_text if reason_text is not None else UNRESOLVED
    targets = backends or [UNRESOLVED]
    out: list[CensusEntry] = []
    for backend in targets:
        if spine_derived:
            bucket = "migrated"
            reason = "spine-derived xfail marker (reason built from a CapabilityFact) — migrated"
        else:
            bucket = "inventoried"
            reason = (
                "capability-encoding static xfail marker with no statically "
                "recoverable spine fact — inventoried"
            )
        out.append(
            CensusEntry(
                node_id=f"{rel}::{qual}::L{node.lineno}[{backend}]",
                path=rel,
                line=node.lineno,
                kind="static-marker",
                operation_key=UNRESOLVED,
                backend=backend,
                param=UNRESOLVED,
                option_value=None,
                current_reason=current,
                bucket=bucket,
                reason=reason,
            )
        )
    return out


def _imperative_site(
    node: ast.Call, rel: str, qual: str, backends: list[str]
) -> list[CensusEntry]:
    reason_expr = node.args[0] if node.args else _kwarg_expr(node, "reason")
    reason_text = _static_str(reason_expr) if reason_expr is not None else None
    refs = _ref_names(reason_expr) if reason_expr is not None else frozenset()
    current = reason_text if reason_text is not None else UNRESOLVED

    nc = _non_capability_predicate(rel, reason_text, reason_expr)
    targets = backends or [UNRESOLVED]
    out: list[CensusEntry] = []
    for backend in targets:
        if nc is not None:
            kind, bucket, reason = "imperative-xfail", "non-capability", nc
        elif refs & _SPINE_REFS:
            kind, bucket, reason = (
                "imperative-xfail",
                "migrated",
                "imperative xfail whose reason is built from a spine CapabilityFact — migrated",
            )
        elif _is_catch_all(reason_expr, reason_text):
            kind, bucket, reason = (
                "catch-all",
                "inventoried",
                "runtime capability-spine catch-all / short-circuit absorber — "
                "closed at the harness in Task 7; catalogued as inventoried",
            )
        else:
            kind, bucket, reason = (
                "imperative-xfail",
                "inventoried",
                "raw imperative xfail encoding a per-backend capability limitation "
                "with no matching spine fact — catalogued for SP2 migration assessment",
            )
        out.append(
            CensusEntry(
                node_id=f"{rel}::{qual}::L{node.lineno}[{backend}]",
                path=rel,
                line=node.lineno,
                kind=kind,
                operation_key=UNRESOLVED,
                backend=backend,
                param=UNRESOLVED,
                option_value=None,
                current_reason=current,
                bucket=bucket,
                reason=reason,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Curated non-capability predicate list (explicit per-family reasons).
# ---------------------------------------------------------------------------
def _non_capability_predicate(
    rel: str, reason_text: str | None, reason_expr: ast.AST | None = None
) -> str | None:
    if rel.endswith("core/test_api_reachability.py"):
        return (
            "non-capability: API reachability gap (fkey not emitted by any public "
            "API entry point) — an emission/wiring gap, not a backend capability "
            "the spine gates"
        )
    if rel.endswith("core/test_signature_conformance.py"):
        return (
            "non-capability: protocol signature/options/call-pattern conformance "
            "divergence — not a backend capability gate"
        )
    if rel.endswith("core/test_rel_signature_conformance.py"):
        return (
            "non-capability: relation protocol conformance divergence "
            "(signature/dispatch/unhandled-node) — not a backend capability gate"
        )
    if rel.endswith("core/test_compile_smoke.py"):
        if reason_text is not None and "AST-internal" in reason_text:
            return (
                "non-capability: AST-internal node, not a compilable expression — a "
                "registry/AST classification, not a backend capability gate"
            )
        # The two compile_smoke harness primitives (SP2-B Task 0.4 / B2): NOT
        # imperative-drain targets. `pytest.xfail(expected_reason)` inside the
        # `if key in _KNOWN_SMOKE_FAILURES` block is a native (non-capability)
        # compile-failure park; `pytest.xfail("undeclared gap (inventoried,
        # pending SP2): …")` is the dynamic catch-all absorber whose ABSORBED
        # runtime gaps are the found_via=catch-all rows, not this static site.
        if isinstance(reason_expr, ast.Name) and reason_expr.id == "expected_reason":
            return (
                "non-capability: _KNOWN_SMOKE_FAILURES park — the harness expects a "
                "NATIVE (non-BackendCapabilityError) compile failure here; not a "
                "spine-gated backend capability"
            )
        if reason_text is not None and "inventoried, pending SP2" in reason_text:
            return (
                "non-capability: the dynamic compile-smoke catch-all absorber "
                "(inventory_has lookup); the absorbed gaps are the runtime "
                "found_via=catch-all rows, not an imperative-drain target"
            )
    return None


def _is_catch_all(reason_expr: ast.AST | None, reason_text: str | None) -> bool:
    if reason_text is not None and "capability spine" in reason_text.lower():
        return True
    # ``pytest.xfail(_KNOWN_SMOKE_FAILURES[key])`` and friends — a runtime lookup
    # into a short-circuit allowlist keyed at collection/run time.
    if isinstance(reason_expr, ast.Subscript):
        base = reason_expr.value
        name = base.id if isinstance(base, ast.Name) else None
        if name and "FAILURES" in name.upper():
            return True
    return False


# ---------------------------------------------------------------------------
# AST call recognition + extraction helpers.
# ---------------------------------------------------------------------------
def _call_kind(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute):
        if func.attr == "xfail" and isinstance(func.value, ast.Name) and func.value.id == "pytest":
            return "xfail"
        if func.attr == "xfail" and _is_pytest_mark(func.value):
            return "mark_xfail"
        if func.attr == "xfail_divergence":
            return "divergence"
    if isinstance(func, ast.Name) and func.id == "xfail_divergence":
        return "divergence"
    return None


def _is_pytest_mark(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "mark"
        and isinstance(node.value, ast.Name)
        and node.value.id == "pytest"
    )


def _has_star(node: ast.Call) -> bool:
    if any(isinstance(a, ast.Starred) for a in node.args):
        return True
    return any(k.arg is None for k in node.keywords)


def _kwarg_expr(node: ast.Call, name: str) -> ast.AST | None:
    for kw in node.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _kwarg_str(node: ast.Call, name: str) -> str | None:
    expr = _kwarg_expr(node, name)
    return _static_str(expr) if expr is not None else None


def _raises_names(node: ast.Call) -> frozenset[str]:
    """All exception type names named in a marker's ``raises=`` argument
    (a single type or a tuple/list of types)."""
    expr = _kwarg_expr(node, "raises")
    if expr is None:
        return frozenset()
    elts = expr.elts if isinstance(expr, (ast.Tuple, ast.List)) else [expr]
    names: set[str] = set()
    for elt in elts:
        if isinstance(elt, ast.Name):
            names.add(elt.id)
        elif isinstance(elt, ast.Attribute):
            names.add(elt.attr)
    return frozenset(names)


def _static_str(expr: ast.AST | None) -> str | None:
    """Best-effort static reconstruction of a string expression. Dynamic
    fragments in an f-string become ``{...}``; a wholly dynamic expression
    returns ``None`` (→ the ``UNRESOLVED`` sentinel at the call site)."""
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.JoinedStr):
        parts: list[str] = []
        for value in expr.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append("{...}")
        return "".join(parts)
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        left = _static_str(expr.left)
        right = _static_str(expr.right)
        if left is not None and right is not None:
            return left + right
    return None


def _ref_names(expr: ast.AST | None) -> frozenset[str]:
    if expr is None:
        return frozenset()
    names: set[str] = set()
    for sub in ast.walk(expr):
        if isinstance(sub, ast.Name):
            names.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            names.add(sub.attr)
    return frozenset(names)


def _marker_is_capability(refs: frozenset[str], raises: frozenset[str]) -> bool:
    """A marker is capability-encoding iff it raises the spine's own gate error
    (``raises=BackendCapabilityError``, alone or in a tuple) or its reason is
    built from a live spine object. Free-text prose is deliberately NOT a
    signal — a native-exception marker whose wording merely says "not supported"
    is a native-library gap for SP2, not a spine expectation site."""
    if "BackendCapabilityError" in raises:
        return True
    return bool(refs & _SPINE_REFS)


# ---------------------------------------------------------------------------
# AST context helpers (enclosing function/class + backend guards).
# ---------------------------------------------------------------------------
def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _enclosing_qualname(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    names: list[str] = []
    cur: ast.AST | None = node
    while cur is not None:
        parent = parents.get(cur)
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(parent.name)
        cur = parent
    return "::".join(reversed(names)) if names else "<module>"


def _enclosing_backends(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> list[str]:
    out: list[str] = []
    cur: ast.AST = node
    while cur in parents:
        parent = parents[cur]
        if isinstance(parent, ast.If) and cur in parent.body:
            for backend in _backends_from_test(parent.test):
                if backend not in out:
                    out.append(backend)
        cur = parent
    return out


def _backends_from_test(test: ast.AST) -> list[str]:
    """Recover backend names from a simple ``if backend_name == ... / in ...``
    guard. Anything that is not a literal comparison against ``backend_name``
    yields nothing (the selector stays ``UNRESOLVED``)."""
    if isinstance(test, ast.BoolOp):
        out: list[str] = []
        for value in test.values:
            for backend in _backends_from_test(value):
                if backend not in out:
                    out.append(backend)
        return out
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        if not _is_backend_name(test.left):
            return []
    op = test.ops[0] if isinstance(test, ast.Compare) and test.ops else None
    comparator = test.comparators[0] if isinstance(test, ast.Compare) and test.comparators else None
    if isinstance(op, ast.Eq) and isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
        return [comparator.value]
    if isinstance(op, ast.In) and isinstance(comparator, (ast.Tuple, ast.List)):
        return [
            elt.value
            for elt in comparator.elts
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        ]
    if _is_startswith_call(test):
        arg = test.args[0]
        prefix = arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None
        if prefix:
            return [prefix.rstrip("-")]
    return []


def _is_backend_name(expr: ast.AST) -> bool:
    return isinstance(expr, ast.Name) and expr.id == "backend_name"


def _is_startswith_call(test: ast.AST) -> bool:
    return (
        isinstance(test, ast.Call)
        and isinstance(test.func, ast.Attribute)
        and test.func.attr == "startswith"
        and _is_backend_name(test.func.value)
        and bool(test.args)
    )


# ---------------------------------------------------------------------------
# Scope (a) static readers over the probe file's AST.
# ---------------------------------------------------------------------------
def _read_family_fixtures(tree: ast.AST) -> dict[CONST_BACKEND, tuple[str, ...]]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "_FAMILY_FIXTURES" for t in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        out: dict[CONST_BACKEND, tuple[str, ...]] = {}
        for key, value in zip(node.value.keys, node.value.values):
            family = _const_backend_from_attr(key)
            if family is None or not isinstance(value, (ast.Tuple, ast.List)):
                continue
            out[family] = tuple(
                elt.value
                for elt in value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            )
        return out
    return {}


def _const_backend_from_attr(expr: ast.AST | None) -> CONST_BACKEND | None:
    if (
        isinstance(expr, ast.Attribute)
        and isinstance(expr.value, ast.Name)
        and expr.value.id == "CONST_BACKEND"
    ):
        return getattr(CONST_BACKEND, expr.attr, None)
    return None


def _read_probe_operation_keys(tree: ast.AST) -> tuple[object, ...]:
    """Recover the canonical operation enums that the runtime provider receives."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "_OP_CASES" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            break
        keys: list[object] = []
        for key in node.value.keys:
            if not (
                isinstance(key, ast.Attribute)
                and isinstance(key.value, ast.Name)
                and key.value.id == "FK_STR"
            ):
                raise UnclassifiedExpectation(
                    f"{_PROBE_REL}:{node.lineno}: _OP_CASES must use canonical FK_STR members"
                )
            operation_key = getattr(FK_STR, key.attr, None)
            if operation_key is None:
                raise UnclassifiedExpectation(
                    f"{_PROBE_REL}:{node.lineno}: unknown FK_STR member {key.attr!r}"
                )
            keys.append(operation_key)
        return tuple(keys)
    raise UnclassifiedExpectation(
        f"{_PROBE_REL}: expected canonical _OP_CASES collection provider"
    )


def _parametrized_op_backend_funcs(tree: ast.AST) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            if (
                isinstance(deco, ast.Call)
                and isinstance(deco.func, ast.Attribute)
                and deco.func.attr == "parametrize"
                and deco.args
            ):
                argnames = _static_str(deco.args[0])
                if argnames and "fkey" in [name.strip() for name in argnames.split(",")]:
                    out.append((node.name, node.lineno))
                    break
    return out


# ---------------------------------------------------------------------------
# Small path / import helpers.
# ---------------------------------------------------------------------------
def _relpath(path: Path) -> str:
    return path.resolve().relative_to(_REPO_ROOT).as_posix()


def _sorted_families(mapping: dict[CONST_BACKEND, Any]) -> list[CONST_BACKEND]:
    return sorted(mapping, key=lambda f: f.value)




# ---------------------------------------------------------------------------
# Committed census report.
# ---------------------------------------------------------------------------
def _write_report(entries: list[CensusEntry]) -> None:
    lines: list[str] = [
        "# Spine expectation census",
        "",
        "> Generated by `tests/fixtures/capability_census.py::build_census()`.",
        "> Do not edit by hand — this is the closed SCOPE authority (§3) that the",
        "> Task 6 inventory and SP2 read. Entries are ordered by `(path, address)`.",
        "",
        "Buckets: `migrated` (derivable from the spine today), `retained` "
        "(a LITERAL_ONLY/ROUTER_METADATA fact — not an assertable gate), "
        "`inventoried` (capability gap with no fact yet — SP2), `non-capability` "
        "(explicitly not a backend capability gate). `UNRESOLVED` marks a "
        "selector that cannot be recovered statically.",
        "",
    ]
    for bucket in VALID_BUCKETS:
        lines.append(f"## {bucket}")
        lines.append("")
        rows = [e for e in entries if e.bucket == bucket]
        if not rows:
            lines.append("_none_")
            lines.append("")
            continue
        lines.append("| site | kind | op | backend | param | option | reason |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for e in rows:
            lines.append(
                "| {path}:{line} | {kind} | {op} | {backend} | {param} | {option} | {reason} |".format(
                    path=e.path,
                    line=e.line,
                    kind=e.kind,
                    op=e.operation_key,
                    backend=e.backend,
                    param=e.param,
                    option=e.option_value,
                    reason=e.reason.replace("|", "\\|"),
                )
            )
        lines.append("")
    _REPORT_PATH.write_text("\n".join(lines) + "\n")
