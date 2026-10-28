# Data Package v2 descriptors

Mountainash implements the Unit A Frictionless Data Package v2 descriptor boundary. The
storage models retain the authored descriptor graph (raw mappings, reference strings and
extension values); typed `TableSchema` and dialect objects are created only when a
consumer asks for them.

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

## Location policy

Descriptor loaders (`from_path`, `from_json`, `from_descriptor`, `datacontract`) confine
every resource, schema and dialect location by default. `from_path`, `from_json` and
`from_descriptor` accept `policy=`, a `mountainash_transport.location.LocationPolicy`;
`datacontract(source)` takes no `policy` and always confines to the source's parent directory.

| Loader call | Root when `policy` has none |
|---|---|
| `from_path(path)` | the descriptor directory |
| `from_json` / `from_descriptor` with a local `base_uri` | that directory |
| the same with a remote `base_uri`, or no `base_uri` | the working directory at load time |
| `datacontract(source)` | the source file's parent directory |
| `DataPackage(...)` / `DataResource(...)` built in code | none (unconfined) |

- Relative resource paths resolve beside the descriptor (or against `base_uri` / the
  working directory), matching Frictionless. A remote `base_uri` joins relative paths but
  grants no permission to fetch from its host.
- Absolute local paths outside the root, symlinks leaving the root, and `file://` URIs outside
  the root raise `LocationNotAllowed` at read time (absolute paths inside the root are accepted),
  including paths assigned after load. `..` and hidden
  segments are still rejected at decode time with the existing error.
- Remote resources and references (`http(s)`, `s3`, ...) need
  `LocationPolicy(allowed_remote={"https": frozenset({"host.example"})})`; an empty set
  allows any host for that scheme. Unknown schemes are rejected.
- `LocationPolicy(root=...)` replaces the declared root; `allowed_remote` alone keeps it.
  `LocationPolicy(allow_unconfined=True)` is the single opt-out.
- `model_copy`, `DataResource.model_validate(bound)` and `DataPackage.model_validate(bound)`
  keep the context and its policy. `to_package()` exports build a new package in code and
  are rootless.
- Reads are confined on Polars, Narwhals and Ibis alike; the descriptor round-trip is
  unchanged because the policy is a private, non-serialized context field.

```python
from mountainash import DataPackage
from mountainash_transport.location import LocationPolicy

package = DataPackage.from_path("pkg/datapackage.json")  # confined to pkg/
open_pkg = DataPackage.from_path(
    "pkg/datapackage.json", policy=LocationPolicy(allow_unconfined=True)
)
```

Not covered: a writer who can change the filesystem inside the root between check and open,
DNS rebinding, custom `DescriptorResolver` code, and endpoints named by profiles you
supplied. Under a policy, an Ibis read of a directory raises `LocationNotAllowed` unless
the backend is DuckDB and the directory path contains none of `[`, `*`, `?` (use a glob);
see the [resource-read support matrix](resource-read-support-matrix.md).

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

## Execution through a relation DAG

`DataPackage.to_relation_dag(overrides=...)` can replace a tabular resource with an
in-memory native frame. When the resource has a table schema, the override follows
the same conform path as a resource read. `dag.collect(name)` therefore applies the
declared schema before returning the collected frame.

Schema inspection also resolves references through the owning DAG:

```python
available = dag.schema("orders")          # Best available native output metadata
complete = dag.ref("orders").collect_schema()  # Complete or IncompleteSchemaError
```

These calls do not deliberately collect result rows. Native reader inference may
read metadata or probe the source; resource declarations alone do not certify the
actual output. `collect_schema(allow_execution=True)` permits ordinary execution
when metadata is insufficient, including its normal conform and validation rules.
Constraint edges do not become execution dependencies during schema inspection.

File resources that cannot use the selected backend's native metadata reader
use `mountainash-files` schema discovery with the same paths, dialect, glob and
archive selection as ordinary reading. Parquet discovery reads footer metadata;
other formats may inspect every source record. Source inference can therefore
perform substantial I/O even without permission to evaluate the relation.
Conform and downstream expressions are still compiled by the selected backend.

Full and metadata observations can establish completeness; bounded observations
remain best-effort evidence, not a complete-schema guarantee. Unsupported
discovery may require explicit execution permission. Missing sources, access
errors, malformed content and missing dependencies are not silently retried by
executing the relation. Discovery results are not cached between schema calls.

The v2 conform path preserves nulls while it performs the declared conversions:

- lexical `list` fields split with their declared `delimiter` and cast each item;
- `array` and `object` fields ingress through portable JSON text, or through a
  no-round-trip native `list`/`struct` source column (see below);
- `geopoint` supports default lexical text, lexical arrays, native numeric arrays, and
  native `lon`/`lat` objects according to its declared format;
- lexical `geojson` and `topojson` values remain valid JSON text after parsing;
- default datetimes become backend datetime values, while XSD duration and partial-date
  values retain their semantic string representation;
- `format: "any"` datetime fields use the temporal parser and preserve nulls.

Conform diagnostics and internal marker columns are consumed at the collection
boundary. Marker columns are not part of the returned public frame. Unsupported
backend cells raise `BackendCapabilityError` with the declared operation key and
capability fact attached to the exception.

### Structured (`array`/`object`) fields

A structured field's ingress route depends on the physical source column, not the
declared type alone:

- **JSON text** (a string-typed source column) is the portable ARRAY and OBJECT
  vehicle — the only round-trippable ingress path, available on every backend. The
  decoder recursively resolves nested `array`-of-`object` and `object`-of-`array`
  structure from the declared schema and rejects a malformed payload or a
  structurally wrong root (e.g. an `array`-declared field whose text decodes to an
  object) as an invalid value under the field's configured action.
- **Native `list`/`struct`** source columns (Polars, its Narwhals wrappers, Ibis) are
  a no-round-trip path: schema evidence alone (`collect_schema()`/table schema, never
  a decoded row) proves the shape, so no JSON parsing ever runs.
- **Opaque native Python containers** (pandas, narwhals-pandas — no native list/struct
  dtype) resolve through logical conversion: the cell already holds a real Python
  list/dict, so the value normalizes directly without a text decode.

A conform transform that decodes JSON text (`coerce`, `discard_value`, `discard_row`)
produces a **physical/logical boundary**: the resulting column carries the *decoded
logical value* for validation and logical egress, but the transported field is a
closed transport carrier for every other relation operation. A transported field
cannot be used as a filter, sort, join, grouping, aggregate, or distinct input before
logical decoding. `.to_polars()`, `.to_pandas()`, `to_dicts`, `to_tuples`, `item`,
`to_dataclasses`, `to_pydantic`, and `validation` are all logical terminals: they
resolve the decode and return the logical value. Only DAG-level **native
collection** (`dag.collect()`/`dag.collect_with_drift()`) fails closed — attempting
native collection on a relation whose plan still requires that decode raises
`LogicalTerminalRequired`, naming the affected fields. `evolve` (preserve the
source, decode only for validation) and a structural-only conform (no value
transform) are exempt from native collection's fail-closed check — both remain
natively collectible.

`dag.validate(specs)` is itself a logical terminal: it always resolves every declared
structured field's logical value, regardless of the DAG's native-collection intent,
because JSON Schema, identity, uniqueness, and foreign-key checks all compare
*logical* values (spec section 15's `canonical_value_key()` — whitespace and
object-key order never change the outcome).

One descriptor with both roots:

```python
import mountainash as ma

spec = ma.table_schema({
    "tags": "array",
    "profile": "object",
})

result = ma.relation(frame).conform(spec).to_dicts()
```

## Schema and dialect references

A resource stores `schema` and `dialect` as their raw mapping, reference string, or
already typed object. The raw value is not eagerly converted during package loading, and
reading it never rewrites storage: `to_descriptor()` keeps authored properties such as an
explicit `format: default` or custom `x-` extension values, even though the typed
`TableSchema` does not retain properties the codec does not model.

`DataResource.to_table_schema()` and `DataResource.to_dialect()` are lazy, one-hop
accessors:

```python
resource = package.resources[0]
schema = resource.to_table_schema()  # TableSchema | None
dialect = resource.to_dialect()      # TableDialect | None
```

`to_table_schema()` returns an already typed `TableSchema` unchanged, and otherwise
converts the resolved raw mapping through the shared Frictionless codec
(`mountainash.typespec.frictionless`; `TableSchema.from_frictionless()` /
`to_frictionless()` delegate to the same functions). The codec is a pure mapping
import/export boundary: it does no file or network resolution and selects no backend.
Resolving the typed schema does not synchronize it back to the raw resource value.

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

There is one default resolver, `DefaultDescriptorResolver`. It resolves a reference under
the context `LocationPolicy` (the one passed to the loader): local references (absolute
paths, `file://` URIs, and base-relative paths) must stay inside the policy root, and
remote references (including references relative to a remote base) are read through the
storage facade only when the policy's `allowed_remote` allow-list names their scheme and
host. Violations raise `mountainash_transport.location.LocationNotAllowed`, before any
network request. With no policy (a programmatic package with no base) local reads are
allowed and every remote reference is denied with `LocationNotAllowed`. Missing bases,
missing files, malformed JSON, and wrong document kinds use the typed errors exported from
`mountainash.exceptions`.

```python
from mountainash import DataPackage
from mountainash_transport.location import LocationPolicy

policy = LocationPolicy(allowed_remote={"s3": frozenset({"bucket"})})
package = DataPackage.from_json(
    text,
    base_uri="s3://bucket/descriptors/",
    policy=policy,
)
```

A custom resolver may accept an optional `policy` keyword; it receives the context policy
and may ignore it (custom resolvers are caller code).

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
v2 URI for each descriptor kind (`frictionless_codec.py`'s `_canonical_profile`,
`_canonicalize_dialect`, `_canonicalize_schema`, `_encode_package_canonical`). See the
central backlog, item 113, for the `MA-V2-01` design record.

## Upstream profile snapshots

The four vendored v2 profile snapshots (package, resource, dialect, and schema),
pinned to upstream commit `6a201af8ed2eacbb3a2440e82e4c55d5807f9c09`, live at
`tests/fixtures/frictionless/v2/profiles/`. `profile-sources.json` records each
snapshot's SHA-256 digest for provenance.

Documented discrepancies between this pinned upstream commit and mountainash's
behavior (`DP-V2-01` through `DP-V2-06`) and local policy decisions (`MA-V2-01`) are
recorded in the central backlog, item 113 — that is the single source of truth; do not
duplicate it elsewhere.

Correctness for each descriptor kind is defended by the functional test suite
(`tests/typespec/test_frictionless_codec.py`, `test_frictionless_v2_smoke.py`, and the
round-trip suites), which exercise real decode/encode paths against real descriptors —
not by a separate coverage-tracking fixture.

When upstream changes, refresh the vendored snapshots and `profile-sources.json`'s
digests together, then update the central backlog's discrepancy record if behavior
changes as a result.

