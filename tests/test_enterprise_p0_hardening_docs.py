from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_enterprise_hardening_report_and_sprint_note_exist() -> None:
    assert (ROOT / "docs/release/ENTERPRISE_P0_HARDENING_REPORT.md").exists()
    assert (ROOT / "docs/architecture/SPRINT_86_ENTERPRISE_P0_HARDENING.md").exists()


def test_enterprise_hardening_docs_preserve_pre_public_truth() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "docs/release/ENTERPRISE_P0_HARDENING_REPORT.md",
            "docs/architecture/SPRINT_86_ENTERPRISE_P0_HARDENING.md",
            "docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md",
        )
    ).lower()

    assert "does not make the repo public" in combined or "does not make the repository public" in combined
    assert "marketplace" in combined
    assert "topocore" in combined
    assert "no mutation" in combined
    assert "public_switch_ready_after_p0_hardening" in combined or "public_blocked_by_" in combined


def test_enterprise_hardening_docs_do_not_claim_marketplace_or_public_switch() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "docs/release/ENTERPRISE_P0_HARDENING_REPORT.md",
            "docs/architecture/SPRINT_86_ENTERPRISE_P0_HARDENING.md",
            "docs/release/PUBLIC_READINESS_ASSESSMENT.md",
        )
    ).lower()

    assert "marketplace published: yes" not in combined
    assert "public switch executed" not in combined
    assert "microsoft partnership claim" in combined
