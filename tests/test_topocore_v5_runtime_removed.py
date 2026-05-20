from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

import repobrain.tky_local as tky_local
from repobrain.topocore_backend import TopoCoreBackendError, V6_UNAVAILABLE_V5_DISABLED_REASON, resolve_backend
from repobrain.topocore_deprecation import (
    TOPOCORE_LEGACY_LITE_REMOVED_REASON,
    TOPOCORE_UNSUPPORTED_LEGACY_BACKEND_REASON,
    TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON,
    TOPOCORE_V5_RUNTIME_REMOVED_REASON,
    get_topocore_deprecation_policy,
)
from repobrain.tky_provider import CandidateChunk


_ROOT = Path(__file__).resolve().parents[1]


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
    for name in (
        "RB_TOPOCORE_BACKEND",
        "RB_TKYA_BACKEND",
        "RB_TOPOCORE_V6_REQUIRE_LOCAL",
        "RB_TOPOCORE_V6_LOCAL_PATH",
        "RB_TOPOCORE_ALLOW_DEPRECATED_V5",
        "RB_TOPOCORE_V5_SIMULATE_DISABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def test_metadata_says_v5_runtime_removed() -> None:
    policy = get_topocore_deprecation_policy()

    assert policy["legacy_runtime_removed"] is True
    assert policy["legacy_runtime_fallback_required"] is False
    assert policy["topocore_v6_authoritative"] is True


def test_allow_env_does_not_reenable_v5() -> None:
    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend(
            env={
                "RB_TOPOCORE_BACKEND": "v5",
                "RB_TOPOCORE_ALLOW_DEPRECATED_V5": "1",
            }
        )

    assert TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON in str(exc_info.value)


def test_explicit_v5_is_unsupported() -> None:
    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend(env={"RB_TOPOCORE_BACKEND": "v5"})
    assert TOPOCORE_V5_RUNTIME_REMOVED_REASON in str(exc_info.value)


def test_legacy_rb_tkya_backend_v5_is_unsupported() -> None:
    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend(env={"RB_TKYA_BACKEND": "v5"})
    assert TOPOCORE_UNSUPPORTED_LEGACY_BACKEND_REASON in str(exc_info.value)


def test_legacy_rb_tkya_backend_lite_is_unsupported() -> None:
    with pytest.raises(TopoCoreBackendError) as exc_info:
        resolve_backend(env={"RB_TKYA_BACKEND": "lite"})
    assert TOPOCORE_LEGACY_LITE_REMOVED_REASON in str(exc_info.value)


def test_auto_with_v6_available_resolves_v6(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()

    result = tky_local.LocalTKYProvider().compress_context(
        question="Explain the provider path.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert result.compression_stats["resolved_backend"] == "v6"
    assert result.compression_stats["fallback_used"] is False


def test_auto_with_v6_unavailable_fails_without_v5_fallback() -> None:
    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Explain the provider path.",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    assert V6_UNAVAILABLE_V5_DISABLED_REASON in str(exc_info.value)


def test_explicit_v6_with_v6_unavailable_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")

    with pytest.raises(TopoCoreBackendError) as exc_info:
        tky_local.LocalTKYProvider().compress_context(
            question="Explain the provider path.",
            candidates=_sample_candidates(),
            limits={"task_type": "ask"},
        )

    assert "v6_required" in str(exc_info.value)


def test_tkya_engine_module_is_stubbed_not_executable() -> None:
    text = (_ROOT / "repobrain" / "tkya" / "engine.py").read_text(encoding="utf-8")
    assert "DeprecatedV5RuntimeRemovedError" in text
    assert "fallback to lite backend" not in text


def test_action_and_workflow_no_longer_advertise_v5_or_lite_as_supported_topocore_backends() -> None:
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8")
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "v5, v6, or auto" not in action_text
    assert '- v5' not in workflow_text
    assert '- lite' not in workflow_text


def test_changed_runtime_paths_do_not_introduce_decide_raw_or_patch_behavior() -> None:
    combined = "\n".join(
        (_ROOT / path).read_text(encoding="utf-8")
        for path in (
            "repobrain/topocore_deprecation.py",
            "repobrain/topocore_backend.py",
            "repobrain/tky_local.py",
            "repobrain/tkya/engine.py",
        )
    )
    assert "decide_raw(" not in combined
    assert "apply_patch" not in combined
    assert "gh pr create" not in combined
