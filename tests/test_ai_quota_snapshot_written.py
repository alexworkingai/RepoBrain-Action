from __future__ import annotations

from pathlib import Path

import orjson

from repobrain.github_flow import run_github_flow


def test_ai_quota_snapshot_is_written_for_dry_run(tmp_path: Path) -> None:
    status = run_github_flow(
        repo_root=tmp_path,
        dry_run=True,
        comment_text="/repobrain help",
        issue_number=None,
        tky_mode="baseline",
    )
    assert status == "DRY_RUN_OK"

    snapshot_path = tmp_path / "artifacts" / "ai_quota_snapshot.json"
    assert snapshot_path.exists()
    data = orjson.loads(snapshot_path.read_bytes())
    assert "llm" in data
    assert "embeddings" in data
    assert "governor" in data

    payload = snapshot_path.read_text(encoding="utf-8").lower()
    assert "raw_text" not in payload
    assert "snippet" not in payload
    assert "content\":" not in payload
