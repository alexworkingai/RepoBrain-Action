from __future__ import annotations

import json
import sys
import types

import pytest

import repobrain.tky_local as tky_local
from repobrain.topocore_backend import BACKEND_AUTO, BACKEND_V5, TopoCoreBackendError, resolve_backend
from repobrain.topocore_deprecation import (
    TOPOCORE_V5_SIMULATED_DISABLED_REASON,
    TOPOCORE_V5_SIMULATION_ENV,
    get_topocore_deprecation_policy,
    is_v5_simulated_disabled,
)
from repobrain.tky_engine import EngineDecision, EngineSecurity
from repobrain.tky_provider import CandidateChunk


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
def _clear_env_and_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RB_TOPOCORE_BACKEND", raising=False)
    monkeypatch.delenv("RB_TKYA_BACKEND", raising=False)
    monkeypatch.delenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", raising=False)
    monkeypatch.delenv("RB_TOPOCORE_V6_LOCAL_PATH", raising=False)
    monkeypatch.delenv(TOPOCORE_V5_SIMULATION_ENV, raising=False)
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def test_simulation_helper_defaults_false() -> None:
    assert is_v5_simulated_disabled({}) is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", "y"])
def test_simulation_helper_accepts_truthy_values(value: str) -> None:
    assert is_v5_simulated_disabled({TOPOCORE_V5_SIMULATION_ENV: value}) is True


@pytest.mark.parametrize("value", ["", "0", "false", "FALSE", "no", "off"])
def test_simulation_helper_rejects_falsey_values(value: str) -> None:
    assert is_v5_simulated_disabled({TOPOCORE_V5_SIMULATION_ENV: value}) is False


def test_policy_helper_exposes_simulation_metadata() -> None:
    policy = get_topocore_deprecation_policy()

    assert policy["topocore_v5_simulation_env"] == TOPOCORE_V5_SIMULATION_ENV
    assert policy["topocore_v5_simulated_disabled_reason"] == TOPOCORE_V5_SIMULATED_DISABLED_REASON
    assert policy["topocore_v5_off_simulation_available"] is True


def test_default_backend_behavior_unchanged_when_simulation_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")
    resolution = resolve_backend()

    assert resolution.requested_backend == BACKEND_V5
    assert resolution.selected_backend == BACKEND_V5


def test_explicit_v5_is_blocked_safely_when_simulation_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")
    monkeypatch.setenv(TOPOCORE_V5_SIMULATION_ENV, "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    message = str(exc_info.value)
    assert TOPOCORE_V5_SIMULATED_DISABLED_REASON in message
    assert "token" not in message.lower()
    assert "traceback" not in message.lower()


def test_legacy_lite_is_blocked_safely_when_simulation_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "lite")
    monkeypatch.setenv(TOPOCORE_V5_SIMULATION_ENV, "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert TOPOCORE_V5_SIMULATED_DISABLED_REASON in str(exc_info.value)


def test_auto_with_v6_available_still_resolves_v6_when_simulation_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    monkeypatch.setenv(TOPOCORE_V5_SIMULATION_ENV, "1")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(decide_raw_raises=True)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Explain the provider path.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert result.compression_stats["requested_backend"] == "auto"
    assert result.compression_stats["resolved_backend"] == "v6"
    assert result.compression_stats["fallback_used"] is False


def test_auto_with_v6_unavailable_does_not_fallback_to_v5_when_simulation_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    monkeypatch.setenv(TOPOCORE_V5_SIMULATION_ENV, "1")
    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Explain the provider path.",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    assert capture.calls == 0
    message = str(exc_info.value)
    assert TOPOCORE_V5_SIMULATED_DISABLED_REASON in message
    assert "v5 fallback" in message.lower()


def test_gate_zero_semantics_remain_v5_when_simulation_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    resolution = resolve_backend()

    assert resolution.requested_backend == BACKEND_V5
    assert resolution.selected_backend == BACKEND_V5


def test_simulation_enabled_gate_zero_behavior_is_explicit_and_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv(TOPOCORE_V5_SIMULATION_ENV, "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert TOPOCORE_V5_SIMULATED_DISABLED_REASON in str(exc_info.value)


def test_no_topocore_v6_import_required_for_simulation_metadata_tests() -> None:
    assert "topocore_v6" not in sys.modules


def test_no_decide_raw_or_patch_side_effects_in_changed_paths() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    changed_files = [
        root / "repobrain" / "topocore_deprecation.py",
        root / "repobrain" / "topocore_backend.py",
        root / "repobrain" / "tky_local.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in changed_files)

    assert "decide_raw(" not in combined
    assert "apply_patch" not in combined
    assert "gh pr create" not in combined
    assert "git commit" not in combined


def test_simulation_reason_is_safely_serializable() -> None:
    payload = {
        "requested_backend": BACKEND_AUTO,
        "resolved_backend": "unavailable",
        "fallback_used": False,
        "fallback_reason": TOPOCORE_V5_SIMULATED_DISABLED_REASON,
        "v5_simulated_disabled": True,
    }

    rendered = json.dumps(payload, sort_keys=True)
    assert TOPOCORE_V5_SIMULATED_DISABLED_REASON in rendered
    assert "token" not in rendered.lower()
