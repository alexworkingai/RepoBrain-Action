from __future__ import annotations

from repobrain.installed_package_preflight import (
    classify_installed_package_preflight_failure,
    sanitize_installed_package_preflight_text,
)


def test_classifies_package_auth_failed_and_sanitizes_tokens_and_paths() -> None:
    raw = (
        "403 Resource not accessible by integration for Bearer ghp_secret123 "
        "while downloading from C:\\Users\\tester\\topocore\\dist\\wheel.whl"
    )

    sanitized = sanitize_installed_package_preflight_text(raw)
    category = classify_installed_package_preflight_failure(raw)

    assert category == "PACKAGE_AUTH_FAILED"
    assert "ghp_secret123" not in sanitized
    assert "C:\\Users\\tester" not in sanitized
    assert "[redacted-token]" in sanitized
    assert "[redacted-path]" in sanitized


def test_classifies_digest_mismatch() -> None:
    category = classify_installed_package_preflight_failure(
        "sha256 mismatch: downloaded wheel does not match expected digest"
    )
    assert category == "PACKAGE_DIGEST_MISMATCH"


def test_classifies_package_install_failed() -> None:
    category = classify_installed_package_preflight_failure(
        "pip install failed with subprocess-exited-with-error"
    )
    assert category == "PACKAGE_INSTALL_FAILED"


def test_classifies_package_import_failed() -> None:
    category = classify_installed_package_preflight_failure(
        "ImportError: No module named topocore_v6 after install"
    )
    assert category == "PACKAGE_IMPORT_FAILED"


def test_classifies_capability_missing() -> None:
    category = classify_installed_package_preflight_failure(
        "run_audit_score_v1 is unavailable in the installed runtime facade"
    )
    assert category == "CAPABILITY_MISSING"
