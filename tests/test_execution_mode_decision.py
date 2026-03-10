from __future__ import annotations

from repobrain.execution_mode import decide_semantic_execution


def test_direct_high_confidence_ask_uses_retrieval_only() -> None:
    decision = decide_semantic_execution(
        task_type="ask",
        route="FAST",
        selected_count=1,
        selected_files=1,
        top_score=0.12,
        score_gap=0.09,
        is_pr_context=False,
        verification_pending=False,
        verification_failed=False,
    )
    assert decision.execution_mode == "retrieval_only"
    assert decision.llm_intent == "none"


def test_deep_multi_source_ask_uses_retrieval_plus_llm() -> None:
    decision = decide_semantic_execution(
        task_type="ask",
        route="DEEP",
        selected_count=4,
        selected_files=3,
        top_score=0.04,
        score_gap=0.01,
        is_pr_context=False,
        verification_pending=False,
        verification_failed=False,
    )
    assert decision.execution_mode == "retrieval_plus_llm"
    assert decision.llm_intent == "summarize"


def test_review_defaults_to_retrieval_plus_llm() -> None:
    decision = decide_semantic_execution(
        task_type="review",
        route="FAST",
        selected_count=3,
        selected_files=2,
        top_score=0.08,
        score_gap=0.02,
        is_pr_context=True,
        verification_pending=False,
        verification_failed=False,
        request_intent="analysis",
    )
    assert decision.execution_mode == "retrieval_plus_llm"
    assert decision.llm_intent == "review"


def test_wait_route_maps_to_verification_first() -> None:
    decision = decide_semantic_execution(
        task_type="ask",
        route="WAIT",
        selected_count=0,
        selected_files=0,
        top_score=0.0,
        score_gap=0.0,
        is_pr_context=False,
        verification_pending=False,
        verification_failed=False,
    )
    assert decision.execution_mode == "verification_first"
    assert decision.llm_intent == "none"


def test_refuse_and_block_routes_map_to_refuse_mode() -> None:
    refuse = decide_semantic_execution(
        task_type="ask",
        route="REFUSE",
        selected_count=0,
        selected_files=0,
        top_score=0.0,
        score_gap=0.0,
        is_pr_context=False,
        verification_pending=False,
        verification_failed=False,
    )
    block = decide_semantic_execution(
        task_type="ask",
        route="BLOCK",
        selected_count=0,
        selected_files=0,
        top_score=0.0,
        score_gap=0.0,
        is_pr_context=False,
        verification_pending=False,
        verification_failed=False,
    )
    assert refuse.execution_mode == "refuse"
    assert block.execution_mode == "refuse"
