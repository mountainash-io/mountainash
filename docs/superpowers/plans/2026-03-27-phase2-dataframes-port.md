# Phase 2: Port Dataframes to Unified Package — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port `mountainash-dataframes` into `mountainash.dataframes` within the unified `mountainash` package, preserving all functionality and enabling `ma.table(df).filter(ma.col("age").gt(30))`.

**Architecture:** Copy the 45 source files from `mountainash-dataframes` into `src/mountainash/dataframes/`, rewrite 14 absolute imports, update the expression integration to use new import paths, wire up top-level exports, port and flatten 84 test files.

**Tech Stack:** Python 3.10+, Hatch build system, pytest

---

## Context for the Implementer

### Source Project Location
```
/home/nathanielramm/git/mountainash-io/mountainash/mountainash-dataframes/src/mountainash_dataframes/
```

### Target Location (currently a stub)
```
/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/src/mountainash/dataframes/
```

The target currently has a single `__init__.py` that raises ImportError. This will be replaced.

### Import Statistics
- **14 absolute imports** (`from mountainash_dataframes.X`) — must be rewritten
- **312 relative imports** (`from .X`, `from ..X`) — preserved by copy (structure unchanged)
- Much simpler than Phase 1 (which had 173 absolute imports)

### Key Discovery: Expression Integration Already Exists
The existing `FilterNamespace._resolve_expression()` already detects mountainash expressions and compiles them. The import path needs updating from `mountainash_dataframes` to `mountainash.dataframes`, and the expression import needs to point to `mountainash.expressions`.

---

### Task 1: Write and run migration script

A simpler version of the Phase 1 migration script. Copies source, rewrites absolute imports.

**Files:**
- Create: `scripts/migrate_dataframes.py`
- Modify: `src/mountainash/dataframes/` (entire directory replaced)

- [ ] **Step 1: Write the migration script**

```python
#!/usr/bin/env python3
"""Migrate mountainash-dataframes into the unified mountainash package.

Copies source from the sibling mountainash-dataframes repo into
src/mountainash/dataframes/, then rewrites absolute imports.

Run from the mountainash-expressions repo root:
    python scripts/migrate_dataframes.py
"""

import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SRC_REPO = REPO_ROOT.parent / "mountainash-dataframes" / "src" / "mountainash_dataframes"
TARGET = REPO_ROOT / "src" / "mountainash" / "dataframes"


def step1_copy_source():
    """Copy dataframes source into unified package."""
    print("Step 1: Copying dataframes source...")
    if not SRC_REPO.exists():
        raise FileNotFoundError(f"Source repo not found: {SRC_REPO}")

    # Remove existing stub/directory
    if TARGET.exists():
        shutil.rmtree(TARGET)

    # Copy entire tree
    shutil.copytree(SRC_REPO, TARGET)
    print(f"  Copied {SRC_REPO} -> {TARGET}")

    # Remove _deprecated if it exists
    deprecated = TARGET / "_deprecated"
    if deprecated.exists():
        shutil.rmtree(deprecated)
        print("  Removed _deprecated/")

    # Remove __pycache__ directories
    for pycache in TARGET.rglob("__pycache__"):
        shutil.rmtree(pycache)
    print("  Cleaned __pycache__/")


def step2_rewrite_imports():
    """Rewrite absolute imports from mountainash_dataframes -> mountainash.dataframes."""
    print("Step 2: Rewriting imports...")
    count = 0

    for py_file in TARGET.rglob("*.py"):
        content = py_file.read_text()
        original = content

        # Rewrite absolute imports
        content = re.sub(
            r'from mountainash_dataframes\.',
            'from mountainash.dataframes.',
            content,
        )
        content = re.sub(
            r'import mountainash_dataframes\.',
            'import mountainash.dataframes.',
            content,
        )
        # Also rewrite string references in lazy_loader calls
        content = re.sub(
            r'"mountainash_dataframes\.',
            '"mountainash.dataframes.',
            content,
        )
        content = re.sub(
            r"'mountainash_dataframes\.",
            "'mountainash.dataframes.",
            content,
        )

        if content != original:
            py_file.write_text(content)
            count += 1

    print(f"  Rewrote imports in {count} files")


def step3_fix_expression_integration():
    """Update expression import in filter namespace to use new path."""
    print("Step 3: Fixing expression integration imports...")

    # The filter namespace already has expression detection.
    # We need to ensure it imports from mountainash.expressions, not mountainash_expressions
    filter_ns = TARGET / "core" / "table_builder" / "namespaces" / "filter.py"
    if filter_ns.exists():
        content = filter_ns.read_text()
        # Replace any mountainash_expressions references
        content = content.replace(
            "from mountainash_expressions",
            "from mountainash.expressions",
        )
        content = content.replace(
            "import mountainash_expressions",
            "import mountainash.expressions",
        )
        filter_ns.write_text(content)
        print("  Updated filter.py expression imports")

    # Also check the expression compiler utility
    compiler = TARGET / "core" / "utils" / "expression_compiler" / "compiler.py"
    if compiler.exists():
        content = compiler.read_text()
        content = content.replace(
            "from mountainash_expressions",
            "from mountainash.expressions",
        )
        content = content.replace(
            "import mountainash_expressions",
            "import mountainash.expressions",
        )
        compiler.write_text(content)
        print("  Updated compiler.py expression imports")


def step4_remove_root_init_version():
    """Clean up files that shouldn't be in the subpackage."""
    print("Step 4: Cleaning up...")

    # Remove __version__.py (version lives at mountainash level)
    version_file = TARGET / "__version__.py"
    if version_file.exists():
        version_file.unlink()
        print("  Removed __version__.py")

    # Remove constants.py at root (if it duplicates core/constants.py)
    root_constants = TARGET / "constants.py"
    if root_constants.exists():
        # Keep it but ensure it imports from the right place
        print("  Kept root constants.py (re-exports)")


def main():
    print("=" * 60)
    print("Migrating mountainash-dataframes -> mountainash.dataframes")
    print("=" * 60)

    step1_copy_source()
    step2_rewrite_imports()
    step3_fix_expression_integration()
    step4_remove_root_init_version()

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Update mountainash/__init__.py with dataframes exports")
    print("  2. Update dataframes/__init__.py for new package")
    print("  3. Port tests")
    print("  4. Run: hatch run test:test-quick")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script**

Run: `python scripts/migrate_dataframes.py`

Expected: Source copied, ~14 files rewritten, expression imports updated.

- [ ] **Step 3: Verify no stale imports remain**

Run: `grep -r "from mountainash_dataframes\." src/mountainash/dataframes/ --include="*.py" | head -5`
Expected: No matches

Run: `grep -r "mountainash_expressions" src/mountainash/dataframes/ --include="*.py" | head -5`
Expected: No matches (all should be `mountainash.expressions`)

- [ ] **Step 4: Commit**

```bash
git add scripts/migrate_dataframes.py src/mountainash/dataframes/
git commit -m "feat: port mountainash-dataframes source into unified package

- 45 source files copied from mountainash-dataframes
- 14 absolute imports rewritten to mountainash.dataframes
- Expression integration imports updated to mountainash.expressions
- Removed _deprecated directory"
```

---

### Task 2: Update dataframes __init__.py

The copied `__init__.py` has old imports and lazy_loader references. Replace it with a clean version that exports the right things.

**Files:**
- Modify: `src/mountainash/dataframes/__init__.py`

- [ ] **Step 1: Read the current copied __init__.py**

Read: `src/mountainash/dataframes/__init__.py` to see what was copied and what needs updating.

- [ ] **Step 2: Write a clean __init__.py**

The file should export the key user-facing classes without relying on lazy_loader (which has complex string-based module paths that may break):

```python
"""Mountainash DataFrames — cross-backend DataFrame operations.

Provides TableBuilder fluent API, DataFrameSystem backend abstraction,
and DataFrameUtils high-level API for joins, selects, casts, and more.
"""

# Core classes
from mountainash.dataframes.core.dataframe_system.base import DataFrameSystem
from mountainash.dataframes.core.dataframe_system.factory import DataFrameSystemFactory
from mountainash.dataframes.core.dataframe_system.constants import CONST_DATAFRAME_BACKEND

# TableBuilder fluent API
from mountainash.dataframes.core.table_builder.table_builder import (
    TableBuilder,
    table,
    from_polars,
    from_pandas,
    from_pyarrow,
    from_ibis,
    from_dict,
    from_records,
)

# Protocols
from mountainash.dataframes.core.protocols import (
    CastProtocol,
    IntrospectProtocol,
    SelectProtocol,
    JoinProtocol,
    FilterProtocol,
    RowProtocol,
    LazyProtocol,
)

# High-level API (lazy import to avoid circular deps)
def __getattr__(name):
    if name == "DataFrameUtils":
        from mountainash.dataframes.core.api.dataframe_utils import DataFrameUtils
        return DataFrameUtils
    raise AttributeError(f"module 'mountainash.dataframes' has no attribute {name!r}")


__all__ = [
    # Core
    "DataFrameSystem",
    "DataFrameSystemFactory",
    "CONST_DATAFRAME_BACKEND",
    # TableBuilder
    "TableBuilder",
    "table",
    "from_polars",
    "from_pandas",
    "from_pyarrow",
    "from_ibis",
    "from_dict",
    "from_records",
    # Protocols
    "CastProtocol",
    "IntrospectProtocol",
    "SelectProtocol",
    "JoinProtocol",
    "FilterProtocol",
    "RowProtocol",
    "LazyProtocol",
    # Lazy
    "DataFrameUtils",
]
```

- [ ] **Step 3: Test the import**

Run: `hatch run test:python -c "from mountainash.dataframes import table, TableBuilder; print('OK')"`
Expected: `OK`

If this fails, debug the import chain. Common issue: the `core/__init__.py` may use lazy_loader with old module paths. If so, replace it with simple imports or fix the paths.

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/dataframes/__init__.py
git commit -m "feat: clean up dataframes __init__.py exports for unified package"
```

---

### Task 3: Wire up top-level mountainash exports

Add `table` and `TableBuilder` to the top-level `mountainash` package.

**Files:**
- Modify: `src/mountainash/__init__.py`

- [ ] **Step 1: Read current mountainash __init__.py**

Read: `src/mountainash/__init__.py`

- [ ] **Step 2: Add dataframes exports**

Add after the expressions imports:

```python
# Dataframes - TableBuilder fluent API
try:
    from mountainash.dataframes import table, TableBuilder  # noqa: F401
except ImportError:
    pass  # dataframes module not yet available
```

- [ ] **Step 3: Test top-level import**

Run: `hatch run test:python -c "import mountainash as ma; print(ma.table); print(ma.TableBuilder)"`
Expected: Prints function and class references

Run: `hatch run test:python -c "import mountainash as ma; print(ma.col); print(ma.lit)"`
Expected: Still works (expressions not broken)

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/__init__.py
git commit -m "feat: export table and TableBuilder at top-level mountainash package"
```

---

### Task 4: Fix internal import issues

The copied source may have import issues due to lazy_loader paths, circular imports, or missing dependencies. This task is about running the imports and fixing whatever breaks.

**Files:**
- Possibly modify: various files under `src/mountainash/dataframes/`

- [ ] **Step 1: Test the full import chain**

Run: `hatch run test:python -c "
from mountainash.dataframes import table, TableBuilder, DataFrameSystemFactory
from mountainash.dataframes import CastProtocol, FilterProtocol
import polars as pl
df = pl.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
tb = table(df)
print('TableBuilder created:', type(tb).__name__)
print('Shape:', tb.shape)
print('Columns:', tb.columns)
result = tb.select('x').to_polars()
print('Select result shape:', result.shape)
"`
Expected: All prints succeed

- [ ] **Step 2: Fix any import errors**

Common issues to fix:
- `lazy_loader` module paths still referencing `mountainash_dataframes` → replace with direct imports
- `core/__init__.py` using lazy_loader → replace with standard imports or fix paths
- Missing `__init__.py` conversion directory → ensure exists
- Circular imports → use lazy imports (in function body, not module level)

For each error, read the failing file, identify the broken import, fix it.

- [ ] **Step 3: Test expression integration**

Run: `hatch run test:python -c "
import mountainash as ma
import polars as pl
df = pl.DataFrame({'age': [25, 35, 45], 'name': ['a', 'b', 'c']})
result = ma.table(df).filter(ma.col('age').gt(30)).to_polars()
print('Filtered rows:', result.shape[0])
assert result.shape[0] == 2, f'Expected 2 rows, got {result.shape[0]}'
print('Expression integration works!')
"`
Expected: `Filtered rows: 2` and `Expression integration works!`

- [ ] **Step 4: Commit fixes**

```bash
git add src/mountainash/dataframes/
git commit -m "fix: resolve import issues in ported dataframes code"
```

---

### Task 5: Port tests

Copy test files from mountainash-dataframes into `tests/dataframes/`, rewrite imports, and flatten the directory structure.

**Files:**
- Create: `tests/dataframes/` directory with ported test files

- [ ] **Step 1: Create port script for tests**

```python
#!/usr/bin/env python3
"""Port mountainash-dataframes tests into unified package test suite."""

import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SRC_TESTS = REPO_ROOT.parent / "mountainash-dataframes" / "tests"
TARGET_TESTS = REPO_ROOT / "tests" / "dataframes"


def main():
    print("Porting dataframes tests...")

    if TARGET_TESTS.exists():
        shutil.rmtree(TARGET_TESTS)

    # Copy the test directory
    shutil.copytree(SRC_TESTS, TARGET_TESTS)
    print(f"  Copied {SRC_TESTS} -> {TARGET_TESTS}")

    # Clean __pycache__
    for pycache in TARGET_TESTS.rglob("__pycache__"):
        shutil.rmtree(pycache)

    # Rewrite imports in all test files
    count = 0
    for py_file in TARGET_TESTS.rglob("*.py"):
        content = py_file.read_text()
        original = content

        # Rewrite package imports
        content = re.sub(
            r'from mountainash_dataframes\.',
            'from mountainash.dataframes.',
            content,
        )
        content = re.sub(
            r'from mountainash_dataframes import',
            'from mountainash.dataframes import',
            content,
        )
        content = re.sub(
            r'import mountainash_dataframes\b',
            'import mountainash.dataframes',
            content,
        )
        # Also fix any mountainash_expressions references
        content = re.sub(
            r'from mountainash_expressions\.',
            'from mountainash.expressions.',
            content,
        )
        content = re.sub(
            r'import mountainash_expressions\b',
            'import mountainash.expressions',
            content,
        )

        if content != original:
            py_file.write_text(content)
            count += 1

    print(f"  Rewrote imports in {count} test files")
    print("Done!")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the test port script**

Run: `python scripts/port_dataframes_tests.py`

- [ ] **Step 3: Verify test imports**

Run: `grep -r "mountainash_dataframes" tests/dataframes/ --include="*.py" | head -5`
Expected: No matches (all rewritten)

- [ ] **Step 4: Commit**

```bash
git add scripts/port_dataframes_tests.py tests/dataframes/
git commit -m "feat: port dataframes tests into unified package test suite

- 84 test files copied from mountainash-dataframes
- All imports rewritten to mountainash.dataframes"
```

---

### Task 6: Run tests and fix failures

Run the ported dataframes tests and fix whatever breaks. Also verify existing expression tests still pass.

**Files:**
- Possibly modify: test files and source files

- [ ] **Step 1: Run expression tests first (regression check)**

Run: `hatch run test:test-target-quick tests/cross_backend/test_boolean.py -v 2>&1 | tail -10`
Expected: All pass (no regressions from dataframes port)

- [ ] **Step 2: Run dataframes tests**

Run: `hatch run test:test-target-quick tests/dataframes/ -v 2>&1 | tail -40`

Note failures. Common issues:
- **Import errors**: Missing modules, wrong paths → fix imports
- **Fixture errors**: conftest.py references fixtures at old paths → update paths
- **Missing dependencies**: Tests may need packages not in hatch test env → add to hatch.toml

- [ ] **Step 3: Fix failing tests iteratively**

For each category of failure:
1. Read the error
2. Identify root cause (import path, missing fixture, missing dep)
3. Fix minimally
4. Re-run that specific test file

- [ ] **Step 4: Run the full test suite**

Run: `hatch run test:test-quick 2>&1 | tail -10`

Expected: All expression tests pass (2842+), dataframes tests mostly pass. Note any remaining failures.

- [ ] **Step 5: Commit fixes**

```bash
git add -A
git commit -m "fix: resolve test failures in ported dataframes tests"
```

---

### Task 7: Write expression integration test

A new test that validates the killer feature: `table(df).filter(ma.col(...))`.

**Files:**
- Create: `tests/dataframes/test_expression_integration.py`

- [ ] **Step 1: Write the test**

```python
"""Test that TableBuilder.filter() integrates with mountainash expressions."""
import pytest
import polars as pl

import mountainash as ma
from mountainash.dataframes import table


class TestExpressionIntegration:
    """Verify TableBuilder.filter() accepts BaseExpressionAPI objects."""

    def test_filter_with_gt_expression(self):
        """Filter with ma.col().gt() produces correct results."""
        df = pl.DataFrame({"age": [25, 35, 45], "name": ["alice", "bob", "charlie"]})
        result = table(df).filter(ma.col("age").gt(30)).to_polars()
        assert result.shape[0] == 2
        assert result["name"].to_list() == ["bob", "charlie"]

    def test_filter_with_compound_expression(self):
        """Filter with compound AND expression."""
        df = pl.DataFrame({
            "age": [25, 35, 45, 55],
            "score": [90, 60, 80, 70],
        })
        expr = ma.col("age").gt(30).and_(ma.col("score").ge(75))
        result = table(df).filter(expr).to_polars()
        assert result.shape[0] == 2
        assert result["age"].to_list() == [45, 55]

    def test_filter_with_string_expression(self):
        """Filter with string contains expression."""
        df = pl.DataFrame({"name": ["alice", "bob", "charlie", "david"]})
        result = table(df).filter(ma.col("name").str.contains("a")).to_polars()
        assert result.shape[0] == 3  # alice, charlie, david

    def test_filter_with_native_expression_still_works(self):
        """Native Polars expressions still work (not broken by integration)."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(pl.col("x") > 3).to_polars()
        assert result.shape[0] == 2

    def test_filter_chain_mixed(self):
        """Chain mountainash and native filters."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})
        result = (
            table(df)
            .filter(ma.col("x").gt(2))
            .filter(pl.col("y") < 50)
            .to_polars()
        )
        assert result.shape[0] == 2  # x=3,y=30 and x=4,y=40

    def test_top_level_table_import(self):
        """ma.table() is accessible at top level."""
        df = pl.DataFrame({"a": [1]})
        result = ma.table(df).to_polars()
        assert result.shape == (1, 1)

    def test_where_alias_with_expression(self):
        """where() alias also accepts mountainash expressions."""
        df = pl.DataFrame({"x": [1, 2, 3]})
        result = table(df).where(ma.col("x").gt(1)).to_polars()
        assert result.shape[0] == 2
```

- [ ] **Step 2: Run the test**

Run: `hatch run test:test-target-quick tests/dataframes/test_expression_integration.py -v`
Expected: All 7 tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/dataframes/test_expression_integration.py
git commit -m "test: add expression integration tests for TableBuilder.filter()"
```

---

### Task 8: Final verification and cleanup

- [ ] **Step 1: Remove migration scripts**

```bash
rm scripts/migrate_dataframes.py scripts/port_dataframes_tests.py
git add scripts/
git commit -m "chore: remove one-time dataframes migration scripts"
```

- [ ] **Step 2: Run full test suite**

Run: `hatch run test:test-quick 2>&1 | tail -10`

Expected: Expression tests (2842+) all pass, dataframes tests pass, expression integration tests pass.

- [ ] **Step 3: Verify key imports**

Run: `hatch run test:python -c "
import mountainash as ma
import polars as pl

# Expression API (unchanged)
expr = ma.col('x').gt(5)
print('Expressions: OK')

# Table API (new)
df = pl.DataFrame({'x': [1, 10], 'name': ['a', 'b']})
result = ma.table(df).filter(ma.col('x').gt(5)).to_polars()
print('TableBuilder + filter:', result.shape)

# Direct import
from mountainash.dataframes import TableBuilder, DataFrameUtils
print('Direct imports: OK')

print('Phase 2 complete!')
"`

Expected: All prints succeed, `Phase 2 complete!`

- [ ] **Step 4: Commit summary**

```bash
git add -A
git commit -m "feat: complete Phase 2 — dataframes ported to unified mountainash package

- 45 source files ported from mountainash-dataframes
- TableBuilder fluent API: ma.table(df).select().filter().join()
- Expression integration: ma.table(df).filter(ma.col('age').gt(30))
- 84 test files ported + 7 new expression integration tests
- All expression tests pass (no regressions)
- Top-level exports: ma.table(), ma.TableBuilder"
```
