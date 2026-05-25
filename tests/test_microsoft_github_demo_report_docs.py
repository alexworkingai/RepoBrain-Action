from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_demo_and_benchmark_reports_exist() -> None:
    assert (ROOT / "docs/release/MICROSOFT_GITHUB_DEMO_REPORT.md").exists()
    assert (ROOT / "docs/release/AUDIT_BENCHMARK_REPORT.md").exists()
    assert (ROOT / "docs/architecture/SPRINT_80_AUDIT_BENCHMARK_DEMO_REPORT.md").exists()


def test_demo_report_covers_positioning_and_proof_without_unsafe_claims() -> None:
    text = _read("docs/release/MICROSOFT_GITHUB_DEMO_REPORT.md")
    lowered = text.lower()

    assert "github-native repository intelligence and quality scoring platform" in lowered
    assert "100-point score" in lowered
    assert "not merely an ai pr reviewer" in lowered or "not just pr review" in lowered
    assert "not an llm reseller" in lowered
    assert "byo-llm" in lowered or "user-paid llm" in lowered
    assert "github actions-native" in lowered
    assert "private topocore v6" in lowered
    assert "no patch/autofix" in lowered
    assert "does not claim microsoft approval" in lowered
    assert "official partnership" in lowered
    assert "no security approval claim" in lowered or "security approval" in lowered
    assert "safe-to-merge" not in lowered


def test_release_docs_are_updated_for_sprint_80_story() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "docs/release/REPOBRAIN_V6_SCORING_MODEL.md",
            "docs/release/MICROSOFT_GITHUB_STRATEGIC_POSITIONING.md",
            "docs/release/RELEASE_NOTES_RC1.md",
            "docs/release/RELEASE_CANDIDATE_CHECKLIST.md",
            "docs/architecture/SPRINT_80_AUDIT_BENCHMARK_DEMO_REPORT.md",
        )
    ).lower()

    assert "benchmark" in combined
    assert "microsoft/github" in combined or "microsoft and github" in combined
    assert "/repobrain audit" in combined
    assert "score remains roadmap-only" in combined or "/repobrain score" in combined
    assert "no v5" in combined
    assert "no repobrain-community" in combined
