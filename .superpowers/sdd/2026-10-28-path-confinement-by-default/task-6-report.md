# Task 6 report (mountainash)
## Implemented
- pyproject: transport>=0.1.1,<0.2 core dep; `storage` extra removed; files>=0.1.1 in ibis/files/s3/gcs/azure/sftp; `all` updated. hatch.toml had no `storage` reference (unchanged). docs/reference/datapackage.md no longer tells users to install `[storage]`.
- `DescriptorContext.policy`, `build_descriptor_context(policy=)`, `loader_policy` (descriptor_context.py).
- Loaders/`DataPackage.from_*` accept `policy=`; context built with `loader_policy(base_uri, policy)`.
- Ruling 3: base_uri stays None when omitted; root = cwd via with_declared_root (also under allow_unconfined); `resolve_resource_location` uses ctx.base_uri else ctx.policy.root (read directly, active or not); policy None returns raw path.
- Retention: DataResource.model_copy and model_validate(instance) keep context; DataPackage.model_validate(instance) passes the instance's context. Extra fix: pydantic re-runs `DataPackage.__init__` on validate, which rebound resources to the default context, so `_rebind_package_resources` re-binds them after validate/validate_json.
- `core/location.py` new. datacontract already passes base_uri=path.parent; covered by a test.
## TDD
RED: `pytest tests/typespec/test_location_policy_context.py` -> ModuleNotFoundError mountainash.core.location (collection error). After impl one case (package_validate) failed (resource policy None) until the rebind fix; GREEN 15 passed (incl. extra opt-out-no-base and datacontract tests).
## Tests
tests/typespec + tests/core: 7972 passed; 4 failures were only `FileNotFoundError: 'python'` (subprocess PATH); rerun with env bin on PATH: 21 passed (those 3 files).
## Files
pyproject.toml, docs/reference/datapackage.md, core/location.py (new), typespec/{descriptor_context,frictionless_codec,datapackage}.py, tests/typespec/test_location_policy_context.py (new).
## Concerns
Initial edits landed in the main `mountainash` checkout by cwd mistake; moved to -381 and main checkout restored clean. Did not run other test dirs or mypy. Package `model_validate_json` rebinding is behavior-neutral (default context).

## Fix round 1
`loader_policy` now calls `normalize_base_uri` first (existing InvalidDescriptorStructure fires) and derives the local root from the normalized file: URI via `_local_path_from_uri`; no transport parsing of the raw base. Added regression tests (malformed `https://[bad`, `file://evilhost/tmp/`, via from_descriptor and from_json). Tests: location_policy + descriptor/base_uri/codec subset 19 passed; full tests/typespec result in commit message run.
