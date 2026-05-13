from __future__ import annotations

from importlib import import_module
from pathlib import Path
import json

import pytest

from repobrain.topocore_v6_adapter import (
    RepoBrainTopoCoreV6Adapter,
    RepoBrainV6AdapterError,
    RepoBrainV6CandidateRef,
    RepoBrainV6SummaryBundle,
)


def _minimal_bundle(**overrides: object) -> RepoBrainV6SummaryBundle:
    bundle = RepoBrainV6SummaryBundle(
        query="Review the pull request risk profile.",
        intent_summary={
            "command": "review",
            "task_type_candidate": "review",
            "user_goal": "summarize PR risk",
        },
        candidates=(
            RepoBrainV6CandidateRef(
                chunk_id="chunk-1",
                score_local=0.91,
                metadata={"path": "repobrain/review.py"},
            ),
        ),
    )
    if not overrides:
        return bundle

    payload = {
        "query": bundle.query,
        "intent_summary": bundle.intent_summary,
        "candidates": bundle.candidates,
        "task_type": bundle.task_type,
        "limits": bundle.limits,
        "pr_context_summary": bundle.pr_context_summary,
        "evidence_summary": bundle.evidence_summary,
        "unknowns_summary": bundle.unknowns_summary,
        "risk_items": bundle.risk_items,
        "review_draft_summary": bundle.review_draft_summary,
        "fix_draft_summary": bundle.fix_draft_summary,
        "verification_results": bundle.verification_results,
        "project_audit_scorecard": bundle.project_audit_scorecard,
        "project_audit_findings": bundle.project_audit_findings,
        "scenario_branches": bundle.scenario_branches,
    }
    payload.update(overrides)
    return RepoBrainV6SummaryBundle(**payload)


def test_adapter_builds_future_request_preview_from_minimal_summaries() -> None:
    adapter = RepoBrainTopoCoreV6Adapter()

    preview = adapter.build_request_preview(_minimal_bundle()).to_dict()

    assert preview["task_type"] == "review"
    assert preview["query"] == "Review the pull request risk profile."
    assert "candidates" in preview
    assert "limits" in preview
    assert "policy" in preview


def test_adapter_maps_summary_families_into_policy_payloads() -> None:
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _minimal_bundle(
        pr_context_summary={"pr_state": "OPEN"},
        evidence_summary={"confirmed_facts": ["tests are green"]},
        unknowns_summary={"unknowns": ["missing benchmark"]},
        risk_items=({"risk_area": "review", "severity_hint": "low"},),
        review_draft_summary={"review_focus": "diff scope"},
        fix_draft_summary={"no_patch_reason": "review only"},
        verification_results={"checks": ["test: pass"]},
        project_audit_scorecard={"structure": "stable"},
        project_audit_findings=({"finding": "no adapter wiring"},),
        scenario_branches=({"name": "shadow-mode-later"},),
    )

    policy = adapter.build_request_preview(bundle).to_dict()["policy"]

    assert policy["intent_summary"]["command"] == "review"
    assert policy["pr_context_summary"]["pr_state"] == "OPEN"
    assert policy["evidence_summary"]["confirmed_facts"] == ["tests are green"]
    assert policy["unknowns_summary"]["unknowns"] == ["missing benchmark"]
    assert policy["risk_items"][0]["risk_area"] == "review"
    assert policy["review_draft_summary"]["review_focus"] == "diff scope"
    assert policy["fix_draft_summary"]["no_patch_reason"] == "review only"
    assert policy["verification_results"]["checks"] == ["test: pass"]
    assert policy["project_audit_scorecard"]["structure"] == "stable"
    assert policy["project_audit_findings"][0]["finding"] == "no adapter wiring"
    assert policy["scenario_branches"][0]["name"] == "shadow-mode-later"


def test_adapter_preserves_safe_candidate_ids_and_scores() -> None:
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _minimal_bundle(
        candidates=(
            RepoBrainV6CandidateRef(
                chunk_id="chunk-7",
                score_local=0.42,
                metadata={"path": "repobrain/output_md.py", "kind": "diff"},
            ),
        )
    )

    candidates = adapter.build_request_preview(bundle).to_dict()["candidates"]

    assert candidates == [
        {
            "chunk_id": "chunk-7",
            "score_local": 0.42,
            "metadata": {
                "path": "repobrain/output_md.py",
                "kind": "diff",
            },
        }
    ]


@pytest.mark.parametrize(
    "unsafe_key",
    ["raw_text", "raw_code", "prompt", "secret", "token", "api_key"],
)
def test_adapter_blocks_unsafe_raw_candidate_metadata(unsafe_key: str) -> None:
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _minimal_bundle(
        candidates=(
            RepoBrainV6CandidateRef(
                chunk_id="chunk-unsafe",
                score_local=0.2,
                metadata={unsafe_key: "blocked"},
            ),
        )
    )

    with pytest.raises(RepoBrainV6AdapterError, match=unsafe_key):
        adapter.build_request_preview(bundle)


def test_adapter_does_not_require_topocore_v6() -> None:
    module = import_module("repobrain.topocore_v6_adapter")

    assert hasattr(module, "RepoBrainTopoCoreV6Adapter")
    assert "topocore_v6" not in module.__dict__


def test_adapter_does_not_expose_raw_decision_internals() -> None:
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _minimal_bundle(
        evidence_summary={
            "confirmed_facts": ["one file changed"],
            "decide_raw": {"should": "not leak"},
            "compression_stats": {"ratio": 0.1},
        },
        unknowns_summary={
            "raw_query": "hidden",
            "trace_internals": {"trace": "hidden"},
        },
        review_draft_summary={
            "review_focus": "bounded",
            "governance_internals": {"internal": True},
        },
    )

    payload = adapter.build_request_preview(bundle).to_dict()
    rendered = json.dumps(payload, sort_keys=True)

    assert "decide_raw" not in rendered
    assert "compression_stats" not in rendered
    assert "governance_internals" not in rendered
    assert "trace_internals" not in rendered
    assert "raw_query" not in rendered
    assert payload["query"] == "Review the pull request risk profile."


def test_adapter_is_not_wired_into_current_runtime_paths() -> None:
    root = Path(__file__).resolve().parents[1]
    target_paths = [
        root / "repobrain" / "github_flow.py",
        root / "repobrain" / "tky_local.py",
        root / "repobrain" / "tkya" / "engine.py",
        root / "action.yml",
        root / ".github" / "workflows" / "repobrain.yml",
    ]

    for path in target_paths:
        content = path.read_text(encoding="utf-8")
        assert "RepoBrainTopoCoreV6Adapter" not in content, path.as_posix()
        assert "topocore_v6_adapter" not in content, path.as_posix()
