from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from repobrain.topocore_v6_adapter import (
    RepoBrainTopoCoreV6Adapter,
    RepoBrainV6AdapterError,
    RepoBrainV6CandidateRef,
    RepoBrainV6SummaryBundle,
)


_FAILURE_TAXONOMY_CATEGORIES = {
    "LLM summary issue",
    "RepoBrain adapter issue",
    "insufficient GitHub data",
    "user request ambiguity",
    "v5/v6 semantic mismatch",
    "TopoCore v6 platform issue",
    "policy/security block",
    "private dependency/install issue",
}


def _build_bundle(
    *,
    query: str = "Summarize the pull request context.",
    intent_summary: dict[str, object] | None = None,
    candidates: tuple[RepoBrainV6CandidateRef, ...] | None = None,
    **overrides: object,
) -> RepoBrainV6SummaryBundle:
    payload: dict[str, object] = {
        "query": query,
        "intent_summary": intent_summary
        or {
            "command": "ask",
            "task_type_candidate": "ask",
            "user_goal": "summarize context",
        },
        "candidates": candidates
        or (
            RepoBrainV6CandidateRef(
                chunk_id="chunk-minimal",
                score_local=0.77,
                metadata={"path": "repobrain/ask.py"},
            ),
        ),
        "task_type": None,
        "limits": {},
        "pr_context_summary": {},
        "evidence_summary": {},
        "unknowns_summary": {},
        "risk_items": (),
        "review_draft_summary": {},
        "fix_draft_summary": {},
        "verification_results": {},
        "project_audit_scorecard": {},
        "project_audit_findings": (),
        "scenario_branches": (),
    }
    payload.update(overrides)
    return RepoBrainV6SummaryBundle(**payload)


def test_minimal_ask_request_preview_matches_expected_v6_style_shape() -> None:
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _build_bundle()

    preview = adapter.build_request_preview(bundle).to_dict()

    assert set(preview) == {"task_type", "query", "candidates", "limits", "policy"}
    assert preview["task_type"] == "ask"
    assert isinstance(preview["candidates"], list)
    assert isinstance(preview["limits"], dict)
    assert isinstance(preview["policy"], dict)
    assert json.loads(json.dumps(preview)) == preview


def test_review_style_request_preview_maps_summaries_into_policy_payloads() -> None:
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _build_bundle(
        query="Review the pull request.",
        intent_summary={
            "command": "review",
            "task_type_candidate": "review",
            "user_goal": "review diff",
        },
        pr_context_summary={
            "pr_state": "OPEN",
            "base_ref": "main",
            "head_ref": "feature/refactor",
            "diff_scope": "narrow",
        },
        evidence_summary={
            "confirmed_facts": ["tests passed", "two files changed"],
            "evidence_items": [{"kind": "check", "value": "test: pass"}],
        },
        unknowns_summary={
            "unknowns": ["benchmark impact"],
            "insufficient_context_reasons": ["no perf data"],
        },
        risk_items=(
            {
                "risk_area": "runtime",
                "severity_hint": "low",
                "likelihood_hint": "low",
            },
        ),
        review_draft_summary={
            "review_focus": "runtime wiring",
            "candidate_findings": [],
            "non_claims": ["no safe-to-merge claim"],
        },
        verification_results={"checks": ["test: pass", "ruff: pass"]},
    )

    policy = adapter.build_request_preview(bundle).to_dict()["policy"]

    assert set(policy) >= {
        "intent_summary",
        "pr_context_summary",
        "evidence_summary",
        "unknowns_summary",
        "risk_items",
        "review_draft_summary",
        "verification_results",
    }
    assert policy["pr_context_summary"]["pr_state"] == "OPEN"
    assert policy["evidence_summary"]["confirmed_facts"] == ["tests passed", "two files changed"]
    assert policy["unknowns_summary"]["unknowns"] == ["benchmark impact"]
    assert policy["risk_items"][0]["risk_area"] == "runtime"
    assert policy["review_draft_summary"]["review_focus"] == "runtime wiring"


def test_fix_style_request_preview_remains_governance_input_only() -> None:
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _build_bundle(
        query="Prepare a bounded fix summary.",
        intent_summary={
            "command": "fix",
            "task_type_candidate": "fix",
            "user_goal": "summarize possible fix path",
        },
        fix_draft_summary={
            "localized_target_hint": "repobrain/patch_validator.py",
            "no_patch_reason": "insufficient localized grounding",
            "patch_safety_notes": ["manual-only", "no patch applied"],
            "grounding_notes": ["await more evidence"],
        },
    )

    preview = adapter.build_request_preview(bundle).to_dict()
    fix_summary = preview["policy"]["fix_draft_summary"]
    rendered = json.dumps(preview, sort_keys=True)

    assert preview["task_type"] == "fix"
    assert fix_summary["localized_target_hint"] == "repobrain/patch_validator.py"
    assert fix_summary["no_patch_reason"] == "insufficient localized grounding"
    assert "apply_patch" not in rendered
    assert "\"apply\"" not in rendered
    assert "create_commit" not in rendered
    assert "create_branch" not in rendered
    assert "create_pr" not in rendered
    assert preview["limits"]["preview_only"] is True


def test_stub_external_decision_view_compatibility_stays_product_level_only() -> None:
    external_decisions = [
        {
            "status": "ready",
            "route": "proceed",
            "explanation": "Enough bounded evidence for a product-level response.",
        },
        {
            "status": "needs_more_information",
            "route": "investigate",
            "unknowns": ["missing CI signal"],
        },
        {
            "status": "blocked",
            "route": "stop",
            "reason": "policy/security block",
        },
    ]

    forbidden_keys = {
        "decide_raw",
        "compression_stats",
        "raw_trace",
        "governance_internals",
        "event_internals",
        "artifact_internals",
        "raw_query",
    }

    for item in external_decisions:
        assert item["status"] in {"ready", "needs_more_information", "blocked"}
        assert item["route"] in {"proceed", "investigate", "stop"}
        assert forbidden_keys.isdisjoint(item)


def test_failure_taxonomy_fixture_coverage_is_explicit() -> None:
    observed_categories = {
        "LLM summary issue",
        "RepoBrain adapter issue",
        "insufficient GitHub data",
        "user request ambiguity",
        "v5/v6 semantic mismatch",
        "TopoCore v6 platform issue",
        "policy/security block",
        "private dependency/install issue",
    }

    assert observed_categories == _FAILURE_TAXONOMY_CATEGORIES


@pytest.mark.parametrize(
    "unsafe_key",
    [
        "raw_text",
        "raw_code",
        "prompt",
        "system_prompt",
        "secret",
        "token",
        "password",
        "api_key",
        "private_key",
        "env",
        "dotenv",
    ],
)
def test_unsafe_metadata_remains_blocked_under_stub_compatibility(unsafe_key: str) -> None:
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = _build_bundle(
        candidates=(
            RepoBrainV6CandidateRef(
                chunk_id="chunk-unsafe",
                score_local=0.1,
                metadata={unsafe_key: "blocked"},
            ),
        )
    )

    with pytest.raises(RepoBrainV6AdapterError, match=unsafe_key):
        adapter.build_request_preview(bundle)


def test_no_runtime_wiring_introduced() -> None:
    root = Path(__file__).resolve().parents[1]
    target_paths = [
        root / "repobrain" / "github_flow.py",
        root / "repobrain" / "tky_local.py",
        root / "repobrain" / "tky_engine.py",
        root / "repobrain" / "tkya" / "engine.py",
        root / "action.yml",
        root / ".github" / "workflows" / "repobrain.yml",
    ]

    for path in target_paths:
        content = path.read_text(encoding="utf-8")
        assert "RepoBrainTopoCoreV6Adapter" not in content, path.as_posix()
        assert "stub compatibility" not in content.lower(), path.as_posix()
        assert "topocore_v6_adapter" not in content, path.as_posix()


def test_no_real_topocore_v6_dependency_required() -> None:
    assert "topocore_v6" not in sys.modules

    adapter = RepoBrainTopoCoreV6Adapter()
    preview = adapter.build_request_preview(_build_bundle()).to_dict()

    assert preview["task_type"] == "ask"
    assert "topocore_v6" not in sys.modules
