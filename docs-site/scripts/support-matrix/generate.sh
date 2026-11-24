#!/usr/bin/env bash
# Regenerate chapter 16 (Backend support and known limits) from the package's
# capability coverage report and divergences catalogue.
# Usage: docs-site/scripts/support-matrix/generate.sh OUTDIR
# OUTDIR must be outside the repository; generated inputs are written there.
set -euo pipefail
OUT="$(mkdir -p "$1" && cd "$1" && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
cd "$REPO"
hatch -e test run python -m mountainash.core.capabilities.render_markdown --output "$OUT"
hatch -e test run python scripts/generate_divergences_catalog.py --report-file "$OUT/known-divergences.md"
hatch -e test run python "$HERE/summarise_coverage.py" "$OUT"
hatch -e test run python "$HERE/assemble_ch16.py" "$OUT"
