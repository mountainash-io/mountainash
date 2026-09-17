"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_BOOLEAN
from mountainash.core.capabilities.schema import ClauseOp
from mountainash.core.capabilities.schema import Clause
from mountainash.core.capabilities.schema import Predicate
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

SEGMENT = CapabilitySegment(domain=Domain.BOOLEAN, capabilities=(CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_BOOLEAN.PARSE_TOKENS, subject='failure_behavior', selector=Selector(kind='predicate', value=Predicate(clauses=(Clause(path='failure_behavior', op=ClauseOp.EQ, operand='throw'),)))), level=CapabilityLevel.UNSUPPORTED, since='2026-08-25', origins=(LocalOrigin(entry='capabilities[0]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.boolean', scope=Scope(backend=CONST_BACKEND.IBIS, applicability=Dialect(name='ibis-sqlite')), source=FactSource.MOUNTAINASH, domain=Domain.BOOLEAN, entry='DECLARATIONS[2].facts[0]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/boolean.py', entry='DECLARATIONS[2].facts[0]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='ibis-sqlite cannot enforce throw-on-invalid boolean tokens'),), evidence_refs=(CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/boolean.py', entry='DECLARATIONS[2]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a'),))
