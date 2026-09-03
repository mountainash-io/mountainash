#!/usr/bin/env python3
"""Generate the deterministic AST-derived transit inventory.

Run:
    hatch run test:python scripts/generate_transit_inventory.py \
        --write tests/fixtures/transit_inventory.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from mountainash.core.generated_artifacts import write_text_if_changed  # noqa: E402
from tests.core._transit_census import (  # noqa: E402
    build_inventory,
    render_inventory,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        type=Path,
        default=None,
        help="Path to write the JSON inventory (prints to stdout if omitted)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=_REPO_ROOT / "src" / "mountainash",
        help="Package directory to scan (default: src/mountainash)",
    )
    args = parser.parse_args(argv)

    entries = build_inventory(args.root)
    text = render_inventory(entries)

    if args.write:
        if write_text_if_changed(args.write, text):
            print("wrote")
        else:
            print("unchanged")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
