"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.capabilities.identity import FamilyWide
from mountainash.core.capabilities.identity import Scope

SCOPE = Scope(backend=CONST_BACKEND.NARWHALS, applicability=FamilyWide())
