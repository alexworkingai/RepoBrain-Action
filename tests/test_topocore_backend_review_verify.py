from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

import repobrain.tky_local as tky_local
from repobrain.topocore_backend import TopoCoreBackendError
from repobrain.tky_engine import EngineDecision, EngineSecurity
from repobrain.tky_provider import CandidateChunk


_ROOT = Path(__file__).resolve().parents[1]


class _CaptureV5Engine:
    def __init__(self) -> None:
        self.calls = 0
        self.last_req = None

    def decide(self, req):  # noqa: ANN001
        self.calls += 1
        self.last_req = req
        return EngineDecision(
            route="REVIEW" if req.task_type == "review" else "FAST",
            selected_chunk_ids=[req.candidates[0].chunk_id] if req.candidates else [],
            compression_stats={"retrieved": len(req.candidates), "selected": 1},
            security=EngineSecurity(
                blocked=False,
                injection_risk="low",
                exfiltration_risk="low",
                signals=[],
            ),
            rationale="v5 ok",
            stable_tokens=["s1"],
        )


class _FakeFacade:
    def __init__(self, recorder: dict[str, object], *, status: str, action: str, message_code: str) -> None:
        self._recorder = recorder
        self._status = status
        self._action = action
        self._message_code = message_code

    def health(self) -> dict[str, object]:
        return {"status": "ok"}

    def decide_external(self, request):  # noqa: ANN001
        self._recorder["request"] = request
        return types.SimpleNamespace(
            status=self._status,
            action=self._action,
            reference_hash="safe-ref-1",
            selected_count=1,
            blocked=False,
            confidence_band="medium",
            message_code=self._message_code,
        )

    @property
    def decide_raw(self) -> object:
        raise AssertionError("decide_raw should never be accessed")


def _sample_candidates() -> list[CandidateChunk]:
    return [
        CandidateChunk(
            chunk_id="c1",
            file_path="repobrain/review.py",
            line_start=10,
            line_end=24,
            score=0.87,
            signature=[1, 2, 3],
        ),
        CandidateChunk(
            chunk_id="c2",
            file_path="repobrain/verify.py",
            line_start=3,
            line_end=11,
            score=0.42,
            signature=[4, 5, 6],
        ),
    ]


def _build_fake_topocore_v6_module(
    recorder: dict[str, object],
    *,
    status: str,
    action: str,
    message_code: str,
) -> types.ModuleType:
    class EngineQuery:
        def __init__(self, *, text: str, signature: list[int] | None = None) -> None:
            self.text = text
            self.signature = signature

    class EngineCandidate:
        def __init__(
            self,
            *,
            chunk_id: str,
            score_local: float,
            signature: list[int] | None = None,
            file_path: str | None = None,
            line_start: int | None = None,
            line_end: int | None = None,
        ) -> None:
            self.chunk_id = chunk_id
            self.score_local = score_local
            self.signature = signature
            self.file_path = file_path
            self.line_start = line_start
            self.line_end = line_end

    class EngineRequest:
        def __init__(
            self,
            *,
            task_type: str,
            query: EngineQuery,
            candidates: list[EngineCandidate],
            limits: dict[str, object],
            policy: dict[str, object],
        ) -> None:
            self.task_type = task_type
            self.query = query
            self.candidates = candidates
            self.limits = limits
            self.policy = policy

    fake_module = types.ModuleType("topocore_v6")
    fake_module.create_topocore = lambda: _FakeFacade(
        recorder,
        status=status,
        action=action,
        message_code=message_code,
    )
    fake_module.EngineQuery = EngineQuery
    fake_module.EngineCandidate = EngineCandidate
    fake_module.EngineRequest = EngineRequest
    fake_module.ExternalDecisionView = types.SimpleNamespace
    return fake_module


@pytest.fixture(autouse=True)
def _clear_env_and_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RB_TOPOCORE_BACKEND", raising=False)
    monkeypatch.delenv("RB_TKYA_BACKEND", raising=False)
    monkeypatch.delenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", raising=False)
    monkeypatch.delenv("RB_TOPOCORE_V6_LOCAL_PATH", raising=False)
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def test_review_task_uses_v5_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Review this change set.",
        candidates=_sample_candidates(),
        limits={"task_type": "review"},
    )

    assert capture.calls == 1
    assert capture.last_req.task_type == "review"
    assert result.compression_stats["topocore_backend"] == "v5"
    assert "topocore_v6" not in sys.modules


def test_verify_task_uses_v5_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Verify current checks.",
        candidates=_sample_candidates(),
        limits={"task_type": "verify"},
    )

    assert capture.calls == 1
    assert capture.last_req.task_type == "review"
    assert result.compression_stats["topocore_backend"] == "v5"
    assert "topocore_v6" not in sys.modules


def test_review_task_can_select_v6_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="needs_review",
        action="review",
        message_code="REVIEW_RECOMMENDED",
    )

    result = tky_local.LocalTKYProvider().compress_context(
        question="Review the PR risk profile.",
        candidates=_sample_candidates(),
        limits={"task_type": "review", "user_goal": "review risk"},
    )

    request = recorder["request"]
    assert request.task_type == "review"
    assert request.policy["project_audit_summary"]["pr_context"]["command_family"] == "review"
    assert request.policy["verification_summary"]["command_family"] == "review"
    assert result.compression_stats["topocore_backend"] == "v6"
    assert result.compression_stats["external_action"] == "review"


def test_verify_task_can_select_v6_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="ready",
        action="proceed",
        message_code="VERIFY_SIGNAL_READY",
    )

    result = tky_local.LocalTKYProvider().compress_context(
        question="Verify the current evidence ladder.",
        candidates=_sample_candidates(),
        limits={"task_type": "verify", "user_goal": "verify checks"},
    )

    request = recorder["request"]
    assert request.task_type == "review"
    assert request.policy["verification_summary"]["command_family"] == "verify"
    assert request.policy["scenario_summary"]["unknowns_summary"]["command_family"] == "verify"
    assert result.compression_stats["topocore_backend"] == "v6"
    assert result.compression_stats["message_code"] == "VERIFY_SIGNAL_READY"


def test_review_policy_uses_real_v6_summary_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="needs_review",
        action="review",
        message_code="REVIEW_RECOMMENDED",
    )

    tky_local.LocalTKYProvider().compress_context(
        question="Review the PR risk profile.",
        candidates=_sample_candidates(),
        limits={"task_type": "review"},
    )

    policy = recorder["request"].policy
    assert set(policy) == {
        "evidence_summary",
        "bit_matrix_summary",
        "verification_summary",
        "project_audit_summary",
        "risk_summary",
        "scenario_summary",
    }
    rendered = json.dumps(policy, sort_keys=True)
    for forbidden in (
        "raw_diff",
        "raw_code",
        "prompt",
        "system_prompt",
        "hidden_prompt",
        "secret",
        "token",
        "api_key",
        "decide_raw",
        "compression_stats",
        "raw_trace",
        "governance_internals",
    ):
        assert forbidden not in rendered


def test_verify_policy_uses_real_v6_summary_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="ready",
        action="proceed",
        message_code="VERIFY_SIGNAL_READY",
    )

    tky_local.LocalTKYProvider().compress_context(
        question="Verify the current evidence ladder.",
        candidates=_sample_candidates(),
        limits={"task_type": "verify"},
    )

    policy = recorder["request"].policy
    assert set(policy) == {
        "evidence_summary",
        "bit_matrix_summary",
        "verification_summary",
        "project_audit_summary",
        "risk_summary",
        "scenario_summary",
    }
    rendered = json.dumps(policy, sort_keys=True)
    for forbidden in (
        "raw_diff",
        "raw_code",
        "prompt",
        "system_prompt",
        "hidden_prompt",
        "secret",
        "token",
        "api_key",
        "decide_raw",
        "compression_stats",
        "raw_trace",
        "governance_internals",
    ):
        assert forbidden not in rendered


def test_missing_v6_dependency_falls_back_to_v5_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Review the fallback behavior.",
        candidates=_sample_candidates(),
        limits={"task_type": "review"},
    )

    assert capture.calls == 1
    assert result.compression_stats["topocore_backend"] == "v5"
    assert result.compression_stats["topocore_backend_fallback"] == "v5"


def test_missing_v6_dependency_strict_mode_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    monkeypatch.setenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Verify strict dependency behavior.",
            candidates=_sample_candidates(),
            limits={"task_type": "verify"},
        )

    message = str(exc_info.value)
    assert "unavailable" in message.lower() or "not available" in message.lower()
    assert "C:\\" not in message
    assert "token" not in message.lower()


def test_v6_review_result_is_normalized_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="needs_review",
        action="review",
        message_code="REVIEW_RECOMMENDED",
    )

    result = tky_local.LocalTKYProvider().compress_context(
        question="Review the PR risk profile.",
        candidates=_sample_candidates(),
        limits={"task_type": "review"},
    )

    stats = result.compression_stats
    assert stats["external_status"] == "needs_review"
    assert stats["external_action"] == "review"
    assert stats["message_code"] == "REVIEW_RECOMMENDED"
    rendered = json.dumps(stats, sort_keys=True)
    assert "safe_to_merge" not in rendered
    assert "approval" not in rendered
    assert "security_verdict" not in rendered


def test_v6_verify_result_is_normalized_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="ready",
        action="proceed",
        message_code="VERIFY_SIGNAL_READY",
    )

    result = tky_local.LocalTKYProvider().compress_context(
        question="Verify the current evidence ladder.",
        candidates=_sample_candidates(),
        limits={"task_type": "verify"},
    )

    stats = result.compression_stats
    assert stats["external_status"] == "ready"
    assert stats["external_action"] == "proceed"
    assert stats["message_code"] == "VERIFY_SIGNAL_READY"
    rendered = json.dumps(stats, sort_keys=True)
    assert "security_verdict" not in rendered
    assert "approval" not in rendered
    assert "rejection" not in rendered


def test_decide_raw_is_never_called(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="ready",
        action="proceed",
        message_code="VERIFY_SIGNAL_READY",
    )

    review_result = tky_local.LocalTKYProvider().compress_context(
        question="Review the PR risk profile.",
        candidates=_sample_candidates(),
        limits={"task_type": "review"},
    )
    verify_result = tky_local.LocalTKYProvider().compress_context(
        question="Verify the current evidence ladder.",
        candidates=_sample_candidates(),
        limits={"task_type": "verify"},
    )

    assert review_result.compression_stats["topocore_backend"] == "v6"
    assert verify_result.compression_stats["topocore_backend"] == "v6"


def test_fix_path_remains_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="ready",
        action="proceed",
        message_code="DECISION_READY",
    )

    result = tky_local.LocalTKYProvider().compress_context(
        question="Prepare a fix path.",
        candidates=_sample_candidates(),
        limits={"task_type": "fix"},
    )

    request = recorder["request"]
    assert request.task_type == "ask"
    rendered = json.dumps(result.compression_stats, sort_keys=True)
    assert "apply_patch" not in rendered
    assert "create_commit" not in rendered
    assert "create_branch" not in rendered
    assert "create_pr" not in rendered


def test_github_default_behavior_remains_unchanged() -> None:
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8")
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "RB_TKYA_BACKEND" in action_text
    assert "v5" in action_text
    assert "RB_TOPOCORE_BACKEND" not in workflow_text

    for relative_path in (
        "repobrain/github_flow.py",
        "repobrain/tky_local.py",
        "repobrain/tky_engine.py",
        "repobrain/tkya/engine.py",
    ):
        content = (_ROOT / relative_path).read_text(encoding="utf-8")
        assert "import topocore_v6" not in content
        assert "from topocore_v6" not in content
