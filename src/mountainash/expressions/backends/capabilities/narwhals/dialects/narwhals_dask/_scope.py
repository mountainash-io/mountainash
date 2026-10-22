"""Concrete scope for the existing Narwhals dask route."""

from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.constants import CONST_BACKEND

SCOPE = Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-dask"))
