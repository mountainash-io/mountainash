# Task 2 report
Implemented: lazy PEP 562 `__init__` (74 names in `_LAZY`, `__all__` unchanged), eager `__version__`, `CONST_STORAGE_PROVIDER_TYPE`, `from . import storage as _storage_pkg` before the `storage()` factory (factory imports StorageFacade in body); `ensure_backends_loaded()` in registry, called by `get_storage_backend` and `get_registered_backends`; removed eager backends import.
Tests: 4 appended to tests/test_lazy_imports.py.
RED: `hatch run test:test-target-quick tests/test_lazy_imports.py` -> stdlib-only test failed (pydantic, httpx, fsspec... imported), 4 passed.
GREEN: full `hatch run test:test-quick` -> 1795 passed, 1 skipped.
Files: src/mountainash_transport/__init__.py, storage/registry/registry.py, tests/test_lazy_imports.py.
Self-review: _core stdlib-only verified by the passing stdlib test.
Concern: clear_registry() then lookup does not re-register (ensure is import-cached), per brief.

## Fix round 1
P2 fixed: `register_storage_backend`'s decorator now calls `ensure_backends_loaded()` before inserting, so built-ins load first and caller registrations win. Nested call during built-ins' own import is a no-op (module in sys.modules). Added subprocess regression test `test_caller_registration_before_first_lookup_wins` (RED before fix, GREEN after). Registry + lazy tests pass; full suite run once.
