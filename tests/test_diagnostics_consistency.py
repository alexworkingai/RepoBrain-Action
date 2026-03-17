from __future__ import annotations

from repobrain.output_md import render_answer_markdown, render_patch_markdown


def test_retained_preferred_model_does_not_render_downgrade_budget_action() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "route_final": "DEEP",
            "pass_count": 2,
            "execution_mode": "retrieval_plus_llm",
            "llm_used": True,
            "llm_model_used": "openai/gpt-4.1",
            "llm_preferred_model_id": "openai/gpt-4.1",
            "llm_final_synthesis_model_id": "openai/gpt-4.1",
            "llm_retained_preferred_model_reason": "retained preferred model: complex ask/explain in estimate mode",
            "llm_budget_action": "model_downgraded_to_mini_estimate_mode",
        },
        next_steps="Validate",
        command="ask",
    )

    assert "AI Budget action: budget policy evaluated; preferred model retained" in md
    assert "model_downgraded_to_mini_estimate_mode" not in md


def test_fix_pr_context_diagnostics_keep_pr_metadata_counts_consistent() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "pr_changed_files_count": 9,
            "pr_metadata_used": True,
            "patch_target_files_total": 9,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence_backed_patch_target",
            "patch_grounding_mode": "pr_metadata",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": (
                "No patch generated: no sufficiently localized, evidence-backed patch target was found."
            ),
        },
    )

    assert "| PR changed files | `9` |" in md
    assert "| PR metadata used | `yes` |" in md


def test_patch_targeting_mode_none_is_meaningful_in_diagnostics() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "pr_changed_files_count": 4,
            "pr_metadata_used": True,
            "patch_target_files_total": 4,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence_backed_patch_target",
            "patch_grounding_mode": "pr_metadata",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
        },
    )

    assert "| Patch targeting mode | `none` |" in md
    assert "undefined: Localized patch-target selection strategy outcome." not in md


def test_ask_diagnostics_do_not_include_review_only_rows() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "route_final": "FAST",
            "pass_count": 1,
            "execution_mode": "retrieval_only",
            "command": "ask",
            "llm_used": False,
        },
        next_steps="n/a",
        command="ask",
    )

    assert "Review confirmed findings" not in md
    assert "Review possible signals" not in md


def test_fix_diagnostics_do_not_include_review_only_rows() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence_backed_patch_target",
            "patch_grounding_mode": "pr_metadata",
        },
    )

    assert "Review confirmed findings" not in md
    assert "Review possible signals" not in md


def test_sprint38_observability_fields_render_for_fix() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_confirmed_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
            "hybrid_rerank_used": False,
            "retrieval_ranking_mode": "lexical",
            "evidence_filtered_count": 2,
            "evidence_filter_reason_codes": "docs_noise,duplicate_region",
            "signal_calibration_used": True,
            "patch_guard_triggered": True,
            "tldr_compressed": False,
        },
    )

    assert "| Hybrid rerank used | `no` |" in md
    assert "| Retrieval ranking mode | `lexical` |" in md
    assert "| Evidence filtered | `2` |" in md
    assert "| Evidence filter reason codes | `docs_noise,duplicate_region` |" in md
    assert "| Signal calibration used | `yes` |" in md
    assert "| Patch guard triggered | `yes` |" in md
    assert "| TL;DR compressed | `no` |" in md


def test_check_publication_diagnostics_fields_render() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "pass_count": 1,
            "check_run_attempted": False,
            "check_run_published": False,
            "check_run_status_code": "deferred",
            "check_run_failure_class": "deferred",
            "check_run_token_source": "workflow_run_github_token",
            "check_run_event_name": "issue_comment",
            "check_run_required_permissions_header": "n/a",
            "check_run_skip_reason": "deferred_workflow_publisher",
        },
        next_steps="n/a",
        command="ask",
    )

    assert "| Check-run attempted | `no` |" in md
    assert "| Check-run status | `deferred` |" in md
    assert "| Check-run token source | `workflow_run_github_token` |" in md
    assert "| Check-run failure class | `deferred` |" in md
