from __future__ import annotations

import sys
import types

import pytest

import repobrain.tky_local as tky_local
from repobrain.topocore_backend import TopoCoreBackendError, V6_UNAVAILABLE_V5_DISABLED_REASON, resolve_backend
from repobrain.topocore_deprecation import (
    TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON,
    TOPOCORE_V5_SIMULATED_DISABLED_REASON,
    TOPOCORE_V5_SIMULATION_ENV,
    get_topocore_deprecation_policy,
    is_v5_simulated_disabled,
)
from repobrain.tky_provider import CandidateChunk


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


def _build_fake_topocore_v6_module() -> types.ModuleType:
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
    monkeypatch.delenv("RB_TOPOCORE_ALLOW_DEPRECATED_V5", raising=False)
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


def test_policy_still_exposes_obsolete_simulation_metadata() -> None:
    policy = get_topocore_deprecation_policy()

    assert policy["legacy_runtime_simulation_env"] == TOPOCORE_V5_SIMULATION_ENV
    assert policy["legacy_runtime_simulated_disabled_reason"] == TOPOCORE_V5_SIMULATED_DISABLED_REASON
    assert policy["legacy_runtime_off_simulation_available"] is True
    assert policy["legacy_runtime_removed"] is True


def test_simulation_env_does_not_block_supported_v6_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    monkeypatch.setenv(TOPOCORE_V5_SIMULATION_ENV, "1")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()

    result = tky_local.LocalTKYProvider().compress_context(
        question="Explain the provider path.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert result.compression_stats["requested_backend"] == "auto"
    assert result.compression_stats["resolved_backend"] == "v6"
    assert result.compression_stats["fallback_used"] is False


def test_simulation_env_does_not_restore_removed_v5_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")
    monkeypatch.setenv(TOPOCORE_V5_SIMULATION_ENV, "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    message = str(exc_info.value)
    assert "deprecated_v5_removed" in message
    assert TOPOCORE_V5_SIMULATED_DISABLED_REASON not in message


def test_simulation_env_does_not_change_auto_v6_unavailable_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    monkeypatch.setenv(TOPOCORE_V5_SIMULATION_ENV, "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Explain the provider path.",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    message = str(exc_info.value)
    assert V6_UNAVAILABLE_V5_DISABLED_REASON in message
    assert TOPOCORE_V5_SIMULATED_DISABLED_REASON not in message


def test_simulation_env_with_allow_env_still_keeps_legacy_v5_unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv("RB_TOPOCORE_ALLOW_DEPRECATED_V5", "1")
    monkeypatch.setenv(TOPOCORE_V5_SIMULATION_ENV, "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON in str(exc_info.value)
