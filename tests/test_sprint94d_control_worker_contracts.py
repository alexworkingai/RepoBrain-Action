from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.control_worker_result import (
    CONTROL_WORKER_RESULT_CONTRACT_VERSION,
    build_completed_result,
    render_control_worker_result_markdown,
)


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8").lower()


def test_94d_contract_docs_exist() -> None:
    assert (ROOT / "docs/contracts/CONTROL_WORKER_REQUEST_V1.md").exists()
    assert (ROOT / "docs/contracts/CONTROL_WORKER_RESULT_V1.md").exists()
    assert (ROOT / "docs/contracts/TOPOCORE_ENTRYPOINT_ADAPTER_V1.md").exists()
    assert (ROOT / "docs/architecture/SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT.md").exists()


def test_control_worker_result_contract_version_is_stable() -> None:
    assert CONTROL_WORKER_RESULT_CONTRACT_VERSION == "repobrain.control_worker_result.v1"


def test_topocore_adapter_doc_keeps_topocore_boundary_explicit() -> None:
    text = _read("docs/contracts/TOPOCORE_ENTRYPOINT_ADAPTER_V1.md")
    assert "topocore is a separate team and system" in text
    assert "without implementing topocore internals" in text


def test_94d_contract_docs_forbid_secret_and_private_path_leakage() -> None:
    combined = "\n".join(
        [
            _read("docs/contracts/CONTROL_WORKER_REQUEST_V1.md"),
            _read("docs/contracts/CONTROL_WORKER_RESULT_V1.md"),
            _read("docs/contracts/TOPOCORE_ENTRYPOINT_ADAPTER_V1.md"),
            _read("docs/architecture/SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT.md"),
        ]
    )
    for required in (
        "tokens",
        "private key",
        "jwt",
        "authorization",
        "private topocore paths",
        "private checkout paths",
    ):
        assert required in combined


def test_completed_result_renderer_keeps_public_safety_footer_and_request_id() -> None:
    result = build_completed_result(
        request_id="rbq_test_contract_123",
        command="score",
        profile="partner-pilot",
        repository_full_name="owner/repo",
        issue_number=7,
        pull_request_number=None,
        backend="private_topocore_stub",
        fallback="not_applicable",
        score=86,
        verdict="GOOD",
        blockers_summary=["No blocking issues."],
        warnings_summary=["Bounded output only."],
        evidence_summary=["Queue request processed by the private control worker."],
        public_notes=["Safe completed result rendered."],
        processed_at="2026-06-13T12:00:00Z",
    )

    markdown = render_control_worker_result_markdown(result)
    assert "rbq_test_contract_123" in markdown
    assert "Score authority: TopoCore." in markdown
    assert "LLM does not modify score." in markdown
    assert "no patch/autofix" in markdown


def test_completed_result_rejects_unsafe_public_note() -> None:
    with pytest.raises(Exception) as exc_info:
        build_completed_result(
            request_id="rbq_test_contract_unsafe",
            command="audit",
            profile="premium",
            repository_full_name="owner/repo",
            issue_number=9,
            pull_request_number=9,
            backend="private_topocore_stub",
            fallback="not_applicable",
            score=90,
            verdict="GOOD",
            blockers_summary=["No blockers."],
            warnings_summary=["None."],
            evidence_summary=["Safe evidence."],
            public_notes=["Authorization: Bearer abc.def.ghi"],
            processed_at="2026-06-13T12:00:00Z",
        )

    assert getattr(exc_info.value, "code", "") == "CONTROL_WORKER_RESULT_INVALID"
