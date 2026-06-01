from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_readiness_docs_exist() -> None:
    assert (ROOT / "docs/release/RELEASE_CANDIDATE_CHECKLIST.md").exists()
    assert (ROOT / "docs/release/PUBLIC_READINESS_ASSESSMENT.md").exists()
    assert (ROOT / "docs/release/MARKETPLACE_READINESS_ASSESSMENT.md").exists()
    assert (ROOT / "docs/release/RELEASE_NOTES_RC1.md").exists()
    assert (ROOT / "docs/architecture/SPRINT_76_RELEASE_CANDIDATE_READINESS.md").exists()
    assert (ROOT / "docs/architecture/SPRINT_77_PUBLIC_SCRUB_LICENSE_TOPOCORE_SECURITY_POSITIONING.md").exists()


def test_release_readiness_docs_preserve_private_topocore_and_no_publication_claims() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "docs/release/RELEASE_CANDIDATE_CHECKLIST.md",
            "docs/release/PUBLIC_READINESS_ASSESSMENT.md",
            "docs/release/MARKETPLACE_READINESS_ASSESSMENT.md",
            "docs/release/RELEASE_NOTES_RC1.md",
            "docs/architecture/SPRINT_76_RELEASE_CANDIDATE_READINESS.md",
            "docs/architecture/SPRINT_77_PUBLIC_SCRUB_LICENSE_TOPOCORE_SECURITY_POSITIONING.md",
        )
    ).lower()

    assert "topocore v6 remains private" in combined
    assert "repo is already public" not in combined
    assert "does not publish to github marketplace" in combined or "marketplace not started" in combined
    assert "no v5" in combined
    assert "no repobrain-community" in combined
    assert "no patch/autofix" in combined
    assert "public_ready_pending_owner_approval" in combined
    assert "marketplace_not_ready" in combined


def test_release_readiness_docs_cover_supported_unsupported_commands_and_limitations() -> None:
    checklist = _read("docs/release/RELEASE_CANDIDATE_CHECKLIST.md")
    notes = _read("docs/release/RELEASE_NOTES_RC1.md")
    sprint = _read("docs/architecture/SPRINT_77_PUBLIC_SCRUB_LICENSE_TOPOCORE_SECURITY_POSITIONING.md")

    for command in (
        "/repobrain audit",
        "/repobrain help",
        "/repobrain ask <query>",
        "/repobrain locate <query>",
        "/repobrain explain <query>",
        "/repobrain review",
        "/repobrain verify",
        "/repobrain fix",
    ):
        assert command in checklist or command in notes

    for command in (
        "/repobrain status",
        "/repobrain doctor",
    ):
        assert command in notes or command in sprint
    assert "/repobrain fix-lite" not in checklist
    assert "/repobrain fix-lite" not in notes

    assert "Known Limitations" in checklist
    assert "Decision" in _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md")
    assert "Decision" in _read("docs/release/MARKETPLACE_READINESS_ASSESSMENT.md")
    assert "/repobrain audit" in sprint
    assert "/repobrain score" in sprint


def test_active_docs_do_not_reintroduce_old_or_unsafe_release_truth() -> None:
    active = "\n".join(
        _read(path)
        for path in (
            "README.md",
            "docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md",
            "docs/commands/REPOBRAIN_COMMANDS.md",
            "docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md",
            "docs/release/RELEASE_CANDIDATE_CHECKLIST.md",
            "docs/release/PUBLIC_READINESS_ASSESSMENT.md",
            "docs/release/MARKETPLACE_READINESS_ASSESSMENT.md",
            "docs/release/RELEASE_NOTES_RC1.md",
        )
    ).lower()

    assert "use v5" not in active
    assert "repobrain-community/.github/workflows" not in active
    assert "repobrain-community/templates/repobrain.yml" not in active
    assert "safe-to-merge claim" in active
    assert "security approval" in active
    assert "contents: write" in active
    assert "not required for the current external product path" in active
    assert "checks: write" in active
    assert "pull-requests: write" in active
    assert "dependency review" in active
    assert "codeql" in active
    assert "sbom" in active
    assert "codeowners" in active
    assert "installed private package" in active
