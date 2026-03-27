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
    shutil.copytree(SRC_TESTS, TARGET_TESTS)
    print(f"  Copied {SRC_TESTS} -> {TARGET_TESTS}")

    # Clean __pycache__
    for pycache in TARGET_TESTS.rglob("__pycache__"):
        shutil.rmtree(pycache)

    # Rewrite imports
    count = 0
    for py_file in TARGET_TESTS.rglob("*.py"):
        content = py_file.read_text()
        original = content
        content = re.sub(r'from mountainash_dataframes\.', 'from mountainash.dataframes.', content)
        content = re.sub(r'from mountainash_dataframes import', 'from mountainash.dataframes import', content)
        content = re.sub(r'import mountainash_dataframes\b', 'import mountainash.dataframes', content)
        content = re.sub(r'from mountainash_expressions\.', 'from mountainash.expressions.', content)
        content = re.sub(r'import mountainash_expressions\b', 'import mountainash.expressions', content)
        # Also fix string references
        content = re.sub(r'"mountainash_dataframes\.', '"mountainash.dataframes.', content)
        content = re.sub(r"'mountainash_dataframes\.", "'mountainash.dataframes.", content)
        if content != original:
            py_file.write_text(content)
            count += 1
    print(f"  Rewrote imports in {count} test files")
    print("Done!")

if __name__ == "__main__":
    main()
