"""Enclosing declaration scope."""

from mountainash.core.capabilities.identity import Dialect
from mountainash.core.capabilities.identity import Scope
from mountainash.core.constants import CONST_BACKEND

SCOPE = Scope(backend=CONST_BACKEND.NARWHALS, applicability=Dialect(name="narwhals-pandas"))
