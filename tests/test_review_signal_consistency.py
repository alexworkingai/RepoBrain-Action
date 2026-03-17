from __future__ import annotations

from repobrain.output_md import render_review_markdown
from repobrain.review_validator import validate_review_findings


def test_possible_signals_counter_matches_rendered_items() -> None:
    review = validate_review_findings(
        {
            "summary_text": "Potential review risks.",
            "risk_items": [
                {"message": "Possible security-sensitive area changed", "severity": "high", "evidence": []},
                {"message": "TODO markers present", "severity": "medium", "evidence": []},
            ],
            "notes": ["Manual check recommended."],
        }
    )
    audit_summary = {
        "route_final": "DEEP",
        "pass_count": 1,
        "review_possible_signals_count": int(review["validation"]["possible_signals_count"]),
        "review_confirmed_findings_count": int(review["validation"]["confirmed_findings_count"]),
        "verification_pass_count": 0,
        "verification_fail_count": 0,
        "verification_pending_count": 0,
        "verification_not_run_count": 0,
    }
    md = render_review_markdown(
        review=review,
        verification_report={"summary": "not run", "checks": []},
        audit_summary=audit_summary,
    )

    assert "### 🟡 Possible signals" in md
    assert "- None." not in md
    assert "### ℹ️ Informational notes" in md


def test_high_risk_output_includes_explicit_risk_drivers() -> None:
    review = validate_review_findings(
        {
            "summary_text": "Appears low risk.",
            "risk_items": [
                {
                    "message": "Security-sensitive area changed",
                    "severity": "high",
                    "evidence": [{"kind": "file_path", "path": "repobrain/security_policy.py", "source": "path_rule"}],
                }
            ],
        }
    )
    md = render_review_markdown(
        review=review,
        verification_report={"summary": "not run", "checks": []},
        audit_summary={"route_final": "DEEP", "pass_count": 1},
    )

    assert "Risk level: **HIGH**" in md
    assert "Risk drivers:" in md
    assert "Security-sensitive area changed" in md


def test_rendered_review_never_leaks_heuristic_secret_signal() -> None:
    review = validate_review_findings(
        {
            "summary_text": "Review summary.",
            "risk_items": [
                {
                    "message": "Possible secret leakage in patch",
                    "severity": "high",
                    "evidence": [{"kind": "patch", "path": ".github/workflows/repobrain.yml", "source": "patch_scan"}],
                }
            ],
        }
    )
    md = render_review_markdown(
        review=review,
        verification_report={"summary": "not run", "checks": []},
        audit_summary={"route_final": "DEEP", "pass_count": 1},
    )

    assert "Possible secret leakage in patch (signal: heuristic wording)" not in md
    assert "heuristic security wording was downgraded" in md.lower()


def test_render_review_strips_raw_leaked_secret_phrase_from_possible_signals() -> None:
    review = {
        "summary_text": "Summary includes review notes.",
        "risk_level": "low",
        "files_block": ["- `src/a.py`"],
        "confirmed_findings": [],
        "possible_signals": ["Possible secret leakage in patch (signal: heuristic wording)"],
        "informational_notes": ["Context note."],
        "recommendations": ["Run tests."],
    }
    md = render_review_markdown(
        review=review,
        verification_report={"summary": "not run", "checks": []},
        audit_summary={"route_final": "FAST", "pass_count": 1},
    )

    assert "Possible secret leakage in patch (signal: heuristic wording)" not in md


def test_render_review_strips_raw_leaked_secret_phrase_from_informational_notes() -> None:
    review = {
        "summary_text": "Summary includes review notes.",
        "risk_level": "low",
        "files_block": ["- `src/a.py`"],
        "confirmed_findings": [],
        "possible_signals": [],
        "informational_notes": [
            "Possible secret leakage in patch (informational: heuristic security wording without concrete evidence)"
        ],
        "recommendations": ["Run tests."],
    }
    md = render_review_markdown(
        review=review,
        verification_report={"summary": "not run", "checks": []},
        audit_summary={"route_final": "FAST", "pass_count": 1},
    )

    assert "Possible secret leakage in patch" not in md
