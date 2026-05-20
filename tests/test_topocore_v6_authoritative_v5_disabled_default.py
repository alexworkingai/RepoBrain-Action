from __future__ import annotations

import sys
import types

import pytest

import repobrain.tky_local as tky_local
from repobrain.topocore_backend import (
    BACKEND_V6,
    LEGACY_LITE_DISABLED_REASON,
    TopoCoreBackendError,
    V6_UNAVAILABLE_V5_DISABLED_REASON,
    resolve_backend,
)
from repobrain.topocore_deprecation import (
    TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON,
    TOPOCORE_V5_DISABLED_BY_DEFAULT,
    TOPOCORE_V5_RUNTIME_REMOVED_REASON,
    TOPOCORE_V6_AUTHORITATIVE,
    get_topocore_deprecation_policy,
    is_deprecated_v5_allowed,
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
    monkeypatch.delenv("RB_TOPOCORE_V5_SIMULATE_DISABLED", raising=False)
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def test_deprecation_metadata_says_v6_is_authoritative() -> None:
    policy = get_topocore_deprecation_policy()

    assert TOPOCORE_V6_AUTHORITATIVE is True
    assert policy["topocore_v6_authoritative"] is True
    assert policy["legacy_runtime_removed"] is True


def test_deprecation_metadata_keeps_v5_disabled_by_default_after_runtime_removal() -> None:
    policy = get_topocore_deprecation_policy()

    assert TOPOCORE_V5_DISABLED_BY_DEFAULT is True
    assert policy["legacy_runtime_disabled_by_default"] is True
    assert policy["legacy_runtime_fallback_required"] is False


def test_allow_deprecated_v5_helper_still_only_reflects_env_request() -> None:
    assert is_deprecated_v5_allowed({}) is False
    assert is_deprecated_v5_allowed({"RB_TOPOCORE_ALLOW_DEPRECATED_V5": "1"}) is True


def test_explicit_v5_is_runtime_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert TOPOCORE_V5_RUNTIME_REMOVED_REASON in str(exc_info.value)


def test_legacy_lite_is_runtime_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "lite")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert LEGACY_LITE_DISABLED_REASON in str(exc_info.value)


def test_auto_with_v6_available_resolves_v6(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()

    result = tky_local.LocalTKYProvider().compress_context(
        question="Explain the provider path.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert result.compression_stats["resolved_backend"] == BACKEND_V6
    assert result.compression_stats["fallback_used"] is False
    assert result.compression_stats["deprecated_v5_allowed"] is False


def test_auto_with_v6_unavailable_does_not_fallback_to_v5(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Explain the provider path.",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    assert V6_UNAVAILABLE_V5_DISABLED_REASON in str(exc_info.value)


def test_allow_flag_does_not_reenable_removed_v5(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v5")
    monkeypatch.setenv("RB_TOPOCORE_ALLOW_DEPRECATED_V5", "1")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON in str(exc_info.value)


def test_legacy_gate_zero_style_v5_pin_is_unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend()

    assert "unsupported_legacy_backend" in str(exc_info.value)
