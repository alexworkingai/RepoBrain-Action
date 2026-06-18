from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8").lower()


def test_sprint94e_docs_exist() -> None:
    assert (ROOT / "docs/architecture/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION.md").exists()
    assert (ROOT / "docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_RUNBOOK.md").exists()
    assert (ROOT / "docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_EVIDENCE.md").exists()
    assert (ROOT / "docs/examples/repobrain_trusted_partner_94e_workflow.yml").exists()


def test_sprint94e_docs_cover_both_trusted_repositories_and_all_commands() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "docs/architecture/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION.md",
            "docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_RUNBOOK.md",
            "docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_EVIDENCE.md",
        )
    )
    assert "alexworkingai/elen-mcp-v.2.2.0" in combined
    assert "alexworkingai/repobrain-community" in combined
    assert "/repobrain score" in combined
    assert "/repobrain audit" in combined
    assert "/repobrain audit --profile premium" in combined


def test_sprint94e_docs_keep_validation_truth_and_workflow_default_branch_rule() -> None:
    architecture = _read("docs/architecture/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION.md")
    runbook = _read("docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_RUNBOOK.md")
    example = _read("docs/examples/repobrain_trusted_partner_94e_workflow.yml")

    assert "trusted partner beta requires live validation evidence" in architecture
    assert "queued acknowledgement alone" in architecture
    assert "stub topocore alone" in architecture
    assert "workflow must be active on the repository default branch" in runbook
    assert "workflow must be present on the target repository default branch" in example
    assert "sprint 94f - public developer beta without marketplace" in architecture


def test_sprint94e_docs_keep_hosted_api_marketplace_and_secret_boundaries_explicit() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "README.md",
            "docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md",
            "docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md",
            "docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_RUNBOOK.md",
            "docs/examples/repobrain_trusted_partner_94e_workflow.yml",
        )
    )
    assert "hosted_api remains experimental/future" in combined or "hosted_api" in combined
    assert "no repobrain_hosted_api_url required" in combined or "do not require `repobrain_hosted_api_url`" in combined
    assert "marketplace is not current route" in combined or "marketplace is not the immediate route" in combined
    assert "no domain" in combined or "no domain/external hosting required" in combined or "do not require a domain" in combined
    assert "no partner secrets" in combined
    assert "no topocore token in partner repo" in combined or "partner repos must not store topocore tokens" in combined
    assert "no github app private key in partner repo" in combined or "partner repos must not store the github app private key" in combined


def test_sprint94e_docs_require_real_topocore_for_trusted_ready_and_do_not_overclaim() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "docs/architecture/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION.md",
            "docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_RUNBOOK.md",
            "docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_EVIDENCE.md",
        )
    )
    assert "real private topocore" in combined
    assert "real private topocore path evidence" in combined
    assert "stub mode is not enough" in combined
    assert "queued acknowledgement alone is not a full pass" in combined
    assert "public_developer_beta_ready" not in _read("docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_EVIDENCE.md")
    assert "marketplace_ready" not in _read("docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_EVIDENCE.md")
    assert "production_approved" not in _read("docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_EVIDENCE.md")
    assert "security_certified" not in _read("docs/release/SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_EVIDENCE.md")
