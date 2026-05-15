from __future__ import annotations

import importlib
import importlib.util
import io
import json
import re
import sys
import types
from pathlib import Path

import pytest

from repobrain.topocore_v6_adapter import (
    RepoBrainTopoCoreV6Adapter,
    RepoBrainV6AdapterError,
    RepoBrainV6AdapterRuntimeError,
    RepoBrainV6CandidateRef,
    RepoBrainV6SummaryBundle,
)


_ROOT = Path(__file__).resolve().parents[1]


def _build_bundle(**overrides: object) -> RepoBrainV6SummaryBundle:
    payload: dict[str, object] = {
        "query": "Review the bounded adapter contract mapping.",
        "intent_summary": {
            "command": "review",
            "task_type_candidate": "review",
            "user_goal": "map safe adapter contract",
        },
        "candidates": (
            RepoBrainV6CandidateRef(
                chunk_id="chunk-1",
                score_local=0.92,
                metadata={"path": "repobrain/topocore_v6_adapter.py"},
            ),
        ),
        "task_type": None,
        "limits": {},
        "pr_context_summary": {"pr_state": "OPEN"},
        "evidence_summary": {"confirmed_facts": ["adapter contract inspected"]},
        "unknowns_summary": {"unknowns": ["real backend switch still pending"]},
        "risk_items": ({"risk_area": "adapter", "severity_hint": "low"},),
        "review_draft_summary": {"review_focus": "contract-safe mapping"},
        "fix_draft_summary": {"no_patch_reason": "review-only"},
        "verification_results": {"checks": ["pytest: pass"]},
        "project_audit_scorecard": {"stability": "planned"},
        "project_audit_findings": ({"finding": "no runtime wiring yet"},),
        "scenario_branches": ({"name": "runtime-switch-later"},),
    }
    payload.update(overrides)
    return RepoBrainV6SummaryBundle(**payload)


def _build_fake_topocore_v6_module(
    *,
    missing_symbols: set[str] | None = None,
    include_decide_raw_guard: bool = False,
) -> types.ModuleType:
    missing_symbols = missing_symbols or set()

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
            self.reference_hash = "ref-123"
            self.selected_count = 1
            self.blocked = False
            self.confidence_band = "high"
            self.message_code = "DECISION_READY"

    class FakeFacade:
        def health(self) -> dict[str, object]:
            return {"status": "ok"}

        def decide_external(self, request: EngineRequest) -> ExternalDecisionView:
            assert request.task_type
            assert request.query.text
            return ExternalDecisionView()

        if include_decide_raw_guard:
            @property
            def decide_raw(self) -> object:
                raise AssertionError("decide_raw should never be accessed")

    fake_module = types.ModuleType("topocore_v6")
    fake_module.__version__ = "0.0.fake"

    if "create_topocore" not in missing_symbols:
        fake_module.create_topocore = lambda: FakeFacade()
    if "EngineRequest" not in missing_symbols:
        fake_module.EngineRequest = EngineRequest
    if "EngineQuery" not in missing_symbols:
        fake_module.EngineQuery = EngineQuery
    if "EngineCandidate" not in missing_symbols:
        fake_module.EngineCandidate = EngineCandidate
    if "ExternalDecisionView" not in missing_symbols:
        fake_module.ExternalDecisionView = ExternalDecisionView

    return fake_module


@pytest.fixture(autouse=True)
def _clear_topocore_module() -> None:
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def test_adapter_module_import_remains_dependency_free() -> None:
    sys.modules.pop("topocore_v6", None)
    module = importlib.import_module("repobrain.topocore_v6_adapter")

    assert hasattr(module, "RepoBrainTopoCoreV6Adapter")
    assert "topocore_v6" not in module.__dict__
    assert "topocore_v6" not in sys.modules


def test_real_engine_request_built_with_fake_public_api() -> None:
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _build_bundle(
        task_type="review",
        candidates=(
            RepoBrainV6CandidateRef(
                chunk_id="chunk-7",
                score_local=0.44,
                signature=[1, 2, 3],
                file_path="repobrain/topocore_v6_adapter.py",
                line_start=10,
                line_end=22,
                metadata={"kind": "diff"},
            ),
        ),
        limits={"max_candidates": 3, "preview_only": False},
    )

    request_bundle = adapter.build_real_engine_request(bundle)

    assert request_bundle.engine_query.text == bundle.query
    assert request_bundle.engine_request.task_type == "review"
    assert request_bundle.engine_request.limits["max_candidates"] == 3
    assert request_bundle.engine_request.limits["preview_only"] is False
    assert request_bundle.engine_request.policy == request_bundle.policy


def test_candidate_mapping_uses_supported_fields_only() -> None:
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _build_bundle(
        candidates=(
            RepoBrainV6CandidateRef(
                chunk_id="chunk-2",
                score_local=0.51,
                signature=[9, 8],
                file_path="repobrain/output_md.py",
                line_start=2,
                line_end=4,
                metadata={"kind": "diff", "extra_safe_context": "ignored"},
            ),
        )
    )

    request_bundle = adapter.build_real_engine_request(bundle)
    candidate = request_bundle.engine_candidates[0]
    safe_candidate = request_bundle.candidates[0]

    assert candidate.chunk_id == "chunk-2"
    assert candidate.score_local == 0.51
    assert candidate.signature == [9, 8]
    assert candidate.file_path == "repobrain/output_md.py"
    assert candidate.line_start == 2
    assert candidate.line_end == 4
    assert "metadata" not in safe_candidate
    assert set(safe_candidate) == {
        "chunk_id",
        "score_local",
        "signature",
        "file_path",
        "line_start",
        "line_end",
    }


@pytest.mark.parametrize(
    "unsafe_key",
    [
        "raw_text",
        "raw_code",
        "prompt",
        "secret",
        "token",
        "api_key",
        "password",
        "private_key",
        "dotenv",
        ".env",
    ],
)
def test_unsafe_candidate_metadata_rejected(unsafe_key: str) -> None:
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _build_bundle(
        candidates=(
            RepoBrainV6CandidateRef(
                chunk_id="chunk-unsafe",
                score_local=0.1,
                metadata={unsafe_key: "blocked-value"},
            ),
        )
    )

    with pytest.raises(RepoBrainV6AdapterError, match=re.escape(unsafe_key)):
        adapter.build_real_engine_request(bundle)


def test_policy_summary_mapping_uses_real_v6_keys() -> None:
    adapter = RepoBrainTopoCoreV6Adapter()
    policy = adapter.build_real_policy_payload(_build_bundle())

    assert set(policy) == {
        "evidence_summary",
        "bit_matrix_summary",
        "verification_summary",
        "project_audit_summary",
        "risk_summary",
        "scenario_summary",
    }
    serialized = json.dumps(policy, sort_keys=True)
    assert "raw_query" not in serialized
    assert "raw_code" not in serialized
    assert "raw_diff" not in serialized
    assert "prompt" not in serialized
    assert "system_prompt" not in serialized
    assert "decide_raw" not in serialized
    assert "compression_stats" not in serialized


def test_decide_external_local_uses_fake_facade_safely() -> None:
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()
    adapter = RepoBrainTopoCoreV6Adapter()

    decision = adapter.decide_external_local(_build_bundle())

    assert decision.to_dict() == {
        "status": "ready",
        "action": "proceed",
        "reference_hash": "ref-123",
        "selected_count": 1,
        "blocked": False,
        "confidence_band": "high",
        "message_code": "DECISION_READY",
    }


def test_decide_raw_is_never_called() -> None:
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(include_decide_raw_guard=True)
    adapter = RepoBrainTopoCoreV6Adapter()

    decision = adapter.decide_external_local(_build_bundle())

    assert decision.status == "ready"


def test_missing_dependency_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = RepoBrainTopoCoreV6Adapter()

    def _raise_import(name: str) -> object:
        raise ModuleNotFoundError(r"topocore_v6 missing from C:\Private\TopoCore\src")

    monkeypatch.setattr(
        "repobrain.topocore_v6_adapter.importlib.import_module",
        _raise_import,
    )

    with pytest.raises(RepoBrainV6AdapterRuntimeError) as exc_info:
        adapter.decide_external_local(_build_bundle())

    message = str(exc_info.value)
    assert "unavailable" in message.lower()
    assert r"C:\Private\TopoCore\src" not in message


def test_api_mismatch_reported_safely() -> None:
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(missing_symbols={"EngineCandidate"})
    adapter = RepoBrainTopoCoreV6Adapter()

    with pytest.raises(RepoBrainV6AdapterRuntimeError) as exc_info:
        adapter.build_real_engine_request(_build_bundle())

    message = str(exc_info.value)
    assert "missing required symbols" in message
    assert "EngineCandidate" in message


def test_existing_preview_behavior_still_works() -> None:
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _build_bundle(
        evidence_summary={
            "confirmed_facts": ["still preview-safe"],
            "decide_raw": {"should": "not leak"},
            "compression_stats": {"ratio": 0.1},
        }
    )

    preview = adapter.build_request_preview(bundle).to_dict()
    rendered = json.dumps(preview, sort_keys=True)

    assert preview["task_type"] == "review"
    assert json.loads(json.dumps(preview)) == preview
    assert "decide_raw" not in rendered
    assert "compression_stats" not in rendered


def test_no_runtime_wiring_introduced() -> None:
    for relative_path in (
        "repobrain/github_flow.py",
        "repobrain/tky_local.py",
        "repobrain/tky_engine.py",
        "repobrain/tkya/engine.py",
        "action.yml",
        ".github/workflows/repobrain.yml",
    ):
        text = (_ROOT / relative_path).read_text(encoding="utf-8")
        assert "decide_external_local" not in text
        assert "load_topocore_v6_public_api" not in text


def test_manual_harness_default_remains_unchanged() -> None:
    script_path = _ROOT / "scripts" / "validate_topocore_v6_local.py"
    spec = importlib.util.spec_from_file_location("validate_topocore_v6_local_adapter_real_test", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    buffer = io.StringIO()
    code = module.main(env={}, stdout=buffer)
    assert code == 0
    assert (
        buffer.getvalue().strip()
        == "TopoCore v6 local validation skipped: set RB_TOPOCORE_V6_LOCAL_VALIDATE=1 to run."
    )


def test_contract_probe_default_remains_unchanged() -> None:
    script_path = _ROOT / "scripts" / "probe_topocore_v6_contract.py"
    spec = importlib.util.spec_from_file_location("probe_topocore_v6_contract_adapter_real_test", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    buffer = io.StringIO()
    code = module.main(env={}, stdout=buffer)
    assert code == 0
    assert (
        buffer.getvalue().strip()
        == "TopoCore v6 contract probe skipped: set RB_TOPOCORE_V6_CONTRACT_PROBE=1 to run."
    )
