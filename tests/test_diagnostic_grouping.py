from __future__ import annotations

from repobrain.output_md import render_answer_markdown


def test_diagnostic_group_order_is_stable() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "route_final": "FAST",
            "execution_mode": "retrieval_only",
            "llm_intent": "none",
            "llm_decision_reason_code": "DIRECT_EVIDENCE_SUFFICIENT",
            "tkya_backend": "v5",
            "tky_engine": "baseline",
            "llm_used": True,
            "llm_model_used": "openai/gpt-4.1-mini",
            "llm_calls_this_run": 1,
            "llm_tokens_total": 33,
            "embed_used": True,
            "embed_model_id": "openai/text-embedding-3-small",
            "embed_query_embedded": True,
            "embed_chunks_embedded": 5,
            "retrieved": 10,
            "selected": 2,
            "pass_count": 1,
            "verification_pass_count": 1,
            "verification_fail_count": 0,
            "verification_pending_count": 0,
            "verification_not_run_count": 0,
            "llm_provider_error_type": "n/a",
            "llm_provider_http_status": 200,
        },
        next_steps="Next",
        command="ask",
    )

    sections = [
        "#### A. Decision summary",
        "#### B. Runtime / Policy",
        "#### C. LLM",
        "#### D. Embeddings",
        "#### E. Retrieval / Evidence",
        "#### F. Verification",
        "#### G. Provider / Quota",
    ]

    indices = [md.index(section) for section in sections]
    assert indices == sorted(indices)
