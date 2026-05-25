from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_83_docs_exist() -> None:
    assert (ROOT / "docs/architecture/SPRINT_83_V6_AUDIT_UX_SCORE_SUMMARY.md").exists()


def test_command_and_support_docs_reflect_score_support() -> None:
    commands = _read("docs/commands/REPOBRAIN_COMMANDS.md")
    troubleshooting = _read("docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")
    scoring = _read("docs/release/REPOBRAIN_V6_SCORING_MODEL.md")

    assert "/repobrain score" in commands
    assert "compact" in commands.lower()
    assert "same audit engine" in commands.lower() or "same guarded audit engine" in commands.lower()
    assert "/repobrain score" in troubleshooting
    assert "/repobrain audit" in troubleshooting
    assert "/repobrain score" in install
    assert "compact" in install.lower()
    assert "/repobrain score" in scoring
    assert "v6-enriched" in scoring.lower()


def test_release_and_coverage_docs_reflect_sprint_83() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "README.md",
            "docs/release/AUDIT_BENCHMARK_REPORT.md",
            "docs/release/MICROSOFT_GITHUB_DEMO_REPORT.md",
            "docs/release/MICROSOFT_GITHUB_STRATEGIC_POSITIONING.md",
            "docs/release/RELEASE_NOTES_RC1.md",
            "docs/release/RELEASE_CANDIDATE_CHECKLIST.md",
            "docs/architecture/SPRINT_83_V6_AUDIT_UX_SCORE_SUMMARY.md",
            "docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md",
        )
    ).lower()

    assert "score" in combined
    assert "[redacted-path]" in combined or "repo-relative" in combined
    assert "no patch/autofix" in combined
    assert "no repobrain-community" in combined
    assert "tests/test_score_command.py" in combined
    assert "tests/test_safe_evidence_path_rendering.py" in combined
    assert "tests/test_v6_audit_ux_hardening.py" in combined
