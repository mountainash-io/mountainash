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
    for subdir in ("dataframes", "schema", "pydata"):
        (NEW_PKG / subdir).mkdir(exist_ok=True)


def step2_move_expression_source():
    """Move mountainash_expressions/ -> mountainash/expressions/."""
    print("Step 2: Moving expression source...")
    if NEW_EXPR.exists():
        shutil.rmtree(NEW_EXPR)
    shutil.copytree(OLD_PKG, NEW_EXPR, dirs_exist_ok=False)
    print(f"  Copied {OLD_PKG} -> {NEW_EXPR}")


def step3_extract_shared_core():
    """Move shared files from expressions/core/ to mountainash/core/."""
    print("Step 3: Extracting shared core...")

    src_constants = NEW_EXPR / "core" / "constants.py"
    dst_constants = NEW_CORE / "constants.py"
    shutil.copy2(src_constants, dst_constants)
    print(f"  Copied constants.py to core/")

    src_types = NEW_EXPR / "types.py"
    dst_types = NEW_CORE / "types.py"
    shutil.copy2(src_types, dst_types)
    print(f"  Copied types.py to core/")

    src_constants.write_text(
        '"""Backwards-compat re-exports from mountainash.core.constants."""\n'
        'from mountainash.core.constants import *  # noqa: F401,F403\n'
    )
    print(f"  Replaced expressions/core/constants.py with re-export shim")

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

    (NEW_CORE / "__init__.py").write_text(
        '"""Mountainash core - shared infrastructure for all modules."""\n'
    )
    print("  Created mountainash/core/__init__.py")

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

    if OLD_PKG.exists():
        shutil.rmtree(OLD_PKG)

    OLD_PKG.mkdir()

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
