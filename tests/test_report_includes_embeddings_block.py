from __future__ import annotations

from repobrain.evidence import EvidenceItem
from repobrain.output_md import render_answer_markdown


def test_render_answer_markdown_includes_embeddings_metadata() -> None:
    md = render_answer_markdown(
        answer_text="Short answer",
        evidence=[
            EvidenceItem(
                file_path="repobrain/tky_provider.py",
                line_start=1,
                line_end=20,
                score=0.9,
            )
        ],
        audit_summary={
            "route_final": "FAST",
            "pass_count": 1,
            "retrieved": 10,
            "selected": 1,
            "embed_used": True,
            "embed_reason": "ok",
            "embed_model_id": "openai/text-embedding-3-small",
            "embed_tokens_prompt": 12,
            "embed_tokens_total": 12,
            "embed_usage_estimated": False,
            "embed_remaining_requests": 77,
            "embed_remaining_is_estimate": False,
            "embed_reset_time_utc_iso": "2026-03-05T23:59:59Z",
            "embed_chunks_embedded": 256,
            "embed_query_embedded": True,
            "embed_index_model": "openai/text-embedding-3-small",
            "embed_index_dim": 1536,
        },
        next_steps="Open evidence links and verify logic",
        command="ask",
    )

    assert "### Embeddings" in md
    assert "Embeddings used: yes" in md
    assert "Embeddings model: `openai/text-embedding-3-small`" in md
    assert "Index vectors: model=openai/text-embedding-3-small, dim=1536, chunks=256" in md
    assert "Query embedded: yes" in md
    assert "Tokens used: prompt=12 total=12 (reported)" in md
