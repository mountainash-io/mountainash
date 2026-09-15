# Release Procedure

Mountainash requires Python 3.12 or later. A verified candidate is not a published release. Required sibling versions must be available on public PyPI before the full candidate check can pass.

## Prepare the source

1. Prepare release changes on `release/*` from `develop`, or a scoped `hotfix/*`, following [CONTRIBUTING.md](CONTRIBUTING.md). Required CI and code-owner review still apply; do not push directly to protected branches.
2. Select the final, unused version in `src/mountainash/__version__.py` under the repository's version policy. The publishing workflow does not rewrite versions or generate a suffix after verification.
3. Record compatibility changes, including the Python 3.12 floor, and reconcile dependency bounds. Files/cloud extras currently require `mountainash-files>=26.8.0,<27`; storage requires `mountainash-transport>=26.7.0`. Publication does not make these optional dependencies mandatory.
4. Release dependencies in order: settings and secrets → auth-client → transport → files. Each repository owns its release authorization. `mountainash-data` is not a prerequisite merely because source tests provision it.

## Verify a local candidate

Use a complete Python 3.12 installation with `venv`/`ensurepip`. On minimal Linux installations, install the distribution's Python venv support or use a complete managed interpreter; do not reuse the development environment as release proof.

From the source checkout, with fresh output paths:

```bash
python3.12 -m venv /tmp/mountainash-release-tools

env -i PATH="$PATH" HOME=/tmp/mountainash-release-home PIP_CONFIG_FILE=/dev/null \
  /tmp/mountainash-release-tools/bin/python -I -m pip install \
  --index-url https://pypi.org/simple build twine

env -i PATH="$PATH" HOME=/tmp/mountainash-release-home PIP_CONFIG_FILE=/dev/null \
  PIP_INDEX_URL=https://pypi.org/simple \
  /tmp/mountainash-release-tools/bin/python -I -m build \
  --wheel --sdist --outdir /tmp/mountainash-release-dist

/tmp/mountainash-release-tools/bin/python -I -m twine check /tmp/mountainash-release-dist/*

/tmp/mountainash-release-tools/bin/python -I scripts/verify_release.py \
  --dist-dir /tmp/mountainash-release-dist \
  --output-dir /tmp/mountainash-release-evidence
```

The distribution directory must contain exactly the wheel and sdist, with no other files. Use the PyPA build command above: some other build tools add repository-control files to their output directory.

The verifier installs from outside all checkouts in fresh environments, removes index/source/Python overrides, checks installation provenance and dependency consistency, rebuilds from the sdist, and executes the README hello world. It discovers extras from the candidate's metadata and checks each extra plus `all`. Cloud credentials and live cloud services are not required.

`--base-only` checks the wheel and sdist hello world without extras. It is useful for the ARM64 lane and early diagnosis, but **does not establish full release readiness**. `--public` confirms the candidate's exact public PyPI file hashes and installs its public version.

Evidence includes `release.json`, `SHA256SUMS`, pip installation reports, command logs, module origins and actual example results. Failed checks retain a failed disposition. Keep this evidence separate from uploadable distributions.

## Configure publishing — separate authorization required

For this repository:

- Create the existing GitHub environment named **`pypi`** with required human reviewers.
- Configure a custom deployment policy allowing **only the `main` branch**. A missing environment, missing reviewers or broader policy fails preflight.
- Configure a PyPI Trusted Publisher for the exact GitHub owner/repository, workflow filename **`build-and-release-package.yml`**, and environment **`pypi`**.
- For a new PyPI project, a pending publisher can create the project on first publication; it does **not** reserve the name.
- No long-lived PyPI token or broad GitHub App token is a fallback for missing setup.

See [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/adding-a-publisher/) and [first-publication setup](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

## Build, approve, publish, confirm

`.github/workflows/build-and-release-package.yml` runs candidate checks for PRs targeting `main` or `develop`. Manual runs default to `publish=false`.

After separately authorized release preparation:

1. Dispatch **Build, Verify, and Publish Package** on `main` with `publish=true`.
2. The pinned source commit builds one wheel and sdist. Linux x86-64 checks the wheel, sdist and advertised extras. Linux ARM64 checks the same candidate's wheel/sdist hello world.
3. Inspect the source/version, artifacts, hashes and verification evidence before approving the protected `pypi` environment.
4. The publisher downloads the exact same-run artifact IDs, rechecks the approved set/hashes and uploads with short-lived OIDC authority. It never rebuilds, rewrites the version or uses `skip-existing`.
5. Public confirmation compares PyPI's file set/hashes with the candidate and runs the public-index hello world on both platforms. Upload success alone is not confirmation.

The old automatic GitHub release/SBOM/wheels-repository upload path is replaced, not retained as a second unverified release path. Historical releases remain untouched. This workflow does not create release branches or publish merely because a PR merged.

## Failures and recovery

- Missing public dependencies block parent verification. Local sibling wheels may help diagnose compatibility but are not final public-resolution evidence.
- Changed source, versions or hashes require a new candidate verification and approval.
- Version collisions, partial uploads and unexpected hashes stop for explicit reconciliation. Check what is already public before selecting a new version or another recovery action.
- Never weaken extraction safety to accept repository-local symlinks in an sdist; fix its build contents.
- Do not equate a GitHub asset, source-tree test, base-only result or successful import with full release readiness.
- Update README/site publication wording only after public confirmation succeeds. An unpublished candidate remains labelled unpublished.
