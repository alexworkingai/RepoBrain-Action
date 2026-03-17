from __future__ import annotations

from repobrain.signal_calibrator import calibrate_security_signal


def test_docs_security_wording_downgrades_to_informational() -> None:
    calibrated = calibrate_security_signal(
        message="Possible secret leakage in patch",
        severity="high",
        evidence_paths=["docs/security.md"],
    )

    assert calibrated.bucket == "informational"
    assert calibrated.severity == "low"
    assert calibrated.reason_code == "DOCS_SECURITY_WORDING_DOWNGRADED"


def test_auth_path_security_signal_stays_elevated() -> None:
    calibrated = calibrate_security_signal(
        message="Possible secret leakage in patch",
        severity="low",
        evidence_paths=["repobrain/security_policy.py"],
    )

    assert calibrated.bucket == "confirmed"
    assert calibrated.severity in {"medium", "high"}


def test_strong_secret_pattern_is_preserved() -> None:
    calibrated = calibrate_security_signal(
        message="Detected ghp_abcdefghijklmnopqrstuvwxyz012345 token",
        severity="medium",
        evidence_paths=["repobrain/github_flow.py"],
    )

    assert calibrated.bucket == "confirmed"
    assert calibrated.reason_code == "STRONG_SECRET_SIGNAL"
