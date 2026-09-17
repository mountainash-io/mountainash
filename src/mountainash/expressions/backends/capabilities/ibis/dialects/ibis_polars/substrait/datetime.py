"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel
from mountainash.core.capabilities.declarations import LocalOrigin
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.capabilities.identity import Dialect
from mountainash.core.capabilities.identity import Scope
from mountainash.core.capabilities.declarations import FactSource
from mountainash.core.capabilities.capture import CapturedAddress
from mountainash.core.capabilities.capture import SourceOrigin
from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(domain=Domain.DATETIME, capabilities=(CapabilityAssertion(key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR, subject='unit', selector=Selector(kind='exact', value='MONTH')), level=CapabilityLevel.UNSUPPORTED, since='2026-08-16', origins=(LocalOrigin(entry='capabilities[0]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.datetime.rounding', scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name='ibis-polars')), source=FactSource.SUBSTRAIT, domain=Domain.DATETIME, entry='DECLARATIONS[0].facts[12]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/datetime/rounding.py', entry='DECLARATIONS[0].facts[12]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- CEIL/ROUND_TIE_DOWN/ROUND_TIE_UP cannot compute the next calendar boundary; verified 2026-08-16, ibis 12.0.0"), CapabilityAssertion(key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR, subject='unit', selector=Selector(kind='exact', value='YEAR')), level=CapabilityLevel.UNSUPPORTED, since='2026-08-16', origins=(LocalOrigin(entry='capabilities[1]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.datetime.rounding', scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name='ibis-polars')), source=FactSource.SUBSTRAIT, domain=Domain.DATETIME, entry='DECLARATIONS[0].facts[13]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/datetime/rounding.py', entry='DECLARATIONS[0].facts[13]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- CEIL/ROUND_TIE_DOWN/ROUND_TIE_UP cannot compute the next calendar boundary; verified 2026-08-16, ibis 12.0.0"),), evidence_refs=(CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/datetime/rounding.py', entry='DECLARATIONS[0]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a'),))
