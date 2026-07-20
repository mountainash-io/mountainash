"""Audit live GitHub state and discover upstream issues from the YAML registry.

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

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
REGISTRY_ROOT = PROJECT_ROOT / "registry"
REGISTRY_YAML = REGISTRY_ROOT / "upstream-issues.yaml"


@dataclass
class RegistryEntry:
    id: str
    project: str
    category: str
    description: str
    upstream_issue: str | None
    upstream_issue_number: str | None
    status: str
    action: str


@dataclass
class GithubIssueStatus:
    url: str
    state: str
    title: str | None
    error: str | None


@dataclass
class AuditReport:
    total_registry: int
    status_mismatches: list[tuple[RegistryEntry, GithubIssueStatus]]
    upstream_discoveries: list[tuple[RegistryEntry, list[dict]]]
    github_checked: int
    github_errors: int


def parse_yaml_registry() -> list[RegistryEntry]:
    """Parse the canonical YAML upstream-issues registry."""
    if not REGISTRY_YAML.exists():
        print(f"  WARNING: YAML registry not found at {REGISTRY_YAML}", flush=True)
        return []

    try:
        import yaml
    except ImportError:
        print("  WARNING: PyYAML not installed — cannot parse YAML registry", flush=True)
        return []

    with open(REGISTRY_YAML) as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict) or "issues" not in data:
        print("  WARNING: YAML registry has unexpected structure", flush=True)
        return []

    results: list[RegistryEntry] = []
    for entry in data["issues"]:
        upstream_url = entry.get("upstream_issue")
        upstream_number = None
        if upstream_url:
            match = re.search(r"/issues/(\d+)$", upstream_url)
            if match:
                upstream_number = f"#{match.group(1)}"

        results.append(
            RegistryEntry(
                id=entry.get("id", ""),
                project=entry.get("project", ""),
                category=entry.get("category", ""),
                description=entry.get("summary", ""),
                upstream_issue=upstream_url,
                upstream_issue_number=upstream_number,
                status=entry.get("status", ""),
                action=entry.get("our_workaround", ""),
            )
        )

    return results


_GITHUB_ISSUE_RE = re.compile(r"github\.com/([^/]+/[^/]+)/issues/(\d+)")


def check_github_issue_status(url: str) -> GithubIssueStatus:
    """Query GitHub API for the state of a single issue URL."""
    match = _GITHUB_ISSUE_RE.search(url)
    if not match:
        return GithubIssueStatus(
            url=url,
            state="error",
            title=None,
            error="Could not parse repo/issue from URL",
        )

    repo = match.group(1)
    issue_num = match.group(2)
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
                url=url,
                state="error",
                title=None,
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
    except Exception as exc:
        return GithubIssueStatus(url=url, state="error", title=None, error=str(exc))


def search_upstream_issues(repo: str, keywords: list[str]) -> list[dict]:
    """Search for GitHub issues in repo matching keywords."""
    query = " ".join(keywords[:5])
    try:
        result = subprocess.run(
            [
                "gh",
                "search",
                "issues",
                "--repo",
                repo,
                "--state",
                "open",
                "--json",
                "number,title,url,state",
                "--limit",
                "5",
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
    entries: list[RegistryEntry], rate_limit_sleep: float = 0.5
) -> dict[str, GithubIssueStatus]:
    """Check GitHub status for all registry entries with linked issue URLs."""
    url_map: dict[str, GithubIssueStatus] = {}
    seen: set[str] = set()

    for entry in entries:
        if entry.upstream_issue and entry.upstream_issue not in seen:
            seen.add(entry.upstream_issue)
            url_map[entry.upstream_issue] = check_github_issue_status(entry.upstream_issue)
            time.sleep(rate_limit_sleep)

    return url_map


def discover_upstream_issues(
    entries: list[RegistryEntry], rate_limit_sleep: float = 1.0
) -> list[tuple[RegistryEntry, list[dict]]]:
    """Search upstream for potential issues for entries marked needs_filing."""
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

        words = re.sub(r"[^\w\s]", "", entry.description.lower()).split()
        stop = {"the", "a", "an", "is", "not", "and", "or", "on", "in", "to", "for", "of", "at"}
        keywords = [word for word in words if word not in stop and len(word) > 3][:6]
        if not keywords:
            continue

        found = search_upstream_issues(repo, keywords)
        if found:
            discoveries.append((entry, found))
        time.sleep(rate_limit_sleep)

    return discoveries


def build_report(
    registry: list[RegistryEntry],
    github_statuses: dict[str, GithubIssueStatus] | None = None,
    discoveries: list[tuple[RegistryEntry, list[dict]]] | None = None,
) -> AuditReport:
    """Build a report from the registry and live GitHub results."""
    status_mismatches: list[tuple[RegistryEntry, GithubIssueStatus]] = []
    if github_statuses:
        for entry in registry:
            if entry.upstream_issue and entry.upstream_issue in github_statuses:
                github_status = github_statuses[entry.upstream_issue]
                if github_status.state == "error":
                    continue
                registry_status = entry.status.lower()
                github_state = github_status.state.lower()
                if "open" in registry_status and github_state == "closed":
                    status_mismatches.append((entry, github_status))
                elif ("closed" in registry_status or "fixed" in registry_status) and github_state == "open":
                    status_mismatches.append((entry, github_status))

    github_checked = len(github_statuses) if github_statuses else 0
    github_errors = (
        sum(1 for status in github_statuses.values() if status.state == "error")
        if github_statuses
        else 0
    )
    return AuditReport(
        total_registry=len(registry),
        status_mismatches=status_mismatches,
        upstream_discoveries=discoveries or [],
        github_checked=github_checked,
        github_errors=github_errors,
    )


def format_report(report: AuditReport) -> str:
    """Format an AuditReport as a markdown string."""
    lines = [
        "# Upstream Registry Reconciliation Audit",
        "",
        "Code<->registry linkage is CI-enforced by "
        "tests/core/test_upstream_registry_join.py (typed upstream_ref join); "
        "this audit covers only what code cannot know: live GitHub state.",
        "",
        f"- **GitHub status mismatches**: {len(report.status_mismatches)}",
        f"- **Upstream discovery hits** (needs_filing with GH matches): {len(report.upstream_discoveries)}",
    ]

    if report.github_checked > 0:
        lines.extend(
            [
                "",
                f"GitHub issues checked: {report.github_checked} ({report.github_errors} errors)",
            ]
        )

    if report.status_mismatches:
        lines.extend(
            [
                "",
                "### GitHub Status Mismatches",
                "",
                "| ID | Registry Status | GitHub State | Title |",
                "|----|----------------|--------------|-------|",
            ]
        )
        for entry, github_status in report.status_mismatches:
            title = (
                github_status.title[:60] + "..."
                if github_status.title and len(github_status.title) > 60
                else (github_status.title or "")
            )
            lines.append(
                f"| {entry.id} | {entry.status} | {github_status.state} | {title} |"
            )

    if report.upstream_discoveries:
        lines.extend(["", "### Upstream Discovery Hits (needs_filing entries with GH matches)", ""])
        for entry, hits in report.upstream_discoveries:
            lines.append(f"**{entry.id}**: {entry.description[:100]}")
            for hit in hits[:3]:
                lines.append(
                    f"  - [{hit.get('number', '?')}] {hit.get('title', '')} — {hit.get('url', '')}"
                )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit upstream issue registry against live GitHub state"
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

    report_text = format_report(build_report(registry, github_statuses, discoveries))
    if args.report_file:
        out_path = Path(args.report_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_text, encoding="utf-8")
        print(f"\nReport written to: {out_path}", flush=True)
    else:
        print("\n" + report_text)


if __name__ == "__main__":
    main()
