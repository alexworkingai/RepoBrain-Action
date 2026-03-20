from __future__ import annotations

from repobrain.github_flow import (
    _collect_pr_changed_file_entries_from_context,
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
        changed_file_entries=[
            {"path": "repobrain/github_flow.py", "operation": "modified"},
            {"path": "repobrain/output_md.py", "operation": "modified"},
        ],
        primary_segments="core_code:repobrain/github_flow",
        segment_summary="primary=core_code:repobrain/github_flow; support=docs:docs; cross_segment=no",
    )

    first_line = text.splitlines()[0]
    assert first_line == "PR metadata: 2 changed files in current PR."
    assert "Primary segments: core_code:repobrain/github_flow" in text
    assert "Segment summary: primary=core_code:repobrain/github_flow" in text
    assert "- Modified: `repobrain/github_flow.py`" in text
    assert "Short synthesized answer." in text


def test_collect_pr_changed_file_entries_from_context_uses_authoritative_status() -> None:
    entries = _collect_pr_changed_file_entries_from_context(
        {
            "files": [
                {"filename": "PRODUCTION_READINESS_ASSESSMENT.md", "status": "removed"},
                {"filename": "docs/topocore_v5_phase0_phase1_parity.md", "status": "removed"},
            ],
            "changed_files": [
                "PRODUCTION_READINESS_ASSESSMENT.md",
                "docs/topocore_v5_phase0_phase1_parity.md",
            ],
        }
    )

    assert entries == [
        {"path": "PRODUCTION_READINESS_ASSESSMENT.md", "operation": "removed"},
        {"path": "docs/topocore_v5_phase0_phase1_parity.md", "operation": "removed"},
    ]


def test_prepend_pr_metadata_filters_untrusted_changed_file_claims_from_llm_text() -> None:
    text = _prepend_pr_metadata_to_answer(
        answer_text=(
            "This PR made the following changes:\n"
            "- Updated `repobrain/ask.py`\n"
            "- Updated `tests/test_pr_review.py`\n\n"
            "Supporting context: retrieval ranked `repobrain/ask.py` as related to the question."
        ),
        changed_files=[
            "PRODUCTION_READINESS_ASSESSMENT.md",
            "docs/topocore_v5_phase0_phase1_parity.md",
        ],
        changed_file_entries=[
            {"path": "PRODUCTION_READINESS_ASSESSMENT.md", "operation": "removed"},
            {"path": "docs/topocore_v5_phase0_phase1_parity.md", "operation": "removed"},
        ],
    )

    assert "- Removed: `PRODUCTION_READINESS_ASSESSMENT.md`" in text
    assert "- Removed: `docs/topocore_v5_phase0_phase1_parity.md`" in text
    assert "Updated `repobrain/ask.py`" not in text
    assert "Updated `tests/test_pr_review.py`" not in text
    assert "Supporting context: retrieval ranked `repobrain/ask.py`" in text


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
