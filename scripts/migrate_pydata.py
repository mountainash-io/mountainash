#!/usr/bin/env python3
"""Migrate mountainash-pydata into the unified mountainash package."""
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SRC_REPO = REPO_ROOT.parent / "mountainash-pydata" / "src" / "mountainash_pydata"
TARGET = REPO_ROOT / "src" / "mountainash" / "pydata"

def main():
    print("=" * 60)
    print("Migrating mountainash-pydata -> mountainash.pydata")
    print("=" * 60)

    # Copy source
    print("Step 1: Copying source...")
    if not SRC_REPO.exists():
        raise FileNotFoundError(f"Source not found: {SRC_REPO}")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SRC_REPO, TARGET)
    for pycache in TARGET.rglob("__pycache__"):
        shutil.rmtree(pycache)
    version_file = TARGET / "__version__.py"
    if version_file.exists():
        version_file.unlink()
    print(f"  Copied {SRC_REPO} -> {TARGET}")

    # Rewrite imports
    print("Step 2: Rewriting imports...")
    count = 0
    for py_file in TARGET.rglob("*.py"):
        content = py_file.read_text()
        original = content
        # mountainash_pydata -> mountainash.pydata
        content = re.sub(r'from mountainash_pydata\.', 'from mountainash.pydata.', content)
        content = re.sub(r'import mountainash_pydata\.', 'import mountainash.pydata.', content)
        content = re.sub(r'"mountainash_pydata\.', '"mountainash.pydata.', content)
        content = re.sub(r"'mountainash_pydata\.", "'mountainash.pydata.", content)
        # mountainash_dataframes -> mountainash.dataframes
        content = re.sub(r'from mountainash_dataframes\.', 'from mountainash.dataframes.', content)
        content = re.sub(r'from mountainash_dataframes import', 'from mountainash.dataframes import', content)
        content = re.sub(r'import mountainash_dataframes\.', 'import mountainash.dataframes.', content)
        content = re.sub(r'"mountainash_dataframes\.', '"mountainash.dataframes.', content)
        content = re.sub(r"'mountainash_dataframes\.", "'mountainash.dataframes.", content)
        # mountainash_schema -> mountainash.schema
        content = re.sub(r'from mountainash_schema\.', 'from mountainash.schema.', content)
        content = re.sub(r'from mountainash_schema import', 'from mountainash.schema import', content)
        # mountainash_expressions -> mountainash.expressions
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
