"""Capability declarations for XSD temporal lexical operations.

XSD duration and partial-date operations use portable string expressions on
all expression systems. Their throw/null residue policy is applied by the
conform operation layer, so this module has no backend limitation facts.
"""
from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilityDeclaration

DECLARATIONS: tuple[CapabilityDeclaration, ...] = ()
