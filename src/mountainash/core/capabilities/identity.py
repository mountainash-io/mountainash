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


@dataclass(frozen=True)
class FamilyWide:
    """An explicitly authored family-wide applicability."""


@dataclass(frozen=True)
class Dialect:
    name: str

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise ValueError("dialect requires a nonempty canonical name")


@dataclass(frozen=True)
class Scope:
    backend: CONST_BACKEND
    applicability: FamilyWide | Dialect

    def __post_init__(self) -> None:
        if type(self.backend) is not CONST_BACKEND:
            raise TypeError("scope backend must be CONST_BACKEND")
        if type(self.applicability) not in (FamilyWide, Dialect):
            raise TypeError("scope applicability must be FamilyWide or Dialect")
        if isinstance(self.applicability, Dialect):
            if self.applicability.name not in KNOWN_DIALECTS[self.backend]:
                raise ValueError(
                    f"unknown {self.backend.value} dialect {self.applicability.name!r}"
                )

    @property
    def dialect(self) -> str | None:
        if isinstance(self.applicability, Dialect):
            return self.applicability.name
        return None
