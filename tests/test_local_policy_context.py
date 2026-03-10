from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import repobrain.tky_local as tky_local
from repobrain.tky_provider import CandidateChunk


class _CaptureEngine:
    def __init__(self) -> None:
        self.last_req: Any | None = None

    def decide(self, req):  # noqa: ANN001
        self.last_req = req
        from repobrain.tky_engine import EngineDecision, EngineSecurity

        return EngineDecision(
            route="FAST",
            selected_chunk_ids=[req.candidates[0].chunk_id] if req.candidates else [],
            compression_stats={"retrieved": len(req.candidates), "selected": 1},
            security=EngineSecurity(
                blocked=False,
                injection_risk="low",
                exfiltration_risk="low",
                signals=[],
            ),
            rationale="ok",
            stable_tokens=["s1"],
        )


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
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_RUN_ID", "42")
    monkeypatch.setenv("GITHUB_ACTOR", "alice")
    monkeypatch.setenv("RB_TKYA_ALLOW_REMOTE", "0")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    provider = tky_local.LocalTKYProvider()
    provider.compress_context(
        question="Where is TKYProvider?",
        candidates=_sample_candidates(),
        limits={"task_type": "ask", "max_sources": 4, "top_k": 30},
    )

    req = capture.last_req
    assert req is not None
    policy = req.policy
    assert policy["corelocked"] is True
    assert "github_context" in policy
    assert "verification_context" in policy
    assert "runtime" in policy
    github_context = policy["github_context"]
    assert github_context["event_name"] == "issue_comment"
    assert github_context["repository"] == "owner/repo"
    assert github_context["pr_number"] == 17
    verification_context = policy["verification_context"]
    assert verification_context["mode"] == "ci"
    assert verification_context["network_allowed"] is False


def test_local_provider_builds_policy_context_for_review(monkeypatch: pytest.MonkeyPatch) -> None:
    capture = _CaptureEngine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    monkeypatch.setenv("RB_TKYA_ALLOW_REMOTE", "0")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    provider = tky_local.LocalTKYProvider()
    provider.compress_context(
        question="Review changes",
        candidates=_sample_candidates(),
        limits={"task_type": "review", "max_sources": 3},
    )

    req = capture.last_req
    assert req is not None
    assert req.task_type == "review"
    assert "github_context" in req.policy
    assert "verification_context" in req.policy
