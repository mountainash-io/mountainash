"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL
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
from mountainash.core.capabilities.schema import ClauseOp
from mountainash.core.capabilities.schema import Clause
from mountainash.core.capabilities.schema import Predicate
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(domain=Domain.RELATION, capabilities=(CapabilityAssertion(key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX, subject='*'), level=CapabilityLevel.UNSUPPORTED, since='2026-08-01', origins=(LocalOrigin(entry='capabilities[0]'), SourceOrigin(module='mountainash.relations.backends.capabilities.ibis', scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name='ibis-polars')), source=FactSource.MOUNTAINASH, domain=Domain.RELATION, entry='DECLARATIONS[0].facts[0]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/relations/backends/capabilities/ibis.py', entry='DECLARATIONS[0].facts[0]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='with_row_index lowers to a window function (row_number); the ibis Polars backend has no WindowFunction translation rule.', workaround='Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends.', issue='IB-REL-01', probe_exempt='relation op-level gap; covered by relation with_row_index cross-backend tests'), CapabilityAssertion(key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.JOIN_ASOF, subject='strategy', selector=Selector(kind='predicate', value=Predicate(clauses=(Clause(path='strategy', op=ClauseOp.IN, operand=frozenset(('forward', 'nearest',))),)))), level=CapabilityLevel.UNSUPPORTED, since='2026-08-18', origins=(LocalOrigin(entry='capabilities[1]'), SourceOrigin(module='mountainash.relations.backends.capabilities.ibis', scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name='ibis-polars')), source=FactSource.MOUNTAINASH, domain=Domain.RELATION, entry='DECLARATIONS[0].facts[2]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/relations/backends/capabilities/ibis.py', entry='DECLARATIONS[0].facts[2]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='join_asof forward/nearest lowers to a non-equality candidate join; the ibis Polars backend rejects non-equality join predicates (TypeError: Only equality join predicates supported with pandas).', workaround='Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends.', issue='IB-REL-15'),), evidence_refs=(CapturedAddress(repository='mountainash', path='src/mountainash/relations/backends/capabilities/ibis.py', entry='DECLARATIONS[0]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a'),))
