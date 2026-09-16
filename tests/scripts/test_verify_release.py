"""Release proof must reject hidden dependency sources and inconsistent artifacts."""

from __future__ import annotations

import json

import pytest

from scripts.verify_release import check_install_report, check_public_files


def test_install_report_rejects_a_local_dependency_after_public_resolution(tmp_path):
    candidate = tmp_path / "mountainash-0.2.0-py3-none-any.whl"
    dependency = {
        "metadata": {"name": "mountainash-files"},
        "download_info": {"url": "https://files.pythonhosted.org/packages/mountainash_files.whl"},
    }
    result = {
        "install": [
            {"metadata": {"name": "mountainash"}, "download_info": {"url": candidate.as_uri()}},
            dependency,
        ]
    }
    report = tmp_path / "install.json"
    report.write_text(json.dumps(result))
    check_install_report(report, candidate)

    dependency["download_info"]["url"] = (tmp_path / "mountainash_files.whl").as_uri()
    report.write_text(json.dumps(result))
    with pytest.raises(ValueError, match="mountainash-files"):
        check_install_report(report, candidate)


def test_public_confirmation_rejects_partial_release():
    expected = {"mountainash-0.2.0.whl": "a" * 64, "mountainash-0.2.0.tar.gz": "b" * 64}
    published = {
        "urls": [
            {"filename": "mountainash-0.2.0.whl", "digests": {"sha256": "a" * 64}},
            {"filename": "mountainash-0.2.0.tar.gz", "digests": {"sha256": "b" * 64}},
        ]
    }
    check_public_files(published, expected)
    published["urls"].pop()
    with pytest.raises(ValueError, match="file set"):
        check_public_files(published, expected)


def test_public_confirmation_rejects_changed_artifact():
    expected = {"mountainash-0.2.0.whl": "a" * 64}
    published = {"urls": [{"filename": "mountainash-0.2.0.whl", "digests": {"sha256": "a" * 64}}]}
    check_public_files(published, expected)
    published["urls"][0]["digests"]["sha256"] = "b" * 64
    with pytest.raises(ValueError, match="hash"):
        check_public_files(published, expected)


def test_malformed_artifact_set_retains_failed_disposition(tmp_path):
    from scripts.verify_release import verify

    distribution = tmp_path / "dist"
    distribution.mkdir()
    evidence = tmp_path / "evidence"
    with pytest.raises(ValueError):
        verify(distribution, evidence, base_only=True)
    assert json.loads((evidence / "release.json").read_text())["status"] == "failed"


def test_candidate_with_unsupported_python_claim_is_rejected(tmp_path):
    import zipfile

    from scripts.verify_release import _metadata

    wheel = tmp_path / "mountainash-0.2.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "mountainash-0.2.0.dist-info/METADATA",
            "Metadata-Version: 2.3\nName: mountainash\nVersion: 0.2.0\nRequires-Python: >=3.10\n",
        )
    with pytest.raises(ValueError, match="Python"):
        _metadata(wheel)
