from __future__ import annotations

from repobrain.output_md import render_answer_markdown


def test_multi_model_rendering_shows_preferred_final_and_distribution() -> None:
    md = render_answer_markdown(
        answer_text="Summary",
        evidence=[],
        audit_summary={
            "route_final": "DEEP",
            "pass_count": 2,
            "retrieved": 20,
            "selected": 5,
            "execution_mode": "retrieval_plus_llm",
            "llm_used": True,
            "llm_preferred_model_id": "openai/gpt-4.1",
            "llm_final_synthesis_model_id": "openai/gpt-4.1",
            "llm_model_used": "openai/gpt-4.1",
            "llm_models_used": "openai/gpt-4.1 (3 calls), openai/gpt-4.1-mini (1 call)",
            "llm_model_counts": {"openai/gpt-4.1": 3, "openai/gpt-4.1-mini": 1},
            "llm_tokens_prompt": 300,
            "llm_tokens_completion": 140,
            "llm_tokens_total": 440,
            "llm_calls_this_run": 4,
            "llm_remaining_requests": 17,
        },
        next_steps="Validate",
        command="ask",
    )

    assert "Preferred model: `openai/gpt-4.1`" in md
    assert "Final synthesis model: `openai/gpt-4.1`" in md
    assert "Models used: openai/gpt-4.1 (3 calls), openai/gpt-4.1-mini (1 call)" in md


def test_failed_llm_run_does_not_claim_final_model_used() -> None:
    md = render_answer_markdown(
        answer_text="Summary",
        evidence=[],
        audit_summary={
            "route_final": "DEEP",
            "pass_count": 2,
            "retrieved": 20,
            "selected": 5,
            "execution_mode": "retrieval_plus_llm",
            "llm_used": False,
            "llm_skip_reason": "LLM_NOT_AVAILABLE:http_error",
            "llm_preferred_model_id": "openai/gpt-4.1",
            "llm_final_synthesis_model_id": "not used",
            "llm_model_used": "not used",
            "llm_models_used": "n/a",
        },
        next_steps="Validate",
        command="ask",
    )

    assert "LLM used: no" in md
    assert "Final synthesis model: `n/a`" in md
    assert "Models used: n/a" in md


def test_retained_preferred_model_hides_downgrade_only_budget_action() -> None:
    md = render_answer_markdown(
        answer_text="Summary",
        evidence=[],
        audit_summary={
            "route_final": "DEEP",
            "pass_count": 2,
            "retrieved": 20,
            "selected": 5,
            "execution_mode": "retrieval_plus_llm",
            "llm_used": True,
            "llm_preferred_model_id": "openai/gpt-4.1",
            "llm_final_synthesis_model_id": "openai/gpt-4.1",
            "llm_model_used": "openai/gpt-4.1",
            "llm_retained_preferred_model_reason": "retained preferred model: complex ask/explain in estimate mode",
            "llm_budget_action": "model_downgraded_to_mini_estimate_mode",
        },
        next_steps="Validate",
        command="ask",
    )

    assert "Preferred model retained:" in md
    assert "AI Budget action: budget policy evaluated; preferred model retained" in md
    assert "model_downgraded_to_mini_estimate_mode" not in md


def test_intermediate_downgrade_does_not_imply_full_final_downgrade() -> None:
    md = render_answer_markdown(
        answer_text="Summary",
        evidence=[],
        audit_summary={
            "route_final": "DEEP",
            "pass_count": 2,
            "retrieved": 20,
            "selected": 5,
            "execution_mode": "retrieval_plus_llm",
            "llm_used": True,
            "llm_preferred_model_id": "openai/gpt-4.1",
            "llm_final_synthesis_model_id": "openai/gpt-4.1",
            "llm_model_used": "openai/gpt-4.1",
            "llm_model_counts": {"openai/gpt-4.1": 2, "openai/gpt-4.1-mini": 1},
            "llm_retained_preferred_model_reason": "retained preferred model: review synthesis retained strong model",
            "llm_budget_action": "model_downgraded_to_mini",
            "llm_model_downgrade_reason": "n/a",
        },
        next_steps="Validate",
        command="review",
    )

    assert "Final synthesis retained preferred model: yes" in md
    assert "Intermediate downgrade occurred: yes" in md
    assert "AI Budget action: budget policy evaluated; final synthesis retained preferred model;" in md
