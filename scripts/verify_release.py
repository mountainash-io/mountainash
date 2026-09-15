"""Verify Mountainash distributions outside checkouts, using public PyPI dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import venv
import zipfile
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

PYPI = "https://pypi.org/simple"
EXTRA_IMPORTS = {
    "pandas": ("pandas",),
    "ibis": ("ibis",),
    "storage": ("mountainash_transport",),
    "files": ("mountainash_files",),
    "dbos": ("dbos",),
    "s3": ("mountainash_files", "boto3", "s3fs"),
    "gcs": ("mountainash_files", "google.cloud.storage", "gcsfs"),
    "azure": ("mountainash_files", "azure.storage.blob", "adlfs"),
    "sftp": ("mountainash_files", "paramiko", "smart_open"),
}
HELLO_WORLD = """
import json
import sys
from pathlib import Path
import mountainash as ma
import polars as pl

origin = Path(ma.__file__).resolve()
if not origin.is_relative_to(Path(sys.prefix).resolve()):
    raise RuntimeError(f"Mountainash loaded outside the verification environment: {origin}")
df = pl.DataFrame({"name": ["Ada", "Lin", "Sam"], "age": [37, 22, None]})
rows = ma.relation(df).filter(ma.col("age").gt(30)).sort("name").to_polars().to_dicts()
if rows != [{"name": "Ada", "age": 37}]:
    raise RuntimeError(f"Unexpected hello-world result: {rows!r}")
print(json.dumps({"rows": rows, "module": str(origin), "python": sys.version}))
"""


def check_install_report(report: Path, candidate: Path | None) -> set[str]:
    """Reject dependency sources other than PyPI and the one selected candidate."""
    allowed_local = candidate.resolve().as_uri() if candidate is not None else None
    candidate_seen = False
    names = set()
    for item in json.loads(report.read_text())["install"]:
        name = canonicalize_name(item["metadata"]["name"])
        names.add(name)
        url = item["download_info"]["url"]
        if allowed_local is not None and url == allowed_local:
            candidate_seen = True
            continue
        source = urlsplit(url)
        if (
            source.scheme != "https"
            or source.hostname not in {"pypi.org", "files.pythonhosted.org"}
            or source.username is not None
            or source.password is not None
            or source.port not in {None, 443}
        ):
            raise ValueError(f"{name} resolved from a non-public dependency source: {url}")
    if allowed_local is not None and not candidate_seen:
        raise ValueError("The install report does not contain the selected candidate")
    return names


def check_public_files(published: dict, expected: dict[str, str]) -> None:
    """Publication is complete only when the exact approved files are public."""
    observed = {item["filename"]: item["digests"]["sha256"] for item in published["urls"]}
    if set(observed) != set(expected) or len(observed) != len(published["urls"]):
        raise ValueError(f"Public file set differs: expected {sorted(expected)}, got {sorted(observed)}")
    if observed != expected:
        raise ValueError("Public artifact hash differs from the approved candidate")


def _metadata(wheel: Path) -> dict:
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(names) != 1:
            raise ValueError(f"{wheel.name} must contain exactly one distribution metadata record")
        metadata = BytesParser().parsebytes(archive.read(names[0]))
    requirements = sorted(metadata.get_all("Requires-Dist", []))
    for requirement in requirements:
        if Requirement(requirement).url is not None:
            raise ValueError(f"Direct-reference runtime requirement is not public-index metadata: {requirement}")
    if canonicalize_name(metadata["Name"]) != "mountainash":
        raise ValueError(f"Expected Mountainash, not {metadata['Name']}")
    if metadata["Requires-Python"] != ">=3.12":
        raise ValueError("Requires-Python must declare the approved >=3.12 support policy")
    return {
        "distribution": metadata["Name"],
        "version": metadata["Version"],
        "requires_python": metadata["Requires-Python"],
        "requires_dist": requirements,
        "extras": sorted(metadata.get_all("Provides-Extra", [])),
    }


def _artifacts(directory: Path) -> tuple[Path, Path]:
    wheels = list(directory.glob("*.whl"))
    sdists = list(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1 or len(list(directory.iterdir())) != 2:
        raise ValueError("Distribution directory must contain exactly one wheel and one sdist")
    return wheels[0], sdists[0]


def _environment(home: Path) -> dict[str, str]:
    # Allow-list rather than chasing every pip/uv/Python/credential override.
    environment = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR"}
    }
    environment.update(
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / "config"),
        PIP_CONFIG_FILE=os.devnull,
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        PIP_INDEX_URL=PYPI,
    )
    return environment


def _run(command: list[str], cwd: Path, environment: dict[str, str], log: Path) -> None:
    print(f"Running {log.stem}", flush=True)
    with log.open("w") as output:
        result = subprocess.run(command, cwd=cwd, env=environment, stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, command)


def _install(
    requirement: str,
    candidate: Path | None,
    label: str,
    work: Path,
    evidence: Path,
    environment: dict[str, str],
    imports: tuple[str, ...] = (),
) -> set[str]:
    target = work / label
    venv.EnvBuilder(with_pip=True).create(target)
    python = str(target / "bin" / "python")
    report = evidence / f"{label}-install.json"
    _run(
        [python, "-I", "-m", "pip", "install", "--no-input", "--index-url", PYPI, "--report", str(report), requirement],
        work,
        environment,
        evidence / f"{label}-install.log",
    )
    names = check_install_report(report, candidate)
    _run([python, "-I", "-m", "pip", "check"], work, environment, evidence / f"{label}-check.log")
    smoke = HELLO_WORLD
    if imports:
        smoke += "\nimport importlib\n"
        smoke += f"\nfor name in {imports!r}:\n    importlib.import_module(name)\n"
    _run([python, "-I", "-c", smoke], work, environment, evidence / f"{label}-hello.json")
    print((evidence / f"{label}-hello.json").read_text(), end="")
    return names


def verify(dist: Path, evidence: Path, *, base_only: bool = False, public: bool = False) -> None:
    hashes: dict[str, str] = {}
    release: dict[str, object] = {
        "source_sha": os.environ.get("GITHUB_SHA"),
        "repository": os.environ.get("GITHUB_REPOSITORY"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "files": hashes,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "scope": "public-base" if public else "candidate-base" if base_only else "candidate-full",
        "status": "running",
    }
    evidence.mkdir(parents=True, exist_ok=False)
    release_path = evidence / "release.json"
    release_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")
    try:
        wheel, sdist = _artifacts(dist)
        metadata = _metadata(wheel)
        release.update(metadata)
        unknown = set(metadata["extras"]) - EXTRA_IMPORTS.keys() - {"all"}
        if unknown:
            raise ValueError(f"Advertised extras lack import smoke coverage: {sorted(unknown)}")
        for path in (wheel, sdist):
            with path.open("rb") as stream:
                hashes[path.name] = hashlib.file_digest(stream, "sha256").hexdigest()
        (evidence / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(hashes.items())))
        with tempfile.TemporaryDirectory(prefix="mountainash-release-") as temporary:
            work = Path(temporary)
            home = work / "home"
            home.mkdir()
            environment = _environment(home)
            if public:
                url = f"https://pypi.org/pypi/{metadata['distribution']}/{metadata['version']}/json"
                with urlopen(url, timeout=30) as response:
                    published = json.load(response)
                check_public_files(published, hashes)
                (evidence / "public-pypi.json").write_text(json.dumps(published, indent=2) + "\n")
                _install(
                    f"{metadata['distribution']}=={metadata['version']}",
                    None,
                    "public",
                    work,
                    evidence,
                    environment,
                )
            else:
                names = _install(str(wheel), wheel, "wheel", work, evidence, environment)
                owned = sorted(name for name in names if name.startswith("mountainash-"))
                if owned:
                    raise ValueError(f"Base installation unexpectedly requires optional siblings: {owned}")
                build_env = work / "build"
                venv.EnvBuilder(with_pip=True).create(build_env)
                rebuilt = work / "rebuilt"
                _run(
                    [
                        str(build_env / "bin" / "python"),
                        "-I",
                        "-m",
                        "pip",
                        "wheel",
                        "--no-deps",
                        "--index-url",
                        PYPI,
                        "--wheel-dir",
                        str(rebuilt),
                        str(sdist),
                    ],
                    work,
                    environment,
                    evidence / "sdist-build.log",
                )
                rebuilt_wheels = list(rebuilt.glob("*.whl"))
                if len(rebuilt_wheels) != 1 or _metadata(rebuilt_wheels[0]) != metadata:
                    raise ValueError("The sdist-derived wheel has a different distribution contract")
                _install(
                    str(rebuilt_wheels[0]),
                    rebuilt_wheels[0],
                    "sdist",
                    work,
                    evidence,
                    environment,
                )
                if not base_only:
                    for extra in metadata["extras"]:
                        imports = (
                            tuple(
                                dict.fromkeys(
                                    module
                                    for key in metadata["extras"]
                                    if key != "all"
                                    for module in EXTRA_IMPORTS[key]
                                )
                            )
                            if extra == "all"
                            else EXTRA_IMPORTS[extra]
                        )
                        _install(
                            f"{metadata['distribution']}[{extra}] @ {wheel.as_uri()}",
                            wheel,
                            f"extra-{extra}",
                            work,
                            evidence,
                            environment,
                            imports,
                        )
        release["status"] = "passed"
    except Exception as error:
        release["status"] = "failed"
        release["error"] = str(error)
        raise
    finally:
        release_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")
    print(f"Verified {release['scope']}: {release_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--base-only", action="store_true", help="Wheel/sdist hello world only; not full release acceptance"
    )
    parser.add_argument("--public", action="store_true", help="Confirm approved hashes and install the public version")
    arguments = parser.parse_args()
    verify(
        arguments.dist_dir.resolve(),
        arguments.output_dir.resolve(),
        base_only=arguments.base_only,
        public=arguments.public,
    )


if __name__ == "__main__":
    main()
