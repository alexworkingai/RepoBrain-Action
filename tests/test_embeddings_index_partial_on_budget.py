from __future__ import annotations

from pathlib import Path
import zipfile

import orjson

from repobrain.ai_budget_governor import AIBudgetGovernor, BudgetPolicy
from repobrain.index_store import MANIFEST_NAME, build_index
from repobrain.llm.github_models_embeddings import EmbeddingsResponse


def test_embeddings_index_stops_early_and_marks_partial(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)
    (repo_root / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
    (repo_root / "src" / "b.py").write_text("b = 2\n", encoding="utf-8")
    (repo_root / "src" / "c.py").write_text("c = 3\n", encoding="utf-8")

    monkeypatch.setenv("RB_EMBED_ENABLED", "1")
    monkeypatch.setenv("RB_EMBED_BATCH_SIZE", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_embed(self, *, model_id: str, inputs: list[str]) -> EmbeddingsResponse:  # noqa: ANN001
        return EmbeddingsResponse(
            vectors=[[0.1, 0.2, 0.3] for _ in inputs],
            model_id=model_id,
            prompt_tokens=10,
            total_tokens=10,
            usage_estimated=False,
            ratelimit_headers={},
            remaining_requests=20,
            remaining_is_estimate=False,
            reset_time_utc_iso=None,
        )

    monkeypatch.setattr("repobrain.index_store.GitHubModelsEmbeddingsClient.embed", fake_embed)

    governor = AIBudgetGovernor(
        BudgetPolicy(
            max_embed_calls_per_run=1,
            min_remaining_buffer=0,
            stop_at_remaining=False,
        )
    )

    zip_path = repo_root / "artifacts" / "index-package.zip"
    build_index(root=repo_root, out_zip=zip_path, store_text=False, governor=governor)

    with zipfile.ZipFile(zip_path, mode="r") as zf:
        manifest = orjson.loads(zf.read(MANIFEST_NAME))
    embeddings = manifest.get("embeddings", {})
    assert embeddings.get("status") in {"PARTIAL", "DISABLED"}
    assert int(embeddings.get("calls", 0) or 0) <= 1
    assert int(embeddings.get("skipped_chunks", 0) or 0) >= 1
