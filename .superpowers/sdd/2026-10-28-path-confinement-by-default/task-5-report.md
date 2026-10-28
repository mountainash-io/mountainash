# Task 5 (files) report
Implemented FileSpec.policy; `_resolve_profiles` returns (profile, auth, policy); policy passed explicitly through _make_facade/_read_bytes/_write_bytes/_with_access/on_source/glob/copy(per endpoint)/stream. resolve_glob(policy=). README "Location policy". Version 0.1.1; transport pin >=0.1.1,<0.2 in pyproject.
RED: new tests/test_location_policy.py -> 11 failed (TypeError unexpected kwarg 'policy'). GREEN: after impl 12 passed.
Full suite: 581 passed (run via .hatch/test-py3.12/bin/python -m pytest tests, py3.12).
Files: base.py, _operations.py, _glob.py, __version__.py, pyproject.toml, README.md, tests/test_location_policy.py (new), tests/test_specs.py (3-tuple unpack), tests/test_write.py (route_factory accepts policy).
Deviations: append test uses parquet (csv not appendable); write_disposition literals are "replace"/"append".
Concerns: `hatch run test:*` can no longer resolve deps (sibling transport is 0.1.0 vs pin >=0.1.1; hatch.toml untouched); transport installed editable via `uv pip` (pip absent) and tests run with env python directly. test.py3.13 env created by hatch lacks the editable transport. hatch.toml untouched (brief mentioned it).
