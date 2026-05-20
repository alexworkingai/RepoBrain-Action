from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

import repobrain.tky_local as tky_local
from repobrain.topocore_backend import (
    BACKEND_AUTO,
    BACKEND_V6,
    LEGACY_LITE_DISABLED_REASON,
    TopoCoreBackendError,
    V6_UNAVAILABLE_V5_DISABLED_REASON,
    resolve_backend,
)
from repobrain.topocore_deprecation import (
    TOPOCORE_V5_ALLOW_DEPRECATED_ENV,
    TOPOCORE_V5_DEPRECATED_ALLOWED_REASON,
    TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON,
)
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
            file_path="repobrain/ask.py",
            line_start=5,
            line_end=16,
            score=0.27,
            signature=[4, 5, 6],
        ),
    ]


def _build_fake_topocore_v6_module(*, decide_raw_raises: bool = False) -> types.ModuleType:
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
            assert request.task_type in {"ask", "locate", "explain", "review"}
            return ExternalDecisionView()

        if decide_raw_raises:
            @property
            def decide_raw(self) -> object:
                raise AssertionError("decide_raw should never be accessed")

    fake_module = types.ModuleType("topocore_v6")
    fake_module.create_topocore = lambda: FakeFacade()
    fake_module.EngineRequest = EngineRequest
    fake_module.EngineQuery = EngineQuery
    fake_module.EngineCandidate = EngineCandidate
    fake_module.ExternalDecisionView = ExternalDecisionView
    return fake_module


@pytest.fixture(autouse=True)
def _clear_topocore_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RB_TOPOCORE_BACKEND", raising=False)
    monkeypatch.delenv("RB_TKYA_BACKEND", raising=False)
    monkeypatch.delenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", raising=False)
    monkeypatch.delenv("RB_TOPOCORE_V6_LOCAL_PATH", raising=False)
    monkeypatch.delenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, raising=False)
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def test_default_backend_policy_is_auto() -> None:
    resolution = resolve_backend()
    assert resolution.requested_backend == BACKEND_AUTO
    assert resolution.source_env == "default_auto"
    assert resolution.selected_backend == BACKEND_V6
    assert resolution.deprecated_v5_allowed is False
    assert "topocore_v6" not in sys.modules


def test_rb_tkya_backend_v5_is_blocked_without_emergency_allow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON in str(exc_info.value)


def test_rb_topocore_backend_v6_selects_v6(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    resolution = resolve_backend()
    assert resolution.requested_backend == BACKEND_V6
    assert resolution.selected_backend == BACKEND_V6
    assert "topocore_v6" not in sys.modules


def test_rb_topocore_backend_has_precedence_even_when_v5_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    assert resolve_backend().selected_backend == BACKEND_V6

    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")
    monkeypatch.setenv("RB_TKYA_BACKEND", "v6")
    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()
    assert TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON in str(exc_info.value)


def test_invalid_backend_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "bad-value")
    provider = tky_local.LocalTKYProvider()

    with pytest.raises(TopoCoreBackendError) as exc_info:
        provider.compress_context(
            question="Where is provider logic?",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    message = str(exc_info.value)
    assert "Invalid backend selection" in message
    assert "RB_TOPOCORE_BACKEND" not in message
    assert "token" not in message.lower()


def test_missing_v6_dependency_fails_safely_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    v5_engine = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: v5_engine)

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Explain the provider path.",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    assert v5_engine.calls == 0
    assert V6_UNAVAILABLE_V5_DISABLED_REASON in str(exc_info.value)


def test_missing_v6_dependency_strict_mode_fails_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    monkeypatch.setenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Explain the provider path.",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    message = str(exc_info.value)
    assert "unavailable" in message.lower() or "not available" in message.lower()
    assert "[redacted-path]" not in message or "path" in message.lower()


def test_fake_v6_backend_returns_normalized_safe_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()

    result = tky_local.LocalTKYProvider().compress_context(
        question="Explain the provider path.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert result.route == "FAST"
    assert result.compression_stats["topocore_backend"] == "v6"
    assert result.compression_stats["external_status"] == "ready"
    assert result.compression_stats["external_action"] == "proceed"
    assert result.compression_stats["message_code"] == "DECISION_READY"
    rendered = json.dumps(result.compression_stats, sort_keys=True)
    assert "decide_raw" not in rendered
    assert "compression_stats_hash" not in rendered


def test_decide_raw_is_never_called(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(decide_raw_raises=True)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Locate provider logic.",
        candidates=_sample_candidates(),
        limits={"task_type": "locate"},
    )

    assert result.route == "FAST"


def test_fix_path_remains_not_migrated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()

    result = tky_local.LocalTKYProvider().compress_context(
        question="Prepare a fix path.",
        candidates=_sample_candidates(),
        limits={"task_type": "fix"},
    )

    assert result.compression_stats["topocore_backend"] == "v6"
    rendered = json.dumps(result.compression_stats, sort_keys=True)
    assert "apply_patch" not in rendered
    assert "create_commit" not in rendered
    assert "create_branch" not in rendered
    assert "create_pr" not in rendered


def test_explicit_v5_can_run_under_emergency_allow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")
    monkeypatch.setenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, "1")
    v5_engine = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: v5_engine)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Emergency v5 only.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert v5_engine.calls == 1
    assert result.compression_stats["topocore_backend"] == "v5"
    assert result.compression_stats["deprecated_v5_allowed"] is True
    assert result.compression_stats["fallback_reason"] == TOPOCORE_V5_DEPRECATED_ALLOWED_REASON


def test_auto_can_fallback_to_v5_only_under_emergency_allow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    monkeypatch.setenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, "1")
    v5_engine = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: v5_engine)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Fallback only if necessary.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert v5_engine.calls == 1
    assert result.compression_stats["requested_backend"] == "auto"
    assert result.compression_stats["resolved_backend"] == "v5"
    assert result.compression_stats["fallback_used"] is True
    assert result.compression_stats["fallback_reason"] == TOPOCORE_V5_DEPRECATED_ALLOWED_REASON
    assert result.compression_stats["topocore_backend_fallback"] == "v5"


def test_legacy_lite_remains_blocked_without_emergency_allow() -> None:
    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend(env={"RB_TKYA_BACKEND": "lite"})
    assert LEGACY_LITE_DISABLED_REASON in str(exc_info.value)


def test_no_github_runtime_private_import_drift() -> None:
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8")
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "RB_TKYA_BACKEND" in action_text
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
