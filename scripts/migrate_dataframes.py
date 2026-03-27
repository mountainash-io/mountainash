#!/usr/bin/env python3
"""Migrate mountainash-dataframes into the unified mountainash package."""

import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SRC_REPO = REPO_ROOT.parent / "mountainash-dataframes" / "src" / "mountainash_dataframes"
TARGET = REPO_ROOT / "src" / "mountainash" / "dataframes"


def step1_copy_source():
    print("Step 1: Copying dataframes source...")
    if not SRC_REPO.exists():
        raise FileNotFoundError(f"Source repo not found: {SRC_REPO}")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SRC_REPO, TARGET)
    print(f"  Copied {SRC_REPO} -> {TARGET}")
    deprecated = TARGET / "_deprecated"
    if deprecated.exists():
        shutil.rmtree(deprecated)
        print("  Removed _deprecated/")
    for pycache in TARGET.rglob("__pycache__"):
        shutil.rmtree(pycache)
    print("  Cleaned __pycache__/")


def step2_rewrite_imports():
    print("Step 2: Rewriting imports...")
    count = 0
    for py_file in TARGET.rglob("*.py"):
        content = py_file.read_text()
        original = content
        content = re.sub(r'from mountainash_dataframes\.', 'from mountainash.dataframes.', content)
        content = re.sub(r'import mountainash_dataframes\.', 'import mountainash.dataframes.', content)
        content = re.sub(r'"mountainash_dataframes\.', '"mountainash.dataframes.', content)
        content = re.sub(r"'mountainash_dataframes\.", "'mountainash.dataframes.", content)
        # Also fix mountainash_expressions references to use new path
        content = re.sub(r'from mountainash_expressions\.', 'from mountainash.expressions.', content)
        content = re.sub(r'import mountainash_expressions\.', 'import mountainash.expressions.', content)
        content = re.sub(r'from mountainash_expressions import', 'from mountainash.expressions import', content)
        content = re.sub(r'import mountainash_expressions\b', 'import mountainash.expressions', content)
        if content != original:
            py_file.write_text(content)
            count += 1
    print(f"  Rewrote imports in {count} files")


def step3_cleanup():
    print("Step 3: Cleaning up...")
    version_file = TARGET / "__version__.py"
    if version_file.exists():
        version_file.unlink()
        print("  Removed __version__.py")


def main():
    print("=" * 60)
    print("Migrating mountainash-dataframes -> mountainash.dataframes")
    print("=" * 60)
    step1_copy_source()
    step2_rewrite_imports()
    step3_cleanup()
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
