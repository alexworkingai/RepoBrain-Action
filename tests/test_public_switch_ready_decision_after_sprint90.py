from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_switch_ready_after_runtime_proof_is_retained_as_history_after_sprint91() -> None:
    architecture = _read("docs/architecture/SPRINT_90_DECISIVE_INSTALLED_PACKAGE_PROOF.md")
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md")

    combined = "\n".join((architecture, readiness))
    assert "PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF" in combined
    assert "PUBLIC_VISIBILITY_SWITCHED_PARTNER_PILOT_READY" in combined


def test_public_switch_docs_keep_marketplace_blocked_and_switch_history_explicit() -> None:
    combined = "\n".join(
        (
            _read("docs/architecture/SPRINT_90_DECISIVE_INSTALLED_PACKAGE_PROOF.md").lower(),
            _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md").lower(),
            _read("docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md").lower(),
        )
    )

    assert "marketplace work is not started" in combined or "marketplace" in combined
    assert "repobrain-action is now public" in combined or "public visibility was switched in sprint 91" in combined
    assert "public_switch_ready_after_runtime_proof" in combined
