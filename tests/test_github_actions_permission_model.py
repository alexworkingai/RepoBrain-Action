from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_permission_model_doc_exists() -> None:
    assert (ROOT / "docs/security/GITHUB_ACTIONS_PERMISSION_MODEL.md").exists()


def test_external_partner_workflow_stays_read_mostly() -> None:
    text = _read("docs/examples/repobrain_external_pilot_workflow.yml").lower()

    assert "contents: read" in text
    assert "checks: read" in text
    assert "pull-requests: read" in text
    assert "contents: write" not in text
    assert "checks: write" not in text
    assert "pull-requests: write" not in text
    assert "pull_request_target" not in text


def test_internal_permission_model_documents_remaining_write_permissions() -> None:
    workflow = _read(".github/workflows/repobrain_checks_publisher.yml").lower()
    doc = _read("docs/security/GITHUB_ACTIONS_PERMISSION_MODEL.md").lower()

    assert "checks: write" in workflow
    assert "statuses: write" in workflow
    assert "checks: write" in doc
    assert "statuses: write" in doc
    assert "justification" in doc or "why each write permission exists" in doc


def test_no_pull_request_target_in_internal_workflows() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (ROOT / ".github/workflows").glob("*.yml")
    )

    assert "pull_request_target" not in combined
