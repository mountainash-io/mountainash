#!/usr/bin/env python3
"""Validate upstream-issues.yaml against the canonical schema.

Usage:
    python scripts/validate_upstream_registry.py [PATH]

Default path:
    ../mountainash-central/01.principles/mountainash/h.backlog/upstream-issues/upstream-issues.yaml
    (relative to the repo root, i.e. the parent of the directory containing this script)

Exit codes:
    0 — validation passed
    1 — validation errors found, or file cannot be read/parsed
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "ERROR: PyYAML is not installed. Install it with:\n"
        "    uv pip install pyyaml\n"
        "or:\n"
        "    pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Canonical allowed values
# ---------------------------------------------------------------------------

VALID_PROJECTS = {"ibis", "narwhals", "polars", "mountainash-internal"}

VALID_ROOT_CAUSES = {
    "upstream_bug",
    "upstream_feature_gap",
    "parameter_width",
    "by_design",
    "mountainash_internal",
}

VALID_BACKENDS = {
    "polars",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite",
    "narwhals-polars",
    "narwhals-pandas",
}

VALID_STATUSES = {
    "needs_filing",
    "needs_investigation",
    "open",
    "closed",
    "wont_fix",
    "by_design",
    "resolved_in_mountainash",
}

VALID_WORKAROUNDS = {
    "xfail_strict",
    "xfail_nonstrict",
    "error_enrichment",
    "fallback_impl",
    "none",
    "accepted_divergence",
}

VALID_FILED_BY = {"us", "other"}

REQUIRED_FIELDS = {
    "id",
    "project",
    "category",
    "summary",
    "root_cause",
    "affected_backends",
    "status",
    "our_workaround",
    "last_verified",
}

# ID format: {PROJ_ABBR}-{CAT_ABBR}-{NN}
PROJECT_ABBR = {
    "ibis": "IB",
    "narwhals": "NW",
    "polars": "PL",
    "mountainash-internal": "MA",
}

CATEGORY_ABBR = {
    "string-ops": "STR",
    "math-ops": "MATH",
    "datetime-ops": "DT",
    "type-inference": "TYPE",
    "relation-ops": "REL",
    "recursive-cte": "CTE",
    "interval-ops": "INT",
    "cast-semantics": "CAST",
    "list-ops": "LIST",
    "aggregate-ops": "AGG",
    "type-system": "TYPE",
    "wiring-gaps": "WIRE",
}

GITHUB_ISSUE_RE = re.compile(
    r"^https://github\.com/[^/]+/[^/]+/issues/\d+$"
)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Matches e.g. IB-STR-01, NW-MATH-123
ID_RE = re.compile(r"^([A-Z]+)-([A-Z]+)-(\d+)$")


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate(data: object) -> list[str]:
    """Return a list of human-readable error strings (empty = valid)."""
    errors: list[str] = []

    # Rule 1: root structure
    if not isinstance(data, dict):
        return ["Root of document must be a mapping (dict)."]
    if "issues" not in data:
        return ["Root mapping must contain an 'issues' key."]
    issues = data["issues"]
    if not isinstance(issues, list):
        return ["'issues' must be a list."]

    seen_ids: set[str] = set()

    for idx, entry in enumerate(issues):
        prefix = f"Entry #{idx + 1}"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: must be a mapping, got {type(entry).__name__}.")
            continue

        entry_id = entry.get("id", f"<no id, index {idx + 1}>")
        prefix = f"Entry '{entry_id}'"

        # Rule 2: required fields
        for field in sorted(REQUIRED_FIELDS):
            if field not in entry:
                errors.append(f"{prefix}: missing required field '{field}'.")

        # Rule 3: project
        project = entry.get("project")
        if project is not None and project not in VALID_PROJECTS:
            errors.append(
                f"{prefix}: 'project' is '{project}'; must be one of {sorted(VALID_PROJECTS)}."
            )

        # Rule 4: root_cause
        root_cause = entry.get("root_cause")
        if root_cause is not None and root_cause not in VALID_ROOT_CAUSES:
            errors.append(
                f"{prefix}: 'root_cause' is '{root_cause}'; must be one of {sorted(VALID_ROOT_CAUSES)}."
            )

        # Rule 5: affected_backends
        affected = entry.get("affected_backends")
        if affected is not None:
            if not isinstance(affected, list) or len(affected) == 0:
                errors.append(
                    f"{prefix}: 'affected_backends' must be a non-empty list."
                )
            else:
                bad = [b for b in affected if b not in VALID_BACKENDS]
                if bad:
                    errors.append(
                        f"{prefix}: 'affected_backends' contains invalid values {bad}; "
                        f"allowed: {sorted(VALID_BACKENDS)}."
                    )

        # Rule 6: status
        status = entry.get("status")
        if status is not None and status not in VALID_STATUSES:
            errors.append(
                f"{prefix}: 'status' is '{status}'; must be one of {sorted(VALID_STATUSES)}."
            )

        # Rule 7: our_workaround
        workaround = entry.get("our_workaround")
        if workaround is not None and workaround not in VALID_WORKAROUNDS:
            errors.append(
                f"{prefix}: 'our_workaround' is '{workaround}'; must be one of {sorted(VALID_WORKAROUNDS)}."
            )

        # Rule 8: upstream_issue_filed_by
        filed_by = entry.get("upstream_issue_filed_by")
        if filed_by is not None and filed_by not in VALID_FILED_BY:
            errors.append(
                f"{prefix}: 'upstream_issue_filed_by' is '{filed_by}'; "
                f"must be one of {sorted(VALID_FILED_BY)}, or null/absent."
            )

        # Rule 9: upstream_issue
        upstream_issue = entry.get("upstream_issue")
        if upstream_issue is not None:
            if not isinstance(upstream_issue, str) or not GITHUB_ISSUE_RE.match(upstream_issue):
                errors.append(
                    f"{prefix}: 'upstream_issue' must be null or a GitHub issue URL "
                    f"matching https://github.com/{{owner}}/{{repo}}/issues/{{number}}; "
                    f"got '{upstream_issue}'."
                )

        # Rule 10: last_verified
        last_verified = entry.get("last_verified")
        if last_verified is not None:
            if not isinstance(last_verified, str) or not DATE_RE.match(last_verified):
                errors.append(
                    f"{prefix}: 'last_verified' must match YYYY-MM-DD format; got '{last_verified}'."
                )

        # Rule 11: id format
        entry_id_str = entry.get("id")
        if entry_id_str is not None:
            m = ID_RE.match(str(entry_id_str))
            if not m:
                errors.append(
                    f"{prefix}: 'id' does not match {{PROJ}}-{{CAT}}-{{NN}} format; got '{entry_id_str}'."
                )
            else:
                proj_abbr_in_id, cat_abbr_in_id, _ = m.groups()

                # Check project abbreviation matches the project field
                if project in PROJECT_ABBR:
                    expected_proj_abbr = PROJECT_ABBR[project]
                    if proj_abbr_in_id != expected_proj_abbr:
                        errors.append(
                            f"{prefix}: 'id' project prefix is '{proj_abbr_in_id}' but "
                            f"'project' is '{project}' (expected prefix '{expected_proj_abbr}')."
                        )

                # Check category abbreviation matches the category field
                category = entry.get("category")
                if category in CATEGORY_ABBR:
                    expected_cat_abbr = CATEGORY_ABBR[category]
                    if cat_abbr_in_id != expected_cat_abbr:
                        errors.append(
                            f"{prefix}: 'id' category prefix is '{cat_abbr_in_id}' but "
                            f"'category' is '{category}' (expected prefix '{expected_cat_abbr}')."
                        )
                elif category is not None:
                    # Category not in our known abbreviation map — warn but don't hard-fail
                    errors.append(
                        f"{prefix}: 'category' is '{category}' which has no known abbreviation. "
                        f"Known categories: {sorted(CATEGORY_ABBR)}."
                    )

        # Rule 12: duplicate ids
        if entry_id_str is not None:
            if entry_id_str in seen_ids:
                errors.append(f"{prefix}: duplicate 'id' value '{entry_id_str}'.")
            else:
                seen_ids.add(entry_id_str)

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    repo_root = Path(__file__).parent.parent
    default_path = (
        repo_root.parent
        / "mountainash-central"
        / "01.principles"
        / "mountainash"
        / "h.backlog"
        / "upstream-issues"
        / "upstream-issues.yaml"
    )

    if len(sys.argv) > 2:
        print(f"Usage: {sys.argv[0]} [PATH]", file=sys.stderr)
        return 1

    path = Path(sys.argv[1]) if len(sys.argv) == 2 else default_path

    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        return 1

    try:
        with open(path) as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        print(f"ERROR: Failed to parse YAML: {exc}", file=sys.stderr)
        return 1

    errors = validate(data)

    if not errors:
        n = len(data.get("issues", []))
        print(f"Validation PASSED — {n} entries, 0 errors")
        return 0

    print(f"Validation FAILED — {len(errors)} error(s):\n", file=sys.stderr)
    for err in errors:
        print(f"  - {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
