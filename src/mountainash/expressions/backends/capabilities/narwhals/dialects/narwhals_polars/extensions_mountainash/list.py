"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import OperationTarget
from mountainash.core.capabilities.schema import Scenario

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.schema import ClauseOp
from mountainash.core.capabilities.schema import Clause
from mountainash.core.capabilities.schema import Predicate
from mountainash.core.capabilities.schema import Boundary
from mountainash.core.capabilities.schema import Enforcement
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.LIST,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="item_type",
                selector=Selector(kind="exact", value="datetime"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="item_type",
                selector=Selector(kind="exact", value="time"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="item_type", op=ClauseOp.EQ, operand="integer"),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="item_type", op=ClauseOp.EQ, operand="boolean"),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="item_type", op=ClauseOp.EQ, operand="number"),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="item_type", op=ClauseOp.EQ, operand="date"),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.CAST_ITEMS,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="null"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.GET, subject="index"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-01",
            message="narwhals list.get() (and list.last(), which calls get(-1)) rejects negative indices on the polars backend.",
            workaround="Use a non-negative index, or the polars/ibis backends.",
            issue="NW-LIST-04",
            boundary=Boundary.MATERIALIZE,
            native_errors=(ValueError,),
            condition="index < 0",
            probe_exempt="value-conditioned (negative index) — not a structural param gate",
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
        ),
    ),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.ALL),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="bool", value="true"),)
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="bool", value="false"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="false"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.ALL),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="bool", value="true"),
                                                        CaptureValue(tag="bool", value="true"),
                                                        CaptureValue(tag="bool", value="true"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="bool", value="true"),
                                                        CaptureValue(tag="bool", value="false"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="bool", value="false"),
                                                        CaptureValue(tag="bool", value="false"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="false"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.ANY),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="bool", value="true"),)
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="bool", value="false"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="false"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.ANY),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="bool", value="true"),
                                                        CaptureValue(tag="bool", value="false"),
                                                        CaptureValue(tag="bool", value="true"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="bool", value="false"),
                                                        CaptureValue(tag="bool", value="false"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="bool", value="true"),
                                                        CaptureValue(tag="bool", value="true"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="true"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MAX),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                        CaptureValue(tag="integer", value="30"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="2"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MAX),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="30"),
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="15"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="0"),
                                CaptureValue(tag="integer", value="1"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MIN),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="0"),
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="0"),
                                CaptureValue(tag="integer", value="0"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MIN),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="30"),
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="15"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="2"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.CONCAT),
                scenario=Scenario(
                    arguments=(
                        (
                            "other",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="b"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="a"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                                CaptureValue(tag="sequence", value=()),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="sequence", value=()),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="2"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="3"),
                                        CaptureValue(tag="integer", value="4"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.CONCAT),
                scenario=Scenario(
                    arguments=(
                        (
                            "other",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="b"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="a"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="6"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="7"),
                                                        CaptureValue(tag="integer", value="8"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="5"),
                                        CaptureValue(tag="integer", value="6"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="3"),
                                        CaptureValue(tag="integer", value="4"),
                                        CaptureValue(tag="integer", value="7"),
                                        CaptureValue(tag="integer", value="8"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES),
                scenario=Scenario(
                    arguments=(
                        (
                            "item",
                            CaptureValue(tag="integer", value="2"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="4"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="0"),
                                CaptureValue(tag="integer", value="1"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES),
                scenario=Scenario(
                    arguments=(
                        (
                            "item",
                            CaptureValue(tag="integer", value="99"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="6"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="0"),
                                CaptureValue(tag="integer", value="0"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.DIFF),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                        CaptureValue(tag="integer", value="35"),
                                                        CaptureValue(tag="integer", value="50"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="6"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="null", value=""),
                                        CaptureValue(tag="integer", value="10"),
                                        CaptureValue(tag="integer", value="15"),
                                        CaptureValue(tag="integer", value="15"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="null", value=""),
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="3"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.DIFF),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="null", value=""),
                                        CaptureValue(tag="integer", value="0"),
                                        CaptureValue(tag="integer", value="0"),
                                        CaptureValue(tag="integer", value="0"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="3"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="4"),
                                        CaptureValue(tag="integer", value="5"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="null", value=""),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="null", value=""),
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="3"),
                                    ),
                                ),
                                CaptureValue(tag="sequence", value=()),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="4"),
                                        CaptureValue(tag="integer", value="5"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.EXPLODE),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="1"),)
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="2"),)
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="3"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="relation_select_to_dict"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "val",
                                    CaptureValue(
                                        tag="sequence",
                                        value=(
                                            CaptureValue(tag="integer", value="1"),
                                            CaptureValue(tag="integer", value="2"),
                                            CaptureValue(tag="integer", value="3"),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="list.explode raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.EXPLODE),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="30"),)
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="40"),
                                                        CaptureValue(tag="integer", value="50"),
                                                        CaptureValue(tag="integer", value="60"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "id",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="relation_select_to_dict"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "id",
                                    CaptureValue(
                                        tag="sequence",
                                        value=(
                                            CaptureValue(tag="integer", value="1"),
                                            CaptureValue(tag="integer", value="1"),
                                            CaptureValue(tag="integer", value="2"),
                                            CaptureValue(tag="integer", value="3"),
                                            CaptureValue(tag="integer", value="3"),
                                            CaptureValue(tag="integer", value="3"),
                                        ),
                                    ),
                                ),
                                (
                                    "val",
                                    CaptureValue(
                                        tag="sequence",
                                        value=(
                                            CaptureValue(tag="integer", value="10"),
                                            CaptureValue(tag="integer", value="20"),
                                            CaptureValue(tag="integer", value="30"),
                                            CaptureValue(tag="integer", value="40"),
                                            CaptureValue(tag="integer", value="50"),
                                            CaptureValue(tag="integer", value="60"),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="list.explode raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY),
                scenario=Scenario(
                    arguments=(
                        (
                            "n",
                            CaptureValue(tag="integer", value="2"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="6"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                        CaptureValue(tag="integer", value="30"),
                                                        CaptureValue(tag="integer", value="40"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="3"),
                                        CaptureValue(tag="integer", value="5"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="10"),
                                        CaptureValue(tag="integer", value="30"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY),
                scenario=Scenario(
                    arguments=(
                        (
                            "n",
                            CaptureValue(tag="integer", value="3"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="6"),
                                                        CaptureValue(tag="integer", value="7"),
                                                        CaptureValue(tag="integer", value="8"),
                                                        CaptureValue(tag="integer", value="9"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="4"),
                                        CaptureValue(tag="integer", value="7"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.HEAD),
                scenario=Scenario(
                    arguments=(
                        (
                            "n",
                            CaptureValue(tag="integer", value="3"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                        CaptureValue(tag="integer", value="30"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="3"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="10"),
                                        CaptureValue(tag="integer", value="20"),
                                        CaptureValue(tag="integer", value="30"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.HEAD),
                scenario=Scenario(
                    arguments=(
                        (
                            "n",
                            CaptureValue(tag="integer", value="5"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="10"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="2"),
                                    ),
                                ),
                                CaptureValue(tag="sequence", value=(CaptureValue(tag="integer", value="10"),)),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.JOIN),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "separator",
                            CaptureValue(tag="text", value=""),
                        ),
                    ),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="text", value="a"),
                                                        CaptureValue(tag="text", value="b"),
                                                        CaptureValue(tag="text", value="c"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="text", value="x"),
                                                        CaptureValue(tag="text", value="y"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="abc"),
                                CaptureValue(tag="text", value="xy"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.JOIN),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "separator",
                            CaptureValue(tag="text", value=","),
                        ),
                    ),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="text", value="only"),)
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="text", value="one"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="only"),
                                CaptureValue(tag="text", value="one"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.JOIN),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "separator",
                            CaptureValue(tag="text", value="-"),
                        ),
                    ),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="text", value="a"),
                                                        CaptureValue(tag="text", value="b"),
                                                        CaptureValue(tag="text", value="c"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="text", value="x"),
                                                        CaptureValue(tag="text", value="y"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="text", value="hello"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="a-b-c"),
                                CaptureValue(tag="text", value="x-y"),
                                CaptureValue(tag="text", value="hello"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="4"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="5"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="7"),
                                                        CaptureValue(tag="integer", value="7"),
                                                        CaptureValue(tag="integer", value="7"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="1"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="1"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="sequence", value=()),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="1"),)
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="sequence", value=()),
                                CaptureValue(tag="sequence", value=(CaptureValue(tag="integer", value="1"),)),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="1"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="6"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="3"),
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="1"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="5"),
                                        CaptureValue(tag="integer", value="4"),
                                    ),
                                ),
                                CaptureValue(tag="sequence", value=(CaptureValue(tag="integer", value="6"),)),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE),
                scenario=Scenario(
                    arguments=(
                        (
                            "other",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="b"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="a"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(tag="sequence", value=(CaptureValue(tag="sequence", value=()),)),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE),
                scenario=Scenario(
                    arguments=(
                        (
                            "other",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="b"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="a"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="6"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="6"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="sequence", value=(CaptureValue(tag="integer", value="1"),)),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="4"),
                                        CaptureValue(tag="integer", value="5"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.SET_INTERSECTION),
                scenario=Scenario(
                    arguments=(
                        (
                            "other",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="b"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="a"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(tag="sequence", value=(CaptureValue(tag="sequence", value=()),)),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.SET_INTERSECTION),
                scenario=Scenario(
                    arguments=(
                        (
                            "other",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="b"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="a"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="6"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="3"),
                                    ),
                                ),
                                CaptureValue(tag="sequence", value=(CaptureValue(tag="integer", value="5"),)),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.SET_UNION),
                scenario=Scenario(
                    arguments=(
                        (
                            "other",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="b"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="a"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="3"),
                                        CaptureValue(tag="integer", value="4"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.SET_UNION),
                scenario=Scenario(
                    arguments=(
                        (
                            "other",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="b"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="a"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="6"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="3"),
                                        CaptureValue(tag="integer", value="4"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="4"),
                                        CaptureValue(tag="integer", value="5"),
                                        CaptureValue(tag="integer", value="6"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT),
                scenario=Scenario(
                    arguments=(
                        (
                            "n",
                            CaptureValue(tag="integer", value="-1"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                        CaptureValue(tag="integer", value="30"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="3"),
                                        CaptureValue(tag="integer", value="4"),
                                        CaptureValue(tag="null", value=""),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="20"),
                                        CaptureValue(tag="integer", value="30"),
                                        CaptureValue(tag="null", value=""),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT),
                scenario=Scenario(
                    arguments=(
                        (
                            "n",
                            CaptureValue(tag="integer", value="1"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                        CaptureValue(tag="integer", value="30"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="null", value=""),
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="3"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="null", value=""),
                                        CaptureValue(tag="integer", value="10"),
                                        CaptureValue(tag="integer", value="20"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.SLICE),
                scenario=Scenario(
                    arguments=(
                        (
                            "offset",
                            CaptureValue(tag="integer", value="0"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "length",
                            CaptureValue(tag="integer", value="2"),
                        ),
                    ),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                        CaptureValue(tag="integer", value="30"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="2"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="10"),
                                        CaptureValue(tag="integer", value="20"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.SLICE),
                scenario=Scenario(
                    arguments=(
                        (
                            "offset",
                            CaptureValue(tag="integer", value="1"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "length",
                            CaptureValue(tag="integer", value="3"),
                        ),
                    ),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                        CaptureValue(tag="integer", value="30"),
                                                        CaptureValue(tag="integer", value="40"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="2"),
                                        CaptureValue(tag="integer", value="3"),
                                        CaptureValue(tag="integer", value="4"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="20"),
                                        CaptureValue(tag="integer", value="30"),
                                        CaptureValue(tag="integer", value="40"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.STD),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="7"),
                                                        CaptureValue(tag="integer", value="9"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(tag="sequence", value=(CaptureValue(tag="float", value="0x1.0000000000000p+1"),)),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.TAIL),
                scenario=Scenario(
                    arguments=(
                        (
                            "n",
                            CaptureValue(tag="integer", value="2"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="3"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                        CaptureValue(tag="integer", value="30"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="4"),
                                        CaptureValue(tag="integer", value="5"),
                                    ),
                                ),
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="20"),
                                        CaptureValue(tag="integer", value="30"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.TAIL),
                scenario=Scenario(
                    arguments=(
                        (
                            "n",
                            CaptureValue(tag="integer", value="5"),
                        ),
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="10"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(
                                    tag="sequence",
                                    value=(
                                        CaptureValue(tag="integer", value="1"),
                                        CaptureValue(tag="integer", value="2"),
                                    ),
                                ),
                                CaptureValue(tag="sequence", value=(CaptureValue(tag="integer", value="10"),)),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.VAR),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="2"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="4"),
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="5"),
                                                        CaptureValue(tag="integer", value="7"),
                                                        CaptureValue(tag="integer", value="9"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(tag="sequence", value=(CaptureValue(tag="float", value="0x1.0000000000000p+2"),)),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text",
                            value="Narwhals lacks native list operations; Mountainash raises BackendCapabilityError.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The listed list operation raises on narwhals-polars.",
            since="2026-08-06",
            workaround="Use a Polars or Ibis backend for these list operations",
            issue="NW-LIST-05",
        ),
    ),
)
