### Task 2 (transport): lazy package import, backend registration, `storage` factory

**Files:** Modify `src/mountainash_transport/__init__.py`, `storage/registry/registry.py:38-101`. Test: `tests/test_lazy_imports.py` (extend).

**Interfaces — Produces:** `mountainash_transport.storage.registry.registry.ensure_backends_loaded() -> None`. Every name in `__all__` still resolves to the same object as before.

- [ ] **Step 1: Failing tests** (append to `tests/test_lazy_imports.py`):

```python
def _run(code): subprocess.run([sys.executable, "-c", code], check=True)

def test_location_module_import_is_stdlib_only():
    _run("import sys; before=set(sys.modules); import mountainash_transport.location; "
         "new={m.split('.')[0] for m in set(sys.modules)-before}; "
         "bad=new-set(sys.stdlib_module_names)-{'mountainash_transport'}; assert not bad, bad")

def test_backends_register_on_first_lookup_after_lazy_import():
    _run("from mountainash_transport.storage.facade.facade import StorageFacade; "
         "StorageFacade.for_local()")

def test_storage_factory_survives_submodule_import_order():
    _run("from mountainash_transport import StorageFacade; import mountainash_transport.storage.facade; "
         "from mountainash_transport import storage; f = storage(); assert f.__class__.__name__ == 'StorageFacade'")

def test_lazy_exports_are_real_objects():
    _run("import mountainash_transport as t; from mountainash_transport.storage.protocols import StorageReadProtocol; "
         "assert t.StorageReadProtocol is StorageReadProtocol; assert isinstance(t.StorageFacade.for_local(), t.StorageFacade)")
```

- [ ] **Step 2: Run** `hatch run test:test-target-quick tests/test_lazy_imports.py` → the first test fails (eager `__init__`).
- [ ] **Step 3: Implement.**
  - Rewrite `__init__.py`:
    - keep `__version__`;
    - add `from __future__ import annotations`; eagerly import the stdlib-only `from ._core.constants import CONST_STORAGE_PROVIDER_TYPE` (the factory's default needs it at definition time);
    - **eagerly** `from . import storage as _storage_pkg  # noqa: F401`, which is docstring-only and keeps the binding order (spec §2), *before* defining the factory;
    - define `storage(provider_type: CONST_STORAGE_PROVIDER_TYPE = CONST_STORAGE_PROVIDER_TYPE.LOCAL, profile=None, *, auth_profile=None) -> "StorageFacade"` with `from .storage.facade import StorageFacade` inside its body. The return annotation is a string, so nothing heavy is evaluated at import;
    - build `_LAZY: dict[str, tuple[str, str]]` mapping every other `__all__` name to `(module, attr)`, copied from the current import lines;
    - add `def __getattr__(name)` that imports the module, sets `globals()[name]`, and returns the attribute. Raise `AttributeError` for unknown names.
    - Keep `__all__` unchanged. Remove the eager `from .storage import backends`.
  - `registry.py`: add

```python
def ensure_backends_loaded() -> None:
    import mountainash_transport.storage.backends  # noqa: F401  (registers on import; cached)
```

  and call it at the top of `get_storage_backend` and `get_registered_backends`. `clear_registry` is unchanged.
- [ ] **Step 4: Run** the full transport suite once: `hatch run test:test-quick` → PASS. Lazy exports must not break any existing import. (Tasks 3–4 run targeted files at their checkpoints; the full transport suite runs again only before the transport PR, in Task 4 Step 6.)
- [ ] **Step 5: Commit** `refactor(init)!: lazy package exports; backends register on first lookup (381)`.

