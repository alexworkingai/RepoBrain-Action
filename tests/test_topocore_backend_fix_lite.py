from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

import repobrain.tky_local as tky_local
from repobrain.topocore_backend import TopoCoreBackendError, V6_UNAVAILABLE_V5_DISABLED_REASON
from repobrain.topocore_deprecation import TOPOCORE_V5_ALLOW_DEPRECATED_ENV
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
            route="FAST",
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
    def __init__(self, recorder: dict[str, object], *, status: str, action: str, blocked: bool, message_code: str) -> None:
        self._recorder = recorder
        self._status = status
        self._action = action
        self._blocked = blocked
        self._message_code = message_code

    def health(self) -> dict[str, object]:
        return {"status": "ok"}

    def decide_external(self, request):  # noqa: ANN001
        self._recorder["request"] = request
        return types.SimpleNamespace(
            status=self._status,
            action=self._action,
            reference_hash="safe-ref-fix",
            selected_count=1,
            blocked=self._blocked,
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
            file_path="repobrain/patch_validator.py",
            line_start=14,
            line_end=38,
            score=0.83,
            signature=[1, 2, 3],
        ),
        CandidateChunk(
            chunk_id="c2",
            file_path="repobrain/patch_governance.py",
            line_start=2,
            line_end=19,
            score=0.41,
            signature=[4, 5, 6],
        ),
    ]


def _fix_policy_seed() -> dict[str, object]:
    return {
        "fix_draft_summary": {
            "localized_target_hint": "repobrain/patch_validator.py",
            "no_patch_reason": "insufficient_localized_grounding",
            "patch_safety_notes": ["manual-only", "no patch applied"],
            "patch_body": "diff --git a/x b/x",
        },
        "patch_governance": {
            "patchability_class": "no_patch_safe_default",
            "governance_reason": "safe_no_patch_default",
            "next_safe_step": "manual review",
        },
    }


def _build_fake_topocore_v6_module(
    recorder: dict[str, object],
    *,
    status: str,
    action: str,
    blocked: bool,
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
        blocked=blocked,
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
    monkeypatch.delenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, raising=False)
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def test_fix_task_fails_safely_without_v6_or_emergency_allow(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Prepare a bounded fix summary.",
            candidates=_sample_candidates(),
            limits={"task_type": "fix", "policy": _fix_policy_seed()},
        )

    assert V6_UNAVAILABLE_V5_DISABLED_REASON in str(exc_info.value)


def test_fix_task_can_select_v6_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="needs_review",
        action="review",
        blocked=False,
        message_code="REVIEW_RECOMMENDED",
    )

    result = tky_local.LocalTKYProvider().compress_context(
        question="Prepare a bounded fix summary.",
        candidates=_sample_candidates(),
        limits={"task_type": "fix", "policy": _fix_policy_seed(), "user_goal": "bounded fix governance"},
    )

    request = recorder["request"]
    assert request.task_type == "ask"
    assert request.policy["project_audit_summary"]["pr_context"]["command_family"] == "fix"
    assert request.policy["scenario_summary"]["fix_draft_summary"]["no_patch_reason"] == "insufficient_localized_grounding"
    assert result.compression_stats["topocore_backend"] == "v6"


def test_fix_policy_uses_real_v6_summary_keys_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="ready",
        action="proceed",
        blocked=False,
        message_code="DECISION_READY",
    )

    tky_local.LocalTKYProvider().compress_context(
        question="Prepare a bounded fix summary.",
        candidates=_sample_candidates(),
        limits={"task_type": "fix", "policy": _fix_policy_seed()},
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
        "patch_body",
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


def test_v6_fix_lite_result_is_conservative(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="ready",
        action="proceed",
        blocked=False,
        message_code="DECISION_READY",
    )

    result = tky_local.LocalTKYProvider().compress_context(
        question="Prepare a bounded fix summary.",
        candidates=_sample_candidates(),
        limits={"task_type": "fix", "policy": _fix_policy_seed()},
    )

    stats = result.compression_stats
    assert stats["fix_lite_decision"] is True
    assert stats["patch_authorized"] is False
    assert stats["patch_applied"] is False
    assert stats["files_modified"] is False
    assert stats["branch_created"] is False
    assert stats["commit_created"] is False
    assert stats["pr_created"] is False
    assert stats["no_patch_reason"] == "insufficient_localized_grounding"
    rendered = json.dumps(stats, sort_keys=True)
    assert "safe_to_merge" not in rendered
    assert "security_verdict" not in rendered
    assert "approval" not in rendered


def test_blocked_v6_fix_result_remains_conservative(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="blocked",
        action="block",
        blocked=True,
        message_code="BLOCKED",
    )

    result = tky_local.LocalTKYProvider().compress_context(
        question="Prepare a bounded fix summary.",
        candidates=_sample_candidates(),
        limits={"task_type": "fix", "policy": _fix_policy_seed()},
    )

    stats = result.compression_stats
    assert result.route == "REFUSE"
    assert stats["blocked"] is True
    assert stats["patch_authorized"] is False
    assert stats["patch_applied"] is False
    assert stats["no_patch_reason"] == "insufficient_localized_grounding"


def test_decide_raw_is_never_called(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="ready",
        action="proceed",
        blocked=False,
        message_code="DECISION_READY",
    )

    result = tky_local.LocalTKYProvider().compress_context(
        question="Prepare a bounded fix summary.",
        candidates=_sample_candidates(),
        limits={"task_type": "fix", "policy": _fix_policy_seed()},
    )

    assert result.compression_stats["topocore_backend"] == "v6"


def test_fix_does_not_reenable_removed_v5_with_allow_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Prepare a bounded fix summary.",
            candidates=_sample_candidates(),
            limits={"task_type": "fix", "policy": _fix_policy_seed()},
        )

    assert V6_UNAVAILABLE_V5_DISABLED_REASON in str(exc_info.value)


def test_missing_v6_dependency_strict_mode_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    monkeypatch.setenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Prepare a bounded fix summary.",
            candidates=_sample_candidates(),
            limits={"task_type": "fix", "policy": _fix_policy_seed()},
        )

    message = str(exc_info.value)
    assert "unavailable" in message.lower() or "not available" in message.lower()
    assert "C:\\" not in message
    assert "token" not in message.lower()


def test_existing_patch_fix_behavior_is_not_changed_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(
        recorder,
        status="ready",
        action="proceed",
        blocked=False,
        message_code="DECISION_READY",
    )

    result = tky_local.LocalTKYProvider().compress_context(
        question="Prepare a bounded fix summary.",
        candidates=_sample_candidates(),
        limits={"task_type": "fix", "policy": _fix_policy_seed()},
    )

    rendered = json.dumps(result.compression_stats, sort_keys=True)
    assert "apply_patch" not in rendered
    assert "create_commit" not in rendered
    assert "create_branch" not in rendered
    assert "create_pr" not in rendered


def test_github_default_behavior_is_authoritative_v6_only() -> None:
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8")
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "RB_TOPOCORE_BACKEND" in action_text
    assert "auto" in action_text
    assert "issue_comment:" in workflow_text
    assert "workflow_dispatch:" in workflow_text
    assert "topocore_backend:" in workflow_text

    for relative_path in (
        "repobrain/github_flow.py",
        "repobrain/tky_local.py",
        "repobrain/tky_engine.py",
        "repobrain/tkya/engine.py",
    ):
        content = (_ROOT / relative_path).read_text(encoding="utf-8")
        assert "import topocore_v6" not in content
        assert "from topocore_v6" not in content
