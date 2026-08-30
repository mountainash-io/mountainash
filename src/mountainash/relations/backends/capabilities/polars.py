"""Import-safe Polars relation-backend capability declarations.

Migrated from ``PolarsBaseRelationSystem.CAPABILITIES`` in
``mountainash.relations.backends.relation_systems.polars.base``
(2026-08 capability-architecture PR). Extracted; the class still carries the
inline tuple until Task 11 rewires the class body.
"""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)


POLARS_REL_CAPABILITIES: tuple[CapabilityFact, ...] = (
    CapabilityFact(
        operation_key=RKEY_MOUNTAINASH_REL.READ_RESOURCE, param="resource",
        level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.POLARS,
        message="CSV dialect fields require the portable provider fallback reader",
        workaround="none needed — mountainash routes automatically",
        since="2026-08-30",
        condition="resource.dialect.escape_char or resource.dialect.line_terminator or resource.dialect.double_quote or resource.dialect.skip_initial_space or resource.dialect.header_rows or resource.dialect.header_join or resource.dialect.comment_char or resource.dialect.comment_rows",
        enforcement=Enforcement.ROUTER_METADATA,
        probe_exempt="router, not gate — fallback handles it; behaviour covered by relations resource tests",
    ),
)


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)


_EVIDENCE = ProbeEvidence(
    probe_date="2026-07-05",  # earliest `since` in the tuple
    library_versions=(),      # not recorded in the source declarations
    fixtures=(),
)


DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.POLARS, domain=Domain.RELATION,
        source=FactSource.MOUNTAINASH, facts=POLARS_REL_CAPABILITIES,
        evidence=_EVIDENCE,
    ),
)
