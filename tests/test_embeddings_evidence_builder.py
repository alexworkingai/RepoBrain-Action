from pathlib import Path
import zipfile

from repobrain import github_flow


def test_embeddings_evidence_ok_when_vectors_used(tmp_path: Path) -> None:
    index_zip = tmp_path / "index-package.zip"
    with zipfile.ZipFile(index_zip, mode="w") as zf:
        zf.writestr("index/embeddings.jsonl", "{\"chunk_id\":\"c1\",\"vec\":[0.1,0.2]}\n")

    payload = github_flow._build_index_embeddings_evidence_payload(  # noqa: SLF001
        index_path=index_zip,
        vectors_meta={
            "status": "PARTIAL",
            "reason": "manifest_partial",
            "model": "openai/text-embedding-3-small",
            "chunks_embedded": 12,
        },
        embeddings_meta={
            "embed_query_embedded": True,
            "embed_model_id": "openai/text-embedding-3-small",
            "embed_chunks_embedded": 12,
        },
        index_vectors_used=True,
    )

    assert payload["status"] == "OK"
    assert payload["reason"] == "index_vectors_used_for_hybrid_scoring"
    assert payload["index_vectors_used"] is True
    assert payload["embeddings_file_present_in_zip"] is True
    assert payload["model"] == "openai/text-embedding-3-small"
    assert payload["chunks_with_vectors"] == 12
    assert payload["index_embeddings_status"] == "OK"
