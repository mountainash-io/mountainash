"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
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
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(domain=Domain.STRING, capabilities=(CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME, subject='*'), level=CapabilityLevel.UNSUPPORTED, since='2026-08-21', origins=(LocalOrigin(entry='capabilities[0]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.string', scope=Scope(backend=CONST_BACKEND.NARWHALS, applicability=FamilyWide()), source=FactSource.MOUNTAINASH, domain=Domain.STRING, entry='DECLARATIONS[11].facts[0]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/string.py', entry='DECLARATIONS[11].facts[0]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='custom time parsing is supported only by Polars', probe_exempt='Custom time parsing is covered by conform temporal contract tests'), CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME, subject='failure_behavior', selector=Selector(kind='exact', value='null')), level=CapabilityLevel.UNSUPPORTED, since='2026-08-21', origins=(LocalOrigin(entry='capabilities[1]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.string', scope=Scope(backend=CONST_BACKEND.NARWHALS, applicability=FamilyWide()), source=FactSource.MOUNTAINASH, domain=Domain.STRING, entry='DECLARATIONS[11].facts[1]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/string.py', entry='DECLARATIONS[11].facts[1]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='null-on-invalid custom time parsing is supported only by Polars'),), evidence_refs=(CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/string.py', entry='DECLARATIONS[11]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a'),))
