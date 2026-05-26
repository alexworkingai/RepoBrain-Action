from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_canonical_external_user_docs_exist() -> None:
    assert (ROOT / "docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md").exists()
    assert (ROOT / "docs/commands/REPOBRAIN_COMMANDS.md").exists()
    assert (ROOT / "docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md").exists()


def test_readme_links_to_install_commands_and_troubleshooting() -> None:
    text = _read("README.md")

    assert "docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md" in text
    assert "docs/commands/REPOBRAIN_COMMANDS.md" in text
    assert "docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md" in text


def test_install_doc_covers_product_model_and_expected_backend_truth() -> None:
    text = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")

    assert "RepoBrain-Action" in text
    assert "private TopoCore v6" in text
    assert "TOPOCORE_V6_REPO_TOKEN" in text
    assert "repobrain-community" in text
    assert "resolved backend: `v6`" in text
    assert "no patch/autofix" in text
    assert "installed private package" in text.lower()


def test_command_guide_documents_supported_and_unsupported_commands_honestly() -> None:
    text = _read("docs/commands/REPOBRAIN_COMMANDS.md")

    for command in (
        "/repobrain help",
        "/repobrain ask <query>",
        "/repobrain audit",
        "/repobrain locate <query>",
        "/repobrain explain <query>",
        "/repobrain review",
        "/repobrain verify",
        "/repobrain fix",
    ):
        assert command in text

    for command in (
        "/repobrain status",
        "/repobrain doctor",
        "/repobrain fix-lite",
    ):
        assert command in text

    assert "does not apply patches" in text
    assert "informational only" in text
    assert "safe to merge" in text
    assert "security approval" in text
    assert "100-point" in text.lower()


def test_troubleshooting_guide_covers_real_external_failures() -> None:
    text = _read("docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md")

    assert "Unable to resolve action" in text
    assert "allowed_actions=local_only" in text
    assert "TOPOCORE_V6_REPO_TOKEN" in text
    assert "Private checkout failed" in text
    assert "Verify returns `NOT_RUN`" in text
    assert "Fix returns `BLOCKED_BY_SAFETY`" in text
    assert "Review, Verify, Or Fix Unsupported In Issue Scope" in text
    assert "Workflow Permissions Too Strict" in text
    assert "Fork PR Restrictions" in text
    assert "Runtime mode confusion" in text


def test_active_external_docs_do_not_reintroduce_old_or_unsafe_truth() -> None:
    active_docs = "\n".join(
        _read(path)
        for path in (
            "README.md",
            "docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md",
            "docs/onboarding/EXTERNAL_REPOSITORY_PILOT_INSTALL.md",
            "docs/commands/REPOBRAIN_COMMANDS.md",
            "docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md",
            "docs/USER_GUIDE.md",
            "docs/EXTERNAL_MODE.md",
            "docs/OPERATOR_QUICKSTART.md",
        )
    ).lower()

    assert "repobrain-community/.github/workflows" not in active_docs
    assert "repobrain-community/templates/repobrain.yml" not in active_docs
    assert "is safe to merge" not in active_docs
    assert "security approved" not in active_docs
    assert "patch/autofix is enabled" not in active_docs
    assert "topocore backend for lab/runtime selection: auto or v6" not in active_docs
