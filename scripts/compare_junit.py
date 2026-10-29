"""Print tests whose outcome differs between two pytest JUnit XML reports.

Typical use, e.g. checking a dependency version change:

    <env-a>/bin/python -m pytest tests/expressions --junitxml=a.xml
    <env-b>/bin/python -m pytest tests/expressions --junitxml=b.xml
    python scripts/compare_junit.py a.xml b.xml

Outcomes: passed, failed, error, skipped, xfailed. JUnit XML records a
non-strict XPASS as passed. Tests missing from one report show as "absent".
Exits 1 if any outcome differs, 0 otherwise.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET


def outcomes(path: str) -> dict[str, str]:
    result = {}
    for case in ET.parse(path).iter("testcase"):
        test_id = f"{case.get('classname')}::{case.get('name')}"
        tags = {child.tag: child for child in case}
        if "failure" in tags:
            outcome = "failed"
        elif "error" in tags:
            outcome = "error"
        elif "skipped" in tags:
            outcome = "xfailed" if tags["skipped"].get("type") == "pytest.xfail" else "skipped"
        else:
            outcome = "passed"
        result[test_id] = outcome
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    a, b = outcomes(argv[0]), outcomes(argv[1])
    changed = sorted(t for t in a.keys() | b.keys() if a.get(t) != b.get(t))
    for test_id in changed:
        print(f"{a.get(test_id, 'absent'):>8} -> {b.get(test_id, 'absent'):<8} {test_id}")
    print(f"{len(a)} vs {len(b)} tests, {len(changed)} changed")
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
