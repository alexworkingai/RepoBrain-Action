from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pytest

import repobrain.tky_local as tky_local
from repobrain.tky_provider import CandidateChunk


class _CaptureEngine:
    def __init__(self) -> None:
        self.last_req: Any | None = None

    def module(self):
        capture = self

        class EngineQuery:
            def __init__(self, *, text: str, signature=None) -> None:  # noqa: ANN001
                self.text = text
                self.signature = signature

        class EngineCandidate:
            def __init__(self, **kwargs) -> None:  # noqa: ANN003
                self.chunk_id = kwargs["chunk_id"]
                self.score_local = kwargs["score_local"]
                self.signature = kwargs.get("signature")
                self.file_path = kwargs.get("file_path")
                self.line_start = kwargs.get("line_start")
                self.line_end = kwargs.get("line_end")

        class EngineRequest:
            def __init__(self, **kwargs) -> None:  # noqa: ANN003
                self.task_type = kwargs["task_type"]
                self.query = kwargs["query"]
                self.candidates = kwargs["candidates"]
                self.limits = kwargs["limits"]
                self.policy = kwargs["policy"]

        class ExternalDecisionView:
            def __init__(self) -> None:
                self.status = "ready"
                self.action = "proceed"
                self.reference_hash = "safe-ref"
                self.selected_count = 1
                self.blocked = False
                self.confidence_band = "high"
                self.message_code = "DECISION_READY"

        class FakeFacade:
            def health(self) -> dict[str, object]:
                return {"status": "ok"}

            def decide_external(self, request: EngineRequest) -> ExternalDecisionView:
                capture.last_req = request
                return ExternalDecisionView()

        import types

        fake_module = types.ModuleType("topocore_v6")
        fake_module.create_topocore = lambda: FakeFacade()
        fake_module.EngineRequest = EngineRequest
        fake_module.EngineQuery = EngineQuery
        fake_module.EngineCandidate = EngineCandidate
        fake_module.ExternalDecisionView = ExternalDecisionView
        return fake_module


def _sample_candidates() -> list[CandidateChunk]:
    return [
        CandidateChunk(
            chunk_id="c1",
            file_path="repobrain/tky_provider.py",
            line_start=1,
            line_end=20,
            score=0.9,
            signature=[1, 2, 3],
        )
    ]


def test_local_provider_builds_policy_context_for_ask(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "issue": {"number": 17, "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/17"}},
        "comment": {"id": 123},
    }
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload), encoding="utf-8")

    capture = _CaptureEngine()
    sys.modules["topocore_v6"] = capture.module()
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_RUN_ID", "42")
    monkeypatch.setenv("GITHUB_ACTOR", "alice")
    monkeypatch.setenv("RB_TKYA_ALLOW_REMOTE", "0")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")

    provider = tky_local.LocalTKYProvider()
    provider.compress_context(
        question="Where is TKYProvider?",
        candidates=_sample_candidates(),
        limits={"task_type": "ask", "max_sources": 4, "top_k": 30},
    )

    req = capture.last_req
    assert req is not None
    policy = req.policy
    assert "project_audit_summary" in policy
    assert "verification_summary" in policy
    assert "evidence_summary" in policy
    pr_context = policy["project_audit_summary"]["pr_context"]
    assert pr_context["is_pr"] is True
    assert pr_context["pr_number"] == 17
    assert pr_context["issue_number"] == 17
    assert policy["verification_summary"]["mode"] == "ci"
    assert policy["verification_summary"]["network_allowed"] is False
    assert policy["evidence_summary"]["pr_context_available"] is True
    sys.modules.pop("topocore_v6", None)


def test_local_provider_builds_policy_context_for_review(monkeypatch: pytest.MonkeyPatch) -> None:
    capture = _CaptureEngine()
    sys.modules["topocore_v6"] = capture.module()
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    monkeypatch.setenv("RB_TKYA_ALLOW_REMOTE", "0")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")

    provider = tky_local.LocalTKYProvider()
    provider.compress_context(
        question="Review changes",
        candidates=_sample_candidates(),
        limits={"task_type": "review", "max_sources": 3},
    )

    req = capture.last_req
    assert req is not None
    assert req.task_type == "review"
    assert "project_audit_summary" in req.policy
    assert "verification_summary" in req.policy
    assert req.policy["project_audit_summary"]["pr_context"]["is_pr"] is False
    assert req.policy["verification_summary"]["mode"] == "local"
    sys.modules.pop("topocore_v6", None)
