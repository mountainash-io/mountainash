"""Concrete Ibis dialect scope for independently qualified restrictions."""

from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.constants import CONST_BACKEND

SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-mysql"))
