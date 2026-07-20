"""Integrity guard: known gaps older than six months require review."""
from datetime import date
import warnings

from fixtures.gap_collection import collect_all_gap_sets


def test_gap_staleness_warns_on_real_today():
    stale = []
    for set_name, gaps in collect_all_gap_sets().items():
        for key, gap in gaps.items():
            if gap.is_stale(today=date.today()):
                stale.append(f"{set_name}: {key} (since {gap.since})")
    if stale:
        warnings.warn(
            "Stale known-gap entries (>6 months, closed-by-default review due):\n"
            + "\n".join(sorted(stale)),
            stacklevel=1,
        )
