"""Frictionless packaging helpers for RelationDAG."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from mountainash.core.resource_ref import ResourceRef

if TYPE_CHECKING:
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.dag.dag import RelationDAG
    from mountainash.typespec.datapackage import DataResource, DataPackage


def _frictionless_from_inferred(schema) -> Optional[dict]:
    """Convert an inferred {col: dtype|status} schema to a Frictionless
    schema dict {"fields": [{"name", "type"}, ...]}, or None if no columns.

    Concrete dtype -> its Frictionless type string; UNKNOWN/UNCONSTRAINED -> "any"
    (best-effort, principle R3: emit, never gate). None ONLY for an empty schema."""
    if not schema:
        return None
    from mountainash.relations.schema_inference import SchemaTypeStatus
    from mountainash.typespec.universal_types import from_canonical
    fields = []
    for name, dt in schema.items():
        if isinstance(dt, SchemaTypeStatus):     # UNKNOWN or UNCONSTRAINED
            type_str = "any"
        else:
            try:
                type_str = from_canonical(dt)[0].value
            except KeyError:
                # Principle R3 (best-effort-introspection): export emits, never gates.
                # A concrete dtype not yet in the canonical→universal boundary map
                # degrades to typeless "any" rather than raising.
                type_str = "any"
        fields.append({"name": name, "type": type_str})
    return {"fields": fields}


def resource_to_relation(ref_or_resource: ResourceRef | DataResource) -> Relation:
    """Wrap a tabular resource in a ResourceReadRelNode relation."""
    ref = (
        ref_or_resource
        if isinstance(ref_or_resource, ResourceRef)
        else ResourceRef(ref_or_resource)
    )
    if not ref.is_tabular:
        raise ValueError(f"resource {ref.resource.name!r} is not tabular")

    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        ResourceReadRelNode,
    )

    return Relation(ResourceReadRelNode(resource=ref.resource))


def _has_unknown(schema) -> bool:
    """Return True if any column in the inferred schema is genuinely UNKNOWN.

    UNCONSTRAINED (explicitly typeless) does NOT count as unknown — it is a
    legitimate declaration of 'any'. Only SchemaTypeStatus.UNKNOWN triggers
    strict-mode rejection (principle best-effort-introspection R4).

    Note: since item 46 (a), un-aliased aggregate measures are inferred
    under their canonical source-column name as UNKNOWN, so strict mode
    sees them. Only measures with no resolvable field root (literal or
    wildcard aggregates) remain absent — a documented best-effort residual.
    """
    from mountainash.relations.schema_inference import SchemaTypeStatus
    return any(v is SchemaTypeStatus.UNKNOWN for v in schema.values())


def to_package(dag: RelationDAG, *, strict: bool = False) -> DataPackage:
    """Export a DAG as a Frictionless DataPackage descriptor.

    Emits a resource for every named tabular relation. A ResourceReadRelNode
    reuses its original DataResource (preserving path/format/dialect for
    round-trip). Any other relation derives its schema via the ref-resolved
    dag.schema(name) authority (NOT relation.output_schema, which lacks a
    resolver and returns {} for ref-containing relations). Assets pass through
    unchanged.

    Default mode is non-fatal (principle best-effort-introspection R3): emits
    a resource per named relation with the best-effort schema (schema-less when
    no columns are determinable). strict=True raises MissingResourceSchema for
    any relation whose inferred schema is empty or contains a genuinely-UNKNOWN
    column (R4). UNCONSTRAINED does NOT trigger strict failure."""
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        ResourceReadRelNode,
    )
    from mountainash.relations.dag.errors import MissingResourceSchema
    from mountainash.typespec.datapackage import DataPackage, DataResource

    resources: list[DataResource] = []
    missing: list[str] = []

    for name, relation in dag.relations.items():
        root = getattr(relation, "_node", None)
        if isinstance(root, ResourceReadRelNode):
            # Fast path: reuse original DataResource (preserves path/format/dialect)
            res = root.resource
            if res.name != name:
                res = res.model_copy(update={"name": name})
            resources.append(res)
            continue

        # Ref-resolved authority: resolves RefRelNodes correctly
        inferred = dag.schema(name)
        out = _frictionless_from_inferred(inferred)

        # FK source is determined by resource kind: pass-through resources
        # emitted their lossless table_schema above (metadata never
        # consulted — no double-emit possible); derived resources emit
        # declared constraint_metadata, in insertion order.
        from mountainash.typespec.frictionless import foreign_key_to_dict

        fk_dicts = [foreign_key_to_dict(fk) for fk in dag.constraints_for(name)]
        if fk_dicts and out is not None:
            out["foreignKeys"] = fk_dicts

        if strict and (not inferred or _has_unknown(inferred)):
            missing.append(name)
            continue

        res_dict: dict = {
            "name": name,
            "path": f"{name}.csv",
            "type": "table",
            "format": "csv",
        }
        if out is not None:  # schema-less when no columns determinable
            res_dict["schema"] = out
        resources.append(DataResource.model_validate(res_dict))

    for name, ref in dag.assets.items():
        res = ref.resource
        if res.name != name:
            res = res.model_copy(update={"name": name})
        resources.append(res)

    if strict and missing:
        raise MissingResourceSchema(
            f"cannot export to DataPackage; relations without schema: {missing}"
        )
    return DataPackage(resources=resources)
