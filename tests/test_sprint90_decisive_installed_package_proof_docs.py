from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _public_readiness_next_step, _read_public_readiness_status


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint90_architecture_doc_exists() -> None:
    assert (ROOT / "docs/architecture/SPRINT_90_DECISIVE_INSTALLED_PACKAGE_PROOF.md").exists()


def test_sprint90_docs_record_decisive_proof_pass() -> None:
    architecture = _read("docs/architecture/SPRINT_90_DECISIVE_INSTALLED_PACKAGE_PROOF.md").lower()
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md").lower()
    proof = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    combined = "\n".join((architecture, readiness, proof))
    assert "topocore_v6_artifact_token" in combined
    assert "public_switch_ready_after_runtime_proof" in combined
    assert "artifact downloaded: yes" in combined or "artifact downloaded" in combined
    assert "private_checkout avoided" in combined
    assert "source checkout avoided" in combined


def test_sprint90_public_readiness_parser_is_now_post_switch_ready() -> None:
    status = _read_public_readiness_status(ROOT)

    assert status == "SPRINT_92F_IMPLEMENTATION_MERGED_LIVE_RETEST_PENDING"
    next_step = _public_readiness_next_step(status).lower()
    assert "partner pilot" in next_step or "partner onboarding" in next_step
