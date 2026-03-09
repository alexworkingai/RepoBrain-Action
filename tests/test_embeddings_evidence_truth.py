from __future__ import annotations

from pathlib import Path

from repobrain import github_flow


def test_embeddings_runtime_truth_ok_when_vectors_used() -> None:
    runtime_truth = github_flow._build_embeddings_runtime_truth(  # noqa: SLF001
        embeddings_enabled=True,
        vectors_meta={
            "status": "PARTIAL",
            "reason": "manifest_partial",
            "chunks_embedded": 11,
            "model": "openai/text-embedding-3-small",
        },
        embeddings_meta={
            "embed_query_embedded": True,
            "embed_model_id": "openai/text-embedding-3-small",
        },
        retrieval_runtime={
            "query_embedded": True,
            "index_vectors_loaded": True,
            "index_vectors_used": True,
            "chunks_with_vectors": 11,
            "evidence_reason": "index_vectors_used_for_hybrid_scoring",
        },
    )

    assert runtime_truth["status"] == "OK"
    assert runtime_truth["evidence_reason"] == "index_vectors_used_for_hybrid_scoring"
    assert runtime_truth["index_vectors_used"] is True


def test_embeddings_runtime_truth_partial_when_query_embedded_without_index_vectors(tmp_path: Path) -> None:
    index_path = tmp_path / "index-package.zip"
    payload = github_flow._build_index_embeddings_evidence_payload(  # noqa: SLF001
        index_path=index_path,
        vectors_meta={"status": "UNKNOWN", "reason": "missing_vectors", "chunks_embedded": 0},
        embeddings_meta={
            "embed_query_embedded": True,
            "embed_model_id": "openai/text-embedding-3-small",
            "embed_chunks_embedded": 0,
        },
        index_vectors_used=False,
        embeddings_runtime={
            "query_embedded": True,
            "index_vectors_loaded": False,
            "index_vectors_used": False,
            "chunks_with_vectors": 0,
            "evidence_reason": "query_embedded_but_no_index_vectors",
            "embedding_model": "openai/text-embedding-3-small",
        },
    )

    assert payload["status"] in {"PARTIAL", "DISABLED"}
    assert payload["reason"] in {
        "query_embedded_but_no_index_vectors",
        "query_embedded_but_index_vectors_not_used",
    }
    assert payload["query_embedded"] is True
    assert payload["index_vectors_loaded"] is False
