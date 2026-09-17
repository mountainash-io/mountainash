"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
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
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(domain=Domain.LIST, capabilities=(CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE, subject='*'), level=CapabilityLevel.UNSUPPORTED, since='2026-08-24', origins=(LocalOrigin(entry='capabilities[0]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.list', scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name='ibis-sqlite')), source=FactSource.MOUNTAINASH, domain=Domain.LIST, entry='DECLARATIONS[2].facts[7]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/list.py', entry='DECLARATIONS[2].facts[7]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='This backend cannot execute LIST.PARSE for the requested item type and failure behavior', probe_exempt='LIST parsing is covered by conform list contract tests'), CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.CAST_ITEMS, subject='failure_behavior', selector=Selector(kind='exact', value='throw')), level=CapabilityLevel.UNSUPPORTED, since='2026-08-24', origins=(LocalOrigin(entry='capabilities[1]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.list', scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name='ibis-sqlite')), source=FactSource.MOUNTAINASH, domain=Domain.LIST, entry='DECLARATIONS[2].facts[13]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/list.py', entry='DECLARATIONS[2].facts[13]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior'), CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.CAST_ITEMS, subject='failure_behavior', selector=Selector(kind='exact', value='null')), level=CapabilityLevel.UNSUPPORTED, since='2026-08-24', origins=(LocalOrigin(entry='capabilities[2]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.list', scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name='ibis-sqlite')), source=FactSource.MOUNTAINASH, domain=Domain.LIST, entry='DECLARATIONS[2].facts[16]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/list.py', entry='DECLARATIONS[2].facts[16]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior'),), evidence_refs=(CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/list.py', entry='DECLARATIONS[2]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a'),))
