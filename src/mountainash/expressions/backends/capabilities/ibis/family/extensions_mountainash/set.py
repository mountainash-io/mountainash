"""Scope-owned capability declarations; import-safe data only."""
from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_SET
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

SEGMENT = CapabilitySegment(domain=Domain.SET, capabilities=(CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_SET.IS_IN, subject='haystack'), level=CapabilityLevel.POLYMORPHIC, since='2026-07-05', origins=(LocalOrigin(entry='capabilities[0]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.polymorphic', scope=Scope(backend=CONST_BACKEND.IBIS, applicability=FamilyWide()), source=FactSource.MOUNTAINASH, domain=Domain.SET, entry='DECLARATIONS[1].facts[0]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/polymorphic.py', entry='DECLARATIONS[1].facts[0]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker)', probe_exempt='polymorphic — both paths supported by design'), CapabilityAssertion(key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_SET.IS_NOT_IN, subject='haystack'), level=CapabilityLevel.POLYMORPHIC, since='2026-07-05', origins=(LocalOrigin(entry='capabilities[1]'), SourceOrigin(module='mountainash.expressions.backends.capabilities.polymorphic', scope=Scope(backend=CONST_BACKEND.IBIS, applicability=FamilyWide()), source=FactSource.MOUNTAINASH, domain=Domain.SET, entry='DECLARATIONS[1].facts[1]', captured=CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/polymorphic.py', entry='DECLARATIONS[1].facts[1]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a')),), message='literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker)', probe_exempt='polymorphic — both paths supported by design'),), evidence_refs=(CapturedAddress(repository='mountainash', path='src/mountainash/expressions/backends/capabilities/polymorphic.py', entry='DECLARATIONS[1]', revision='80dc283a1eb65c33b0b3bae946b3a8f5305cd66a'),))
