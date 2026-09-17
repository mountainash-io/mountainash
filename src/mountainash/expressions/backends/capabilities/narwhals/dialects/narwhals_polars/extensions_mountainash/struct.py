"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
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

SEGMENT = CapabilitySegment(domain=Domain.STRUCT, capabilities=(CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST, subject='failure_behavior', selector=Selector(kind='predicate', value=Predicate(clauses=(Clause(path='failure_behavior', op=ClauseOp.EQ, operand='null'),)))), level=CapabilityLevel.UNSUPPORTED, since='2026-08-24', origins=(LocalOrigin(entry='capabilities[0]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.struct', scope=Scope(backend=CONST_BACKEND.NARWHALS, applicability=Dialect(name='narwhals-polars')), source=FactSource.MOUNTAINASH, domain=Domain.STRUCT, entry='DECLARATIONS[1].facts[1]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/struct.py', entry='DECLARATIONS[1].facts[1]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='This backend cannot execute STRUCT.CAST for the requested failure behavior'),), evidence_refs=(CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/struct.py', entry='DECLARATIONS[1]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a'),))
