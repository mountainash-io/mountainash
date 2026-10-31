"""Execute the recipes users run and check their documented output."""

from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
RECIPES = sorted((ROOT / "examples").glob("*/example.py"))
assert RECIPES, "no recipes found"


def _documented_output(recipe: Path) -> str:
    readme = (recipe.parent / "README.md").read_text(encoding="utf-8")
    match = re.search(r"Expected output:\n\n```text\n(.*?)^```", readme, re.MULTILINE | re.DOTALL)
    assert match, f"{recipe.parent.name}/README.md must document its expected output"
    return match.group(1).strip()


def _tree(work: Path) -> list[tuple[Path, bytes | None]]:
    return sorted(
        (p.relative_to(work), p.read_bytes() if p.is_file() else None)
        for p in work.rglob("*")
    )


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda path: path.parent.name)
def test_recipe_prints_documented_output(recipe: Path, tmp_path: Path) -> None:
    work = tmp_path / "examples"
    shutil.copytree(EXAMPLES, work)
    before = _tree(work)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    script = str(work / recipe.relative_to(EXAMPLES))
    outputs = []
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-I", script], cwd=cwd,
            capture_output=True, text=True, timeout=120, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1], "recipe output differs between runs"
    assert outputs[0].strip() == _documented_output(recipe)
    assert _tree(work) == before, "recipe left files in the examples tree"
    assert not list(cwd.iterdir()), "recipe left files in its working directory"


def test_index_lists_every_recipe() -> None:
    index = (EXAMPLES / "README.md").read_text(encoding="utf-8")
    missing = [path.parent.name for path in RECIPES if f"]({path.parent.name}/)" not in index]
    assert not missing, f"examples/README.md does not link: {missing}"


def test_readmes_have_no_dashes() -> None:
    offenders = []
    for readme in EXAMPLES.rglob("README.md"):
        text = readme.read_text(encoding="utf-8")
        if any(token in text for token in ("—", "–", " -- ")):
            offenders.append(str(readme.relative_to(ROOT)))
    assert not offenders, f"dashes found in: {offenders}"


def test_readme_links_resolve() -> None:
    link = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
    dangling = []
    for readme in EXAMPLES.rglob("README.md"):
        for target in link.findall(readme.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0]
            if not (readme.parent / path).exists():
                dangling.append(f"{readme.relative_to(ROOT)} -> {target}")
    assert not dangling, f"dangling README links: {dangling}"
