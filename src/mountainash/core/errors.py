"""Root of the mountainash error hierarchy.

`MountainashError` is a deliberately bare marker class: it carries no custom
`__init__`, so subclasses that also inherit a builtin (e.g.
`class MissingResourceSchema(DAGError, ValueError)`) construct exactly as the
builtin did before re-parenting. Structure (codes, context) can be added later
with optional parameters without breaking existing raises.
"""
from __future__ import annotations


class MountainashError(Exception):
    """Root of all mountainash-raised typed errors."""
