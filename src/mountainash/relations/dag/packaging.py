"""Frictionless packaging helpers for RelationDAG."""
from __future__ import annotations

from typing import TYPE_CHECKING

from mountainash.core.resource_ref import ResourceRef

if TYPE_CHECKING:
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.dag.dag import RelationDAG
    from mountainash.typespec.datapackage import DataResource, DataPackage


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


def to_package(dag: RelationDAG) -> DataPackage:
    """Export a DAG as a Frictionless DataPackage descriptor."""
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
            res = root.resource
            if res.name != name:
                res = res.model_copy(update={"name": name})
            resources.append(res)
            continue

        output_schema = getattr(relation, "output_schema", None)
        if output_schema is None:
            missing.append(name)
            continue
        resources.append(
            DataResource.model_validate(
                {
                    "name": name,
                    "path": f"{name}.csv",
                    "type": "table",
                    "format": "csv",
                    "schema": output_schema,
                }
            )
        )

    for name, ref in dag.assets.items():
        res = ref.resource
        if res.name != name:
            res = res.model_copy(update={"name": name})
        resources.append(res)

    if missing:
        raise MissingResourceSchema(
            f"cannot export to DataPackage; relations without schema: {missing}"
        )
    return DataPackage(resources=resources)
