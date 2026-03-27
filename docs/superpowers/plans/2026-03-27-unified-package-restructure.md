# Unified Package Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `mountainash-expressions` into the unified `mountainash` package with `mountainash.core` (shared infrastructure) and `mountainash.expressions` (column-level ops), preserving all 2849+ tests.

**Architecture:** Move the entire `src/mountainash_expressions/` tree into `src/mountainash/expressions/`, extract shared pieces (constants, types) into `src/mountainash/core/`, rewrite absolute imports via script, and create a backwards-compat shim at `src/mountainash_expressions/`.

**Tech Stack:** Python 3.10+, Hatch build system, pytest, sed/Python for import rewriting

---

## Context for the Implementer

### Current Package Structure
```
src/mountainash_expressions/        # 224 Python files
├── __init__.py                     # Public API (col, lit, when, etc.)
├── __version__.py
├── types.py                        # Type aliases (SupportedExpressions, TypeGuards)
├── constants.py                    # Re-exports from core.constants
├── runtime_imports.py
├── core/
│   ├── constants.py                # CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES, etc.
│   ├── expression_system/          # expsys_base, function_keys, function_mapping
│   ├── expression_nodes/           # 7-node AST
│   ├── expression_protocols/       # ExpressionSystem + API builder protocols
│   ├── expression_api/             # API builders + entrypoints + boolean.py
│   ├── unified_visitor/            # visitor.py
│   └── utils/                      # temporal.py
└── backends/
    └── expression_systems/         # polars/, ibis/, narwhals/ (base.py + implementations)
```

### Target Package Structure
```
src/mountainash/                    # NEW unified package
├── __init__.py                     # Public API (same exports as today)
├── __version__.py
├── core/                           # SHARED infrastructure (used by all modules)
│   ├── __init__.py
│   ├── constants.py                # CONST_BACKEND (renamed from CONST_VISITOR_BACKENDS)
│   └── types.py                    # SupportedExpressions, SupportedDataFrames, TypeGuards
├── expressions/                    # Column-level ops (moved from mountainash_expressions/)
│   ├── __init__.py                 # Expression-specific exports
│   ├── core/                       # Expression-specific core (everything except shared constants/types)
│   │   ├── constants.py            # Re-exports from mountainash.core.constants for compat
│   │   ├── expression_system/
│   │   ├── expression_nodes/
│   │   ├── expression_protocols/
│   │   ├── expression_api/
│   │   ├── unified_visitor/
│   │   └── utils/
│   └── backends/
│       └── expression_systems/
├── dataframes/                     # STUB (Phase 2)
│   └── __init__.py
├── schema/                         # STUB (Phase 3)
│   └── __init__.py
└── pydata/                         # STUB (Phase 4)
    └── __init__.py

src/mountainash_expressions/        # BACKWARDS-COMPAT SHIM
└── __init__.py                     # DeprecationWarning + re-exports from mountainash
```

### Import Statistics (drives the migration script)
- **173 absolute imports** (`from mountainash_expressions.X`) across **111 source files** — must be rewritten
- **455 relative imports** (`from .X`, `from ..X`) across **142 source files** — preserved by move (relative structure unchanged)
- **146 absolute imports** across **55 test files** — rewritten by script
- **Total imports to rewrite:** ~319 across ~166 files

### Key Design Decision: What Moves to Core
Only two files move from `mountainash_expressions/` to `mountainash/core/`:
1. `core/constants.py` → `mountainash/core/constants.py` (backend enums, logic types)
2. `types.py` → `mountainash/core/types.py` (type aliases, TypeGuards)

Everything else stays in `mountainash/expressions/` with its internal structure preserved.

**Deferred to Phase 2:** The spec mentions extracting `detection.py` and `registration.py` to core. These are tightly coupled to the expression system today (there's no second consumer). They'll be extracted when dataframes is ported and actually needs shared detection/registration machinery.

---

### Task 1: Create the migration script

This script does the mechanical heavy lifting: moves directories, rewrites imports. Building and testing the script first prevents errors during the actual migration.

**Files:**
- Create: `scripts/migrate_to_unified_package.py`

- [ ] **Step 1: Write the migration script**

```python
#!/usr/bin/env python3
"""Migrate mountainash_expressions to unified mountainash package.

This script:
1. Creates the new directory structure
2. Moves source files
3. Rewrites absolute imports in source and test files
4. Creates the backwards-compat shim

Run from the repo root: python scripts/migrate_to_unified_package.py
"""

import os
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SRC = REPO_ROOT / "src"
OLD_PKG = SRC / "mountainash_expressions"
NEW_PKG = SRC / "mountainash"
NEW_EXPR = NEW_PKG / "expressions"
NEW_CORE = NEW_PKG / "core"
TESTS = REPO_ROOT / "tests"


def step1_create_skeleton():
    """Create the new mountainash package skeleton."""
    print("Step 1: Creating directory skeleton...")
    NEW_PKG.mkdir(exist_ok=True)
    NEW_CORE.mkdir(exist_ok=True)
    # Stub dirs for future modules
    for subdir in ("dataframes", "schema", "pydata"):
        (NEW_PKG / subdir).mkdir(exist_ok=True)


def step2_move_expression_source():
    """Move mountainash_expressions/ -> mountainash/expressions/."""
    print("Step 2: Moving expression source...")
    if NEW_EXPR.exists():
        shutil.rmtree(NEW_EXPR)
    # Copy the entire tree (we'll create shim at old location later)
    shutil.copytree(OLD_PKG, NEW_EXPR, dirs_exist_ok=False)
    print(f"  Copied {OLD_PKG} -> {NEW_EXPR}")


def step3_extract_shared_core():
    """Move shared files from expressions/core/ to mountainash/core/."""
    print("Step 3: Extracting shared core...")

    # 1. Copy core/constants.py -> mountainash/core/constants.py
    src_constants = NEW_EXPR / "core" / "constants.py"
    dst_constants = NEW_CORE / "constants.py"
    shutil.copy2(src_constants, dst_constants)
    print(f"  Copied constants.py to core/")

    # 2. Copy types.py -> mountainash/core/types.py
    src_types = NEW_EXPR / "types.py"
    dst_types = NEW_CORE / "types.py"
    shutil.copy2(src_types, dst_types)
    print(f"  Copied types.py to core/")

    # 3. Replace expressions/core/constants.py with re-export shim
    src_constants.write_text(
        '"""Backwards-compat re-exports from mountainash.core.constants."""\n'
        'from mountainash.core.constants import *  # noqa: F401,F403\n'
    )
    print(f"  Replaced expressions/core/constants.py with re-export shim")

    # 4. Replace expressions/types.py with re-export shim
    src_types.write_text(
        '"""Backwards-compat re-exports from mountainash.core.types."""\n'
        'from mountainash.core.types import *  # noqa: F401,F403\n'
    )
    print(f"  Replaced expressions/types.py with re-export shim")


def step4_rewrite_imports(root_dir: Path, file_glob: str = "**/*.py"):
    """Rewrite absolute imports from mountainash_expressions -> mountainash.expressions."""
    print(f"Step 4: Rewriting imports in {root_dir}...")
    count = 0

    for py_file in root_dir.rglob(file_glob):
        if "__pycache__" in str(py_file):
            continue
        if py_file.name == "migrate_to_unified_package.py":
            continue

        content = py_file.read_text()
        original = content

        # Rewrite: from mountainash_expressions.X -> from mountainash.expressions.X
        # Rewrite: import mountainash_expressions.X -> import mountainash.expressions.X
        # But NOT: import mountainash_expressions as ma (that's handled by shim)
        content = re.sub(
            r'from mountainash_expressions\.',
            'from mountainash.expressions.',
            content,
        )
        content = re.sub(
            r'import mountainash_expressions\.',
            'import mountainash.expressions.',
            content,
        )

        if content != original:
            py_file.write_text(content)
            count += 1

    print(f"  Rewrote imports in {count} files")
    return count


def step5_create_init_files():
    """Create __init__.py files for the new package structure."""
    print("Step 5: Creating __init__.py files...")

    # mountainash/__init__.py - top-level public API
    (NEW_PKG / "__init__.py").write_text(
        '"""Mountainash - Unified cross-backend DataFrame expression system."""\n'
        '\n'
        '# Re-export the full expressions public API at the top level\n'
        '# so that `import mountainash as ma; ma.col("x")` works\n'
        'from mountainash.expressions import (\n'
        '    BaseExpressionAPI,\n'
        '    BooleanExpressionAPI,\n'
        '    col,\n'
        '    lit,\n'
        '    native,\n'
        '    coalesce,\n'
        '    greatest,\n'
        '    least,\n'
        '    when,\n'
        '    t_col,\n'
        '    always_true,\n'
        '    always_false,\n'
        '    always_unknown,\n'
        '    CONST_VISITOR_BACKENDS,\n'
        '    CONST_LOGIC_TYPES,\n'
        '    CONST_EXPRESSION_NODE_TYPES,\n'
        ')  # noqa: F401\n'
        '\n'
        'from mountainash.expressions.__version__ import __version__  # noqa: F401\n'
    )
    print("  Created mountainash/__init__.py")

    # mountainash/core/__init__.py
    (NEW_CORE / "__init__.py").write_text(
        '"""Mountainash core - shared infrastructure for all modules."""\n'
    )
    print("  Created mountainash/core/__init__.py")

    # Module stubs with ImportError guards
    for module in ("dataframes", "schema", "pydata"):
        (NEW_PKG / module / "__init__.py").write_text(
            f'"""Mountainash {module} - not yet available.\n'
            f'\n'
            f'Install with: pip install mountainash[{module}]\n'
            f'"""\n'
            f'\n'
            f'raise ImportError(\n'
            f'    "mountainash.{module} is not yet available in this version. "\n'
            f'    "It will be added in a future release."\n'
            f')\n'
        )
        print(f"  Created mountainash/{module}/__init__.py (stub)")


def step6_create_shim():
    """Create backwards-compat mountainash_expressions shim."""
    print("Step 6: Creating backwards-compat shim...")

    # Remove old package (we already copied it to new location)
    if OLD_PKG.exists():
        shutil.rmtree(OLD_PKG)

    # Create shim directory
    OLD_PKG.mkdir()

    # Create shim __init__.py
    (OLD_PKG / "__init__.py").write_text(
        '"""Backwards-compatibility shim for mountainash_expressions.\n'
        '\n'
        'This package has been renamed to `mountainash`.\n'
        'Please update your imports:\n'
        '    import mountainash as ma  # NEW\n'
        '    import mountainash_expressions as ma  # DEPRECATED\n'
        '"""\n'
        'import warnings\n'
        '\n'
        'warnings.warn(\n'
        '    "mountainash_expressions is deprecated. "\n'
        '    "Use \'import mountainash as ma\' instead.",\n'
        '    DeprecationWarning,\n'
        '    stacklevel=2,\n'
        ')\n'
        '\n'
        '# Re-export everything from the new location\n'
        'from mountainash import *  # noqa: F401,F403\n'
        'from mountainash import __version__  # noqa: F401\n'
        '\n'
        '# Re-export submodules so deep imports work\n'
        '# e.g., from mountainash_expressions.core.expression_nodes import ScalarFunctionNode\n'
        'import mountainash.expressions.core as core  # noqa: F401\n'
        'import mountainash.expressions.backends as backends  # noqa: F401\n'
    )
    print("  Created mountainash_expressions/__init__.py (shim)")


def step7_copy_version():
    """Ensure __version__.py exists at the right level."""
    print("Step 7: Setting up version file...")
    # Copy expressions __version__.py to top level too
    src_version = NEW_EXPR / "__version__.py"
    dst_version = NEW_PKG / "__version__.py"
    if src_version.exists() and not dst_version.exists():
        shutil.copy2(src_version, dst_version)
        print("  Copied __version__.py to mountainash/")


def main():
    print("=" * 60)
    print("Migrating mountainash_expressions -> mountainash")
    print("=" * 60)

    step1_create_skeleton()
    step2_move_expression_source()
    step3_extract_shared_core()
    step4_rewrite_imports(NEW_PKG)
    step4_rewrite_imports(TESTS)
    step5_create_init_files()
    step6_create_shim()
    step7_copy_version()

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Update pyproject.toml (package name, find-packages config)")
    print("  2. Run: hatch run test:test-quick")
    print("  3. Fix any remaining import issues")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify script is syntactically valid**

Run: `python -c "import ast; ast.parse(open('scripts/migrate_to_unified_package.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit the migration script**

```bash
git add scripts/migrate_to_unified_package.py
git commit -m "feat: add migration script for unified mountainash package"
```

---

### Task 2: Run the migration script

**Files:**
- Modify: entire `src/` directory tree (automated by script)
- Create: `src/mountainash/` (new package root)
- Create: `src/mountainash/core/` (shared infrastructure)
- Create: `src/mountainash/expressions/` (moved from `src/mountainash_expressions/`)
- Create: `src/mountainash_expressions/__init__.py` (backwards-compat shim)

- [ ] **Step 1: Verify clean git state before migration**

Run: `git stash` (if needed — save any uncommitted work)

- [ ] **Step 2: Run the migration script**

Run: `python scripts/migrate_to_unified_package.py`

Expected output:
```
============================================================
Migrating mountainash_expressions -> mountainash
============================================================
Step 1: Creating directory skeleton...
Step 2: Moving expression source...
  Copied src/mountainash_expressions -> src/mountainash/expressions
Step 3: Extracting shared core...
  Copied constants.py to core/
  Copied types.py to core/
  Replaced expressions/core/constants.py with re-export shim
  Replaced expressions/types.py with re-export shim
Step 4: Rewriting imports in src/mountainash...
  Rewrote imports in ~111 files
Step 4: Rewriting imports in tests...
  Rewrote imports in ~55 files
Step 5: Creating __init__.py files...
  Created mountainash/__init__.py
  Created mountainash/core/__init__.py
  Created mountainash/dataframes/__init__.py (stub)
  Created mountainash/schema/__init__.py (stub)
  Created mountainash/pydata/__init__.py (stub)
Step 6: Creating backwards-compat shim...
  Created mountainash_expressions/__init__.py (shim)
Step 7: Setting up version file...
  Copied __version__.py to mountainash/

============================================================
Migration complete!
============================================================
```

- [ ] **Step 3: Verify the directory structure was created correctly**

Run: `ls -la src/mountainash/ && ls -la src/mountainash/core/ && ls -la src/mountainash/expressions/ && ls -la src/mountainash_expressions/`

Expected: All directories exist, `mountainash_expressions/` has only `__init__.py` (the shim).

- [ ] **Step 4: Verify import rewriting worked**

Run: `grep -r "from mountainash_expressions\." src/mountainash/ | head -5`
Expected: No matches (all should be rewritten to `from mountainash.expressions.`)

Run: `grep -r "from mountainash\.expressions\." src/mountainash/expressions/ | head -5`
Expected: Matches found (confirming rewrite worked)

- [ ] **Step 5: Commit the migration**

```bash
git add -A src/mountainash/ src/mountainash_expressions/
git commit -m "feat: restructure to unified mountainash package

- Move mountainash_expressions/ -> mountainash/expressions/
- Extract shared constants + types to mountainash/core/
- Rewrite 166 files with updated absolute imports
- Create backwards-compat shim at mountainash_expressions/
- Add module stubs for dataframes, schema, pydata"
```

---

### Task 3: Update pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Read the current pyproject.toml**

Read: `pyproject.toml` to see current package config, especially `[project]` name and `[tool.hatch.build.targets.wheel]` packages.

- [ ] **Step 2: Update package name and find-packages**

Change the `[project]` name from `mountainash_expressions` to `mountainash`. Update the Hatch build config to find both the `mountainash` package and the `mountainash_expressions` shim:

```toml
[project]
name = "mountainash"
# ... rest of project metadata unchanged ...

[project.optional-dependencies]
dataframes = []  # Phase 2: will add dependencies
schema = []      # Phase 3: will add dependencies
pydata = []      # Phase 4: will add dependencies
all = []         # Phase 2-4: will combine all optional deps

[tool.hatch.build.targets.wheel]
packages = ["src/mountainash", "src/mountainash_expressions"]
```

- [ ] **Step 3: Verify build config**

Run: `hatch build --clean`
Expected: Build succeeds, producing a `mountainash-*.whl` that includes both `mountainash/` and `mountainash_expressions/` packages.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "feat: update pyproject.toml for unified mountainash package"
```

---

### Task 4: Fix the backwards-compat shim for deep imports

The simple shim from Task 2 handles `import mountainash_expressions as ma` and top-level exports. But tests use deep imports like `from mountainash_expressions.core.expression_nodes import ScalarFunctionNode`. These need a more robust shim.

**Files:**
- Modify: `src/mountainash_expressions/__init__.py`

- [ ] **Step 1: Test which deep imports break**

Run: `python -c "from mountainash_expressions.core.expression_nodes import ScalarFunctionNode; print('OK')"`
Expected: Likely fails with `ModuleNotFoundError`

- [ ] **Step 2: Create module-level shims for deep import paths**

Instead of trying to make `mountainash_expressions.core.X` resolve dynamically, create a package structure that mirrors the old paths:

```python
# src/mountainash_expressions/__init__.py
"""Backwards-compatibility shim for mountainash_expressions.

This package has been renamed to `mountainash`.
Please update your imports:
    import mountainash as ma  # NEW
    import mountainash_expressions as ma  # DEPRECATED
"""
import importlib
import sys
import warnings

warnings.warn(
    "mountainash_expressions is deprecated. "
    "Use 'import mountainash as ma' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export top-level API
from mountainash import *  # noqa: F401,F403
from mountainash import __version__  # noqa: F401


class _ShimFinder:
    """Import hook that redirects mountainash_expressions.X -> mountainash.expressions.X."""

    PREFIX = "mountainash_expressions."
    TARGET = "mountainash.expressions."

    def find_module(self, fullname, path=None):
        if fullname.startswith(self.PREFIX):
            return self
        return None

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        # Map old name to new name
        new_name = self.TARGET + fullname[len(self.PREFIX):]
        mod = importlib.import_module(new_name)
        sys.modules[fullname] = mod
        return mod


sys.meta_path.insert(0, _ShimFinder())
```

- [ ] **Step 3: Test deep imports through shim**

Run: `python -c "from mountainash_expressions.core.expression_nodes import ScalarFunctionNode; print(ScalarFunctionNode)"`
Expected: `<class 'mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function.ScalarFunctionNode'>`

Run: `python -c "import mountainash_expressions as ma; print(ma.col('x'))"`
Expected: No error, prints expression repr

Run: `python -c "from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON; print(FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL)"`
Expected: Prints the enum value

- [ ] **Step 4: Commit**

```bash
git add src/mountainash_expressions/__init__.py
git commit -m "feat: add import hook shim for deep mountainash_expressions imports"
```

---

### Task 5: Fix expression __init__.py exports

The expressions `__init__.py` was moved but still has old import paths that were rewritten. It needs to export the same public API but from the new internal paths.

**Files:**
- Modify: `src/mountainash/expressions/__init__.py`

- [ ] **Step 1: Read the current expressions __init__.py**

Read: `src/mountainash/expressions/__init__.py`

The migration script rewrote `from mountainash_expressions.` to `from mountainash.expressions.` in this file. Verify the imports are correct.

- [ ] **Step 2: Verify the expressions __init__.py imports resolve**

Run: `python -c "from mountainash.expressions import col, lit, when, BooleanExpressionAPI; print('OK')"`
Expected: `OK`

If this fails, fix the import paths in `src/mountainash/expressions/__init__.py`. The imports should be:

```python
from mountainash.expressions.core.expression_api.boolean import BooleanExpressionAPI
from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
from mountainash.expressions.core.expression_api.entrypoints import (
    col, lit, native, coalesce, greatest, least, when, t_col,
    always_true, always_false, always_unknown,
)
from mountainash.expressions.core.constants import (
    CONST_VISITOR_BACKENDS,
    CONST_LOGIC_TYPES,
    CONST_EXPRESSION_NODE_TYPES,
)
```

Note: `from mountainash.expressions.core.constants` now re-exports from `mountainash.core.constants` (via the shim created in the migration script). This chain works: `mountainash.expressions.core.constants` → `mountainash.core.constants` → actual constants.

- [ ] **Step 3: Verify top-level mountainash import works**

Run: `python -c "import mountainash as ma; expr = ma.col('x').gt(5); print(expr)"`
Expected: No error, prints expression repr

- [ ] **Step 4: Commit if changes were needed**

```bash
git add src/mountainash/expressions/__init__.py
git commit -m "fix: correct expression __init__.py exports for new package structure"
```

---

### Task 6: Run the full test suite and fix failures

This is the critical validation step. The test suite should pass with zero changes to test files IF the backwards-compat shim works correctly. However, some tests may need fixes.

**Files:**
- Possibly modify: various test files if imports fail despite the shim

- [ ] **Step 1: Run the quick test suite**

Run: `hatch run test:test-quick 2>&1 | tail -30`

Expected: Most tests pass. Note any failures.

- [ ] **Step 2: If tests fail, categorize the failures**

Common failure patterns and fixes:

**Pattern A: `ModuleNotFoundError: No module named 'mountainash_expressions.X'`**
- Cause: The import hook shim isn't catching this path
- Fix: The shim from Task 4 should handle this. If not, check `_ShimFinder` prefix matching.

**Pattern B: `ImportError: cannot import name 'X' from 'mountainash.expressions.core.constants'`**
- Cause: The re-export shim in `expressions/core/constants.py` uses `from mountainash.core.constants import *` but the star-export doesn't include `X`
- Fix: Add explicit `__all__` to `mountainash/core/constants.py` or use explicit imports.

**Pattern C: `AttributeError: module 'mountainash' has no attribute 'X'`**
- Cause: Missing export in `mountainash/__init__.py`
- Fix: Add the missing export.

**Pattern D: Circular import**
- Cause: The re-export shim creates a circular dependency
- Fix: Use lazy imports or restructure the re-export chain.

- [ ] **Step 3: Fix any failing tests**

Apply fixes based on the patterns above. Each fix should be minimal and targeted.

- [ ] **Step 4: Run the full test suite with coverage**

Run: `hatch run test:test 2>&1 | tail -30`
Expected: All 2849+ tests pass (same count as before migration), 278 xfailed.

- [ ] **Step 5: Commit fixes**

```bash
git add -A
git commit -m "fix: resolve import issues from package restructure

All 2849+ tests passing with new mountainash package structure."
```

---

### Task 7: Update the expressions __init__ re-export for core.expression_nodes

Tests use `from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode`. The `expression_nodes/__init__.py` inside expressions has relative imports that the migration script already rewrote. But we need to verify the re-export chain works end-to-end.

**Files:**
- Possibly modify: `src/mountainash/expressions/core/expression_nodes/__init__.py`

- [ ] **Step 1: Verify the expression_nodes re-exports**

Run: `python -c "from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode, CastNode, IfThenNode, SingularOrListNode; print('All node types importable')"`
Expected: `All node types importable`

- [ ] **Step 2: Verify through the shim**

Run: `python -c "from mountainash_expressions.core.expression_nodes import ScalarFunctionNode; print(ScalarFunctionNode.__module__)"`
Expected: Prints a module path (confirms the import hook resolves correctly)

- [ ] **Step 3: Verify function key enums through shim**

Run: `python -c "from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON; print(FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL)"`
Expected: Prints enum value

- [ ] **Step 4: Commit if changes were needed**

```bash
git add -A
git commit -m "fix: ensure expression node and enum re-exports work through shim"
```

---

### Task 8: Update hatch test configuration

The test runner needs to know about the new package structure.

**Files:**
- Modify: `pyproject.toml` (test configuration section)

- [ ] **Step 1: Read the test configuration**

Read: `pyproject.toml` — look for `[tool.hatch.envs.test]` and `[tool.pytest.ini_options]` sections.

- [ ] **Step 2: Update pytest configuration if needed**

The `testpaths` and any `pythonpath` settings may need updating. If `pyproject.toml` has:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
```

This should still work since both `src/mountainash` and `src/mountainash_expressions` are under `src/`.

If there are any `filterwarnings` for `mountainash_expressions`, update them:

```toml
filterwarnings = [
    "ignore::DeprecationWarning:mountainash_expressions",
]
```

- [ ] **Step 3: Run quick tests to verify config**

Run: `hatch run test:test-quick 2>&1 | tail -10`
Expected: Tests run and pass

- [ ] **Step 4: Commit if changes were needed**

```bash
git add pyproject.toml
git commit -m "fix: update pytest config for unified package structure"
```

---

### Task 9: Verify the wiring audit still passes

The wiring audit test (`tests/unit/test_protocol_alignment.py`) dynamically imports protocols and backend classes. It's the most import-sensitive test and must pass.

**Files:**
- No changes expected (just verification)

- [ ] **Step 1: Run only the wiring audit tests**

Run: `hatch run test:test-target tests/unit/test_protocol_alignment.py -v 2>&1 | tail -40`

Expected: All `TestWiringAudit`, `TestWiringAuditHelpers`, `TestProtocolAlignment`, and `TestInheritanceIntegrity` tests pass. 35 xfailed aspirational methods.

- [ ] **Step 2: Run the namespace infrastructure tests**

Run: `hatch run test:test-target tests/unit/test_namespace_infrastructure.py -v 2>&1 | tail -20`

Expected: All pass

- [ ] **Step 3: Run a cross-backend smoke test**

Run: `hatch run test:test-target tests/cross_backend/test_boolean.py -v 2>&1 | tail -20`

Expected: All pass across all backends (polars, pandas, narwhals, ibis-duckdb, ibis-polars, ibis-sqlite)

- [ ] **Step 4: Run the full suite one final time**

Run: `hatch run test:test 2>&1 | tail -10`

Expected: Same results as pre-migration: 2849+ passed, 278 xfailed, 0 failed.

---

### Task 10: Update CLAUDE.md

The CLAUDE.md needs to reflect the new package structure.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the package name and import paths**

At the top of CLAUDE.md, change:
- `**mountainash-expressions** is a Python package` → `**mountainash** is a Python package (formerly mountainash-expressions)`
- Update the "Package Structure" section to show the new `src/mountainash/` tree
- Update "Quick Reference > Import Paths" to show both old and new paths
- Add a note about backwards compatibility

- [ ] **Step 2: Update import examples throughout**

All examples should use `import mountainash as ma` (which is the same as today). Deep import examples should use the new paths with a note that old paths still work:

```python
# New paths (preferred)
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON
from mountainash.core.constants import CONST_VISITOR_BACKENDS

# Old paths (deprecated, still work via shim)
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode
```

- [ ] **Step 3: Add section about unified package architecture**

Add a brief section explaining:
- The package is being unified from 4 separate packages
- `mountainash.core` contains shared infrastructure
- `mountainash.expressions` contains column-level operations
- `mountainash.dataframes`, `.schema`, `.pydata` are planned for future phases

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for unified mountainash package structure"
```

---

### Task 11: Final verification and cleanup

- [ ] **Step 1: Remove migration script (it's a one-time tool)**

```bash
rm scripts/migrate_to_unified_package.py
git add -A scripts/
git commit -m "chore: remove one-time migration script"
```

- [ ] **Step 2: Verify no stale references remain**

Run: `grep -r "mountainash_expressions" src/mountainash/ --include="*.py" | grep -v "__pycache__" | grep -v "# OLD\|# DEPRECATED\|# deprecated\|DeprecationWarning\|backwards"`

Expected: No matches (all internal references should use `mountainash.expressions`)

Run: `grep -r "mountainash_expressions" tests/ --include="*.py" | grep -v "__pycache__" | head -5`

Expected: Only `import mountainash_expressions as ma` patterns (these work via shim and are fine for now; tests can be updated later).

- [ ] **Step 3: Verify clean import**

Run: `python -c "import mountainash as ma; print(f'mountainash v{ma.__version__}'); expr = ma.col('x').gt(5).and_(ma.col('y').lt(10)); print(f'Expression: {expr}')"`

Expected: Version prints, expression created successfully.

- [ ] **Step 4: Verify full test suite one last time**

Run: `hatch run test:test 2>&1 | tail -5`
Expected: 2849+ passed, 278 xfailed, 0 failed

- [ ] **Step 5: Create summary commit**

```bash
git add -A
git commit -m "feat: complete unified mountainash package restructure

Phase 1 of the unified package plan is complete:
- Package renamed from mountainash_expressions to mountainash
- Shared infrastructure extracted to mountainash.core (constants, types)
- Expression code lives at mountainash.expressions
- Backwards-compat shim with import hook for mountainash_expressions
- Module stubs for future dataframes, schema, pydata modules
- All 2849+ tests passing, 0 regressions"
```
