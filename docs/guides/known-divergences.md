# Known Divergences — Reading the Catalog

The generated [catalog](../known-divergences.md) renders published capability
information, explicit policies, and display-only examples. It is produced by
`scripts/generate_divergences_catalog.py`; do not edit the generated catalog
by hand.

## Authority and identity

Capability declarations are scoped by their physical `SEGMENT` home under
`src/mountainash/{expressions,relations}/backends/capabilities/`. Its path
fixes the backend, family or dialect applicability, Substrait/extension
namespace, and domain. The module exports local declarations only; the loader
derives qualified keys and source locations during publication.

There are two deliberately separate declaration types:

- **`CapabilityInformation`** is a descriptive native or public statement.
  It has no executable consumer. A family home can describe a behavior shared
  by that family, while a dialect home can describe a concrete dialect.
- **`CapabilityPolicyRule`** is an executable rule with an explicit consumer
  and action. It belongs only to a concrete dialect. Policies are never
  inferred from a family description or from related information.

The native/public layer belongs to information, not to a test result. An
optional issue reference is descriptive metadata; it does not establish
support, select a policy, or imply a version range.

## Local authoring and stored access

For example, a dialect-local module declares information and an independent
policy in its `SEGMENT`. This shape uses the current constructors; it does not
repeat the scope supplied by the module's physical location.

```python
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
    Selector,
)
from mountainash.core.capabilities.schema import (
    CapabilityLevel,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as STRING,
)

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                STRING.STARTS_WITH,
                "case_sensitivity",
                Selector(kind="exact", value="CASE_INSENSITIVE_ASCII"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-09-18",
            message="The native operation cannot preserve the requested case behavior.",
        ),
    ),
    policies=(
        CapabilityPolicyRule(
            key=CapabilityKey(STRING.STARTS_WITH, "substring"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-09-18",
            message="This concrete dialect requires a literal substring.",
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
        ),
    ),
)
```

The loader publishes physical segments. A direct registry setup, such as an
isolated test, must construct one `BoundSegment` and call
`CapabilityRegistry.register_segment()` once. The call validates the complete
segment before replacing the registry generation: a rejected segment leaves
the previous generation intact. Do not publish its information and policies in
separate calls.

```python
from mountainash.core.capabilities.declarations import BoundSegment
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.constants import CONST_BACKEND

scope = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))
CapabilityRegistry.register_segment(
    BoundSegment(
        module=(
            "mountainash.expressions.backends.capabilities.ibis."
            "dialects.ibis_duckdb.substrait.string"
        ),
        scope=scope,
        segment=SEGMENT,
    )
)
```

Capture inspection keeps exact and composed information distinct. A scope
reader returns only declarations owned by that exact scope. When both scopes
were captured, `composed_information()` explicitly combines a dialect's
information with its family information; it does not compose policies.

```python
from mountainash.core.capabilities.catalogue import (
    CatalogueQuery,
    InformationQuery,
    PolicyQuery,
)

capture = CapabilityRegistry.capture()
records = capture.search(
    CatalogueQuery(
        information=InformationQuery(),
        policies=PolicyQuery(),
    )
)
exact_information = capture.reader(scope).search(InformationQuery())
composed_information = capture.composed_information(scope)
```

`records.information` and `records.policies` are independent result fields.
Exact `get()` raises on a missing qualified key and `get_optional()` returns
`None`; neither method falls back from a dialect to its family.

## Execution policies

Capability declarations are data. An execution policy is the separate,
request-local statement of which optional actions the runtime may take for
one request. Wrap a public terminal in `ma.capability_policy()`; the ambient
default is `ma.CapabilityPolicy.checked()`.

```python
import mountainash as ma
import polars as pl

data = pl.DataFrame({"x": [1, 2]})
with ma.capability_policy(ma.CapabilityPolicy.native_debugging()):
    result = ma.relation(data).select((ma.col("x") + 1).alias("y")).to_polars()
assert result["y"].to_list() == [2, 3]
```

This is an executable public example: inside the scope the request runs with
gate blocking and result protection active and exception enrichment off, and
the projected result is `[2, 3]`. The presets differ only in which optional
actions they demand:

- `CapabilityPolicy.checked()` — every consumer active (the ambient default).
- `CapabilityPolicy.native_debugging()` — protection stays on; exception
  enrichment is disabled so native error surfaces reach you unmodified.
  It disables enrichment, not protection.
- `CapabilityPolicy.trusted()` — no optional action runs. It disables
  optional actions only: required backend conversion, ordinary argument
  validation, and explicitly requested conformance still execute, because
  they belong to backend code rather than to a policy.

Each preset accepts keyword overrides, for example
`native_debugging(protection="none")`. Consumers are selected by demand:
without a demanded gate a declared block is not applied, and without
demanded enrichment a native failure is not rewritten into a public
capability error.

Two boundaries are deliberate and observed, not authored:

- **Unknown version coordinates.** A declaration that constrains a version
  coordinate the observed environment does not supply matches as
  *indeterminate*: an unknown version neither manufactures a policy outcome
  nor certifies support. Explicitly unconstrained declarations match without
  acquiring version coordinates.
- **Extracted native objects.** Executing a native object that was produced
  inside Mountainash and then invoked outside it is outside later
  interception guarantees. Native construction observations are captured at
  the declared construction stage and are never attributed to later
  Mountainash execution.

### Authoring applicability and variants

The examples above are observations. Applicability and variants are the two
authored shapes that scope a declaration; both are claims that must carry
their own evidence.

Regions (`Region`, `CoordinateConstraint`, `Applicability`) are authored
finite unions of environment regions. One record with identical behavior
over several intervals carries a union of regions, not one variant per
interval:

```python
from mountainash.core.capabilities.applicability import (
    Applicability,
    ComparisonScheme,
    CoordinateConstraint,
    Region,
)

APPLICABILITY = Applicability(regions=(
    Region(constraints=(
        CoordinateConstraint(
            "package", "ibis-framework", ComparisonScheme.PEP440,
            equal="12.0.0",
        ),
        CoordinateConstraint(
            "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
            lower="1.2", upper="1.3", upper_inclusive=False,
        ),
    )),
    Region(constraints=(
        CoordinateConstraint(
            "package", "ibis-framework", ComparisonScheme.PEP440,
            equal="12.0.0",
        ),
        CoordinateConstraint(
            "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
            lower="1.4", upper="1.5", upper_inclusive=False,
        ),
    )),
))
```

Pass `applicability=APPLICABILITY` on a `CapabilityInformation` or
`CapabilityPolicyRule`. Variants (`CapabilityKey(..., variant="...")`) name
records that genuinely need to coexist; a variant name identifies a record,
never applicability, priority or fallback, and exact unqualified lookup
never falls back to a variant or vice versa.

Keep the two sides distinct:

- An **exact observation** is an `Environment` of typed coordinates that
  preserves raw version text and original labels. It states what one
  concrete environment supplied.
- An **authored range** is a `Region`/`Applicability` claim matched against
  observations. No `since` date, upstream issue status, evidence timestamp,
  or fixed-version value becomes a range automatically; author production
  version regions only with their own concrete evidence, and never infer a
  family-wide range from one dialect or environment.

## Observations and tests

Tests are ordinary case-owned tests. Each test supplies its concrete input,
executes the selected public or native path, and asserts its own result or
exception. A capability policy can make a call refuse at its declared boundary,
but it neither manufactures a test case nor supplies an oracle.

Keep native behavior and public behavior distinct. A public
`BackendCapabilityError` is a policy outcome, not an observation of native
backend behavior. Do not infer behavior for a backend family by running one
dialect, and do not infer a fixed-version range from one environment.

An expected failure belongs only to the concrete case that owns its reason and
oracle. Discovery remains closed: an unsupported outcome not owned by that
case is an ordinary failure to investigate, not a reason to broaden an
expectation.

## Adding a claim

1. Identify the operation, parameter or option, concrete scope, and whether
   the statement is descriptive information or an executable policy.
2. Put the local declaration in the physical scoped `SEGMENT` for its domain.
   Use `CapabilityInformation` for native/public description and
   `CapabilityPolicyRule` only when an explicit concrete-dialect consumer and
   action are required.
3. State only the behavior supported by the source being authored. Do not turn
   an issue reference, display example, or one environment into a support or
   affected-version claim.
4. Keep a test's inputs and oracle in that test. Add a narrow expected outcome
   only when the case itself owns the concrete reason.
5. Add an issue reference only when it is useful descriptive metadata; it does
   not change routing or test selection.

## Correcting or retiring a claim

Correct or remove only the information or policy rule whose own scope and
behavior changed. A passing concrete case does not establish that a related
operation, family, or dialect has changed. Remove an obsolete case-owned
expectation with the behavior it described; do not preserve it as a broad
fallback.

## Gap inventories

Gap inventories are an independent, explicitly acquired inspection namespace.
Pass the inventory tuple directly to a capture, then query it with `GapQuery`.
No inventory is silently discovered from declarations or from test execution.

```python
from mountainash.core.capabilities.catalogue import CatalogueQuery, GapQuery

capture = CapabilityRegistry.capture(inventories=(inventory,))
gaps = capture.search(
    CatalogueQuery(gaps=GapQuery(inventory=inventory.name))
).gaps
```

Calling `capture()` without inventories does not make a gap inventory
available. Passing `inventories=()` explicitly captures an empty inventory
set. This keeps absence of acquired inventory separate from an acquired
inventory that contains no gaps.

## Maintenance commands

```bash
# Render generated capability projections and the display catalog.
python -m mountainash.core.capabilities.render_markdown
python scripts/generate_divergences_catalog.py

# Check whether the generated display catalog is current.
python scripts/generate_divergences_catalog.py --check
```

`scripts/fixtures/divergence_examples.json` contains render-only illustrations
used by `scripts/generate_divergences_catalog.py`. The generator joins those
illustrations with authored information, policies, and issue metadata to write
the catalog. It does not execute tests, probe a backend, or create current
evidence. A successful render or `--check` therefore says nothing about
installed-package behavior, performance, or a newly verified divergence.

See also [backend architecture](backend-architecture.md) and the enforced
cross-backend consistency and upstream-fix-monitoring principles.
