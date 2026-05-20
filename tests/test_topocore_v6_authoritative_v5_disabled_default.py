from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

import repobrain.tky_local as tky_local
from repobrain.topocore_backend import (
    BACKEND_V5,
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
    TOPOCORE_V5_DISABLED_BY_DEFAULT,
    TOPOCORE_V5_SIMULATED_DISABLED_REASON,
    TOPOCORE_V5_SIMULATION_ENV,
    TOPOCORE_V6_AUTHORITATIVE,
    get_topocore_deprecation_policy,
    is_deprecated_v5_allowed,
)
from repobrain.tky_engine import EngineDecision, EngineSecurity
from repobrain.tky_provider import CandidateChunk


_ROOT = Path(__file__).resolve().parents[1]


class _CaptureV5Engine:
    def __init__(self) -> None:
        self.calls = 0

    def decide(self, req):  # noqa: ANN001
        self.calls += 1
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
        )
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
def _clear_env_and_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RB_TOPOCORE_BACKEND", raising=False)
    monkeypatch.delenv("RB_TKYA_BACKEND", raising=False)
    monkeypatch.delenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", raising=False)
    monkeypatch.delenv("RB_TOPOCORE_V6_LOCAL_PATH", raising=False)
    monkeypatch.delenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, raising=False)
    monkeypatch.delenv(TOPOCORE_V5_SIMULATION_ENV, raising=False)
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def test_deprecation_metadata_says_v6_is_authoritative() -> None:
    policy = get_topocore_deprecation_policy()

    assert TOPOCORE_V6_AUTHORITATIVE is True
    assert policy["topocore_v6_authoritative"] is True


def test_deprecation_metadata_says_v5_is_disabled_by_default() -> None:
    policy = get_topocore_deprecation_policy()

    assert TOPOCORE_V5_DISABLED_BY_DEFAULT is True
    assert policy["topocore_v5_disabled_by_default"] is True


def test_allow_deprecated_v5_helper_defaults_false() -> None:
    assert is_deprecated_v5_allowed({}) is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", "y"])
def test_allow_deprecated_v5_helper_accepts_truthy_values(value: str) -> None:
    assert is_deprecated_v5_allowed({TOPOCORE_V5_ALLOW_DEPRECATED_ENV: value}) is True


def test_explicit_v5_is_blocked_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON in str(exc_info.value)


def test_legacy_lite_is_blocked_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "lite")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert LEGACY_LITE_DISABLED_REASON in str(exc_info.value)


def test_auto_with_v6_available_resolves_v6_while_v5_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(decide_raw_raises=True)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Explain the provider path.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert result.compression_stats["resolved_backend"] == BACKEND_V6
    assert result.compression_stats["fallback_used"] is False
    assert result.compression_stats["deprecated_v5_allowed"] is False


def test_auto_with_v6_unavailable_does_not_fallback_to_v5_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Explain the provider path.",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    assert capture.calls == 0
    assert V6_UNAVAILABLE_V5_DISABLED_REASON in str(exc_info.value)


def test_emergency_allow_flag_permits_explicit_deprecated_v5_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")
    monkeypatch.setenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, "1")
    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Use emergency v5.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert capture.calls == 1
    assert result.compression_stats["resolved_backend"] == BACKEND_V5
    assert result.compression_stats["deprecated_v5_allowed"] is True
    assert result.compression_stats["fallback_reason"] == TOPOCORE_V5_DEPRECATED_ALLOWED_REASON


def test_emergency_allow_flag_permits_auto_fallback_to_deprecated_v5(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    monkeypatch.setenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, "1")
    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Fallback only if needed.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert capture.calls == 1
    assert result.compression_stats["resolved_backend"] == BACKEND_V5
    assert result.compression_stats["fallback_used"] is True
    assert result.compression_stats["fallback_reason"] == TOPOCORE_V5_DEPRECATED_ALLOWED_REASON


def test_simulation_flag_beats_emergency_allow_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")
    monkeypatch.setenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, "1")
    monkeypatch.setenv(TOPOCORE_V5_SIMULATION_ENV, "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert TOPOCORE_V5_SIMULATED_DISABLED_REASON in str(exc_info.value)


def test_gate_zero_style_semantics_are_safe_without_allow_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON in str(exc_info.value)


def test_gate_zero_style_semantics_can_still_use_emergency_allow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, "1")
    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Emergency gate zero fallback.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert capture.calls == 1
    assert result.compression_stats["resolved_backend"] == BACKEND_V5
    assert result.compression_stats["fallback_reason"] == TOPOCORE_V5_DEPRECATED_ALLOWED_REASON


def test_default_behavior_does_not_import_topocore_v6_at_module_import_time() -> None:
    assert "topocore_v6" not in sys.modules


def test_metadata_module_does_not_import_v5_engine() -> None:
    import repobrain.topocore_deprecation as topocore_deprecation

    assert "tkya" not in topocore_deprecation.__dict__
    assert "tky_local" not in topocore_deprecation.__dict__


def test_changed_paths_do_not_introduce_decide_raw_or_patch_behavior() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            _ROOT / "repobrain" / "topocore_deprecation.py",
            _ROOT / "repobrain" / "topocore_backend.py",
            _ROOT / "repobrain" / "tky_local.py",
        )
    )

    assert "decide_raw(" not in combined
    assert "apply_patch" not in combined
    assert "gh pr create" not in combined
    assert "git commit" not in combined
