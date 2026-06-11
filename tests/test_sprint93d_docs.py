from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8").lower()


def test_quickstart_and_example_reflect_93d_end_to_end_path_without_overclaim() -> None:
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    workflow = _read("docs/examples/repobrain_partner_self_service_workflow.yml")

    assert "sprint 93d now wires the end-to-end action-to-hosted flow" in quickstart
    assert "sprint 93e is still required" in quickstart
    assert "no repobrain owner-generated secret" in quickstart or "no repobrain owner token" in quickstart
    assert "no manual partner registration" in quickstart
    assert "do not install or download topocore" in quickstart
    assert "api_url: https://repobrain.example.invalid" in workflow
    assert 'self_service_mode: "true"' in workflow
    assert "id-token: write" in workflow
    assert "topocore_v6_repo_token" not in workflow
    assert "topocore_v6_artifact_token" not in workflow


def test_readme_and_architecture_note_reflect_93d_without_full_launch_claim() -> None:
    readme = _read("README.md")
    architecture = _read("docs/architecture/SPRINT_93D_END_TO_END_PARTNER_SELF_SERVICE_WORKFLOW.md")

    assert "sprint 93d end-to-end self-service truth" in readme
    assert "supported `ask`, `audit`, and `score` commands" in readme
    assert "final trusted partner hardening and validation remain deferred to sprint 93e" in readme
    assert "supported self-service commands are `ask`, `audit`, and `score`" in architecture
    assert "self_service_mode: \"true\"" in architecture
    assert "does not claim" in architecture
    assert "marketplace readiness" in architecture
