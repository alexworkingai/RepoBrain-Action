from __future__ import annotations

from repobrain.github_flow import (
    _prepend_pr_metadata_to_answer,
    _resolve_answer_grounding_mode,
    _should_use_pr_metadata_grounding,
)
from repobrain.llm.prompts import build_messages_for_review


def test_pr_metadata_grounding_selected_for_pr_semantic_context() -> None:
    used = _should_use_pr_metadata_grounding(
        cmd="ask",
        question="Summarize current PR impact",
        github_context={"is_pr": True, "changed_files": ["repobrain/github_flow.py", "README.md"]},
        execution_mode="retrieval_plus_llm",
        llm_intent="summarize",
    )
    assert used is True


def test_answer_grounding_mode_prefers_pr_metadata_or_hybrid() -> None:
    assert _resolve_answer_grounding_mode(pr_metadata_used=True, evidence_count=0) == "pr_metadata"
    assert _resolve_answer_grounding_mode(pr_metadata_used=True, evidence_count=3) == "hybrid"
    assert _resolve_answer_grounding_mode(pr_metadata_used=False, evidence_count=3) == "retrieval"


def test_prepend_pr_metadata_places_changed_files_first() -> None:
    text = _prepend_pr_metadata_to_answer(
        answer_text="Short synthesized answer.",
        changed_files=["repobrain/github_flow.py", "repobrain/output_md.py"],
        primary_segments="core_code:repobrain/github_flow",
        segment_summary="primary=core_code:repobrain/github_flow; support=docs:docs; cross_segment=no",
    )

    first_line = text.splitlines()[0]
    assert first_line == "PR metadata (changed files):"
    assert "Primary segments: core_code:repobrain/github_flow" in text
    assert "Segment summary: primary=core_code:repobrain/github_flow" in text
    assert "- `repobrain/github_flow.py`" in text
    assert "Short synthesized answer." in text


def test_review_prompt_assembles_changed_files_before_diff_context() -> None:
    messages, _stats = build_messages_for_review(
        query="Review this PR",
        changed_files=["repobrain/github_flow.py", "repobrain/output_md.py"],
        diff_hunks=["@@ -1 +1 @@\n-old\n+new"],
        max_input_tokens=1200,
        selected_snippets=["chunk-1", "chunk-2"],
    )

    assert len(messages) == 2
    user_content = messages[1]["content"]
    locators_pos = user_content.find("Locators:")
    diff_pos = user_content.find("Diff hunks:")
    assert locators_pos >= 0
    assert diff_pos > locators_pos
    assert "- repobrain/github_flow.py" in user_content
