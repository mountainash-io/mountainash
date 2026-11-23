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


def test_base_install_allows_required_siblings_and_rejects_optional_ones():
    from scripts.verify_release import check_base_siblings

    requires = [
        "polars",
        "mountainash-transport",
        'mountainash-files; extra == "files"',
    ]
    check_base_siblings({"mountainash", "mountainash-transport", "polars"}, requires)
    with pytest.raises(ValueError, match="mountainash-files"):
        check_base_siblings({"mountainash", "mountainash-transport", "mountainash-files"}, requires)
    with pytest.raises(ValueError, match="mountainash-settings"):
        check_base_siblings({"mountainash", "mountainash-transport", "mountainash-settings"}, requires)


def _report(tmp_path, *urls):
    report = tmp_path / "install.json"
    report.write_text(
        json.dumps(
            {"install": [{"metadata": {"name": name}, "download_info": {"url": url}} for name, url in urls]}
        )
    )
    return report


def test_install_report_allows_only_the_candidate_and_supplied_sibling_wheels(tmp_path):
    candidate = tmp_path / "mountainash-0.2.0-py3-none-any.whl"
    sibling = tmp_path / "siblings" / "mountainash_transport-0.1.0-py3-none-any.whl"
    other = tmp_path / "siblings" / "mountainash_files-0.1.0-py3-none-any.whl"
    report = _report(
        tmp_path,
        ("mountainash", candidate.as_uri()),
        ("mountainash-transport", sibling.as_uri()),
        ("polars", "https://files.pythonhosted.org/packages/polars.whl"),
    )
    assert check_install_report(report, candidate, (sibling, other)) == {
        "mountainash",
        "mountainash-transport",
        "polars",
    }
    with pytest.raises(ValueError, match="mountainash-transport"):
        check_install_report(report, candidate)
    with pytest.raises(ValueError, match="mountainash-transport"):
        check_install_report(report, candidate, (other,))


def test_dependency_wheels_are_offered_to_every_candidate_install(tmp_path, monkeypatch):
    from scripts import verify_release

    siblings = tmp_path / "siblings"
    siblings.mkdir()
    wheel = siblings / "mountainash_transport-0.1.0-py3-none-any.whl"
    wheel.write_bytes(b"")
    commands = []
    monkeypatch.setattr(verify_release.venv.EnvBuilder, "create", lambda self, target: None)

    def fake_run(command, cwd, env, log):
        commands.append(command)
        log.write_text("")

    monkeypatch.setattr(verify_release, "_run", fake_run)
    monkeypatch.setattr(verify_release, "check_install_report", lambda *args: set())
    verify_release._install(
        "mountainash.whl", None, "wheel", tmp_path, tmp_path, {}, dependency_wheels=verify_release._dependency_wheels(siblings)
    )
    install = commands[0]
    assert install[install.index("--find-links") + 1] == str(siblings)
    assert install[install.index("--index-url") + 1] == "https://pypi.org/simple"


def test_dependency_wheels_are_rejected_with_public_verification(tmp_path):
    from scripts.verify_release import verify

    with pytest.raises(ValueError, match="dependency-wheels"):
        verify(tmp_path / "dist", tmp_path / "evidence", public=True, dependency_wheels=tmp_path)
    assert not (tmp_path / "evidence").exists()


def test_empty_dependency_wheel_directory_is_rejected(tmp_path):
    from scripts.verify_release import verify

    distribution = tmp_path / "dist"
    distribution.mkdir()
    with pytest.raises(ValueError, match="no dependency wheels"):
        verify(distribution, tmp_path / "evidence", base_only=True, dependency_wheels=tmp_path)
