"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel
from mountainash.core.capabilities.declarations import LocalOrigin
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.capabilities.identity import FamilyWide
from mountainash.core.capabilities.identity import Scope
from mountainash.core.capabilities.declarations import FactSource
from mountainash.core.capabilities.capture import CapturedAddress
from mountainash.core.capabilities.capture import SourceOrigin
from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(domain=Domain.LIST, capabilities=(CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS, subject='item'), level=CapabilityLevel.LITERAL_ONLY, since='2026-07-05', origins=(LocalOrigin(entry='capabilities[0]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.narwhals', scope=Scope(backend=CONST_BACKEND.NARWHALS, applicability=FamilyWide()), source=FactSource.MOUNTAINASH, domain=Domain.LIST, entry='DECLARATIONS[2].facts[0]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/narwhals.py', entry='DECLARATIONS[2].facts[0]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='Narwhals list.contains() requires a literal item argument, not a column expression', workaround='Use a literal value for item or use the Polars/Ibis backend.', issue='NW-LIST-01'), CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.T_CONTAINS, subject='item'), level=CapabilityLevel.LITERAL_ONLY, since='2026-07-05', origins=(LocalOrigin(entry='capabilities[1]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.narwhals', scope=Scope(backend=CONST_BACKEND.NARWHALS, applicability=FamilyWide()), source=FactSource.MOUNTAINASH, domain=Domain.LIST, entry='DECLARATIONS[2].facts[2]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/narwhals.py', entry='DECLARATIONS[2].facts[2]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='Narwhals list.t_contains() requires a literal item argument, not a column expression', workaround='Use a literal value for item or use the Polars/Ibis backend.', issue='NW-LIST-01'),), evidence_refs=(CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/narwhals.py', entry='DECLARATIONS[2]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a'),))
