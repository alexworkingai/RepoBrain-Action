from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_security_contributing_and_codeowners_exist() -> None:
    assert (ROOT / "SECURITY.md").exists()
    assert (ROOT / "CONTRIBUTING.md").exists()
    assert (ROOT / ".github/CODEOWNERS").exists()


def test_supply_chain_configs_and_workflows_exist() -> None:
    assert (ROOT / ".github/dependabot.yml").exists()
    assert (ROOT / ".github/workflows/dependency-review.yml").exists()
    assert (ROOT / ".github/workflows/codeql.yml").exists()
    assert (ROOT / ".github/workflows/sbom.yml").exists()
    assert (ROOT / ".github/workflows/provenance.yml").exists()


def test_supply_chain_baseline_doc_covers_required_controls() -> None:
    text = _read("docs/security/SUPPLY_CHAIN_SECURITY_BASELINE.md").lower()

    assert "security.md" in text
    assert "codeowners" in text
    assert "dependabot" in text
    assert "dependency review" in text
    assert "codeql" in text
    assert "sbom" in text
    assert "provenance" in text or "attestation" in text
    assert "branch / ruleset governance" in text or "branch/ruleset governance" in text
    assert "release integrity" in text
    assert "before public switch" in text


def test_supply_chain_workflows_preserve_safe_triggers_and_permissions() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            ".github/workflows/dependency-review.yml",
            ".github/workflows/codeql.yml",
            ".github/workflows/sbom.yml",
            ".github/workflows/provenance.yml",
        )
    ).lower()

    assert "pull_request_target" not in combined
    assert "dependency-review-action@v4" in combined
    assert "github/codeql-action/init@v3" in combined
    assert "actions/attest-build-provenance@v3" in combined
