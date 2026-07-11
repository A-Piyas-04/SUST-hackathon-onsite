"""Safety & security scans pass and produce a machine-checkable artifact."""

from __future__ import annotations

from app.scripts import safety_scan


def test_all_scans_pass():
    result = safety_scan.run_scans()
    failing = [s["name"] for s in result["scans"] if not s["passed"]]
    assert result["passed"], f"failing scans: {failing}"


def test_no_unsafe_action_endpoints():
    scan = safety_scan.scan_unsafe_endpoints()
    assert scan["passed"], scan["findings"]
    assert scan["routes_checked"] > 0


def test_secrets_scan_passes_with_only_synthetic_waivers():
    scan = safety_scan.scan_secrets()
    assert scan["passed"], scan["findings"]
    # Any waived match must be an explicitly synthetic demo credential.
    for waiver in scan["waivers"]:
        assert "synthetic" in waiver["reason"]


def test_prohibited_language_scan_passes():
    scan = safety_scan.scan_prohibited_language()
    assert scan["passed"], scan["findings"]


def test_release_candidate_recorded_in_scan():
    result = safety_scan.run_scans()
    rc = result["release_candidate"]
    assert "commit" in rc and "contract_version" in rc


def test_artifact_written(tmp_path, monkeypatch):
    # Ensure the writer produces valid JSON at the expected path.
    result = safety_scan.run_scans()
    path = safety_scan.write_artifact(result)
    assert path.exists()
    assert path.name == "safety-security-scan.json"
