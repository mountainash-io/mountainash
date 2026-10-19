"""Enclosing declaration scope."""

from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.constants import CONST_BACKEND

SCOPE = Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name="ibis-exasol"))
