"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import Selector
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

SEGMENT = CapabilitySegment(domain=Domain.DATETIME, capabilities=(CapabilityAssertion(key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE, subject='failure_behavior', selector=Selector(kind='exact', value='null')), level=CapabilityLevel.UNSUPPORTED, since='2026-08-21', origins=(LocalOrigin(entry='capabilities[0]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.datetime.strptime', scope=Scope(backend=CONST_BACKEND.NARWHALS, applicability=FamilyWide()), source=FactSource.SUBSTRAIT, domain=Domain.DATETIME, entry='DECLARATIONS[1].facts[1]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/datetime/strptime.py', entry='DECLARATIONS[1].facts[1]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='null-on-invalid custom temporal parsing is supported only by Polars'), CapabilityAssertion(key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP, subject='failure_behavior', selector=Selector(kind='exact', value='null')), level=CapabilityLevel.UNSUPPORTED, since='2026-08-21', origins=(LocalOrigin(entry='capabilities[1]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.datetime.strptime', scope=Scope(backend=CONST_BACKEND.NARWHALS, applicability=FamilyWide()), source=FactSource.SUBSTRAIT, domain=Domain.DATETIME, entry='DECLARATIONS[1].facts[2]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/datetime/strptime.py', entry='DECLARATIONS[1].facts[2]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='null-on-invalid custom temporal parsing is supported only by Polars'),), evidence_refs=(CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/datetime/strptime.py', entry='DECLARATIONS[1]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a'),))
