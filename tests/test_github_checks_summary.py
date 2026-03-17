from __future__ import annotations

from repobrain.checks_md import build_check_summary_markdown


def test_ask_check_summary_is_compact_and_command_aware() -> None:
    summary, text = build_check_summary_markdown(
        cmd="ask",
        audit={
            "route_final": "DEEP",
            "answer_grounding_mode": "hybrid",
            "llm_used": True,
            "llm_final_synthesis_model_id": "openai/gpt-4.1",
            "check_answer_summary": "Answer about changed files and risks.",
            "verification_report": {"overall": "NOT_RUN"},
            "pr_number": 17,
        },
        conclusion="success",
    )

    assert "### RepoBrain Ask Check" in summary
    assert "- Command: `ask`" in summary
    assert "- Grounding: `hybrid`" in summary
    assert "- Verification: `NOT_RUN`" in summary
    assert "Confirmed findings" not in summary
    assert "Patch result" not in summary
    assert summary == text


def test_review_check_summary_contains_risk_and_finding_counts() -> None:
    summary, _ = build_check_summary_markdown(
        cmd="review",
        audit={
            "route_final": "DEEP",
            "review_risk_level": "HIGH",
            "review_confirmed_findings_count": 3,
            "review_possible_signals_count": 2,
            "review_informational_notes_count": 1,
            "review_risk_drivers_count": 2,
            "review_tldr": "Risk concentrated in CI and security-sensitive files.",
            "verification_report": {"overall": "WARN"},
            "pr_number": 22,
        },
        conclusion="success",
    )

    assert "- Risk level: `HIGH`" in summary
    assert "- Confirmed findings: `3`" in summary
    assert "- Possible signals: `2`" in summary
    assert "- Informational notes: `1`" in summary
    assert "- Risk drivers: `2`" in summary
    assert "Patch result" not in summary


def test_fix_check_summary_contains_patch_fields_only() -> None:
    summary, _ = build_check_summary_markdown(
        cmd="fix",
        audit={
            "route_final": "FAST",
            "patch_generation_result": "valid_patch",
            "patch_target_files_selected": 2,
            "patch_target_files_total": 5,
            "patch_validation_result": "valid_patch",
            "patch_validation_reason": "Patch validated and ready for review.",
            "verification_report": {"overall": "PASS"},
            "pr_number": 31,
        },
        conclusion="success",
    )

    assert "- Patch result: `valid_patch`" in summary
    assert "- Patch targeting: 2 selected / 5 considered" in summary
    assert "- Patch validation: `valid_patch`" in summary
    assert "Confirmed findings" not in summary


def test_closed_pr_review_skip_summary_is_usersafe_and_neutral() -> None:
    summary, _ = build_check_summary_markdown(
        cmd="review",
        audit={
            "route_final": "WAIT",
            "skip_reason_code": "pr_closed_or_merged_review",
            "skip_reason_short": "Skipped: `/repobrain review` runs only on open PRs.",
            "verification_report": {"overall": "NOT_RUN"},
            "pr_number": 40,
        },
        conclusion="neutral",
    )

    assert "Status: **neutral (safe skip)**" in summary
    assert "Skip reason: Skipped: `/repobrain review` runs only on open PRs." in summary


def test_review_check_summary_drops_unsupported_secret_phrase_from_tldr() -> None:
    summary, _ = build_check_summary_markdown(
        cmd="review",
        audit={
            "route_final": "DEEP",
            "review_risk_level": "LOW",
            "review_confirmed_findings_count": 0,
            "review_possible_signals_count": 0,
            "review_informational_notes_count": 0,
            "review_risk_drivers_count": 0,
            "review_tldr": "Possible secret leakage in patch (signal: heuristic wording)",
            "verification_report": {"overall": "NOT_RUN"},
            "pr_number": 22,
        },
        conclusion="neutral",
    )

    assert "Possible secret leakage in patch" not in summary
