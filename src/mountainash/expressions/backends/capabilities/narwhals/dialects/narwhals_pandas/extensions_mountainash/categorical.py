"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_CATEGORICAL
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

SEGMENT = CapabilitySegment(domain=Domain.CATEGORICAL, capabilities=(CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_CATEGORICAL.CAST, subject='value_type', selector=Selector(kind='predicate', value=Predicate(clauses=(Clause(path='failure_behavior', op=ClauseOp.EQ, operand='null'), Clause(path='value_type', op=ClauseOp.EQ, operand='integer'),)))), level=CapabilityLevel.UNSUPPORTED, since='2026-08-24', origins=(LocalOrigin(entry='capabilities[0]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.categorical', scope=Scope(backend=CONST_BACKEND.NARWHALS, applicability=Dialect(name='narwhals-pandas')), source=FactSource.MOUNTAINASH, domain=Domain.CATEGORICAL, entry='DECLARATIONS[1].facts[1]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/categorical.py', entry='DECLARATIONS[1].facts[1]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='This backend cannot execute CATEGORICAL.CAST for the requested value type and failure behavior'),), evidence_refs=(CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/categorical.py', entry='DECLARATIONS[1]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a'),))
