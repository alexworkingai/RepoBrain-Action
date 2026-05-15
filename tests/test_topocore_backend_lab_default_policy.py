from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

import repobrain.tky_local as tky_local
from repobrain.topocore_backend import BACKEND_AUTO, BACKEND_V5, BACKEND_V6, TopoCoreBackendError, resolve_backend
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
    def __init__(self, recorder: dict[str, object]) -> None:
        self._recorder = recorder

    def health(self) -> dict[str, object]:
        return {"status": "ok"}

    def decide_external(self, request):  # noqa: ANN001
        self._recorder.setdefault("requests", []).append(request)
        status = "ready"
        action = "proceed"
        message_code = "DECISION_READY"
        if request.limits.get("requested_task_type") == "review":
            status = "needs_review"
            action = "review"
            message_code = "REVIEW_RECOMMENDED"
        elif request.limits.get("requested_task_type") == "verify":
            status = "needs_more_information"
            action = "investigate"
            message_code = "MORE_INFORMATION_REQUIRED"
        return types.SimpleNamespace(
            status=status,
            action=action,
            reference_hash="safe-auto-ref",
            selected_count=1,
            blocked=False,
            confidence_band="high",
            message_code=message_code,
        )

    @property
    def decide_raw(self) -> object:
        raise AssertionError("decide_raw should never be accessed")


def _sample_candidates() -> list[CandidateChunk]:
    return [
        CandidateChunk(
            chunk_id="c1",
            file_path="repobrain/tky_provider.py",
            line_start=1,
            line_end=20,
            score=0.91,
            signature=[1, 2, 3],
        ),
        CandidateChunk(
            chunk_id="c2",
            file_path="repobrain/review.py",
            line_start=5,
            line_end=16,
            score=0.27,
            signature=[4, 5, 6],
        ),
    ]


def _fix_policy_seed() -> dict[str, object]:
    return {
        "fix_draft_summary": {
            "localized_target_hint": "repobrain/patch_validator.py",
            "no_patch_reason": "insufficient_localized_grounding",
            "patch_safety_notes": ["manual-only", "no patch applied"],
        },
        "patch_governance": {
            "patchability_class": "no_patch_safe_default",
            "governance_reason": "safe_no_patch_default",
            "next_safe_step": "manual review",
        },
    }


def _build_fake_topocore_v6_module(recorder: dict[str, object]) -> types.ModuleType:
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
    fake_module.create_topocore = lambda: _FakeFacade(recorder)
    fake_module.EngineRequest = EngineRequest
    fake_module.EngineQuery = EngineQuery
    fake_module.EngineCandidate = EngineCandidate
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


def test_no_env_defaults_to_auto_policy() -> None:
    resolution = resolve_backend()
    assert resolution.requested_backend == BACKEND_AUTO
    assert resolution.selected_backend == BACKEND_V6
    assert resolution.source_env == "default_auto"
    assert "topocore_v6" not in sys.modules


def test_auto_policy_uses_v6_when_fake_v6_is_available() -> None:
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(recorder)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Explain the provider path.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert result.compression_stats["requested_backend"] == "auto"
    assert result.compression_stats["resolved_backend"] == "v6"
    assert result.compression_stats["fallback_used"] is False
    assert result.compression_stats["topocore_backend"] == "v6"
    assert len(recorder["requests"]) == 1


def test_auto_policy_falls_back_to_v5_when_v6_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Locate provider logic.",
        candidates=_sample_candidates(),
        limits={"task_type": "locate"},
    )

    assert capture.calls == 1
    assert result.compression_stats["requested_backend"] == "auto"
    assert result.compression_stats["resolved_backend"] == "v5"
    assert result.compression_stats["fallback_used"] is True
    assert result.compression_stats["fallback_reason"] == "v6_unavailable"
    assert result.compression_stats["topocore_backend_fallback"] == "v5"
    assert "C:\\" not in json.dumps(result.compression_stats, sort_keys=True)


def test_auto_policy_strict_mode_fails_safely_when_v6_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Ask in strict auto mode.",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    message = str(exc_info.value)
    assert "unavailable" in message.lower() or "not available" in message.lower()
    assert "C:\\" not in message
    assert "token" not in message.lower()
    assert "RB_TOPOCORE_BACKEND" not in message


def test_rb_topocore_backend_v5_forces_v5(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(recorder)

    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Ask on forced v5.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert capture.calls == 1
    assert result.compression_stats["requested_backend"] == "v5"
    assert result.compression_stats["resolved_backend"] == "v5"
    assert "requests" not in recorder


def test_rb_topocore_backend_v6_forces_v6(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(recorder)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Ask on forced v6.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert result.compression_stats["requested_backend"] == "v6"
    assert result.compression_stats["resolved_backend"] == "v6"
    assert len(recorder["requests"]) == 1


def test_rb_topocore_backend_has_precedence_over_rb_tkya_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")
    monkeypatch.setenv("RB_TKYA_BACKEND", "v6")
    assert resolve_backend().requested_backend == "v5"
    assert resolve_backend().selected_backend == BACKEND_V5

    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    assert resolve_backend().requested_backend == "v6"
    assert resolve_backend().selected_backend == BACKEND_V6


def test_rb_tkya_backend_v5_preserves_github_style_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(recorder)

    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Review under GitHub-style pin.",
        candidates=_sample_candidates(),
        limits={"task_type": "review"},
    )

    assert capture.calls == 1
    assert result.compression_stats["requested_backend"] == "v5"
    assert result.compression_stats["resolved_backend"] == "v5"
    assert "requests" not in recorder


def test_rb_tkya_backend_lite_remains_compatible() -> None:
    resolution = resolve_backend(env={"RB_TKYA_BACKEND": "lite"})
    assert resolution.requested_backend == BACKEND_V5
    assert resolution.selected_backend == BACKEND_V5
    assert "topocore_v6" not in sys.modules


def test_invalid_backend_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "bad-value")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Ask with bad backend.",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    message = str(exc_info.value)
    assert "Invalid backend selection" in message
    assert "RB_TOPOCORE_BACKEND" not in message
    assert "token" not in message.lower()


def test_command_coverage_under_auto_v6() -> None:
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(recorder)

    command_limits = {
        "ask": {"task_type": "ask"},
        "explain": {"task_type": "explain"},
        "locate": {"task_type": "locate"},
        "review": {"task_type": "review"},
        "verify": {"task_type": "verify"},
        "fix": {"task_type": "fix", "policy": _fix_policy_seed()},
    }

    results = {}
    for command, limits in command_limits.items():
        results[command] = tky_local.LocalTKYProvider().compress_context(
            question=f"Run {command} path.",
            candidates=_sample_candidates(),
            limits=limits,
        )

    assert len(recorder["requests"]) == 6
    for request in recorder["requests"]:
        assert set(request.policy) == {
            "evidence_summary",
            "bit_matrix_summary",
            "verification_summary",
            "project_audit_summary",
            "risk_summary",
            "scenario_summary",
        }

    assert results["ask"].compression_stats["resolved_backend"] == "v6"
    assert results["explain"].compression_stats["resolved_backend"] == "v6"
    assert results["locate"].compression_stats["resolved_backend"] == "v6"
    assert results["review"].compression_stats["resolved_backend"] == "v6"
    assert results["verify"].compression_stats["resolved_backend"] == "v6"
    assert results["fix"].compression_stats["resolved_backend"] == "v6"


def test_fix_lite_remains_conservative_under_auto_v6() -> None:
    recorder: dict[str, object] = {}
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(recorder)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Prepare a bounded fix summary.",
        candidates=_sample_candidates(),
        limits={"task_type": "fix", "policy": _fix_policy_seed()},
    )

    stats = result.compression_stats
    assert stats["resolved_backend"] == "v6"
    assert stats["patch_authorized"] is False
    assert stats["patch_applied"] is False
    assert stats["files_modified"] is False
    assert stats["branch_created"] is False
    assert stats["commit_created"] is False
    assert stats["pr_created"] is False
    rendered = json.dumps(stats, sort_keys=True)
    assert "autofix" not in rendered
    assert "safe_to_merge" not in rendered
    assert "security_verdict" not in rendered


def test_github_default_files_unchanged() -> None:
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
