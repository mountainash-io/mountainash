# Task 4 report
Implemented: facade `_check` (require_known_scheme for all; S3 bucket/profile rules; SFTP url host vs profile; HTTP allow_remote), from_path unknown-scheme check, HttpRequestEngine `location_check` (checked before every send), HTTP backend + `get_storage_backend` forward `location_check` (registry.py also changed, needed for wiring), facade passes `location_check=self._check` for HTTP when policy active. README "Location policy", version 0.1.1.
Tests: new tests/storage/facade/test_facade_remote_policy.py (12), 2 engine cases in test_redirects.py. _S3_MINIMAL/_SFTP_MINIMAL copied from profile tests (BUCKET=None omitted since profile rejects None). 
RED: 9 failed in remote_policy, 2 failed in redirects (TypeError location_check). GREEN: tests/storage/facade tests/_core/http pass; full `test-quick`: 1816 passed, 1 skipped.
Files: facade.py, engine.py, backends/http/__init__.py, registry/registry.py, README.md, __version__.py, tests.
Concerns: bucketless S3 test omits BUCKET (None invalid for profile). Fake backend needed no extra methods. PR not opened per instruction.

## Fix round 1
1. HTTPStorageBackend raises ValueError when both `engine` and `location_check` given; test added.
2. `_check` returns path for remote providers when policy is None/inactive (no S3 parse); tests assert ValueError (not LocationNotAllowed) for `s3://` with no policy and allow_unconfined. 
Tests: facade+backends pass; full suite re-run below.
