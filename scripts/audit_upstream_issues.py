"""Upstream registry reconciliation audit script.

Cross-references:
  1. Static pytest.mark.xfail markers in tests/
  2. KNOWN_EXPR_LIMITATIONS registries in backend base.py files
  3. YAML registry (upstream-issues.yaml) in mountainash-central upstream-issues/

Produces a reconciliation report showing counts and discrepancies.

Usage:
    python scripts/audit_upstream_issues.py
    python scripts/audit_upstream_issues.py --skip-github
    python scripts/audit_upstream_issues.py --report-file report.md
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to project root — determined at runtime)
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TESTS_DIR = PROJECT_ROOT / "tests"

BACKEND_BASE_FILES = {
    "polars": PROJECT_ROOT
    / "src/mountainash/expressions/backends/expression_systems/polars/base.py",
    "narwhals": PROJECT_ROOT
    / "src/mountainash/expressions/backends/expression_systems/narwhals/base.py",
    "ibis": PROJECT_ROOT
    / "src/mountainash/expressions/backends/expression_systems/ibis/base.py",
}

REGISTRY_ROOT = (
    PROJECT_ROOT.parent
    / "mountainash-central/01.principles/mountainash/h.backlog/upstream-issues"
)

REGISTRY_YAML = REGISTRY_ROOT / "upstream-issues.yaml"

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class StaticXfail:
    file: str
    line: int
    reason: str
    strict: bool
    backend: str | None  # extracted from surrounding pytest.param context


@dataclass
class KelEntry:
    """A single KNOWN_EXPR_LIMITATIONS entry."""

    backend: str
    function_key: str  # e.g. "FK_STR.REPLACE" or "FK_DT.ADD_YEARS"
    param_name: str
    message: str
    shared_var: str | None  # name of shared KnownLimitation variable if used


@dataclass
class RegistryEntry:
    id: str
    project: str  # ibis | narwhals | polars | mountainash-internal
    category: str  # derived from filename
    description: str
    upstream_issue: str | None  # URL or None
    upstream_issue_number: str | None  # "#123" or None
    status: str
    action: str
    kel_count: str | None  # column value if present
    xfail_refs: list[str] | None = None


@dataclass
class GithubIssueStatus:
    url: str
    state: str  # open | closed | error
    title: str | None
    error: str | None


@dataclass
class AuditReport:
    # Raw counts
    total_xfails: int
    total_kel: int
    total_registry: int

    # Cross-reference results
    orphaned_xfails: list[StaticXfail]  # xfails with no registry entry
    orphaned_kel: list[KelEntry]  # KEL entries with no registry entry
    orphaned_registry: list[RegistryEntry]  # registry entries with no xfail/KEL
    status_mismatches: list[tuple[RegistryEntry, GithubIssueStatus]]  # registry says open, GH says closed (or vice versa)
    upstream_discoveries: list[tuple[RegistryEntry, list[dict]]]  # needs_filing entries with potential matches
    ambiguous_xfails: list[StaticXfail]  # xfails with no clear backend attribution

    # GitHub check results
    github_checked: int
    github_errors: int

    # Per-backend breakdown
    xfail_by_backend: dict[str, int]
    kel_by_backend: dict[str, int]
    registry_by_project: dict[str, int]
    registry_by_status: dict[str, int]


# ---------------------------------------------------------------------------
# 1. Parse static xfails
# ---------------------------------------------------------------------------

# Matches: pytest.param("backend", marks=pytest.mark.xfail(
_PARAM_XFAIL_RE = re.compile(
    r'pytest\.param\s*\(\s*["\'](?P<backend>[^"\']+)["\']'
    r'.*?marks\s*=\s*pytest\.mark\.xfail\s*\(',
    re.DOTALL,
)

# Matches: @pytest.mark.xfail( or standalone pytest.mark.xfail(
_BARE_XFAIL_RE = re.compile(r'pytest\.mark\.xfail\s*\(')

# Extract reason="..." or reason='...'
_REASON_RE = re.compile(
    r'\breason\s*=\s*(?:'
    r'(?P<q>["\'])(?P<reason>.*?)(?P=q)'       # reason="..." or reason='...'
    r'|'
    r'\(\s*["\'](?P<reason_paren>.*?)["\']'    # reason=("..." — first string in parens
    r')',
    re.DOTALL,
)

# Extract strict=True/False
_STRICT_RE = re.compile(r'\bstrict\s*=\s*(?P<val>True|False)')


def _extract_xfail_attrs(text: str) -> tuple[str, bool]:
    """Extract (reason, strict) from the text of an xfail call's arguments."""
    reason_m = _REASON_RE.search(text)
    reason = (reason_m.group("reason") or reason_m.group("reason_paren") or "") if reason_m else ""
    strict_m = _STRICT_RE.search(text)
    strict = strict_m.group("val") == "True" if strict_m else False
    return reason, strict


def _read_paren_body(text: str, start: int) -> str:
    """Read from `start` (pointing at opening '(') until the matching ')'.

    Returns the content between the outer parens (exclusive).
    """
    depth = 0
    i = start
    body_start = start + 1
    while i < len(text):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[body_start:i]
        elif c in ('"', "'"):
            # Skip string literal
            q = c
            i += 1
            while i < len(text) and text[i] != q:
                if text[i] == "\\":
                    i += 1  # skip escaped char
                i += 1
        i += 1
    return text[body_start:]


def parse_static_xfails() -> list[StaticXfail]:
    """Walk tests/ and extract every pytest.mark.xfail occurrence."""
    results: list[StaticXfail] = []

    for py_file in sorted(TESTS_DIR.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        text = py_file.read_text(encoding="utf-8")
        rel_path = str(py_file.relative_to(PROJECT_ROOT))
        lines = text.splitlines()

        # Build a line-offset map for position → line number
        line_offsets: list[int] = []
        pos = 0
        for line in lines:
            line_offsets.append(pos)
            pos += len(line) + 1  # +1 for newline

        def pos_to_line(p: int) -> int:
            lo, hi = 0, len(line_offsets) - 1
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if line_offsets[mid] <= p:
                    lo = mid
                else:
                    hi = mid - 1
            return lo + 1  # 1-based

        # Strategy: find all pytest.mark.xfail( occurrences
        for m in _BARE_XFAIL_RE.finditer(text):
            xfail_pos = m.start()
            # Read the body of the xfail call
            paren_start = m.end() - 1  # position of '('
            body = _read_paren_body(text, paren_start)
            reason, strict = _extract_xfail_attrs(body)

            line_num = pos_to_line(xfail_pos)

            # Try to determine the backend from surrounding context.
            # Look back ~200 chars for a pytest.param("backend-name", ...)
            look_back = text[max(0, xfail_pos - 300) : xfail_pos]
            backend: str | None = None

            # Case 1: pytest.param("backend", marks=pytest.mark.xfail(
            param_m = list(_PARAM_XFAIL_RE.finditer(look_back))
            if param_m:
                # Use the last (closest) match
                backend = param_m[-1].group("backend")
            else:
                # Case 2: @pytest.mark.xfail — decorator, no inline backend
                # Look for the backend in the reason string
                backend_keywords = [
                    "polars", "narwhals", "ibis", "pandas",
                    "duckdb", "sqlite", "ibis-polars", "ibis-duckdb", "ibis-sqlite",
                ]
                reason_lower = reason.lower()
                for kw in backend_keywords:
                    if kw in reason_lower:
                        backend = kw
                        break

            results.append(StaticXfail(
                file=rel_path,
                line=line_num,
                reason=reason,
                strict=strict,
                backend=backend,
            ))

    return results


# ---------------------------------------------------------------------------
# 2. Parse KNOWN_EXPR_LIMITATIONS
# ---------------------------------------------------------------------------

# Match the start of KNOWN_EXPR_LIMITATIONS dict
_KEL_DICT_START_RE = re.compile(r'KNOWN_EXPR_LIMITATIONS\s*:\s*dict\[.*?\]\s*=\s*\{', re.DOTALL)

# Match shared-variable definitions: _VAR_NAME = KnownLimitation(
_SHARED_VAR_RE = re.compile(
    r'(?P<varname>_[A-Z_]+)\s*=\s*KnownLimitation\s*\((?P<body>[^)]*(?:\([^)]*\)[^)]*)*)\)',
    re.DOTALL,
)


def _extract_message_from_known_limitation(text: str) -> str:
    """Extract message= from a KnownLimitation(...) call text."""
    m = re.search(r'\bmessage\s*=\s*(?P<q>["\']|(?:\([\s\S]*?\)))(?P<msg>[\s\S]*?)(?P=q)', text)
    if m:
        return m.group("msg").strip()
    # Try triple-quoted or parenthesized string
    m2 = re.search(r'message\s*=\s*\(\s*["\'](?P<msg>.*?)["\']', text, re.DOTALL)
    if m2:
        return m2.group("msg").strip()
    return text.strip()[:120]


def parse_known_expr_limitations() -> list[KelEntry]:
    """Parse KNOWN_EXPR_LIMITATIONS from all three backend base.py files."""
    results: list[KelEntry] = []

    for backend, base_path in BACKEND_BASE_FILES.items():
        if not base_path.exists():
            continue

        text = base_path.read_text(encoding="utf-8")

        # First collect shared variables (class-level KnownLimitation variables)
        shared_vars: dict[str, str] = {}
        for sm in _SHARED_VAR_RE.finditer(text):
            varname = sm.group("varname")
            body = sm.group("body")
            msg_m = re.search(
                r'message\s*=\s*\(\s*["\'](?P<msg>.*?)["\']|message\s*=\s*["\'](?P<msg2>.*?)["\']',
                body,
                re.DOTALL,
            )
            if msg_m:
                shared_vars[varname] = (msg_m.group("msg") or msg_m.group("msg2") or "").strip()
            else:
                shared_vars[varname] = body.strip()[:120]

        # Find the KNOWN_EXPR_LIMITATIONS dict block
        kel_m = _KEL_DICT_START_RE.search(text)
        if not kel_m:
            continue

        dict_start = kel_m.end()  # position right after '{'
        # Read until the matching '}' (accounting for nesting)
        depth = 1
        i = dict_start
        while i < len(text) and depth > 0:
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c in ('"', "'"):
                q = c
                i += 1
                while i < len(text) and text[i] != q:
                    if text[i] == "\\":
                        i += 1
                    i += 1
            i += 1
        dict_body = text[dict_start : i - 1]

        # Parse entries line by line (robust against multi-line values)
        # Collect lines that start a key tuple
        for km in re.finditer(
            r'\(\s*(?P<fkey>[A-Za-z_]+\.[A-Z_]+)\s*,\s*["\'](?P<param>[^"\']+)["\']\s*\)\s*:\s*(?P<val>.+)',
            dict_body,
        ):
            fkey = km.group("fkey")
            param = km.group("param")
            val_text = km.group("val").strip()

            shared_var: str | None = None
            if val_text.startswith("_"):
                # Shared variable reference
                var_name = val_text.split(",")[0].strip().rstrip(",")
                shared_var = var_name
                message = shared_vars.get(var_name, f"<shared: {var_name}>")
            elif val_text.startswith("KnownLimitation"):
                # Inline definition — try to extract message
                message = _extract_message_from_known_limitation(val_text)
            else:
                message = val_text[:120]

            results.append(KelEntry(
                backend=backend,
                function_key=fkey,
                param_name=param,
                message=message,
                shared_var=shared_var,
            ))

    return results


# ---------------------------------------------------------------------------
# 3. Parse YAML registry
# ---------------------------------------------------------------------------


def parse_yaml_registry() -> list[RegistryEntry]:
    """Parse the canonical YAML upstream-issues registry."""
    yaml_path = REGISTRY_YAML
    if not yaml_path.exists():
        print(f"  WARNING: YAML registry not found at {yaml_path}", flush=True)
        return []

    try:
        import yaml
    except ImportError:
        print("  WARNING: PyYAML not installed — cannot parse YAML registry", flush=True)
        return []

    with open(yaml_path) as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict) or "issues" not in data:
        print("  WARNING: YAML registry has unexpected structure", flush=True)
        return []

    results: list[RegistryEntry] = []
    for entry in data["issues"]:
        upstream_url = entry.get("upstream_issue")
        upstream_number = None
        if upstream_url:
            m = re.search(r'/issues/(\d+)$', upstream_url)
            if m:
                upstream_number = f"#{m.group(1)}"

        kel = entry.get("known_expr_limitations", [])
        kel_count = str(len(kel)) if kel else None

        xfail_refs = entry.get("xfail_refs", []) or []

        results.append(RegistryEntry(
            id=entry.get("id", ""),
            project=entry.get("project", ""),
            category=entry.get("category", ""),
            description=entry.get("summary", ""),
            upstream_issue=upstream_url,
            upstream_issue_number=upstream_number,
            status=entry.get("status", ""),
            action=entry.get("our_workaround", ""),
            kel_count=kel_count,
            xfail_refs=xfail_refs,
        ))

    return results


# ---------------------------------------------------------------------------
# 4. GitHub functions
# ---------------------------------------------------------------------------

_GITHUB_ISSUE_RE = re.compile(r'github\.com/([^/]+/[^/]+)/issues/(\d+)')


def check_github_issue_status(url: str) -> GithubIssueStatus:
    """Query GitHub API for the state of a single issue URL."""
    m = _GITHUB_ISSUE_RE.search(url)
    if not m:
        return GithubIssueStatus(url=url, state="error", title=None, error="Could not parse repo/issue from URL")

    repo = m.group(1)
    issue_num = m.group(2)
    api_path = f"repos/{repo}/issues/{issue_num}"

    try:
        result = subprocess.run(
            ["gh", "api", api_path, "--jq", "{state: .state, title: .title}"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return GithubIssueStatus(
                url=url, state="error", title=None,
                error=result.stderr.strip() or "gh api returned non-zero exit code",
            )

        data = json.loads(result.stdout.strip())
        return GithubIssueStatus(
            url=url,
            state=data.get("state", "unknown"),
            title=data.get("title"),
            error=None,
        )
    except subprocess.TimeoutExpired:
        return GithubIssueStatus(url=url, state="error", title=None, error="Timeout")
    except Exception as e:
        return GithubIssueStatus(url=url, state="error", title=None, error=str(e))


def search_upstream_issues(repo: str, keywords: list[str]) -> list[dict]:
    """Search for GitHub issues in repo matching keywords."""
    query = " ".join(keywords[:5])  # GH search caps at reasonable length
    try:
        result = subprocess.run(
            [
                "gh", "search", "issues",
                "--repo", repo,
                "--state", "open",
                "--json", "number,title,url,state",
                "--limit", "5",
                query,
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout.strip() or "[]")
        return data if isinstance(data, list) else []
    except Exception:
        return []


def check_all_linked_issues(
    entries: list[RegistryEntry],
    rate_limit_sleep: float = 0.5,
) -> dict[str, GithubIssueStatus]:
    """Check GitHub status for all registry entries that have a linked issue URL."""
    url_map: dict[str, GithubIssueStatus] = {}
    seen: set[str] = set()

    for entry in entries:
        if entry.upstream_issue and entry.upstream_issue not in seen:
            seen.add(entry.upstream_issue)
            status = check_github_issue_status(entry.upstream_issue)
            url_map[entry.upstream_issue] = status
            time.sleep(rate_limit_sleep)

    return url_map


def discover_upstream_issues(
    entries: list[RegistryEntry],
    rate_limit_sleep: float = 1.0,
) -> list[tuple[RegistryEntry, list[dict]]]:
    """For entries with status needs_filing, search upstream for potential existing issues."""
    repo_map = {
        "ibis": "ibis-project/ibis",
        "narwhals": "narwhals-dev/narwhals",
        "polars": "pola-rs/polars",
    }
    discoveries: list[tuple[RegistryEntry, list[dict]]] = []

    for entry in entries:
        if "needs_filing" not in entry.status.lower():
            continue
        repo = repo_map.get(entry.project)
        if not repo:
            continue

        # Build search keywords from description
        words = re.sub(r'[^\w\s]', '', entry.description.lower()).split()
        # Filter out very common words
        stop = {"the", "a", "an", "is", "not", "and", "or", "on", "in", "to", "for", "of", "at"}
        keywords = [w for w in words if w not in stop and len(w) > 3][:6]

        if not keywords:
            continue

        found = search_upstream_issues(repo, keywords)
        if found:
            discoveries.append((entry, found))
        time.sleep(rate_limit_sleep)

    return discoveries


# ---------------------------------------------------------------------------
# 5. Cross-reference engine
# ---------------------------------------------------------------------------


def _extract_keywords(text: str) -> set[str]:
    """Extract significant keywords from a text string for fuzzy matching."""
    stop = {
        "the", "a", "an", "is", "not", "and", "or", "on", "in", "to", "for",
        "of", "at", "this", "that", "with", "from", "are", "be", "do", "as",
        "by", "it", "its", "we", "our", "has", "have", "been", "was", "were",
    }
    words = re.sub(r'[^\w\s]', ' ', text.lower()).split()
    return {w for w in words if len(w) > 3 and w not in stop}


def _registry_matches_xfail(entry: RegistryEntry, xfail: StaticXfail) -> bool:
    """Heuristic: does a registry entry plausibly describe a given xfail?"""
    # Check xfail_refs first — if the file path appears in xfail_refs, it's a match
    if entry.xfail_refs:
        xfail_file = xfail.file.replace("\\", "/")
        for ref in entry.xfail_refs:
            ref_file = ref.split(":")[0]
            if ref_file in xfail_file or xfail_file.endswith(ref_file):
                return True

    # Fall back to keyword heuristic
    reg_kw = _extract_keywords(entry.description + " " + entry.status + " " + entry.action)
    xfail_kw = _extract_keywords(xfail.reason)
    if not xfail_kw:
        return False
    overlap = reg_kw & xfail_kw
    return len(overlap) >= 2


def _registry_matches_kel(entry: RegistryEntry, kel: KelEntry) -> bool:
    """Heuristic: does a registry entry plausibly cover a given KEL entry?"""
    # Check if function key components appear in the description
    fkey_parts = kel.function_key.lower().replace("fk_", "").replace("fk_ma_", "").split(".")
    fkey_op = fkey_parts[-1].lower().replace("_", " ") if fkey_parts else ""
    param = kel.param_name.lower()

    desc = entry.description.lower()
    reg_kw = _extract_keywords(entry.description)
    kel_kw = _extract_keywords(kel.function_key + " " + kel.param_name + " " + kel.message)

    # Check direct keyword overlap
    if len(reg_kw & kel_kw) >= 2:
        return True

    # Check function key operation name appears in description
    op_words = fkey_op.split()
    if any(w in desc for w in op_words if len(w) > 3):
        return True

    # Check param name appears in description
    if param in desc and len(param) > 3:
        return True

    return False


def cross_reference(
    xfails: list[StaticXfail],
    kel_entries: list[KelEntry],
    registry: list[RegistryEntry],
    github_statuses: dict[str, GithubIssueStatus] | None = None,
    discoveries: list[tuple[RegistryEntry, list[dict]]] | None = None,
) -> AuditReport:
    """Cross-reference all three data sources and produce an AuditReport."""

    # Per-backend counts
    xfail_by_backend: dict[str, int] = {}
    for x in xfails:
        key = x.backend or "unknown"
        xfail_by_backend[key] = xfail_by_backend.get(key, 0) + 1

    kel_by_backend: dict[str, int] = {}
    for k in kel_entries:
        kel_by_backend[k.backend] = kel_by_backend.get(k.backend, 0) + 1

    registry_by_project: dict[str, int] = {}
    registry_by_status: dict[str, int] = {}
    for r in registry:
        registry_by_project[r.project] = registry_by_project.get(r.project, 0) + 1
        registry_by_status[r.status] = registry_by_status.get(r.status, 0) + 1

    # Orphaned xfails: those where no registry entry plausibly matches
    orphaned_xfails: list[StaticXfail] = []
    for xfail in xfails:
        matched = any(_registry_matches_xfail(entry, xfail) for entry in registry)
        if not matched and xfail.reason:
            orphaned_xfails.append(xfail)

    # Orphaned KEL: KEL entries with no plausible registry match
    orphaned_kel: list[KelEntry] = []
    for kel in kel_entries:
        matched = any(_registry_matches_kel(entry, kel) for entry in registry)
        if not matched:
            orphaned_kel.append(kel)

    # Orphaned registry: registry entries with no xfail or KEL match
    orphaned_registry: list[RegistryEntry] = []
    for entry in registry:
        xfail_match = any(_registry_matches_xfail(entry, x) for x in xfails)
        kel_match = any(_registry_matches_kel(entry, k) for k in kel_entries)
        if not xfail_match and not kel_match:
            orphaned_registry.append(entry)

    # Status mismatches: registry says open but GH says closed (or vice versa)
    status_mismatches: list[tuple[RegistryEntry, GithubIssueStatus]] = []
    if github_statuses:
        for entry in registry:
            if entry.upstream_issue and entry.upstream_issue in github_statuses:
                gh_status = github_statuses[entry.upstream_issue]
                if gh_status.state == "error":
                    continue
                reg_status = entry.status.lower()
                gh_state = gh_status.state.lower()

                # Mismatch: registry says "open" but GH says "closed"
                if "open" in reg_status and gh_state == "closed":
                    status_mismatches.append((entry, gh_status))
                # Mismatch: registry says "closed" or "fixed" but GH says "open"
                elif ("closed" in reg_status or "fixed" in reg_status) and gh_state == "open":
                    status_mismatches.append((entry, gh_status))

    # Ambiguous xfails: no backend could be determined (exclude unit tests — they're backend-agnostic by design)
    ambiguous_xfails = [
        x for x in xfails
        if x.backend is None and "/unit/" not in x.file and "/expressions/" not in x.file
    ]

    # GitHub stats
    github_checked = len(github_statuses) if github_statuses else 0
    github_errors = (
        sum(1 for s in github_statuses.values() if s.state == "error")
        if github_statuses
        else 0
    )

    return AuditReport(
        total_xfails=len(xfails),
        total_kel=len(kel_entries),
        total_registry=len(registry),
        orphaned_xfails=orphaned_xfails,
        orphaned_kel=orphaned_kel,
        orphaned_registry=orphaned_registry,
        status_mismatches=status_mismatches,
        upstream_discoveries=discoveries or [],
        ambiguous_xfails=ambiguous_xfails,
        github_checked=github_checked,
        github_errors=github_errors,
        xfail_by_backend=xfail_by_backend,
        kel_by_backend=kel_by_backend,
        registry_by_project=registry_by_project,
        registry_by_status=registry_by_status,
    )


# ---------------------------------------------------------------------------
# 6. Format report
# ---------------------------------------------------------------------------


def format_report(report: AuditReport) -> str:
    """Format an AuditReport as a markdown string."""
    lines: list[str] = []

    lines.append("# Upstream Registry Reconciliation Audit")
    lines.append("")
    lines.append("## Summary Counts")
    lines.append("")
    lines.append(f"| Source | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Static `pytest.mark.xfail` markers | {report.total_xfails} |")
    lines.append(f"| `KNOWN_EXPR_LIMITATIONS` entries | {report.total_kel} |")
    lines.append(f"| YAML registry entries | {report.total_registry} |")
    lines.append("")

    # Per-backend breakdown
    lines.append("## xfail by Backend")
    lines.append("")
    lines.append("| Backend | Count |")
    lines.append("|---------|-------|")
    for backend, count in sorted(report.xfail_by_backend.items(), key=lambda x: -x[1]):
        lines.append(f"| {backend} | {count} |")
    lines.append("")

    lines.append("## KNOWN_EXPR_LIMITATIONS by Backend")
    lines.append("")
    lines.append("| Backend | Count |")
    lines.append("|---------|-------|")
    for backend, count in sorted(report.kel_by_backend.items(), key=lambda x: -x[1]):
        lines.append(f"| {backend} | {count} |")
    lines.append("")

    lines.append("## Registry by Project")
    lines.append("")
    lines.append("| Project | Count |")
    lines.append("|---------|-------|")
    for proj, count in sorted(report.registry_by_project.items(), key=lambda x: -x[1]):
        lines.append(f"| {proj} | {count} |")
    lines.append("")

    lines.append("## Registry by Status")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    for status, count in sorted(report.registry_by_status.items(), key=lambda x: -x[1]):
        lines.append(f"| {status} | {count} |")
    lines.append("")

    # Cross-reference results
    lines.append("## Cross-Reference Results")
    lines.append("")

    lines.append(f"- **Orphaned xfails** (no registry match): {len(report.orphaned_xfails)}")
    lines.append(f"- **Orphaned KEL entries** (no registry match): {len(report.orphaned_kel)}")
    lines.append(f"- **Orphaned registry entries** (no xfail/KEL match): {len(report.orphaned_registry)}")
    lines.append(f"- **GitHub status mismatches**: {len(report.status_mismatches)}")
    lines.append(f"- **Upstream discovery hits** (needs_filing with GH matches): {len(report.upstream_discoveries)}")
    lines.append(f"- **Ambiguous xfails** (no backend attribution): {len(report.ambiguous_xfails)}")
    lines.append("")

    if report.github_checked > 0:
        lines.append(f"GitHub issues checked: {report.github_checked} "
                     f"({report.github_errors} errors)")
        lines.append("")

    # Orphaned xfails detail
    if report.orphaned_xfails:
        lines.append("### Orphaned xfails (no registry entry found)")
        lines.append("")
        lines.append("| File | Line | Backend | Reason (truncated) |")
        lines.append("|------|------|---------|-------------------|")
        for x in report.orphaned_xfails[:40]:  # cap at 40 rows
            reason = (x.reason[:80] + "...") if len(x.reason) > 80 else x.reason
            reason = reason.replace("|", "\\|")
            lines.append(f"| {x.file} | {x.line} | {x.backend or 'unknown'} | {reason} |")
        if len(report.orphaned_xfails) > 40:
            lines.append(f"| ... | | | *({len(report.orphaned_xfails) - 40} more)* |")
        lines.append("")

    # Orphaned KEL detail
    if report.orphaned_kel:
        lines.append("### Orphaned KNOWN_EXPR_LIMITATIONS (no registry entry found)")
        lines.append("")
        lines.append("| Backend | Function Key | Param | Shared Var |")
        lines.append("|---------|-------------|-------|------------|")
        for k in report.orphaned_kel:
            lines.append(f"| {k.backend} | {k.function_key} | {k.param_name} | {k.shared_var or ''} |")
        lines.append("")

    # Orphaned registry detail
    if report.orphaned_registry:
        lines.append("### Orphaned Registry Entries (no xfail or KEL match)")
        lines.append("")
        lines.append("| ID | Project | Status | Description (truncated) |")
        lines.append("|----|---------|--------|------------------------|")
        for r in report.orphaned_registry[:40]:
            desc = (r.description[:80] + "...") if len(r.description) > 80 else r.description
            desc = desc.replace("|", "\\|")
            lines.append(f"| {r.id} | {r.project} | {r.status} | {desc} |")
        if len(report.orphaned_registry) > 40:
            lines.append(f"| ... | | | *({len(report.orphaned_registry) - 40} more)* |")
        lines.append("")

    # Status mismatches
    if report.status_mismatches:
        lines.append("### GitHub Status Mismatches")
        lines.append("")
        lines.append("| ID | Registry Status | GitHub State | Title |")
        lines.append("|----|----------------|--------------|-------|")
        for entry, gh in report.status_mismatches:
            title = (gh.title[:60] + "...") if gh.title and len(gh.title) > 60 else (gh.title or "")
            lines.append(f"| {entry.id} | {entry.status} | {gh.state} | {title} |")
        lines.append("")

    # Upstream discoveries
    if report.upstream_discoveries:
        lines.append("### Upstream Discovery Hits (needs_filing entries with GH matches)")
        lines.append("")
        for entry, hits in report.upstream_discoveries:
            lines.append(f"**{entry.id}**: {entry.description[:100]}")
            for hit in hits[:3]:
                lines.append(f"  - [{hit.get('number', '?')}] {hit.get('title', '')} — {hit.get('url', '')}")
        lines.append("")

    # Ambiguous xfails
    if report.ambiguous_xfails:
        lines.append("### Ambiguous xfails (backend attribution unclear)")
        lines.append("")
        lines.append("| File | Line | Reason (truncated) |")
        lines.append("|------|------|-------------------|")
        for x in report.ambiguous_xfails[:20]:
            reason = (x.reason[:80] + "...") if len(x.reason) > 80 else x.reason
            reason = reason.replace("|", "\\|")
            lines.append(f"| {x.file} | {x.line} | {reason} |")
        if len(report.ambiguous_xfails) > 20:
            lines.append(f"| ... | | *({len(report.ambiguous_xfails) - 20} more)* |")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 7. main()
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit upstream issue registry against static xfails and KNOWN_EXPR_LIMITATIONS"
    )
    parser.add_argument(
        "--report-file",
        metavar="PATH",
        help="Write the markdown report to this file (default: print to stdout)",
    )
    parser.add_argument(
        "--skip-github",
        action="store_true",
        help="Skip all GitHub API calls (faster, offline-friendly)",
    )
    args = parser.parse_args()

    print("Parsing static xfails...", flush=True)
    xfails = parse_static_xfails()
    print(f"  Found {len(xfails)} xfail markers", flush=True)

    print("Parsing KNOWN_EXPR_LIMITATIONS...", flush=True)
    kel_entries = parse_known_expr_limitations()
    print(f"  Found {len(kel_entries)} KEL entries", flush=True)

    print("Parsing YAML registry...", flush=True)
    registry = parse_yaml_registry()
    print(f"  Found {len(registry)} registry entries", flush=True)

    github_statuses: dict[str, GithubIssueStatus] | None = None
    discoveries: list[tuple[RegistryEntry, list[dict]]] | None = None

    if not args.skip_github:
        print("Checking linked GitHub issues...", flush=True)
        github_statuses = check_all_linked_issues(registry)
        print(f"  Checked {len(github_statuses)} unique issue URLs", flush=True)

        print("Searching for upstream issues (needs_filing entries)...", flush=True)
        discoveries = discover_upstream_issues(registry)
        print(f"  Found {len(discoveries)} potential discovery hits", flush=True)
    else:
        print("Skipping GitHub checks (--skip-github)", flush=True)

    print("Cross-referencing...", flush=True)
    report = cross_reference(xfails, kel_entries, registry, github_statuses, discoveries)

    report_text = format_report(report)

    if args.report_file:
        out_path = Path(args.report_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_text, encoding="utf-8")
        print(f"\nReport written to: {out_path}", flush=True)
    else:
        print("\n" + report_text)


if __name__ == "__main__":
    main()
