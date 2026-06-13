from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8").lower()


def test_quickstart_and_example_reclassify_hosted_path_after_94a() -> None:
    quickstart = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")
    workflow = _read("docs/examples/repobrain_partner_self_service_workflow.yml")

    assert "hosted self-service remains available only as an experimental and future external-runtime mode" in quickstart
    assert "trusted beta partners must not be told to create fake `repobrain_hosted_api_url` values" in quickstart
    assert "trusted partners should wait for github app and control-worker beta instructions from sprints 94b-94e" in quickstart
    assert "api_url: https://repobrain.example.invalid" in workflow
    assert "do not use this hosted path as the default trusted beta setup" in workflow
    assert 'self_service_mode: "true"' in workflow
    assert "transport_mode: github_app_queue" in workflow


def test_readme_and_93d_architecture_note_reflect_correction_without_launch_claim() -> None:
    readme = _read("README.md")
    architecture = _read("docs/architecture/SPRINT_93D_END_TO_END_PARTNER_SELF_SERVICE_WORKFLOW.md")
    alias = _read("docs/architecture/SPRINT_93D_END_TO_END_SELF_SERVICE_WORKFLOW.md")

    assert "`hosted_api` mode requires a real external runtime" in readme
    assert "the next implementation stage is a github-native beta control plane" in readme
    assert "github marketplace is not the immediate route" in readme
    assert "correction notice" in architecture
    assert "`hosted_api` path was reclassified as experimental and future external-runtime mode" in architecture
    assert "the next implementation stages move to github app identity, github-native queueing, and a private control worker" in architecture
    assert "default trusted beta path is now the github-native control plane" in alias
