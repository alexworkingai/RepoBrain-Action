import importlib
import json
from pathlib import Path

import pytest

from repobrain.topocore_v6_advisory_artifact import (
    AdvisoryArtifactError,
    AdvisoryArtifactMetadata,
    assert_advisory_artifact_safe,
    build_advisory_artifact,
)
from repobrain.topocore_v6_decision_diff import build_decision_diff_report


def _safe_v5_snapshot(**overrides):
    payload = {
        "command": "ask",
        "route": "proceed",
        "selected_chunk_ids": ["chunk-1"],
        "execution_mode": "manual_local",
        "llm_intent": "answer_question",
        "llm_decision_reason_code": "aligned",
        "verification_gate_decision": "pass",
        "verification_gate_reason": "fixture_safe",
        "safe_reason_code": "safe_aligned",
        "has_patch_candidate": False,
        "no_patch_reason": "",
    }
    payload.update(overrides)
    return payload


def _safe_v6_snapshot(**overrides):
    payload = {
        "status": "ready",
        "action": "proceed",
        "selected_chunk_ids": ["chunk-1"],
        "safe_reason_code": "safe_aligned",
        "needs_more_information_reason": "",
        "blocked_reason_code": "",
        "confidence_hint": "medium",
        "task_type": "ask",
    }
    payload.update(overrides)
    return payload


def _safe_decision_diff(severity="low", category="aligned", **overrides):
    payload = {
        "overall_severity": severity,
        "command": "ask",
        "task_type": "ask",
        "v5_route": "proceed",
        "v6_status": "ready",
        "v6_action": "proceed",
        "overlap_count": 1,
        "v5_selected_count": 1,
        "v6_selected_count": 1,
        "overlap_ids": ["chunk-1"],
        "findings": [
            {
                "category": category,
                "severity": severity,
                "message": "safe diff fixture",
                "details": {"overlap_count": 1, "overlap_ids": ["chunk-1"]},
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_builds_minimal_advisory_artifact():
    artifact = build_advisory_artifact(
        v5_primary_snapshot=_safe_v5_snapshot(),
        v6_advisory_snapshot=_safe_v6_snapshot(),
        decision_diff=_safe_decision_diff(),
        metadata=AdvisoryArtifactMetadata(mode="manual_local", command="ask"),
    )

    payload = artifact.to_dict()
    json.dumps(payload)

    assert payload["schema_version"] == "topocore-v6-advisory-artifact/v1"
    assert payload["artifact_kind"] == "topocore_v6_advisory"
    assert payload["mode"] == "manual_local"
    assert payload["command"] == "ask"
    assert "raw_query" not in payload["v5_primary_snapshot"]
    assert "raw_query" not in payload["v6_advisory_snapshot"]
    assert "raw_query" not in payload["decision_diff"]


@pytest.mark.parametrize(
    ("severity", "expected_hint"),
    [
        ("info", "go_candidate"),
        ("low", "go_candidate"),
        ("medium", "needs_review"),
        ("high", "blocked"),
    ],
)
def test_severity_maps_to_go_no_go_hint(severity, expected_hint):
    artifact = build_advisory_artifact(
        v5_primary_snapshot=_safe_v5_snapshot(),
        v6_advisory_snapshot=_safe_v6_snapshot(),
        decision_diff=_safe_decision_diff(severity=severity),
        metadata={"mode": "manual_local", "command": "ask"},
    )

    assert artifact.to_dict()["classification"]["go_no_go_hint"] == expected_hint


@pytest.mark.parametrize(
    ("severity", "expected_hint"),
    [("medium", "needs_review"), ("high", "blocked")],
)
def test_fix_governance_cannot_become_go_candidate_on_mismatch(severity, expected_hint):
    artifact = build_advisory_artifact(
        v5_primary_snapshot=_safe_v5_snapshot(command="fix", route="no_patch", no_patch_reason="no_localized_target"),
        v6_advisory_snapshot=_safe_v6_snapshot(task_type="fix", status="ready", action="proceed"),
        decision_diff=_safe_decision_diff(severity=severity, category="fix_governance_mismatch"),
        metadata={"mode": "manual_local", "command": "fix"},
    )

    payload = artifact.to_dict()
    assert payload["classification"]["go_no_go_hint"] == expected_hint
    serialized = json.dumps(payload)
    assert "authorize_patch" not in serialized
    assert "create_commit" not in serialized
    assert "create_branch" not in serialized
    assert "create_pr" not in serialized


@pytest.mark.parametrize(
    "field_name",
    [
        "compression_stats",
        "trace",
        "raw_query",
        "raw_code",
        "raw_diff",
        "prompt",
        "system_prompt",
        "secret",
        "token",
        "api_key",
        "private_key",
        "dotenv",
    ],
)
def test_forbidden_raw_fields_are_rejected(field_name):
    v5_snapshot = _safe_v5_snapshot()
    v5_snapshot[field_name] = "unsafe"

    with pytest.raises(AdvisoryArtifactError):
        build_advisory_artifact(
            v5_primary_snapshot=v5_snapshot,
            v6_advisory_snapshot=_safe_v6_snapshot(),
            decision_diff=_safe_decision_diff(),
            metadata={"mode": "manual_local", "command": "ask"},
        )


def test_decision_diff_report_can_be_embedded_safely():
    report = build_decision_diff_report(
        v5_snapshot=_safe_v5_snapshot(selected_chunk_ids=["chunk-1", "chunk-2"]),
        v6_advisory_snapshot=_safe_v6_snapshot(selected_chunk_ids=["chunk-2", "chunk-3"]),
    )

    artifact = build_advisory_artifact(
        v5_primary_snapshot=_safe_v5_snapshot(selected_chunk_ids=["chunk-1", "chunk-2"]),
        v6_advisory_snapshot=_safe_v6_snapshot(selected_chunk_ids=["chunk-2", "chunk-3"]),
        decision_diff=report,
        metadata={"mode": "manual_local", "command": "review", "fixture_name": "review-like"},
    )

    payload = artifact.to_dict()
    json.dumps(payload)

    assert payload["decision_diff"]["overlap_count"] == 1
    assert payload["decision_diff"]["overlap_ids"] == ["chunk-2"]
    assert payload["fixture_name"] == "review-like"
    assert_advisory_artifact_safe(artifact)


def test_retention_defaults_are_conservative():
    artifact = build_advisory_artifact(
        v5_primary_snapshot=_safe_v5_snapshot(),
        v6_advisory_snapshot=_safe_v6_snapshot(),
        decision_diff=_safe_decision_diff(),
        metadata={"mode": "future_shadow_advisory", "command": "review"},
    )

    retention = artifact.to_dict()["retention"]
    assert retention["default_scope"] == "manual_local_only"
    assert retention["default_persist"] is False
    assert retention["future_shadow_persist_allowed"] is False


def test_artifact_safety_flags_remain_false():
    artifact = build_advisory_artifact(
        v5_primary_snapshot=_safe_v5_snapshot(),
        v6_advisory_snapshot=_safe_v6_snapshot(),
        decision_diff=_safe_decision_diff(),
        metadata={"mode": "manual_local", "command": "ask"},
    )

    safety = artifact.to_dict()["safety"]
    assert safety["contains_raw_query"] is False
    assert safety["contains_raw_code"] is False
    assert safety["contains_decide_raw"] is False
    assert safety["contains_secrets"] is False


def test_no_runtime_wiring_introduced():
    artifact_helper_name = "topocore_v6_advisory_artifact"
    files_to_check = [
        "repobrain/github_flow.py",
        "repobrain/tky_local.py",
        "repobrain/tky_engine.py",
        "repobrain/tkya/engine.py",
        "action.yml",
        ".github/workflows/repobrain.yml",
    ]
    for rel_path in files_to_check:
        text = Path(rel_path).read_text(encoding="utf-8")
        assert artifact_helper_name not in text


def test_no_topocore_v6_dependency_required():
    module = importlib.import_module("repobrain.topocore_v6_advisory_artifact")
    assert hasattr(module, "build_advisory_artifact")
