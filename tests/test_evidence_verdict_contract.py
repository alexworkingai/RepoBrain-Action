from __future__ import annotations

from repobrain.output_md import render_patch_markdown, render_review_markdown
from repobrain.review_validator import validate_review_findings


def _primary(md: str) -> str:
    return md.split("<details>", 1)[0]


def test_review_validator_emits_evidence_verdict_contract_fields() -> None:
    validated = validate_review_findings(
        {
            "summary_text": "Review summary.",
            "risk_items": [
                {
                    "message": "Merge conflict markers present",
                    "severity": "high",
                    "evidence": [{"kind": "patch", "path": "repobrain/github_flow.py", "source": "patch_scan"}],
                }
            ],
        }
    )

    verdicts = validated.get("evidence_verdicts", [])
    assert isinstance(verdicts, list) and verdicts
    verdict = verdicts[0]
    assert verdict["claim"] == "Merge conflict markers present"
    assert verdict["evidence_anchors"] == ["repobrain/github_flow.py"]
    assert verdict["confidence"] in {"medium", "high"}
    assert verdict["impact"] == "high"
    assert verdict["patchability"] in {"patchable", "review_only", "blocked"}
    assert verdict["why_now"]
    assert verdict["why_not"]
    assert verdict["uncertainty"]


def test_review_markdown_renders_evidence_verdicts_in_details_only() -> None:
    review = validate_review_findings(
        {
            "summary_text": "Review summary.",
            "risk_items": [
                {
                    "message": "Merge conflict markers present",
                    "severity": "high",
                    "evidence": [{"kind": "patch", "path": "repobrain/github_flow.py", "source": "patch_scan"}],
                }
            ],
        }
    )

    md = render_review_markdown(
        review=review,
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={"command": "review", "route_final": "FAST"},
    )

    assert "### 📌 Evidence verdicts" in md
    assert "Claim: Merge conflict markers present" in md
    assert "Evidence anchors: `repobrain/github_flow.py`" in md
    assert "Patchability: `patchable`" in md
    assert "### 📌 Evidence verdicts" not in _primary(md)


def test_fix_no_patch_renders_governed_evidence_verdict() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 8,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence_backed_patch_target",
            "localized_patch_evidence_count": 0,
            "patch_grounding_mode": "pr_metadata",
        },
    )

    assert "### 📌 Evidence verdict" in md
    assert "Claim: No patch was generated." in md
    assert "Patchability: `blocked`" in md
    assert "Why now: Governance requires localized evidence-backed targets before patch synthesis." in md
    assert "Why not: no_localized_evidence_backed_patch_target" in md
    assert "### 📌 Evidence verdict" not in _primary(md)
