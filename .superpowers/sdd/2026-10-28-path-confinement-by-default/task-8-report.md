# Task 8 report
Implemented: ResourceRef.read_bytes uses resolve_resource_location/resource_policy/confine_local, remote via facade_read_bytes(path, policy). core/io: is_remote via transport identify_scheme (fallback list deleted); facade_read_bytes(path, policy=None) -> StorageFacade.from_path(path, policy=policy). One DefaultDescriptorResolver (Local/Storage deleted; remote with policy None -> LocationNotAllowed(reference,"remote not allowed")). _local_path_from_uri deleted; callsites use `_file_uri_path` (wraps transport local_path, LocationNotAllowed -> DescriptorReferenceInvalid as before); loader_policy uses transport local_path directly after normalize_base_uri. resolve_descriptor_mapping passes policy only if resolver.resolve accepts `policy`/**kwargs; LocationNotAllowed is re-raised unwrapped. DescriptorReferenceSchemeDenied removed (errors, exceptions, __init__ exports). Docs updated.
TDD: RED = 8 failed/2 passed on the two new files; GREEN after impl.
Tests: tests/core tests/typespec: 7988 passed, 39 skipped, 254 xfailed; other DataPackage/ResourceRef tests (638) passed.
Migrated: test_descriptor_context resolver tests, test_io, parity test (now LocationNotAllowed), test_descriptor_errors, test_datapackage_resource.
Concern: signature inspected per call, not once (cheap). sftp/ssh/ftp is_remote cases kept (only the fallback comment removed).

## Fix round 1
Added require_known_scheme(location, policy) before the local/remote branch in ResourceRef.read_bytes and DefaultDescriptorResolver.resolve (same gap). Tests added for hf:// resource and schema reference -> LocationNotAllowed "unknown scheme". 46 passed (policy tests + descriptor_context). Ruling 6 respected.
