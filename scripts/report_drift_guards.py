#!/usr/bin/env python3
"""Drift guard report: xfail population across protocol_alignment and argument_types suites.

Usage:
    python scripts/report_drift_guards.py
    python scripts/report_drift_guards.py --report-file scripts/outputs/drift-guards-report.md
"""

from __future__ import annotations

import argparse
import ast
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TESTS_DIR = PROJECT_ROOT / "tests"
ARG_TYPES_DIR = TESTS_DIR / "cross_backend" / "argument_types"
PROTOCOL_ALIGNMENT_FILE = TESTS_DIR / "unit" / "test_protocol_alignment.py"
BACKEND_BASE_FILES = {
    "polars": PROJECT_ROOT / "src/mountainash/expressions/backends/expression_systems/polars/base.py",
    "narwhals": PROJECT_ROOT / "src/mountainash/expressions/backends/expression_systems/narwhals/base.py",
    "ibis": PROJECT_ROOT / "src/mountainash/expressions/backends/expression_systems/ibis/base.py",
}


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Task 2: Protocol Alignment Collection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AspirationalGap:
    protocol_name: str
    method_name: str
    reason: str
    since: str


def _extract_known_gap_kwargs(call_node: ast.Call) -> dict[str, str]:
    return {
        kw.arg: kw.value.value
        for kw in call_node.keywords
        if isinstance(kw.value, ast.Constant)
    }


def collect_protocol_alignment() -> list[AspirationalGap]:
    """Parse KNOWN_ASPIRATIONAL from test_protocol_alignment.py via AST."""
    source = PROTOCOL_ALIGNMENT_FILE.read_text()
    tree = ast.parse(source)
    gaps: list[AspirationalGap] = []

    for node in ast.walk(tree):
        # Match both bare Assign and annotated AnnAssign
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        else:
            continue
        if not any(
            isinstance(t, ast.Name) and t.id == "KNOWN_ASPIRATIONAL"
            for t in targets
        ):
            continue
        if not isinstance(value, ast.Dict):
            continue
        for key, val in zip(value.keys, value.values):
            if not isinstance(key, ast.Tuple) or len(key.elts) != 2:
                continue
            proto_node, method_node = key.elts
            if not isinstance(proto_node, ast.Name):
                continue
            if not isinstance(method_node, ast.Constant):
                continue
            if not isinstance(val, ast.Call):
                continue
            kwargs = _extract_known_gap_kwargs(val)
            gaps.append(AspirationalGap(
                protocol_name=proto_node.id,
                method_name=str(method_node.value),
                reason=kwargs.get("reason", ""),
                since=kwargs.get("since", ""),
            ))
        break  # Only the first KNOWN_ASPIRATIONAL assignment

    return sorted(gaps, key=lambda g: (g.protocol_name, g.method_name))


# ---------------------------------------------------------------------------
# Task 3: KEL Entries Collection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KelGap:
    backend: str
    op_name: str
    param_name: str
    message: str
    est_cases: int


def _attr_to_op_name(node: ast.expr) -> str:
    """FK_STR.REPLACE → 'replace', 'substring' → 'substring'."""
    if isinstance(node, ast.Attribute):
        return node.attr.lower()
    if isinstance(node, ast.Constant):
        return str(node.value)
    return repr(node)


def _extract_message_from_kel_call(val: ast.expr) -> str:
    """Extract message= from a KnownLimitation(...) call node."""
    if not isinstance(val, ast.Call):
        return ""
    for kw in val.keywords:
        if kw.arg == "message" and isinstance(kw.value, ast.Constant):
            return str(kw.value.value)
    return ""


def _parse_kel_from_class_body(source: str, backend: str, est_cases: int) -> list[KelGap]:
    tree = ast.parse(source)
    gaps: list[KelGap] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        # Build a map of class-level variable name → message for Name-reference values
        class_var_messages: dict[str, str] = {}
        for item in node.body:
            if not isinstance(item, ast.Assign):
                continue
            for target in item.targets:
                if isinstance(target, ast.Name):
                    msg = _extract_message_from_kel_call(item.value)
                    if msg:
                        class_var_messages[target.id] = msg

        for item in ast.walk(node):
            if isinstance(item, ast.Assign):
                targets, value = item.targets, item.value
            elif isinstance(item, ast.AnnAssign):
                targets, value = [item.target], item.value
            else:
                continue
            if not any(
                isinstance(t, ast.Name) and t.id == "KNOWN_EXPR_LIMITATIONS"
                for t in targets
            ):
                continue
            if not isinstance(value, ast.Dict):
                continue
            for key, val in zip(value.keys, value.values):
                if not isinstance(key, ast.Tuple) or len(key.elts) != 2:
                    continue
                fkey_node, param_node = key.elts
                if not isinstance(param_node, ast.Constant):
                    continue
                op_name = _attr_to_op_name(fkey_node)
                # Value may be a direct Call or a Name reference to a class variable
                if isinstance(val, ast.Call):
                    message = _extract_message_from_kel_call(val)
                elif isinstance(val, ast.Name):
                    message = class_var_messages.get(val.id, "")
                else:
                    message = ""
                gaps.append(KelGap(
                    backend=backend,
                    op_name=op_name,
                    param_name=str(param_node.value),
                    message=message,
                    est_cases=est_cases,
                ))
    return gaps


def collect_kel_entries() -> list[KelGap]:
    """Parse KNOWN_EXPR_LIMITATIONS from each backend base class via AST.

    Est. cases per entry:
      polars: 2 input types (col, complex) × 1 backend = 2
      narwhals: 2 input types × 2 sub-backends (narwhals-polars + narwhals-pandas) = 4
               (approximate — some narwhals-polars ops pass and are in _NW_POLARS_FIXED)
      ibis: 2 input types × 1 backend = 2
    """
    backend_est = {"polars": 2, "narwhals": 4, "ibis": 2}
    gaps: list[KelGap] = []
    for backend, path in BACKEND_BASE_FILES.items():
        gaps.extend(_parse_kel_from_class_body(path.read_text(), backend, backend_est[backend]))
    return sorted(gaps, key=lambda g: (g.backend, g.op_name, g.param_name))


# ---------------------------------------------------------------------------
# Task 4: Fully-Unsupported Ops Collection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FullyUnsupportedGap:
    op_name: str
    param_name: str
    backends: tuple[str, ...]
    est_cases: int  # len(backends) × 4 input types


def _ast_tuple_pair(elt: ast.expr) -> tuple[str, str] | None:
    """(FK_STR.REPEAT, "count") or ("to_time", "x") → ("repeat", "count")."""
    if not isinstance(elt, ast.Tuple) or len(elt.elts) != 2:
        return None
    left, right = elt.elts
    if isinstance(left, ast.Attribute):
        op = left.attr.lower()
    elif isinstance(left, ast.Constant):
        op = str(left.value)
    else:
        return None
    if not isinstance(right, ast.Constant):
        return None
    return op, str(right.value)


def _parse_set_assignment(source: str, var_name: str) -> set[tuple[str, str]]:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        else:
            continue
        if not any(isinstance(t, ast.Name) and t.id == var_name for t in targets):
            continue
        if not isinstance(value, ast.Set):
            continue
        result: set[tuple[str, str]] = set()
        for elt in value.elts:
            pair = _ast_tuple_pair(elt)
            if pair:
                result.add(pair)
        return result
    return set()


def collect_fully_unsupported() -> list[FullyUnsupportedGap]:
    """Parse _NARWHALS_FULLY_UNSUPPORTED and _IBIS_FULLY_UNSUPPORTED from test_arg_types_string.py."""
    source = (ARG_TYPES_DIR / "test_arg_types_string.py").read_text()
    narwhals_set = _parse_set_assignment(source, "_NARWHALS_FULLY_UNSUPPORTED")
    ibis_set = _parse_set_assignment(source, "_IBIS_FULLY_UNSUPPORTED")
    all_pairs = narwhals_set | ibis_set
    gaps: list[FullyUnsupportedGap] = []
    for op, param in sorted(all_pairs):
        backends: list[str] = []
        if (op, param) in narwhals_set:
            backends.append("narwhals")
        if (op, param) in ibis_set:
            backends.append("ibis")
        gaps.append(FullyUnsupportedGap(
            op_name=op,
            param_name=param,
            backends=tuple(backends),
            est_cases=len(backends) * 4,
        ))
    return gaps


# ---------------------------------------------------------------------------
# Task 5: Manual xfail Block Detection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ManualXfailBlock:
    variable_name: str
    source_file: str
    reason: str
    active: bool  # True if referenced inside _params() body, False if dead code


def _extract_xfail_reason_from_call(node: ast.expr) -> str | None:
    """Return reason= string from a pytest.mark.xfail(...) call, or None."""
    if not isinstance(node, ast.Call):
        return None
    for kw in node.keywords:
        if kw.arg == "reason" and isinstance(kw.value, ast.Constant):
            return str(kw.value.value)
    return None


def _collect_xfail_vars_from_file(path: Path) -> list[ManualXfailBlock]:
    source = path.read_text()
    tree = ast.parse(source)

    # Collect module-level *_XFAIL = pytest.mark.xfail(...) assignments
    xfail_vars: dict[str, str] = {}  # var_name → reason string
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if not target.id.endswith("_XFAIL"):
                continue
            reason = _extract_xfail_reason_from_call(node.value)
            if reason is not None:
                xfail_vars[target.id] = reason

    if not xfail_vars:
        return []

    # Find _params() and collect all Name references inside it
    params_refs: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_params":
            for child in ast.walk(node):
                if isinstance(child, ast.Name):
                    params_refs.add(child.id)

    return [
        ManualXfailBlock(
            variable_name=var_name,
            source_file=path.name,
            reason=reason,
            active=var_name in params_refs,
        )
        for var_name, reason in sorted(xfail_vars.items())
    ]


def collect_manual_xfail_blocks() -> list[ManualXfailBlock]:
    """Scan test_arg_types_*.py for module-level *_XFAIL variables."""
    blocks: list[ManualXfailBlock] = []
    for path in sorted(ARG_TYPES_DIR.glob("test_arg_types_*.py")):
        blocks.extend(_collect_xfail_vars_from_file(path))
    return blocks


def render_report() -> str:
    return "# Drift Guard Report\n\n(stub)\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-file",
        metavar="PATH",
        help="Write markdown report to this file in addition to printing to stdout.",
    )
    args = parser.parse_args()
    report = render_report()
    print(report)
    if args.report_file:
        out = Path(args.report_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report)
        print(f"Report saved to {out}")


if __name__ == "__main__":
    main()
