#!/usr/bin/env python3
"""Migrate mountainash-schema into the unified mountainash package."""
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SRC_REPO = REPO_ROOT.parent / "mountainash-schema" / "src" / "mountainash_schema"
TARGET = REPO_ROOT / "src" / "mountainash" / "schema"

def main():
    print("=" * 60)
    print("Migrating mountainash-schema -> mountainash.schema")
    print("=" * 60)

    # Step 1: Copy source
    print("Step 1: Copying source...")
    if not SRC_REPO.exists():
        raise FileNotFoundError(f"Source not found: {SRC_REPO}")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SRC_REPO, TARGET)
    for pycache in TARGET.rglob("__pycache__"):
        shutil.rmtree(pycache)
    deprecated = TARGET / "_deprecated"
    if deprecated.exists():
        shutil.rmtree(deprecated)
    version_file = TARGET / "__version__.py"
    if version_file.exists():
        version_file.unlink()
    print(f"  Copied {SRC_REPO} -> {TARGET}")

    # Step 2: Rewrite imports
    print("Step 2: Rewriting imports...")
    count = 0
    for py_file in TARGET.rglob("*.py"):
        content = py_file.read_text()
        original = content
        # Rewrite mountainash_schema -> mountainash.schema
        content = re.sub(r'from mountainash_schema\.', 'from mountainash.schema.', content)
        content = re.sub(r'import mountainash_schema\.', 'import mountainash.schema.', content)
        content = re.sub(r'"mountainash_schema\.', '"mountainash.schema.', content)
        content = re.sub(r"'mountainash_schema\.", "'mountainash.schema.", content)
        # Rewrite mountainash_dataframes -> mountainash.dataframes
        content = re.sub(r'from mountainash_dataframes\.', 'from mountainash.dataframes.', content)
        content = re.sub(r'from mountainash_dataframes import', 'from mountainash.dataframes import', content)
        content = re.sub(r'import mountainash_dataframes\.', 'import mountainash.dataframes.', content)
        content = re.sub(r'"mountainash_dataframes\.', '"mountainash.dataframes.', content)
        content = re.sub(r"'mountainash_dataframes\.", "'mountainash.dataframes.", content)
        # Rewrite mountainash_expressions -> mountainash.expressions
        content = re.sub(r'from mountainash_expressions\.', 'from mountainash.expressions.', content)
        content = re.sub(r'import mountainash_expressions', 'import mountainash.expressions', content)
        if content != original:
            py_file.write_text(content)
            count += 1
    print(f"  Rewrote imports in {count} files")

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
