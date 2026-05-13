from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

import pytest

from repobrain.topocore_v6_decision_diff import (
    DecisionDiffCategory,
    DecisionDiffSeverity,
    RepoBrainV5DecisionSnapshot,
    RepoBrainV6DecisionDiffError,
    TopoCoreV6AdvisorySnapshot,
    build_decision_diff_report,
)


def test_aligned_ask_style_decision_produces_low_or_no_findings() -> None:
    report = build_decision_diff_report(
        v5_snapshot=RepoBrainV5DecisionSnapshot(
            command="ask",
            route="answer",
            selected_chunk_ids=("chunk-1", "chunk-2"),
        ),
        v6_advisory_snapshot=TopoCoreV6AdvisorySnapshot(
            status="ready",
            action="proceed",
            selected_chunk_ids=("chunk-1", "chunk-2"),
            task_type="ask",
        ),
    )

    payload = report.to_dict()
    rendered = json.dumps(payload, sort_keys=True)

    assert json.loads(rendered) == payload
    assert report.overall_severity in {DecisionDiffSeverity.INFO, DecisionDiffSeverity.LOW}
    assert "decide_raw" not in rendered
    assert "compression_stats" not in rendered
    assert "raw_query" not in rendered


def test_v6_more_conservative_than_v5_is_classified() -> None:
    report = build_decision_diff_report(
        v5_snapshot={"command": "review", "route": "proceed"},
        v6_advisory_snapshot={
            "status": "needs_more_information",
            "action": "investigate",
            "task_type": "review",
        },
    )

    categories = {item.category for item in report.findings}
    severities = {item.severity for item in report.findings}

    assert DecisionDiffCategory.V6_MORE_CONSERVATIVE in categories
    assert DecisionDiffCategory.NEEDS_MORE_INFORMATION_MISMATCH in categories
    assert severities <= {DecisionDiffSeverity.MEDIUM, DecisionDiffSeverity.HIGH, DecisionDiffSeverity.INFO, DecisionDiffSeverity.LOW}
    assert report.overall_severity in {DecisionDiffSeverity.MEDIUM, DecisionDiffSeverity.HIGH}


def test_v6_more_permissive_than_v5_is_classified_as_high_risk() -> None:
    report = build_decision_diff_report(
        v5_snapshot={
            "command": "fix",
            "route": "no_patch",
            "no_patch_reason": "insufficient localized evidence",
            "has_patch_candidate": False,
        },
        v6_advisory_snapshot={
            "status": "ready",
            "action": "proceed",
            "task_type": "fix",
        },
    )

    categories = {item.category for item in report.findings}

    assert DecisionDiffCategory.V6_MORE_PERMISSIVE in categories
    assert report.overall_severity == DecisionDiffSeverity.HIGH


def test_candidate_overlap_is_computed_safely() -> None:
    report = build_decision_diff_report(
        v5_snapshot=RepoBrainV5DecisionSnapshot(
            command="review",
            route="proceed",
            selected_chunk_ids=("chunk-a", "chunk-b", "chunk-c"),
        ),
        v6_advisory_snapshot=TopoCoreV6AdvisorySnapshot(
            status="ready",
            action="respond",
            selected_chunk_ids=("chunk-b", "chunk-x"),
            task_type="review",
        ),
    )

    payload = report.to_dict()
    rendered = json.dumps(payload, sort_keys=True)

    assert report.overlap_count == 1
    assert report.overlap_ids == ("chunk-b",)
    assert "chunk-b" in rendered
    assert "raw_code" not in rendered


def test_fix_governance_mismatch_is_detected() -> None:
    report = build_decision_diff_report(
        v5_snapshot={
            "command": "fix",
            "route": "no_patch",
            "no_patch_reason": "missing grounded localized target",
            "has_patch_candidate": False,
        },
        v6_advisory_snapshot={
            "status": "ready",
            "action": "proceed",
            "task_type": "fix",
        },
    )

    categories = {item.category for item in report.findings}

    assert DecisionDiffCategory.FIX_GOVERNANCE_MISMATCH in categories
    assert report.overall_severity == DecisionDiffSeverity.HIGH
    assert "apply_patch" not in json.dumps(report.to_dict(), sort_keys=True)


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "compression_stats",
        "trace",
        "raw_query",
        "raw_code",
        "prompt",
        "secret",
        "token",
        "api_key",
    ],
)
def test_forbidden_input_fields_are_rejected(forbidden_field: str) -> None:
    with pytest.raises(RepoBrainV6DecisionDiffError, match=forbidden_field):
        build_decision_diff_report(
            v5_snapshot={"command": "ask", "route": "answer", forbidden_field: "blocked"},
            v6_advisory_snapshot={"status": "ready", "action": "respond", "task_type": "ask"},
        )


def test_report_is_product_safe() -> None:
    report = build_decision_diff_report(
        v5_snapshot={"command": "review", "route": "proceed"},
        v6_advisory_snapshot={"status": "blocked", "action": "stop", "task_type": "review"},
    )

    rendered = json.dumps(report.to_dict(), sort_keys=True)

    for forbidden in (
        "decide_raw",
        "compression_stats",
        "raw_trace",
        "governance_internals",
        "event_internals",
        "artifact_internals",
        "raw_query",
        "raw_code",
        "secret",
        "token",
        "api_key",
    ):
        assert forbidden not in rendered


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
        assert "topocore_v6_decision_diff" not in content, path.as_posix()
        assert "build_decision_diff_report" not in content, path.as_posix()


def test_no_topocore_v6_dependency_required() -> None:
    sys.modules.pop("topocore_v6", None)
    module = importlib.import_module("repobrain.topocore_v6_decision_diff")

    assert hasattr(module, "build_decision_diff_report")
    assert "topocore_v6" not in module.__dict__
