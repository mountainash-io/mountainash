"""Backend identity — family + dialect, the spine's runtime vocabulary.

The spec's BackendFamily is realized as the existing CONST_BACKEND enum
(no duplicate). Dialects here are the DECLARABLE vocabulary — validation
constrains facts to these names; runtime detection may compute names
outside it (e.g. narwhals-pyarrow), which simply never match a fact.
"""
from __future__ import annotations

from dataclasses import dataclass

from mountainash.core.constants import CONST_BACKEND


@dataclass(frozen=True)
class BackendIdentity:
    family: CONST_BACKEND
    dialect: str | None = None  # None = unknown/unbound → family-level facts only


KNOWN_DIALECTS: dict[CONST_BACKEND, frozenset[str]] = {
    CONST_BACKEND.POLARS: frozenset({"polars"}),
    CONST_BACKEND.IBIS: frozenset({"ibis-duckdb", "ibis-sqlite", "ibis-polars"}),
    CONST_BACKEND.NARWHALS: frozenset(
        {"narwhals-polars", "narwhals-pandas", "narwhals-lazy"}
    ),
    CONST_BACKEND.PANDAS: frozenset({"pandas"}),
    CONST_BACKEND.PYARROW: frozenset({"pyarrow"}),
}
# NOTE: this dict MUST be exhaustive over CONST_BACKEND — _validate_fact
# indexes KNOWN_DIALECTS[family] directly, so a missing member is a latent
# KeyError. CONST_BACKEND has five members (POLARS/PANDAS/PYARROW/IBIS/
# NARWHALS); PYARROW is a real member even though no Phase-1 backend
# registers facts under it.
