# Data Package v2 descriptors

Mountainash implements the Unit A Frictionless Data Package v2 descriptor boundary. The
storage models retain the authored descriptor graph, while typed schema and dialect
objects are created only when a consumer asks for them.

## Inputs

Use the input method that matches the representation you already have. The methods do
not infer whether a string is a path or JSON.

### Mapping

`DataPackage.from_descriptor()` accepts a mapping. It owns the mapping and all nested
values during decoding.

```python
from mountainash import DataPackage

descriptor = {
    "name": "orders",
    "resources": [{"name": "orders", "path": "orders.csv", "type": "table"}],
}
package = DataPackage.from_descriptor(descriptor)
```

For relative schema and dialect references supplied in a mapping, pass an absolute
`base_uri` (an absolute local path or URI). A custom resolver can be supplied with
`resolver=`.

### JSON text

`DataPackage.from_json()` accepts JSON text. Give it a `base_uri` when the JSON contains
relative schema or dialect references.

```python
from pathlib import Path
from mountainash import DataPackage

text = Path("datapackage.json").read_text(encoding="utf-8")
package = DataPackage.from_json(text, base_uri=Path(".").resolve())
```

### Path

`DataPackage.from_path()` reads a local JSON descriptor and sets the descriptor
 directory as the reference base. Use this method for a filename or `Path`; it is the
explicit path input and the replacement for path-overloaded `from_descriptor()` calls.

```python
from mountainash import DataPackage

package = DataPackage.from_path("datapackage.json")
resource = package.resources[0]
```

The package must contain at least one resource. Resource names are unique, and each
resource declares exactly one of `path` or `data`.

## Outputs and ownership

The default writer is preserve mode:

```python
preserved = package.to_descriptor()
```

`to_descriptor()` returns a fresh, independently owned output graph. It keeps authored
schema and dialect mappings or reference strings, extension values, profile identities,
and property forms. Mutating `preserved` does not mutate `package`.

Canonical mode is explicit:

```python
canonical = package.to_canonical_descriptor()
```

Canonical output is also a fresh graph. It emits the standard v2 profile URIs where a
profile is absent or recognized as a v1 profile, removes v1-only `profile` fields and
dialect markers, and applies the documented v2 key-shape normalizations. It preserves
unknown extension values instead of sharing them with the package.

`DataPackage.write()` serializes either mode to a JSON file:

```python
from mountainash import DescriptorWriteMode

package.write("out/datapackage.json")
package.write("out/datapackage.canonical.json", mode=DescriptorWriteMode.CANONICAL)
```

Use `DescriptorWriteMode.PRESERVE` (the default) when the authored storage form is the
contract; use `DescriptorWriteMode.CANONICAL` when a normalized v2 descriptor is the
contract.

## Schema and dialect references

A resource stores `schema` and `dialect` as their raw mapping, reference string, or
already typed object. The raw value is not eagerly converted during package loading.

`DataResource.to_typespec()` and `DataResource.to_dialect()` are lazy, one-hop
accessors:

```python
schema = resource.to_typespec()  # TypeSpec | None
dialect = resource.to_dialect()  # TableDialect | None
```

A relative reference resolves against the package descriptor directory when the package
came from `from_path()`, or against the explicit `base_uri` supplied to another input
method. Resolution reads one JSON mapping and validates that it has the expected kind.
A schema mapping must be a Table Schema mapping with a `fields` list; a dialect
mapping must be a Table Dialect mapping and must not contain the schema `fields` or
package/resource `resources` properties. A resolved document of the wrong kind raises
a typed descriptor reference error rather than being silently coerced. Inline malformed
values raise typed structure errors.

Resolution is one hop. A resolved schema or dialect mapping is converted at the
accessor boundary; references embedded inside the resolved document are not followed
recursively by that accessor.

`resource.effective_sources` returns a fresh list. Explicit resource sources take
precedence; otherwise the package sources from the descriptor context are inherited
without mutating package or resource storage.

## Resolver security

The default resolver is local-only. It reads absolute local paths and `file://` URIs,
and it resolves relative references only when a base URI is available. It denies every
non-local URI scheme with `DescriptorReferenceSchemeDenied`. Missing bases, missing
files, malformed JSON, and wrong document kinds use the typed errors exported from
`mountainash.exceptions`.

Remote resolution requires an injected resolver with an explicit scheme allow-list. To
use the storage-backed resolver, install the optional dependency:

```bash
uv pip install "mountainash[storage]"
```

Then construct an opt-in resolver and pass it to an input method:

```python
from mountainash import DataPackage
from mountainash.typespec.descriptor_context import StorageDescriptorResolver

resolver = StorageDescriptorResolver(allowed_schemes={"s3"})
package = DataPackage.from_json(
    text,
    base_uri="s3://bucket/descriptors/",
    resolver=resolver,
)
```

The storage resolver still denies schemes that are not in its allow-list. Do not use a
remote resolver when local-only resolution is sufficient.

## V2-only policy

The decoder rejects recognized v1 profile identities in HTTP(S) `$schema` values. The
recognized families are:

- `datapackage.org/profiles/1.0/{datapackage,dataresource,tabledialect,tableschema}.json`;
- `specs.frictionlessdata.io/schemas/{data-package,data-resource,tabular-data-resource,tabular-data-package,fiscal-data-package,table-schema,csv-dialect}.json`;
- `frictionlessdata.io/schemas/{data-package,data-resource,tabular-data-resource,tabular-data-package,fiscal-data-package,table-schema,csv-dialect}.json`.

The corresponding `www.` aliases are recognized for the latter two host families.
These identities are rejected at package, resource, schema, and dialect boundaries with
`UnsupportedDescriptorVersion`.

The decoder also rejects explicit v1 properties: package and resource `profile`, and
the dialect properties `caseSensitiveHeader` and `csvddfVersion`. The canonical writer
removes those v1-only properties when canonicalizing a descriptor it can represent.

## Contributor compatibility

Contributor objects use the v2 `roles` list. For compatibility with prose and older
producer shapes, a single `role` value is accepted as a fallback only when `roles` is
absent. When both are present, `roles` wins.

Canonical output emits the selected value as `roles` and removes the singular `role`
key. An explicitly empty `roles` list is invalid; use a non-empty list of role strings.

## Absent profile policy

`MA-V2-01` is the approved local policy for an omitted `$schema`. An absent profile is
treated as v2 for package, resource, schema, and dialect documents. This avoids
reintroducing the v1 defaults currently present in upstream v2 profile sources.

Preserve output keeps an omitted profile omitted. Canonical output writes the standard
v2 URI for each descriptor kind. The coverage manifest records `MA-V2-01` as the
storage, typed, and execution disposition for all four `$schema` capabilities.

## Coverage maintenance

The coverage gate uses the four vendored v2 profile snapshots (package, resource,
dialect, and schema) pinned to upstream commit
`6a201af8ed2eacbb3a2440e82e4c55d5807f9c09`. `profile-sources.json` records each
snapshot digest. `profile-coverage.json` records one storage, typed, and execution
disposition for every discovered capability, including evidence-backed upstream
exceptions, local policies, and dated Unit B-E deferrals.

Run the closed coverage checks with:

```bash
hatch run test:test-target-quick tests/typespec/test_frictionless_profile_coverage.py -v
```

The checks recompute every SHA-256 digest, compare the pinned upstream commit with the
upstream discrepancy evidence, discover instance-path capabilities, and fail closed on
unknown profile paths, missing dispositions, duplicate dimensions, orphan manifest rows,
or incomplete evidence. A prose-backed capability absent from a profile must have an
evidence row and an `absent_from_profile` manifest entry; it must not be hidden by
editing a snapshot.

When upstream changes, refresh all snapshots and their provenance atomically. Update
the discrepancy record and manifest dispositions together, then rerun the coverage
tests. For a digest or commit mismatch, restore the last verified snapshot set or
refresh it from the recorded upstream commit before investigating behavior. For an
unknown capability or orphan row, add the correct disposition and evidence (or a dated
Unit owner and acceptance reference for deferred work) rather than weakening the gate.
