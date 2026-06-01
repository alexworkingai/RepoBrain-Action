from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint91_architecture_doc_exists() -> None:
    assert (ROOT / "docs/architecture/SPRINT_91_PUBLIC_SWITCH_PARTNER_PILOT.md").exists()


def test_sprint91_pre_switch_docs_record_owner_approval_but_not_executed_switch() -> None:
    architecture = _read("docs/architecture/SPRINT_91_PUBLIC_SWITCH_PARTNER_PILOT.md").lower()
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md").lower()
    checklist = _read("docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md").lower()

    combined = "\n".join((architecture, readiness, checklist))
    assert "owner approval" in combined
    assert "public_switch_ready_after_runtime_proof" in combined
    assert "public_visibility_switched_partner_pilot_ready" in combined
    assert "public visibility is not switched" in checklist or "switch still pending execution" in architecture


def test_sprint91_docs_keep_topocore_private_and_marketplace_not_started() -> None:
    combined = "\n".join(
        (
            _read("docs/architecture/SPRINT_91_PUBLIC_SWITCH_PARTNER_PILOT.md").lower(),
            _read("docs/release/PARTNER_TESTING_READINESS.md").lower(),
            _read("README.md").lower(),
        )
    )
    assert "topocore" in combined
    assert "private" in combined
    assert "marketplace" in combined
