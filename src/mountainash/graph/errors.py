"""Errors raised by the shared graph kernel."""
from __future__ import annotations


class UnknownNodeError(KeyError):
    """A named node is not in the graph."""


class DuplicateNodeError(ValueError):
    """A node name is already registered."""


class CycleError(ValueError):
    """The dependency edges contain a cycle."""
