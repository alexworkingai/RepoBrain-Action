from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _active_release_and_user_docs() -> str:
    paths = [
        "README.md",
        "LICENSE",
        "docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md",
        "docs/commands/REPOBRAIN_COMMANDS.md",
        "docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md",
        "docs/release/LICENSE_MODEL.md",
        "docs/release/SERVICE_AND_COMMERCIAL_MODEL.md",
        "docs/release/PRIVATE_TOPOCORE_DISTRIBUTION_STRATEGY.md",
        "docs/release/MICROSOFT_GITHUB_STRATEGIC_POSITIONING.md",
        "docs/release/REPOBRAIN_V6_SCORING_MODEL.md",
        "docs/release/SUPPORT_POLICY.md",
        "docs/release/VERSIONING_AND_PINNING_STRATEGY.md",
        "docs/release/PUBLIC_READINESS_ASSESSMENT.md",
        "docs/release/MARKETPLACE_READINESS_ASSESSMENT.md",
        "docs/release/RELEASE_CANDIDATE_CHECKLIST.md",
        "docs/release/RELEASE_NOTES_RC1.md",
        "docs/architecture/SPRINT_77_PUBLIC_SCRUB_LICENSE_TOPOCORE_SECURITY_POSITIONING.md",
        "docs/security/TOPOCORE_V6_HIGH_SECURITY_POLICY.md",
        "docs/examples/repobrain_external_pilot_workflow.yml",
    ]
    return "\n".join(_read(path) for path in paths)


def _all_tracked_docs_text() -> str:
    parts = [(ROOT / "README.md").read_text(encoding="utf-8"), (ROOT / "LICENSE").read_text(encoding="utf-8")]
    parts.extend(path.read_text(encoding="utf-8") for path in (ROOT / "docs").rglob("*") if path.is_file())
    return "\n".join(parts)


def test_sprint_77_artifacts_exist() -> None:
    assert (ROOT / "docs/architecture/SPRINT_77_PUBLIC_SCRUB_LICENSE_TOPOCORE_SECURITY_POSITIONING.md").exists()
    assert (ROOT / "LICENSE").exists()
    assert (ROOT / "docs/release/LICENSE_MODEL.md").exists()
    assert (ROOT / "docs/release/SERVICE_AND_COMMERCIAL_MODEL.md").exists()
    assert (ROOT / "docs/security/TOPOCORE_V6_HIGH_SECURITY_POLICY.md").exists()
    assert (ROOT / "docs/release/PRIVATE_TOPOCORE_DISTRIBUTION_STRATEGY.md").exists()
    assert (ROOT / "docs/release/MICROSOFT_GITHUB_STRATEGIC_POSITIONING.md").exists()
    assert (ROOT / "docs/release/REPOBRAIN_V6_SCORING_MODEL.md").exists()
    assert (ROOT / "docs/release/SUPPORT_POLICY.md").exists()
    assert (ROOT / "docs/release/VERSIONING_AND_PINNING_STRATEGY.md").exists()


def test_license_contains_required_source_available_byollm_terms() -> None:
    text = _read("LICENSE")

    assert "RepoBrain Action Source-Available BYO-LLM License v0.2" in text
    assert "GitHub Models billed to your own GitHub account" in text
    assert "your own paid LLM" in text
    assert "TopoCore v6" in text
    assert "does not grant any TopoCore v6 source-code rights" in text
    assert "hosted service" in text
    assert "SaaS" in text
    assert "WITHOUT WARRANTY" in text


def test_active_release_and_user_docs_are_scrubbed_of_local_paths_and_secret_value_patterns() -> None:
    combined = _all_tracked_docs_text()

    assert r"D:\ARIADNA_Minsk" not in combined
    assert r"C:\Users" not in combined
    assert "/mnt/data" not in combined
    assert "ghp_" not in combined
    assert "github_pat_" not in combined
    assert "BEGIN PRIVATE KEY" not in combined


def test_active_release_and_user_docs_preserve_current_product_truth() -> None:
    combined = _active_release_and_user_docs().lower()

    assert "repobrain-community/.github/workflows" not in combined
    assert "repobrain-community/templates/repobrain.yml" not in combined
    assert "patch/autofix is enabled" not in combined
    assert "is safe to merge" not in combined
    assert "security approved" not in combined
    assert "topocore v6 remains private" in combined
    assert "marketplace" in combined


def test_release_docs_record_no_visibility_switch_and_no_marketplace_publication() -> None:
    combined = "\n".join(
        _read(path).lower()
        for path in (
            "docs/release/PUBLIC_READINESS_ASSESSMENT.md",
            "docs/release/MARKETPLACE_READINESS_ASSESSMENT.md",
            "docs/architecture/SPRINT_77_PUBLIC_SCRUB_LICENSE_TOPOCORE_SECURITY_POSITIONING.md",
        )
    )

    assert "does not publish repobrain-action" in combined or "visibility" in combined
    assert "does not publish to github marketplace" in combined or "does not publish to marketplace" in combined
    assert "public_blocked_by_distribution_strategy" in combined
    assert "marketplace_not_ready" in combined


def test_scoring_model_and_command_roadmap_are_explicit() -> None:
    text = _read("docs/release/REPOBRAIN_V6_SCORING_MODEL.md")

    for line in (
        "Architecture and modularity: 15",
        "Code quality and maintainability: 12",
        "Testing and validation: 12",
        "Security posture: 12",
        "CI/CD and automation: 10",
        "Dependency hygiene: 8",
        "Documentation and onboarding: 8",
        "Release and operations readiness: 8",
        "GitHub governance: 8",
        "AI-readiness / repository intelligence: 7",
        "Total: 100",
    ):
        assert line in text

    for command in (
        "/repobrain audit",
        "/repobrain score",
        "/repobrain doctor",
        "/repobrain status",
        "/repobrain fix",
    ):
        assert command in text

    assert "use `/repobrain fix`" in text


def test_external_example_remains_read_mostly() -> None:
    text = _read("docs/examples/repobrain_external_pilot_workflow.yml")

    assert "pull_request_target" not in text
    assert "contents: write" not in text
    assert "checks: write" not in text
    assert "pull-requests: write" not in text
