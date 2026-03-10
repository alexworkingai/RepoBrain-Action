from __future__ import annotations

from pathlib import Path

from repobrain.index_store import build_index
from repobrain.llm.github_models_embeddings import EmbeddingsResponse


def test_index_embeddings_cache_reuses_vectors(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)
    (repo_root / "src" / "main.py").write_text(
        "class Provider:\n    pass\n",
        encoding="utf-8",
    )
    (repo_root / "README.md").write_text("# RepoBrain\n", encoding="utf-8")

    monkeypatch.setenv("RB_EMBED_ENABLED", "1")
    monkeypatch.setenv("RB_EMBED_MODEL", "openai/text-embedding-3-small")
    monkeypatch.setenv("RB_EMBED_BATCH_SIZE", "64")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    calls = {"n": 0}

    def fake_embed(self, *, model_id: str, inputs: list[str]) -> EmbeddingsResponse:  # noqa: ANN001
        calls["n"] += 1
        vectors = [[0.1, 0.2, 0.3] for _ in inputs]
        return EmbeddingsResponse(
            vectors=vectors,
            model_id=model_id,
            prompt_tokens=10,
            total_tokens=10,
            usage_estimated=False,
            ratelimit_headers={},
            remaining_requests=100,
            remaining_is_estimate=False,
            reset_time_utc_iso="2026-03-05T23:59:59+00:00",
        )

    monkeypatch.setattr(
        "repobrain.index_store.GitHubModelsEmbeddingsClient.embed",
        fake_embed,
    )

    out1 = repo_root / "artifacts" / "index-first.zip"
    out2 = repo_root / "artifacts" / "index-second.zip"
    build_index(root=repo_root, out_zip=out1, store_text=False)
    first_calls = calls["n"]
    build_index(root=repo_root, out_zip=out2, store_text=False)

    assert first_calls > 0
    assert calls["n"] == first_calls
